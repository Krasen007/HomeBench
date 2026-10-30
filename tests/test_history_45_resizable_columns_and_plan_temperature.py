"""History: make results columns resizable."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


def test_results_columns_have_pointer_and_keyboard_resize_handles():
    assert "function resizeHandle(th, col, index)" in HTML
    assert "handle.onpointerdown" in HTML
    assert "handle.onpointermove" in HTML
    assert "ArrowLeft" in HTML
    assert "columnWidths.set(index, clamped)" in HTML
    assert "resizeHandle(cell, colgroup.children[index], index);" in HTML
    assert "table-layout: auto;" in CSS
    assert ".column-resize" in CSS
