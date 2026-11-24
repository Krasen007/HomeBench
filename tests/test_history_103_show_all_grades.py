"""History: keep every per-text grade visible and list all wrong answers."""

from pathlib import Path

from tasks.bulmmlu import Question, answer_status
from tasks import reasoningbg_full


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_per_text_grades_render_as_visible_content_not_collapsed_details():
    renderer = HTML.split("function renderDetailRun(r, index) {", 1)[1].split(
        "function buildPages(model)", 1
    )[0]
    per_text_section = renderer.split("const itemGrades =", 1)[1].split(
        "if (r.note)", 1
    )[0]

    assert "document.createElement('div')" in per_text_section
    assert "Per-text grades" in per_text_section
    assert "document.createElement('details')" not in per_text_section


def test_multiple_choice_failure_lists_every_wrong_question():
    questions = tuple(
        Question(f"Question {number}", ("A", "B", "C", "D"), "A")
        for number in range(1, 120)
    )

    passed, reason = answer_status("\n".join(["B"] * len(questions)), questions)

    assert passed is False
    assert reason.startswith("FAIL: 0/119 correct;")
    assert "Q1: expected A, got B" in reason
    assert "Q119: expected A, got B" in reason
    assert "+114 more" not in reason


def test_full_task_failure_lists_every_failed_text():
    results = tuple(
        (f"{number:04}.txt", "bad answer", False, "FAIL: answer mismatch")
        for number in range(1, 9)
    )

    passed, reason = reasoningbg_full.aggregate(results)

    assert passed is False
    for number in range(1, 9):
        assert f"{number:04}.txt" in reason
    assert "+3 more" not in reason


def test_history_maps_the_full_grade_visibility_request():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert "Per-text grades should always be visible" in history
    assert "show all incorrect questions" in history
    assert "tests/test_history_103_show_all_grades.py" in history
