#!/usr/bin/env python3
"""
homebench.py - a tiny 7-task LLM benchmark for llama.cpp (llama-server).

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
                  out_path, note="", on_result=None):
    """Run every task `runs` times, append rows to out_path (JSONL).

    on_result(task_id, run_index, passed, reason) is called after each
    task-run so callers can print progress or update UI state.
    Returns the batch id.
    """
    batch = int(time.time())
    with open(out_path, "a") as out:
        for task in TASKS:
            for run in range(runs):
                try:
                    output = chat(url, task["prompt"], temperature,
                                  max_tokens, timeout)
                    passed = bool(task["check"](output))
                    reason = task.get("explain", lambda x: "")(output)
                except Exception as e:  # server down, timeout, bad response...
                    output, passed, reason = f"[ERROR] {e}", False, "FAIL: " + str(e)
                row = {
                    "batch": batch, "model": name, "task": task["id"],
                    "run": run, "passed": passed, "reason": reason,
                    "output": output, "note": note, "temperature": temperature,
                }
                out.write(json.dumps(row) + "\n")
                out.flush()
                if on_result:
                    on_result(task["id"], run, passed, reason)
    return batch


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
state = {"running": False, "model": "", "done": 0, "total": 0, "log": [], "error": None}


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
            runs = int(body.get("runs", 1))
            temperature = float(body.get("temperature", 0.0))
            max_tokens = int(body.get("max_tokens", 8192))
            note = _format_note(body.get("note", ""), temperature)
            if not name:
                name = infer_model_name(url) or "model"
            with lock:
                if state["running"]:
                    self.send({"error": "a benchmark is already running"}, code=409)
                    return
                existing = {r["model"] for r in load_rows(WEB_OUT)}
                name = unique_model_name(name, existing)
                state.update({"running": True, "model": name, "done": 0,
                              "total": len(TASKS) * runs, "log": [], "error": None})

            def work():
                try:
                    def on_result(task_id, run, passed, reason):
                        with lock:
                            state["done"] += 1
                            state["log"].append(
                                f"{task_id} run {run + 1}: {'PASS' if passed else 'FAIL'}")
                    run_benchmark(url, name, runs, temperature, max_tokens, 300,
                                  WEB_OUT, note=note, on_result=on_result)
                finally:
                    with lock:
                        state["running"] = False

            threading.Thread(target=work, daemon=True).start()
            self.send({"ok": True})
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
                              "total": 0, "log": [], "error": None})
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
    args = ap.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Open http://localhost:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()