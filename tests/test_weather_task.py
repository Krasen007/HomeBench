"""History: simple weather task accepts any realistic Celsius temperature.

The weather task embeds the openclaw weather skill and asks the model to check
the weather in Varna for today, answering with the temperature in degrees
Celsius. The checker accepts any bare Celsius value in a realistic range.
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


def test_weather_task_accepts_celsius_suffix_variants():
    """Various Celsius suffixes should be accepted."""
    for answer in ("18 C", "18 degrees celsius"):
        assert weather.check(answer), answer


def test_weather_task_rejects_no_temperature():
    """An answer without any Celsius temperature should fail."""
    assert not weather.check("It is sunny in Varna today.")
    assert weather.explain("It is sunny in Varna today.").startswith("FAIL:")


def test_weather_task_requires_temperature_after_tool_call():
    output = '''{
      "tool": "web_fetch",
      "args": {"url": "https://wttr.in/Varna?format=j2"}
    }'''

    assert not weather.check(output)
    reason = weather.explain(output)
    assert "no temperature in degrees Celsius" in reason


def test_weather_prompt_describes_supported_executable_tool():
    assert "HomeBench executes one constrained web_fetch request" in weather.PROMPT
    assert "https://wttr.in/Varna?format=j2" in weather.PROMPT
    assert "Do not request shell commands or any other tool." in weather.PROMPT


def test_weather_task_rejects_empty_output():
    """Empty output should fail."""
    assert not weather.check("")
    assert not weather.check(None)
    assert weather.explain("").startswith("FAIL:")


def test_weather_task_rejects_out_of_range_temperature():
    """Temperatures outside a realistic range should fail."""
    assert not weather.check("100°C")
    assert not weather.check("-100°C")
