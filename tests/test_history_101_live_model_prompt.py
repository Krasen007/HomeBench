"""History: show the active prompt in the live model output panel."""

from pathlib import Path
from typing import NamedTuple

import homebench


ROOT = Path(__file__).parents[1]
HTML = (ROOT / "static" / "index.html").read_text(encoding="utf-8")


def test_live_stream_start_contains_task_prompt(monkeypatch, tmp_path):
    task = {"id": "test", "prompt": "The actual task prompt", "check": lambda _: True}
    monkeypatch.setattr(homebench, "TASKS", [task])
    prompts = []
    monkeypatch.setattr(homebench, "chat", lambda *args, **kwargs: "answer")

    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 100, 10,
        tmp_path / "results.jsonl",
        task_ids=["test"],
        on_token=lambda task_id, run, chunk: prompts.append(
            chunk["prompt"]
        ) if chunk.get("start") else None,
    )

    assert prompts == ["The actual task prompt"]


def test_live_stream_start_tracks_each_active_item_prompt(monkeypatch, tmp_path):
    class Item(NamedTuple):
        label: str
        prompt: str

        def status(self, output):
            return True, "PASS"

    task = {
        "id": "bundle",
        "prompt": "Generic task prompt",
        "check": lambda _: True,
        "items_for_run": lambda _: (
            Item("one.txt", "Prompt for one"),
            Item("two.txt", "Prompt for two"),
        ),
        "render_output": lambda results: "",
        "aggregate": lambda _: (True, "PASS"),
    }
    monkeypatch.setattr(homebench, "TASKS", [task])
    monkeypatch.setattr(homebench, "chat", lambda *args, **kwargs: "answer")
    prompts = []

    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 100, 10,
        tmp_path / "results.jsonl",
        task_ids=["bundle"],
        on_token=lambda task_id, run, chunk: prompts.append(
            chunk["prompt"]
        ) if chunk.get("start") else None,
    )

    assert prompts == [
        "Generic task prompt",
        "Prompt for one",
        "Prompt for two",
    ]


def test_live_output_panel_renders_prompt_as_text():
    poll = HTML.split("async function poll()", 1)[1].split(
        "$('detect').onclick", 1
    )[0]

    assert 'id="livePromptDetails"' in HTML
    assert 'id="livePrompt"' in HTML
    assert "$('livePrompt').textContent = s.stream_prompt || '';" in poll
    assert "$('livePromptDetails').hidden = !s.stream_prompt;" in poll


def test_history_maps_live_prompt_request():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert "Live model output" in history
    assert "tests/test_history_101_live_model_prompt.py" in history
