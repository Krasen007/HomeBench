#!/usr/bin/env python3
"""
mini_bench.py - a tiny 6-task LLM benchmark for llama.cpp (llama-server).
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

# --------------------------------------------------------------------------
# Scoring functions: each takes the model's text output, returns True/False
# --------------------------------------------------------------------------

def _math_status(text):
    # 18 pencils = 6 groups of 3 -> $7.20; change from $10 = $2.80
    nums = re.findall(r"answer\s*:\s*\$?\s*(-?\d+(?:\.\d+)?)", text, re.I)
    if not nums:
        return False, "FAIL: no 'Answer: <number>' found"
    got = float(nums[-1])
    if abs(got - 2.80) < 0.005:
        return True, "PASS: answer is 2.80"
    return False, "FAIL: expected 2.80, got %g" % got


def check_math(text):
    return _math_status(text)[0]


def explain_math(text):
    return _math_status(text)[1]


def _logic_status(text):
    # Bob must own the cat, so Alice owns the fish
    names = re.findall(r"answer\s*:\s*\**\s*(\w+)", text, re.I)
    if not names:
        return False, "FAIL: no 'Answer: <name>' found"
    got = names[-1]
    if got.lower() == "alice":
        return True, "PASS: answer is Alice"
    return False, "FAIL: expected Alice, got %s" % got


def check_logic(text):
    return _logic_status(text)[0]


def explain_logic(text):
    return _logic_status(text)[1]


def _instructions_status(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if len(lines) != 3:
        return False, "FAIL: expected exactly 3 non-empty lines, got %d" % len(lines)
    for i, line in enumerate(lines, 1):
        if not re.match(r"^[-*\u2022]\s+", line):
            return False, "FAIL: line %d does not start with '- '" % i
        words = re.sub(r"^[-*\u2022]\s+", "", line).split()
        if not 0 < len(words) < 8:
            return False, "FAIL: line %d has %d words (need 1-7)" % (i, len(words))
    return True, "PASS: 3 bullets, each '- ' prefix, 1-7 words"


def check_instructions(text):
    return _instructions_status(text)[0]


def explain_instructions(text):
    return _instructions_status(text)[1]


def _json_status(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return False, "FAIL: no JSON object found"
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        return False, "FAIL: invalid JSON (%s)" % e
    expected = {
        "name": "Maria Lopez",
        "age": 34,
        "company": "Acme Corp",
        "start_date": "2021-03-15",
        "city": "Valencia",
    }
    mismatches = []
    for k, v in expected.items():
        if str(data.get(k, "")).strip() != str(v):
            mismatches.append("%s: expected %r, got %r" % (k, v, data.get(k)))
    if mismatches:
        return False, "FAIL: " + "; ".join(mismatches)
    return True, "PASS: all fields match"


def check_json(text):
    return _json_status(text)[0]


def explain_json(text):
    return _json_status(text)[1]


def _code_status(text):
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
    code = m.group(1) if m else text
    tests = '''
cases = [("A man, a plan, a canal: Panama", True), ("race a car", False),
         ("", True), ("No 'x' in Nixon", True), ("ab", False), ("12321", True)]
for s, expected in cases:
    assert is_palindrome(s) == expected, (s, expected)
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code + "\n" + tests)
        path = f.name
    try:
        # NOTE: this executes model-generated code. Fine for a demo of simple
        # tasks, but run it in a container/VM if you extend the benchmark.
        r = subprocess.run([sys.executable, path], capture_output=True, timeout=10)
        if r.returncode == 0:
            return True, "PASS: all palindrome test cases passed"
        err = (r.stderr or r.stdout or b"").decode(errors="replace").strip()
        if err:
            return False, "FAIL: tests failed: " + err.splitlines()[-1]
        return False, "FAIL: tests failed (non-zero exit)"
    except subprocess.TimeoutExpired:
        return False, "FAIL: execution timed out"
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def check_code(text):
    return _code_status(text)[0]


def explain_code(text):
    return _code_status(text)[1]


def _browser_executable():
    import shutil
    env = os.environ.get("BROWSER_BIN") or os.environ.get("CHROME_BIN")
    if env and os.path.exists(env):
        return env
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    for name in ("msedge", "chrome", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _inject_runtime_checks(html):
    capture = ("<script>window.__errors=[];window.__bench_interaction=null;"
               "window.__bench_refresh_status=function(){var d=document.getElementById('__bench_status');"
               "if(d)d.textContent=window.__errors.length?'ERROR: '+window.__errors.join('; '):"
               "window.__bench_interaction===true?'OK':'ERROR: no observable game-state change after interaction';};"
               "window.addEventListener('error',function(e){window.__errors.push(e.message||String(e));"
               "window.__bench_refresh_status();});"
               "window.addEventListener('unhandledrejection',function(e){"
               "window.__errors.push('Promise: '+(e.reason&&(e.reason.message||e.reason)||e.reason));"
               "window.__bench_refresh_status();});"
               "</script>")
    interact = ("<script>window.addEventListener('load',function(){"
                "setTimeout(function(){try{"
                "function snapshot(){var s=document.body?document.body.innerHTML:'';"
                "Array.from(document.querySelectorAll('canvas')).forEach(function(c){"
                "try{s+='|canvas:'+c.toDataURL();}catch(e){s+='|canvas-size:'+c.width+'x'+c.height;}});"
                "return s;}"
                "var before=snapshot();"
                "var bs=Array.from(document.querySelectorAll('button'));"
                "var play=bs.find(function(b){return /play/i.test(b.textContent||'');});"
                "if(play)play.click();"
                "var c=document.querySelector('canvas');"
                "if(c){var ev=new MouseEvent('mousemove',{clientX:120,clientY:120,bubbles:true});c.dispatchEvent(ev);}"
                "setTimeout(function(){window.__bench_interaction=snapshot()!==before;"
                "window.__bench_refresh_status();},500);"
                "}catch(e){window.__errors.push('interact: '+(e.message||e));"
                "window.__bench_interaction=false;window.__bench_refresh_status();}"
                "},1000);});</script>")
    status = ("<script>window.addEventListener('load',function(){"
              "setTimeout(function(){var d=document.createElement('div');d.id='__bench_status';"
              "document.body.appendChild(d);window.__bench_refresh_status();},4000);});</script>")
    if re.search(r"<head[^>]*>", html, re.I):
        html = re.sub(r"(<head[^>]*>)", r"\1" + capture, html, count=1, flags=re.I)
    elif re.search(r"<body[^>]*>", html, re.I):
        html = re.sub(r"(<body[^>]*>)", capture + r"\1", html, count=1, flags=re.I)
    else:
        html = capture + html
    if re.search(r"</body>", html, re.I):
        html = re.sub(r"</body>", interact + status + "</body>", html, count=1, flags=re.I)
    else:
        html = html + interact + status
    return html


def _game_runtime_status(html):
    browser = _browser_executable()
    if not browser:
        return None, "runtime check skipped (no browser found)"
    injected = _inject_runtime_checks(html)
    fd, path = tempfile.mkstemp(suffix=".html")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(injected)
        url = "file:///" + path.replace("\\", "/")
        try:
            r = subprocess.run(
                [browser, "--headless=new", "--disable-gpu",
                 "--virtual-time-budget=6000", "--dump-dom", url],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=30)
        except subprocess.TimeoutExpired:
            return False, "FAIL: runtime check timed out"
        out = r.stdout or ""
        mm = re.search(r'<div[^>]*id="__bench_status"[^>]*>(.*?)</div>',
                       out, re.S | re.I)
        if not mm:
            # fall back: any uncaught error text in stdout
            if "Uncaught" in out or "ERROR:" in out:
                return False, "FAIL: runtime error detected"
            return None, "runtime check inconclusive (no status)"
        status = mm.group(1).strip()
        if status.startswith("ERROR:"):
            msg = status[len("ERROR:"):].strip()
            return False, "FAIL: runtime error: " + (msg or "unknown")
        return True, "PASS: runs without runtime errors"
    except Exception as e:
        return None, "runtime check skipped (%s)" % e
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def _game_status(text):
    # Extract the HTML document from the model output (code block or raw).
    m = re.search(r"```(?:html|htm)?\s*\n(.*?)```", text, re.S | re.I)
    html = m.group(1).strip() if m else text.strip()
    low = html.lower()

    # Must be an HTML document.
    if "<html" not in low and "<!doctype" not in low and "<canvas" not in low:
        return False, "FAIL: not an HTML document"

    # Core elements / content from the design document.
    for token in ("canvas", "car", "coin", "yellow", "red", "green", "grass",
                  "play", "200"):
        if token not in low:
            return False, "FAIL: missing required element/content '%s'" % token

    # Sound: generated audio for pickups.
    if not any(s in low for s in ("audiocontext", "oscillator", "audio", "sound",
                                  "beep", "tone", "webaudio")):
        return False, "FAIL: no generated sound (audio) found"

    # Input: mouse or touch control.
    if not any(s in low for s in ("mousemove", "touchmove", "pointermove",
                                  "mousedown", "touchstart", "pointerdown")):
        return False, "FAIL: no mouse/touch input handler found"

    # Spawning logic present.
    if not any(s in low for s in ("spawn", "setinterval", "settimeout")):
        return False, "FAIL: no coin spawning logic found"

    # Single self-contained file: no external script/style dependencies.
    if re.search(r"<script[^>]*\bsrc\s*=", html, re.I):
        return False, "FAIL: uses external script (src=) - not a single file"

    # JavaScript syntax check on inline scripts.
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S | re.I)
    js = "\n".join(scripts)
    if js.strip():
        fd, path = tempfile.mkstemp(suffix=".js")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(js)
            r = subprocess.run(["node", "--check", path], capture_output=True,
                               timeout=10)
            if r.returncode != 0:
                err = (r.stderr or b"").decode(errors="replace").strip()
                msg = err.splitlines()[-1] if err else "syntax error"
                return False, "FAIL: JS syntax error: " + msg
        except Exception as e:
            return False, "FAIL: could not check JS (%s)" % e
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    # Runtime playability check: load in a headless browser, click play, and
    # ensure no uncaught errors are thrown.
    rt_ok, rt_reason = _game_runtime_status(html)
    if rt_ok is False:
        return False, rt_reason
    if rt_ok is None:
        return False, "INCONCLUSIVE: " + rt_reason
    return True, "PASS: valid single-file HTML game with all required elements (runtime OK)"


def check_game(text):
    return _game_status(text)[0]


def explain_game(text):
    return _game_status(text)[1]


# --------------------------------------------------------------------------
# The tasks
# --------------------------------------------------------------------------

TASKS = [
    {
        "id": "math",
        "prompt": (
            "Maya buys 18 pencils. The shop sells pencils at 3 for $1.20. "
            "She pays with a $10 bill. How much change does she get, in dollars? "
            "Think step by step, then end with a final line in the form "
            "'Answer: <number>'."
        ),
        "check": check_math,
        "explain": explain_math,
    },
    {
        "id": "logic",
        "prompt": (
            "Alice, Bob and Carol each own exactly one pet: a cat, a dog, or a "
            "fish, and no two own the same pet. Alice does not own the dog. "
            "Bob owns neither the dog nor the fish. Who owns the fish? "
            "Reason briefly, then end with a final line in the form "
            "'Answer: <name>'."
        ),
        "check": check_logic,
        "explain": explain_logic,
    },
    {
        "id": "instructions",
        "prompt": (
            "Give me exactly 3 bullet points about the benefits of sleep. "
            "Each bullet must start with '- ' and contain fewer than 8 words. "
            "Output nothing except the 3 bullets."
        ),
        "check": check_instructions,
        "explain": explain_instructions,
    },
    {
        "id": "json",
        "prompt": (
            "Extract information from the text below and reply with only a JSON "
            "object with keys: name (string), age (integer), company (string), "
            "start_date (YYYY-MM-DD), city (string).\n\n"
            "Text: Maria Lopez, 34, joined Acme Corp as a data engineer on "
            "March 15, 2021. She currently lives in Valencia."
        ),
        "check": check_json,
        "explain": explain_json,
    },
    {
        "id": "code",
        "prompt": (
            "Write a Python function `is_palindrome(s: str) -> bool` that returns "
            "True if s reads the same forwards and backwards, ignoring case and "
            "any non-alphanumeric characters. Reply with only the code in a "
            "single ```python block."
        ),
        "check": check_code,
        "explain": explain_code,
    },
    {
        "id": "game",
        "prompt": (
            "Create a single-file HTML5 game for a 3-year-old toddler following this "
            "design document exactly:\n\n"
            "Generate a 2d game for my 3 year old toddler.\n\n"
            "The gameplay is as follows:\n"
            "1. you use the mouse or touch to move a car on the screen.\n"
            "2. there are Yellow coins spawning every 1 to 2 seconds.\n"
            "3. maximum number of yellow coins on the screen at any given time is 5.\n"
            "3a. if you collect the yellow coins faster than the spawning speed, then "
            "the spawning speed decreases to 0.3 to 0.8 sec. to allow for faster "
            "yellow coins appearing on the screen.\n"
            "4. after 5 to 10 yellow (random number each time 5-10) coins are "
            "collected a Red coin appears.\n"
            "4a. every next red coin should appear after 5 to 10 (random 5-10) "
            "yellow coins are collected.\n"
            "5. after 2 red coins are collected a cluster of 5 Green coins appears.\n\n"
            "Win condition:\n"
            "After 200 total coins are collected the game ends.\n\n"
            "Constraints:\n"
            "Single HTML File (index.html)\n\n"
            "State:\n"
            "Main menu with a single play button which starts the game.\n\n"
            "Visual style:\n"
            "Bright and cartoony style, bright colors. Grass. Flags.\n\n"
            "Sound:\n"
            "Generated sounds for coin pickup.\n"
            "Different sound for the different color coins.\n\n"
            "Requirements:\n"
            "- Output ONLY the complete index.html inside a single ```html code block.\n"
            "- The file must be fully self-contained (inline CSS and JS, no external "
            "dependencies or CDN links).\n"
            "- Implement every gameplay rule, the win condition, the main menu, the "
            "visual style, and the generated sounds."
        ),
        "check": check_game,
        "explain": explain_game,
    },
]

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
