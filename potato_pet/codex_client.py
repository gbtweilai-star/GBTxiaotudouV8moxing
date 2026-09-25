"""Codex 对话内核的 Qt 适配层。

把 gbt_allinone.codex_bridge 的流式事件、审批请求与工具活动转换成 Qt 信号，
供全息面板直接消费；Codex 不可用时由调用方回落到原有 LLM 通道。
"""
from __future__ import annotations

import logging
import os
import sys
import threading

from PySide6.QtCore import QObject, Signal

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_BASE_DIR)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from gbt_allinone import codex_bridge as CB  # noqa: E402

logger = logging.getLogger("potato.codex")

APPROVAL_TIMEOUT = 300.0


class CodexPanelClient(QObject):
    """数字人面板的 Codex 通道（流式、工具、审批、中断）。"""

    chunk = Signal(str)
    replied = Signal(str)
    thinking_changed = Signal(bool)
    status_changed = Signal(str)
    plan_updated = Signal(list)
    approval_requested = Signal(dict)
    turn_finished = Signal(dict)
    failed = Signal(str)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config or {}
        codex_cfg = self.config.get("codex", {}) or {}
        self.enabled = bool(codex_cfg.get("enabled", True))
        self.model = codex_cfg.get("model") or None
        self.sandbox = codex_cfg.get("sandbox", "workspace-write")
        self.effort = codex_cfg.get("effort") or None
        self.cwd = codex_cfg.get("cwd") or _ROOT

        self._server = None
        self._thread_id = None
        self._turn_id = None
        self._turn_active = False       # 是否有在途回合（决定 interrupt 是否真有活干）
        self._lock = threading.Lock()
        self._approvals: dict[int, dict] = {}
        self._approval_seq = 0
        self._delta_buf: list[str] = []
        self._replied_emitted = False

    @property
    def available(self) -> bool:
        return self.enabled and bool(CB.find_codex())

    def status(self) -> dict:
        result = CB.status()
        result["panel_enabled"] = self.enabled
        result["thread_id"] = self._thread_id
        return result

    def models(self) -> list:
        """列出本机 Codex 可用模型；失败时返回空列表，不打断面板。"""
        try:
            return self._ensure_server().list_models()
        except Exception as exc:  # noqa: BLE001
            logger.warning("codex model list failed: %s", exc)
            return []

    def start(self) -> bool:
        """预启动内核；返回是否可用。启动失败不抛异常，交给调用方降级。"""
        if not self.available:
            return False
        try:
            self._server = self._ensure_server()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("codex start failed: %s", exc)
            self.failed.emit(f"Codex 内核启动失败：{exc}")
            return False

    def stop(self) -> None:
        with self._lock:
            if self._server is not None:
                try:
                    self._server.stop()
                except Exception:  # noqa: BLE001
                    logger.debug("codex stop failed", exc_info=True)
                self._server = None

    def _ensure_server(self):
        if self._server is not None and self._server.alive:
            return self._server
        codex_cfg = self.config.get("codex", {}) or {}
        server = CB.CodexAppServer(
            cwd=self.cwd,
            codex_home=codex_cfg.get("codex_home") or None,
            on_event=self._on_event,
            on_approval=self._on_approval,
        )
        server.start()
        self._server = server
        return server

    def _ensure_thread(self, server) -> str:
        if self._thread_id:
            try:
                server.resume_thread(
                    self._thread_id,
                    model=self.model,
                    developer_instructions=self._instructions(),
                    dynamic_tools=CB.dynamic_tool_specs(),
                )
                return self._thread_id
            except CB.CodexAppServerError:
                logger.info("resume failed, starting a new Codex thread")
                self._thread_id = None
        result = server.start_thread(
            model=self.model,
            sandbox=self.sandbox,
            effort=self.effort,
            developer_instructions=self._instructions(),
            dynamic_tools=CB.dynamic_tool_specs(),
            ephemeral=bool((self.config.get("codex", {}) or {}).get("ephemeral", False)),
        )
        self._thread_id = (result.get("thread") or {}).get("id")
        return self._thread_id or ""

    def _instructions(self) -> str:
        persona = (self.config.get("chat", {}) or {}).get("persona", "")
        return CB.default_developer_instructions(persona)

    def new_thread(self) -> None:
        with self._lock:
            self._thread_id = None
            self._turn_id = None
            self._turn_active = False

    def send(self, text: str) -> bool:
        """后台线程发起一个回合；立即返回是否成功派发。"""
        text = (text or "").strip()
        if not text:
            return False
        if not self.available:
            self.failed.emit("Codex 未就绪")
            return False
        threading.Thread(target=self._run_turn, args=(text,),
                         name="potato-codex-turn", daemon=True).start()
        return True

    def _run_turn(self, text: str) -> None:
        self._delta_buf = []
        self._replied_emitted = False
        self._turn_active = True
        self.thinking_changed.emit(True)
        self.status_changed.emit("正在理解你的需求…")
        try:
            with self._lock:
                server = self._ensure_server()
                thread_id = self._ensure_thread(server)
            turn = server.start_turn(thread_id, text, model=self.model,
                                     effort=self.effort)
            self._turn_id = (turn.get("turn") or {}).get("id")
            self.status_changed.emit("正在推进任务…")
        except Exception as exc:  # noqa: BLE001
            logger.warning("codex turn failed: %s", exc)
            self._turn_active = False
            self.thinking_changed.emit(False)
            self.failed.emit(str(exc))

    def interrupt(self) -> bool:
        """请求中断在途回合；没有在途回合时返回 False（不再假报成功）。

        旧实现只判断 `server is None or not self._thread_id`——只要跑过任意一次
        回合，之后空闲时点中断都会 return True，界面随即播报「已请求中断当前任务」，
        用户以为拦下了什么。
        """
        server = self._server
        if server is None or not self._thread_id or not self._turn_active:
            return False
        try:
            server.interrupt(self._thread_id, self._turn_id)
            return True
        except CB.CodexAppServerError as exc:
            logger.warning("interrupt failed: %s", exc)
            return False

    def _on_event(self, method: str, params: dict) -> None:
        if method == "item/agentMessage/delta":
            piece = params.get("delta") or ""
            if piece:
                self._delta_buf.append(piece)
                self.chunk.emit(piece)
            return
        if method == "item/completed":
            item = params.get("item") or {}
            itype = item.get("type")
            if itype == "agentMessage":
                phase = item.get("phase")
                text = item.get("text") or ""
                if text and phase in ("final_answer", None):
                    self._replied_emitted = True
                    self.replied.emit(text)
            elif itype == "commandExecution":
                command = (item.get("command") or "").strip()
                if command:
                    self.status_changed.emit(f"已执行：{command[:60]}")
            elif itype == "fileChange":
                self.status_changed.emit("已更新文件")
            return
        if method == "item/started":
            kind = (params.get("item") or {}).get("type")
            if kind == "commandExecution":
                self.status_changed.emit("正在执行命令…")
            elif kind == "fileChange":
                self.status_changed.emit("正在修改文件…")
            elif kind == "reasoning":
                self.status_changed.emit("正在分析…")
            return
        if method == "item/commandExecution/outputDelta":
            piece = (params.get("delta") or "").strip()
            if piece and len(piece) < 400:
                self.status_changed.emit(piece[:80])
            return
        if method == "turn/plan/updated":
            plan = params.get("plan") or params.get("steps") or []
            if isinstance(plan, list):
                self.plan_updated.emit(plan)
            return
        if method == "turn/completed":
            turn = params.get("turn") or {}
            self._turn_active = False
            if not self._replied_emitted and self._delta_buf:
                self._replied_emitted = True
                self.replied.emit("".join(self._delta_buf))
            self.thinking_changed.emit(False)
            self.status_changed.emit("")
            self.turn_finished.emit({
                "thread_id": params.get("threadId"),
                "turn_id": turn.get("id"),
                "status": turn.get("status"),
            })
            return
        if method == "error":
            detail = params.get("message") or params.get("detail") or "未知错误"
            self._turn_active = False
            self.failed.emit(str(detail)[:300])

    def _on_approval(self, method: str, params: dict):
        with self._lock:
            self._approval_seq += 1
            req_id = self._approval_seq
            slot = {"event": threading.Event(), "decision": None, "method": method}
            self._approvals[req_id] = slot
        self.approval_requested.emit({
            "id": req_id,
            "method": method,
            "params": params,
            "summary": self._describe_approval(method, params),
        })
        if slot["event"].wait(APPROVAL_TIMEOUT):
            return slot["decision"]
        with self._lock:
            self._approvals.pop(req_id, None)
        logger.info("approval %s timed out, declining", req_id)
        return None

    def resolve_approval(self, req_id: int, decision: str) -> None:
        """GUI 线程调用：把主人裁决回传给 Codex。"""
        with self._lock:
            slot = self._approvals.pop(req_id, None)
        if slot is None:
            return
        slot["decision"] = self._decision_payload(slot.get("method"), decision)
        slot["event"].set()

    @staticmethod
    def _decision_payload(method: str, decision: str) -> dict:
        if method == "item/permissions/requestApproval":
            return {"permissions": {},
                    "scope": "session" if decision == "acceptForSession" else "turn"}
        if method == "item/tool/requestUserInput":
            return {"answers": {}}
        if method == "mcpServer/elicitation/request":
            return {"action": "accept" if decision == "accept" else "decline"}
        return {"decision": decision}

    @staticmethod
    def _describe_approval(method: str, params: dict) -> dict:
        if method == "item/commandExecution/requestApproval":
            return {"kind": "command", "title": "请求执行命令",
                    "detail": str(params.get("command") or "")[:600],
                    "cwd": str(params.get("cwd") or "")}
        if method == "item/fileChange/requestApproval":
            return {"kind": "file", "title": "请求修改文件",
                    "detail": str(params.get("reason") or params.get("path") or "")[:600]}
        if method == "item/permissions/requestApproval":
            return {"kind": "permissions", "title": "请求额外权限",
                    "detail": str(params.get("reason") or "")[:600]}
        if method == "item/tool/requestUserInput":
            return {"kind": "question", "title": "需要你确认",
                    "detail": str(params.get("prompt") or params.get("question") or "")[:600]}
        return {"kind": "other", "title": "需要你确认",
                "detail": str(params)[:600]}
