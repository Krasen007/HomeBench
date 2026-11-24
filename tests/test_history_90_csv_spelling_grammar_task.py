"""History: add the supplied Bulgarian spelling and grammar CSV as a benchmark task."""

from pathlib import Path

import pytest

from tasks import TASKS, spelling_grammar

SAMPLE_CSV = (
    "Въпрос едно?;първи;втори;трети;четвърти;C\n"
    "Въпрос две?;peta;druga;treta;chetvrta;A\n"
)


def test_load_questions_parses_semicolon_columns(tmp_path: Path):
    csv_path = tmp_path / "questions.csv"
    _ = csv_path.write_text(SAMPLE_CSV, encoding="utf-8")

    questions = spelling_grammar.load_questions(csv_path)

    assert len(questions) == 2
    assert questions[0].text == "Въпрос едно?"
    assert questions[0].options == ("първи", "втори", "трети", "четвърти")
    assert questions[0].answer == "C"


def test_load_questions_rejects_an_invalid_answer(tmp_path: Path):
    csv_path = tmp_path / "questions.csv"
    _ = csv_path.write_text("Въпрос?;a;b;c;d;E\n", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid answer"):
        _ = spelling_grammar.load_questions(csv_path)


def test_spelling_grammar_task_is_registered_with_the_csv_prompt():
    task = next(task for task in TASKS if task["id"] == spelling_grammar.ID)

    assert task["check"] is spelling_grammar.check
    assert task["explain"] is spelling_grammar.explain
    assert spelling_grammar.QUESTIONS[0].text in task["prompt"]
    assert spelling_grammar.QUESTIONS[-1].text in task["prompt"]


def test_check_accepts_answers_in_csv_order():
    answer = "\n".join(question.answer for question in spelling_grammar.QUESTIONS)

    assert spelling_grammar.check(answer)
    assert spelling_grammar.explain(answer).startswith("PASS:")


def test_check_accepts_numbered_answer_lines():
    answer = "\n".join(
        f"{number}. {question.answer}"
        for number, question in enumerate(spelling_grammar.QUESTIONS, 1)
    )

    assert spelling_grammar.check(answer)


def test_check_reports_the_first_incorrect_answer():
    answers = [question.answer for question in spelling_grammar.QUESTIONS]
    wrong_answer = "B" if answers[0] != "B" else "A"
    answers[0] = wrong_answer

    answer = "\n".join(answers)

    assert not spelling_grammar.check(answer)
    assert f"Q1: expected {spelling_grammar.QUESTIONS[0].answer}, got {wrong_answer}" in spelling_grammar.explain(answer)


def test_check_rejects_an_incomplete_answer_sheet():
    answer = "\n".join(
        question.answer for question in spelling_grammar.QUESTIONS[:-1]
    )

    assert not spelling_grammar.check(answer)
    assert f"got {len(spelling_grammar.QUESTIONS) - 1}" in spelling_grammar.explain(answer)
