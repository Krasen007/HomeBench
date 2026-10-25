def _bg_article_status(text):
    if not isinstance(text, str):
        return False, "FAIL: no model output received"
    low = " ".join(text.split()).casefold()
    expected_tokens = ["директора", "лекаря", "ученика", "влакът"]
    missing = [t for t in expected_tokens if t not in low]
    if missing:
        return False, "FAIL: missing corrected form(s): " + ", ".join(missing)
    return True, "PASS: all sentences use the correct article"


def check(text):
    return _bg_article_status(text)[0]


def explain(text):
    return _bg_article_status(text)[1]


PROMPT = (
    "Correct the use of the Bulgarian definite article (full vs. short form) "
    "in the following sentences. Output only the corrected sentences, one per "
    "line, in the same order:\n"
    "1. Вчера видях директорът.\n"
    "2. Отидохме при лекарят.\n"
    "3. Извикаха ученикът в кабинета.\n"
    "4. Влака закъсня с един час."
)

ID = "bulgarian"
