"""History: implement all BulMMLU CSV files from their shared directory."""

from pathlib import Path
from typing import Callable, NamedTuple, Optional, Tuple

import pytest

from tasks import (
    TASKS,
    april_uprising,
    bulmmlu,
    contemporary_bulgarian_poets,
    modern_economy_of_bulgaria,
    spelling_grammar,
)


class TaskSpec(NamedTuple):
    task_id: str
    csv_name: str
    expected_rows: int
    csv_path: Path
    questions: Tuple[bulmmlu.Question, ...]
    prompt: str
    check: Callable[[Optional[str]], bool]
    explain: Callable[[Optional[str]], str]


SPECS = (
    TaskSpec(
        spelling_grammar.ID, "Spelling and Grammar.csv", 118,
        spelling_grammar.CSV_PATH, spelling_grammar.QUESTIONS,
        spelling_grammar.PROMPT, spelling_grammar.check, spelling_grammar.explain,
    ),
    TaskSpec(
        april_uprising.ID, "April Uprising.csv", 120,
        april_uprising.CSV_PATH, april_uprising.QUESTIONS,
        april_uprising.PROMPT, april_uprising.check, april_uprising.explain,
    ),
    TaskSpec(
        contemporary_bulgarian_poets.ID, "Contemporary Bulgarian poets.csv", 119,
        contemporary_bulgarian_poets.CSV_PATH, contemporary_bulgarian_poets.QUESTIONS,
        contemporary_bulgarian_poets.PROMPT,
        contemporary_bulgarian_poets.check, contemporary_bulgarian_poets.explain,
    ),
    TaskSpec(
        modern_economy_of_bulgaria.ID, "Modern economy of Bulgaria.csv", 133,
        modern_economy_of_bulgaria.CSV_PATH, modern_economy_of_bulgaria.QUESTIONS,
        modern_economy_of_bulgaria.PROMPT,
        modern_economy_of_bulgaria.check, modern_economy_of_bulgaria.explain,
    ),
)


@pytest.mark.parametrize("spec", SPECS, ids=[spec.task_id for spec in SPECS])
def test_csv_path_points_to_the_bulmmlu_file(spec: TaskSpec):
    assert spec.csv_path.parent.name == "BulMMLU"
    assert spec.csv_path.name == spec.csv_name
    assert spec.csv_path.is_file()


@pytest.mark.parametrize("spec", SPECS, ids=[spec.task_id for spec in SPECS])
def test_question_count_matches_the_csv(spec: TaskSpec):
    assert len(spec.questions) == spec.expected_rows


@pytest.mark.parametrize("spec", SPECS, ids=[spec.task_id for spec in SPECS])
def test_prompt_contains_the_first_and_last_questions(spec: TaskSpec):
    assert spec.questions[0].text in spec.prompt
    assert spec.questions[-1].text in spec.prompt


@pytest.mark.parametrize("spec", SPECS, ids=[spec.task_id for spec in SPECS])
def test_registered_task_uses_the_module_prompt_and_checkers(spec: TaskSpec):
    task = next(task for task in TASKS if task["id"] == spec.task_id)

    assert task["prompt"] == spec.prompt
    assert task["check"] is spec.check
    assert task["explain"] is spec.explain


@pytest.mark.parametrize("spec", SPECS, ids=[spec.task_id for spec in SPECS])
def test_check_accepts_all_csv_answers(spec: TaskSpec):
    answer = "\n".join(question.answer for question in spec.questions)

    assert spec.check(answer)
    assert spec.explain(answer).startswith("PASS:")


@pytest.mark.parametrize("spec", SPECS, ids=[spec.task_id for spec in SPECS])
def test_check_reports_score_when_one_answer_is_wrong(spec: TaskSpec):
    answers = [question.answer for question in spec.questions]
    wrong_answer = "B" if answers[0] != "B" else "A"
    answers[0] = wrong_answer

    reason = spec.explain("\n".join(answers))

    assert f"{spec.expected_rows - 1}/{spec.expected_rows} correct" in reason
