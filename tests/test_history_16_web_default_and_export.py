"""History: start the web app by default and export results from its UI."""

import subprocess
import sys
from pathlib import Path

import homebench


def test_default_command_is_web_only_and_has_no_report_option():
    script = Path(homebench.__file__)
    result = subprocess.run([sys.executable, str(script), "--help"],
                            capture_output=True, text=True, check=True)
    assert "--port" in result.stdout
    assert "--report" not in result.stdout
    assert "--model" not in result.stdout


def test_web_ui_has_export_action_and_endpoint():
    assert 'id="export"' in homebench.PAGE
    assert "path == \"/api/export\"" in Path(homebench.__file__).read_text(encoding="utf-8")
