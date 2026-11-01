"""History: identify why the example game's coin bounds are rejected."""

from tasks import game


EXAMPLE_SPAWN_AND_COLLECTION = """
const coins = [];
const car = { x: 100, y: 100, radius: 30 };
let width = 800;
let height = 600;
let totalCoins = 0;
function spawnCoin() {
  const x = Math.random() * (width - 60) + 30;
  const y = Math.random() * (height / 2) + 50;
  coins.push({ x, y, type: 'yellow', radius: 20 });
}
function spawnGreenCluster() {
  const centerX = width / 2;
  const centerY = height / 2;
  const dist = 40;
  const angle = 0;
  const x = centerX + Math.cos(angle) * dist;
  const y = centerY + Math.sin(angle) * dist;
  coins.push({ x, y, type: 'green', radius: 18 });
}
function update() {
  for (let i = coins.length - 1; i >= 0; i--) {
    const coin = coins[i];
    const distance = Math.sqrt((car.x - coin.x) ** 2 + (car.y - coin.y) ** 2);
    if (distance < car.radius + coin.radius) {
      collectCoin(coin, i);
    }
  }
}
function collectCoin(coin, index) {
  coins.splice(index, 1);
  totalCoins++;
}
"""


def test_checker_accepts_example_game_coin_spawn_and_collection_pattern():
    passed, reason = game._coin_bounds_and_collection_status(
        EXAMPLE_SPAWN_AND_COLLECTION
    )

    assert passed, reason


def test_checker_rejects_example_spawn_when_x_can_clip_canvas_edge():
    js = EXAMPLE_SPAWN_AND_COLLECTION.replace(
        "Math.random() * (width - 60) + 30",
        "Math.random() * width",
    )

    passed, reason = game._coin_bounds_and_collection_status(js)

    assert not passed
    assert "inside the canvas" in reason
