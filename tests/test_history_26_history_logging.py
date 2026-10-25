"""History: log the request to follow AGENTS.md in the history file."""

from pathlib import Path


def test_history_records_this_request_and_has_a_dedicated_test_file():
    root = Path(__file__).parents[1]
    history = (root / "History.md").read_text(encoding="utf-8")
    assert "update history.md as per agents.md" in history
    assert (root / "tests" / "test_history_26_history_logging.py").is_file()
