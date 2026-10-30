"""History: assert the default chat timeout without an environment override."""

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_default_timeout_test_runs_with_override_removed():
    env = os.environ.copy()
    env.pop("HOMEBENCH_CHAT_TIMEOUT", None)
    result = subprocess.run(
        [sys.executable, "-c",
         "from homebench import CHAT_TIMEOUT; assert CHAT_TIMEOUT == 600"],
        capture_output=True, text=True, env=env,
    )

    assert result.returncode == 0, result.stderr
