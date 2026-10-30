"""Timeout defaults and environment-variable overrides.

Covers the configurable timeouts added for LLM chat, code execution,
JS syntax check and browser runtime checks.

Timeouts are upper bounds: subprocess.run returns as soon as the child
process exits, so the full cap is never waited when the work finishes
early. Override any value with its HOMEBENCH_*_TIMEOUT environment variable.
"""

import os
import subprocess
import sys

import tasks.code_task as code_task
import tasks.game as game


def _env_int(name, default):
    return int(os.environ.get(name, default))


def test_default_timeouts_match_environment_contract():
    assert code_task.CODE_TIMEOUT == _env_int("HOMEBENCH_CODE_TIMEOUT", 10)
    assert game.BROWSER_TIMEOUT == _env_int("HOMEBENCH_BROWSER_TIMEOUT", 30)
    assert game.JS_CHECK_TIMEOUT == _env_int("HOMEBENCH_JS_CHECK_TIMEOUT", 10)


def test_timeouts_are_positive_ints():
    for value in (code_task.CODE_TIMEOUT, game.BROWSER_TIMEOUT,
                  game.JS_CHECK_TIMEOUT):
        assert isinstance(value, int)
        assert value > 0


def test_env_override_code_timeout():
    env = dict(os.environ, HOMEBENCH_CODE_TIMEOUT="25")
    out = subprocess.run(
        [sys.executable, "-c",
         "import tasks.code_task as c; print(c.CODE_TIMEOUT)"],
        capture_output=True, text=True, env=env, check=True,
    )
    assert out.stdout.strip() == "25"


def test_env_override_browser_timeout():
    env = dict(os.environ, HOMEBENCH_BROWSER_TIMEOUT="45")
    out = subprocess.run(
        [sys.executable, "-c",
         "import tasks.game as g; print(g.BROWSER_TIMEOUT)"],
        capture_output=True, text=True, env=env, check=True,
    )
    assert out.stdout.strip() == "45"


def test_env_override_js_check_timeout():
    env = dict(os.environ, HOMEBENCH_JS_CHECK_TIMEOUT="7")
    out = subprocess.run(
        [sys.executable, "-c",
         "import tasks.game as g; print(g.JS_CHECK_TIMEOUT)"],
        capture_output=True, text=True, env=env, check=True,
    )
    assert out.stdout.strip() == "7"


def test_homebench_timeout_cli_flag_is_accepted():
    out = subprocess.run(
        [sys.executable, "homebench.py", "--timeout", "60", "--help"],
        capture_output=True, text=True, check=True,
    )
    assert out.returncode == 0
    assert "--timeout" in out.stdout