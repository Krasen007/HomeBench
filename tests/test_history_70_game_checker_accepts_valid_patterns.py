"""History: accept equivalent safe coin-spawn and collection patterns."""

from tasks import game


SAFE_GAME = """
const coins = [];
const car = { x: 100, y: 100, radius: 30 };
let width = 800;
let height = 600;
let totalCoins = 0;
function spawnCoin() {
  const x = Math.random() * (width - 60) + 30;
  const y = Math.random() * (height / 2) + 50;
  coins.push({ x, y, radius: 20 });
}
function update() {
  const coin = coins[0];
  const distance = Math.sqrt((car.x - coin.x) ** 2 + (car.y - coin.y) ** 2);
  if (distance < car.radius + coin.radius) {
    collectCoin(coin, 0);
  }
}
function collectCoin(coin, index) {
  coins.splice(index, 1);
  totalCoins++;
}
"""


def test_checker_accepts_safe_coordinates_stored_in_shorthand_coin_object():
    passed, reason = game._coin_bounds_and_collection_status(SAFE_GAME)

    assert passed, reason


def test_checker_rejects_unsafe_spawn_after_resolving_local_coordinate():
    js = SAFE_GAME.replace(
        "Math.random() * (width - 60) + 30",
        "Math.random() * width",
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason
