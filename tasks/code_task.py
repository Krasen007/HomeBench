import os
import re
import subprocess
import sys
import tempfile


def _code_status(text):
    m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
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
        r = subprocess.run([sys.executable, path], capture_output=True, timeout=10)
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
