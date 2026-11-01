"""History: row selection keeps the select-all checkbox state synchronized."""

from pathlib import Path


PAGE = (Path(__file__).parents[1] / "static" / "index.html").read_text(
    encoding="utf-8"
)


def test_row_selection_recomputes_select_all_and_indeterminate_state():
    row_handler = PAGE.split("rowCheckbox.onchange = () => {", 1)[1].split(
        "};", 1
    )[0]

    assert "selectAll.checked = models.length > 0" in row_handler
    assert "models.every(model => selectedModels.has(model))" in row_handler
    assert "selectAll.indeterminate = selectedModels.size > 0" in row_handler
    assert "!selectAll.checked" in row_handler
