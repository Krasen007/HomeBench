"""History: simple weather task with skill guidance and Celsius checking."""

from tasks import weather


def test_weather_prompt_contains_skill_guidance():
    prompt = weather.PROMPT
    assert "weather" in prompt.lower()
    assert "wttr.in" in prompt
    assert "Varna" in prompt
    assert "Celsius" in prompt


def test_weather_checker_accepts_celsius_temperatures():
    assert weather.check("17°C")
    assert weather.check("17 C")
    assert weather.check("17 degrees celsius")


def test_weather_checker_rejects_non_celsius():
    assert not weather.check("17°F")
    assert not weather.check("Partly cloudy")
    assert not weather.check("")
    assert not weather.check(None)


def test_weather_checker_rejects_out_of_range():
    assert not weather.check("100°C")
    assert not weather.check("-100°C")
