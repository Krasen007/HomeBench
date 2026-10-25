"""History: publish results as each task finishes, not only after the batch."""

import json

import homebench


def test_result_is_flushed_before_progress_callback(tmp_path, monkeypatch):
    task = {
        "id": "test",
        "prompt": "prompt",
        "check": lambda _: True,
        "explain": lambda _: "PASS: done",
    }
    monkeypatch.setattr(homebench, "TASKS", [task])
    monkeypatch.setattr(homebench, "chat", lambda *args: "answer")
    out = tmp_path / "results.jsonl"
    observed = []

    def on_result(*args):
        observed.append(json.loads(out.read_text(encoding="utf-8").strip()))

    homebench.run_benchmark("http://localhost:8080", "model", 1, 0, 10, 10,
                            out, on_result=on_result)

    assert observed[0]["output"] == "answer"
    assert observed[0]["reason"] == "PASS: done"
