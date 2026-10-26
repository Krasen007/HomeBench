"""History: delete rows UI shows a single (-) sign for the whole row."""

from pathlib import Path

HTML = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_delete_rows_uses_single_sign_for_whole_row():
    assert "el('button', '(-)')" in HTML
    assert "Delete all results for model " in HTML
    assert "api('/api/delete_rows', { model: m })" in HTML
    # No per-test delete button remains in the results table.
    assert "Delete all ' + rs.length + ' run(s) for " not in HTML
    assert "u00d7" not in HTML