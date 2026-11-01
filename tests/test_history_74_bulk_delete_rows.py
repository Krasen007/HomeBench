"""History: delete multiple model rows with one request."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import homebench


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def _write_rows(path, rows):
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )


def _handler(body):
    handler = homebench.Handler.__new__(homebench.Handler)
    payload = json.dumps(body).encode()
    handler.path = "/api/delete_rows"
    handler.headers = {"Content-Length": str(len(payload))}
    handler.rfile = io.BytesIO(payload)
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = io.BytesIO()
    return handler


def test_delete_models_removes_only_named_models(tmp_path):
    path = tmp_path / "results.jsonl"
    _write_rows(path, [
        {"model": "a", "task": "math"},
        {"model": "b", "task": "math"},
        {"model": "c", "task": "math"},
        {"model": "a", "task": "logic"},
    ])

    deleted = homebench.delete_models(str(path), ["a", "b"])

    assert deleted == 3
    remaining = homebench.load_rows(str(path))
    assert [row["model"] for row in remaining] == ["c"]


def test_delete_models_rejects_empty_or_non_string_input(tmp_path):
    path = tmp_path / "results.jsonl"
    _write_rows(path, [{"model": "a"}])

    for models in ([], ["", "   "], [1], [None], None):
        with pytest.raises(ValueError):
            homebench.delete_models(str(path), models)

    assert homebench.load_rows(str(path)) == [{"model": "a"}]


def test_delete_rows_endpoint_accepts_a_models_list(tmp_path, monkeypatch):
    path = tmp_path / "results.jsonl"
    _write_rows(path, [
        {"model": "a", "task": "math"},
        {"model": "b", "task": "math"},
        {"model": "c", "task": "math"},
    ])
    monkeypatch.setattr(homebench, "WEB_OUT", str(path))
    previous_running = homebench.state["running"]
    homebench.state["running"] = False
    try:
        handler = _handler({"models": ["a", "b"]})
        handler.do_POST()
        assert json.loads(handler.wfile.getvalue()) == {"ok": True, "deleted": 2}

        handler = _handler({"models": []})
        with patch("homebench.threading.Thread") as thread:
            handler.do_POST()
        thread.assert_not_called()
        assert handler.send_response.call_args.args[0] == 400
        assert json.loads(handler.wfile.getvalue())["error"] == (
            "models must be a non-empty list of model labels"
        )
    finally:
        homebench.state["running"] = previous_running


def test_frontend_provides_bulk_selection_and_one_request_delete():
    assert "const selectedModels = new Set();" in HTML
    assert "selectAllModels" in HTML
    assert "Delete selected" in HTML
    assert "function syncBulkDelete()" in HTML
    assert "api('/api/delete_rows', { models })" in HTML
    assert "api('/api/delete_rows', { model: m })" in HTML
