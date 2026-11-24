"""Full-pass task that grades every ReasoningBG text in one benchmark run."""

from __future__ import annotations

import re
from typing import Callable, Final, List, NamedTuple, Optional, Tuple

from . import reasoningbg

ID: Final = "reasoningbg_full"
_SECTION_LINE: Final = re.compile(r"^=== (.+) ===$")
PROMPT: Final = (
    "Answer every Bulgarian reading-comprehension text in tasks/ReasoningBG, "
    "in filename order: " + ", ".join(item.name for item in reasoningbg.SETS)
)


class Item(NamedTuple):
    label: str
    prompt: str
    status: Callable[[str], Tuple[bool, str]]


class ItemResult(NamedTuple):
    label: str
    output: str
    passed: bool
    reason: str


def items_for_run(run: int) -> Tuple[Item, ...]:
    return tuple(
        Item(
            label=question_set.name,
            prompt=question_set.prompt,
            status=lambda text, qset=question_set: reasoningbg.status_for_set(text, qset),
        )
        for question_set in reasoningbg.SETS
    )


def render_output(results: Tuple[ItemResult, ...]) -> str:
    return "\n\n".join(f"=== {result[0]} ===\n{result[1]}" for result in results)


def aggregate(results: Tuple[ItemResult, ...]) -> Tuple[bool, str]:
    total = len(results)
    correct = sum(1 for result in results if result[2])
    if correct == total:
        return True, f"PASS: {correct}/{total} texts correct"

    failed = [result for result in results if not result[2]]
    preview = ", ".join(result[0] for result in failed[:5])
    if len(failed) > 5:
        preview += f" (+{len(failed) - 5} more)"
    first = failed[0]
    return False, (
        f"FAIL: {correct}/{total} texts correct; failed: {preview}; "
        f"first: {first[0]}: {first[3]}"
    )


def parse_sections(text: Optional[str]) -> List[Tuple[str, str]]:
    sections: List[Tuple[str, str]] = []
    label: Optional[str] = None
    body: List[str] = []
    for line in (text or "").splitlines():
        match = _SECTION_LINE.match(line)
        if match:
            if label is not None:
                sections.append((label, "\n".join(body).strip()))
            label = match.group(1)
            body = []
        elif label is not None:
            body.append(line)
    if label is not None:
        sections.append((label, "\n".join(body).strip()))
    return sections


def results_from_output(text: Optional[str]) -> Tuple[ItemResult, ...]:
    sections = parse_sections(text)
    results: List[ItemResult] = []
    for (label, output), question_set in zip(sections, reasoningbg.SETS):
        passed, reason = reasoningbg.status_for_set(output, question_set)
        results.append(ItemResult(label, output, passed, reason))
    return tuple(results)


def check(text: Optional[str]) -> bool:
    sections = parse_sections(text)
    if [label for label, _ in sections] != [item.name for item in reasoningbg.SETS]:
        return False
    return aggregate(results_from_output(text))[0]


def explain(text: Optional[str]) -> str:
    sections = parse_sections(text)
    expected = len(reasoningbg.SETS)
    if [label for label, _ in sections] != [item.name for item in reasoningbg.SETS]:
        return f"FAIL: expected {expected} text sections, got {len(sections)}"
    return aggregate(results_from_output(text))[1]


__all__ = (
    "ID",
    "PROMPT",
    "Item",
    "ItemResult",
    "aggregate",
    "check",
    "explain",
    "items_for_run",
    "parse_sections",
    "render_output",
    "results_from_output",
)
