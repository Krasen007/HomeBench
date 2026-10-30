"""History: make empty final model responses visible and diagnosable."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import homebench


ROOT = Path(__file__).parents[1]


def _response(payload):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_chat_reports_empty_content_with_available_completion_metadata():
    payload = {
        "choices": [{
            "message": {"content": None},
            "finish_reason": "length",
        }],
        "usage": {"completion_tokens": 32768},
    }

    with patch("homebench.urllib.request.urlopen", return_value=_response(payload)):
        with pytest.raises(
                ValueError,
                match=r"no final answer text \(finish_reason=length, completion_tokens=32768\)"):
            homebench.chat("http://localhost:1234", "prompt", 0, 32768, 600)


def test_run_benchmark_persists_response_diagnostic(tmp_path, monkeypatch):
    task = {
        "id": "game_solved",
        "prompt": "make game",
        "check": lambda _: False,
        "explain": lambda _: "FAIL: not an HTML document",
    }
    monkeypatch.setattr(homebench, "TASKS", [task])
    monkeypatch.setattr(
        homebench, "chat",
        lambda *args: (_ for _ in ()).throw(
            ValueError("model server returned no final answer text (finish_reason=length)")
        ),
    )
    out = tmp_path / "results.jsonl"

    homebench.run_benchmark(
        "http://localhost:1234", "model", 1, 0, 32768, 600, out,
    )

    row = json.loads(out.read_text(encoding="utf-8").strip())
    assert row["output"].startswith("[ERROR] model server returned no final answer text")
    assert row["reason"].startswith("FAIL: model server returned no final answer text")


def test_history_records_empty_response_diagnostic_behavior():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert "report empty final model content explicitly" in history
    assert (ROOT / "tests" / "test_history_53_empty_model_answer_diagnostics.py").is_file()
