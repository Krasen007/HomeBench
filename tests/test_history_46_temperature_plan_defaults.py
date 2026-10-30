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


def test_history_records_corrected_temperature_plan_defaults():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert (
        "i meant to add another add temperature so it will be default 0 "
        "next add is 0.6 and the next one is 1.0"
    ) in history
    assert (ROOT / "tests" / "test_history_46_temperature_plan_defaults.py").is_file()
