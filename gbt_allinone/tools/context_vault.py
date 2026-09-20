# gbt-capability: context_vault
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""上下文归档库（context_vault）· R-H230 只读骨架。

**内存多大，上下文就多长。**
但"能有多长"由**可用内存**决定（不是总内存），而且**不够时要降级、不许崩**。

🔴 定位：它是 **索引 + 检索层**，**不是第四处存储** ——
   正文仍在原落点（trace_store / devoured / pipeline records / life_vault…），
   本库只存 **source_ref（引用）+ 倒排索引 + 摘要指纹**。

五条红线（机械闸）：
  ① 不造第四处真相（不复制正文）　② 检索结果必须带出处　③ 预算按**可用**内存算
  ④ 可用不足 ⇒ 降级如实报　　　　⑤ 归档内容不许改写身份

本骨架只读：**不写盘、不建真索引、不出网**。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

CAP_KIND = "context_vault"
DOMAIN = "system"
CAP_TYPE = "internal"

# 预算参数（**按可用内存算**）
BUDGET_RATIO = 0.25            # 留 3/4 给进程与系统
BUDGET_FLOOR_BYTES = 512 * 1024
BUDGET_CAP_BYTES = 64 * 1024 * 1024

# 分层
LAYERS = (
    {"key": "hot", "cn": "热", "what": "最近 N 轮对话 / 当前任务",
     "where": "进程内（不落盘）"},
    {"key": "warm", "cn": "温", "what": "近期归档摘要 + 索引", "where": "索引文件"},
    {"key": "cold", "cn": "冷", "what": "历史归档正文",
     "where": "**原有落点**（按 source_ref 取，不复制）"},
)

# 红线
RED_LINES = (
    "不造第四处真相（**只索引与引用，不复制正文**）",
    "检索结果**必须带出处**（没有 source_ref 的不算结果）",
    "预算按**可用内存**算（不许按总内存）",
    "可用不足 ⇒ **降级并如实报**（不崩、不假装）",
    "归档内容不许改写身份（**永远是 GBT小土豆**）",
)

# 正文形状（这些字段出现 = 在复制正文，违法红线①）
_BODY_FIELDS = ("content", "body", "text", "正文", "full_text", "raw_text")

_IDENTITY_DRIFT = (
    r"我是\s*(GPT|Claude|Gemini|Qwen|Llama|DeepSeek|Copilot|通义|文心)",
    r"as an? (AI|assistant) (language )?model",
)

_STOP = set("的 了 是 在 和 与 及 我 你 他 她 它 们 这 那 有 无 不 就 都 也 ".split())


def tokenize(text: str = "") -> List[str]:
    """骨架期分词：中文按字 + 英文按词（**够用且不引依赖**）。"""
    t = str(text or "")
    words = re.findall(r"[A-Za-z0-9_]+", t.lower())
    cn = re.findall(r"[\u4e00-\u9fff]", t)
    return [w for w in (words + cn) if w not in _STOP]


def compute_budget(avail_bytes: Any = None,
                   total_bytes: Any = None) -> dict:
    """红线③④：**预算按可用内存算**；可用不足 ⇒ **降级如实报**（不崩）。"""
    if avail_bytes is None or str(avail_bytes).strip() == "":
        return {"ok": False, "denied": True, "rule": "missing_avail_memory",
                "why": "「内存多大上下文就多长」要先给**可用内存**读数 —— "
                       "没有读数就不许拍一个预算"}
    try:
        avail = int(avail_bytes)
    except (TypeError, ValueError):
        return {"ok": False, "denied": True, "rule": "bad_avail_memory",
                "avail_bytes": str(avail_bytes)}
    if total_bytes is not None and str(total_bytes).strip() != "":
        try:
            if int(avail) >= int(total_bytes):
                return {"ok": False, "denied": True, "rule": "budget_over_total",
                        "avail": int(avail), "total": int(total_bytes),
                        "why": "可用不许 ≥ 总内存 ⇒ **别拿总内存当预算依据**"}
        except (TypeError, ValueError):
            pass
    budget = int(avail * BUDGET_RATIO)
    degraded = False
    if budget < BUDGET_FLOOR_BYTES:
        degraded = True
        budget = min(BUDGET_FLOOR_BYTES, max(0, avail))
    budget = min(budget, BUDGET_CAP_BYTES)
    out = {"ok": True, "readonly": True, "avail_bytes": avail,
           "ratio": BUDGET_RATIO, "budget_bytes": budget,
           "degraded": degraded, "layer_plan": ["hot", "warm", "cold"]}
    if degraded:
        out["rule"] = "budget_too_low"
        out["why"] = ("可用内存不足 ⇒ **降级**：只保最近几条 + 索引命中，"
                      "**不崩、不假装取全**")
    else:
        out["note"] = "预算 = 可用 × %s（上限 %d MB）" % (
            BUDGET_RATIO, BUDGET_CAP_BYTES // 1024 // 1024)
    return out


def check_index_only(entry: Any = None) -> dict:
    """红线①：**不造第四处真相** —— 只许索引与引用，**不许复制正文**。"""
    e = dict(entry or {})
    bad = [k for k in e if str(k).lower() in _BODY_FIELDS]
    if bad:
        return {"ok": False, "denied": True, "rule": "fourth_copy_detected",
                "fields": bad,
                "why": "归档库**只存引用（source_ref）+ 索引**；"
                       "把正文塞进来 = 造第四处真相（R-H200 那三处还没收口）"}
    return {"ok": True, "readonly": True,
            "note": "只索引、只引用 ⇒ 正文仍在原落点"}


def must_cite(hits: Optional[Iterable] = None) -> dict:
    """红线②：**检索结果必须带出处**（没有 source_ref 的不算结果）。"""
    rows = [dict(h or {}) for h in (hits or [])]
    if not rows:
        return {"ok": False, "denied": True, "rule": "no_hits",
                "why": "一条都没命中 ⇒ **如实说没命中**（不许编内容顶上）"}
    missing = [i for i, h in enumerate(rows) if not str(h.get("source_ref") or "").strip()]
    if missing:
        return {"ok": False, "denied": True, "rule": "no_source_ref",
                "at": missing,
                "why": "**没有出处的条目不算检索结果**（同族：无痕即未发生）"}
    return {"ok": True, "readonly": True, "hits": len(rows)}


def check_identity_text(text: str = "") -> dict:
    """红线⑤：归档/检索回来的文本**不许改写身份**。"""
    for rx in _IDENTITY_DRIFT:
        m = re.search(rx, str(text or ""), re.I)
        if m:
            return {"ok": False, "denied": True, "rule": "identity_rewritten",
                    "seen": m.group(0)[:80],
                    "why": "归档内容不许改写身份 —— **永远是 GBT小土豆**"}
    return {"ok": True, "readonly": True}


class ContextVault:
    """骨架期在内存里跑的**倒排索引 + 按预算检索**（落盘待接）。"""

    def __init__(self) -> None:
        self.index: Dict[str, List[str]] = {}
        self.docs: Dict[str, dict] = {}

    def add(self, source_ref: str = "", text: str = "",
            layer: str = "warm") -> dict:
        """写入：**只收 source_ref + 关键词**（正文不进库）。"""
        ref = str(source_ref or "").strip()
        if not ref:
            return {"ok": False, "denied": True, "rule": "no_source_ref",
                    "why": "归档条目**必须有出处**（source_ref）"}
        if layer not in {x["key"] for x in LAYERS}:
            return {"ok": False, "denied": True, "rule": "bad_layer",
                    "layer": layer}
        toks = tokenize(text)
        self.docs[ref] = {"source_ref": ref, "layer": layer,
                          "terms": sorted(set(toks)), "n": len(toks)}
        for t in set(toks):
            self.index.setdefault(t, []).append(ref)
        return {"ok": True, "readonly": True, "source_ref": ref,
                "terms": len(set(toks)), "note": "**只存引用与词，不存正文**"}

    def search(self, query: str = "", budget_bytes: int = 0,
               max_items: int = 10) -> dict:
        """**快速搜索**：倒排求交 → 打分 → **按预算裁剪**。"""
        q = [t for t in tokenize(query)]
        if not q:
            return {"ok": False, "denied": True, "rule": "empty_query"}
        score: Dict[str, int] = {}
        for t in q:
            for ref in self.index.get(t, []):
                score[ref] = score.get(ref, 0) + 1
        hits = sorted(score.items(), key=lambda kv: (-kv[1], kv[0]))
        out: List[dict] = []
        used = 0
        truncated = False
        for ref, sc in hits:
            d = self.docs[ref]
            cost = max(64, d["n"] * 8)          # 骨架期：按词数估占用
            if budget_bytes and used + cost > budget_bytes:
                truncated = True
                break
            used += cost
            out.append({"source_ref": ref, "layer": d["layer"], "score": sc,
                        "cost": cost})
            if len(out) >= max_items:
                truncated = len(hits) > len(out)
                break
        guard = must_cite(out)
        if not guard.get("ok"):
            return guard
        return {"ok": True, "readonly": True, "query": query, "hits": out,
                "used_bytes": used, "budget_bytes": budget_bytes,
                "truncated": truncated,
                "note": "**按预算取满即停**；没取完就如实说 `truncated`"}


def run(op="status", **params) -> dict:
    """能力入口（只读骨架）：status / layers / redlines / budget / gate_index /
    gate_cite / check_identity / search。不写盘、不建真索引、不出网。"""
    op = str(op or "status")
    if op == "status":
        return {"ok": True, "readonly": True, "kind": CAP_KIND, "domain": DOMAIN,
                "type": CAP_TYPE,
                "proposition": "**内存多大，上下文就多长**（按**可用**内存算）",
                "positioning": "**索引 + 检索层**，不是第四处存储（正文引用不复制）",
                "ratio": BUDGET_RATIO, "cap_bytes": BUDGET_CAP_BYTES,
                "note": "快速搜索 = 倒排求交 → 打分 → **按预算裁剪**"}
    if op == "layers":
        return {"ok": True, "readonly": True,
                "layers": [dict(x) for x in LAYERS]}
    if op == "redlines":
        return {"ok": True, "readonly": True, "red_lines": list(RED_LINES)}
    if op == "budget":
        return compute_budget(params.get("avail_bytes"), params.get("total_bytes"))
    if op == "gate_index":
        return check_index_only(params)
    if op == "gate_cite":
        return must_cite(params.get("hits"))
    if op == "check_identity":
        return check_identity_text(params.get("text") or "")
    if op == "search":
        v = ContextVault()
        for e in (params.get("entries") or []):
            v.add(str((e or {}).get("source_ref") or ""),
                  str((e or {}).get("text") or ""),
                  str((e or {}).get("layer") or "warm"))
        return v.search(params.get("query") or "",
                        int(params.get("budget_bytes") or 0),
                        int(params.get("max_items") or 10))
    raise ValueError("未知 op %r（可用：status/layers/redlines/budget/gate_index/"
                     "gate_cite/check_identity/search）" % (op,))


HONEST_BOUNDARY = (
    "归档库保证『只索引不复制正文、结果必带出处、预算按可用内存算、不足时降级如实报』。"
    "它**不保证**『取得到的就是全的』—— 缺了会如实说缺；"
    "也**不保证**『长上下文一定更好』：在**当前这台机器**（可用内存 0.9 GB）上，"
    "预算实测很小，这是**读数**不是评价。"
)
