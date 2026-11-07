"""History: store reasoning tokens so any finished run can be audited later."""

import json
from pathlib import Path

import homebench


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def _rows(path):
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _single_math_task(monkeypatch):
    task = {"id": "math", "prompt": "2 + 2", "check": lambda _: True}
    monkeypatch.setattr(homebench, "TASKS", [task])


def test_run_benchmark_saves_reasoning_next_to_the_answer(monkeypatch, tmp_path):
    _single_math_task(monkeypatch)

    def fake_chat(*args, on_token=None, **kwargs):
        on_token({"content": "", "reasoning": "first thought "})
        on_token({"content": "", "reasoning": "second thought"})
        on_token({"content": "4", "reasoning": ""})
        return "4"

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out = tmp_path / "results.jsonl"

    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 100, 10, out,
        on_token=lambda *args: None,
    )

    row = _rows(out)[0]
    assert row["output"] == "4"
    assert row["reasoning"] == "first thought second thought"


def test_rows_without_reasoning_still_record_an_empty_string(
        monkeypatch, tmp_path):
    _single_math_task(monkeypatch)
    monkeypatch.setattr(homebench, "chat", lambda *args, **kwargs: "4")
    out = tmp_path / "results.jsonl"

    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 100, 10, out,
    )

    assert _rows(out)[0]["reasoning"] == ""


def test_partial_reasoning_survives_a_user_skip(monkeypatch, tmp_path):
    _single_math_task(monkeypatch)

    def fake_chat(*args, on_token=None, **kwargs):
        on_token({"content": "", "reasoning": "went off the rails"})
        raise homebench._SkipRequested

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out = tmp_path / "results.jsonl"

    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 100, 10, out,
        on_token=lambda *args: None,
    )

    row = _rows(out)[0]
    assert row["status"] == "skipped"
    assert row["reasoning"] == "went off the rails"


def test_partial_reasoning_survives_loop_failure(monkeypatch, tmp_path):
    _single_math_task(monkeypatch)

    def fake_chat(*args, on_token=None, **kwargs):
        on_token({"content": "", "reasoning": "repeat repeat "})
        raise homebench._LoopDetected("partial answer")

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out = tmp_path / "results.jsonl"

    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 100, 10, out,
        on_token=lambda *args: None,
    )

    row = _rows(out)[0]
    assert row["reason"] == "FAIL: repetition loop detected"
    assert row["reasoning"] == "repeat repeat "


def test_detail_card_renders_saved_reasoning_as_raw_text():
    renderer = HTML.split("function renderDetailRun(r, index) {", 1)[1].split(
        "function updateDetailRuns()", 1)[0]

    assert "Reasoning tokens" in renderer
    assert "r.reasoning" in renderer
    assert "el('pre', reasoning, 'reasoning-text')" in renderer
    assert "renderMarkdown(reasoning)" not in renderer
    assert "Copy reasoning" in renderer
    assert "Copy answer" in renderer


def test_live_panel_labels_counts_and_opens_the_finished_run():
    assert 'id="liveAnswerSummary"' in HTML
    assert 'id="liveReasoningSummary"' in HTML
    assert "$('liveAnswerSummary').textContent" in HTML
    assert "$('liveReasoningSummary').textContent" in HTML
    assert 'id="openLiveResult"' in HTML
    assert "showDetail(liveRun.model, task)" in HTML
    assert "function formatChars(text)" in HTML


AUDIT_REQUEST = (
    "read the reasoning tokens and the generated answer for each task"
)


def test_history_records_the_reasoning_audit_request():
    assert "reasoning tokens" in AUDIT_REQUEST
    assert "generated answer" in AUDIT_REQUEST
    assert (ROOT / "tests" / "test_history_86_reasoning_audit_in_results.py").is_file()
