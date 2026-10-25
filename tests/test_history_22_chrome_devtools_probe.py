"""History: verify Chrome's optional DevTools probe is a harmless 404."""

import io
from unittest.mock import MagicMock

from homebench import Handler


def test_chrome_devtools_probe_uses_normal_not_found_response():
    handler = Handler.__new__(Handler)
    handler.path = "/.well-known/appspecific/com.chrome.devtools.json"
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = io.BytesIO()

    handler.do_GET()

    handler.send_response.assert_called_once_with(404)
