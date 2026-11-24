from . import (
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

TASKS = [
    {"id": m.ID, "prompt": m.PROMPT, "check": m.check, "explain": m.explain}
    for m in (
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
    )
]

TASKS.append({
    "id": reasoningbg.ID,
    "prompt": reasoningbg.PROMPT,
    "check": reasoningbg.check,
    "explain": reasoningbg.explain,
    "prompt_for_run": reasoningbg.prompt_for_run,
    "check_for_run": reasoningbg.check_for_run,
    "explain_for_run": reasoningbg.explain_for_run,
})

TASKS.append({
    "id": reasoningbg_full.ID,
    "prompt": reasoningbg_full.PROMPT,
    "check": reasoningbg_full.check,
    "explain": reasoningbg_full.explain,
    "items_for_run": reasoningbg_full.items_for_run,
    "render_output": reasoningbg_full.render_output,
    "aggregate": reasoningbg_full.aggregate,
})
