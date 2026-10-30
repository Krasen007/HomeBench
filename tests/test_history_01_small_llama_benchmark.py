"""History: keep the demo benchmark small and usable with llama.cpp."""

import io
import json
from unittest.mock import MagicMock, patch

from homebench import TASKS, chat


def test_demo_suite_stays_small_and_includes_the_eight_requested_tasks():
    assert len(TASKS) == 9
    assert all(task["id"] and task["prompt"] for task in TASKS)


@patch("homebench.urllib.request.urlopen")
def test_chat_uses_llama_cpp_openai_compatible_endpoint(urlopen):
    response = MagicMock()
    response.read.return_value = json.dumps({
        "choices": [{"message": {"content": "Answer: 2.80"}}]
    }).encode()
    response.readline.side_effect = io.BytesIO(response.read.return_value).readline
    response.__enter__.return_value = response
    urlopen.return_value = response

    assert chat("http://localhost:8080", "prompt", 0, 128, 10) == "Answer: 2.80"
    assert urlopen.call_args.args[0].full_url.endswith("/v1/chat/completions")
