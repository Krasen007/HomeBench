"""History: skipping interrupts active work and is excluded from pass rates."""
from pathlib import Path


ROOT = Path(__file__).parents[1]
HOME_BENCH = (ROOT / "homebench.py").read_text(encoding="utf-8")
PAGE = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
HISTORY = (ROOT / "History-v1.2.md").read_text(encoding="utf-8")


def test_skip_interrupts_chat_and_writes_a_skipped_result():
    assert "def cancellable_lines():" in HOME_BENCH
    assert "lines.get(timeout=0.2)" in HOME_BENCH
    assert "sock.shutdown(socket.SHUT_RDWR)" in HOME_BENCH
    assert "should_skip=skip_requested_now" in HOME_BENCH
    assert 'output, passed, reason, status = (' in HOME_BENCH
    assert '"", None, "SKIP: skipped by user", "skipped"' in HOME_BENCH


def test_skip_button_reenables_after_progress_to_a_new_run():
    assert "requestedSkipDone = currentDone;" in PAGE
    assert "s.done > requestedSkipDone && skipTarget !== requestedSkipTarget" in PAGE
    assert "$('skip').disabled = false;" in PAGE


def test_skipped_runs_are_excluded_from_task_and_aggregate_rates():
    assert "const completedRuns = rs.filter(r => r.status !== 'skipped');" in PAGE
    assert "const p = completedRuns.filter(r => r.passed === true).length;" in PAGE
    assert "const completed = completedRuns.length;" in PAGE
    assert "scoreClass(p, completed)" in PAGE
    assert "r.status !== 'skipped'" in PAGE
    assert "tp += p; tt += completed;" in PAGE


def test_review_followups_are_recorded_in_history():
    assert "Fix review findings: interrupt active chat reads" in HISTORY
