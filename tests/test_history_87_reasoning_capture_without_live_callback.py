"""History: capture reasoning even when no live token callback is supplied."""

import json
from pathlib import Path

import homebench
from tasks import weather


ROOT = Path(__file__).parents[1]
TOOL_REQUEST = json.dumps({
    "tool": "web_fetch",
    "args": {"url": "https://wttr.in/Varna?format=j2"},
})


def test_weather_request_and_follow_up_capture_reasoning_without_live_callback(
        monkeypatch, tmp_path):
    task = {
        "id": weather.ID,
        "prompt": weather.PROMPT,
        "check": weather.check,
        "explain": weather.explain,
    }
    monkeypatch.setattr(homebench, "TASKS", [task])
    responses = iter((TOOL_REQUEST, "13.0°C"))
    reasoning = iter(("tool reasoning ", "answer reasoning"))
    calls = []

    def fake_chat(*args, on_token=None, **kwargs):
        assert callable(on_token)
        calls.append(on_token)
        on_token({"content": "", "reasoning": next(reasoning)})
        return next(responses)

    monkeypatch.setattr(homebench, "chat", fake_chat)
    monkeypatch.setattr(
        weather, "execute_tool_request",
        lambda request, timeout: {"temperature_c": 13.0},
    )
    out = tmp_path / "results.jsonl"

    homebench.run_benchmark(
        "http://localhost:8080", "weather-model", 1, 0.0, 64, 30, out,
    )

    row = json.loads(out.read_text(encoding="utf-8").strip())
    assert len(calls) == 2
    assert row["reasoning"] == "tool reasoning answer reasoning"
    assert row["passed"] is True


REQUEST = (
    "always pass capture_token as the token callback, regardless of whether "
    "on_token is set"
)


def test_history_records_reasoning_capture_request():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert REQUEST in history
    assert (
        ROOT / "tests" /
        "test_history_87_reasoning_capture_without_live_callback.py"
    ).is_file()
