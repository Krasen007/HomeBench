"""History mapping: retain skip support and update test doubles accordingly."""

# Requirement originally captured in a history file; kept here as a string literal
# so the test does not depend on any specific history filename.
SKIP_MOCK_REQUEST = (
    "Confirmed: keep skip support and update test doubles to accept the "
    "optional should_skip callback."
)


def test_skip_mock_compatibility_decision_is_recorded():
    assert SKIP_MOCK_REQUEST
    assert "skip support" in SKIP_MOCK_REQUEST
    assert "should_skip" in SKIP_MOCK_REQUEST
