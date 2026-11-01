"""History: game bounds checks resolve actual dimensions and full expressions."""

from tasks import game


SAFE = """
const canvas = { width: 100, height: 80 };
const coins = [];
const player = { x: 20, y: 20 };
let score = 0;
const coinRadius = 5;
function spawn() {
  const x = Math.random() * (canvas.width - 20) + 10;
  const y = Math.random() * (canvas.height - 20) + 10;
  coins.push({ x, y, radius: coinRadius + 5 });
}
function collect(index) {
  if (index >= 0) {
    score += 1;
  }
  coins.splice(index, 1);
}
function update() {
  const coin = coins[0];
  if (Math.hypot(player.x - coin.x, player.y - coin.y) < coin.radius + 10) {
    collect(0);
  }
}
"""


def test_bounds_use_actual_canvas_width_and_height():
    js = SAFE.replace(
        "const x = Math.random() * (canvas.width - 20) + 10;",
        "const x = 95;",
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason


def test_bounds_resolve_full_radius_expression():
    passed, reason = game._coin_bounds_and_collection_status(SAFE)

    assert passed, reason


def test_unsupported_radius_expression_is_rejected_without_raising():
    js = SAFE.replace("coinRadius + 5", "Math.max(coinRadius, 5)")

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason


def test_reassigned_coordinate_uses_its_value_at_coin_spawn():
    js = SAFE.replace(
        "const x = Math.random() * (canvas.width - 20) + 10;",
        "let x = Math.random() * (canvas.width - 20) + 10;\n"
        "  x = 0;",
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason


def test_divisor_interval_crossing_zero_is_rejected():
    js = SAFE.replace(
        "const x = Math.random() * (canvas.width - 20) + 10;",
        "const x = Math.random() / (Math.random() - 0.5) + 10;",
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason


def test_helper_extraction_includes_actions_after_nested_block():
    passed, reason = game._coin_bounds_and_collection_status(SAFE)

    assert passed, reason
