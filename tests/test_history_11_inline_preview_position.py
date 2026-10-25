"""History: put the inline HTML preview directly below its controls."""

from pathlib import Path


HTML = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_preview_is_initially_hidden_and_ordered_between_controls_and_answer():
    assert "iframe.hidden = true;" in HTML
    assert "d.append(btnRow, iframe);" in HTML
    assert "d.append(outDiv);" in HTML
    assert HTML.index("d.append(btnRow, iframe);") < HTML.index("d.append(outDiv);")


def test_iframe_content_is_loaded_only_when_inline_preview_is_activated():
    renderer = HTML.split("function renderDetailRun(r, index) {", 1)[1].split(
        "function updateDetailRuns()", 1)[0]
    assert renderer.index("iframe.hidden = true;") < renderer.index("toggleBtn.onclick")
    assert "iframe.srcdoc = html;" not in renderer.split("toggleBtn.onclick", 1)[0]
    assert "iframe.srcdoc = html;" in renderer.split("toggleBtn.onclick", 1)[1]
    assert "iframe.removeAttribute('srcdoc');" in renderer.split("toggleBtn.onclick", 1)[1]


def test_preview_button_label_tracks_visibility():
    assert "toggleBtn.textContent = iframe.hidden ? 'Render HTML inline' : 'Hide inline HTML';" in HTML
