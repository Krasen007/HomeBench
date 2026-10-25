"""History: model output sanitization keeps '>' intact in HTML/code."""


from homebench import _sanitize_output


def test_html_arrows_are_preserved():
    html = (
        "<!DOCTYPE html>\n"
        "<html lang=en>\n"
        "<head>\n"
        '<title>Game</title>\n'
        "</head>\n"
        "<body>\n"
        "<canvas></canvas>\n"
        "</body>\n"
        "</html>"
    )
    assert _sanitize_output(html) == html


def test_code_comparisons_are_preserved():
    code = "def f(x):\n    return x > 0 and x >= 1\n"
    assert _sanitize_output(code) == code


def test_thinking_blocks_are_stripped():
    output = "<thinking>reasoning</thinking>\n<!doctype html><html>"
    assert _sanitize_output(output) == "\n<!doctype html><html>"

    output = "print(1 > 0)\n</thinking>"
    assert _sanitize_output(output) == "print(1 > 0)\n"


def test_non_string_passthrough():
    assert _sanitize_output(None) is None
    assert _sanitize_output(123) == 123
