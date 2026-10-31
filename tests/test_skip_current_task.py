"""Skip current task: a skipped run records status="skipped" with passed=null.

Maps to the History.md request:
    "add button in the webui to skip the current task while its running,
     make the table reflect if the test is run or skipped or pending"

run_benchmark must:
  * honor should_skip() after a task's chat completes without error,
    writing status="skipped", passed=null, reason="SKIP: skipped by user";
  * consume the skip flag so only the current task is skipped;
  * NOT skip a run that errored (chat failure takes precedence);
  * default to never skipping when should_skip is omitted.
"""
import io
import json
import unittest
from unittest.mock import MagicMock, patch

from homebench import run_benchmark


def _fake_response(text):
    body = json.dumps({"choices": [{"message": {"content": text}}]}).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = body
    resp.readline.side_effect = io.BytesIO(body).readline
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    return resp


def _written_rows(mock_file):
    written = "".join(call.args[0] for call in mock_file.write.call_args_list)
    return [json.loads(line) for line in written.strip().splitlines()]


class TestSkipCurrentTask(unittest.TestCase):
    @patch("homebench.urllib.request.urlopen")
    def test_skip_flags_current_task_then_consumes_flag(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response("Answer: 2.80")
        with patch("homebench.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            once = {"value": True}
            run_benchmark(
                "http://localhost:1234", "test-model", runs=2,
                temperature=0.0, max_tokens=32768, timeout=600,
                out_path="/tmp/results.jsonl", task_id="math",
                should_skip=lambda: once.pop("value", False),
            )
        rows = _written_rows(mock_file)
        self.assertEqual(len(rows), 2)
        # First run of the current task is skipped...
        self.assertEqual(rows[0]["status"], "skipped")
        self.assertIsNone(rows[0]["passed"])
        self.assertEqual(rows[0]["reason"], "SKIP: skipped by user")
        self.assertEqual(rows[0]["output"], "")
        # ...and the flag is consumed, so the next run runs normally.
        self.assertEqual(rows[1]["status"], "run")
        self.assertTrue(rows[1]["passed"])

    @patch("homebench.urllib.request.urlopen")
    def test_errored_run_is_not_skipped(self, mock_urlopen):
        mock_urlopen.side_effect = OSError("server down")
        with patch("homebench.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            run_benchmark(
                "http://localhost:1234", "test-model", runs=1,
                temperature=0.0, max_tokens=32768, timeout=600,
                out_path="/tmp/results.jsonl", task_id="math",
                should_skip=lambda: True,
            )
        rows = _written_rows(mock_file)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "run")
        self.assertFalse(rows[0]["passed"])
        self.assertTrue(rows[0]["reason"].startswith("FAIL:"))

    @patch("homebench.urllib.request.urlopen")
    def test_default_does_not_skip(self, mock_urlopen):
        mock_urlopen.return_value = _fake_response("Answer: 2.80")
        with patch("homebench.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            run_benchmark(
                "http://localhost:1234", "test-model", runs=1,
                temperature=0.0, max_tokens=32768, timeout=600,
                out_path="/tmp/results.jsonl", task_id="math",
            )
        rows = _written_rows(mock_file)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "run")
        self.assertTrue(rows[0]["passed"])
