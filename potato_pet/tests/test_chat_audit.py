"""Digital-human chat egress must pass through the application-level audit."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


_STORE = Path(tempfile.mkdtemp(prefix="gbt_chat_audit_test_"))
os.environ["GBT_STORE_DIR"] = str(_STORE)

_HERE = os.path.dirname(os.path.abspath(__file__))
_PET = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PET)
for path in (_PET, _ROOT):
    if path not in sys.path:
        sys.path.insert(0, path)

from gbt_allinone import _paths  # noqa: E402
from gbt_allinone.security import ai_audit  # noqa: E402
from chat_client import ChatClient  # noqa: E402

_paths.STORE_DIR = _STORE


class _FakeResponse:
    def __init__(self, data=None, status_code=200, lines=None):
        self._data = data or {}
        self.status_code = status_code
        self._lines = list(lines or [])

    def raise_for_status(self):
        return None

    def json(self):
        return self._data

    def iter_lines(self, decode_unicode=True):
        return iter(self._lines)

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False


class TestDigitalHumanChatAudit(unittest.TestCase):
    def setUp(self):
        path = ai_audit._audit_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.unlink(missing_ok=True)
        self.client = ChatClient({"chat": {}})
        self.client.api_key = "sk-abcdefghijklmnop"
        self.client.base_url = "https://api.openai.com/v1"
        self.client.model = "gpt-test"
        self.client.provider = "openai"
        self.client.timeout = 10
        self.client.audit_session_id = "panel-session"

    def test_non_stream_chat_records_metadata_only(self):
        response = _FakeResponse(data={
            "choices": [{"message": {"content": "private answer"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 2,
                      "total_tokens": 3},
        })
        replies = []
        with mock.patch("requests.post", return_value=response):
            self.client._call_glm("private prompt", replies.append)
        self.assertEqual(replies, ["private answer"])
        rows = ai_audit.query()
        self.assertEqual([row["event"] for row in rows],
                         ["ai_request", "ai_response"])
        self.assertNotIn("private prompt", json.dumps(rows))
        self.assertNotIn("private answer", json.dumps(rows))
        self.assertNotIn("sk-abcdefghijklmnop", json.dumps(rows))

    def test_stream_chat_records_final_fingerprint(self):
        response = _FakeResponse(lines=[
            'data: {"choices":[{"delta":{"content":"hel"}}]}',
            'data: {"choices":[{"delta":{"content":"lo"}}]}',
            "data: [DONE]",
        ])
        chunks = []
        replies = []
        with mock.patch("requests.post", return_value=response):
            self.client._call_glm_stream(
                "private stream prompt", replies.append,
                lambda delta, full: chunks.append((delta, full)),
            )
        self.assertEqual(replies, ["hello"])
        rows = ai_audit.query()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]["response_meta"]["content_chars"], 5)
        self.assertNotIn("private stream prompt", json.dumps(rows))


if __name__ == "__main__":
    unittest.main(verbosity=2)
