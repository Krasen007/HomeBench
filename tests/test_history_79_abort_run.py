"""History: Abort run button cancels the remaining benchmark queue."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock

import homebench


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
SOURCE = (ROOT / "homebench.py").read_text(encoding="utf-8")


def _handler(body, path="/api/abort"):
    handler = homebench.Handler.__new__(homebench.Handler)
    payload = json.dumps(body).encode()
    handler.path = path
    handler.headers = {"Content-Length": str(len(payload))}
    handler.rfile = io.BytesIO(payload)
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = io.BytesIO()
    return handler


def test_abort_button_sits_next_to_skip():
    assert 'id="abort"' in HTML
    assert ">Abort run</button>" in HTML
    assert "id=\"skip\" type=\"button\">Skip task</button>" in HTML


def test_abort_button_calls_the_abort_endpoint():
    assert "api('/api/abort', {})" in HTML
    assert "$('abort').hidden = !s.running;" in HTML
    assert "$('abort').textContent = 'Abort run';" in HTML


def test_abort_endpoint_requires_a_running_benchmark():
    previous_running = homebench.state["running"]
    previous_abort = homebench.state["abort"]
    homebench.state["running"] = False
    homebench.state["abort"] = False
    try:
        handler = _handler({})
        handler.do_POST()
        assert handler.send_response.call_args.args[0] == 409
        assert json.loads(handler.wfile.getvalue())["error"] == "no benchmark is running"

        homebench.state["running"] = True
        handler = _handler({})
        handler.do_POST()
        assert json.loads(handler.wfile.getvalue()) == {"ok": True}
        assert homebench.state["abort"] is True
    finally:
        homebench.state["running"] = previous_running
        homebench.state["abort"] = previous_abort


def test_run_benchmark_stops_after_abort(monkeypatch, tmp_path):
    monkeypatch.setattr(homebench, "chat", lambda *args, **kwargs: "42")
    flags = {"aborted": False}

    def on_result(*args, **kwargs):
        flags["aborted"] = True

    path = tmp_path / "results.jsonl"
    homebench.run_benchmark(
        "http://x", "m", 5, 0.0, 8, 5, str(path),
        task_ids=["math"], on_result=on_result,
        should_abort=lambda: flags["aborted"])

    assert len(homebench.load_rows(str(path))) == 1


def test_run_benchmark_discards_in_flight_row_when_aborted(monkeypatch, tmp_path):
    flags = {"aborted": False}

    def fake_chat(*args, should_skip=None, **kwargs):
        flags["aborted"] = True
        if should_skip is not None and should_skip():
            return ""
        return "42"

    monkeypatch.setattr(homebench, "chat", fake_chat)
    path = tmp_path / "results.jsonl"
    homebench.run_benchmark(
        "http://x", "m", 2, 0.0, 8, 5, str(path),
        task_ids=["math"], should_skip=lambda: flags["aborted"],
        should_abort=lambda: flags["aborted"])

    assert homebench.load_rows(str(path)) == []


def test_run_benchmark_plans_stops_between_plans(monkeypatch):
    flags = {"aborted": False}
    calls = []

    def fake_run(url, name, runs, temperature, max_tokens, timeout, out_path, **kwargs):
        calls.append(name)
        flags["aborted"] = True
        return 0

    monkeypatch.setattr(homebench, "run_benchmark", fake_run)
    monkeypatch.setattr(homebench, "load_rows", lambda path: [])

    homebench.run_benchmark_plans(
        "http://x", "m",
        [{"temperature": 0.0, "runs": 1}, {"temperature": 0.6, "runs": 1}],
        8, 5, "unused", should_abort=lambda: flags["aborted"])

    assert len(calls) == 1
