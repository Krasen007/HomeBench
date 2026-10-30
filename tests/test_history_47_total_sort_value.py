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
