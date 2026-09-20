# gbt-capability: meta_cognition
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""元认知循环（meta_cognition）· R-H200 只读骨架。

**知道自己不知道，比什么都知道更重要。**
四步：自省 → 先查内部 → 再查外部（需授权）→ 问主人 → 沉淀 → 进化。

五条红线（做成机械闸）：
  ① 自省不是自责 ② 不懂就问，不许硬猜 ③ 先查后问，不许瞎问
  ④ 问完必须沉淀 ⑤ 大脑也要自省。

本骨架只读：不写盘（**引用** root_fix.work_log 作为落点）、不出网、不执行。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

GAP_TYPES = ("missing_context", "uncertain", "unknown_topic", "missing_param")
GAP_CN = {"missing_context": "缺上下文", "uncertain": "不确定",
          "unknown_topic": "未知领域", "missing_param": "缺参数"}

SCOPES = ("tentacle", "brain", "router", "gate", "audit")

KNOWLEDGE_SPOTS = (
    "gbt_allinone/store/devoured/<主题>/knowledge.json",
    "gbt_allinone/store/pipeline/records/absorbed_knowledge.md-*.json",
    "gbt_allinone/brain_vault.py",
)

EXTERNAL_SCOPES = ("network_private", "external_llm", "data_export")

_SELF_BLAME_HINTS = ("我太差", "我真笨", "我完蛋", "我就是不行", "我不配", "我是废物")

RED_LINES = (
    "自省不是自责——自检只记录『哪里卡了』，不写『我太差了』（情绪归导演，自省归系统）",
    "不懂就问，不许硬猜——缺上下文 missing_context；不确定 uncertain；一律拒执行",
    "先查后问，不许瞎问——先查内部知识库，再查外部资料，最后才提问",
    "问完必须沉淀——得到答案后写入知识库，下次不用再问",
    "大脑也要自省——自省不只针对触手，大脑/路由/门禁/审计也要自检短板",
)


@dataclass
class SelfReflection:
    task_id: str
    scope: str = "tentacle"
    gaps: List[Dict] = field(default_factory=list)
    guesses: List[str] = field(default_factory=list)
    resolution: Optional[str] = None


class MetaCognitionLoop:
    """元认知循环（内存态骨架）：自省 → 查内部 → 查外部 → 问 → 沉淀。"""

    def __init__(self) -> None:
        self.reflections: List[SelfReflection] = []
        self.knowledge: Dict[str, str] = {}
        self.lookups: Dict[str, List[str]] = {}
        self.asked: Dict[str, str] = {}
        self.work_log_ref = "root_fix.work_log"

    def reflect(self, task_id: str, gaps: Optional[List[Dict]] = None,
                guesses: Optional[List[str]] = None, scope: str = "tentacle") -> dict:
        sc = str(scope or "tentacle").strip()
        if sc not in SCOPES:
            raise ValueError("未知 scope %r（可用：%s）" % (sc, "/".join(SCOPES)))
        rows = [dict(g) for g in (gaps or []) if isinstance(g, dict)]
        for g in rows:
            if g.get("type") not in GAP_TYPES:
                return {"ok": False, "denied": True, "rule": "unknown_gap_type",
                        "why": "gap 类型必须在 %s 之内（实测：%r）"
                               % ("/".join(GAP_TYPES), g.get("type"))}
        blob = " ".join(str(g.get("note") or "") for g in rows) \
            + " ".join(str(x) for x in (guesses or []))
        hit = [h for h in _SELF_BLAME_HINTS if h in blob]
        if hit:
            return {"ok": False, "denied": True, "rule": "self_blame_not_allowed",
                    "why": "自省不是自责（出现 %s）：情绪归导演，自省归系统 —— 只记『哪里卡了』" % hit}
        ref = SelfReflection(task_id=str(task_id or ""), scope=sc, gaps=rows,
                             guesses=[str(x) for x in (guesses or [])])
        self.reflections.append(ref)
        return {"ok": True, "readonly": True, "task_id": ref.task_id, "scope": ref.scope,
                "gaps": ref.gaps, "guesses": ref.guesses, "log_ref": self.work_log_ref}

    def look_up(self, topic: str, inside: bool = True) -> dict:
        key = str(topic or "").strip()
        if not key:
            raise ValueError("topic 不能为空")
        self.lookups.setdefault(key, [])
        if inside:
            if key in self.knowledge:
                self.lookups[key].append("knowledge_base")
                return {"ok": True, "readonly": True, "source": "knowledge_base",
                        "answer": self.knowledge[key]}
            self.lookups[key].append("internal_spots")
            return {"ok": False, "readonly": True, "reason": "not_in_knowledge_base",
                    "checked": list(KNOWLEDGE_SPOTS), "next": "查外部资料（需授权）或问主人"}
        self.lookups[key].append("external")
        return {"ok": True, "readonly": True, "source": "external",
                "requires_scopes": list(EXTERNAL_SCOPES),
                "note": "外部查证要授权：network_private / external_llm / data_export"}

    def external_scopes(self) -> dict:
        return {"ok": True, "readonly": True, "scopes": list(EXTERNAL_SCOPES),
                "note": "查外部资料必须先拿这三个作用域之一（主人发授权）"}

    def ask_owner(self, question: str, topic: str = "") -> dict:
        key = str(topic or question or "").strip()
        if not self.lookups.get(key):
            return {"ok": False, "denied": True, "rule": "must_look_up_first",
                    "why": "先查后问，不许瞎问：查过内部（必要时外部）再来问主人"}
        if key in self.asked:
            return {"ok": False, "denied": True, "rule": "already_asked_deposit_first",
                    "why": "这个问题问过了：先把答案沉淀进知识库，再谈下一步"}
        self.asked[key] = str(question or "")
        return {"ok": False, "reason": "need_owner_input", "question": str(question or ""),
                "topic": key, "note": "不确定就不执行，等主人回答"}

    def answer(self, topic: str, answer_text: str) -> dict:
        """收到主人答案 ⇒ **必须沉淀**（红线④）。"""
        key = str(topic or "").strip()
        if not str(answer_text or "").strip():
            return {"ok": False, "denied": True, "rule": "empty_answer"}
        self.knowledge[key] = str(answer_text)
        self.asked.pop(key, None)
        return {"ok": True, "readonly": True, "topic": key, "deposited": True,
                "note": "沉淀入知识库：下次不用再问"}

    def decide(self, gaps: Optional[List[Dict]] = None, guess: bool = False) -> dict:
        """下一步该干什么：**有缺口 ⇒ 先查再问，不许硬做**。"""
        rows = [g for g in (gaps or []) if isinstance(g, dict)]
        if guess:
            return {"ok": False, "denied": True, "rule": "no_guessing",
                    "why": "不懂就问，不许硬猜（盲猜即违规）"}
        if rows:
            return {"ok": False, "reason": "need_lookup_or_ask",
                    "gaps": [g.get("type") for g in rows],
                    "next": ["look_up(inside=True)", "look_up(inside=False)", "ask_owner()"],
                    "note": "有缺口就停下：先查内部 → 再查外部 → 最后问主人"}
        return {"ok": True, "readonly": True, "proceed": True}

    def report_short_boards(self, require_brain: bool = True) -> dict:
        """短板汇总（含大脑）：**只记触手不记大脑 ⇒ 拒**（红线⑤）。"""
        boards, scopes = set(), set()
        for ref in self.reflections:
            scopes.add(ref.scope)
            for g in ref.gaps:
                boards.add(g.get("type"))
        out = {"ok": True, "readonly": True, "short_boards": sorted(boards),
                "scopes_seen": sorted(scopes), "reflections": len(self.reflections),
                "bind_to": "native_surface（原生面）"}
        if require_brain and "brain" not in scopes:
            out["ok"] = False
            out["rule"] = "brain_not_covered"
            out["why"] = "大脑也要自省：自省记录里必须出现 scope=brain（不只触手）"
        return out


_DEFAULT = MetaCognitionLoop()


def run(op="law", **params) -> dict:
    """能力入口（只读骨架）：law / knowledge_spots / external_scopes。不写盘、不出网、不执行。"""
    op = str(op or "law")
    if op == "law":
        return {"ok": True, "readonly": True, "red_lines": list(RED_LINES),
                "gap_types": [{"key": k, "cn": GAP_CN[k]} for k in GAP_TYPES],
                "scopes": list(SCOPES), "log_ref": _DEFAULT.work_log_ref,
                "knowledge_spots": list(KNOWLEDGE_SPOTS)}
    if op == "knowledge_spots":
        return {"ok": True, "readonly": True, "spots": list(KNOWLEDGE_SPOTS),
                "note": "没有统一 KB：三处口径未收口（登记在册）"}
    if op == "external_scopes":
        return _DEFAULT.external_scopes()
    raise ValueError("未知 op %r（可用：law/knowledge_spots/external_scopes）" % (op,))


HONEST_BOUNDARY = (
    "元认知循环保证『自省、查证、提问、沉淀』四步可执行；"
    "它保证不了『永远不犯同一个错』——但它能保证同一个坑不会静默地再踩一次。"
)
