# -*- coding: utf-8 -*-
"""根治：让平台"万能插设计能力"真正可用（4 处，带备份）。

1) gbt_cap_bridge.py —— 动作路由根因：do_{action} 精确匹配优先 + 把 action 并入 params
   （旧实现 do_run 吞掉所有 action 且收不到动作名 -> 评分器/路由形同占位）
2) caps/design_brain/run.py —— do_aesthetic 随输入语义自动匹配风格；补 do_run 分发
3) brain/aesthetic_brain.py —— 评分器升级为多维度（结构/密度/结论性/具体性/可读性）
4) brain/skill_polish.py —— 补 do_status/do_run/HANDLERS（修复 Action not found）
"""
import sys, io, re, json, shutil, time, importlib.util
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r'C:\Users\ADMIN\Desktop\GBT小土豆')
TS = time.strftime('%Y%m%d%H%M%S')

def readtext(p):
    b = Path(p).read_bytes()
    nl = '\r\n' if b'\r\n' in b else '\n'
    for enc in ('utf-8', 'utf-8-sig', 'gbk'):
        try:
            return b.decode(enc).replace('\ufeff', '').replace('\r\n', '\n'), enc, nl
        except Exception:
            continue
    return b.decode('utf-8', errors='replace').replace('\r\n', '\n'), 'utf-8', nl

def backup(p):
    p = Path(p)
    dst = p.with_name(p.name + '.pre-fix-' + TS + '.bak')
    shutil.copy2(p, dst)
    return dst.name

def writetext(p, s, enc, nl='\n'):
    Path(p).write_bytes(s.replace('\n', nl).encode(enc if enc != 'utf-8-sig' else 'utf-8', errors='replace'))

# ── 1) 桥：动作路由 ──
f1 = ROOT / 'gbt_cap_bridge.py'
c1, e1, nl1 = readtext(f1)
old1 = """        # Priority: do_run > do_{action} > action > any do_*
        action_func = getattr(mod, 'do_run', None)
        if not action_func:
            action_func = getattr(mod, f'do_{action}', None)"""
new1 = """        # Priority: do_{action} > do_run > action > any do_*
        # V8 根因修复(2026-09-12): 精确动作优先，且把 action 并入参数——
        # 旧实现让 do_run 吞掉所有 action 又收不到动作名(evaluate/assess_layout/style_guide 被误路由,
        # 表现为"评分器恒返回/路由偏差"),这里是平台设计能力"形同占位"的根因。
        action_func = getattr(mod, f'do_{action}', None)
        if not action_func:
            action_func = getattr(mod, 'do_run', None)"""
assert old1 in c1, 'bridge-anchor'
c1 = c1.replace(old1, new1, 1)

old1b = """        t0 = time.time()
        result = action_func(params if params else {})
        elapsed = time.time() - t0"""
new1b = """        t0 = time.time()
        merged = dict(params) if isinstance(params, dict) else {}
        merged.setdefault('action', action)
        try:
            result = action_func(merged)
        except TypeError:
            result = action_func()   # 兼容无参处理函数
        elapsed = time.time() - t0"""
assert old1b in c1, 'bridge-anchor2'
c1 = c1.replace(old1b, new1b, 1)
print('backup:', backup(f1))
writetext(f1, c1, e1, nl1)
print('[1/4] 桥：动作路由已修（do_{action} 优先 + action 并入参数）')

# ── 2) design_brain：aesthetic 随输入匹配 + do_run ──
f2 = ROOT / 'caps' / 'design_brain' / 'run.py'
c2, e2, nl2 = readtext(f2)
old2 = """    aesthetic_styles = params.get("aesthetic", "warm_luxury")
    aesthetics = {"""
new2 = """    aesthetic_styles = params.get("aesthetic") or _match_aesthetic(desc)
    aesthetics = {"""
assert old2 in c2, 'db-anchor1'
c2 = c2.replace(old2, new2, 1)

# 在 do_aesthetic 前插入风格匹配器
helper = '''def _match_aesthetic(text: str) -> str:
    """按输入语义自动匹配 aesthetic 风格（修复：旧实现恒用默认 warm_luxury）。"""
    t = (text or "").lower()
    rules = [
        ("cyberpunk", ("cyberpunk", "neon", "futuristic", "赛博", "霓虹", "未来")),
        ("zen", ("zen", "禅", "bamboo", "meditat", "peace", "日式", "和风")),
        ("natural", ("nature", "plant", "wood", "organic", "biophilic", "自然", "木", "绿植", "森林")),
        ("cool_minimal", ("minimal", "minimalist", "grey", "gray", "white", "极简", "简约", "冷", "无印")),
        ("dramatic", ("dramatic", "moody", "spotlight", "cinematic", "戏剧", "聚光", "高对比")),
        ("warm_luxury", ("luxury", "gold", "brass", "marble", "elegant", "豪华", "奢华", "金", "大理石", "暖")),
    ]
    for style, kws in rules:
        if any(k in t for k in kws):
            return style
    return "warm_luxury"


def do_aesthetic(params: dict) -> dict:'''
assert 'def do_aesthetic(params: dict) -> dict:' in c2
c2 = c2.replace('def do_aesthetic(params: dict) -> dict:', helper, 1)

# 返回里带上匹配到的风格说明
c2 = c2.replace('''        "quality_level": quality,
        "aesthetic": aesthetic_styles,''', '''        "quality_level": quality,
        "aesthetic": aesthetic_styles,
        "style_matched": True,''', 1)

# 补 do_run 分发 + 注册
old2b = """HANDLERS = {
    "status": do_status,"""
new2b = '''def do_run(params: dict = None) -> dict:
    """统一入口（桥优先调 do_run）：按 action 分发到对应 handler。"""
    p = params or {}
    action = p.get("action") or "style_guide"
    fn = HANDLERS.get(action)
    if not fn:
        return {"ok": False, "error": f"未知动作: {action}", "available": sorted(HANDLERS.keys())}
    try:
        return fn(p) if action != "status" else fn()
    except TypeError:
        return fn()


HANDLERS = {
    "run": do_run,
    "status": do_status,'''
assert old2b in c2, 'db-anchor2'
c2 = c2.replace(old2b, new2b, 1)
print('backup:', backup(f2))
writetext(f2, c2, e2, nl2)
print('[2/4] design_brain：aesthetic 随输入匹配 + do_run 分发')

# ── 3) aesthetic_brain：多维评分器 ──
f3 = ROOT / 'brain' / 'aesthetic_brain.py'
_, e3, nl3 = readtext(f3)
new3 = '''"""aesthetic_brain.py — 审美大脑: 设计/文案质量评估（多维度启发式）

V8 升级(2026-09-12): 由单一分数升级为多维度评分 + 改进建议，且随输入真实变化
（旧实现被平台调用时表现为恒定/占位）。
开发者：自由的风 · 本署名不可删除、不可篡改归属
"""
import json
import re
import time
from pathlib import Path

STATE_DIR = Path.home() / ".gbt" / "aesthetic"
LOG_FILE = STATE_DIR / "scores.jsonl"
STATE_DIR.mkdir(parents=True, exist_ok=True)


def _clamp(x):
    return max(0, min(100, int(round(x))))


def _log(kind, payload):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": kind, **payload},
                               ensure_ascii=False) + "\\n")
    except Exception:
        pass


def evaluate(text):
    """文案/设计说明质量评估：结构·密度·结论性·具体性·可读性 五维。"""
    t = str(text or "")
    n = len(t)
    dims = {}
    struct = 30
    if "#" in t:
        struct += 15
    if any(m in t for m in ("- ", "\\u00b7", "1.", "\\u2460", "\\u2022")):
        struct += 15
    if "\\n" in t:
        struct += 15
    if len([ln for ln in t.split("\\n") if ln.strip()]) >= 3:
        struct += 10
    dims["\\u7ed3\\u6784"] = _clamp(struct)
    dims["\\u5bc6\\u5ea6"] = _clamp(n / 4) if n < 400 else 100
    kws = sum(1 for w in ("\\u7ed3\\u8bba", "\\u603b\\u7ed3", "\\u56e0\\u6b64", "\\u5efa\\u8bae", "\\u7efc\\u4e0a", "summary", "conclusion")
              if w in t.lower())
    dims["\\u7ed3\\u8bba\\u6027"] = _clamp(20 + kws * 20)
    nums = len(re.findall(r"\\d+", t))
    dims["\\u5177\\u4f53\\u6027"] = _clamp(20 + nums * 8)
    sents = max(1, len(re.findall(r"[\\u3002.!\\uff01?\\uff1f\\n]", t)) or 1)
    avg = n / sents
    dims["\\u53ef\\u8bfb\\u6027"] = 100 if 8 <= avg <= 45 else (65 if avg < 8 else 50)
    score = _clamp(sum(dims.values()) / len(dims))
    verdict = "good" if score >= 75 else ("ok" if score >= 50 else "weak")
    weakest = min(dims, key=dims.get)
    hint = {
        "\\u7ed3\\u6784": "\\u8865\\u6807\\u9898/\\u5206\\u70b9\\uff0c\\u8ba9\\u5c42\\u7ea7\\u6e05\\u695a",
        "\\u5bc6\\u5ea6": "\\u5185\\u5bb9\\u504f\\u8584\\uff0c\\u8865\\u5173\\u952e\\u4fe1\\u606f",
        "\\u7ed3\\u8bba\\u6027": "\\u8865\\u4e00\\u5904\\u660e\\u786e\\u7ed3\\u8bba\\u6216\\u5efa\\u8bae",
        "\\u5177\\u4f53\\u6027": "\\u52a0\\u5165\\u5177\\u4f53\\u6570\\u5b57/\\u547d\\u540d\\uff0c\\u51cf\\u5c11\\u7a7a\\u6cdb",
        "\\u53ef\\u8bfb\\u6027": "\\u53e5\\u5b50\\u504f\\u957f\\u6216\\u504f\\u788e\\uff0c\\u8c03\\u6574\\u8282\\u594f",
    }[weakest]
    _log("evaluate", {"score": score, "verdict": verdict, "dims": dims, "len": n})
    return {"ok": True, "score": score, "verdict": verdict, "dimensions": dims,
            "advice": {"weakest": weakest, "hint": hint}, "length": n}


def assess_layout(meta):
    """版面质量评估：对比·间距·层级·对齐·色彩 五维（meta 可给 contrast/space/levels/align/colors）。"""
    m = meta or {}

    def num(k, d):
        try:
            return float(m.get(k, d))
        except Exception:
            return d

    dims = {}
    c = num("contrast", 4.5)
    dims["\\u5bf9\\u6bd4"] = _clamp(40 + (c - 3) * 20) if c >= 3 else _clamp(c / 3 * 40)
    sp = num("space", 16)
    dims["\\u95f4\\u8ddd"] = 100 if 12 <= sp <= 24 else (70 if 8 <= sp <= 32 else 50)
    lv = num("levels", 3)
    dims["\\u5c42\\u7ea7"] = 100 if 3 <= lv <= 5 else (75 if lv <= 6 else 55)
    dims["\\u5bf9\\u9f50"] = 100 if num("align", 1) >= 1 else 60
    cols = num("colors", 3)
    dims["\\u8272\\u5f69"] = 100 if 2 <= cols <= 4 else (70 if cols <= 6 else 50)
    score = _clamp(sum(dims.values()) / len(dims))
    verdict = "good" if score >= 75 else ("ok" if score >= 50 else "weak")
    _log("assess_layout", {"score": score, "verdict": verdict, "dims": dims})
    return {"ok": True, "score": score, "verdict": verdict, "dimensions": dims, "contrast": c}


def status():
    n = 0
    if LOG_FILE.exists():
        try:
            n = len([l for l in LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()])
        except Exception:
            pass
    return {"ok": True, "scores": n}


def do_run(params={}):
    p = params or {}
    action = p.get("action", "evaluate")
    if action == "evaluate":
        return evaluate(p.get("text", ""))
    if action == "assess_layout":
        return assess_layout(p.get("meta", {}))
    if action == "status":
        return status()
    return {"ok": False, "error": "unknown action: " + str(action),
            "available": ["evaluate", "assess_layout", "status"]}


HANDLERS = {"status": status, "evaluate": evaluate, "assess_layout": assess_layout, "run": do_run}
'''
print('backup:', backup(f3))
writetext(f3, new3, 'utf-8', nl3)
print('[3/4] aesthetic_brain：多维评分器已升级')

# ── 4) skill_polish：补 do_run/HANDLERS ──
f4 = ROOT / 'brain' / 'skill_polish.py'
c4, e4, nl4 = readtext(f4)
anchor4 = 'if __name__ == "__main__":'
assert anchor4 in c4, 'sp-anchor'
add = '''def ledger(limit=100):
    """打磨台账（可回滚记录）。"""
    entries = []
    if LEDGER.exists():
        try:
            entries = [json.loads(ln) for ln in LEDGER.read_text(encoding="utf-8").splitlines() if ln.strip()]
        except Exception:
            entries = []
    return {"ok": True, "count": len(entries), "entries": entries[-int(limit or 100):]}


def do_status(params=None):
    """打磨器状态：快照数 + 台账条数。"""
    snaps = len(list(SNAP.glob("*.capability.json*"))) if SNAP.exists() else 0
    led = ledger(limit=1).get("count", 0)
    return {"ok": True, "cap": "skill_polish", "status": "ready", "snapshots": snaps,
            "ledger_entries": led, "note": "capability.json 元数据打磨器（经镜像门禁 publish，可回滚）"}


def do_polish_action(params=None):
    """按名字打磨若干能力（params: name/names，可选 dry）。"""
    p = params or {}
    names = p.get("names") or p.get("name") or ""
    if isinstance(names, str):
        names = [x.strip() for x in names.split(",") if x.strip()]
    dry = bool(p.get("dry", False))
    return {"ok": True, "results": [polish(n, dry=dry) for n in names]}


def do_run(params=None):
    """统一入口（桥优先调 do_run）：scan / polish / ledger / status。"""
    p = params or {}
    action = p.get("action") or "scan"
    if action in ("scan", "report"):
        return {"ok": True, **scan_all()}
    if action == "polish":
        return do_polish_action(p)
    if action == "ledger":
        return ledger(p.get("limit", 100))
    if action == "status":
        return do_status(p)
    return {"ok": False, "error": f"未知动作: {action}", "available": ["scan", "polish", "ledger", "status"]}


HANDLERS = {"status": do_status, "scan": lambda p=None: {"ok": True, **scan_all()},
            "polish": do_polish_action, "ledger": ledger, "run": do_run}


'''
c4 = c4.replace(anchor4, add + anchor4, 1)
print('backup:', backup(f4))
writetext(f4, c4, e4, nl4)
print('[4/4] skill_polish：do_run/HANDLERS 已补')

# ── 验证（模拟桥的 execute_cap 调用）──
print('\n=== 验证（经桥 execute_cap 逻辑）===')
spec = importlib.util.spec_from_file_location('_bridge', str(f1))
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
import importlib
for cap, act, params in [
    ('design_brain', 'aesthetic', {'prompt': 'cyberpunk office'}),
    ('design_brain', 'aesthetic', {'prompt': 'quiet luxury lobby with marble'}),
    ('design_brain', 'style_guide', {}),
    ('aesthetic_brain', 'evaluate', {'text': '短句'}),
    ('aesthetic_brain', 'evaluate', {'text': '这是一段设计说明。包含结论与建议，因此可读性较好。# 标题 ' + 'x'*180}),
    ('aesthetic_brain', 'assess_layout', {'meta': {'contrast': 7, 'space': 16, 'levels': 3, 'colors': 3}}),
    ('skill_polish', 'status', {}),
    ('skill_polish', 'scan', {}),
]:
    # execute_cap 每次重新加载模块，保证读的是刚写入的文件
    r = bridge.execute_cap(cap, act, params)
    brief = {k: r.get(k) for k in ('ok', 'action', 'enhanced', 'aesthetic', 'score', 'verdict', 'dimensions', 'with_mirror_policy', 'error') if k in r}
    print(f'{cap}.{act}:', json.dumps(brief, ensure_ascii=False)[:260])
