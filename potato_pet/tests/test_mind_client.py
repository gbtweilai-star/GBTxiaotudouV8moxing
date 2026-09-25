"""数字人面板心智适配层回归：引擎不可用时不影响原有主线。"""
from __future__ import annotations

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PET = os.path.dirname(_HERE)
if _PET not in sys.path:
    sys.path.insert(0, _PET)

from mind_client import MindClient  # noqa: E402


class _FakeEngine:
    def pulse(self):
        return {"ok": True, "mood": "好奇", "expression": "happy"}

    def observe(self, event, **payload):
        return {"ok": True, "event": event, "payload_keys": sorted(payload)}

    def recall(self, query, limit=5):
        return {"ok": True, "lessons": []}

    def decide(self, event, **payload):
        return {"action": "soft_note"}

    def status(self):
        return {"ok": True, "state": "awake"}


class TestMindClient(unittest.TestCase):
    def test_fail_open_when_engine_unavailable(self):
        client = MindClient()
        client._engine = None
        pulse = client.pulse()
        self.assertFalse(pulse["ok"])
        self.assertEqual(pulse["mood"], "平稳")
        observed = client.observe("user_message", text="hello")
        self.assertFalse(observed["ok"])
        self.assertEqual(observed["communication"]["action"], "silent")

    def test_delegates_to_engine_when_available(self):
        client = MindClient()
        client._engine = _FakeEngine()
        pulse = client.pulse()
        self.assertTrue(pulse["ok"])
        self.assertEqual(pulse["mood"], "好奇")
        observed = client.observe("pre_work", task="x", side_effect=True)
        self.assertEqual(observed["event"], "pre_work")
        self.assertIn("side_effect", observed["payload_keys"])

    def test_status_degrades_without_raising(self):
        client = MindClient()
        client._engine = None
        status = client.status()
        self.assertFalse(status["ok"])
        self.assertEqual(status["state"], "degraded")


if __name__ == "__main__":
    unittest.main(verbosity=2)
