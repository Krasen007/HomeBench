"""History: keep backward-compatible task check and explanation aliases."""

import homebench
from tasks import bulgarian, code_task, game, instructions, json_task, logic, math


def test_aliases_reference_the_extracted_task_functions():
    for suffix, module in (
        ("math", math), ("logic", logic), ("instructions", instructions),
        ("json", json_task), ("code", code_task), ("game", game),
        ("bg_article", bulgarian),
    ):
        assert getattr(homebench, "check_" + suffix) is module.check
        assert getattr(homebench, "explain_" + suffix) is module.explain
