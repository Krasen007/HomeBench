"""History: add agentic weather task that tests tool/skill usage.

The weather task embeds the openclaw weather skill and asks the model to check
the current weather in Varna for today, answering with the temperature in
degrees Celsius.
"""

from tasks import weather


def test_weather_task_accepts_celsius_temperature():
    """A model answer containing a temperature in °C should pass."""
    assert weather.check("The temperature in Varna is 18°C.")
    assert weather.explain("The temperature in Varna is 18°C.").startswith("PASS:")


def test_weather_task_accepts_decimal_celsius():
    """Decimal Celsius values should also pass."""
    assert weather.check("Current temperature: 22.5°C")
    assert weather.explain("Current temperature: 22.5°C").startswith("PASS:")


def test_weather_task_accepts_negative_celsius():
    """Negative Celsius values should pass."""
    assert weather.check("-5°C")
    assert weather.explain("-5°C").startswith("PASS:")


def test_weather_task_rejects_no_temperature():
    """An answer without any Celsius temperature should fail."""
    assert not weather.check("It is sunny in Varna today.")
    assert weather.explain("It is sunny in Varna today.").startswith("FAIL:")


def test_weather_task_rejects_empty_output():
    """Empty output should fail."""
    assert not weather.check("")
    assert not weather.check(None)
    assert weather.explain("").startswith("FAIL:")
