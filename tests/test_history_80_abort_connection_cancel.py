"""History: aborting a run interrupts a pending chat connection open."""

import threading
import time
from unittest.mock import MagicMock

import pytest

import homebench


def test_chat_abort_does_not_wait_for_urlopen_timeout(monkeypatch):
    opening = threading.Event()
    release = threading.Event()
    closed = threading.Event()
    response = MagicMock()
    response.close.side_effect = closed.set

    def blocked_urlopen(request, timeout):
        opening.set()
        release.wait(2)
        return response

    monkeypatch.setattr(homebench.urllib.request, "urlopen", blocked_urlopen)
    started = time.monotonic()
    try:
        with pytest.raises(homebench._SkipRequested):
            homebench.chat(
                "http://localhost:8080", "prompt", 0.0, 8, 600,
                should_abort=opening.is_set,
            )
    finally:
        release.set()

    assert time.monotonic() - started < 1
    assert closed.wait(1)
    response.close.assert_called_once()


def test_benchmark_passes_abort_callback_to_chat(monkeypatch, tmp_path):
    abort = lambda: False
    received = []

    def fake_chat(*args, should_abort=None, **kwargs):
        received.append(should_abort)
        return "42"

    monkeypatch.setattr(homebench, "chat", fake_chat)
    homebench.run_benchmark(
        "http://localhost:8080", "model", 1, 0.0, 8, 5,
        str(tmp_path / "results.jsonl"), task_ids=["math"],
        should_abort=abort,
    )

    assert received == [abort]
