"""History: explain all seven task IDs before any results are available."""

from pathlib import Path

from tasks import TASKS


HTML = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_empty_state_lists_every_task_with_a_description():
    assert "const TASK_DESCRIPTIONS =" in HTML
    assert "TASKS.map(t => `<li><strong>${t.id}</strong>: ${TASK_DESCRIPTIONS[t.id]}</li>`)" in HTML
    descriptions = HTML.split("const TASK_DESCRIPTIONS = {", 1)[1].split("};", 1)[0]
    for task in TASKS:
        assert task["id"] + ":" in descriptions
        assert descriptions.count(task["id"] + ":") == 1
