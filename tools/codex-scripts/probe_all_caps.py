# -*- coding: utf-8 -*-
"""140 个能力逐个真调 —— 建立真实执行矩阵。

判据（不靠印象，也不靠子串猜）：2026-09-21 的「信封形状普查」先枚举出**真实结构**，
再按结构判定（见 scan_envelope_shapes.py / envelope_shapes.json）：

  A 直拒（门）：顶层 ok=False / status="denied" / denied=True / missing=[...] / how_to_grant
     —— 结构化字段，直接读，不猜
  B 成功信封：顶层 ok=True / gbt_result={kind,result:{...内层 ok ...}}
     —— **信封 ok=True 只代表「这个调用被派发了」，不代表能力成功**；
        真正的成败在内层 result.ok。旧版只看信封，于是把 3 个内层拒绝误报成 ok。

归类：
  ok              真能跑（top ok=True 且内层没拒绝）
  gated           有实现，卡在授权门（denied=True）—— 授权只能主人发
  needs_params    有实现，但必须给参数（error_class=user_error）
  inner_refused   信封 ok=True，内层如实拒绝（如 backend_not_wired / empty_input）
  exception/odd   真坏，要修
全部走 api.run_task，绝不绕门、绝不自己发授权。
"""
import json
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

from gbt_allinone import api  # noqa: E402

OUT = Path(__file__).resolve().parent / "capability_matrix.json"


def unwrap(res):
    """下沉到真正的业务结果。信封有两层，判定必须在最里层。"""
    if not isinstance(res, dict):
        return {}, {}
    g = res.get("gbt_result")
    if isinstance(g, dict):
        inner = g.get("result")
        return (inner if isinstance(inner, dict) else {}), g
    inner = res.get("result")
    return (inner if isinstance(inner, dict) else {}), res


def classify(res, exc):
    if exc:
        return "exception", "%s: %s" % (type(exc).__name__, str(exc)[:150])
    if not isinstance(res, dict):
        return "odd", repr(res)[:120]

    # ① 结构化的门：优先于一切子串猜测
    if res.get("denied") is True or res.get("status") == "denied":
        scopes = res.get("scopes") or res.get("missing") or []
        how = str(res.get("how_to_grant") or "")[:110]
        return "gated", "需要人工授权 %s%s" % (scopes, (" · " + how) if how else "")

    inner, env = unwrap(res)
    top_ok = res.get("ok") is True

    # ② 信封 ok=True：成败看内层
    if top_ok:
        if inner.get("ok") is False:
            why = (inner.get("reason_code") or inner.get("detail")
                   or inner.get("last_error") or inner.get("error") or "")
            return "inner_refused", "信封 ok=True 但内层拒绝（%s）" % str(why)[:120]
        return "ok", ""

    # ③ 信封 ok=False 且不是门：按 error_class 分
    ec = str(res.get("error_class") or "")
    msg = ""
    for src in (res, inner):
        msg = str(src.get("message") or src.get("error") or src.get("detail") or "")
        if msg:
            break
    msg = msg[:180]
    if "user_error" in ec or "UserError" in ec:
        return "needs_params", msg
    if "not_implemented" in ec or "未实现" in msg or "只读骨架" in msg \
            or "needs_dependency" in ec or "backend_not_wired" in msg:
        return "not_implemented", msg
    return "refused_other", (ec + " | " + msg)[:200]


rows = api.list_capabilities()
print("能力总数:", len(rows))
matrix = []
t0 = time.time()
for i, r in enumerate(rows, 1):
    name = r["name"]
    exc, res = None, None
    st = time.time()
    try:
        res = api.run_task(name, {}, safe=True, probe=True)
    except Exception as e:  # noqa: BLE001
        exc = e
    ms = int((time.time() - st) * 1000)
    kind, note = classify(res, exc)
    inner, _env = unwrap(res)
    keys = sorted(inner.keys())[:8] if inner else []
    matrix.append({"name": name, "domain": r.get("domain"), "kind": kind, "note": note,
                   "ms": ms, "keys": keys})
    if i % 20 == 0 or kind in ("exception", "refused_other", "odd", "not_implemented"):
        print("  [%3d/%d] %-26s %-16s %5dms %s" % (i, len(rows), name, kind, ms, note[:70]))

print("\n总耗时 %.1f s" % (time.time() - t0))
print("\n" + "=" * 90)
print("执行矩阵汇总（结构判定）")
print("=" * 90)
c = Counter(m["kind"] for m in matrix)
for k, v in c.most_common():
    print("  %-18s %3d" % (k, v))

for kind in ("exception", "refused_other", "odd"):
    bad = [m for m in matrix if m["kind"] == kind]
    if bad:
        print("\n● %s（真坏，要修）: %d" % (kind, len(bad)))
        for m in bad:
            print("   %-26s %-13s %s" % (m["name"], m["domain"], m["note"][:120]))

print("\n● inner_refused（信封 ok=True 但内层拒绝 —— 旧口径会误报成 ok）: %d"
      % len([m for m in matrix if m["kind"] == "inner_refused"]))
for m in [m for m in matrix if m["kind"] == "inner_refused"]:
    print("   %-26s %-13s %s" % (m["name"], m["domain"], m["note"][:110]))

print("\n● needs_params（有实现，需给参数）: %d" % len([m for m in matrix if m["kind"] == "needs_params"]))
for m in [m for m in matrix if m["kind"] == "needs_params"]:
    print("   %-26s %-13s %s" % (m["name"], m["domain"], m["note"][:96]))

print("\n● gated（卡在授权门，授权只能主人发）: %d" % len([m for m in matrix if m["kind"] == "gated"]))
for m in [m for m in matrix if m["kind"] == "gated"]:
    print("   %-26s %-13s %s" % (m["name"], m["domain"], m["note"][:96]))

print("\n● not_implemented（只读骨架/未接线，如实承认）: %d"
      % len([m for m in matrix if m["kind"] == "not_implemented"]))
for m in [m for m in matrix if m["kind"] == "not_implemented"]:
    print("   %-26s %-13s %s" % (m["name"], m["domain"], m["note"][:96]))

# 门的作用域归总 —— 主人要看的是「到底要发哪些授权」
scopes = defaultdict(list)
for m in matrix:
    if m["kind"] == "gated":
        for s in (m["note"].split("需要人工授权 ")[-1].split(" · ")[0].strip("[]").split(", ")):
            s = s.strip("'\" ")
            if s:
                scopes[s].append(m["name"])
print("\n" + "=" * 90)
print("授权门作用域归总（主人只需按这个清单发授权）")
print("=" * 90)
for s, names in sorted(scopes.items(), key=lambda kv: -len(kv[1])):
    print("  %-18s %2d 个能力: %s" % (s, len(names), "、".join(names)))

OUT.write_text(json.dumps(matrix, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n写出:", OUT.name)
