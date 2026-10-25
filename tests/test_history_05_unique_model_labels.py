"""History: increment duplicate model labels rather than replacing results."""

import io
import json
from unittest.mock import MagicMock, patch

import homebench


def test_duplicate_model_submissions_get_incremented_labels(monkeypatch):
    monkeypatch.setattr(homebench, "WEB_OUT", "unused-results.jsonl")
    monkeypatch.setattr(homebench, "load_rows",
                        lambda _: [{"model": "model"}, {"model": "model (1)"}])
    handler = homebench.Handler.__new__(homebench.Handler)
    handler.path = "/api/run"
    handler.headers = {"Content-Length": "0"}
    handler.rfile = io.BytesIO(b"{}")
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = io.BytesIO()

    try:
        with patch("homebench.threading.Thread"):
            handler.do_POST()
        assert homebench.state["model"] == "model (2)"
    finally:
        homebench.state.update({"running": False, "model": "", "done": 0,
                                "total": 0, "log": [], "error": None})
