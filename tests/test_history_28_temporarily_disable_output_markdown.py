"""History: show raw model output to verify Markdown isn't masking its format."""

from pathlib import Path


PAGE = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")
RENDERER = PAGE.split("function renderDetailRun(r, index) {", 1)[1].split(
    "function updateDetailRuns()", 1)[0]


def test_model_output_is_rendered_as_literal_preformatted_text():
    assert "document.createElement('pre')" in RENDERER
    assert "outDiv.textContent = r.output || '(empty output)';" in RENDERER
    assert "outDiv.innerHTML = renderMarkdown" not in RENDERER


def test_prompt_markdown_and_html_preview_remain_available():
    assert "promptDiv.innerHTML = renderMarkdown(task.prompt);" in PAGE
    assert "const html = extractHtml(r.output);" in RENDERER
