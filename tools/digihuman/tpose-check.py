# -*- coding: utf-8 -*-
"""S2 门 · T-pose 姿态规范 —— **严格对齐技能源码口径**（不是我自己发明的判据）

源码口径（`skills/digihuman-pipeline/scripts/run-pipeline.ps1:64,73` + `SKILL.md:33`）：
    五条判据 = 水平双臂 / 直立双腿 / 正面全身 / **无遮挡物** / 白底
    ⚠ **必做人工复核**：打开规范化图看，五条全过才继续
    （SKILL.md:34 另有一条机器代理：`臂展≈身高` —— 属下游阶段）

所以本门的正确语义是：
  · 机器只给**代理读数**（剪影/白底/直立），**仅作提示，不能单独判过**；
  · **必须存在人工确认记录** `.digihuman/S2-human-ok.json`（人看过图、勾了五条）才算过。

    python tools/digihuman/tpose-check.py                      # 门：无人工确认 ⇒ 判「待人工确认」
    python tools/digihuman/tpose-check.py --confirm "<复核人>"   # 人看过图后落确认记录
"""
from __future__ import annotations

import json
import pathlib
import struct
import sys
import time

# 🔴 2026-09-26 补：Windows 管道/重定向下 stdout 回落 GBK，emoji 一打印就崩；与 self_model.py 同一款补丁
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


WS = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_GLB = WS / "holo_pet/assets/digital-human/raw/phase2a-lowpoly-glb/tripo-out/gbt-tpose-lowpoly-glb-convert-16d8db89/model.glb"
REF = WS / "holo_pet/assets/digital-human/raw/phase2a-tpose/T-pose参考-规范化.png"
GLB = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else DEFAULT_GLB
OK_FILE = WS / ".digihuman/S2-human-ok.json"
FIVE = ["双臂水平", "双腿直立", "正面全身", "无遮挡物", "白底"]


def positions(p: pathlib.Path):
    import numpy as np
    raw = p.read_bytes()
    jl, = struct.unpack_from("<I", raw, 12)
    J = json.loads(raw[20:20 + jl].decode("utf-8"))
    off = 20 + jl + ((-jl) % 4)
    bl, = struct.unpack_from("<I", raw, off)
    BIN = raw[off + 8: off + 8 + bl]
    a = J["accessors"][J["meshes"][0]["primitives"][0]["attributes"]["POSITION"]]
    bv = J["bufferViews"][a["bufferView"]]
    return np.frombuffer(BIN, np.float32, a["count"] * 3, bv.get("byteOffset", 0)).reshape(-1, 3).astype("float32")


def proxies():
    """机器代理读数（**仅提示**：源码把判定权交给人工复核）。"""
    import numpy as np
    out = {}
    if GLB.exists():
        P = positions(GLB)
        y0, y1 = float(P[:, 1].min()), float(P[:, 1].max())
        H = max(1e-6, y1 - y0)
        span = float(max(P[:, 0].max() - P[:, 0].min(), P[:, 2].max() - P[:, 2].min()))
        out["臂展/身高（源码口径：≈身高）"] = f"{span/H:.2f}（高 {H:.3f}）"
        lo = P[P[:, 1] <= y0 + H * 0.33]
        mid = P[(P[:, 1] > y0 + H * 0.33) & (P[:, 1] <= y0 + H * 0.66)]
        w = lambda q: float(max(q[:, 0].max() - q[:, 0].min(), q[:, 2].max() - q[:, 2].min())) if len(q) else 0.0
        out["下/中段水平半宽（腿细于躯干）"] = f"{w(lo):.3f}/{w(mid):.3f}"
    if REF.exists():
        try:
            from PIL import Image
            im = np.asarray(Image.open(REF).convert("RGB"), dtype="float32")
            b = np.concatenate([im[:6].reshape(-1, 3), im[-6:].reshape(-1, 3),
                                im[:, :6].reshape(-1, 3), im[:, -6:].reshape(-1, 3)])
            out["白底（边缘亮度/饱和）"] = f"{b.mean():.0f} / {(b.max(axis=1)-b.min(axis=1)).mean():.1f}"
        except Exception as e:
            out["白底"] = f"读图失败 {type(e).__name__}"
    return out


def main():
    if "--confirm" in sys.argv:
        who = sys.argv[sys.argv.index("--confirm") + 1] if len(sys.argv) > sys.argv.index("--confirm") + 1 else "unknown"
        OK_FILE.parent.mkdir(parents=True, exist_ok=True)
        OK_FILE.write_text(json.dumps({
            "confirmed_by": who, "at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "artifact": str(REF.relative_to(WS)) if REF.exists() else None,
            "five": FIVE, "note": "人工复核：打开规范化图逐条看过（源码 run-pipeline.ps1:73 要求）",
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"已落人工确认记录 → {OK_FILE.relative_to(WS)}（复核人 {who}）")
        return 0

    print("S2 姿态门（源码口径：五条判据 **必做人工复核**；机器只给代理读数，不单独判过）")
    for k, v in proxies().items():
        print(f"  · 代理读数 {k}  {v}")
    print(f"  待人工复核图: {REF.relative_to(WS) if REF.exists() else '（缺图）'}")
    print("  五条判据: " + " / ".join(FIVE))

    if not OK_FILE.exists():
        print("S2 门: ⏳ 待人工确认 —— 打开上图逐条看过，然后：")
        print('        python tools/digihuman/tpose-check.py --confirm "<复核人>"')
        return 1
    rec = json.loads(OK_FILE.read_text(encoding="utf-8"))
    print(f"S2 门: ✅ 人工已复核（{rec.get('confirmed_by')} @ {rec.get('at')}）· 五条 = {' / '.join(rec.get('five', FIVE))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
