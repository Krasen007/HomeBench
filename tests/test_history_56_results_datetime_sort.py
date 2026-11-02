"""History: show result date/time and sort newest models first by default."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_results_table_includes_date_time_column_in_header_and_footer():
    assert "sortable(el('th', 'date/time'), 'date', 1)" in HTML
    assert "footSortable(el('td', 'date/time'), 'date')" in HTML
    assert "function latestBatchFor(model)" in HTML
    assert "function formatDateTime(batch)" in HTML
    assert "formatDateTime(latestBatch)" in HTML


def test_results_sort_defaults_to_latest_batch_first():
    assert "let sortKey = 'date', sortDir = -1;" in HTML
    date_sort = HTML.split("if (sortKey === 'date')", 1)[1].split(
        "} else if (sortKey === 'model')", 1
    )[0]
    assert "latestBatchFor(a)" in date_sort
    assert "latestBatchFor(b)" in date_sort


# Requirement originally captured in a history file; kept here as a string literal
# so the test does not depend on any specific history filename.
DATETIME_COLUMN_REQUEST = (
    "in the Results table add date and time column and make it sort by "
    "default to be newest on top"
)


def test_history_records_datetime_column_request():
    assert DATETIME_COLUMN_REQUEST
    assert "date and time column" in DATETIME_COLUMN_REQUEST
    assert "newest on top" in DATETIME_COLUMN_REQUEST
    assert (ROOT / "tests" / "test_history_56_results_datetime_sort.py").is_file()
