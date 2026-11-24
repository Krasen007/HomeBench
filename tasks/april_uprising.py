"""April Uprising multiple-choice benchmark task."""

from __future__ import annotations

from pathlib import Path
from typing import Final, Optional

from .bulmmlu import create_task

CSV_PATH: Final = Path(__file__).resolve().parent / "BulMMLU" / "April Uprising.csv"
ID: Final = "april_uprising"

_TASK: Final = create_task(ID, "the April Uprising", CSV_PATH)
QUESTIONS: Final = _TASK.questions
PROMPT: Final = _TASK.prompt


def check(text: Optional[str]) -> bool:
    return _TASK.check(text)


def explain(text: Optional[str]) -> str:
    return _TASK.explain(text)
