"""History: combine the row checkbox and delete-all button in one column."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_column_count_drops_the_trailing_actions_column():
    assert "const columnCount = TASKS.length + 6;" in HTML


def test_leading_select_cell_holds_only_the_checkbox():
    assert "selectTd.append(rowCheckbox);" in HTML
    assert "rowDelBtn" not in HTML


def test_no_trailing_header_or_row_action_cells():
    assert "head.append(el('th', ''));" not in HTML


def test_footer_ends_with_time_column():
    assert (
        "      foot.append(footSortable(el('td', 'time'), 'time'));\n"
        "      tfoot.append(foot);"
    ) in HTML


def test_select_all_and_row_label_are_kept():
    assert "selectAllModels" in HTML
    assert "'Select model '" in HTML
