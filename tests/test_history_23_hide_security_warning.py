"""History: hide the local-code-execution warning while a benchmark runs."""

from pathlib import Path


PAGE = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_security_warning_visibility_tracks_running_status():
    assert 'id="securityWarning"' in PAGE
    assert "$('securityWarning').hidden = s.running;" in PAGE
