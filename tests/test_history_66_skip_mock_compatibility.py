"""History mapping: retain skip support and update test doubles accordingly."""
from pathlib import Path


def test_skip_mock_compatibility_decision_is_recorded():
    history = Path(__file__).parents[1] / "History.md"
    assert (
        "Confirmed: keep skip support and update test doubles to accept the "
        "optional should_skip callback."
    ) in history.read_text(encoding="utf-8")
