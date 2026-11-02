"""History: show the running plan's row immediately with pending task cells."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
SOURCE = (ROOT / "homebench.py").read_text(encoding="utf-8")


def test_running_model_row_is_added_before_its_first_result():
    assert "if (benchRunning && benchModel) modelSet.add(benchModel);" in HTML


def test_queued_tasks_render_pending_until_they_have_results():
    render = HTML.split("function render()", 1)[1].split(
        "async function editModelName", 1
    )[0]

    assert (
        "const awaitingRun = benchRunning && m === benchModel "
        "&& activeTasks.includes(t.id);"
    ) in render
    assert "const awaitingResult = awaitingRun && rs.length === 0;" in render
    assert (
        "text = pending ? (benchPhase || 'running') "
        ": (awaitingResult ? 'pending' : '-');"
    ) in render
    assert "if (awaitingResult && !pending) cls += ' pending';" in render
    assert "if (pending) cls += ' running';" in render
    assert "not completed yet" in render


def test_poll_caches_queued_tasks_and_temperature():
    poll = HTML.split("async function poll()", 1)[1].split(
        "$('detect').onclick", 1
    )[0]

    assert "activeTasks = Array.isArray(s.tasks) ? s.tasks : [];" in poll
    assert (
        "benchTemperature = Number.isFinite(s.temperature) ? s.temperature : null;"
    ) in poll


def test_currently_running_predicate_is_unchanged():
    assert (
        "const pending = benchRunning && m === benchModel "
        "&& pendingTask === t.id && pendingRun === nextRun;"
    ) in HTML


def test_status_exposes_queued_tasks_and_temperature():
    assert '"tasks": list(task_ids)' in SOURCE
    assert '"temperature": None' in SOURCE
    assert 'state["temperature"] = plan["temperature"]' in SOURCE
