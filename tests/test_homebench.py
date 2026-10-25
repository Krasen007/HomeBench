"""Tests for HomeBench to prevent regressions.

Covers fixes for:
1. chat() returning None instead of the model response text
2. send() failing on bytes payloads (results export)
3. unique_model_name() returning None on duplicate model names
"""
import io
import json
import unittest
from unittest.mock import MagicMock, patch

from homebench import chat, unique_model_name, Handler, TASKS
from tasks import math, logic, instructions, json_task, code_task, game, bulgarian


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


if __name__ == "__main__":
    unittest.main()
