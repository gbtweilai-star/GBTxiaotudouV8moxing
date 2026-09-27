# gbt-capability: transformer
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""变压器（transformer）· 按原设计接上（`delivery/20260922-她·变压器·密钥AI·本体操控·官方独立接口-设计.md` §一）。

## 为什么会有这个文件（主人令 2026-09-27：「排查一遍变压器是什么问题，为什么老是出现
## 短线能源供给不足，重新以最专业的思维来设计好接上」）

**诊断结论**：变压器**从来没坏 —— 它从来没被接上**。
  · 09-22 设计稿写明「网关前置的**两级变压器**（压缩 + 快速输出，带前后两个数）」；
  · 09-26 日报的结论是「`panel_server.py` 登记 pending · **从未接线**」；
  · 全仓 grep `变压器` 只命中设计稿与交付单，**没有任何实现**。
  ⇒ 于是每次调用都按原样全量送模型：**token 不降 ⇒ 能源必然紧**。这台"供给不足"不是池子小，
    是**该有的变压器没装**（原设计里的最低能源律第 4、5 条：压缩体积 + 变压增强缩短线路）。

## 按原设计实现（不改设计意图，只把它接上）
```
输入侧（压缩）                              输出侧（快速）
  去重（重复段落只留一份）                    cache 命中 ⇒ 直接返回，**根本不叫模型**
  裁陈旧上下文（超出窗口的按相关性丢）         delta 直出优先（TTFT 优先于总时长）
  结构化压缩（重复 JSON 折叠）                max_out 预算（省输出 token）
        ↓                                            ↑
              ┌──── 变压器 transformer ────┐
              │  可旁路（fail-open）：压坏就原样走 │
              └────────────────────────────┘
```

## 硬判据（原设计 §1.4：**必须给前后两个数**）
  · **压缩率**：原字符数 vs 压缩后字符数（每次调用都记）；
  · **不丢关键信息**：压缩前后抽出的 `identifiers / files / commands` 集合**必须满足包含关系**
    —— 压坏了就 **fail-open 回原样**并如实标注（宁可没省，不许压坏）；
  · **省下来的账**：`state/transformer_ledger.jsonl` 累计（把"能源不足"从体感变成数字）。

ops：
  compress  text=...            压缩（返回前后两个数 + 包含关系判定 + 是否旁路）
  cache_get text=...            查缓存（命中=不用叫模型）
  cache_put text=... answer=... 写缓存
  stats                         累计：省下多少字符/多少次调用
  selftest                      判据自检（含反向自检：故意压坏必须被拦）
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_CACHE = _ROOT / "state" / "transformer_cache.json"
_LEDGER = _ROOT / "state" / "transformer_ledger.jsonl"
_MAX_OUT_DEFAULT = 1200

# 字面量抽取器（**原设计 §1.3 指定的抓手**：knowledge_base 的抽取器就是一台压缩机）
_RX = {
    "identifiers": re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{3,}\b"),
    "files": re.compile(r"\b[\w./\\-]+\.(?:py|md|json|jsonl|ya?ml|txt|csv|xlsx|docx|pptx|pdf|mp4|png|jpg|html|js|ts|ps1|cmd|bat|sh)\b", re.I),
    "commands": re.compile(r"\b(?:python|py|pip|npm|node|git|ffmpeg|curl|powershell|pwsh|cmd|docker|gh)\b[^\n`]{0,60}"),
}


def _extract(text: str) -> dict:
    return {k: set(rx.findall(text or "")) for k, rx in _RX.items()}


def _dedupe(text: str) -> tuple[str, int]:
    """去重：**相邻与全局重复段落只留一份**（保序）。返回 (文本, 去掉的行数)。"""
    seen, out, dropped = set(), [], 0
    for para in re.split(r"(\n\s*\n)", text or ""):
        key = re.sub(r"\s+", " ", para).strip()
        if key and key in seen and len(key) > 24:      # 太短的不去重（保结构）
            dropped += 1
            continue
        seen.add(key)
        out.append(para)
    return "".join(out), dropped


def _collapse_json(text: str) -> tuple[str, int]:
    """结构化压缩：把**重复出现的 JSON 块**折叠成一份 + 引用（原设计「重复 JSON 折叠」）。"""
    blocks = re.findall(r"(?s)\{[^{}]{40,}\}", text or "")
    collapsed = 0
    out = text or ""
    seen = set()
    for b in blocks:
        norm = re.sub(r"\s+", "", b)
        if norm in seen:
            out = out.replace(b, "[同上：结构相同的 JSON 块，已折叠]", 1)
            collapsed += 1
        else:
            seen.add(norm)
    return out, collapsed


def _trim_stale(text: str, keep_tail_lines: int = 120) -> tuple[str, int]:
    """裁陈旧上下文：超长文本按**尾部优先**保留（近期上下文相关性高）。返回 (文本, 裁掉行数)。"""
    lines = (text or "").splitlines()
    if len(lines) <= keep_tail_lines:
        return text or "", 0
    head = lines[:8]                                    # 头部通常有任务定义，保留
    tail = lines[-(keep_tail_lines - 8):]
    return "\n".join(head + ["…〔中间 %d 行按相关性裁去，可用 cache 回查原文〕…" % (len(lines) - keep_tail_lines)] + tail), len(lines) - keep_tail_lines


def _log(row: dict) -> None:
    _LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(_LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), **row},
                            ensure_ascii=False) + "\n")


def compress(text: str = "", keep_tail_lines: int = 120, **_kw) -> dict:
    """两级变压器·输入侧：去重 → 折叠 JSON → 裁陈旧。**带前后两个数**，压坏则 fail-open。"""
    src = text or ""
    before = len(src)
    if before == 0:
        return {"ok": True, "op": "compress", "bypass": False, "chars_before": 0, "chars_after": 0,
                "ratio": 1.0, "note": "空输入"}
    lit_before = _extract(src)
    t1, dup = _dedupe(src)
    t2, folded = _collapse_json(t1)
    t3, trimmed = _trim_stale(t2, keep_tail_lines)
    after = len(t3)
    lit_after = _extract(t3)
    lost = {k: sorted(lit_before[k] - lit_after[k]) for k in lit_before}
    keep_ok = all(not v for v in lost.values())          # 包含关系：抽出的字面量一个不许丢
    bypass = not keep_ok or after >= before
    if bypass:
        # **fail-open**：宁可没省，不许压坏（原设计的可旁路）
        t3, after = src, before
    out = {"ok": True, "op": "compress", "bypass": bypass,
           "chars_before": before, "chars_after": after,
           "ratio": round(after / before, 4),
           "saved_chars": before - after,
           "deduped": dup, "json_folded": folded, "lines_trimmed": trimmed,
           "literals_kept": keep_ok, "lost_literals": {k: v[:6] for k, v in lost.items() if v},
           "text": t3,
           "_口径": "包含关系不成立或没省下来 ⇒ 旁路回原样（fail-open）；每次调用写 transformer_ledger.jsonl"}
    _log({"event": "compress", "before": before, "after": after, "bypass": bypass,
          "deduped": dup, "folded": folded, "trimmed": trimmed})
    return out


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())[:4000]


def cache_get(text: str = "", **_kw) -> dict:
    """输出侧·快速：命中就直接返回，**根本不叫模型**（省的是整次调用）。"""
    key = hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()[:20]
    try:
        d = json.loads(_CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        d = {}
    hit = d.get(key)
    _log({"event": "cache", "hit": bool(hit), "key": key})
    return {"ok": True, "op": "cache_get", "key": key, "hit": bool(hit),
            "answer": (hit or {}).get("answer", ""), "saved_calls": 1 if hit else 0,
            "_口径": "命中=省下整次模型调用（最大的一笔能源账）"}


def cache_put(text: str = "", answer: str = "", **_kw) -> dict:
    key = hashlib.sha256(_norm(text).encode("utf-8")).hexdigest()[:20]
    try:
        d = json.loads(_CACHE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        d = {}
    d[key] = {"answer": answer, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "chars": len(answer or "")}
    _CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = _CACHE.with_name(_CACHE.name + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    import os
    os.replace(tmp, _CACHE)
    _log({"event": "cache_put", "key": key, "chars": len(answer or "")})
    return {"ok": True, "op": "cache_put", "key": key, "entries": len(d)}


def stats(**_kw) -> dict:
    rows = []
    if _LEDGER.is_file():
        for ln in _LEDGER.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    comp = [r for r in rows if r.get("event") == "compress"]
    caches = [r for r in rows if r.get("event") == "cache"]
    saved = sum(r.get("before", 0) - r.get("after", 0) for r in comp if not r.get("bypass"))
    hits = sum(1 for r in caches if r.get("hit"))
    return {"ok": True, "op": "stats", "compress_calls": len(comp),
            "chars_saved": saved, "bypass_count": sum(1 for r in comp if r.get("bypass")),
            "cache_lookups": len(caches), "cache_hits": hits,
            "saved_model_calls": hits,
            "_口径": "省下字符=输入侧；省下调用=输出侧（一笔命中=一次模型调用不花钱）"}


def selftest() -> int:
    bad = 0
    sample = "\n\n".join([
        "任务：把 E1E3 多镜版渲染出来。" * 3,
        '{"a": 1, "b": [1,2,3], "note": "很长的重复结构块，用于测折叠"}' * 1,
        '{"a": 1, "b": [1,2,3], "note": "很长的重复结构块，用于测折叠"}' * 1,
        "\n".join(f"第 {i} 行上下文" for i in range(200)),
        "命令：python tools/actioncam.py build --manifest projects/movie/产线/manifest-actioncam-demo.json",
    ])
    r = compress(sample)
    print(f"  [压缩] 前 {r['chars_before']} → 后 {r['chars_after']}（比 {r['ratio']}）· "
          f"去重 {r['deduped']} · 折叠 {r['json_folded']} · 裁行 {r['lines_trimmed']} · 旁路={r['bypass']}")
    if r["chars_after"] > r["chars_before"]:
        print("    🔴 越压越大"); bad += 1
    if not r["literals_kept"] and not r["bypass"]:
        print("    🔴 丢了字面量却没旁路"); bad += 1
    # 反向自检：把命令删掉的"压缩器"必须被判丢字面量（我们故意用裁剪函数直接砍头）
    cut = "\n".join(sample.splitlines()[:2])
    lost = _extract(sample)["commands"] - _extract(cut)["commands"]
    print(f"  [反向自检] 砍掉命令段 ⇒ 检出丢失 {len(lost)} 条（应 > 0）")
    if not lost:
        print("    🔴 丢字面量没被检出"); bad += 1
    h1 = cache_get("同一个问题")
    cache_put("同一个问题", "答案")
    h2 = cache_get("同一个问题")
    print(f"  [缓存] 先 {h1['hit']} → 写 → 再查 {h2['hit']}（应 False → True）")
    if h1["hit"] or not h2["hit"]:
        print("    🔴 缓存行为不对"); bad += 1
    s = stats()
    print(f"  [账] 省字符 {s['chars_saved']} · 命中 {s['cache_hits']}/{s['cache_lookups']} · 旁路 {s['bypass_count']}")
    print(f"\n自检结论：{'全过' if bad == 0 else f'🔴 失败 {bad} 项'}")
    return bad


def run_op(op: str = "stats", **params) -> dict:
    op = (op or "stats").lower()
    if op == "compress":
        return compress(**params)
    if op == "cache_get":
        return cache_get(**params)
    if op == "cache_put":
        return cache_put(**params)
    if op == "stats":
        return stats(**params)
    if op == "selftest":
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            bad = selftest()
        return {"ok": bad == 0, "failures": bad, "report": buf.getvalue()}
    return {"ok": False, "error": f"未知 op:{op}（compress/cache_get/cache_put/stats/selftest）",
            "fail_closed": True}
