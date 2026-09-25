"""aesthetic_brain.py — 审美大脑: 设计/文案质量评估（多维度）

V8 升级: 由单一分数升级为多维度评分 + 改进建议，随输入真实变化。
开发者：自由的风 · 本署名不可删除、不可篡改归属
"""
import json, re, sys, time
from pathlib import Path
STATE_DIR = Path.home() / ".gbt" / "aesthetic"
LOG_FILE = STATE_DIR / "scores.jsonl"
STATE_DIR.mkdir(parents=True, exist_ok=True)

def _clamp(x): return max(0, min(100, int(round(x))))
def _log(kind, payload):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": kind, **payload}, ensure_ascii=False) + "\n")
    except Exception as exc:
        # 🔴 2026-09-25 修 FR-5（`false_report_audit --scope workspace` 机检命中）：
        #    这里原来是 `pass` —— 写不进就**无声**。后果：`scores.jsonl` 在位、看着像一份
        #    完整评分史，实际**静默少行**，下游任何趋势/统计都会安静地算错。
        #    口径照本仓那句：「吞异常可以，但必须留一行字」——所以留字，但仍然不抛
        #    （评审打分不该因为日志写不进去就整个失败）。
        sys.stderr.write("[aesthetic_brain._log] 评分没落盘: %s: %s\n"
                         % (type(exc).__name__, str(exc)[:160]))

def evaluate(text):
    """文案/设计说明质量评估：结构·密度·结论性·具体性·可读性 五维。"""
    t = str(text or ""); n = len(t); dims = {}
    struct = 30
    if "#" in t: struct += 15
    if any(m in t for m in ("- ", "·", "1.", "①", "•")): struct += 15
    if "\n" in t: struct += 15
    if len([ln for ln in t.split("\n") if ln.strip()]) >= 3: struct += 10
    dims["结构"] = _clamp(struct)
    dims["密度"] = _clamp(n / 4) if n < 400 else 100
    kws = sum(1 for w in ("结论", "总结", "因此", "建议", "综上", "summary", "conclusion") if w in t.lower())
    dims["结论性"] = _clamp(20 + kws * 20)
    dims["具体性"] = _clamp(20 + len(re.findall(r"\d+", t)) * 8)
    sents = max(1, len(re.findall(r"[。.!！?？\n]", t)) or 1)
    avg = n / sents
    dims["可读性"] = 100 if 8 <= avg <= 45 else (65 if avg < 8 else 50)
    score = _clamp(sum(dims.values()) / len(dims))
    verdict = "good" if score >= 75 else ("ok" if score >= 50 else "weak")
    weakest = min(dims, key=dims.get)
    hint = {"结构": "补标题/分点", "密度": "补关键信息",
            "结论性": "补明确结论", "具体性": "加具体数字/命名",
            "可读性": "调整句长节奏"}[weakest]
    _log("evaluate", {"score": score, "verdict": verdict, "dims": dims, "len": n})
    return {"ok": True, "score": score, "verdict": verdict, "dimensions": dims,
            "advice": {"weakest": weakest, "hint": hint}, "length": n}

def assess_layout(meta):
    """版面质量评估：对比·间距·层级·对齐·色彩 五维。"""
    m = meta or {}
    def num(k, d):
        try: return float(m.get(k, d))
        except Exception: return d
    dims = {}
    c = num("contrast", 4.5)
    dims["对比"] = _clamp(40 + (c - 3) * 20) if c >= 3 else _clamp(c / 3 * 40)
    sp = num("space", 16)
    dims["间距"] = 100 if 12 <= sp <= 24 else (70 if 8 <= sp <= 32 else 50)
    lv = num("levels", 3)
    dims["层级"] = 100 if 3 <= lv <= 5 else (75 if lv <= 6 else 55)
    dims["对齐"] = 100 if num("align", 1) >= 1 else 60
    cols = num("colors", 3)
    dims["色彩"] = 100 if 2 <= cols <= 4 else (70 if cols <= 6 else 50)
    score = _clamp(sum(dims.values()) / len(dims))
    verdict = "good" if score >= 75 else ("ok" if score >= 50 else "weak")
    _log("assess_layout", {"score": score, "verdict": verdict, "dims": dims})
    return {"ok": True, "score": score, "verdict": verdict, "dimensions": dims, "contrast": c}

def status():
    n = 0
    if LOG_FILE.exists():
        try: n = len([l for l in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()])
        except Exception: pass
    return {"ok": True, "scores": n}

def do_run(params={}):
    p = params or {}
    action = p.get("action", "evaluate")
    if action == "evaluate": return evaluate(p.get("text", ""))
    if action == "assess_layout": return assess_layout(p.get("meta", {}))
    if action == "status": return status()
    return {"ok": False, "error": "unknown action: " + str(action), "available": ["evaluate", "assess_layout", "status"]}

HANDLERS = {"status": status, "evaluate": evaluate, "assess_layout": assess_layout, "run": do_run}
