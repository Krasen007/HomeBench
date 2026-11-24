"""History: place the active benchmark row first in the default date sort."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_active_model_uses_the_current_time_as_its_latest_batch():
    latest_batch = HTML.split("function latestBatchFor(model)", 1)[1].split(
        "function formatDateTime", 1
    )[0]

    assert "if (benchRunning && model === benchModel)" in latest_batch
    assert "batches.push(Date.now() / 1000);" in latest_batch


def test_default_date_sort_is_newest_first():
    assert "let sortKey = 'date', sortDir = -1;" in HTML
