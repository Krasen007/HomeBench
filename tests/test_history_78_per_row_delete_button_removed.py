"""History: remove the per-row (-) delete button; bulk delete stays."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
SOURCE = (ROOT / "homebench.py").read_text(encoding="utf-8")


def test_per_row_delete_button_is_gone():
    assert "rowDelBtn" not in HTML
    assert "'(-)'" not in HTML
    assert "Delete all results for model " not in HTML


def test_leading_cell_keeps_only_the_checkbox():
    assert "selectTd.append(rowCheckbox);" in HTML


def test_bulk_delete_still_uses_checkboxes_and_one_request():
    assert 'id="deleteSelected"' in HTML
    assert "api('/api/delete_rows', { models })" in HTML
    assert "'Select model '" in HTML


def test_backend_still_supports_filter_and_bulk_deletes():
    assert (
        'filters = {k: v for k, v in body.items() if k in ("model", "task", "batch", "run")}'
    ) in SOURCE
    assert "def delete_models(" in SOURCE
