"""History: record the daily benchmark summary and commit request."""

from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_history_records_today_summary_and_commit_request():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert (
        "Summarize today's benchmark changes and commit the pending worktree changes."
        in history
    )
    assert "tests/test_history_104_daily_summary_and_commit.py" in history
