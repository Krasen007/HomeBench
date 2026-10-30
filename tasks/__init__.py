from . import math, logic, instructions, json_task, code_task, game, bulgarian, weather, game_solved

TASKS = [
    {"id": m.ID, "prompt": m.PROMPT, "check": m.check, "explain": m.explain}
    for m in (math, logic, instructions, json_task, code_task, game, bulgarian, weather, game_solved)
]