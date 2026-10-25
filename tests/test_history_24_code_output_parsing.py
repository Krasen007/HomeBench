"""History: accept normal fenced or bare code-task output."""

from tasks.code_task import _code_status


def test_code_task_accepts_code_fence_and_unfenced_output():
    code = "def is_palindrome(s):\n    s = ''.join(c.lower() for c in s if c.isalnum())\n    return s == s[::-1]\n"
    for output in ("```python\n" + code + "```", code):
        passed, reason = _code_status(output)
        assert passed, reason
