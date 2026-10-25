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
# The web page (single HTML file, no external resources)
# --------------------------------------------------------------------------

PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mini LLM Bench</title>
<style>
  :root { --bg:#fafaf9; --fg:#1c1917; --muted:#78716c; --card:#fff; --border:#e7e5e4;
          --accent:#2563eb; --pass:#16a34a; --fail:#dc2626; --part:#d97706; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#161514; --fg:#f5f5f4; --muted:#a8a29e; --card:#1f1e1c; --border:#34312e;
            --accent:#60a5fa; --pass:#4ade80; --fail:#f87171; --part:#fbbf24; }
  }
  * { box-sizing: border-box; }
  body { font: 15px/1.5 system-ui, sans-serif; background: var(--bg); color: var(--fg);
         margin: 0; padding: 24px; }
  main { max-width: 900px; margin: 0 auto; }
  h1 { font-size: 22px; margin: 0 0 4px; }
  h2 { font-size: 16px; margin: 0 0 12px; }
  .sub { color: var(--muted); margin: 0 0 20px; }
  .card { background: var(--card); border: 1px solid var(--border); border-radius: 10px;
          padding: 16px; margin-bottom: 16px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }
  label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
  input { width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 6px;
          background: var(--bg); color: var(--fg); font: inherit; }
  .wide { grid-column: span 2; }
  .row { display: flex; gap: 8px; align-items: center; margin-top: 14px; flex-wrap: wrap; }
  button { padding: 8px 16px; border-radius: 6px; border: 1px solid var(--border);
           background: var(--card); color: var(--fg); font: inherit; cursor: pointer; }
  button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
  button:disabled { opacity: .5; cursor: not-allowed; }
  progress { flex: 1; min-width: 120px; height: 8px; }
  #status { font-size: 13px; color: var(--muted); }
  pre { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 10px;
        overflow-x: auto; white-space: pre-wrap; word-break: break-word; font-size: 13px; margin: 6px 0; }
  #log { max-height: 110px; overflow-y: auto; margin-top: 10px; }
  .scroll { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--border); }
  th { font-size: 12px; color: var(--muted); font-weight: 600; }
  td.cell { cursor: pointer; font-weight: 600; font-variant-numeric: tabular-nums; }
  td.cell:hover { background: var(--bg); }
  .md { margin: 6px 0; }
  .md p { margin: 6px 0; }
  .md pre { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 10px;
            overflow-x: auto; white-space: pre-wrap; word-break: break-word; font-size: 13px; margin: 6px 0; }
  .md code { font-family: ui-monospace, monospace; font-size: 12px; background: var(--bg);
             padding: 1px 4px; border-radius: 4px; }
  .md pre code { background: none; padding: 0; }
  .md ul, .md ol { margin: 6px 0 6px 20px; }
  .md h1, .md h2, .md h3, .md h4 { margin: 10px 0 4px; }
  .md blockquote { border-left: 3px solid var(--border); margin: 6px 0; padding-left: 10px; color: var(--muted); }
  .reason { font-size: 13px; font-weight: 600; margin: 2px 0 8px; }
  .preview { width: 100%; height: 420px; border: 1px solid var(--border); border-radius: 8px; margin: 6px 0 12px; background: #fff; }
  .note { font-size: 13px; color: var(--muted); font-style: italic; margin: 2px 0 8px; white-space: pre-wrap; }
  .pass { color: var(--pass); } .fail { color: var(--fail); } .part { color: var(--part); }
  .hint { font-size: 12px; color: var(--muted); margin: 10px 0 0; }
</style>
</head>
<body>
<main>
  <h1>Mini LLM Bench</h1>
  <p class="sub">6 tasks against a local llama-server. Run one model at a time and compare below.</p>

  <section class="card">
    <h2>Run</h2>
    <div class="grid">
      <div><label for="name">Model name (label for the table)</label>
           <input id="name" placeholder="auto-detected if empty">
           <button id="detect" type="button">Detect from server</button></div>
      <div class="wide"><label for="url">llama-server URL</label>
           <input id="url" value="http://localhost:8080"></div>
      <div><label for="runs">Runs per task</label>
           <input id="runs" type="number" min="1" max="20" value="1"></div>
      <div><label for="temp">Temperature</label>
           <input id="temp" type="number" min="0" max="2" step="0.1" value="0"></div>
      <div><label for="maxtok">Max tokens</label>
           <input id="maxtok" type="number" min="64" step="64" value="8192"></div>
      <div><label for="note">Notes for this run</label>
           <textarea id="note" rows="2" placeholder="optional notes saved with results"></textarea></div>
    </div>
    <div class="row">
      <button id="run" class="primary">Run benchmark</button>
      <progress id="bar" value="0" max="1"></progress>
      <span id="status">Idle</span>
    </div>
    <pre id="log" hidden></pre>
  </section>

  <section class="card">
    <h2>Results</h2>
    <p id="empty" class="sub">No results yet. Run a model above.</p>
    <div class="scroll"><table id="table"></table></div>
    <p class="hint">Click a cell to see the prompt and the model's raw output. Re-running a model
       with the same name replaces its row.</p>
    <div class="row"><button id="clear">Clear all results</button></div>
  </section>

  <section id="detail" class="card" hidden></section>
</main>

<script>
const $ = id => document.getElementById(id);
let TASKS = [], ROWS = [], wasRunning = false;
let detailContext = null, detailPage = 0;
const RUNS_PER_PAGE = 1;

function el(tag, text, cls) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;   // textContent: model output is never parsed as HTML
  if (cls) e.className = cls;
  return e;
}

async function api(path, body) {
  const opts = body === undefined ? undefined : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
  };
  return (await fetch(path, opts)).json();
}

function scoreClass(p, t) { return p === t ? 'pass' : p === 0 ? 'fail' : 'part'; }

function render() {
  const models = [...new Set(ROWS.map(r => r.model))];
  const table = $('table');
  table.replaceChildren();
  $('empty').hidden = models.length > 0;
  if (!models.length) return;

  const head = el('tr');
  head.append(el('th', 'model'));
  TASKS.forEach(t => head.append(el('th', t.id)));
  head.append(el('th', 'total'));
  table.append(head);

  models.forEach(m => {
    const tr = el('tr');
    tr.append(el('td', m));
    let tp = 0, tt = 0;
    TASKS.forEach(t => {
      const rs = ROWS.filter(r => r.model === m && r.task === t.id);
      const p = rs.filter(r => r.passed).length;
      tp += p; tt += rs.length;
      const td = el('td', rs.length ? `${p}/${rs.length}` : '-', 'cell ' + (rs.length ? scoreClass(p, rs.length) : ''));
      td.onclick = () => showDetail(m, t);
      tr.append(td);
    });
    tr.append(el('td', `${tp}/${tt}`, 'cell ' + (tt ? scoreClass(tp, tt) : '')));
    table.append(tr);
  });
}

function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function inlineMd(s) {
  s = escapeHtml(s);
  s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
  return s;
}

function renderMarkdown(src) {
  if (src === null || src === undefined) return '';
  const lines = String(src).split(/\n/);
  let html = '';
  let inCode = false;
  let codeLang = '';
  let codeLines = [];
  let inList = false;
  let listType = '';
  function closeList() {
    if (inList) { html += '</' + listType + '>'; inList = false; listType = ''; }
  }
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const fence = line.match(/^```(\w*)\s*$/);
    if (fence) {
      if (!inCode) {
        closeList();
        inCode = true;
        codeLang = fence[1] || '';
        codeLines = [];
      } else {
        html += '<pre><code' + (codeLang ? ' class="language-' + escapeHtml(codeLang) + '"' : '') + '>' +
                escapeHtml(codeLines.join('\n')) + '</code></pre>';
        inCode = false;
      }
      continue;
    }
    if (inCode) { codeLines.push(line); continue; }
    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      closeList();
      const lvl = heading[1].length;
      html += '<h' + lvl + '>' + inlineMd(heading[2]) + '</h' + lvl + '>';
      continue;
    }
    const bq = line.match(/^>\s?(.*)$/);
    if (bq) { closeList(); html += '<blockquote>' + inlineMd(bq[1]) + '</blockquote>'; continue; }
    const ul = line.match(/^[-*+]\s+(.*)$/);
    if (ul) {
      if (!inList || listType !== 'ul') { closeList(); html += '<ul>'; inList = true; listType = 'ul'; }
      html += '<li>' + inlineMd(ul[1]) + '</li>';
      continue;
    }
    const ol = line.match(/^\d+\.\s+(.*)$/);
    if (ol) {
      if (!inList || listType !== 'ol') { closeList(); html += '<ol>'; inList = true; listType = 'ol'; }
      html += '<li>' + inlineMd(ol[1]) + '</li>';
      continue;
    }
    if (line.trim() === '') { closeList(); continue; }
    closeList();
    html += '<p>' + inlineMd(line) + '</p>';
  }
  if (inCode) html += '<pre><code>' + escapeHtml(codeLines.join('\n')) + '</code></pre>';
  closeList();
  return html;
}

function extractHtml(src) {
  const m = String(src || '').match(/```html\\s*([\\s\\S]*?)```/i);
  if (m) return m[1].trim();
  if (/<html[\\s>]/i.test(src) || /<!DOCTYPE\\s+html/i.test(src)) return String(src).trim();
  return null;
}


function renderDetailRun(r, index) {
  const d = $('detailRuns');
  const outDiv = document.createElement('div');
  outDiv.className = 'md';
  outDiv.innerHTML = renderMarkdown(r.output || '(empty output)');
  const reasonEl = document.createElement('div');
  reasonEl.className = 'reason ' + (r.passed ? 'pass' : 'fail');
  reasonEl.textContent = r.reason || (r.passed ? 'PASS' : 'FAIL');
  d.append(el('label', `Run ${index + 1}: ${r.passed ? 'PASS' : 'FAIL'}`), reasonEl);
  if (r.note) {
    const noteEl = el('div', 'Note: ' + r.note, 'note');
    d.append(noteEl);
  }
  const html = extractHtml(r.output);
  let frame = null;
  if (html) {
    const btnRow = document.createElement('div');
    btnRow.className = 'row';
    const openBtn = el('button', 'Open HTML in new tab');
    openBtn.onclick = () => {
      const blob = new Blob([html], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      window.open(url, '_blank');
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    };
    const toggleBtn = el('button', 'Render HTML inline');
    frame = document.createElement('iframe');
    frame.className = 'preview';
    frame.srcdoc = html;
    frame.hidden = true;
    toggleBtn.onclick = () => {
      frame.hidden = !frame.hidden;
      toggleBtn.textContent = frame.hidden ? 'Render HTML inline' : 'Hide inline HTML';
    };
    btnRow.append(openBtn, toggleBtn);
    d.append(btnRow);
  }
  d.append(outDiv);
  if (frame) d.append(frame);
}

function updateDetailRuns() {
  if (!detailContext) return;
  const container = $('detailRuns');
  const pager = $('detailPager');
  if (!container || !pager) return;
  container.replaceChildren();
  pager.replaceChildren();
  const runs = detailContext.runs;
  const totalPages = Math.max(1, Math.ceil(runs.length / RUNS_PER_PAGE));
  if (detailPage >= totalPages) detailPage = totalPages - 1;
  if (detailPage < 0) detailPage = 0;
  const start = detailPage * RUNS_PER_PAGE;
  runs.slice(start, start + RUNS_PER_PAGE).forEach((r, i) => renderDetailRun(r, start + i));
  if (runs.length > RUNS_PER_PAGE) {
    const prev = el('button', 'Prev');
    prev.disabled = detailPage === 0;
    prev.onclick = () => { detailPage--; updateDetailRuns(); };
    const info = el('span', `Page ${detailPage + 1} / ${totalPages}`);
    info.style.margin = '0 8px';
    const next = el('button', 'Next');
    next.disabled = detailPage === totalPages - 1;
    next.onclick = () => { detailPage++; updateDetailRuns(); };
    pager.append(prev, info, next);
  }
}

function showDetail(model, task) {
  const d = $('detail');
  const promptDiv = document.createElement('div');
  promptDiv.className = 'md';
  promptDiv.innerHTML = renderMarkdown(task.prompt);
  const runsContainer = document.createElement('div');
  runsContainer.id = 'detailRuns';
  const pager = document.createElement('div');
  pager.id = 'detailPager';
  pager.className = 'row';
  d.replaceChildren(el('h2', `${model} / ${task.id}`), el('label', 'Prompt'), promptDiv, pager, runsContainer);
  detailContext = { model, task, runs: ROWS.filter(r => r.model === model && r.task === task.id) };
  detailPage = 0;
  updateDetailRuns();
  d.hidden = false;
  d.scrollIntoView({ behavior: 'smooth' });
}

async function loadResults() {
  ROWS = await api('/api/results');
  if (detailContext) {
    detailContext.runs = ROWS.filter(r => r.model === detailContext.model && r.task === detailContext.task);
    updateDetailRuns();
  }
  render();
}

async function poll() {
  try {
    const s = await api('/api/status');
    $('run').disabled = s.running;
    $('bar').value = s.total ? s.done / s.total : 0;
    $('status').textContent = s.running ? `Running ${s.model}: ${s.done}/${s.total}`
      : s.error ? 'Error: ' + s.error
      : s.total ? `Finished ${s.model}` : 'Idle';
    $('log').hidden = !s.log.length;
    $('log').textContent = s.log.join('\n');
    if (s.running || wasRunning) await loadResults();
    wasRunning = s.running;
  } catch (e) { $('status').textContent = 'Cannot reach web_bench.py server'; }
}

$('detect').onclick = async () => {
  const url = $('url').value.trim();
  if (!url) { alert('enter a server URL first'); return; }
  try {
    const res = await api('/api/detect_model?url=' + encodeURIComponent(url));
    if (res.error) alert(res.error); else $('name').value = res.name;
  } catch (e) { alert('detection failed'); }
};

$('run').onclick = async () => {
  const res = await api('/api/run', {
    name: $('name').value, url: $('url').value, runs: $('runs').value,
    temperature: $('temp').value, max_tokens: $('maxtok').value,
    note: $('note').value
  });
  if (res.error) alert(res.error);
  poll();
};

$('clear').onclick = async () => {
  if (!confirm('Delete all saved results?')) return;
  const res = await api('/api/clear', {});
  if (res.error) alert(res.error);
  $('detail').hidden = true;
  loadResults();
};

(async () => { TASKS = await api('/api/tasks'); await loadResults(); await poll(); setInterval(poll, 1000); })();
</script>
</body>
</html>
"""


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
