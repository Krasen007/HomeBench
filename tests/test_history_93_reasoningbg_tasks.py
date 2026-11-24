"""History: implement the rotating tasks/ReasoningBG reading-comprehension set."""

import json

import pytest

import homebench
from homebench import run_benchmark
from tasks import TASKS, reasoningbg
from tasks.bulmmlu import OPTIONS
from tasks.reasoningbg import TextFormatError, load_text


def answer_sheet(question_set):
    return "\n".join(question.answer for question in question_set.questions)


def test_every_text_in_the_folder_is_loaded():
    paths = sorted(reasoningbg.TEXT_DIR.glob("*.txt"))

    assert len(paths) == 232
    assert [item.name for item in reasoningbg.SETS] == [path.name for path in paths]


def test_every_question_set_has_a_passage_and_a_complete_answer_key():
    for question_set in reasoningbg.SETS:
        assert question_set.passage
        assert question_set.numbers
        assert len(question_set.numbers) == len(question_set.questions)
        assert len(set(question_set.numbers)) == len(question_set.numbers)
        assert question_set.prompt.startswith("Прочети текста")

        for number, question in zip(question_set.numbers, question_set.questions):
            assert number > 0
            assert question.text
            assert question.answer in OPTIONS
            assert all(option for option in question.options)


def test_file_with_missing_questions_keeps_its_original_numbering():
    question_set = next(item for item in reasoningbg.SETS
                        if item.name == "0130_naukata-potvarzhdava-legendata-2.txt")

    assert question_set.numbers == (1, 2, 4, 5, 7, 8, 9, 10)
    assert "\n4. " in question_set.prompt
    assert "\n3. " not in question_set.prompt


def test_load_text_rejects_a_file_without_an_answer_key(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_text("Текст.\n\nВъпроси\n\n1. Въпрос?\nA) едно\nB) две\nC) три\nD) четири\n",
                    encoding="utf-8")

    with pytest.raises(TextFormatError, match="Отговори"):
        load_text(path)


def test_run_index_selects_the_text_and_prompt_deterministically():
    assert reasoningbg.set_for_run(0).name == reasoningbg.SETS[0].name
    assert reasoningbg.set_for_run(231).name == reasoningbg.SETS[-1].name
    assert reasoningbg.set_for_run(232).name == reasoningbg.SETS[0].name
    assert reasoningbg.prompt_for_run(1) == reasoningbg.SETS[1].prompt
    assert reasoningbg.PROMPT == reasoningbg.prompt_for_run(0)


def test_prompt_contains_the_passage_questions_and_options():
    question_set = reasoningbg.SETS[0]

    assert question_set.passage in question_set.prompt
    assert question_set.questions[0].text in question_set.prompt
    assert f"A) {question_set.questions[0].options[0]}" in question_set.prompt


@pytest.mark.parametrize("run", [0, 1, 57, 231])
def test_check_and_explain_use_the_answer_key_for_that_run(run):
    question_set = reasoningbg.set_for_run(run)

    assert reasoningbg.check_for_run(answer_sheet(question_set), run) is True
    assert reasoningbg.explain_for_run(answer_sheet(question_set), run).startswith("PASS:")

    answers = [question.answer for question in question_set.questions]
    answers[0] = "B" if answers[0] != "B" else "A"
    wrong = "\n".join(answers)
    assert reasoningbg.check_for_run(wrong, run) is False
    assert f"{len(answers) - 1}/{len(answers)} correct" in reasoningbg.explain_for_run(wrong, run)

    assert reasoningbg.explain_for_run("", run).startswith("FAIL:")


def test_registered_task_exposes_the_run_aware_hooks():
    task = next(item for item in TASKS if item["id"] == reasoningbg.ID)

    assert task["prompt"] == reasoningbg.PROMPT
    assert task["check"] is reasoningbg.check
    assert task["explain"] is reasoningbg.explain
    assert task["prompt_for_run"] is reasoningbg.prompt_for_run
    assert task["check_for_run"] is reasoningbg.check_for_run
    assert task["explain_for_run"] is reasoningbg.explain_for_run


def test_benchmark_sends_and_records_the_prompt_for_each_run(tmp_path, monkeypatch):
    task = next(item for item in TASKS if item["id"] == reasoningbg.ID)
    monkeypatch.setattr(homebench, "TASKS", [task])
    answers = {item.prompt: answer_sheet(item) for item in reasoningbg.SETS[:2]}
    seen = []

    def fake_chat(url, prompt, temperature, max_tokens, timeout, **kwargs):
        seen.append(prompt)
        return answers[prompt]

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out_path = tmp_path / "results.jsonl"
    run_benchmark("http://localhost:1234", "model", runs=2, temperature=0.0,
                  max_tokens=1024, timeout=30, out_path=str(out_path),
                  task_ids=[reasoningbg.ID])

    rows = [json.loads(line) for line in out_path.read_text(encoding="utf-8").splitlines()]
    assert seen == [reasoningbg.prompt_for_run(0), reasoningbg.prompt_for_run(1)]
    assert [row["prompt"] for row in rows] == seen
    assert [row["passed"] for row in rows] == [True, True]
    assert all(row["task"] == reasoningbg.ID for row in rows)
