"""Bulgarian spelling and grammar multiple-choice benchmark task."""

from __future__ import annotations

from pathlib import Path
from typing import Final, Optional, Tuple

from .bulmmlu import (
    CsvFormatError,
    OPTIONS,
    Question,
    create_task,
    load_questions as parse_questions,
)

CSV_PATH: Final = Path(__file__).resolve().parent / "BulMMLU" / "Spelling and Grammar.csv"
ID: Final = "spelling_grammar"

_TASK: Final = create_task(ID, "Bulgarian spelling and grammar", CSV_PATH)
QUESTIONS: Final = _TASK.questions
PROMPT: Final = _TASK.prompt


def load_questions(path: Path) -> Tuple[Question, ...]:
    return parse_questions(path)


def check(text: Optional[str]) -> bool:
    return _TASK.check(text)


def explain(text: Optional[str]) -> str:
    return _TASK.explain(text)


__all__ = (
    "CSV_PATH",
    "CsvFormatError",
    "ID",
    "OPTIONS",
    "PROMPT",
    "QUESTIONS",
    "Question",
    "check",
    "explain",
    "load_questions",
)
