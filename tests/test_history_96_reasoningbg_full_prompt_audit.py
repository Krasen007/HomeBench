"""History: make ReasoningBG full prompts and failures easier to audit."""

import json
from pathlib import Path

import homebench
from tasks import TASKS, reasoningbg, reasoningbg_full


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def _answer_sheet(question_set):
    return "\n".join(question.answer for question in question_set.questions)


def test_full_task_prompt_explains_each_file_is_a_separate_prompt():
    assert "separate prompt" in reasoningbg_full.PROMPT
    assert "filename order:" not in reasoningbg_full.PROMPT


def test_failure_summary_distinguishes_fully_correct_texts_and_question_score():
    results = [
        (question_set.name, _answer_sheet(question_set), True, "PASS")
        for question_set in reasoningbg.SETS
    ]
    first = results[2]
    results[2] = (
        first[0],
        first[1],
        False,
        "FAIL: expected 10 answers, got 101 (7/10 correct)",
    )
    results[3] = (results[3][0], "", False, "FAIL: no model output received")

    passed, reason = reasoningbg_full.aggregate(tuple(results))

    assert passed is False
    assert "230/232 texts fully correct" in reason
    assert "2 failed" in reason
    assert f"first failure ({first[0]})" in reason
    assert "expected 10 answers, got 101 (7/10 correct)" in reason


def test_benchmark_saves_each_file_prompt_with_its_result(tmp_path, monkeypatch):
    task = next(item for item in TASKS if item["id"] == reasoningbg_full.ID)
    monkeypatch.setattr(homebench, "TASKS", [task])
    prompt_to_set = {
        item.prompt: question_set
        for item, question_set in zip(
            reasoningbg_full.items_for_run(0), reasoningbg.SETS
        )
    }

    monkeypatch.setattr(
        homebench, "chat",
        lambda url, prompt, temperature, max_tokens, timeout, **kwargs:
            _answer_sheet(prompt_to_set[prompt]),
    )
    out_path = tmp_path / "results.jsonl"
    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 1024, 30, out_path,
        task_ids=[reasoningbg_full.ID],
    )

    row = json.loads(out_path.read_text(encoding="utf-8").splitlines()[0])
    prompts = row["item_prompts"]
    assert len(prompts) == len(reasoningbg.SETS) == 232
    assert prompts[0] == {
        "label": reasoningbg.SETS[0].name,
        "prompt": reasoningbg.SETS[0].prompt,
    }
    assert prompts[-1] == {
        "label": reasoningbg.SETS[-1].name,
        "prompt": reasoningbg.SETS[-1].prompt,
    }
    assert row["prompt"] == reasoningbg_full.PROMPT


def test_result_detail_displays_saved_file_specific_prompts():
    renderer = HTML.split("function renderDetailRun(r, index) {", 1)[1].split(
        "function buildPages(model)", 1
    )[0]

    assert "r.item_prompts" in renderer
    assert "Individual prompts" in renderer
    assert "item.prompt" in renderer
    assert "promptText.textContent = item.prompt" in renderer
