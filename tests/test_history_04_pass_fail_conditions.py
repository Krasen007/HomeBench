"""History: show a condition describing each task pass or failure."""

import json

import homebench


def test_run_saves_the_explanation_for_both_pass_and_fail(tmp_path, monkeypatch):
    task = {"id": "test", "prompt": "prompt", "check": lambda output: output == "good",
            "explain": lambda output: "PASS: accepted" if output == "good" else "FAIL: rejected"}
    monkeypatch.setattr(homebench, "TASKS", [task])
    out = tmp_path / "results.jsonl"

    for output, expected_pass, expected_reason in (
        ("good", True, "PASS: accepted"), ("bad", False, "FAIL: rejected"),
    ):
        monkeypatch.setattr(homebench, "chat", lambda *args, value=output: value)
        homebench.run_benchmark("http://localhost:8080", "model", 1, 0, 10, 10, out)

    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines()]
    assert [(row["passed"], row["reason"]) for row in rows] == [
        (True, "PASS: accepted"), (False, "FAIL: rejected")]
