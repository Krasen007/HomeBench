"""History: execute only a constrained live weather web_fetch tool request."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import homebench
from tasks import weather


ROOT = Path(__file__).parents[1]
TOOL_REQUEST = json.dumps({
    "tool": "web_fetch",
    "args": {"url": "https://wttr.in/Varna?format=j2"},
})


def _weather_response(temperature="18"):
    response = MagicMock()
    response.read.return_value = json.dumps({
        "current_condition": [{"temp_C": temperature}],
    }).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_weather_tool_request_is_parsed_and_allowlisted():
    parsed = weather.parse_tool_request(TOOL_REQUEST)

    assert parsed["tool"] == "web_fetch"
    assert parsed["args"]["url"] == "https://wttr.in/Varna?format=j2"
    assert weather.parse_tool_request("18°C") is None


def test_weather_tool_rejects_non_allowlisted_requests():
    for request in (
        {"tool": "curl", "args": {"url": "https://wttr.in/Varna?format=j2"}},
        {"tool": "web_fetch", "args": {"url": "http://wttr.in/Varna?format=j2"}},
        {"tool": "web_fetch", "args": {"url": "https://example.com/"}},
        {"tool": "web_fetch", "args": {"url": "https://wttr.in/other?format=j2"}},
    ):
        try:
            weather.parse_tool_request(json.dumps(request))
        except ValueError:
            continue
        raise AssertionError(f"unsafe tool request was accepted: {request!r}")


def test_weather_tool_executes_https_request_and_returns_temperature():
    opener = MagicMock()
    opener.open.return_value = _weather_response("18")
    with patch("tasks.weather.urllib.request.build_opener",
               return_value=opener) as build_opener:
        result = weather.execute_tool_request(json.loads(TOOL_REQUEST))

    assert result == {"temperature_c": 18.0}
    build_opener.assert_called_once()
    opener.open.assert_called_once()
    assert opener.open.call_args.kwargs["timeout"] == 20


def test_weather_benchmark_runs_tool_then_checks_final_answer_matches(
        tmp_path, monkeypatch):
    task = {
        "id": "weather",
        "prompt": weather.PROMPT,
        "check": weather.check,
        "explain": weather.explain,
    }
    monkeypatch.setattr(homebench, "TASKS", [task])
    responses = iter((TOOL_REQUEST, "18°C"))
    prompts = []

    def fake_chat(url, prompt, temperature, max_tokens, timeout, **kwargs):
        prompts.append(prompt)
        return next(responses)

    monkeypatch.setattr(homebench, "chat", fake_chat)
    monkeypatch.setattr(
        weather, "execute_tool_request", lambda request, timeout: {"temperature_c": 18.0}
    )
    out = tmp_path / "results.jsonl"

    homebench.run_benchmark(
        "http://localhost:8080", "weather-model", 1, 0, 2048, 30, out,
    )

    row = json.loads(out.read_text(encoding="utf-8").strip())
    assert row["passed"] is True
    assert row["reason"] == "PASS: temperature in Varna is 18.0°C"
    assert "Weather tool result" in row["output"]
    assert row["output"].endswith("Final answer:\n18°C")
    assert "temperature_c" in prompts[1]


def test_weather_answer_must_match_actual_observation():
    passed, reason = weather._weather_status("19°C", expected_temperature=18)

    assert not passed
    assert "does not match the live weather observation" in reason


def test_tool_execution_failure_is_visible_in_saved_benchmark_result(
        tmp_path, monkeypatch):
    task = {"id": "weather", "prompt": "", "check": weather.check}
    monkeypatch.setattr(homebench, "TASKS", [task])
    monkeypatch.setattr(homebench, "chat", lambda *args, **kwargs: TOOL_REQUEST)
    monkeypatch.setattr(
        weather, "execute_tool_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("weather timed out")),
    )
    out = tmp_path / "results.jsonl"

    homebench.run_benchmark("http://localhost:8080", "m", 1, 0, 100, 30, out)

    row = json.loads(out.read_text(encoding="utf-8").strip())
    assert row["passed"] is False
    assert "Weather tool error:\nweather timed out" in row["output"]
    assert "weather tool could not be executed" in row["reason"]


def test_history_records_live_allowlisted_weather_tool_behavior():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert (
        "execute the weather task's exact allowlisted wttr.in web_fetch request"
    ) in history
    assert (
        ROOT / "tests" / "test_history_58_execute_allowlisted_weather_tool.py"
    ).is_file()
