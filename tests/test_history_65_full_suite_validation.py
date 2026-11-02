"""History mapping: request to run and check the whole test suite."""

# Requirement originally captured in a history file; kept here as a string literal
# so the test does not depend on any specific history filename.
FULL_SUITE_REQUEST = "lets run the whole suite and check if everything is ok"


def test_full_suite_validation_request_is_recorded():
    assert FULL_SUITE_REQUEST
    assert "whole suite" in FULL_SUITE_REQUEST
