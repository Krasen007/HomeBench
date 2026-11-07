"""History: accept the bare observed number after the live weather tool runs."""

import json

import homebench
from tasks import weather


TOOL_REQUEST = json.dumps({
    "tool": "web_fetch",
    "args": {"url": "https://wttr.in/Varna?format=j2"},
})


def test_bare_decimal_matching_the_observation_passes():
    passed, reason = weather._weather_status("13.0", expected_temperature=13.0)

    assert passed, reason
    assert reason == "PASS: temperature in Varna is 13.0°C"


def test_bare_integer_matching_the_observation_passes():
    passed, reason = weather._weather_status("13", expected_temperature=13.0)

    assert passed, reason


def test_backticked_bare_number_matching_the_observation_passes():
    assert weather._weather_status("`13.0`", expected_temperature=13.0)[0]


def test_bare_number_not_matching_the_observation_fails():
    passed, reason = weather._weather_status("14", expected_temperature=13.0)

    assert not passed
    assert "does not match the live weather observation" in reason


def test_bare_number_without_an_observation_keeps_the_unit_requirement():
    assert not weather.check("13.0")
    assert weather.explain("13.0").startswith("FAIL:")


def test_celsius_answer_still_passes_with_an_observation():
    passed, reason = weather._weather_status("13.0°C", expected_temperature=13.0)

    assert passed, reason


def test_fahrenheit_answer_is_not_accepted_as_celsius():
    passed, _ = weather._weather_status("13.0°F", expected_temperature=13.0)

    assert not passed


def test_follow_up_prompt_shows_the_observed_temperature_with_the_unit():
    prompt = weather.follow_up_prompt({"temperature_c": 13.0})

    assert "13.0°C" in prompt
    assert "Do not request another tool." in prompt


def test_benchmark_passes_a_bare_observed_number(tmp_path, monkeypatch):
    task = {
        "id": "weather",
        "prompt": weather.PROMPT,
        "check": weather.check,
        "explain": weather.explain,
    }
    monkeypatch.setattr(homebench, "TASKS", [task])
    responses = iter((TOOL_REQUEST, "13.0"))
    monkeypatch.setattr(homebench, "chat", lambda *args, **kwargs: next(responses))
    monkeypatch.setattr(
        weather, "execute_tool_request",
        lambda request, timeout: {"temperature_c": 13.0},
    )
    out = tmp_path / "results.jsonl"

    homebench.run_benchmark(
        "http://localhost:8080", "weather-model", 1, 0.0, 64, 30, out,
    )

    row = json.loads(out.read_text(encoding="utf-8").strip())
    assert row["passed"] is True
    assert row["reason"] == "PASS: temperature in Varna is 13.0°C"
    assert row["output"].endswith("Final answer:\n13.0")
