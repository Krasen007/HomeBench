#!/usr/bin/env python3
"""
mini_bench.py - a tiny 7-task LLM benchmark for llama.cpp (llama-server).
Only needs Python 3.8+ (standard library, no pip installs).

1) Start one llama-server per model (different ports):
     llama-server -m qwen2.5-3b-instruct-q4_k_m.gguf --port 8080
     llama-server -m llama-3.2-3b-instruct-q4_k_m.gguf --port 8081

2) Run the benchmark:
     python mini_bench.py --model qwen=http://localhost:8080 --model llama=http://localhost:8081

   Low on RAM? Run one server at a time and call the script once per model.
   Results accumulate in results.jsonl; print the combined table anytime with:
     python mini_bench.py --report
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

from tasks import TASKS
# Backward-compatible aliases for the extracted task check/explain functions.
from tasks import math as _t_math, logic as _t_logic, instructions as _t_instructions
from tasks import json_task as _t_json, code_task as _t_code, game as _t_game
from tasks import bulgarian as _t_bg

check_math, explain_math = _t_math.check, _t_math.explain
check_logic, explain_logic = _t_logic.check, _t_logic.explain
check_instructions, explain_instructions = _t_instructions.check, _t_instructions.explain
check_json, explain_json = _t_json.check, _t_json.explain
check_code, explain_code = _t_code.check, _t_code.explain
check_game, explain_game = _t_game.check, _t_game.explain
check_bg_article, explain_bg_article = _t_bg.check, _t_bg.explain


# --------------------------------------------------------------------------
# Talking to llama-server (OpenAI-compatible endpoint)
# --------------------------------------------------------------------------

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
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    text = re.sub(r"<think>.*$", "", text, flags=re.S)  # truncated, never closed
    return text.strip()


# --------------------------------------------------------------------------
# Running and reporting
# --------------------------------------------------------------------------

def report(rows):
    if not rows:
        print("No results yet.")
        return
    models = list(dict.fromkeys(r["model"] for r in rows))
    # If a model was run several times, only show its most recent batch
    latest = {m: max(r["batch"] for r in rows if r["model"] == m) for m in models}
    rows = [r for r in rows if r["batch"] == latest[r["model"]]]

    ids = [t["id"] for t in TASKS]
    w = max(len(m) for m in models + ["model"])
    print("\n" + "model".ljust(w) + "  " + "  ".join(i.ljust(12) for i in ids) + "  total")
    print("-" * (w + 2 + 14 * len(ids) + 7))
    for m in models:
        cells, tp, tt = [], 0, 0
        for t in ids:
            rs = [r for r in rows if r["model"] == m and r["task"] == t]
            p = sum(r["passed"] for r in rs)
            cells.append(f"{p}/{len(rs)}".ljust(12))
            tp, tt = tp + p, tt + len(rs)
        print(m.ljust(w) + "  " + "  ".join(cells) + f"  {tp}/{tt}")


def load_rows(path):
    try:
        with open(path) as f:
            return [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        return []


def infer_model_name(base_url):
    """Best-effort model name from a llama-server (OpenAI-compatible) endpoint."""
    base = base_url.rstrip("/")
    try:
        with urllib.request.urlopen(base + "/v1/models", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8", "replace"))
        models = data.get("data") or data.get("models") or []
        if models:
            m = models[0]
            for key in ("id", "name", "model", "path"):
                if m.get(key):
                    return str(m[key])
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


def unique_model_name(name, existing):
    name = (name or "").strip()
    if not name:
        return name
    if name not in existing:
        return name
    i = 2
    while "%s-%d" % (name, i) in existing:
        i += 1
    return "%s-%d" % (name, i)


def main():
    ap = argparse.ArgumentParser(description="Tiny LLM benchmark for llama-server")
    ap.add_argument("--model", action="append", default=[], metavar="NAME=URL",
                    help="e.g. qwen=http://localhost:8080 or just http://localhost:8080 (name auto-detected); repeatable")
    ap.add_argument("--runs", type=int, default=1, help="runs per task (default 1)")
    ap.add_argument("--temperature", type=float, default=0.0,
                    help="default 0. Use >0 (e.g. 0.7) with --runs 3 to test consistency")
    ap.add_argument("--max-tokens", type=int, default=8192)
    ap.add_argument("--timeout", type=int, default=300, help="seconds per request")
    ap.add_argument("--out", default="results.jsonl")
    ap.add_argument("--report", action="store_true", help="just print the saved results")
    args = ap.parse_args()

    if args.report:
        report(load_rows(args.out))
        return
    if not args.model:
        ap.error("give at least one --model NAME=URL (or use --report)")

    with open(args.out, "a") as out:
        for spec in args.model:
            if "=" in spec:
                name, _, url = spec.partition("=")
            else:
                name, url = "", spec
            name, url = name.strip(), url.strip()
            if not url:
                url, name = name, ""
            if not name:
                name = infer_model_name(url) or "model"
            existing = {r["model"] for r in load_rows(args.out)}
            name = unique_model_name(name, existing)
            batch = int(time.time())
            print(f"\n== {name} ({url}) ==")
            for task in TASKS:
                for run in range(args.runs):
                    try:
                        output = chat(url, task["prompt"], args.temperature,
                                      args.max_tokens, args.timeout)
                        passed = bool(task["check"](output))
                        reason = task.get("explain", lambda x: "")(output)
                    except Exception as e:  # server down, timeout, bad response...
                        output, passed, reason = f"[ERROR] {e}", False, "FAIL: " + str(e)
                    print(f"  {task['id']:<13} run {run + 1}: {'PASS' if passed else 'FAIL'} - {reason}")
                    out.write(json.dumps({
                        "batch": batch, "model": name, "task": task["id"],
                        "run": run, "passed": passed, "reason": reason, "output": output,
                    }) + "\n")
                    out.flush()

    report(load_rows(args.out))
    print(f"\nRaw outputs saved in {args.out} (inspect FAILs before trusting them).")


if __name__ == "__main__":
    main()
