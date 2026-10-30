#!/usr/bin/env python3
"""
homebench.py - a tiny 8-task LLM benchmark for llama.cpp (llama-server).

Starts a web UI at http://localhost:8000. Open it in your browser, enter a
llama-server URL, and run benchmarks. Results accumulate in results.jsonl.

Usage:
    python homebench.py
    # then open http://localhost:8000

    python homebench.py --port 8001
    # custom port
"""
import argparse
import json
import os
import re
import threading
import tempfile
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from tasks import TASKS


# --------------------------------------------------------------------------
# Timeouts (overridable via environment variables)
# --------------------------------------------------------------------------
# subprocess.run returns as soon as the child process exits — it does NOT
# wait the full timeout if the work finishes early. These are upper bounds.
CHAT_TIMEOUT = int(os.environ.get("HOMEBENCH_CHAT_TIMEOUT", "600"))  # seconds


# --------------------------------------------------------------------------
# Talking to llama-server (OpenAI-compatible endpoint)
# --------------------------------------------------------------------------


def _sanitize_output(text):
    if not isinstance(text, str):
        return text
    text = re.sub(r'(?is)<thinking>.*?</thinking>', '', text)
    text = re.sub(r'(?i)</?thinking>', '', text)
    return text


def chat(base_url, prompt, temperature, max_tokens, timeout):
    body = json.dumps({
        "model": "local",  # llama-server ignores this; it serves one model
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        text = json.load(resp)["choices"][0]["message"].get("content") or ""
    # Drop reasoning blocks from "thinking" models (e.g. Qwen3, DeepSeek-R1)
    return _sanitize_output(text)


# --------------------------------------------------------------------------
# Shared benchmark core
# --------------------------------------------------------------------------

def run_benchmark(url, name, runs, temperature, max_tokens, timeout,
                  out_path, note="", on_result=None, task_id=None):
    """Run tasks `runs` times, append rows to out_path (JSONL).

    If ``task_id`` is given, only that task is run; otherwise every task
    in ``TASKS`` is run.

    on_result(task_id, run_index, passed, reason) is called after each
    task-run so callers can print progress or update UI state.
    Each row records ``elapsed`` — the wall-clock seconds spent on that
    single task run (chat request plus checker).
    Returns the batch id.
    """
    tasks = [t for t in TASKS if t["id"] == task_id] if task_id else TASKS
    if task_id and not tasks:
        raise ValueError(f"unknown task id: {task_id!r}")
    batch = int(time.time())
    with open(out_path, "a") as out:
        for task in tasks:
            for run in range(runs):
                started = time.perf_counter()
                try:
                    output = chat(url, task["prompt"], temperature,
                                  max_tokens, timeout)
                    passed = bool(task["check"](output))
                    reason = task.get("explain", lambda x: "")(output)
                except Exception as e:  # server down, timeout, bad response...
                    output, passed, reason = f"[ERROR] {e}", False, "FAIL: " + str(e)
                elapsed = round(time.perf_counter() - started, 3)
                row = {
                    "batch": batch, "model": name, "task": task["id"],
                    "run": run, "passed": passed, "reason": reason,
                    "output": output, "note": note, "temperature": temperature,
                    "elapsed": elapsed,
                }
                out.write(json.dumps(row) + "\n")
                out.flush()
                if on_result:
                    on_result(task["id"], run, passed, reason)
    return batch


# Highest number of repeats allowed for one temperature plan.
MAX_PLAN_RUNS = 50


def parse_plans(raw):
    """Validate temperature plans: ``[{"temperature": 0.6, "runs": 3}, ...]``.

    Returns a normalized list of dicts with float ``temperature`` and int
    ``runs``. Raises ValueError with a user-facing message for invalid input.
    """
    if not isinstance(raw, list) or not raw:
        raise ValueError("at least one temperature plan is required")
    plans = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each temperature plan must be an object")
        try:
            temperature = float(item.get("temperature", 0.0))
            runs = int(item.get("runs", 1))
        except (TypeError, ValueError):
            raise ValueError("temperature and runs must be numbers")
        if not 0 <= temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")
        if not 1 <= runs <= MAX_PLAN_RUNS:
            raise ValueError(f"runs must be between 1 and {MAX_PLAN_RUNS}")
        plans.append({"temperature": temperature, "runs": runs})
    return plans


def run_benchmark_plans(url, name, plans, max_tokens, timeout, out_path,
                        note="", task_id=None, on_result=None, on_plan=None):
    """Execute every temperature plan in order, one model label per plan.

    Each plan runs the selected task(s) ``runs`` times at its temperature.
    Labels are made unique against the results file (and earlier plans) so a
    multi-temperature sweep does not overwrite previous results.

    on_plan(index, label, plan) is called before a plan starts so callers can
    update progress state. Returns the list of ``(label, plan)`` jobs executed.
    """
    existing = {r.get("model") for r in load_rows(out_path)}
    jobs = []
    for plan in plans:
        label = unique_model_name(name, existing)
        existing.add(label)
        jobs.append((label, plan))
    for index, (label, plan) in enumerate(jobs):
        if on_plan:
            on_plan(index, label, plan)
        run_benchmark(url, label, plan["runs"], plan["temperature"],
                      max_tokens, timeout, out_path,
                      note=_format_note(note, plan["temperature"]),
                      on_result=on_result, task_id=task_id)
    return jobs


def load_rows(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def infer_model_name(base_url):
    """Try to guess the model name from llama-server /v1/models or /props."""
    base = base_url.rstrip("/")
    try:
        with urllib.request.urlopen(base + "/v1/models", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        for m in data.get("data", []):
            if m.get("id"):
                return m["id"]
    except Exception:
        pass
    try:
        with urllib.request.urlopen(base + "/props", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        for key in ("model_path", "model", "id", "name"):
            if data.get(key):
                val = str(data[key])
                return os.path.splitext(os.path.basename(val))[0] or val
    except Exception:
        pass
    return None


def _format_note(note, temperature):
    """Append temperature to the note string."""
    note = (note or "").strip()
    return f"{note} (temp={temperature})" if note else f"temp={temperature}"


def unique_model_name(name, existing):
    name = (name or "").strip()
    if not name:
        return name
    if name not in existing:
        return name
    i = 1
    while f"{name} ({i})" in existing:
        i += 1
    return f"{name} ({i})"


def delete_rows(path, filters):
    """Remove rows matching all filter criteria from the JSONL results file.

    ``filters`` is a dict whose keys correspond to row fields (e.g. ``model``,
    ``task``, ``batch``, ``run``). Only rows where every filter key matches
    are removed.

    Returns the number of rows deleted.
    """
    rows = load_rows(path)
    remaining = []
    deleted = 0
    for r in rows:
        if all(r.get(k) == v for k, v in filters.items()):
            deleted += 1
        else:
            remaining.append(r)
    if deleted:
        directory = os.path.dirname(os.path.abspath(path))
        fd, temp_path = tempfile.mkstemp(prefix=".homebench-", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                for r in remaining:
                    f.write(json.dumps(r) + "\n")
            os.replace(temp_path, path)
        finally:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass
    return deleted


def rename_model(path, old_name, new_name):
    """Rename old_name to new_name in every row of the JSONL results file.

    Returns the final (possibly auto-incremented) name written to the rows.
    """
    old_name = (old_name or "").strip()
    new_name = (new_name or "").strip()
    if not old_name or not new_name:
        raise ValueError("old and new model name are required")
    rows = load_rows(path)
    if not any(r.get("model") == old_name for r in rows):
        raise KeyError(f"model {old_name!r} not found")
    existing = {r.get("model") for r in rows if r.get("model") != old_name}
    final = unique_model_name(new_name, existing)
    for r in rows:
        if r.get("model") == old_name:
            r["model"] = final
    directory = os.path.dirname(os.path.abspath(path))
    fd, temp_path = tempfile.mkstemp(prefix=".homebench-", suffix=".tmp",
                                     dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        os.replace(temp_path, path)
    finally:
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass
    return final


# --------------------------------------------------------------------------
# Web UI state + endpoints
# --------------------------------------------------------------------------

WEB_OUT = "results.jsonl"
lock = threading.Lock()
state = {"running": False, "model": "", "done": 0, "total": 0, "log": [],
         "error": None, "plan": 0, "plans": 0}


def latest_rows():
    """Rows from each model's most recent run."""
    rows = load_rows(WEB_OUT)
    latest = {}
    for r in rows:
        latest[r["model"]] = max(latest.get(r["model"], 0), r["batch"])
    return [r for r in rows if r["batch"] == latest[r["model"]]]


class Handler(BaseHTTPRequestHandler):
    # def log_message(self, *args):  # keep the terminal quiet
    #     pass

    def send(self, payload, code=200, ctype="application/json"):
        if isinstance(payload, str):
            data = payload.encode()
        elif isinstance(payload, bytes):
            data = payload
        else:
            data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/":
            self.send(PAGE, ctype="text/html")
            return
        if path == "/style.css":
            css_path = Path(__file__).with_name("static") / "style.css"
            self.send(css_path.read_text(encoding="utf-8"), ctype="text/css")
            return
        if path == "/api/tasks":
            self.send([{"id": t["id"], "prompt": t["prompt"]} for t in TASKS])
            return
        if path == "/api/status":
            with lock:
                self.send(dict(state))
            return
        if path == "/api/results":
            self.send(latest_rows())
            return
        if path == "/api/detect_model":
            url = (query.get("url") or [""])[0]
            if not url:
                self.send({"error": "no url"}, code=400)
                return
            try:
                name = infer_model_name(url)
                if name:
                    self.send({"name": name})
                else:
                    self.send({"error": "could not infer model name"}, code=400)
            except Exception as e:
                self.send({"error": str(e)}, code=400)
            return
        if path == "/api/export":
            try:
                with open(WEB_OUT, "rb") as f:
                    data = f.read()
            except FileNotFoundError:
                data = b""
            self.send(data, ctype="application/jsonl")
            return
        self.send({"error": "not found"}, code=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")

        if path == "/api/run":
            name = (body.get("name") or "").strip()
            url = (body.get("url") or "").strip()
            max_tokens = int(body.get("max_tokens", 8192))
            note = body.get("note", "")
            task_id = (body.get("task") or "").strip() or None
            if task_id and task_id not in {t["id"] for t in TASKS}:
                self.send({"error": f"unknown task id: {task_id!r}"}, code=400)
                return
            # New multi-temperature requests send "plans"; the legacy single
            # temperature/runs fields are still accepted for API clients.
            raw_plans = body.get("plans")
            if raw_plans is None:
                raw_plans = [{
                    "temperature": body.get("temperature", 0.0),
                    "runs": body.get("runs", 1),
                }]
            try:
                plans = parse_plans(raw_plans)
            except ValueError as e:
                self.send({"error": str(e)}, code=400)
                return
            if not name:
                name = infer_model_name(url) or "model"
            with lock:
                if state["running"]:
                    self.send({"error": "a benchmark is already running"}, code=409)
                    return
                existing = {r["model"] for r in load_rows(WEB_OUT)}
                name = unique_model_name(name, existing)
                total_tasks = 1 if task_id else len(TASKS)
                total_runs = sum(p["runs"] for p in plans) * total_tasks
                state.update({"running": True, "model": name, "done": 0,
                              "total": total_runs, "log": [], "error": None,
                              "plan": 1, "plans": len(plans)})

            def on_result(task_id, run, passed, reason):
                with lock:
                    state["done"] += 1
                    state["log"].append(
                        f"{task_id} run {run + 1}: {'PASS' if passed else 'FAIL'}")

            def on_plan(index, label, plan):
                with lock:
                    state["model"] = label
                    state["plan"] = index + 1
                    state["log"].append(
                        f"queued {label} @ temp {plan['temperature']} × "
                        f"{plan['runs']} run(s)")

            def work():
                try:
                    run_benchmark_plans(url, name, plans, max_tokens, CHAT_TIMEOUT,
                                        WEB_OUT, note=note, task_id=task_id,
                                        on_result=on_result, on_plan=on_plan)
                finally:
                    with lock:
                        state["running"] = False

            threading.Thread(target=work, daemon=True).start()
            self.send({"ok": True, "queued": len(plans), "total": total_runs})
            return
        if path == "/api/clear":
            if not confirm_clear():
                self.send({"error": "cancelled"}, code=400)
                return
            try:
                os.remove(WEB_OUT)
            except FileNotFoundError:
                pass
            with lock:
                state.update({"running": False, "model": "", "done": 0,
                              "total": 0, "log": [], "error": None,
                              "plan": 0, "plans": 0})
            self.send({"ok": True})
            return
        if path == "/api/rename_model":
            old_name = body.get("old_name") or ""
            new_name = body.get("new_name") or ""
            with lock:
                if state["running"]:
                    self.send({"error": "cannot rename a model while a benchmark is running"},
                              code=409)
                    return
                try:
                    final = rename_model(WEB_OUT, old_name, new_name)
                except (ValueError, KeyError) as e:
                    self.send({"error": str(e)}, code=400)
                    return
            self.send({"ok": True, "name": final})
            return
        if path == "/api/delete_rows":
            with lock:
                if state["running"]:
                    self.send({"error": "cannot delete rows while a benchmark is running"},
                              code=409)
                    return
                filters = {k: v for k, v in body.items() if k in ("model", "task", "batch", "run")}
                if not filters:
                    self.send({"error": "at least one of model, task, batch, run is required"}, code=400)
                    return
                deleted = delete_rows(WEB_OUT, filters)
            self.send({"ok": True, "deleted": deleted})
            return
        self.send({"error": "not found"}, code=404)


PAGE_PATH = Path(__file__).with_name("static") / "index.html"
PAGE = PAGE_PATH.read_text(encoding="utf-8")


def confirm_clear():
    """No-op in headless; the web UI confirms via browser dialog before calling /api/clear."""
    return True


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="LLM benchmark for llama-server — opens a web UI at http://localhost:8000")
    ap.add_argument("--port", type=int, default=8000,
                    help="web UI port (default 8000)")
    ap.add_argument("--timeout", type=int, default=None,
                    help="LLM chat timeout in seconds "
                         "(default: HOMEBENCH_CHAT_TIMEOUT or 300)")
    args = ap.parse_args()
    if args.timeout is not None:
        global CHAT_TIMEOUT
        CHAT_TIMEOUT = args.timeout

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Open http://localhost:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()