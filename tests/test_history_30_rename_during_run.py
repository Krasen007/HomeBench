"""History: reject model rename requests while benchmark execution is active."""

import io
import json
from unittest.mock import MagicMock, patch

import homebench


def test_rename_endpoint_returns_conflict_while_running():
    handler = homebench.Handler.__new__(homebench.Handler)
    body = json.dumps({"old_name": "old", "new_name": "new"}).encode()
    handler.path = "/api/rename_model"
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = io.BytesIO(body)
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = io.BytesIO()

    previous = homebench.state["running"]
    homebench.state["running"] = True
    try:
        with patch("homebench.rename_model") as rename:
            handler.do_POST()
        handler.send_response.assert_called_once_with(409)
        assert json.loads(handler.wfile.getvalue())["error"]
        rename.assert_not_called()
    finally:
        homebench.state["running"] = previous
