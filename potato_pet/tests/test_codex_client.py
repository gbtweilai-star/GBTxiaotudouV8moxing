"""Codex Qt 适配层测试：用轻量 Qt 桩验证事件映射与审批往返。

不依赖真实 PySide6 安装；只覆盖纯逻辑（信号转发 / 裁决回传 / 活动文案）。
"""
from __future__ import annotations

import os
import sys
import threading
import types
import unittest
from unittest import mock


class _FakeSignal:
    def __init__(self, *_types):
        self._handlers: list = []

    def connect(self, handler):
        self._handlers.append(handler)

    def emit(self, *args):
        for handler in list(self._handlers):
            handler(*args)

    def disconnect(self, handler=None):
        if handler is None:
            self._handlers = []
        elif handler in self._handlers:
            self._handlers.remove(handler)


class _FakeQObject:
    def __init__(self, *args, **kwargs):
        pass


def _install_qt_stub() -> None:
    if "PySide6.QtCore" in sys.modules:
        return
    qtcore = types.ModuleType("PySide6.QtCore")
    qtcore.QObject = _FakeQObject
    qtcore.Signal = lambda *a, **k: _FakeSignal()
    pyside = types.ModuleType("PySide6")
    pyside.QtCore = qtcore
    sys.modules["PySide6"] = pyside
    sys.modules["PySide6.QtCore"] = qtcore


_install_qt_stub()

_HERE = os.path.dirname(os.path.abspath(__file__))
_PET = os.path.dirname(_HERE)
sys.path.insert(0, _PET)

from codex_client import CodexPanelClient  # noqa: E402
from gbt_allinone import codex_bridge as CB  # noqa: E402


class TestCodexPanelClient(unittest.TestCase):
    def setUp(self):
        self.client = CodexPanelClient({"codex": {"enabled": True}})

    def test_delta_maps_to_chunk_and_accumulates(self):
        seen: list[str] = []
        self.client.chunk.connect(seen.append)
        self.client._delta_buf = []
        self.client._replied_emitted = False
        self.client._on_event("item/agentMessage/delta", {"delta": "he"})
        self.client._on_event("item/agentMessage/delta", {"delta": "llo"})
        self.assertEqual(seen, ["he", "llo"])
        self.assertEqual("".join(self.client._delta_buf), "hello")

    def test_final_answer_emits_replied_once(self):
        replies: list[str] = []
        self.client.replied.connect(replies.append)
        self.client._delta_buf = ["draft"]
        self.client._replied_emitted = False
        self.client._on_event("item/completed", {
            "item": {"type": "agentMessage", "text": "final", "phase": "final_answer"}})
        self.client._on_event("turn/completed", {"turn": {"id": "t1", "status": "done"}})
        self.assertEqual(replies, ["final"])

    def test_turn_completed_falls_back_to_delta_buffer(self):
        replies: list[str] = []
        self.client.replied.connect(replies.append)
        self.client._delta_buf = ["only", " delta"]
        self.client._replied_emitted = False
        self.client._on_event("turn/completed", {
            "threadId": "th", "turn": {"id": "t1", "status": "done"}})
        self.assertEqual(replies, ["only delta"])

    def test_turn_completed_clears_thinking(self):
        states: list[bool] = []
        self.client.thinking_changed.connect(states.append)
        self.client._on_event("turn/completed", {"turn": {"id": "t", "status": "done"}})
        self.assertEqual(states, [False])

    def test_status_reports_activity_for_commands(self):
        notes: list[str] = []
        self.client.status_changed.connect(notes.append)
        self.client._on_event("item/started", {"item": {"type": "commandExecution"}})
        self.client._on_event("item/completed", {
            "item": {"type": "commandExecution", "command": "pytest -q"}})
        self.assertTrue(any("命令" in n for n in notes))
        self.assertTrue(any("pytest" in n for n in notes))

    def test_approval_roundtrip_returns_decision(self):
        requests: list[dict] = []
        self.client.approval_requested.connect(requests.append)
        holder: dict = {}

        def worker():
            holder["result"] = self.client._on_approval(
                "item/commandExecution/requestApproval",
                {"command": "rm -rf /tmp/x", "cwd": "C:/work"})

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        for _ in range(200):
            if requests:
                break
            threading.Event().wait(0.01)
        self.assertTrue(requests, "未收到审批请求信号")
        req = requests[0]
        self.assertEqual(req["summary"]["kind"], "command")
        self.assertIn("rm -rf", req["summary"]["detail"])
        self.client.resolve_approval(req["id"], "accept")
        thread.join(timeout=5)
        self.assertEqual(holder.get("result"), {"decision": "accept"})

    def test_permissions_approval_maps_scope(self):
        self.assertEqual(
            self.client._decision_payload(
                "item/permissions/requestApproval", "acceptForSession"),
            {"permissions": {}, "scope": "session"})
        self.assertEqual(
            self.client._decision_payload(
                "item/permissions/requestApproval", "accept"),
            {"permissions": {}, "scope": "turn"})

    def test_describe_approval_variants(self):
        self.assertEqual(
            self.client._describe_approval("item/fileChange/requestApproval",
                                           {"reason": "write config"})["kind"],
            "file")
        self.assertEqual(
            self.client._describe_approval("item/tool/requestUserInput",
                                           {"prompt": "pick one"})["kind"],
            "question")

    def test_new_thread_resets_ids(self):
        self.client._thread_id = "old"
        self.client._turn_id = "oldturn"
        self.client.new_thread()
        self.assertIsNone(self.client._thread_id)
        self.assertIsNone(self.client._turn_id)

    def test_new_thread_registers_gbt_dynamic_tools_and_discipline(self):
        server = mock.Mock()
        server.start_thread.return_value = {"thread": {"id": "thread-tools"}}
        tools = [{"name": "gbt_native_browser"}]
        with mock.patch.object(CB, "dynamic_tool_specs", return_value=tools):
            thread_id = self.client._ensure_thread(server)
        self.assertEqual(thread_id, "thread-tools")
        kwargs = server.start_thread.call_args.kwargs
        self.assertEqual(kwargs["dynamic_tools"], tools)
        self.assertIn("执行前先看再动", kwargs["developer_instructions"])
        self.assertIn("gbt_universal_plug", kwargs["developer_instructions"])
        self.assertIn("gbt_tentacle", kwargs["developer_instructions"])
        self.assertIn("gbt_mind", kwargs["developer_instructions"])
        self.assertIn("功能型人类心智顺序", kwargs["developer_instructions"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
