"""History: distinguish malformed generated source from lost code fences."""

from tasks import code_task, game


def test_reported_python_output_is_extracted_then_fails_syntax_validation():
    output = '''```
import re

def is_palindrome(s: str) -    """
    Checks if a string is a palindrome, ignoring case and non-alphanumeric characters.
    """
    processed_s = re.sub(r'[^a-z0-9]', '', s.lower())
    return processed_s == processed_s[::-1]
```'''

    passed, reason = code_task._code_status(output)

    assert not passed
    assert "SyntaxError" in reason
    assert "expected ':'" in reason


def test_reported_game_output_is_extracted_then_fails_missing_canvas_check():
    output = '''```
<!DOCTYPE html<html lang="en"<head    <meta charset="UTF-8"    <meta name="viewport" content="width=device-width, initial-scale=1.0"    <title    <style        body {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
```'''
    expected_html = output.removeprefix("```\n").removesuffix("\n```")

    assert game._extract_html(output) == expected_html
    passed, reason = game._game_status(output)

    assert not passed
    assert reason == "FAIL: missing required element/content 'canvas'"
