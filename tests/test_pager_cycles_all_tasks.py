"""History: detail-view Next/Prev page through all tasks of a model (math -> logic -> ...)."""
from pathlib import Path

HTML = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_pager_walks_all_tasks_of_the_model():
    for content in (
        # one page per run, walking every task of the model in TASKS order
        "byTask.forEach(rs => rs.sort((a, b) => a.run - b.run))",
        "(byTask.get(t.id) || []).forEach((r, i) => pages.push({ task: t, runIndex: i, run: r }))",
        # Next/Prev move across the full page range of all tasks
        "prev.onclick = (e) => { e.stopPropagation(); detailPage--; updateDetailRuns(); };",
        "next.onclick = (e) => { e.stopPropagation(); detailPage++; updateDetailRuns(); };",
        "el('span', `Page ${detailPage + 1} / ${totalPages}`)",
        "if (pages.length > 1) {",
        # header and prompt follow the current task
        "detailContext.header.textContent = `${detailContext.model} / ${taskId}`",
        "detailContext.promptDiv.innerHTML = t ? renderMarkdown(t.prompt) : ''",
    ):
        assert content in HTML
