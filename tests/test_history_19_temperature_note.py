"""History: append the sampling temperature to the saved run note."""

from homebench import _format_note


def test_temperature_is_added_with_or_without_a_custom_note():
    assert _format_note("baseline", 0.7) == "baseline (temp=0.7)"
    assert _format_note("", 0.0) == "temp=0.0"
