import re


def _logic_status(text):
    if not isinstance(text, str):
        return False, "FAIL: no model output received"
    names = re.findall(r"answer\s*:\s*\**\s*(\w+)", text, re.I)
    if not names:
        return False, "FAIL: no 'Answer: <name>' found"
    got = names[-1]
    if got.lower() == "alice":
        return True, "PASS: answer is Alice"
    return False, "FAIL: expected Alice, got %s" % got


def check(text):
    return _logic_status(text)[0]


def explain(text):
    return _logic_status(text)[1]


PROMPT = (
    "Alice, Bob and Carol each own exactly one pet: a cat, a dog, or a "
    "fish, and no two own the same pet. Alice does not own the dog. "
    "Bob owns neither the dog nor the fish. Who owns the fish? "
    "Reason briefly, then end with a final line in the form "
    "'Answer: <name>'."
)

ID = "logic"
