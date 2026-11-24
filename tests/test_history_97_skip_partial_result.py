"""History: retain and grade partial output when a task is skipped."""

import json
from pathlib import Path
from typing import NamedTuple

import homebench


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def _read_row(path):
    return json.loads(path.read_text(encoding="utf-8").splitlines()[0])


def test_skipped_task_saves_and_grades_streamed_answer(tmp_path, monkeypatch):
    task = {
        "id": "math",
        "prompt": "Calculate.",
        "check": lambda output: output.strip() == "42",
        "explain": lambda output: (
            "PASS: answer is 42" if output.strip() == "42"
            else "FAIL: incomplete answer"
        ),
    }
    monkeypatch.setattr(homebench, "TASKS", [task])

    def fake_chat(*args, on_token=None, **kwargs):
        on_token({"content": "4", "reasoning": "calculating"})
        on_token({"content": "2", "reasoning": ""})
        raise homebench._SkipRequested

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out_path = tmp_path / "results.jsonl"
    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 100, 10, out_path,
        task_ids=["math"],
    )

    row = _read_row(out_path)
    assert row["status"] == "skipped"
    assert row["passed"] is None
    assert row["output"] == "42"
    assert row["reasoning"] == "calculating"
    assert row["partial_grade"] == {
        "passed": True,
        "reason": "PASS: answer is 42",
    }


def test_skipped_multi_item_task_keeps_completed_and_partial_answers(
        tmp_path, monkeypatch):
    class Item(NamedTuple):
        label: str
        prompt: str

        def status(self, output):
            passed = output.strip() == "A"
            return passed, "PASS: correct" if passed else "FAIL: answer is not A"

    items = (Item("first.txt", "first prompt"), Item("second.txt", "second prompt"))
    task = {
        "id": "bundle",
        "prompt": "Answer both.",
        "check": lambda _: False,
        "explain": lambda _: "FAIL",
        "items_for_run": lambda _: items,
        "render_output": lambda results: "\n".join(
            f"=== {label} ===\n{output}" for label, output, _, _ in results
        ),
        "aggregate": lambda results: (False, "FAIL: bundle incomplete"),
    }
    monkeypatch.setattr(homebench, "TASKS", [task])
    calls = {"count": 0}

    def fake_chat(*args, on_token=None, **kwargs):
        calls["count"] += 1
        answer = "A" if calls["count"] == 1 else "B"
        on_token({"content": answer, "reasoning": ""})
        if calls["count"] == 2:
            raise homebench._SkipRequested
        return answer

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out_path = tmp_path / "results.jsonl"
    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 100, 10, out_path,
        task_ids=["bundle"],
    )

    row = _read_row(out_path)
    assert row["status"] == "skipped"
    assert row["passed"] is None
    assert "=== first.txt ===\nA" in row["output"]
    assert "=== second.txt ===\nB" in row["output"]
    assert row["partial_grade"]["reason"].startswith(
        "1/2 captured texts fully correct"
    )
    assert "FAIL: answer is not A" in row["partial_grade"]["reason"]


def test_detail_view_displays_partial_grade_on_skipped_runs():
    renderer = HTML.split("function renderDetailRun(r, index) {", 1)[1].split(
        "function buildPages(model)", 1
    )[0]

    assert "r.partial_grade" in renderer
    assert "Partial grade (" in renderer
    assert "partial.reason" in renderer
