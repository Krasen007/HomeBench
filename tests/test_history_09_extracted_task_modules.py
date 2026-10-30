"""History: keep each task prompt and checker in its own module."""

from tasks import (
    TASKS, bulgarian, code_task, game, instructions, json_task, logic, math,
    weather, game_solved,
)


def test_all_registered_tasks_have_separate_prompt_check_and_explanation():
    modules = (math, logic, instructions, json_task, code_task, game, bulgarian, weather, game_solved)
    assert [task["id"] for task in TASKS] == [module.ID for module in modules]
    for module, task in zip(modules, TASKS):
        assert task["prompt"] == module.PROMPT
        assert task["check"] is module.check
        assert task["explain"] is module.explain
