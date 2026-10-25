"""History: auto-detect and use the model name when the field is blank."""

import io
import json
from unittest.mock import MagicMock, patch

import homebench


def test_model_name_is_detected_from_llama_server_models_endpoint():
    response = MagicMock()
    response.read.return_value = json.dumps({"data": [{"id": "local-model"}]}).encode()
    response.__enter__.return_value = response
    with patch("homebench.urllib.request.urlopen", return_value=response):
        assert homebench.infer_model_name("http://localhost:8080") == "local-model"


def test_blank_model_label_is_filled_from_server_detection():
    handler = homebench.Handler.__new__(homebench.Handler)
    body = json.dumps({"name": "", "url": "http://localhost:8080"}).encode()
    handler.path = "/api/run"
    handler.headers = {"Content-Length": str(len(body))}
    handler.rfile = io.BytesIO(body)
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    handler.wfile = io.BytesIO()
    try:
        with patch("homebench.infer_model_name", return_value="detected-model"), \
             patch("homebench.load_rows", return_value=[]), \
             patch("homebench.threading.Thread"):
            handler.do_POST()
        assert homebench.state["model"] == "detected-model"
    finally:
        homebench.state.update({"running": False, "model": "", "done": 0,
                                "total": 0, "log": [], "error": None})
