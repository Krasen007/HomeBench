"""Modern economy of Bulgaria multiple-choice benchmark task."""

from __future__ import annotations

from pathlib import Path
from typing import Final, Optional

from .bulmmlu import create_task

CSV_PATH: Final = Path(__file__).resolve().parent / "BulMMLU" / "Modern economy of Bulgaria.csv"
ID: Final = "modern_economy_of_bulgaria"

_TASK: Final = create_task(ID, "the modern economy of Bulgaria", CSV_PATH)
QUESTIONS: Final = _TASK.questions
PROMPT: Final = _TASK.prompt


def check(text: Optional[str]) -> bool:
    return _TASK.check(text)


def explain(text: Optional[str]) -> str:
    return _TASK.explain(text)
