"""History: show reasoning vs. answer generation and auto-skip repeated loops."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import homebench


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
SOURCE = (ROOT / "homebench.py").read_text(encoding="utf-8")


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


def test_backend_stream_phase_tracks_reasoning_and_answer_generation():
    assert 'state["stream_phase"] = chunk.get("phase", "starting")' in SOURCE
    assert 'state["stream_phase"] = "reasoning"' in SOURCE
    assert 'state["stream_phase"] = "generating answer"' in SOURCE


def test_table_running_cell_uses_the_live_phase():
    render = HTML.split("function render()", 1)[1].split(
        "async function editModelName", 1
    )[0]
    poll = HTML.split("async function poll()", 1)[1].split(
        "$('detect').onclick", 1
    )[0]

    assert (
        "text = pending ? (benchPhase || 'running') "
        ": (awaitingResult ? 'pending' : '-');"
    ) in render
    assert "currently ${benchPhase}" in render
    assert "benchPhase = s.stream_phase || '';" in poll
    assert "benchPhase = '';" in poll


def test_repetition_loop_detector_flags_repeated_answer_text():
    phrase = "The cat sat on the mat. "
    assert homebench._detect_repetition_loop(phrase * 20)


def test_repetition_loop_detector_ignores_normal_answer_text():
    text = " ".join(
        f"Sentence {index} contains a different number." for index in range(60)
    )
    assert not homebench._detect_repetition_loop(text)


def test_chat_auto_skips_a_looping_answer():
    phrase = "I keep saying the same thing over and over. "
    response = _stream_response(_delta_events([phrase] * 15, "content"))
    with patch("homebench.urllib.request.urlopen", return_value=response):
        with pytest.raises(homebench._SkipRequested) as excinfo:
            homebench.chat(
                "http://localhost:1234", "prompt", 0.2, 1024, 30,
            )

    assert "repetition loop detected" in str(excinfo.value)


def test_chat_auto_skips_a_looping_reasoning_block():
    chunk = "Let me think about this again. "
    response = _stream_response(_delta_events([chunk] * 30, "reasoning_content"))
    with patch("homebench.urllib.request.urlopen", return_value=response):
        with pytest.raises(homebench._SkipRequested) as excinfo:
            homebench.chat(
                "http://localhost:1234", "prompt", 0.2, 1024, 30,
            )

    assert "repetition loop detected" in str(excinfo.value)


def test_run_benchmark_records_the_loop_auto_skip_reason(monkeypatch, tmp_path):
    def fake_chat(*args, **kwargs):
        raise homebench._SkipRequested("repetition loop detected")

    monkeypatch.setattr(homebench, "chat", fake_chat)
    path = tmp_path / "results.jsonl"
    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 8, 5, str(path),
        task_ids=["math"],
    )

    rows = homebench.load_rows(str(path))
    assert len(rows) == 1
    assert rows[0]["status"] == "skipped"
    assert rows[0]["passed"] is None
    assert rows[0]["reason"] == "SKIP: repetition loop detected"
