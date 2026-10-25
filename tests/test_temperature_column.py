"""History: rows store the sampling temperature and the results table shows a temperature column."""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from homebench import run_benchmark

HTML = (Path(__file__).parents[1] / "static" / "index.html").read_text(encoding="utf-8")


def test_rows_store_temperature():
    with patch("homebench.chat", return_value="Answer: 2.80"):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            run_benchmark("http://localhost:1234", "temp-model", 1, 0.7, 256, 30, path)
            rows = [json.loads(line) for line in open(path)]
            assert rows
            assert {r["temperature"] for r in rows} == {0.7}
        finally:
            os.unlink(path)


def test_results_table_has_temperature_column():
    assert "el('th', 'temp')" in HTML
    assert "r.temperature" in HTML
