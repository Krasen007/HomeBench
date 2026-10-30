"""History: stream live model output and reasoning without blocking the UI."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import homebench


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")


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


def test_chat_streams_content_and_reasoning_as_the_chunks_arrive():
    response = _stream_response([
        {"choices": [{"delta": {"reasoning_content": "thinking "},
                      "finish_reason": None}]},
        {"choices": [{"delta": {"content": "<html>"},
                      "finish_reason": None}]},
        {"choices": [{"delta": {}, "finish_reason": "stop"}]},
    ])
    chunks = []
    with patch("homebench.urllib.request.urlopen", return_value=response) as urlopen:
        result = homebench.chat(
            "http://localhost:1234", "prompt", 0.2, 1024, 30,
            on_token=chunks.append,
        )

    assert result == "<html>"
    assert chunks == [
        {"content": "", "reasoning": "thinking "},
        {"content": "<html>", "reasoning": ""},
    ]
    request = urlopen.call_args.args[0]
    assert json.loads(request.data)["stream"] is True


def test_run_benchmark_marks_stream_start_and_forwards_model_chunks(
        tmp_path, monkeypatch):
    task = {"id": "math", "prompt": "", "check": lambda _: True}
    monkeypatch.setattr(homebench, "TASKS", [task])
    captured = []

    def fake_chat(*args, on_token=None):
        on_token({"content": "partial", "reasoning": ""})
        return "complete"

    monkeypatch.setattr(homebench, "chat", fake_chat)
    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0, 100, 30,
        tmp_path / "results.jsonl",
        on_token=lambda task_id, run, chunk: captured.append(
            (task_id, run, chunk)
        ),
    )

    assert captured == [
        ("math", 0, {"start": True}),
        ("math", 0, {"content": "partial", "reasoning": ""}),
    ]


def test_ui_displays_live_answer_and_reasoning_in_scrollable_independent_panes():
    assert 'id="liveStream"' in HTML
    assert 'id="liveOutput"' in HTML
    assert 'id="liveReasoning"' in HTML
    assert "$('liveOutput').textContent = s.stream_output" in HTML
    assert "$('liveReasoning').textContent = s.stream_reasoning" in HTML
    assert "max-height: 260px;" in CSS
    assert "overflow: auto;" in CSS
    poll = HTML.split("async function poll()", 1)[1].split(
        "$('detect').onclick", 1
    )[0]
    assert "d.scrollIntoView" not in poll


def test_history_records_live_streaming_request():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert (
        "show the reasoning or output tokens of the model in real time"
    ) in history
    assert (ROOT / "tests" / "test_history_55_live_model_streaming.py").is_file()
