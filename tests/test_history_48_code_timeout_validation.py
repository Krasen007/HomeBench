"""History: reject non-positive model-generated code execution timeouts."""

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_code_timeout_rejects_zero_and_negative_configuration():
    for value in ("0", "-1"):
        env = os.environ.copy()
        env["HOMEBENCH_CODE_TIMEOUT"] = value
        result = subprocess.run(
            [sys.executable, "-c", "import tasks.code_task"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode != 0
        assert "HOMEBENCH_CODE_TIMEOUT must be a positive integer" in result.stderr


def test_history_records_code_timeout_validation():
    history = (ROOT / "History.md").read_text(encoding="utf-8")

    assert "Reject zero or negative HOMEBENCH_CODE_TIMEOUT values" in history
    assert (ROOT / "tests" / "test_history_48_code_timeout_validation.py").is_file()
