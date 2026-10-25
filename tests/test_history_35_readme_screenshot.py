"""History: include the supplied HomeBench screenshot in the README."""

from pathlib import Path


ROOT = Path(__file__).parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_readme_embeds_an_existing_screenshot_asset():
    assert "![HomeBench benchmark interface" in README
    assert "screenshots/homebench.png" in README
    image = ROOT / "screenshots" / "homebench.png"
    assert image.is_file()
    assert image.stat().st_size > 0
