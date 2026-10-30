"""History: results-table fields are sortable and column labels are
repeated in a footer row at the bottom of the table."""
from pathlib import Path

HTML = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_results_table_fields_are_sortable():
    assert "function sortBy(key)" in HTML
    assert "sortable" in HTML
    assert "sort-dir" in HTML
    # header labels keep their original literal calls
    assert "el('th', 'model')" in HTML
    assert "el('th', 'temp')" in HTML
    assert "el('th', 'total')" in HTML
    assert "el('th', 'total per run')" in HTML


def test_result_labels_repeated_in_footer_at_bottom():
    assert "el('thead')" in HTML
    assert "el('tbody')" in HTML
    assert "el('tfoot')" in HTML
    # table sections are built header -> body -> footer
    assert HTML.index("el('thead')") < HTML.index("el('tbody')")
    assert HTML.index("el('tbody')") < HTML.index("el('tfoot')")
    # footer repeats the column labels at the bottom of the table
    assert "el('td', 'model')" in HTML
    assert "el('td', 'temp')" in HTML
    assert "el('td', 'total')" in HTML
    assert "el('td', 'total per run')" in HTML
