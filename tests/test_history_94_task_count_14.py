"""History: 14 is the confirmed task count after adding the rotating task."""

from tasks import TASKS, reasoningbg


def test_registry_has_fourteen_unique_tasks():
    ids = [task["id"] for task in TASKS]

    assert len(ids) == 14
    assert len(set(ids)) == 14
    assert ids[-1] == reasoningbg.ID
