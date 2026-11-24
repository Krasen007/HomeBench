"""Shared engine for BulMMLU multiple-choice CSV benchmark tasks."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Final, List, NamedTuple, Optional, Tuple

OPTIONS: Final = ("A", "B", "C", "D")


class CsvFormatError(ValueError):
    """Raised when a BulMMLU CSV row cannot be parsed."""

    def __init__(self, row: int, detail: str) -> None:
        super().__init__(f"CSV row {row} has {detail}")
        self.row: int = row
        self.detail: str = detail


class Question(NamedTuple):
    text: str
    options: Tuple[str, str, str, str]
    answer: str


def load_questions(path: Path) -> Tuple[Question, ...]:
    """Parse a headerless six-column BulMMLU CSV into validated questions."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle, delimiter=";"))

    questions: List[Question] = []
    for number, row in enumerate(rows, 1):
        if len(row) != 6:
            raise CsvFormatError(number, f"{len(row)} columns; expected 6")
        answer = row[5].strip().upper()
        if answer not in OPTIONS:
            raise CsvFormatError(number, f"invalid answer {row[5]!r}")
        questions.append(
            Question(
                text=row[0].strip(),
                options=(row[1], row[2], row[3], row[4]),
                answer=answer,
            )
        )
    return tuple(questions)


def build_prompt(subject: str, questions: Tuple[Question, ...]) -> str:
    """Build the ordered-answer prompt for one BulMMLU question set."""
    lines = [
        f"Answer every multiple-choice question about {subject} below.",
        "For each question, output one line containing only A, B, C, or D.",
        "Keep the same order and do not include explanations or numbering.",
        "",
    ]
    for number, question in enumerate(questions, 1):
        lines.append(f"{number}. {question.text}")
        for label, option in zip(OPTIONS, question.options):
            lines.append(f"   {label}) {option}")
        lines.append("")
    return "\n".join(lines)


_ANSWER_LINE = re.compile(
    r"^\s*(?:\d+[\).:]\s*|[-*]\s+)?\*{0,2}([ABCD])\*{0,2}(?:[\).:\-–—\s].*)?$",
    re.IGNORECASE,
)
_ANSWER_TOKEN = re.compile(r"(?<![A-Za-z])[ABCD](?![A-Za-z])", re.IGNORECASE)
_CYRILLIC_TO_LATIN = str.maketrans({
    "А": "A", "В": "B", "С": "C", "Д": "D",
    "а": "a", "в": "b", "с": "c", "д": "d",
})


def extract_answers(text: str, question_count: int) -> List[str]:
    """Extract option letters from a model answer, preferring line-aligned values."""
    normalized = text.translate(_CYRILLIC_TO_LATIN)
    line_answers = [match.group(1).upper() for match in _ANSWER_LINE.finditer(normalized)]
    if len(line_answers) == question_count:
        return line_answers
    token_answers = [match.group(0).upper() for match in _ANSWER_TOKEN.finditer(normalized)]
    if len(token_answers) == question_count:
        return token_answers
    return line_answers or token_answers


def answer_status(text: Optional[str], questions: Tuple[Question, ...]) -> Tuple[bool, str]:
    """Check an ordered answer sheet against the supplied questions."""
    if not isinstance(text, str) or not text.strip():
        return False, "FAIL: no model output received"

    answers = extract_answers(text, len(questions))
    expected = [question.answer for question in questions]
    correct = sum(actual == wanted for actual, wanted in zip(answers, expected))
    if len(answers) != len(expected):
        return False, (
            f"FAIL: expected {len(expected)} answers, got {len(answers)} "
            f"({correct}/{len(expected)} correct)"
        )

    wrong: List[str] = []
    for number, (actual, wanted) in enumerate(zip(answers, expected), 1):
        if actual != wanted:
            wrong.append(f"Q{number}: expected {wanted}, got {actual}")
    if wrong:
        preview = "; ".join(wrong[:5])
        if len(wrong) > 5:
            preview += f" (+{len(wrong) - 5} more)"
        return False, f"FAIL: {correct}/{len(expected)} correct; {preview}"
    return True, f"PASS: all {len(expected)} answers match"


class MultipleChoiceTask(NamedTuple):
    task_id: str
    questions: Tuple[Question, ...]
    prompt: str

    def status(self, text: Optional[str]) -> Tuple[bool, str]:
        return answer_status(text, self.questions)

    def check(self, text: Optional[str]) -> bool:
        return self.status(text)[0]

    def explain(self, text: Optional[str]) -> str:
        return self.status(text)[1]


def create_task(task_id: str, subject: str, csv_path: Path) -> MultipleChoiceTask:
    """Load a CSV and build the benchmark task it defines."""
    questions = load_questions(csv_path)
    return MultipleChoiceTask(
        task_id=task_id,
        questions=questions,
        prompt=build_prompt(subject, questions),
    )
