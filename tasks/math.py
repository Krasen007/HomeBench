import re


def _math_status(text):
    if not isinstance(text, str):
        return False, "FAIL: no model output received"
    nums = re.findall(r"answer\s*:\s*\$?\s*(-?\d+(?:\.\d+)?)", text, re.I)
    if not nums:
        return False, "FAIL: no 'Answer: <number>' found"
    got = float(nums[-1])
    if abs(got - 2.80) < 0.005:
        return True, "PASS: answer is 2.80"
    return False, "FAIL: expected 2.80, got %g" % got


def check(text):
    return _math_status(text)[0]


def explain(text):
    return _math_status(text)[1]


PROMPT = (
    "Maya buys 18 pencils. The shop sells pencils at 3 for $1.20. "
    "She pays with a $10 bill. How much change does she get, in dollars? "
    "Think step by step, then end with a final line in the form "
    "'Answer: <number>'."
)

ID = "math"
