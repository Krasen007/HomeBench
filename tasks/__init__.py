from . import math, logic, instructions, json_task, code_task, game, bulgarian, weather

TASKS = [
    {"id": m.ID, "prompt": m.PROMPT, "check": m.check, "explain": m.explain}
    for m in (math, logic, instructions, json_task, code_task, game, bulgarian, weather)
]