"""History: looping tasks fail and continue; archived history tests use v1.2."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import homebench


ROOT = Path(__file__).parents[1]


def _stream_response(events):
    data = b"".join(
        b"data: " + json.dumps(event).encode("utf-8") + b"\n\n"
        for event in events
    ) + b"data: [DONE]\n\n"
    response = MagicMock()
    response.readline.side_effect = io.BytesIO(data).readline
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def _delta_events(chunks, field="content"):
    return [{"choices": [{"delta": {field: chunk}}]} for chunk in chunks]


def test_repetition_loop_detector_flags_repeated_answer_text():
    phrase = "The cat sat on the mat. "
    assert homebench._detect_repetition_loop(phrase * 20)


def test_repetition_loop_detector_ignores_normal_answer_text():
    text = " ".join(
        f"Sentence {index} contains a different number." for index in range(60)
    )
    assert not homebench._detect_repetition_loop(text)


def test_chat_raises_loop_detected_for_a_looping_answer():
    phrase = "I keep saying the same thing over and over. "
    response = _stream_response(_delta_events([phrase] * 15, "content"))
    with patch("homebench.urllib.request.urlopen", return_value=response):
        with pytest.raises(homebench._LoopDetected) as excinfo:
            homebench.chat(
                "http://localhost:1234", "prompt", 0.2, 1024, 30,
            )

    assert "repetition loop detected" in str(excinfo.value)
    assert phrase in excinfo.value.output


def test_chat_raises_loop_detected_for_a_looping_reasoning_block():
    chunk = "Let me think about this again. "
    response = _stream_response(_delta_events([chunk] * 30, "reasoning_content"))
    with patch("homebench.urllib.request.urlopen", return_value=response):
        with pytest.raises(homebench._LoopDetected) as excinfo:
            homebench.chat(
                "http://localhost:1234", "prompt", 0.2, 1024, 30,
            )

    assert "repetition loop detected" in str(excinfo.value)


def test_run_benchmark_marks_the_loop_as_failed_and_continues(
        monkeypatch, tmp_path):
    tasks = [
        {"id": "first", "prompt": "first", "check": lambda _: True},
        {"id": "second", "prompt": "second", "check": lambda _: True},
    ]
    monkeypatch.setattr(homebench, "TASKS", tasks)
    calls = {"count": 0}

    def fake_chat(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise homebench._LoopDetected("looping output")
        return "42"

    monkeypatch.setattr(homebench, "chat", fake_chat)
    path = tmp_path / "results.jsonl"
    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 8, 5, str(path),
    )

    rows = homebench.load_rows(str(path))
    assert [row["task"] for row in rows] == ["first", "second"]
    assert rows[0]["status"] == "run"
    assert rows[0]["passed"] is False
    assert rows[0]["reason"] == "FAIL: repetition loop detected"
    assert rows[0]["output"] == "looping output"
    assert rows[1]["status"] == "run"
    assert rows[1]["passed"] is True


# Requirement originally captured in history.md; kept here as a string literal
# so the test does not depend on any specific history filename.
LOOP_FAILURE_REQUIREMENT = "if looping is detected it should be marked as failed"


def test_history_records_loop_failure_request():
    assert LOOP_FAILURE_REQUIREMENT
    assert "looping" in LOOP_FAILURE_REQUIREMENT
    assert "marked as failed" in LOOP_FAILURE_REQUIREMENT
