#!/usr/bin/env python3
"""
web_bench.py - a small web interface for mini_bench.py.
Standard library only. Keep this file in the same folder as mini_bench.py.

Usage:
  1) Start llama-server with the model you want to test:
       llama-server -m your-model.gguf --port 8080
  2) Start the web UI:
       python web_bench.py
  3) Open http://localhost:8000, enter a name for the model, and click Run.

To test the next model: stop llama-server, start it with another .gguf,
type a new name in the UI, and run again. Results from all models are shown
side by side. They are stored in results.jsonl (shared with mini_bench.py).
"""
import argparse
import json
import os
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from mini_bench import TASKS, chat, load_rows, infer_model_name, unique_model_name

OUT = "results.jsonl"
lock = threading.Lock()
state = {"running": False, "model": "", "done": 0, "total": 0, "log": [], "error": None}


# --------------------------------------------------------------------------
# Benchmark runner (runs in a background thread)
# --------------------------------------------------------------------------

def run_benchmark(p):
    batch = int(time.time())
    try:
        with open(OUT, "a") as out:
            for task in TASKS:
                for run in range(p["runs"]):
                    try:
                        output = chat(p["url"], task["prompt"], p["temperature"],
                                      p["max_tokens"], 300)
                        passed = bool(task["check"](output))
                        reason = task.get("explain", lambda x: "")(output)
                    except Exception as e:  # server down, timeout, bad response...
                        output, passed, reason = f"[ERROR] {e}", False, "FAIL: " + str(e)
                    out.write(json.dumps({
                        "batch": batch, "model": p["name"], "task": task["id"],
                        "run": run, "passed": passed, "reason": reason, "output": output,
                        "note": p.get("note", ""),
                    }) + "\n")
                    out.flush()
                    with lock:
                        state["done"] += 1
                        state["log"].append(
                            f"{task['id']} run {run + 1}: {'PASS' if passed else 'FAIL'}")
    except Exception as e:
        with lock:
            state["error"] = str(e)
    finally:
        with lock:
            state["running"] = False


def latest_rows():
    """Rows from each model's most recent run."""
    rows = load_rows(OUT)
    latest = {}
    for r in rows:
        latest[r["model"]] = max(latest.get(r["model"], 0), r["batch"])
    return [r for r in rows if r["batch"] == latest[r["model"]]]


# --------------------------------------------------------------------------
# HTTP server
# --------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # keep the terminal quiet
        pass

    def send(self, payload, code=200, ctype="application/json"):
        data = payload.encode() if isinstance(payload, str) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self.send(PAGE, ctype="text/html")
        elif parsed.path == "/api/tasks":
            self.send([{"id": t["id"], "prompt": t["prompt"]} for t in TASKS])
        elif parsed.path == "/api/results":
            self.send(latest_rows())
        elif parsed.path == "/api/status":
            with lock:
                self.send(dict(state))
        elif parsed.path == "/api/detect_model":
            qs = urllib.parse.parse_qs(parsed.query)
            url = (qs.get("url") or [""])[0].strip()
            if not url:
                self.send({"error": "missing url"}, 400)
                return
            name = infer_model_name(url)
            if not name:
                self.send({"error": "could not detect model name"}, 404)
                return
            self.send({"name": name})
        else:
            self.send({"error": "not found"}, 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self.send({"error": "bad JSON"}, 400)

        if self.path == "/api/clear":
            with lock:
                if state["running"]:
                    return self.send({"error": "a run is in progress"}, 409)
            if os.path.exists(OUT):
                os.remove(OUT)
            return self.send({"ok": True})

        if self.path == "/api/run":
            try:
                name = str(body.get("name", "")).strip()
                url = str(body["url"]).strip()
                runs = int(body["runs"])
                temperature = float(body["temperature"])
                max_tokens = int(body["max_tokens"])
                note = str(body.get("note", "")).strip()
            except (KeyError, ValueError, TypeError):
                return self.send({"error": "invalid parameters"}, 400)
            if not url.startswith("http"):
                return self.send({"error": "enter a URL starting with http"}, 400)
            if not name:
                name = infer_model_name(url)
            if not name:
                return self.send({"error": "enter a model name or a detectable server URL"}, 400)
            if not 1 <= runs <= 20:
                return self.send({"error": "runs must be between 1 and 20"}, 400)
            # avoid overwriting previous results for the same label
            existing = {r["model"] for r in load_rows(OUT)}
            name = unique_model_name(name, existing)
            p = {
                "name": name,
                "url": url,
                "runs": runs,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "note": note,
            }
            with lock:
                if state["running"]:
                    return self.send({"error": "a run is already in progress"}, 409)
                state.update(running=True, model=p["name"], done=0,
                             total=len(TASKS) * p["runs"], log=[], error=None)
            threading.Thread(target=run_benchmark, args=(p,), daemon=True).start()
            return self.send({"ok": True})

        self.send({"error": "not found"}, 404)


# --------------------------------------------------------------------------
# The web page (served from static/index.html)
# --------------------------------------------------------------------------

PAGE_PATH = Path(__file__).with_name("static") / "index.html"
PAGE = PAGE_PATH.read_text(encoding="utf-8")


def main():
    global OUT
    ap = argparse.ArgumentParser(description="Web UI for mini_bench.py")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--out", default="results.jsonl", help="results file (shared with mini_bench.py)")
    args = ap.parse_args()
    OUT = args.out

    # Bound to localhost only: the code-generation task executes model output,
    # so this should not be reachable from other machines.
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Open http://localhost:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
