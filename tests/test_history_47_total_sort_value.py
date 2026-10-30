"""History: sort the total column by its displayed overall result."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_total_sort_uses_overall_pass_rate_not_task_lookup():
    sort_models = HTML.split("function sortModels(models)", 1)[1].split(
        "function resizeHandle", 1
    )[0]

    assert "function totalPassRateFor(model)" in HTML
    assert "sortKey === 'total'" in sort_models
    assert "totalPassRateFor(a)" in sort_models
    assert "totalPassRateFor(b)" in sort_models
    assert "passesFor(a, sortKey)" in sort_models


def test_history_records_total_sort_fix():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert "Sort the displayed total by its overall pass rate" in history
    assert (ROOT / "tests" / "test_history_47_total_sort_value.py").is_file()
