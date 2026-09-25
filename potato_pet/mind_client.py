"""数字人面板到 GBT 心智引擎的轻量适配层。

面板只依赖这个适配器，不直接耦合框架内部存储。心智引擎不可用时返回稳定
降级脉冲，原有对话、动画和语音能力继续工作。
"""
from __future__ import annotations

import os
import sys

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_BASE_DIR)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
if _BASE_DIR not in sys.path:
    sys.path.insert(0, _BASE_DIR)

import ui_theme as T  # noqa: E402  （配色 token 单一真源）


def _fallback(reason: str = "") -> dict:
    return {
        "ok": False,
        "mood": "平稳",
        "expression": "happy",
        "color": T.ACCENT_BRIGHT,
        "presence": "在场",
        "communication": {"action": "silent", "reason": reason},
        "emotions": {},
        "relationship": {},
        "needs": {},
        "self_model": {},
        "owner_model": {"state": "unknown", "confidence": 0.0},
        "intention": {},
        "metacognition": {"mode": "inspect_then_act", "should_pause": False},
        "appraisal": {},
        "reasoning_options": [],
        "lesson_count": 0,
    }


class MindClient:
    """以显式方法调用心智引擎，并在失败时不影响数字人主流程。"""

    def __init__(self):
        self._engine = None
        self.error = ""
        try:
            from gbt_allinone import mind_engine
            self._engine = mind_engine
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"[:200]

    @property
    def available(self) -> bool:
        return self._engine is not None

    def pulse(self) -> dict:
        if self._engine is None:
            return _fallback(self.error)
        try:
            return self._engine.pulse()
        except Exception as exc:
            return _fallback(f"{type(exc).__name__}: {exc}"[:160])

    def observe(self, event: str, **payload) -> dict:
        if self._engine is None:
            return _fallback(self.error)
        try:
            return self._engine.observe(event, **payload)
        except Exception as exc:
            return _fallback(f"{type(exc).__name__}: {exc}"[:160])

    def recall(self, query: str, limit: int = 5) -> dict:
        if self._engine is None:
            return {"ok": False, "lessons": [], "error": self.error}
        try:
            return self._engine.recall(query, limit)
        except Exception as exc:
            return {
                "ok": False,
                "lessons": [],
                "error": f"{type(exc).__name__}: {exc}"[:160],
            }

    def decide(self, event: str, **payload) -> dict:
        if self._engine is None:
            return _fallback(self.error)["communication"]
        try:
            return self._engine.decide(event, **payload)
        except Exception as exc:
            return {
                "action": "silent",
                "reason": f"mind unavailable: {type(exc).__name__}",
            }

    def status(self) -> dict:
        if self._engine is None:
            return {"ok": False, "state": "degraded", "error": self.error}
        try:
            return self._engine.status()
        except Exception as exc:
            return {
                "ok": False,
                "state": "degraded",
                "error": f"{type(exc).__name__}: {exc}"[:160],
            }
