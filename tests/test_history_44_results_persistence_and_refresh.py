"""History: keep older benchmarks visible and refresh results after every run."""

import json
from pathlib import Path

import homebench


def test_results_include_older_batches_for_the_same_model(tmp_path, monkeypatch):
    results = [
        {"batch": 1, "model": "model", "task": "math", "run": 0},
        {"batch": 2, "model": "model", "task": "logic", "run": 0},
    ]
    path = tmp_path / "results.jsonl"
    path.write_text(
        "".join(json.dumps(row) + "\n" for row in results),
        encoding="utf-8",
    )
    monkeypatch.setattr(homebench, "WEB_OUT", str(path))

    assert homebench.latest_rows() == results


def test_run_start_forces_result_refresh_even_if_run_finishes_before_poll():
    page = (Path(__file__).parents[1] / "static" / "index.html").read_text(
        encoding="utf-8"
    )
    run_handler = page.split("$('run').onclick", 1)[1].split(
        "$('addPlan').onclick", 1
    )[0]

    assert "wasRunning = true;" in run_handler
    assert "if (s.running || wasRunning) await loadResults();" in page


def test_results_table_attaches_populated_body_between_header_and_footer():
    page = (Path(__file__).parents[1] / "static" / "index.html").read_text(
        encoding="utf-8"
    )
    render = page.split("function render()", 1)[1].split(
        "async function editModelName", 1
    )[0]

    assert "tbody.append(tr);" in render
    assert "table.append(tbody);" in render
    assert render.index("table.append(thead);") < render.index("table.append(tbody);")
    assert render.index("table.append(tbody);") < render.index("table.append(tfoot);")
