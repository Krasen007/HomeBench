"""History: add reasoningbg full, which runs all 232 texts in one task row."""

import json

import homebench
from homebench import _LoopDetected, run_benchmark
from tasks import TASKS, reasoningbg, reasoningbg_full


def answer_sheets():
    return {
        item.prompt: "\n".join(question.answer for question in question_set.questions)
        for item, question_set in zip(reasoningbg_full.items_for_run(0), reasoningbg.SETS)
    }


def correct_results():
    return tuple(
        (question_set.name, answer_sheets()[item.prompt], True, "PASS")
        for item, question_set in zip(reasoningbg_full.items_for_run(0), reasoningbg.SETS)
    )


def test_registry_has_fifteen_unique_tasks():
    ids = [task["id"] for task in TASKS]

    assert len(ids) == 15
    assert len(set(ids)) == 15
    assert ids[-2:] == [reasoningbg.ID, reasoningbg_full.ID]


def test_full_task_registration_exposes_its_hooks():
    task = next(item for item in TASKS if item["id"] == reasoningbg_full.ID)

    assert task["prompt"] == reasoningbg_full.PROMPT
    assert task["check"] is reasoningbg_full.check
    assert task["explain"] is reasoningbg_full.explain
    assert task["items_for_run"] is reasoningbg_full.items_for_run
    assert task["render_output"] is reasoningbg_full.render_output
    assert task["aggregate"] is reasoningbg_full.aggregate


def test_full_task_items_cover_every_text_in_order():
    items = reasoningbg_full.items_for_run(0)

    assert [item.label for item in items] == [item.name for item in reasoningbg.SETS]
    assert [item.prompt for item in items] == [item.prompt for item in reasoningbg.SETS]

    first = items[0]
    passed, reason = first.status(answer_sheets()[first.prompt])
    assert passed is True
    assert reason.startswith("PASS:")


def test_full_output_roundtrip_passes_only_when_every_file_is_correct():
    results = correct_results()
    output = reasoningbg_full.render_output(results)

    assert reasoningbg_full.parse_sections(output)[0][0] == reasoningbg.SETS[0].name
    assert reasoningbg_full.check(output) is True
    assert reasoningbg_full.explain(output) == "PASS: 232/232 texts correct"

    wrong = list(results)
    wrong[0] = (wrong[0][0], "", False, "FAIL: no model output received")
    failed_output = reasoningbg_full.render_output(tuple(wrong))
    assert reasoningbg_full.check(failed_output) is False
    assert "231/232 texts fully correct" in reasoningbg_full.explain(failed_output)


def test_full_output_requires_all_232_sections():
    assert reasoningbg_full.check("=== 0001_aheloy-2.txt ===\nA") is False
    assert "expected 232 text sections, got 1" in reasoningbg_full.explain(
        "=== 0001_aheloy-2.txt ===\nA")


def test_benchmark_runs_every_file_and_records_one_passing_row(tmp_path, monkeypatch):
    task = next(item for item in TASKS if item["id"] == reasoningbg_full.ID)
    monkeypatch.setattr(homebench, "TASKS", [task])
    sheets = answer_sheets()
    seen = []
    phases = []

    def fake_chat(url, prompt, temperature, max_tokens, timeout, **kwargs):
        seen.append(prompt)
        return sheets[prompt]

    def on_token(task_id, run, chunk):
        if chunk.get("start") and "phase" in chunk:
            phases.append(chunk["phase"])

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out_path = tmp_path / "results.jsonl"
    run_benchmark("http://localhost:1234", "model", runs=1, temperature=0.0,
                  max_tokens=1024, timeout=30, out_path=str(out_path),
                  task_ids=[reasoningbg_full.ID], on_token=on_token)

    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    assert len(seen) == 232
    assert seen == [item.prompt for item in reasoningbg_full.items_for_run(0)]
    assert phases[0].startswith("file 1/232:")
    assert phases[-1].startswith("file 232/232:")
    assert len(rows) == 1
    assert rows[0]["task"] == reasoningbg_full.ID
    assert rows[0]["prompt"] == reasoningbg_full.PROMPT
    assert rows[0]["passed"] is True
    assert rows[0]["reason"] == "PASS: 232/232 texts correct"
    assert f"=== {reasoningbg.SETS[0].name} ===" in rows[0]["output"]
    assert f"=== {reasoningbg.SETS[-1].name} ===" in rows[0]["output"]


def test_benchmark_continues_after_a_loop_in_one_file(tmp_path, monkeypatch):
    task = next(item for item in TASKS if item["id"] == reasoningbg_full.ID)
    monkeypatch.setattr(homebench, "TASKS", [task])
    sheets = answer_sheets()
    calls = []

    def fake_chat(url, prompt, temperature, max_tokens, timeout, **kwargs):
        calls.append(prompt)
        if prompt == reasoningbg.SETS[0].prompt:
            raise _LoopDetected("looping output")
        return sheets[prompt]

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out_path = tmp_path / "results.jsonl"
    run_benchmark("http://localhost:1234", "model", runs=1, temperature=0.0,
                  max_tokens=1024, timeout=30, out_path=str(out_path),
                  task_ids=[reasoningbg_full.ID])

    row = json.loads(out_path.read_text(encoding="utf-8").splitlines()[0])
    assert len(calls) == 232
    assert row["passed"] is False
    assert "231/232 texts fully correct" in row["reason"]
    assert reasoningbg.SETS[0].name in row["reason"]
    assert "repetition loop detected" in row["reason"]
    assert f"=== {reasoningbg.SETS[-1].name} ===" in row["output"]
