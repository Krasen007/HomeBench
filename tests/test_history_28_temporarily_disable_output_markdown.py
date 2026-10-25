"""History: model output is rendered as Markdown again (disable was temporary)."""

from pathlib import Path


PAGE = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
RENDERER = PAGE.split("function renderDetailRun(r, index) {", 1)[1].split(
    "function updateDetailRuns()", 1)[0]


def test_model_output_is_rendered_as_markdown():
    assert "outDiv.innerHTML = renderMarkdown(r.output || '')" in RENDERER
    assert "outDiv.textContent = r.output" not in RENDERER


def test_prompt_markdown_and_html_preview_remain_available():
    assert "promptDiv.innerHTML = renderMarkdown(task.prompt);" in PAGE
    assert "const html = extractHtml(r.output);" in RENDERER
