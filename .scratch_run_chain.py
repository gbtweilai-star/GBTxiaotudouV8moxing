"""一句话全链 · 真跑（一次性脚本，用完即删）。

链：一句话 → one_shot.plan → 写清单 → actioncam plan/build（出 8 拍）→ look_grade pick（取味）
    → actioncam qc（机械 QC）→ filmgrade deliver_check（三级交付检查）。
凡"写/跑"的步骤**一律经唯一门 run_task**；只有读文件的检查（deliver_check）直连模块。
"""
from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
PROMPT = "潮湿阴冷的雨夜，她在代码里醒来，节奏紧凑"


def _gate(kind: str, payload: dict) -> dict:
    import sys
    sys.path.insert(0, str(ROOT))
    import gbt_allinone as g
    r = g.run_task(kind, payload)
    d = r.get("result") if isinstance(r, dict) else None
    while isinstance(d, dict) and isinstance(d.get("result"), dict) and set(d) <= {"status", "kind", "result", "ok"}:
        d = d["result"]
    return {"gate_ok": bool(isinstance(r, dict) and r.get("ok", True)), "payload": d}


def _tool(rel: str, name: str):
    sp = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


print("═══ ① 一句话 → 计划（过门）═══")
p = _gate("one_shot", {"op": "plan", "prompt": PROMPT})
plan = p["payload"] or {}
print("  推导：", json.dumps(plan.get("推导"), ensure_ascii=False)[:200])
mf = plan.get("manifest（未写盘）") or {}
print(f"  清单：BPM {mf.get('bpm')} · {mf.get('beats')} 拍 · 调色 {mf.get('grade')} · 画质 {mf.get('quality')}")

print("\n═══ ② 写清单（落 projects/movie/产线/）═══")
ts = time.strftime("%Y%m%d-%H%M%S")
mp = ROOT / "projects" / "movie" / "产线" / f"manifest-oneshot-{ts}.json"
mp.parent.mkdir(parents=True, exist_ok=True)
mp.write_text(json.dumps(mf, ensure_ascii=False, indent=1), encoding="utf-8")
print("  ", mp.relative_to(ROOT))

print("\n═══ ③ actioncam plan（过门·校验清单）═══")
ac_plan = _gate("actioncam", {"op": "plan", "manifest": str(mp)})
print("  gate_ok =", ac_plan["gate_ok"], "·", json.dumps(ac_plan["payload"], ensure_ascii=False)[:240])

print("\n═══ ④ actioncam build（过门·真出 8 拍 + 总装）═══")
t0 = time.time()
ac = _gate("actioncam", {"op": "build", "manifest": str(mp)})
dt = time.time() - t0
pl = ac["payload"] or {}
print(f"  gate_ok = {ac['gate_ok']} · 耗时 {dt:.1f}s")
print("  ", json.dumps({k: v for k, v in pl.items() if k in
                        ("ok", "out", "film", "path", "segments", "beats", "elapsed_s", "denied", "error", "how_to_grant")},
                       ensure_ascii=False)[:400])

print("\n═══ ⑤ look_grade pick（过门·词即指令）═══")
lg = _gate("look_grade", {"op": "pick", "intent": PROMPT})   # 参数名是 intent=（实测：text= 会被拒）
print("  ", json.dumps(lg["payload"], ensure_ascii=False)[:220])

print("\n═══ ⑥ 交付检查（读文件：三级检查 + SSIM 阶梯）═══")
film = None
for k in ("film", "out", "path"):
    v = pl.get(k)
    if isinstance(v, str) and v.lower().endswith((".mp4", ".mov", ".mkv")):
        film = ROOT / v if not Path(v).is_absolute() else Path(v)
        break
if not film:
    films = sorted((ROOT / "projects" / "movie").rglob("*.mp4"), key=lambda x: -x.stat().st_mtime)[:3]
    film = films[0] if films else None
print("  成片：", (film.relative_to(ROOT) if film else "（没找到——看 build 的输出）"))
if film and film.is_file():
    fgm = _tool("tools/filmgrade.py", "fg_chain")
    dc = fgm.deliver_check(film)
    print("  deliver_check：", json.dumps(dc, ensure_ascii=False)[:420])
    try:
        dl = fgm.deliver_ladder(film)
        print("  deliver_ladder：", json.dumps(dl, ensure_ascii=False)[:300])
    except Exception as e:                                     # noqa: BLE001
        print("  deliver_ladder 没跑成：", f"{type(e).__name__}: {str(e)[:120]}")
    qc = _gate("actioncam", {"op": "qc", "manifest": str(mp)})
    print("  actioncam qc（过门）：", json.dumps(qc["payload"], ensure_ascii=False)[:260])
else:
    print("  ⇒ 没有可检的成片文件（build 若失败，上面有原因）")
