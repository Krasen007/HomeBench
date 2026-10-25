"""History: serve the web page from a separate static HTML file."""

from pathlib import Path

import homebench


def test_page_is_loaded_from_static_index_html():
    expected = Path(homebench.__file__).with_name("static") / "index.html"
    assert homebench.PAGE_PATH == expected
    assert homebench.PAGE == expected.read_text(encoding="utf-8")
