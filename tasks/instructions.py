import re


def _instructions_status(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if len(lines) != 3:
        return False, "FAIL: expected exactly 3 non-empty lines, got %d" % len(lines)
    for i, line in enumerate(lines, 1):
        if not re.match(r"^[-*\u2022]\s+", line):
            return False, "FAIL: line %d does not start with '- '" % i
        words = re.sub(r"^[-*\u2022]\s+", "", line).split()
        if not 0 < len(words) < 8:
            return False, "FAIL: line %d has %d words (need 1-7)" % (i, len(words))
    return True, "PASS: 3 bullets, each '- ' prefix, 1-7 words"


def check(text):
    return _instructions_status(text)[0]


def explain(text):
    return _instructions_status(text)[1]


PROMPT = (
    "Give me exactly 3 bullet points about the benefits of sleep. "
    "Each bullet must start with '- ' and contain fewer than 8 words. "
    "Output nothing except the 3 bullets."
)

ID = "instructions"
