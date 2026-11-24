"""History: place run grading below the generated answer in result details."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_result_score_section_follows_answer_and_answer_output():
    renderer = HTML.split("function renderDetailRun(r, index) {", 1)[1].split(
        "function buildPages(model)", 1
    )[0]

    answer_bar = renderer.index("d.append(answerBar);")
    answer_output = renderer.index("d.append(outDiv);")
    score_section = renderer.index("d.append(scoreSection);")

    assert answer_bar < answer_output < score_section
    assert "scoreSection.append(" in renderer
    assert "reasonEl" in renderer


def test_history_maps_the_result_score_layout_request():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert "run's score and failure details" in history
    assert "tests/test_history_102_score_below_generated_answer.py" in history
