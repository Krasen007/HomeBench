"""History: keep the web and benchmark functionality in one application."""

from pathlib import Path

import homebench


ROOT = Path(homebench.__file__).parent


def test_homebench_is_the_single_entry_point_and_legacy_scripts_are_absent():
    assert (ROOT / "homebench.py").is_file()
    assert not (ROOT / "mini_bench.py").exists()
    assert not (ROOT / "web_bench.py").exists()
    assert callable(homebench.run_benchmark)
    assert callable(homebench.Handler)
