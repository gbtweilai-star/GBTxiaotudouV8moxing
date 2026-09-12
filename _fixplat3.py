# -*- coding: utf-8 -*-
"""经镜像门禁发布 design_brain + skill_polish 修复，并做持久性验证。"""
import sys, json, time, importlib.util
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(r'C:\Users\ADMIN\Desktop\GBT小土豆')

def rd(p):
    return Path(ROOT / p).read_bytes().decode('utf-8').replace('\r\n', '\n').replace('\ufeff', '')

def load_mod(name, rel):
    spec = importlib.util.spec_from_file_location(name, str(ROOT / rel))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m

mg = load_mod('_mg', r'brain\mirror_gate.py')

# ── design_brain/run.py ──
c = rd(r'caps\design_brain\run.py')
helper = '''def _match_aesthetic(text: str) -> str:
    """\u6309\u8f93\u5165\u8bed\u4e49\u81ea\u52a8\u5339\u914d aesthetic \u98ce\u683c\uff08\u4fee\u590d\uff1a\u65e7\u5b9e\u73b0\u6052\u7528\u9ed8\u8ba4 warm_luxury\uff09\u3002"""
    t = (text or "").lower()
    rules = [
        ("cyberpunk", ("cyberpunk", "neon", "futuristic", "\u8d5b\u535a", "\u9713\u8679", "\u672a\u6765")),
        ("zen", ("zen", "\u7985", "bamboo", "meditat", "peace", "\u65e5\u5f0f", "\u548c\u98ce")),
        ("natural", ("nature", "plant", "wood", "organic", "biophilic", "\u81ea\u7136", "\u6728", "\u7eff\u690d", "\u68ee\u6797")),
        ("cool_minimal", ("minimal", "minimalist", "grey", "gray", "white", "\u6781\u7b80", "\u7b80\u7ea6", "\u51b7", "\u65e0\u5370")),
        ("dramatic", ("dramatic", "moody", "spotlight", "cinematic", "\u620f\u5267", "\u805a\u5149", "\u9ad8\u5bf9\u6bd4")),
        ("warm_luxury", ("luxury", "gold", "brass", "marble", "elegant", "\u8c6a\u534e", "\u5962\u534e", "\u91d1", "\u5927\u7406\u77f3", "\u6696")),
    ]
    for style, kws in rules:
        if any(k in t for k in kws):
            return style
    return "warm_luxury"


def do_aesthetic(params: dict) -> dict:'''
assert 'def do_aesthetic(params: dict) -> dict:' in c
c = c.replace('def do_aesthetic(params: dict) -> dict:', helper, 1)
c = c.replace('''    aesthetic_styles = params.get("aesthetic", "warm_luxury")''',
              '''    aesthetic_styles = params.get("aesthetic") or _match_aesthetic(desc)''', 1)
c = c.replace('''        "quality_level": quality,
        "aesthetic": aesthetic_styles,''',
              '''        "quality_level": quality,
        "aesthetic": aesthetic_styles,
        "style_matched": True,''', 1)
old = '''HANDLERS = {
    "status": do_status,'''
new = '''def do_run(params: dict = None) -> dict:
    """\u7edf\u4e00\u5165\u53e3\uff08\u6865\u4f18\u5148\u8c03 do_run\uff09\uff1a\u6309 action \u5206\u53d1\u3002"""
    p = params or {}
    action = p.get("action") or "style_guide"
    fn = HANDLERS.get(action)
    if not fn:
        return {"ok": False, "error": f"\u672a\u77e5\u52a8\u4f5c: {action}", "available": sorted(HANDLERS.keys())}
    try:
        return fn(p) if action != "status" else fn()
    except TypeError:
        return fn()


HANDLERS = {
    "run": do_run,
    "status": do_status,'''
assert old in c
c = c.replace(old, new, 1)
r2 = mg.authorize('caps/design_brain/run.py', c, context='V8 设计能力修复: aesthetic 随输入匹配 + do_run')
print('design_brain:', json.dumps({k: r2.get(k) for k in ('ok', 'written', 'hash', 'error')}, ensure_ascii=False))

# ── skill_polish.py ──
c4 = rd(r'brain\skill_polish.py')
anchor = 'if __name__ == "__main__":'
add = '''def ledger(limit=100):
    """\u6253\u78e8\u53f0\u8d26\uff08\u53ef\u56de\u6eda\u8bb0\u5f55\uff09\u3002"""
    entries = []
    if LEDGER.exists():
        try:
            entries = [json.loads(ln) for ln in LEDGER.read_text(encoding="utf-8").splitlines() if ln.strip()]
        except Exception:
            entries = []
    return {"ok": True, "count": len(entries), "entries": entries[-int(limit or 100):]}


def do_status(params=None):
    """\u6253\u78e8\u5668\u72b6\u6001\uff1a\u5feb\u7167\u6570 + \u53f0\u8d26\u6761\u6570\u3002"""
    snaps = len(list(SNAP.glob("*.capability.json*"))) if SNAP.exists() else 0
    led = ledger(limit=1).get("count", 0)
    return {"ok": True, "cap": "skill_polish", "status": "ready", "snapshots": snaps,
            "ledger_entries": led, "note": "capability.json \u5143\u6570\u636e\u6253\u78e8\u5668\uff08\u7ecf\u955c\u50cf\u95e8\u7981 publish\uff0c\u53ef\u56de\u6eda\uff09"}


def do_polish_action(params=None):
    """\u6309\u540d\u5b57\u6253\u78e8\u82e5\u5e72\u80fd\u529b\uff08params: name/names\uff0c\u53ef\u9009 dry\uff09\u3002"""
    p = params or {}
    names = p.get("names") or p.get("name") or ""
    if isinstance(names, str):
        names = [x.strip() for x in names.split(",") if x.strip()]
    dry = bool(p.get("dry", False))
    return {"ok": True, "results": [polish(n, dry=dry) for n in names]}


def do_run(params=None):
    """\u7edf\u4e00\u5165\u53e3\uff08\u6865\u4f18\u5148\u8c03 do_run\uff09\uff1ascan / polish / ledger / status\u3002"""
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
    return {"ok": False, "error": f"\u672a\u77e5\u52a8\u4f5c: {action}", "available": ["scan", "polish", "ledger", "status"]}


HANDLERS = {"status": do_status, "scan": lambda p=None: {"ok": True, **scan_all()},
            "polish": do_polish_action, "ledger": ledger, "run": do_run}


'''
assert anchor in c4
c4 = c4.replace(anchor, add + anchor, 1)
r4 = mg.authorize('brain/skill_polish.py', c4, context='V8 设计能力修复: 补 do_run/HANDLERS')
print('skill_polish:', json.dumps({k: r4.get(k) for k in ('ok', 'written', 'hash', 'error')}, ensure_ascii=False))

# ── 持久性验证（等 20s 再读）──
print('\n等待 20s 观察是否被还原...')
time.sleep(20)
for rel, marker in [(r'brain\aesthetic_brain.py', 'dimensions'),
                    (r'caps\design_brain\run.py', '_match_aesthetic'),
                    (r'brain\skill_polish.py', 'HANDLERS')]:
    p = ROOT / rel
    txt = rd(rel)
    print(f'{rel}: 含新码={marker in txt} | mtime={time.strftime("%H:%M:%S", time.localtime(p.stat().st_mtime))}')
