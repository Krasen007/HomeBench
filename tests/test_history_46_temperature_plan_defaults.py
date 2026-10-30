"""History: default plan temperatures are 0.0, then 0.6, then 1.0."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_initial_temperature_plan_defaults_to_zero():
    assert "addPlanRow(1, 0.0);" in HTML


def test_added_temperature_plans_default_to_point_six_then_one():
    assert "let nextPlanTemperature = 0.6;" in HTML
    assert "addPlanRow(1, nextPlanTemperature);" in HTML
    assert "nextPlanTemperature = 1.0;" in HTML
