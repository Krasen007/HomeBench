"""History: game_solved must use only the strict game checker."""

from pathlib import Path

from tasks import game_solved


ROOT = Path(__file__).parents[1]


def test_marker_rich_html_without_valid_coin_logic_does_not_pass():
    html = """
    <html><body><canvas></canvas>car coin yellow red green grass Play 200
    audio mousemove setInterval
    <script>const coins = []; const player = {};</script>
    </body></html>
    """

    passed, reason = game_solved._solved_status(html)

    assert not passed
    assert "coins must spawn" in reason or "collision with the car/player" in reason


def test_solved_checker_returns_strict_checker_result(monkeypatch):
    expected = (False, "FAIL: strict validation")
    monkeypatch.setattr(game_solved.game, "_game_status", lambda _: expected)

    assert game_solved._solved_status("anything") == expected
