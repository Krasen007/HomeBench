"""History: a game must demonstrate interaction and report runtime errors."""

from types import SimpleNamespace

from tasks import game


def test_runtime_checker_is_defined_and_checks_interaction_and_late_errors():
    assert callable(game._game_runtime_status)
    injected = game._inject_runtime_checks("<html><body><button>Play</button><canvas></canvas></body></html>")
    assert "play.click()" in injected
    assert "c.dispatchEvent(ev)" in injected
    assert "idleDomChanged=before.dom!==idle.dom" in injected
    assert "idleCanvasChanged=changed(before.canvas,idle.canvas)" in injected
    assert "!idleDomChanged&&after.dom!==idle.dom" in injected
    assert "!idleCanvasChanged&&changed(idle.canvas,after.canvas)" in injected
    assert "window.__bench_refresh_status();" in injected


def test_inconclusive_runtime_does_not_count_as_a_game_pass(monkeypatch):
    html = ("<html><canvas></canvas> car coin yellow red green grass Play 200 "
            "sound mousemove spawn</html>")
    monkeypatch.setattr(game, "_game_runtime_status",
                        lambda _: (None, "runtime check skipped (no browser found)"))

    assert game.check(html) is False
    assert game.explain(html).startswith("INCONCLUSIVE:")


def test_runtime_status_requires_observed_interaction_and_surfaces_late_errors(monkeypatch):
    monkeypatch.setattr(game, "_browser_executable", lambda: "browser")
    monkeypatch.setattr(game.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(stdout='<div id="__bench_status">OK</div>'))
    assert game._game_runtime_status("<html></html>")[0] is True

    monkeypatch.setattr(game.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(stdout='<div id="__bench_status">ERROR: no observable game-state change</div>'))
    passed, reason = game._game_runtime_status("<html></html>")
    assert not passed
    assert "no observable game-state change" in reason

    monkeypatch.setattr(game.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(stdout='<div id="__bench_status">ERROR: late timer error</div>'))
    passed, reason = game._game_runtime_status("<html></html>")
    assert not passed
    assert "late timer error" in reason


def test_game_html_extraction_accepts_common_fence_formats():
    document = """<!doctype html>
<html><body><canvas></canvas>car coin yellow red green grass Play 200
sound mousemove spawn</body></html>"""
    for output in (
        "```html\n" + document + "\n```",
        "  ```HTML\r\n" + document + "\r\n  ```\r\n",
        "```htm\n" + document,
        "``` \n" + document + "\n```",
        "Here is the game:\n" + document,
    ):
        assert game._extract_html(output) == document


def test_game_validator_checks_extracted_document_not_markdown_wrapper(monkeypatch):
    document = """<!doctype html>
<html><body><canvas></canvas>car coin yellow red green grass Play 200
sound mousemove spawn</body></html>"""
    monkeypatch.setattr(game, "_game_runtime_status",
                        lambda html: (True, "PASS: runtime ok"))
    for output in ("```HTML\n" + document + "\n```",
                   "Here is the game:\n" + document):
        passed, reason = game._game_status(output)
        assert passed, reason
