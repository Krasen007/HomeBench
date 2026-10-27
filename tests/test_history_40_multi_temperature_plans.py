"""History: multi-temperature run plans, queued execution, and elapsed time.

The web UI replaces the single temperature input with a list of plans
("1 × at 0.0", "3 × at 0.6", ...); Run Benchmark queues every plan, each run
records its elapsed seconds, and the results table shows an average time
column.
"""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import homebench

ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Web UI
# ---------------------------------------------------------------------------

def test_single_temperature_and_runs_inputs_are_gone():
    assert 'id="temp"' not in HTML
    assert 'id="runs"' not in HTML


def test_web_ui_has_multi_plan_editor():
    assert 'id="plans"' in HTML
    assert 'id="addPlan"' in HTML
    assert "function addPlanRow(" in HTML
    assert "function readPlans()" in HTML
    assert "'× at'" in HTML
    assert "addPlanRow(1, 0.0);" in HTML


def test_run_button_sends_every_plan_in_one_request():
    assert "const plans = readPlans();" in HTML
    assert "plans," in HTML
    assert "api('/api/run'" in HTML
    assert "runs: $('runs').value" not in HTML
    assert "temperature: $('temp').value" not in HTML


def test_results_table_has_elapsed_average_column():
    assert "el('th', 'avg time')" in HTML
    assert "formatSeconds(avgTime)" in HTML
    assert "formatSeconds(Number(r.elapsed))" in HTML


# ---------------------------------------------------------------------------
# parse_plans
# ---------------------------------------------------------------------------

def test_parse_plans_normalizes_values():
    plans = homebench.parse_plans([
        {"temperature": 0, "runs": 1},
        {"temperature": "0.6", "runs": "3"},
        {"temperature": 1.0, "runs": 3},
    ])
    assert plans == [
        {"temperature": 0.0, "runs": 1},
        {"temperature": 0.6, "runs": 3},
        {"temperature": 1.0, "runs": 3},
    ]


def test_parse_plans_rejects_invalid_input():
    for raw in ([], None, "0.6",
                [{"temperature": -0.1, "runs": 1}],
                [{"temperature": 2.1, "runs": 1}],
                [{"temperature": 0.6, "runs": 0}],
                [{"temperature": 0.6, "runs": homebench.MAX_PLAN_RUNS + 1}],
                [{"temperature": "warm", "runs": 1}],
                ["not-an-object"]):
        try:
            homebench.parse_plans(raw)
        except ValueError:
            continue
        raise AssertionError(f"parse_plans accepted invalid input: {raw!r}")



# ---------------------------------------------------------------------------
# run_benchmark_plans — executes every plan and records elapsed time
# ---------------------------------------------------------------------------

def test_run_benchmark_plans_runs_each_plan_and_records_elapsed(tmp_path):
    out = tmp_path / "results.jsonl"
    plans = [
        {"temperature": 0.0, "runs": 1},
        {"temperature": 0.6, "runs": 3},
        {"temperature": 1.0, "runs": 2},
    ]
    with patch("homebench.chat", return_value="Answer: 2.80"):
        jobs = homebench.run_benchmark_plans(
            "http://localhost:1234", "qwen", plans, 256, 30, str(out),
            note="sweep", task_id="math",
        )

    assert [job[0] for job in jobs] == ["qwen", "qwen (1)", "qwen (2)"]
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(rows) == 6
    # Every temperature plan ran its own number of times.
    assert {r["temperature"] for r in rows} == {0.0, 0.6, 1.0}
    for temperature, runs in ((0.0, 1), (0.6, 3), (1.0, 2)):
        at_temp = [r for r in rows if r["temperature"] == temperature]
        assert len(at_temp) == runs
        assert {r["note"] for r in at_temp} == {f"sweep (temp={temperature})"}
    # Distinct labels keep the plans apart in the results table.
    assert {r["model"] for r in rows} == {"qwen", "qwen (1)", "qwen (2)"}
    # Each run stores its elapsed wall-clock time.
    assert all(isinstance(r["elapsed"], (int, float)) and r["elapsed"] >= 0
               for r in rows)


# ---------------------------------------------------------------------------
# /api/run — validates plans and queues them in one background worker
# ---------------------------------------------------------------------------

def _handler(body):
    h = homebench.Handler.__new__(homebench.Handler)
    payload = json.dumps(body).encode()
    h.path = "/api/run"
    h.headers = {"Content-Length": str(len(payload))}
    h.rfile = io.BytesIO(payload)
    h.send_response = MagicMock()
    h.send_header = MagicMock()
    h.end_headers = MagicMock()
    h.wfile = io.BytesIO()
    return h


def _reset_state():
    homebench.state.update({"running": False, "model": "", "done": 0,
                            "total": 0, "log": [], "error": None,
                            "plan": 0, "plans": 0})


def test_run_endpoint_queues_all_plans_in_one_worker(tmp_path, monkeypatch):
    monkeypatch.setattr(homebench, "WEB_OUT", str(tmp_path / "results.jsonl"))
    body = {
        "name": "qwen",
        "url": "http://localhost:1234",
        "task": "math",
        "max_tokens": 128,
        "plans": [
            {"temperature": 0.0, "runs": 1},
            {"temperature": 0.6, "runs": 3},
        ],
    }
    h = _handler(body)
    try:
        with patch("homebench.threading.Thread") as thread:
            h.do_POST()
        response = json.loads(h.wfile.getvalue())
        assert response["ok"] is True
        assert response["queued"] == 2
        # 1 task × (1 + 3) runs.
        assert response["total"] == 4
        assert homebench.state["total"] == 4
        assert homebench.state["plans"] == 2
        thread.assert_called_once()

        # The captured worker executes every queued plan, in order.
        calls = []

        def fake_run(url, name, runs, temperature, max_tokens, timeout,
                     out_path, note="", on_result=None, task_id=None):
            calls.append((name, runs, temperature, note))
            return 0

        with patch("homebench.run_benchmark", side_effect=fake_run):
            thread.call_args.kwargs["target"]()

        assert calls == [
            ("qwen", 1, 0.0, "temp=0.0"),
            ("qwen (1)", 3, 0.6, "temp=0.6"),
        ]
        assert homebench.state["running"] is False
    finally:
        _reset_state()


def test_run_endpoint_rejects_invalid_plans(tmp_path, monkeypatch):
    monkeypatch.setattr(homebench, "WEB_OUT", str(tmp_path / "results.jsonl"))
    body = {
        "name": "qwen",
        "url": "http://localhost:1234",
        "plans": [{"temperature": 5, "runs": 1}],
    }
    h = _handler(body)
    try:
        with patch("homebench.threading.Thread") as thread:
            h.do_POST()
        thread.assert_not_called()
        h.send_response.assert_called_once_with(400)
        assert "temperature" in json.loads(h.wfile.getvalue())["error"]
    finally:
        _reset_state()


# ---------------------------------------------------------------------------
# AGENTS.md history mapping
# ---------------------------------------------------------------------------

def test_history_records_this_request():
    history = (ROOT / "History.md").read_text(encoding="utf-8")
    assert "multi-selection tool for temperature values and run counts" in history
    assert (ROOT / "tests" / "test_history_40_multi_temperature_plans.py").is_file()

