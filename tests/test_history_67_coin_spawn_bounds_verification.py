"""History: verify coin spawn bounds against the supplied sample formulas."""

from tasks import game


SAFE_COIN_LOGIC = """
const canvas = { width: 800, height: 600 };
const coins = [];
const player = { x: 20, y: 20 };
const coin = {
  radius: 15,
  x: Math.random() * (canvas.width - 60) + 30,
  y: Math.random() * (canvas.height - 30) + 15
};
if (Math.hypot(player.x - coin.x, player.y - coin.y) < coin.radius + 10) {
  coins.splice(0, 1);
}
"""


def test_coin_bounds_accept_the_supplied_safe_inset_formula():
    passed, reason = game._coin_bounds_and_collection_status(SAFE_COIN_LOGIC)

    assert passed, reason


def test_coin_bounds_reject_the_supplied_zero_inset_y_formula():
    js = SAFE_COIN_LOGIC.replace(
        "Math.random() * (canvas.height - 30) + 15",
        "Math.random() * (canvas.height / 3)",
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason
