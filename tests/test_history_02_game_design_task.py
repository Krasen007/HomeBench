"""History: add the toddler-game design document as a benchmark task."""

from tasks import game
from tasks import TASKS


def test_game_design_is_a_registered_task_with_required_design_details():
    task = next(task for task in TASKS if task["id"] == "game")
    for phrase in ("3-year-old toddler", "Yellow coins", "Red coin",
                   "Green coins", "200 total coins", "single ```html code block"):
        assert phrase.lower() in task["prompt"].lower()
    assert game.PROMPT == task["prompt"]
