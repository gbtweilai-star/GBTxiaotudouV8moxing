# -*- coding: utf-8 -*-
"""经镜像门禁发布设计能力修复（受信通道），并验证是否持久。"""
import sys, io, json, time, importlib.util
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r'C:\Users\ADMIN\Desktop\GBT小土豆')

def rd(p):
    return Path(p).read_bytes().decode('utf-8').replace('\r\n', '\n').replace('\ufeff', '')

def load_mod(name, rel):
    spec = importlib.util.spec_from_file_location(name, str(ROOT / rel))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

# ── 目标 1: brain/aesthetic_brain.py（多维评分器）──
ab_new = rd(ROOT / 'brain' / 'aesthetic_brain.py')  # 当前(旧)内容，用于对比
NEW_AB = '''"""aesthetic_brain.py \u2014 \u5ba1\u7f8e\u5927\u8111: \u8bbe\u8ba1/\u6587\u6848\u8d28\u91cf\u8bc4\u4f30\uff08\u591a\u7ef4\u5ea6\uff09

V8 \u5347\u7ea7: \u7531\u5355\u4e00\u5206\u6570\u5347\u7ea7\u4e3a\u591a\u7ef4\u5ea6\u8bc4\u5206 + \u6539\u8fdb\u5efa\u8bae\uff0c\u968f\u8f93\u5165\u771f\u5b9e\u53d8\u5316\u3002
\u5f00\u53d1\u8005\uff1a\u81ea\u7531\u7684\u98ce \u00b7 \u672c\u7f72\u540d\u4e0d\u53ef\u5220\u9664\u3001\u4e0d\u53ef\u7be1\u6539\u5f52\u5c5e
"""
import json, re, time
from pathlib import Path
STATE_DIR = Path.home() / ".gbt" / "aesthetic"
LOG_FILE = STATE_DIR / "scores.jsonl"
STATE_DIR.mkdir(parents=True, exist_ok=True)

def _clamp(x): return max(0, min(100, int(round(x))))
def _log(kind, payload):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": kind, **payload}, ensure_ascii=False) + "\\n")
    except Exception:
        pass

def evaluate(text):
    """\u6587\u6848/\u8bbe\u8ba1\u8bf4\u660e\u8d28\u91cf\u8bc4\u4f30\uff1a\u7ed3\u6784\u00b7\u5bc6\u5ea6\u00b7\u7ed3\u8bba\u6027\u00b7\u5177\u4f53\u6027\u00b7\u53ef\u8bfb\u6027 \u4e94\u7ef4\u3002"""
    t = str(text or ""); n = len(t); dims = {}
    struct = 30
    if "#" in t: struct += 15
    if any(m in t for m in ("- ", "\u00b7", "1.", "\u2460", "\u2022")): struct += 15
    if "\\n" in t: struct += 15
    if len([ln for ln in t.split("\\n") if ln.strip()]) >= 3: struct += 10
    dims["\u7ed3\u6784"] = _clamp(struct)
    dims["\u5bc6\u5ea6"] = _clamp(n / 4) if n < 400 else 100
    kws = sum(1 for w in ("\u7ed3\u8bba", "\u603b\u7ed3", "\u56e0\u6b64", "\u5efa\u8bae", "\u7efc\u4e0a", "summary", "conclusion") if w in t.lower())
    dims["\u7ed3\u8bba\u6027"] = _clamp(20 + kws * 20)
    dims["\u5177\u4f53\u6027"] = _clamp(20 + len(re.findall(r"\\d+", t)) * 8)
    sents = max(1, len(re.findall(r"[\u3002.!\uff01?\uff1f\\n]", t)) or 1)
    avg = n / sents
    dims["\u53ef\u8bfb\u6027"] = 100 if 8 <= avg <= 45 else (65 if avg < 8 else 50)
    score = _clamp(sum(dims.values()) / len(dims))
    verdict = "good" if score >= 75 else ("ok" if score >= 50 else "weak")
    weakest = min(dims, key=dims.get)
    hint = {"\u7ed3\u6784": "\u8865\u6807\u9898/\u5206\u70b9", "\u5bc6\u5ea6": "\u8865\u5173\u952e\u4fe1\u606f",
            "\u7ed3\u8bba\u6027": "\u8865\u660e\u786e\u7ed3\u8bba", "\u5177\u4f53\u6027": "\u52a0\u5177\u4f53\u6570\u5b57/\u547d\u540d",
            "\u53ef\u8bfb\u6027": "\u8c03\u6574\u53e5\u957f\u8282\u594f"}[weakest]
    _log("evaluate", {"score": score, "verdict": verdict, "dims": dims, "len": n})
    return {"ok": True, "score": score, "verdict": verdict, "dimensions": dims,
            "advice": {"weakest": weakest, "hint": hint}, "length": n}

def assess_layout(meta):
    """\u7248\u9762\u8d28\u91cf\u8bc4\u4f30\uff1a\u5bf9\u6bd4\u00b7\u95f4\u8ddd\u00b7\u5c42\u7ea7\u00b7\u5bf9\u9f50\u00b7\u8272\u5f69 \u4e94\u7ef4\u3002"""
    m = meta or {}
    def num(k, d):
        try: return float(m.get(k, d))
        except Exception: return d
    dims = {}
    c = num("contrast", 4.5)
    dims["\u5bf9\u6bd4"] = _clamp(40 + (c - 3) * 20) if c >= 3 else _clamp(c / 3 * 40)
    sp = num("space", 16)
    dims["\u95f4\u8ddd"] = 100 if 12 <= sp <= 24 else (70 if 8 <= sp <= 32 else 50)
    lv = num("levels", 3)
    dims["\u5c42\u7ea7"] = 100 if 3 <= lv <= 5 else (75 if lv <= 6 else 55)
    dims["\u5bf9\u9f50"] = 100 if num("align", 1) >= 1 else 60
    cols = num("colors", 3)
    dims["\u8272\u5f69"] = 100 if 2 <= cols <= 4 else (70 if cols <= 6 else 50)
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
'''

mg = load_mod('_mg', r'brain\mirror_gate.py')
r = mg.authorize('brain/aesthetic_brain.py', NEW_AB, context='V8 设计能力修复')
print('authorize aesthetic_brain:', json.dumps({k: r.get(k) for k in ('ok', 'written', 'hash', 'error')}, ensure_ascii=False))
if r.get('error'):
    print('  validate:', json.dumps(r.get('validate', {}), ensure_ascii=False)[:300])
print('gatekeeper status:', json.dumps(mg.status(), ensure_ascii=False))
