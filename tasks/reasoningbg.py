"""Rotating Bulgarian reading-comprehension benchmark task.

Each text in tasks/ReasoningBG contains a passage, ten multiple-choice
questions and an answer key. One task id covers the whole folder: run N uses
file N modulo the number of files, so repeated runs cover every text in order.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Final, List, NamedTuple, Optional, Tuple

from .bulmmlu import OPTIONS, Question, answer_status

TEXT_DIR: Final = Path(__file__).resolve().parent / "ReasoningBG"
ID: Final = "reasoningbg"

_QUESTION_MARKER: Final = "Въпроси"
_ANSWER_MARKER: Final = "Отговори"
_QUESTION_LINE: Final = re.compile(r"^\s*(\d+)[\).:]\s*(.+)$")
_OPTION_LINE: Final = re.compile(r"^\s*([ABCD])[\).:]\s*(.*)$", re.IGNORECASE)
_ANSWER_LINE: Final = re.compile(
    r"^\s*(\d+)[\).:]\s*([ABCD])\)\s*$", re.IGNORECASE
)


class TextFormatError(ValueError):
    """Raised when a ReasoningBG text cannot be parsed."""

    def __init__(self, name: str, detail: str) -> None:
        super().__init__(f"{name}: {detail}")
        self.name: str = name
        self.detail: str = detail


class QuestionSet(NamedTuple):
    name: str
    passage: str
    numbers: Tuple[int, ...]
    questions: Tuple[Question, ...]
    prompt: str


def _marker(lines: Tuple[str, ...], marker: str, name: str) -> int:
    indexes = [i for i, line in enumerate(lines) if line.strip() == marker]
    if len(indexes) != 1:
        raise TextFormatError(name, f"expected one {marker!r} marker, got {len(indexes)}")
    return indexes[0]


def build_prompt(passage: str, numbers: Tuple[int, ...],
                 questions: Tuple[Question, ...]) -> str:
    """Build the answer-sheet prompt for one passage and its questions."""
    lines = [
        "Прочети текста и отговори на въпросите към него.",
        "За всеки въпрос изведи един ред само с буквата на верния отговор: A, B, C или D.",
        "Запази реда на въпросите. Не добавяй обяснения, номера или друг текст.",
        "",
        passage,
        "",
        "Въпроси:",
    ]
    for number, question in zip(numbers, questions):
        lines.append(f"{number}. {question.text}")
        for label, option in zip(OPTIONS, question.options):
            lines.append(f"   {label}) {option}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def load_text(path: Path) -> QuestionSet:
    """Parse one ReasoningBG text into a passage, questions and answer key."""
    lines = tuple(path.read_text(encoding="utf-8-sig").splitlines())
    question_marker = _marker(lines, _QUESTION_MARKER, path.name)
    answer_marker = _marker(lines, _ANSWER_MARKER, path.name)
    if answer_marker <= question_marker:
        raise TextFormatError(path.name, "answer marker precedes question marker")

    passage = "\n".join(line.strip() for line in lines[:question_marker]).strip()
    if not passage:
        raise TextFormatError(path.name, "empty passage")

    numbers: List[int] = []
    question_texts: List[str] = []
    option_sets: List[Dict[str, str]] = []
    number: Optional[int] = None
    text: str = ""
    options: Dict[str, str] = {}

    def store_question() -> None:
        if number is None:
            return
        if not text:
            raise TextFormatError(path.name, f"question {number} has no text")
        if set(options) != set(OPTIONS):
            raise TextFormatError(path.name, f"question {number} has incomplete options")
        numbers.append(number)
        question_texts.append(text)
        option_sets.append(options)

    for raw in lines[question_marker + 1:answer_marker]:
        line = raw.strip()
        if not line:
            continue
        match = _QUESTION_LINE.match(line)
        if match:
            store_question()
            number = int(match.group(1))
            text = match.group(2).strip()
            options = {}
            continue
        match = _OPTION_LINE.match(line)
        if match:
            label = match.group(1).upper()
            if number is None or label in options:
                raise TextFormatError(path.name, f"misplaced or duplicate option {label!r}")
            options[label] = match.group(2).strip()
            continue
        # A few source texts contain an explanatory note between questions.
        # It is not part of any answer option, so keep the surrounding Q/A pairs.
    store_question()
    if not numbers:
        raise TextFormatError(path.name, "no questions found")

    answers: Dict[int, str] = {}
    for raw in lines[answer_marker + 1:]:
        line = raw.strip()
        if not line:
            continue
        match = _ANSWER_LINE.match(line)
        if not match:
            raise TextFormatError(path.name, f"invalid answer line {line!r}")
        answer_number = int(match.group(1))
        if answer_number in answers:
            raise TextFormatError(path.name, f"duplicate answer for question {answer_number}")
        answers[answer_number] = match.group(2).upper()

    questions: List[Question] = []
    for item_number, item_text, item_options in zip(numbers, question_texts, option_sets):
        answer = answers.get(item_number)
        if answer is None:
            raise TextFormatError(path.name, f"missing answer for question {item_number}")
        questions.append(
            Question(
                text=item_text,
                options=tuple(item_options[label] for label in OPTIONS),
                answer=answer,
            )
        )

    question_tuple = tuple(questions)
    number_tuple = tuple(numbers)
    return QuestionSet(
        name=path.name,
        passage=passage,
        numbers=number_tuple,
        questions=question_tuple,
        prompt=build_prompt(passage, number_tuple, question_tuple),
    )


def load_texts(directory: Path = TEXT_DIR) -> Tuple[QuestionSet, ...]:
    """Load every ReasoningBG text in filename order."""
    texts = tuple(load_text(path) for path in sorted(directory.glob("*.txt")))
    if not texts:
        raise TextFormatError(directory.name, "no .txt files found")
    return texts


SETS: Final = load_texts()
PROMPT: Final = SETS[0].prompt


def set_for_run(run: int) -> QuestionSet:
    """Return the text used by a zero-based run index."""
    if run < 0:
        raise ValueError("run must be non-negative")
    return SETS[run % len(SETS)]


def prompt_for_run(run: int) -> str:
    return set_for_run(run).prompt


def status_for_set(text: Optional[str], question_set: QuestionSet) -> Tuple[bool, str]:
    return answer_status(text, question_set.questions)


def status_for_run(text: Optional[str], run: int) -> Tuple[bool, str]:
    return status_for_set(text, set_for_run(run))


def check_for_run(text: Optional[str], run: int) -> bool:
    return status_for_run(text, run)[0]


def explain_for_run(text: Optional[str], run: int) -> str:
    return status_for_run(text, run)[1]


def check(text: Optional[str]) -> bool:
    """Grade against the first text, for callers without a run index."""
    return check_for_run(text, 0)


def explain(text: Optional[str]) -> str:
    return explain_for_run(text, 0)


__all__ = (
    "ID",
    "PROMPT",
    "SETS",
    "TEXT_DIR",
    "QuestionSet",
    "TextFormatError",
    "build_prompt",
    "check",
    "check_for_run",
    "explain",
    "explain_for_run",
    "load_text",
    "load_texts",
    "prompt_for_run",
    "set_for_run",
    "status_for_set",
    "status_for_run",
)
