"""History: the reported loop repeated long paragraphs instead of a short phrase.

The quoted text below is the exact tail of the reasoning stored in
``results.jsonl`` for the ``game_solved`` run of
``DeepSeek-V4-Pro-Qwen3.5-9B-MTP-Q4_K_M`` (71,430 reasoning characters, 181
occurrences of "Now, let's write the code.", finish_reason=length).

The run was only stopped by the token limit; the repetition detector never
fired because the looped unit is a long, slightly varying cycle rather than a
short contiguous pattern.
"""

import io
import json
from unittest.mock import MagicMock, patch

import pytest

import homebench


REPORTED_LOOP_TEXT = """Now, let's write the code.

We'll also need to handle the spawn interval reduction: we'll set spawnInterval to a random between 0.3 and 0.8 seconds when the condition is met. We'll need to ensure that the spawn interval is in milliseconds.

Now, let's write the code.

We'll also need to handle the spawn interval reduction: we'll check after each yellow coin collection if the time since last collection is less than current spawnInterval. We'll need to know when the last collection occurred. We'll store lastCollectionTime. We'll update it on each collection.

Now, let's write the code.

We'll also need to handle the spawn interval reduction: we'll set spawnInterval to a random between 0.3 and 0.8 seconds when the condition is met. We'll need to ensure that the spawn interval is in milliseconds.

Now, let's write the code.

We'll also need to handle the spawn interval reduction: we'll check after each yellow coin collection if the time since last collection is"""


def test_reported_long_paragraph_loop_is_detected():
    assert homebench._detect_repetition_loop(REPORTED_LOOP_TEXT)


def test_chat_raises_for_the_reported_long_paragraph_loop():
    event = {"choices": [{"delta": {"reasoning_content": REPORTED_LOOP_TEXT}}]}
    data = (b"data: " + json.dumps(event).encode("utf-8")
            + b"\n\ndata: [DONE]\n\n")
    response = MagicMock()
    response.readline.side_effect = io.BytesIO(data).readline
    response.__enter__.return_value = response
    response.__exit__.return_value = False

    with patch("homebench.urllib.request.urlopen", return_value=response):
        with pytest.raises(homebench._LoopDetected):
            homebench.chat(
                "http://localhost:1234", "prompt", 0.2, 1024, 30,
            )
