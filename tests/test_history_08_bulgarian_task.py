"""History: check corrected Bulgarian full and short definite-article forms."""

from tasks import bulgarian


def test_bulgarian_task_accepts_all_corrected_examples():
    answer = "Вчера видях директора. Отидохме при лекаря. Извикаха ученика. Влакът закъсня."
    assert bulgarian.check(answer)
    assert bulgarian.explain(answer).startswith("PASS:")


def test_bulgarian_task_reports_missing_corrected_forms():
    passed, reason = bulgarian._bg_article_status("Вчера видях директорът.")
    assert not passed
    assert "лекаря" in reason
