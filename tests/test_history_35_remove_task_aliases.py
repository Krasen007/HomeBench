"""History: remove unused top-level task check/explain aliases."""

import homebench


def test_homebench_does_not_export_task_check_or_explain_functions():
    assert not [
        name
        for name in vars(homebench)
        if name.startswith(("check_", "explain_"))
    ]
