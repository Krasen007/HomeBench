"""History: use a deterministic fixture and require its exact Celsius value."""

from tasks import weather


def test_weather_prompt_contains_fixture_observation():
    assert f'"temp_C": "{weather.EXPECTED_C}"' in weather.PROMPT
    assert "simulated" in weather.PROMPT


def test_weather_checker_requires_a_bare_answer_matching_fixture():
    assert weather.check(f"{weather.EXPECTED_C}°C")
    assert weather.check(f"{weather.EXPECTED_C} celsius")
    assert not weather.check("15°C")
    assert not weather.check("The answer is 17°C")


def test_weather_task_identifies_the_fixture_as_simulated():
    prompt = weather._make_prompt("TEST SKILL CONTENT")
    assert "simulated result" in prompt
    assert "not live data" in prompt
