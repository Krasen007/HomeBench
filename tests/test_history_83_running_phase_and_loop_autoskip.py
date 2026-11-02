"""History: show reasoning vs. answer generation in the running task cell."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
SOURCE = (ROOT / "homebench.py").read_text(encoding="utf-8")


def test_backend_stream_phase_tracks_reasoning_and_answer_generation():
    assert 'state["stream_phase"] = chunk.get("phase", "starting")' in SOURCE
    assert 'state["stream_phase"] = "reasoning"' in SOURCE
    assert 'state["stream_phase"] = "generating answer"' in SOURCE


def test_table_running_cell_uses_the_live_phase():
    render = HTML.split("function render()", 1)[1].split(
        "async function editModelName", 1
    )[0]
    poll = HTML.split("async function poll()", 1)[1].split(
        "$('detect').onclick", 1
    )[0]

    assert (
        "text = pending ? (benchPhase || 'running') "
        ": (awaitingResult ? 'pending' : '-');"
    ) in render
    assert "currently ${benchPhase}" in render
    assert "benchPhase = s.stream_phase || '';" in poll
    assert "benchPhase = '';" in poll
