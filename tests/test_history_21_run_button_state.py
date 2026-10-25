"""History: re-enable the Run button when a benchmark completes."""

from pathlib import Path

from homebench import PAGE


def test_browser_disables_run_button_only_while_server_reports_running():
    assert "$('run').disabled = s.running;" in PAGE
    assert "if (s.running || wasRunning) await loadResults();" in PAGE


def test_worker_resets_running_state_on_success_and_failure():
    source = Path(__file__).parents[1] / "homebench.py"
    text = source.read_text(encoding="utf-8")
    assert "finally:" in text
    assert 'state["running"] = False' in text
