"""History: collision must control the coin collection action."""

from pathlib import Path

from tasks import game


ROOT = Path(__file__).parents[1]

CONNECTED = """
const coins = [];
const player = { x: 2, y: 2 };
let score = 0;
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

BOUNDED_POSITIONS = """
const canvas = { width: 400, height: 300 };
const coin = {
  radius: 10,
  x: Math.random() * (canvas.width - 20) + 10,
  y: Math.random() * (canvas.height - 20) + 10
};
"""


def test_collection_path_uses_collision_to_remove_and_score_coin():
    passed, reason = game._coin_bounds_and_collection_status(
        BOUNDED_POSITIONS + CONNECTED
    )

    assert passed, reason


def test_unconditional_removal_and_score_do_not_satisfy_collection_check():
    js = CONNECTED.replace(
        "if (Math.hypot(player.x - coin.x, player.y - coin.y) < coin.radius + 10) {\n"
        "      coins.splice(i, 1);\n"
        "      score++;\n"
        "    }",
        "if (false) {}\n    coins.splice(i, 1);\n    score++;",
    )
    passed, reason = game._coin_bounds_and_collection_status(BOUNDED_POSITIONS + js)

    assert not passed
    assert "collision with the car/player" in reason


def test_history_records_connected_collection_validation():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert "connect collision checks to collection actions" in history
    assert (ROOT / "tests" / "test_history_49_connected_coin_collection.py").is_file()
