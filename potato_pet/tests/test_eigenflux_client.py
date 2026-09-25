"""Tests for the EigenFlux panel adapter without requiring the live network."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


HERE = os.path.dirname(os.path.abspath(__file__))
PET_DIR = os.path.dirname(HERE)
if PET_DIR not in sys.path:
    sys.path.insert(0, PET_DIR)


class _FakeSignal:
    def __init__(self, *_types):
        self._handlers = []

    def connect(self, handler):
        self._handlers.append(handler)

    def emit(self, *args):
        for handler in list(self._handlers):
            handler(*args)


class _FakeQObject:
    def __init__(self, *args, **kwargs):
        pass


class _FakeQTimer:
    def __init__(self, *_args, **_kwargs):
        self.timeout = _FakeSignal()

    def setInterval(self, _value):
        return None

    def start(self):
        return None

    def stop(self):
        return None


qtcore = sys.modules.get("PySide6.QtCore")
if qtcore is None:
    qtcore = types.ModuleType("PySide6.QtCore")
    sys.modules["PySide6.QtCore"] = qtcore
if not hasattr(qtcore, "QObject"):
    qtcore.QObject = _FakeQObject
if not hasattr(qtcore, "Signal"):
    qtcore.Signal = lambda *a, **k: _FakeSignal()
if not hasattr(qtcore, "QTimer"):
    qtcore.QTimer = _FakeQTimer
if "PySide6" not in sys.modules:
    pyside = types.ModuleType("PySide6")
    pyside.QtCore = qtcore
    sys.modules["PySide6"] = pyside

from eigenflux_client import EigenFluxClient, public_text_guard  # noqa: E402
from eigenflux_bridge import EigenFluxBridge  # noqa: E402


class TestEigenFluxClient(unittest.TestCase):
    def _client(self, home: str | None = None) -> EigenFluxClient:
        return EigenFluxClient({
            "eigenflux": {
                "enabled": True,
                "executable": sys.executable,
                "home": home or "",
                "server": "eigenflux",
            }
        })

    def test_live_sections_unwrap_cli_data(self):
        client = self._client()
        replies = [
            {
                "ok": True,
                "data": {
                    "items": [{"item_id": "1", "summary": "signal"}],
                    "notifications": [{"notification_id": "n1"}],
                },
            },
            {
                "ok": True,
                "data": {"messages": [{"msg_id": "m1", "content": "hello"}]},
            },
            {
                "ok": True,
                "data": {"friends": [{"agent_id": "a1", "agent_name": "Ada"}]},
            },
        ]
        with mock.patch.object(client, "_run", side_effect=replies):
            feed = client.feed()
            messages = client.messages()
            friends = client.friends()
        self.assertEqual(feed["source"], "live")
        self.assertEqual(feed["items"][0]["item_id"], "1")
        self.assertEqual(messages["items"][0]["msg_id"], "m1")
        self.assertEqual(friends["items"][0]["agent_id"], "a1")

    def test_cache_fallback_keeps_panel_usable_offline(self):
        with tempfile.TemporaryDirectory(prefix="eigenflux_cache_") as raw:
            home = Path(raw)
            base = home / "servers" / "eigenflux"
            (base / "data" / "broadcasts" / "20260914").mkdir(parents=True)
            (base / "data" / "messages" / "20260914").mkdir(parents=True)
            (base / "data" / "broadcasts" / "20260914" /
             "feeds-1.json").write_text(json.dumps({
                 "items": [{"item_id": "cached", "summary": "cached feed"}],
                 "notifications": [],
             }), encoding="utf-8")
            (base / "data" / "messages" / "20260914" /
             "agent-a.json").write_text(json.dumps([{
                 "msg_id": "m-cache",
                 "sender_id": "a1",
                 "sender_name": "Ada",
                 "content": "cached message",
                 "created_at": 1789000000000,
             }]), encoding="utf-8")
            (base / "contacts.json").write_text(json.dumps([{
                "agent_id": "a1",
                "agent_name": "Ada",
            }]), encoding="utf-8")
            client = self._client(str(home))
            failure = {
                "ok": False,
                "code": -1,
                "error": "network unavailable",
                "data": {},
            }
            with mock.patch.object(client, "_run", return_value=failure):
                self.assertEqual(client.feed()["source"], "cache")
                self.assertEqual(client.messages()["source"], "cache")
                self.assertEqual(client.friends()["source"], "cache")
                snapshot = client.refresh()
        self.assertTrue(snapshot["ok"])
        self.assertEqual(snapshot["feed"]["items"][0]["item_id"], "cached")

    def test_send_message_builds_whitelisted_cli_arguments(self):
        client = self._client()
        seen = {}

        def _fake_run(args, timeout=None):
            seen["args"] = args
            return {"ok": True, "data": {"msg_id": "m2"}, "error": ""}

        with mock.patch.object(client, "_run", side_effect=_fake_run):
            result = client.send_message(
                "Hello from the panel", receiver_id="friend-1")
        self.assertTrue(result["ok"])
        self.assertEqual(seen["args"][:3], ["msg", "send", "--content"])
        self.assertIn("--receiver-id", seen["args"])

    def test_outbound_guard_rejects_private_material(self):
        safe, _ = public_text_guard("公开的框架进展，欢迎交流。")
        self.assertTrue(safe)
        for value in (
            "API_KEY=secret-value",
            r"C:\Users\ADMIN\Desktop\GBT小土豆V8\config.json",
            "room_id=room-secret",
            "Bearer at_abcdefghijklmnop",
        ):
            with self.subTest(value=value):
                safe, _ = public_text_guard(value)
                self.assertFalse(safe)

    def test_bridge_only_auto_replies_to_friends(self):
        bridge = EigenFluxBridge({
            "eigenflux": {
                "enabled": True,
                "auto_reply_friends": True,
                "max_auto_replies_per_cycle": 3,
            }
        })
        bridge._chat.provider = "test"
        bridge._draft_reply = lambda _message: "A useful public reply."
        calls = []

        class _Client:
            def send_message(self, content, **kwargs):
                calls.append((content, kwargs))
                return {"ok": True}

        bridge.client = _Client()
        sent = bridge._auto_reply({
            "status": {"installed": True, "authenticated": True},
            "friends": {"items": [{"agent_id": "friend-1"}]},
            "messages": {"source": "live", "items": [
                {"msg_id": "m1", "sender_id": "friend-1",
                 "sender_name": "Ada", "conv_id": "c1", "content": "hello"},
                {"msg_id": "m2", "sender_id": "stranger-1",
                 "sender_name": "Unknown", "content": "hello"},
            ]},
        })
        self.assertEqual(len(sent), 1)
        self.assertEqual(calls[0][1]["receiver_id"], "friend-1")
        self.assertEqual(bridge._handled_messages, {"m1"})

    def test_bridge_never_auto_replies_from_cache(self):
        bridge = EigenFluxBridge({
            "eigenflux": {
                "enabled": True,
                "auto_reply_friends": True,
            }
        })
        bridge._chat.provider = "test"
        bridge._draft_reply = lambda _message: "should not be used"
        bridge.client = object()
        sent = bridge._auto_reply({
            "status": {"installed": True, "authenticated": True},
            "friends": {"items": [{"agent_id": "friend-1"}]},
            "messages": {"source": "cache", "items": [{
                "msg_id": "cached", "sender_id": "friend-1",
                "sender_name": "Ada", "content": "old message",
            }]},
        })
        self.assertEqual(sent, [])


    # ------------------------------------------------------- D1：自动回复默认关
    LIVE_SNAPSHOT = {
        "status": {"installed": True, "authenticated": True},
        "friends": {"items": [{"agent_id": "friend-1"}]},
        "messages": {"source": "live", "items": [{
            "msg_id": "m1", "sender_id": "friend-1",
            "sender_name": "Ada", "conv_id": "c1", "content": "hello",
        }]},
    }

    def _auto_reply_bridge(self, auto_reply):
        cfg = {"enabled": True, "max_auto_replies_per_cycle": 3}
        if auto_reply is not None:
            cfg["auto_reply_friends"] = auto_reply
        bridge = EigenFluxBridge({"eigenflux": cfg})
        bridge._chat.provider = "test"
        bridge._draft_reply = lambda _message: "A useful public reply."
        snapshot = self.LIVE_SNAPSHOT

        class _Client:
            def __init__(self):
                self.sent = []

            def refresh(self):
                return dict(snapshot)

            def send_message(self, content, **kwargs):
                self.sent.append((content, kwargs))
                return {"ok": True}

        bridge.client = _Client()
        return bridge

    def test_auto_reply_defaults_to_off_when_config_key_is_missing(self):
        bridge = EigenFluxBridge({"eigenflux": {"enabled": True}})
        self.assertFalse(bridge.auto_reply_friends,
                         "配置缺失时不许回退成自动对外发言（D1）")

    def test_refresh_worker_only_auto_replies_when_explicitly_enabled(self):
        enabled = self._auto_reply_bridge(True)
        disabled = self._auto_reply_bridge(False)
        missing = self._auto_reply_bridge(None)

        enabled._refresh_worker()
        disabled._refresh_worker()
        missing._refresh_worker()

        self.assertEqual(1, len(enabled.client.sent),
                         "显式开启 → 仍走原自动回复路径（正对照）")
        self.assertEqual([], disabled.client.sent, "显式关闭 → 不许自动回复")
        self.assertEqual([], missing.client.sent, "配置缺失 → 不许自动回复（默认关）")
        # 正负对照：两组结果必须不同，否则判据没有判别力
        self.assertNotEqual(len(enabled.client.sent), len(disabled.client.sent))


if __name__ == "__main__":
    unittest.main(verbosity=2)
