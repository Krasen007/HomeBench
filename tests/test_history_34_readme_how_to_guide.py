"""History: document HomeBench clearly and provide a practical how-to guide."""

from pathlib import Path

from tasks import TASKS


ROOT = Path(__file__).parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_explains_project_and_all_registered_tasks():
    assert "## What it tests" in README
    for task in TASKS:
        assert f"`{task['id']}`" in README


def test_readme_documents_setup_run_results_security_and_tests():
    for section in ("## Requirements", "## How to run a benchmark",
                    "### 1. Start llama.cpp", "### 2. Start HomeBench",
                    "### 3. Configure and run", "### 4. Inspect and manage results",
                    "## Security note", "## Run the tests"):
        assert section in README
    assert "python homebench.py" in README
    assert "llama-server -m" in README
    assert "model-generated Python locally" in README
    assert "results.jsonl" in README


def test_readme_task_descriptions_track_the_task_registry_count():
    assert "seven repeatable tasks" in README
    assert README.count("| `") >= len(TASKS)
