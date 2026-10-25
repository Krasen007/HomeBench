"""Regression tests for common model-generated Python code-fence formats."""

from tasks.code_task import _code_status


CODE = """def is_palindrome(s: str) -> bool:
    cleaned = ''.join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]
"""


def test_python_fence_with_standard_format_passes():
    passed, reason = _code_status("```python\n" + CODE + "```")
    assert passed, reason


def test_python_fence_accepts_case_alias_indentation_and_windows_newlines():
    for label in ("Python", "PYTHON3", "py"):
        output = "  ```" + label + "\r\n" + CODE + "  ```\r\n"
        passed, reason = _code_status(output)
        assert passed, (label, reason)


def test_python_fence_without_closing_delimiter_passes():
    passed, reason = _code_status("```python\n" + CODE)
    assert passed, reason


def test_unfenced_python_code_still_passes():
    passed, reason = _code_status(CODE)
    assert passed, reason
