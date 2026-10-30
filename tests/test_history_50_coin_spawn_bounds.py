"""History: validate coin spawn coordinates and full random ranges."""

from pathlib import Path

from tasks import game


ROOT = Path(__file__).parents[1]
JS = """
const canvas = { width: 400, height: 300 };
const coins = [];
const player = { x: 20, y: 20 };
const coin = {
  radius: 10,
  x: Math.random() * (canvas.width - 20) + 10,
  y: Math.random() * (canvas.height - 20) + 10
};
if (Math.hypot(player.x - coin.x, player.y - coin.y) < coin.radius + 10) {
  coins.splice(0, 1);
}
"""


def test_position_ranges_allow_full_coin_inside_canvas():
    passed, reason = game._coin_bounds_and_collection_status(JS)

    assert passed, reason


def test_player_position_randomness_cannot_stand_in_for_coin_spawn_bounds():
    js = JS.replace(
        "x: Math.random() * (canvas.width - 20) + 10",
        "x: Math.random() * canvas.width",
    )
    js = js.replace(
        "const player = { x: 20, y: 20 };",
        "const player = { x: Math.random() * (canvas.width - 20) + 10, "
        "y: Math.random() * (canvas.height - 20) + 10 };",
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason


def test_random_range_must_include_coin_radius_inset():
    js = JS.replace(
        "Math.random() * (canvas.width - 20) + 10",
        "Math.random() * canvas.width",
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason


def test_history_records_full_coin_spawn_bounds_validation():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert "Verify coin spawn positions against coin bounds" in history
    assert (ROOT / "tests" / "test_history_50_coin_spawn_bounds.py").is_file()
