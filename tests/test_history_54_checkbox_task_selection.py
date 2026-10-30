"""History: allow selecting a subset of benchmark tasks with checkboxes."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import homebench


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def _handler(body):
    handler = homebench.Handler.__new__(homebench.Handler)
    payload = json.dumps(body).encode()
    handler.path = "/api/run"
    handler.headers = {"Content-Length": str(len(payload))}
    handler.rfile = io.BytesIO(payload)
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = io.BytesIO()
    return handler


def _reset_state():
    homebench.state.update({
        "running": False, "model": "", "done": 0, "total": 0, "log": [],
        "error": None, "plan": 0, "plans": 0,
    })


def test_web_ui_builds_checked_task_options_and_sends_selection():
    assert 'id="taskAll" type="checkbox" checked' in HTML
    assert 'id="taskOptions"' in HTML
    assert "checkbox.checked = true;" in HTML
    assert "function selectedTaskIds()" in HTML
    assert "if (!tasks.length)" in HTML
    assert "tasks," in HTML
    assert "task: $('task').value" not in HTML


def test_run_endpoint_queues_only_selected_tasks_and_adjusts_progress(
        tmp_path, monkeypatch):
    monkeypatch.setattr(homebench, "WEB_OUT", str(tmp_path / "results.jsonl"))
    body = {
        "name": "model",
        "url": "http://localhost:1234",
        "tasks": ["math", "game"],
        "plans": [{"temperature": 0, "runs": 2}],
    }
    handler = _handler(body)
    try:
        with patch("homebench.threading.Thread") as thread:
            handler.do_POST()
        response = json.loads(handler.wfile.getvalue())
        assert response["total"] == 4
        assert homebench.state["total"] == 4

        calls = []

        def fake_run(url, name, runs, temperature, max_tokens, timeout,
                     out_path, note="", on_result=None, task_id=None,
                     task_ids=None, on_token=None):
            calls.append(task_ids)

        with patch("homebench.run_benchmark", side_effect=fake_run):
            thread.call_args.kwargs["target"]()

        assert calls == [["math", "game"]]
    finally:
        _reset_state()


def test_run_endpoint_rejects_empty_unknown_or_duplicate_task_selections(
        tmp_path, monkeypatch):
    monkeypatch.setattr(homebench, "WEB_OUT", str(tmp_path / "results.jsonl"))
    for selection in ([], ["missing"], ["math", "math"]):
        handler = _handler({
            "name": "model",
            "url": "http://localhost:1234",
            "tasks": selection,
            "plans": [{"temperature": 0, "runs": 1}],
        })
        with patch("homebench.threading.Thread") as thread:
            handler.do_POST()
        thread.assert_not_called()
        assert handler.send_response.call_args.args[0] == 400
        _reset_state()


def test_benchmark_core_runs_selected_task_ids_only(tmp_path, monkeypatch):
    tasks = [
        {"id": "math", "prompt": "", "check": lambda _: True},
        {"id": "logic", "prompt": "", "check": lambda _: True},
        {"id": "game", "prompt": "", "check": lambda _: True},
    ]
    monkeypatch.setattr(homebench, "TASKS", tasks)
    monkeypatch.setattr(homebench, "chat", lambda *args: "result")
    out = tmp_path / "results.jsonl"

    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0, 100, 10, out,
        task_ids=["math", "game"],
    )

    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert [row["task"] for row in rows] == ["math", "game"]
