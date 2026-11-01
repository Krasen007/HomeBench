"""History: the results-table "time" column renders elapsed totals as m:ss.

The former "total per run" column is renamed to "time" and its value is shown
as minutes:seconds (for example ``0:42`` or ``2:12``) instead of raw seconds.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_results_table_uses_time_column():
    assert "el('th', 'time')" in HTML
    assert "el('td', 'time')" in HTML
    assert "formatDuration(totalPerRun)" in HTML
    assert "total per run" not in HTML


def test_header_and_footer_sort_by_time_key():
    assert "sortable(el('th', 'time'), 'time', TASKS.length + 5)" in HTML
    assert "footSortable(el('td', 'time'), 'time')" in HTML


def test_time_column_is_sortable_by_time_key():
    start = HTML.index("function sortModels(")
    end = HTML.index("function resizeHandle(", start)
    sort_models = HTML[start:end]
    assert "sortKey === 'time'" in sort_models
    assert "totalSecondsFor(a)" in sort_models
    assert "totalSecondsFor(b)" in sort_models


def test_detail_view_still_uses_format_seconds():
    assert "formatSeconds(Number(r.elapsed))" in HTML


def test_format_duration_renders_minutes_and_seconds():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")

    start = HTML.index("function formatDuration(v)")
    end = HTML.index("function average(", start)
    snippet = HTML[start:end].rstrip()
    script = snippet + (
        "\nconsole.log(JSON.stringify(["
        "formatDuration(42), formatDuration(132), formatDuration(0), "
        "formatDuration(3600), formatDuration(null)"
        "]));"
    )
    result = subprocess.run(
        [node, "-e", script],
        capture_output=True, text=True, check=True,
    )
    assert json.loads(result.stdout) == ["0:42", "2:12", "0:00", "60:00", "-"]
