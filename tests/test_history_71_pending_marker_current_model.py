"""History: scope the currently-running marker to the active plan's model."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
SOURCE = (ROOT / "homebench.py").read_text(encoding="utf-8")


def test_pending_marker_requires_the_running_plan_model():
    render = HTML.split("function render()", 1)[1].split(
        "async function editModelName", 1
    )[0]

    assert "let benchModel = '';" in HTML
    assert (
        "const pending = benchRunning && m === benchModel "
        "&& pendingTask === t.id && pendingRun === nextRun;"
    ) in render


def test_poll_tracks_and_resets_the_running_plan_model():
    poll = HTML.split("async function poll()", 1)[1].split(
        "$('detect').onclick", 1
    )[0]

    assert "benchModel = s.model || '';" in poll
    assert "benchModel = '';" in poll


def test_run_endpoint_still_labels_the_running_plan():
    assert 'state.update({"running": True, "model": name' in SOURCE
