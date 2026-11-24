"""History: spelling/grammar failures should report how many answers were correct."""

from typing import List

from tasks import spelling_grammar


def _correct_answers() -> List[str]:
    return [question.answer for question in spelling_grammar.QUESTIONS]


def test_incomplete_answer_sheet_reports_correct_count():
    answers = _correct_answers()[:5]

    reason = spelling_grammar.explain("\n".join(answers))

    total = len(spelling_grammar.QUESTIONS)
    assert f"expected {total} answers, got 5" in reason
    assert f"5/{total} correct" in reason


def test_incorrect_answer_sheet_reports_correct_count():
    answers = _correct_answers()
    wrong_answer = "B" if answers[0] != "B" else "A"
    answers[0] = wrong_answer

    reason = spelling_grammar.explain("\n".join(answers))

    total = len(spelling_grammar.QUESTIONS)
    assert f"{total - 1}/{total} correct" in reason
    assert f"Q1: expected {spelling_grammar.QUESTIONS[0].answer}, got {wrong_answer}" in reason
