"""History: render benchmark output and prompts as Markdown in the web UI."""

from pathlib import Path


HTML = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_markdown_renderer_handles_common_markdown_and_escapes_html():
    assert "function renderMarkdown(src)" in HTML
    for syntax in ("<strong>", "<em>", "<code>", "<pre>", "<ul>", "<ol>",
                   "<blockquote>", "escapeHtml"):
        assert syntax in HTML
    assert "function inlineMd(s)" in HTML
    assert "s = escapeHtml(s);" in HTML
