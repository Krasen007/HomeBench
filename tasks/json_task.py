import json


def _json_status(text):
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return False, "FAIL: no JSON object found"
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError as e:
        return False, "FAIL: invalid JSON (%s)" % e
    expected = {
        "name": "Maria Lopez",
        "age": 34,
        "company": "Acme Corp",
        "start_date": "2021-03-15",
        "city": "Valencia",
    }
    mismatches = []
    for k, v in expected.items():
        if str(data.get(k, "")).strip() != str(v):
            mismatches.append("%s: expected %r, got %r" % (k, v, data.get(k)))
    if mismatches:
        return False, "FAIL: " + "; ".join(mismatches)
    return True, "PASS: all fields match"


def check(text):
    return _json_status(text)[0]


def explain(text):
    return _json_status(text)[1]


PROMPT = (
    "Extract information from the text below and reply with only a JSON "
    "object with keys: name (string), age (integer), company (string), "
    "start_date (YYYY-MM-DD), city (string).\n\n"
    "Text: Maria Lopez, 34, joined Acme Corp as a data engineer on "
    "March 15, 2021. She currently lives in Valencia."
)

ID = "json"
