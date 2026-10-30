"""History: accept valid CHROME_BIN or BROWSER_BIN paths in start.bat."""

from pathlib import Path

START_BAT = (Path(__file__).parents[1] / "start.bat").read_text(
    encoding="utf-8"
)


def test_configured_browser_paths_are_checked_before_missing_warning():
    chrome_check = (
        'if defined CHROME_BIN if exist "!CHROME_BIN!" '
        'set "BROWSER_FOUND=!CHROME_BIN!"'
    )
    browser_check = (
        'if defined BROWSER_BIN if exist "!BROWSER_BIN!" '
        'set "BROWSER_FOUND=!BROWSER_BIN!"'
    )

    assert chrome_check in START_BAT
    assert browser_check in START_BAT
    assert START_BAT.index(chrome_check) < START_BAT.index(
        "WARNING: Chrome or Edge not found"
    )
    assert START_BAT.index(browser_check) < START_BAT.index(
        "WARNING: Chrome or Edge not found"
    )
