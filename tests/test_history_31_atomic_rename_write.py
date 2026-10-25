"""History: failed model rename writes must leave the original file intact."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from homebench import rename_model


def test_failed_result_serialization_preserves_existing_file_and_cleans_temp(tmp_path):
    results = tmp_path / "results.jsonl"
    rows = [{"model": "old", "task": "math"}, {"model": "other", "task": "logic"}]
    original = "".join(json.dumps(row) + "\n" for row in rows)
    results.write_text(original, encoding="utf-8")

    with patch("homebench.json.dumps", side_effect=OSError("simulated write failure")):
        with pytest.raises(OSError, match="simulated write failure"):
            rename_model(results, "old", "new")

    assert results.read_text(encoding="utf-8") == original
    assert list(Path(tmp_path).iterdir()) == [results]
