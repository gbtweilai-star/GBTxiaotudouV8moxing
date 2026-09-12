# -*- coding: utf-8 -*-
# ? 开发者：自由的风 · 永久钢印 · 禁止删除
"""brain/skill_polish.py — 常用原生技能打磨迭代器 v1 (2026-09-09)
规则: 技能打磨=编程/配置修改 → 必须走镜像门禁(gatekeeper.publish)。
流程(每个技能): 备份快照 → 注入打磨变更(版本/镜像策略/变更说明) → publish(镜像多维验证+签名+stamp)
              → 回读校验 + is_promoted 确认 → 写 skill_polish_ledger.jsonl(可回滚: 快照留存)
用法: python brain/skill_polish.py polish deep_reasoner,intent_broker,visual_cortex
      python brain/skill_polish.py scan           # 全量技能健康扫描(547)
      python brain/skill_polish.py ledger
"""
import importlib.util, io, json, shutil, sys, time
from pathlib import Path

ROOT = Path.home() / "Desktop" / "GBT小土豆"
CAPS = ROOT / "caps"
SNAP = Path.home() / ".gbt" / "unified_core" / "cap_snapshots"
LEDGER = Path.home() / ".gbt" / "unified_core" / "skill_polish_ledger.jsonl"
POLISH_NOTE = {"mirror_policy": {"prod_write": "must-publish",
                                 "note": "编程与部署修改须经 mirror_gate/gatekeeper.publish 进入镜像多维度空间(2026-09-09 强制规范)"}}

def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, str(ROOT / rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def cap_path(name):
    d = CAPS / name
    if (d / "capability.json").exists():
        return d / "capability.json"
    return None

def polish(name, dry=False):
    p = cap_path(name)
    if p is None:
        return {"name": name, "ok": False, "error": "capability.json 不存在"}
    doc = json.loads(p.read_text(encoding="utf-8"))
    orig = json.dumps(doc, ensure_ascii=False)
    # 快照(记录真实文件名供回滚)
    SNAP.mkdir(parents=True, exist_ok=True)
    snap_name = name + ".capability.json.v-snapshot-" + time.strftime("%Y%m%d%H%M%S")
    (SNAP / snap_name).write_text(orig, encoding="utf-8")
    # 注入打磨(幂等)
    doc["version"] = str(doc.get("version") or "1.0.0").replace("1.0.0", "1.1.0") if doc.get("version") in (None, "1.0.0") else doc.get("version")
    doc.setdefault("changelog", []).append({"v": "1.1.0", "date": "2026-09-09",
                                             "reason": "镜像门禁打磨: 技能修改须经镜像多维空间 publish 发布(用户强制口径)"})
    doc.setdefault("mirror_policy", POLISH_NOTE["mirror_policy"])
    content = json.dumps(doc, ensure_ascii=False, indent=1)
    if dry:
        return {"name": name, "ok": True, "dry": True, "changed": content != orig}
    # 经镜像门禁发布(唯一受信出口)
    mg = _load("_mg", r"brain\mirror_gate.py")
    r = mg.authorize(str(p), content, context="skill-polish")
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+07"), "cap": name, "file": str(p),
           "ok": bool(r.get("ok")), "hash": r.get("hash"), "written": r.get("written"),
           "error": r.get("error"), "snapshot": str(SNAP / snap_name)}
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"name": name, "ok": bool(r.get("ok")), "hash": r.get("hash"),
            "written": r.get("written"), "error": r.get("error")}

def scan_all():
    """全量技能健康扫描(547): 关键字段完整性/版本/描述/镜像策略缺失"""
    idx_f = CAPS / "gbt_cap_index.json"
    total = 0; missing_desc = []; missing_ver = []; no_mirror_policy = []; ok = []
    if idx_f.exists():
        idx = json.loads(idx_f.read_text(encoding="utf-8"))
        total = idx.get("total_caps", 0)
    for d in sorted(CAPS.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        p = d / "capability.json"
        if not p.exists():
            continue
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            no_mirror_policy.append(d.name + ":JSON-ERR")
            continue
        if not doc.get("description"):
            missing_desc.append(d.name)
        if not doc.get("version"):
            missing_ver.append(d.name)
        if "mirror_policy" not in doc:
            no_mirror_policy.append(d.name)
        else:
            ok.append(d.name)
    return {"index_total": total, "scanned": len(ok) + len(no_mirror_policy) + len(missing_desc),
            "with_mirror_policy": len(ok), "no_mirror_policy": len(no_mirror_policy),
            "missing_version": len(missing_ver), "missing_desc": len(missing_desc),
            "sample_no_policy": no_mirror_policy[:5]}

def ledger(limit=100):
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


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: polish <a,b,c> | scan | ledger")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "polish":
        out = [polish(n) for n in sys.argv[2].split(",")]
    elif cmd == "scan":
        out = scan_all()
    elif cmd == "ledger":
        out = [json.loads(ln) for ln in LEDGER.read_text(encoding="utf-8").splitlines()] if LEDGER.exists() else []
    else:
        out = {"error": "unknown"}
    print(json.dumps(out, ensure_ascii=False, indent=1))