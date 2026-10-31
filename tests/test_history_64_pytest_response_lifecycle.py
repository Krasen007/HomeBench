"""Regression coverage for finite, fresh mock responses in benchmark tests."""
import io
import json
from unittest.mock import MagicMock, patch

from homebench import TASKS, run_benchmark


def _fake_response(text):
    body = json.dumps({"choices": [{"message": {"content": text}}]}).encode()
    response = MagicMock()
    response.read.return_value = body
    response.readline.side_effect = io.BytesIO(body).readline
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_each_benchmark_request_gets_a_fresh_eof_terminating_response():
    responses = []

    def open_response(*_args, **_kwargs):
        response = _fake_response("Answer: 2.80")
        responses.append(response)
        return response

    with patch("homebench.urllib.request.urlopen", side_effect=open_response) as urlopen, \
            patch("homebench.open", create=True) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        run_benchmark(
            "http://localhost:1234", "test-model", runs=2,
            temperature=0.0, max_tokens=16384, timeout=600,
            out_path="unused-results.jsonl", task_id="math",
        )

    assert urlopen.call_count == 2
    assert len(responses) == 2
    assert responses[0] is not responses[1]
    assert all(response.readline.side_effect.__self__.read() == b"" for response in responses)
