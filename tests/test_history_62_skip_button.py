"""History: skip button in the web UI posts /api/skip while a benchmark runs."""
from pathlib import Path

PAGE = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_skip_button_exists_and_calls_api_skip():
    assert 'id="skip"' in PAGE
    assert 'type="button"' in PAGE
    assert "/api/skip" in PAGE
    assert "Skipping current task" in PAGE


def test_skip_button_visibility_tracks_running_state():
    assert "$('skip').hidden = !s.running;" in PAGE
