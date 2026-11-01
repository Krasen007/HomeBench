"""History: render result timestamps as local YYYY-MM-DD : HH:MM."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def _format_function():
    rest = HTML.split("function formatDateTime(batch)", 1)[1].split(
        "function sortModels", 1
    )[0]
    return "function formatDateTime(batch)" + rest


def test_format_datetime_uses_padded_local_time():
    function = _format_function()

    assert "getFullYear()" in function
    assert "padStart(2, '0')" in function
    assert " : " in function
    assert "getHours()" in function
    assert "getMinutes()" in function
    assert "toLocaleString" not in function


def test_format_datetime_renders_the_expected_shape_with_node():
    if shutil.which("node") is None:
        pytest.skip("node not available")

    script = _format_function() + "\nconsole.log(formatDateTime(1793547000));\n"
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2} : \d{2}:\d{2}", result.stdout.strip()
    )
