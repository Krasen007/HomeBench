"""History: simple weather checker accepts any realistic Celsius temperature."""

from tasks import weather


def test_weather_checker_accepts_realistic_celsius_temperatures():
    assert weather.check("18°C")
    assert weather.check("22.5°C")
    assert weather.check("-5°C")


def test_weather_checker_rejects_no_temperature():
    assert not weather.check("It is sunny today.")
    assert weather.explain("It is sunny today.").startswith("FAIL:")


def test_weather_checker_rejects_empty_output():
    assert not weather.check("")
    assert not weather.check(None)


def test_weather_checker_rejects_out_of_range_temperatures():
    assert not weather.check("100°C")
    assert not weather.check("-100°C")
