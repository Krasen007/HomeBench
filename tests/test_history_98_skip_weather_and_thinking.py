"""History: preserve weather context and exclude partial thinking from grades."""

import json
from pathlib import Path

import homebench
from tasks import weather


ROOT = Path(__file__).parents[1]
TOOL_REQUEST = json.dumps({
    "tool": "web_fetch",
    "args": {"url": "https://wttr.in/Varna?format=j2"},
})


def _run_weather(tmp_path, monkeypatch, second_response, should_skip=None):
    task = {
        "id": weather.ID,
        "prompt": weather.PROMPT,
        "check": weather.check,
        "explain": weather.explain,
    }
    monkeypatch.setattr(homebench, "TASKS", [task])
    monkeypatch.setattr(
        weather, "execute_tool_request",
        lambda request, timeout: {"temperature_c": 18.0},
    )
    calls = {"count": 0}

    def fake_chat(*args, on_token=None, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            on_token({"content": TOOL_REQUEST, "reasoning": ""})
            return TOOL_REQUEST
        content = second_response
        on_token({"content": content, "reasoning": ""})
        if isinstance(second_response, Exception):
            raise second_response
        return content

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out_path = tmp_path / "weather-results.jsonl"
    homebench.run_benchmark(
        "http://localhost:1234", "weather-model", 1, 0.0, 100, 10, out_path,
        task_ids=[weather.ID], should_skip=should_skip,
    )
    return json.loads(out_path.read_text(encoding="utf-8").splitlines()[0])


def test_skip_during_weather_follow_up_saves_context_and_separate_partial_answer(
        tmp_path, monkeypatch):
    row = _run_weather(
        tmp_path,
        monkeypatch,
        homebench._SkipRequested(),
    )

    assert row["status"] == "skipped"
    assert "Weather tool request:" in row["output"]
    assert "Weather tool result:" in row["output"]
    assert '"temperature_c": 18.0' in row["output"]
    assert row["output"].endswith("Final answer:\n")


def test_skip_after_weather_follow_up_returns_keeps_complete_result(
        tmp_path, monkeypatch):
    checks = {"count": 0}

    def skip_after_response():
        checks["count"] += 1
        return checks["count"] >= 3

    row = _run_weather(tmp_path, monkeypatch, "18°C", skip_after_response)

    assert row["status"] == "skipped"
    assert row["output"].endswith("Final answer:\n18°C")
    assert row["partial_grade"]["passed"] is True


def test_skip_after_tool_result_keeps_completed_weather_context(
        tmp_path, monkeypatch):
    checks = {"count": 0}

    def skip_after_tool_result():
        checks["count"] += 1
        return checks["count"] >= 2

    row = _run_weather(tmp_path, monkeypatch, "18°C", skip_after_tool_result)

    assert row["status"] == "skipped"
    assert "Weather tool request:" in row["output"]
    assert "Weather tool result:" in row["output"]
    assert row["output"].endswith("Final answer:\n")


def test_unterminated_thinking_is_audited_but_not_graded_on_skip(
        tmp_path, monkeypatch):
    task = {
        "id": "math",
        "prompt": "Answer.",
        "check": lambda output: output.strip() == "42",
        "explain": lambda output: (
            "PASS: answer is 42" if output.strip() == "42"
            else f"FAIL: graded {output!r}"
        ),
    }
    monkeypatch.setattr(homebench, "TASKS", [task])

    def fake_chat(*args, on_token=None, **kwargs):
        on_token({
            "content": "42\n<thinking>unfinished private reasoning",
            "reasoning": "",
        })
        raise homebench._SkipRequested

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out_path = tmp_path / "partial-results.jsonl"
    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 100, 10, out_path,
        task_ids=["math"],
    )

    row = json.loads(out_path.read_text(encoding="utf-8").splitlines()[0])
    assert row["output"] == "42\n"
    assert row["reasoning"] == "<thinking>unfinished private reasoning"
    assert row["partial_grade"] == {
        "passed": True,
        "reason": "PASS: answer is 42",
    }


def test_unterminated_thinking_is_removed_from_partial_item_grade(
        tmp_path, monkeypatch):
    class Item:
        label = "one.txt"
        prompt = "Answer."

        @staticmethod
        def status(output):
            return output == "A", f"graded {output!r}"

    task = {
        "id": "bundle",
        "prompt": "Answer.",
        "check": lambda _: False,
        "items_for_run": lambda _: (Item(),),
        "render_output": lambda results: results[0][1],
        "aggregate": lambda _: (False, "FAIL"),
    }
    monkeypatch.setattr(homebench, "TASKS", [task])

    def fake_chat(*args, on_token=None, **kwargs):
        on_token({"content": "A<thinking>unfinished reasoning", "reasoning": ""})
        raise homebench._SkipRequested

    monkeypatch.setattr(homebench, "chat", fake_chat)
    out_path = tmp_path / "item-results.jsonl"
    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0.0, 100, 10, out_path,
        task_ids=["bundle"],
    )

    row = json.loads(out_path.read_text(encoding="utf-8").splitlines()[0])
    assert row["output"] == "A"
    assert row["reasoning"] == "<thinking>unfinished reasoning"
    assert row["partial_grade"]["reason"] == (
        "1/1 captured texts fully correct; processed 1 of 1"
    )


def test_history_maps_the_review_follow_ups_to_this_test():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert "incomplete thinking blocks" in history
    assert "tests/test_history_98_skip_weather_and_thinking.py" in history
