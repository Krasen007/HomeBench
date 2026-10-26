"""Tests for HomeBench to prevent regressions.

Covers fixes for:
1. chat() returning None instead of the model response text
2. send() failing on bytes payloads (results export)
3. unique_model_name() returning None on duplicate model names
4. Temperature not appended to note
5. Run button staying grayed after benchmark finishes (state not reset)
"""
import io
import json
import unittest
from unittest.mock import MagicMock, patch

from homebench import (
    chat,
    run_benchmark,
    unique_model_name,
    Handler,
    TASKS,
    _format_note,
    state,
)
from tasks import bulgarian, code_task, game, instructions, json_task, logic, math, weather


# ---------------------------------------------------------------------------
# unique_model_name — prevent returning None on duplicate names
# ---------------------------------------------------------------------------

class TestUniqueModelName(unittest.TestCase):
    def test_new_name_returned_as_is(self):
        self.assertEqual(unique_model_name("llama-3.1", set()), "llama-3.1")

    def test_empty_name(self):
        self.assertEqual(unique_model_name("", {"model"}), "")
        self.assertEqual(unique_model_name("   ", {"model"}), "")

    def test_never_returns_none_for_non_empty_input(self):
        existing = {"model", "model (1)", "model (2)", "llama-3.1"}
        for name in ("model", "llama-3.1", "model (1)"):
            result = unique_model_name(name, existing)
            self.assertIsNotNone(result, f"unique_model_name({name!r}) returned None")

    def test_single_duplicate_gets_suffix_1(self):
        self.assertEqual(unique_model_name("model", {"model"}), "model (1)")

    def test_multiple_duplicates_increment(self):
        existing = {"model", "model (1)", "model (2)"}
        self.assertEqual(unique_model_name("model", existing), "model (3)")

    def test_gap_in_suffixes_is_filled(self):
        existing = {"model", "model (2)"}
        self.assertEqual(unique_model_name("model", existing), "model (1)")


# ---------------------------------------------------------------------------
# chat — must return a str, never None (fixes NoneType regression)
# ---------------------------------------------------------------------------

class TestChatReturnsString(unittest.TestCase):
    def _fake_response(self, text):
        """Return a mock urllib response with the given text as message content."""
        body = json.dumps({
            "choices": [{"message": {"content": text}}]
        }).encode("utf-8")
        resp = MagicMock()
        resp.read.return_value = body
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        return resp

    @patch("homebench.urllib.request.urlopen")
    def test_returns_plain_text(self, mock_urlopen):
        mock_urlopen.return_value = self._fake_response("The answer is 42.")
        result = chat("http://localhost:1234", "prompt", 0.0, 8192, 300)
        self.assertIsInstance(result, str)
        self.assertEqual(result, "The answer is 42.")

    @patch("homebench.urllib.request.urlopen")
    def test_returns_empty_string_not_none(self, mock_urlopen):
        mock_urlopen.return_value = self._fake_response("")
        result = chat("http://localhost:1234", "prompt", 0.0, 8192, 300)
        self.assertIsInstance(result, str)
        self.assertEqual(result, "")

    @patch("homebench.urllib.request.urlopen")
    def test_strips_reasoning_blocks(self, mock_urlopen):
        mock_urlopen.return_value = self._fake_response(
            "thinking...\nAnswer: 2.80"
        )
        result = chat("http://localhost:1234", "prompt", 0.0, 8192, 300)
        self.assertIsInstance(result, str)


# ---------------------------------------------------------------------------
# Task check functions — must not crash on None input (defense in depth)
# ---------------------------------------------------------------------------

class TestTaskCheckHandlesNone(unittest.TestCase):
    def test_each_check_returns_false_on_none(self):
        for module in (math, logic, instructions, json_task,
                       code_task, game, bulgarian):
            # Should not raise; should return False for invalid input
            result = module.check(None)
            self.assertIsInstance(result, bool)
            self.assertFalse(result)


# ---------------------------------------------------------------------------
# send() — must handle str, bytes, and dict payloads
# ---------------------------------------------------------------------------

class TestSendHandlesBytes(unittest.TestCase):
    def _make_handler(self):
        """Create a Handler-like object with mocked socket methods."""
        h = Handler.__new__(Handler)
        h.send_response = MagicMock()
        h.send_header = MagicMock()
        h.end_headers = MagicMock()
        h.wfile = io.BytesIO()
        return h

    def test_send_str_payload(self):
        h = self._make_handler()
        h.send("hello world", ctype="text/plain")
        self.assertEqual(h.wfile.getvalue(), b"hello world")

    def test_send_bytes_payload(self):
        h = self._make_handler()
        raw = b'{"batch":1,"model":"m"}'
        h.send(raw, ctype="application/jsonl")
        self.assertEqual(h.wfile.getvalue(), raw)

    def test_send_dict_payload(self):
        h = self._make_handler()
        h.send({"ok": True})
        data = h.wfile.getvalue()
        self.assertEqual(json.loads(data), {"ok": True})


# ---------------------------------------------------------------------------
# _format_note — temperature appended to note
# ---------------------------------------------------------------------------

class TestFormatNote(unittest.TestCase):
    def test_empty_note_becomes_temperature_only(self):
        self.assertEqual(_format_note("", 0.7), "temp=0.7")
        self.assertEqual(_format_note(None, 0.0), "temp=0.0")
        self.assertEqual(_format_note("   ", 1.2), "temp=1.2")

    def test_temperature_appended_to_existing_note(self):
        self.assertEqual(_format_note("my run", 0.7), "my run (temp=0.7)")
        self.assertEqual(_format_note("baseline", 0.0), "baseline (temp=0.0)")


# ---------------------------------------------------------------------------
# work() — state["running"] must reset to False when benchmark finishes
# ---------------------------------------------------------------------------

class TestWorkResetsState(unittest.TestCase):
    def _make_handler(self, path="/api/run", body=None):
        """Create a Handler-like object with mocked socket methods and rfile."""
        h = Handler.__new__(Handler)
        h.send_response = MagicMock()
        h.send_header = MagicMock()
        h.end_headers = MagicMock()
        h.wfile = io.BytesIO()
        h.path = path
        h.headers = {"Content-Length": str(len(body or b"{}"))}
        h.rfile = io.BytesIO(body or b"{}")
        h.command = "POST"
        return h

    def _capture_work_function(self, h, body):
        """Call do_POST, capture the threading.Thread target (work function)."""
        with patch("homebench.run_benchmark"), \
             patch("homebench.threading.Thread") as mock_thread:
            h.do_POST()
            self.assertTrue(mock_thread.called)
            kwargs = mock_thread.call_args.kwargs
            return kwargs["target"]

    def test_state_running_reset_after_success(self):
        h = self._make_handler(body=json.dumps({
            "name": "test-model",
            "url": "http://localhost:1234",
            "runs": 1,
            "temperature": 0.7,
            "max_tokens": 8192,
        }).encode())
        work = self._capture_work_function(h, h.rfile.getvalue())

        # Simulate successful benchmark completion
        with patch("homebench.run_benchmark"):
            work()

        self.assertFalse(state["running"], "state['running'] should be False after success")

    def test_state_running_reset_after_exception(self):
        h = self._make_handler(body=json.dumps({
            "name": "test-model",
            "url": "http://localhost:1234",
            "runs": 1,
            "temperature": 0.7,
            "max_tokens": 8192,
        }).encode())
        work = self._capture_work_function(h, h.rfile.getvalue())

        # Simulate benchmark raising an exception
        def boom(*args, **kwargs):
            raise RuntimeError("server died")

        with patch("homebench.run_benchmark", side_effect=boom):
            with self.assertRaises(RuntimeError):
                work()

        self.assertFalse(state["running"], "state['running'] should be False after error")


# ---------------------------------------------------------------------------
# run_benchmark — single-task filtering via task_id
# ---------------------------------------------------------------------------

class TestRunBenchmarkSingleTask(unittest.TestCase):
    def _fake_response(self, text):
        body = json.dumps({"choices": [{"message": {"content": text}}]}).encode("utf-8")
        resp = MagicMock()
        resp.read.return_value = body
        resp.__enter__.return_value = resp
        resp.__exit__.return_value = False
        return resp

    @patch("homebench.urllib.request.urlopen")
    def test_task_id_filters_to_single_task(self, mock_urlopen):
        mock_urlopen.return_value = self._fake_response("Answer: 2.80")
        rows = []
        with patch("homebench.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            run_benchmark(
                "http://localhost:1234", "test-model", runs=2,
                temperature=0.0, max_tokens=8192, timeout=300,
                out_path="/tmp/results.jsonl", task_id="math",
                on_result=lambda *a: rows.append(a),
            )
        # Only math should have been called (runs=2), not all 8 tasks.
        self.assertEqual(mock_urlopen.call_count, 2)
        written = "".join(call.args[0] for call in mock_file.write.call_args_list)
        # All written rows should be for the math task.
        for line in written.strip().splitlines():
            row = json.loads(line)
            self.assertEqual(row["task"], "math")

    @patch("homebench.urllib.request.urlopen")
    def test_no_task_id_runs_all_tasks(self, mock_urlopen):
        mock_urlopen.return_value = self._fake_response("Answer: 2.80")
        with patch("homebench.open", create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file
            run_benchmark(
                "http://localhost:1234", "test-model", runs=1,
                temperature=0.0, max_tokens=8192, timeout=300,
                out_path="/tmp/results.jsonl",
            )
        # 8 tasks * 1 run each.
        self.assertEqual(mock_urlopen.call_count, len(TASKS))
        written = "".join(call.args[0] for call in mock_file.write.call_args_list)
        tasks_seen = {json.loads(line)["task"] for line in written.strip().splitlines()}
        self.assertEqual(tasks_seen, {t["id"] for t in TASKS})


if __name__ == "__main__":
    unittest.main()
