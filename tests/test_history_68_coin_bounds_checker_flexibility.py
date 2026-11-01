"""History: accept safe coin bounds without requiring Math.random()."""

from tasks import game


SAFE_COIN_LOGIC = """
const canvas = { width: 400, height: 300 };
const coins = [];
const player = { x: 20, y: 20 };
const radius = 10;
const coin = {
  radius: 10,
  x: canvas.width / 2,
  y: Math.random() * (canvas.height - 2 * radius) + radius
};
if (Math.hypot(player.x - coin.x, player.y - coin.y) < coin.radius + 10) {
  coins.splice(0, 1);
}
"""


def test_coin_bounds_accept_deterministic_inset_positions():
    js = SAFE_COIN_LOGIC.replace(
        "x: canvas.width / 2,",
        "x: 200,",
    ).replace(
        "y: Math.random() * (canvas.height - 2 * radius) + radius",
        "y: 150",
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert passed, reason


def test_coin_bounds_accept_radius_relative_random_positions():
    passed, reason = game._coin_bounds_and_collection_status(SAFE_COIN_LOGIC)

    assert passed, reason


def test_coin_bounds_still_reject_uninset_random_position():
    js = SAFE_COIN_LOGIC.replace(
        "Math.random() * (canvas.height - 2 * radius) + radius",
        "Math.random() * canvas.height",
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason
