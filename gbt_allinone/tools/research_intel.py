# gbt-capability: research_intel
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""调研 AI · 三个情报组只读骨架（research_intel）· R-H175。

**一句话总纲**：调研 AI 不是"找灵感"，是 **"画禁区 + 找流量 + 定方向"**——
它本质上是**情报部门**（先于发布、决定该做什么的那个部门）。

结构：**三组 × 六维**（缺一不可）
  组：music_intel（AI音乐部）· video_intel（AI短视频部）· film_intel（AI电影部）
  维：合规红线 · 过审规则 · 流量集中 · 用户画像 · 竞品动态 · **禁区清单**

三条红线（**做成机械闸，不是写在注释里**）
  1. **情报必须可追溯**：没有 `evidence` ⇒ 一律 `status="待核实"`、`usable_for_decision=False`；
  2. **禁区清单优先于流量趋势**：`gate()` 只要见到禁区命中 ⇒ `hold`，**哪怕趋势条数再多**；
  3. **情报是输入，不是指令**：`gate()` 只给判断，**不执行**；输出里明写
     `is_instruction=False` 且 `generator_still_has_veto=True`。

诚实边界：本模块**不联网、不抓数、不写盘** ⇒ 今天只有"该收什么、怎么记账、什么不许进决策"
的结构；第 ③ 步抓数要过 `auth_gate`（出网授权），**排在飞书之后**。
"""
from __future__ import annotations

import time
import hashlib
import json
import math

GROUPS = {
    "music_intel": {"cn": "AI音乐部", "code": "MUSIC",
                    "scope": "平台合规（Spotify/Apple Music/抖音音乐/TikTok）· 流派趋势 · 用户偏好 · 版权雷区"},
    "video_intel": {"cn": "AI短视频部", "code": "VIDEO",
                    "scope": "平台合规（抖音/快手/视频号/TikTok/YouTube Shorts）· 流量机制 · 时长/标签/封面规则"},
    "film_intel": {"cn": "AI电影部", "code": "FILM",
                   "scope": "平台合规（B站/YouTube/Netflix 长视频）· 内容分级 · 版权链 · 发行窗口"},
}

DIMENSIONS = {
    "compliance_redlines": {"cn": "合规红线", "artifact": "compliance_redlines.json"},
    "approval_rules": {"cn": "过审规则", "artifact": "approval_rules.md"},
    "traffic_trend": {"cn": "流量集中", "artifact": "traffic_trend.json"},
    # R-H189 · 贯通②：用户画像**必须带"听歌/看片场景"**（场景锚定接管）
    "audience_profile": {"cn": "用户画像", "artifact": "audience_profile.json",
                         "must_scene": True},
    "competitor_watch": {"cn": "竞品动态", "artifact": "competitor_watch.json"},
    "forbidden_lists": {"cn": "禁区清单", "artifact": "forbidden_lists.md", "absolute": True},
}

CONFIDENCE_FLOOR = 0.6          # 置信度低于此值 ⇒ 不许进决策（只进台账）
IMPACTS = ("low", "medium", "high")

RED_LINES = (
    "情报必须可追溯：没有出处的『听说』不许进台账（没 evidence ⇒ 待核实）",
    "禁区清单优先于流量趋势：哪怕题材再火，在禁区里就不做",
    "情报是输入，不是指令：生成端仍有过目权，情报不许自动执行",
)


def _now(now=None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S") if now is None else str(now)


def coverage(group: str | None = None) -> dict:
    """三组 × 六维 的覆盖矩阵：**缺哪一格，一眼看得见**。"""
    groups = [group] if group else list(GROUPS)
    for g in groups:
        if g not in GROUPS:
            raise ValueError("未知情报组 %r（可用：%s）" % (g, "/".join(GROUPS)))
    rows = []
    for g in groups:
        for dim, meta in DIMENSIONS.items():
            rows.append({
                "group": g, "department": GROUPS[g]["cn"],
                "dimension": dim, "cn": meta["cn"], "artifact": meta["artifact"],
                "absolute": bool(meta.get("absolute")),
                "filled": False,           # 骨架期一律未填（不许假装有情报）
                "status": "待核实",
            })
    return {
        "ok": True, "readonly": True,
        "groups": [{"group": g, "cn": GROUPS[g]["cn"], "code": GROUPS[g]["code"],
                    "scope": GROUPS[g]["scope"]} for g in groups],
        "dimensions": [{"dimension": d, "cn": m["cn"], "artifact": m["artifact"],
                        "absolute": bool(m.get("absolute"))} for d, m in DIMENSIONS.items()],
        "cells": rows, "cells_total": len(rows),
        "filled": 0, "unfilled": len(rows),
        "confidence_floor": CONFIDENCE_FLOOR,
        "note": "骨架期：结构在、情报不在 —— 所有格子一律『待核实』，不许把结构读成情报",
    }


def make_intel(department: str, dimension: str, finding: str, evidence: str = "",
               confidence: float = 0.0, impact: str = "low",
               action_required: str = "", intel_id: str = "", now=None) -> dict:
    """造一条**台账记录**并当场校验（不落盘）。

    三条记账纪律机械化的地方：没出处 ⇒ 待核实；置信度低 ⇒ 不进决策；`verified` 恒为 False
    （**自己不能给自己标已核实**，升级要另一个 checker）。
    """
    if department not in GROUPS:
        raise ValueError("未知部门 %r（可用：%s）" % (department, "/".join(GROUPS)))
    if dimension not in DIMENSIONS:
        raise ValueError("未知维度 %r（可用：%s）" % (dimension, "/".join(DIMENSIONS)))
    if not str(finding or "").strip():
        raise ValueError("finding 不能为空：情报部门不许记空条目")
    # 贯通②：用户画像维度必须说清"场景"（引用场景锚定的口径，不另立标准）
    if DIMENSIONS[dimension].get("must_scene"):
        blob = str(finding) + str(action_required)
        if "场景" not in blob:
            return {"ok": False, "denied": True, "rule": "scene_required",
                    "why": "用户画像必须带『听歌/看片场景』（贯通场景锚定）：谁在什么情况下点开"}
    if impact not in IMPACTS:
        raise ValueError("未知 impact %r（可用：%s）" % (impact, "/".join(IMPACTS)))
    try:
        conf = float(confidence)
    except (TypeError, ValueError):
        conf = 0.0
    conf = 0.0 if not math.isfinite(conf) or conf < 0 else (1.0 if conf > 1 else conf)
    has_evidence = bool(str(evidence or "").strip())
    low_conf = conf < CONFIDENCE_FLOOR
    if not has_evidence:
        status, usable = "待核实", False
    elif low_conf:
        status, usable = "低置信", False
    else:
        status, usable = "可用", True
    return {
        "intel_id": intel_id or ("%s-%s-XXX" % (GROUPS[department]["code"], _now(now)[:10])),
        "department": department,
        "department_cn": GROUPS[department]["cn"],
        "dimension": dimension,
        "dimension_cn": DIMENSIONS[dimension]["cn"],
        "finding": str(finding)[:500],
        "evidence": str(evidence or "")[:500],
        "confidence": conf,
        "impact": impact,
        "action_required": str(action_required or "")[:300],
        "status": status,
        "usable_for_decision": usable,
        "verified": False,              # 🔴 恒为 False：升级要另一个 checker，自己不能标
        "recorded_at": _now(now),
        "readonly": True,
    }


def gate(rows) -> dict:
    """决策闸（红线 2 的机械形态）：**禁区优先于流量**；情报只是输入，不是指令。"""
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    forbidden = [r for r in rows if r.get("dimension") == "forbidden_lists"]
    trends = [r for r in rows if r.get("dimension") == "traffic_trend"]
    usable = [r for r in rows if r.get("usable_for_decision")]
    base = {"ok": True, "readonly": True, "is_instruction": False,
            "generator_still_has_veto": True, "red_lines": list(RED_LINES)}
    if forbidden:
        return {**base, "decision": "hold",
                "reason": "禁区命中：哪怕题材再火，在禁区里就不做（红线 2）",
                "blocked_by": [r.get("finding") for r in forbidden],
                "trend_ignored": len(trends)}
    if not usable:
        return {**base, "decision": "ask_human",
                "reason": "没有可用情报（全部待核实 / 低置信）⇒ 先问人，不硬猜"}
    return {**base, "decision": "proceed",
            "reason": "无禁区命中，且有可用情报（仍需人过目）",
            "based_on": [r.get("finding") for r in usable]}


def evidence_report(question, sources, claims) -> dict:
    """核验调用方提供的文本快照及引用；不声明已抓取来源或证明结论真实。"""
    errors = []
    if not isinstance(question, str) or not question.strip():
        errors.append("question_required")
    if not isinstance(sources, list) or not sources or len(sources) > 100:
        return {"ok": False, "errors": ["sources_required_or_limit_exceeded"]}
    if not isinstance(claims, list) or not claims or len(claims) > 500:
        return {"ok": False, "errors": ["claims_required_or_limit_exceeded"]}
    indexed = {}
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"source:{index}:invalid")
            continue
        source_id, origin, content = (source.get(key) for key in ("id", "origin", "content"))
        if not all(isinstance(value, str) and value.strip()
                   for value in (source_id, origin, content)):
            errors.append(f"source:{index}:missing_fields")
            continue
        if source_id in indexed:
            errors.append(f"source:{index}:duplicate_id")
            continue
        if len(content) > 1_000_000:
            errors.append(f"source:{index}:too_large")
            continue
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        if source.get("sha256") is not None and source["sha256"] != digest:
            errors.append(f"source:{index}:hash_mismatch")
            continue
        indexed[source_id] = {"id": source_id, "origin": origin,
                              "content": content, "sha256": digest}
    bound = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"claim:{index}:invalid")
            continue
        text, quote, source_id = (claim.get(key) for key in ("text", "quote", "source_id"))
        if not all(isinstance(value, str) and value.strip()
                   for value in (text, quote, source_id)):
            errors.append(f"claim:{index}:missing_fields")
            continue
        source = indexed.get(source_id)
        if source is None or quote not in source["content"]:
            errors.append(f"claim:{index}:quote_not_found")
            continue
        line = source["content"][:source["content"].index(quote)].count("\n") + 1
        bound.append({"text": text, "quote": quote, "source_id": source_id,
                      "line": line, "source_sha256": source["sha256"]})
    if errors:
        return {"ok": False, "readonly": True, "errors": errors,
                "status": "blocked", "report": None}
    manifest = [{key: value for key, value in source.items() if key != "content"}
                for source in indexed.values()]
    payload = {"question": question.strip(), "sources": manifest, "claims": bound}
    report_id = hashlib.sha256(json.dumps(payload, ensure_ascii=False,
                                          sort_keys=True).encode("utf-8")).hexdigest()
    return {"ok": True, "readonly": True, "report_id": report_id,
            "status": "source_bound_pending_review", "report": payload,
            "validation_scope": "supplied_text_hash_and_exact_quote",
            "source_fetched": False, "verified": False,
            "is_instruction": False, "usable_for_decision": False,
            "limitations": ["来源内容由调用方提供，尚未核实来源真实性",
                            "原文包含引用，不等于原文支持结论；仍需独立复核"]}


def run(op="coverage", group=None, **params) -> dict:
    """能力入口（只读）：coverage / group / redlines。**不联网、不写盘、不执行。**"""
    op = str(op or "coverage")
    if op == "coverage":
        return coverage(group)
    if op == "group":
        if not group:
            raise ValueError("group 需要 group（%s）" % "/".join(GROUPS))
        return coverage(group)
    if op == "redlines":
        return {"ok": True, "readonly": True, "red_lines": list(RED_LINES),
                "confidence_floor": CONFIDENCE_FLOOR,
                "groups": list(GROUPS), "dimensions": list(DIMENSIONS)}
    if op == "gate":
        return gate(params.get("rows") or [])
    if op == "report":
        return evidence_report(params.get("question"), params.get("sources"),
                               params.get("claims"))
    if op == "scene_vocab":
        # 贯通②的可见面：情报组能直接查"场景锚定的 8 大类"（真引用那一份）
        from . import scene_anchor
        return {"ok": True, "readonly": True, "from": "tools.scene_anchor",
                "classes": list(scene_anchor.SCENE_CLASSES),
                "note": "用户画像维度必须落到这些场景里（谁在什么情况下点开）"}
    raise ValueError("未知 op %r（可用：coverage/group/redlines/gate/report/scene_vocab）" % (op,))


HONEST_BOUNDARY = (
    "骨架只保证『该收哪六维、怎么记账、什么不许进决策』是清楚的。"
    "它不保证『情报是对的』—— 那要靠出网取证 + 独立复核。"
)
