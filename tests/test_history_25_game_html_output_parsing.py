"""History: extract game HTML from fenced and explanatory model output."""

from tasks import game


def test_game_html_is_extracted_from_fences_and_prefixed_raw_output():
    document = "<!doctype html>\n<html><body>game</body></html>"
    assert game._extract_html("```HTML\n" + document + "\n```") == document
    assert game._extract_html("Here is the HTML:\n" + document) == document
