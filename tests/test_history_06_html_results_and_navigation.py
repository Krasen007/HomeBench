"""History: view generated HTML, open it separately, and page through runs."""

from pathlib import Path


HTML = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_detail_view_extracts_html_and_offers_preview_and_new_tab():
    for content in ("function extractHtml(src)", "const fence =", "srcdoc = html",
                    "Open HTML in new tab", "Render HTML inline", "window.open(url",
                    "reasonEl.textContent = r.reason"):
        assert content in HTML


def test_html_preview_extracts_html_from_tolerant_fences_or_prefixed_documents():
    assert "(html|htm)?" in HTML
    assert "^[ \\t]{0,3}```" in HTML
    assert "src.slice(start.index).trim()" in HTML


def test_per_run_pager_is_built_before_the_run_details():
    assert "const RUNS_PER_PAGE = 1;" in HTML
    assert "pager.append(prev, info, next);" in HTML
    assert "pager, runsContainer" in HTML
