import os
import re
import subprocess
import sys
import tempfile


# Upper bound for running the model-generated Python code. subprocess.run
# returns as soon as the process exits; it does not wait the full timeout
# when the code finishes early. Override with HOMEBENCH_CODE_TIMEOUT.
CODE_TIMEOUT = int(os.environ.get("HOMEBENCH_CODE_TIMEOUT", "10"))


def _code_status(text):
    if not isinstance(text, str):
        return False, "FAIL: no model output received"
    m = re.search(
        r"(?im)^[ \t]{0,3}```[ \t]*(?:python(?:\d+)?|py)?[ \t]*\r?\n"
        r"(.*?)(?:^[ \t]{0,3}```[ \t]*\r?$|\Z)",
        text, re.S | re.M)
    code = m.group(1) if m else text
    tests = '''
cases = [("A man, a plan, a canal: Panama", True), ("race a car", False),
         ("", True), ("No 'x' in Nixon", True), ("ab", False), ("12321", True)]
for s, expected in cases:
    assert is_palindrome(s) == expected, (s, expected)
'''
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code + "\n" + tests)
        path = f.name
    try:
        r = subprocess.run([sys.executable, path], capture_output=True,
                           timeout=CODE_TIMEOUT)
        if r.returncode == 0:
            return True, "PASS: all palindrome test cases passed"
        err = (r.stderr or r.stdout or b"").decode(errors="replace").strip()
        if err:
            return False, "FAIL: tests failed: " + err.splitlines()[-1]
        return False, "FAIL: tests failed (non-zero exit)"
    except subprocess.TimeoutExpired:
        return False, "FAIL: execution timed out"
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def check(text):
    return _code_status(text)[0]


def explain(text):
    return _code_status(text)[1]


PROMPT = (
    "Write a Python function `is_palindrome(s: str) -> bool` that returns "
    "True if s reads the same forwards and backwards, ignoring case and "
    "any non-alphanumeric characters. Reply with only the code in a "
    "single ```python block."
)

ID = "code"
