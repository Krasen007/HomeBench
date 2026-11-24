"""History: keep each task prompt and checker in its own module."""

from tasks import (
    TASKS,
    april_uprising,
    bulgarian,
    code_task,
    contemporary_bulgarian_poets,
    game,
    game_solved,
    instructions,
    json_task,
    logic,
    math,
    modern_economy_of_bulgaria,
    reasoningbg,
    reasoningbg_full,
    spelling_grammar,
    weather,
)


def test_all_registered_tasks_have_separate_prompt_check_and_explanation():
    modules = (
        math,
        logic,
        instructions,
        json_task,
        code_task,
        game,
        bulgarian,
        weather,
        game_solved,
        spelling_grammar,
        april_uprising,
        contemporary_bulgarian_poets,
        modern_economy_of_bulgaria,
        reasoningbg,
        reasoningbg_full,
    )
    assert [task["id"] for task in TASKS] == [module.ID for module in modules]
    for module, task in zip(modules, TASKS):
        assert task["prompt"] == module.PROMPT
        assert task["check"] is module.check
        assert task["explain"] is module.explain
