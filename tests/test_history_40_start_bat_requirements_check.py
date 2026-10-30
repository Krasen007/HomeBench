"""History: start.bat should verify that the user has the needed requirements
to run the app (Python 3.8+, Node.js, Chrome/Edge) before launching
homebench.py.
"""
from pathlib import Path

ROOT = Path(__file__).parents[1]
START_BAT = (ROOT / "start.bat").read_text(encoding="utf-8")


def test_start_bat_checks_python_3_8_or_later():
    """Python 3.8 is the minimum required version."""
    assert "3, 8" in START_BAT


def test_start_bat_checks_python_installation():
    """Must verify python is installed before launching."""
    assert "where python" in START_BAT


def test_start_bat_checks_node_js():
    """Node.js is needed for the game task's JS syntax validation."""
    assert "where node" in START_BAT


def test_start_bat_checks_chrome_or_edge():
    """Chrome or Edge is needed for the game task's headless runtime check."""
    lowered = START_BAT.lower()
    assert "chrome" in lowered
    assert "msedge" in lowered


def test_start_bat_starts_homebench():
    """After all checks, start.bat must launch the app."""
    assert "python homebench.py" in START_BAT


def test_start_bat_reports_missing_python():
    """Missing Python should produce an error and exit."""
    assert "ERROR" in START_BAT
    assert "exit /b" in START_BAT


def test_start_bat_warns_about_optional_tools():
    """Missing Node.js or browser should produce warnings, not errors."""
    assert "WARNING" in START_BAT
