"""History: show grades for each text captured before a multi-item skip."""

import json
from pathlib import Path
from typing import NamedTuple

import homebench


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_skipped_multi_item_run_saves_each_partial_grade(tmp_path, monkeypatch):
    class Item(NamedTuple):
        label: str
        prompt: str

        def status(self, output):
            correct = sum(answer == "A" for answer in output.split())
            passed = output.split() == ["A", "A"]
            verdict = "PASS" if passed else "FAIL"
            return passed, f"{verdict}: {correct}/2 answers correct"

    items = (Item("first.txt", "first"), Item("second.txt", "second"))
    task = {
        "id": "bundle",
        "prompt": "Answer both.",
        "check": lambda _: False,
        "items_for_run": lambda _: items,
        "render_output": lambda results: "\n".join(
            f"=== {label} ===\n{output}" for label, output, _, _ in results
        ),
        "aggregate": lambda _: (False, "FAIL"),
    }
    monkeypatch.setattr(homebench, "TASKS", [task])
    calls = {"count": 0}

    def fake_chat(*args, on_token=None, **kwargs):
        calls["count"] += 1
        answer = "A A" if calls["count"] == 1 else "A B"
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

    row = json.loads(out_path.read_text(encoding="utf-8").splitlines()[0])
    assert row["status"] == "skipped"
    assert row["passed"] is None
    assert row["partial_grade"]["items"] == [
        {
            "label": "first.txt",
            "passed": True,
            "reason": "PASS: 2/2 answers correct",
        },
        {
            "label": "second.txt",
            "passed": False,
            "reason": "FAIL: 1/2 answers correct",
        },
    ]


def test_skipped_partial_grade_displays_per_text_verdicts():
    renderer = HTML.split("function renderDetailRun(r, index) {", 1)[1].split(
        "function buildPages(model)", 1
    )[0]

    assert "partial.items" in renderer
    assert "Per-text grades" in renderer
    assert "item.label" in renderer
    assert "item.reason" in renderer


def test_history_maps_partial_item_grading_request():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert "show whether the captured answers are correct" in history
    assert "tests/test_history_100_skipped_item_grades.py" in history
