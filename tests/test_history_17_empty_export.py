"""History: exporting without results must not fail on a None response."""

import io
from unittest.mock import MagicMock, patch

from homebench import Handler


def test_empty_export_returns_bytes_without_a_none_payload():
    handler = Handler.__new__(Handler)
    handler.path = "/api/export"
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = io.BytesIO()

    with patch("builtins.open", side_effect=FileNotFoundError):
        handler.do_GET()

    assert handler.wfile.getvalue() == b""
    handler.send_response.assert_called_once_with(200)
