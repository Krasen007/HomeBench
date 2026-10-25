"""History: the model name can be edited from the results page via /api/rename_model."""
import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from homebench import Handler, rename_model


class TestRenameModel(unittest.TestCase):
    def _write_rows(self, path, models):
        with open(path, "w", encoding="utf-8") as f:
            for m in models:
                f.write(json.dumps({
                    "batch": 1, "model": m, "task": "math", "run": 0,
                    "passed": True, "reason": "PASS", "output": "x",
                    "note": "temp=0.7", "temperature": 0.7,
                }) + "\n")

    def test_renames_all_rows_of_model(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            self._write_rows(path, ["model-a", "model-b", "model-a"])
            final = rename_model(path, "model-a", "renamed")
            self.assertEqual(final, "renamed")
            rows = [json.loads(line) for line in open(path)]
            self.assertEqual([r["model"] for r in rows], ["renamed", "model-b", "renamed"])
        finally:
            os.unlink(path)

    def test_auto_increments_on_collision(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            self._write_rows(path, ["model-a", "model-b", "model-b (1)"])
            final = rename_model(path, "model-a", "model-b")
            self.assertEqual(final, "model-b (2)")
        finally:
            os.unlink(path)

    def test_raises_on_missing_model(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            self._write_rows(path, ["model-a"])
            with self.assertRaises(KeyError):
                rename_model(path, "nope", "x")
        finally:
            os.unlink(path)

    def test_rename_model_endpoint(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            self._write_rows(path, ["model-a"])
            h = Handler.__new__(Handler)
            h.send_response = MagicMock()
            h.send_header = MagicMock()
            h.end_headers = MagicMock()
            h.wfile = io.BytesIO()
            h.path = "/api/rename_model"
            body = json.dumps({"old_name": "model-a", "new_name": "renamed"}).encode()
            h.headers = {"Content-Length": str(len(body))}
            h.rfile = io.BytesIO(body)
            h.command = "POST"
            with patch("homebench.WEB_OUT", path):
                h.do_POST()
            resp = json.loads(h.wfile.getvalue())
            self.assertEqual(resp, {"ok": True, "name": "renamed"})
        finally:
            os.unlink(path)
