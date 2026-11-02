"""History mapping: request to run and check the whole test suite."""
from pathlib import Path


def test_full_suite_validation_request_is_recorded():
    history = Path(__file__).parents[1] / "History-v1.2.md"
    assert "lets run the whole suite and check if everything is ok" in (
        history.read_text(encoding="utf-8")
    )
