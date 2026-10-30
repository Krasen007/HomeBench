"""History: coins must stay inside the canvas and be collectible by the player."""

from tasks import game


BOUNDED_GAME_LOGIC = """
const canvas = { width: 400, height: 300 };
const coins = [];
const player = { x: 20, y: 20 };
let score = 0;
function spawnCoin() {
  const coin = {
    radius: 10,
    x: Math.random() * (canvas.width - 20) + 10,
    y: Math.random() * (canvas.height - 20) + 10
  };
  coins.push(coin);
}
function collectCoins() {
  for (let i = coins.length - 1; i >= 0; i--) {
    const coin = coins[i];
    if (Math.hypot(player.x - coin.x, player.y - coin.y) < coin.radius + 10) {
      coins.splice(i, 1);
      score++;
    }
  }
}
"""


def test_coin_check_passes_when_spawn_bounds_and_collection_are_implemented():
    passed, reason = game._coin_bounds_and_collection_status(BOUNDED_GAME_LOGIC)

    assert passed
    assert "inside the canvas and are collectible" in reason


def test_coin_check_fails_when_spawn_positions_can_clip_canvas_edges():
    js = BOUNDED_GAME_LOGIC.replace(
        "Math.random() * (canvas.width - 20) + 10",
        "Math.random() * canvas.width"
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason


def test_coin_check_fails_when_player_cannot_collect_coins():
    js = BOUNDED_GAME_LOGIC.replace(
        "if (Math.hypot(player.x - coin.x, player.y - coin.y) < coin.radius + 10) {",
        "if (false) {"
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "collision with the car/player" in reason


def test_coin_check_rejects_collection_actions_disconnected_from_collision():
    js = BOUNDED_GAME_LOGIC.replace(
        "      coins.splice(i, 1);\n      score++;",
        "    }\n    coins.splice(i, 1);\n    score++;"
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "collision with the car/player" in reason


def test_coin_check_rejects_unrelated_player_spawn_position_as_coin_bounds():
    js = BOUNDED_GAME_LOGIC.replace(
        "x: Math.random() * (canvas.width - 20) + 10",
        "x: 20"
    ).replace(
        "const player = { x: 20, y: 20 };",
        "const player = { x: Math.random() * (canvas.width - 20) + 10, "
        "y: Math.random() * (canvas.height - 20) + 10 };"
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason


def test_coin_check_rejects_random_position_range_that_exceeds_coin_inset():
    js = BOUNDED_GAME_LOGIC.replace(
        "Math.random() * (canvas.width - 20) + 10",
        "Math.random() * canvas.width"
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason
