# -*- coding: utf-8 -*-
"""GBT小土豆V8 · 甲方案镜像排练驱动器（**可复跑**，六步按序真跑、逐步贴原文）。

按主人令的顺序跑，**任何一步红就停在那一步**（不跳过、不继续）：

    ① mirror_shape   ×N（把 plugins/dsh-mcp-bridge/* 成形进镜像维度；现实无感知）
    ② mirror_scan    维度体检（完整性/署名/纪律/入口）
    ③ mirror_plan    写下排练计划（假设/架构/步骤/服务与环境契约/验收/回滚）
    ④ mirror_simulate 静态推演（文件/依赖图/入口/契约/闭环）
    ⑤ mirror_parity  沙盒与生产环境契约一致性
    ⑥ mirror_rehearse 生产前排练（沙盒里真跑 selfcheck）

🔴 铁律（写死在本文件的代码里，不靠记性）：
  · 本驱动器**永不**调用 `mirror_ascend` / `mirror_release` / `pipeline_submit`
    （它们要 `deploy_publish` 一次性票，票在主人手上）；
  · 一切调用都走 `gbt_allinone.run_task` 唯一门（不直接 import 模块函数绕门）；
  · 不设 `GBT_OWNER_SESSION`：要票的动作走真票闸，用了票由框架自己记账。

用法：
    py -3.14 plugins/dsh-mcp-bridge/rehearse.py                 # 全跑（含成形）
    py -3.14 plugins/dsh-mcp-bridge/rehearse.py --no-shape      # 只跑六步里的②③④⑤⑥
    py -3.14 plugins/dsh-mcp-bridge/rehearse.py --out <文件>    # 落一份全文读数（默认 .scratch/…）

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
SHAPE_FILES = ("server.py", "selfcheck.py", "interop-check.mjs", "rehearsal-plan.json",
               "rehearse.py", "README.md")
PLAN_NAME = "dsh-mcp-bridge"
FORBIDDEN_KINDS = ("mirror_ascend", "mirror_release", "pipeline_submit", "one_key_deploy")

ROOT = None
for cand in [HERE, *HERE.parents]:
    if (cand / "gbt_allinone" / "__init__.py").is_file():
        ROOT = cand
        break
if ROOT is None:
    print("✗ 找不到仓根（gbt_allinone/__init__.py）")
    sys.exit(2)
sys.path.insert(0, str(ROOT))

from gbt_allinone import api  # noqa: E402


def cap(kind, payload=None):
    """走唯一门。**显式拒绝**任何晋升类 kind（防将来有人手滑加进来）。"""
    if kind in FORBIDDEN_KINDS:
        raise SystemExit("🔴 本驱动器禁止调用 %s（要 deploy_publish 一次性票，票在主人手上）" % kind)
    t0 = time.time()
    out = api.run_task(kind, payload or {}, safe=True)
    return out, round((time.time() - t0) * 1000.0, 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="甲方案镜像排练驱动器（六步）")
    ap.add_argument("--no-shape", action="store_true", help="跳过①成形，直接②③④⑤⑥")
    ap.add_argument("--out", default=str(ROOT / ".scratch" / "mcp-bridge-rehearsal.json"))
    a = ap.parse_args(argv)

    transcript = {"started": time.strftime("%Y-%m-%dT%H:%M:%S"), "steps": []}
    red_at = None

    def record(label, kind, payload, out, ms):
        transcript["steps"].append({"label": label, "kind": kind, "payload": payload,
                                    "ms": ms, "out": out})

    # ① mirror_shape ×N
    if not a.no_shape:
        shapes = []
        for name in SHAPE_FILES:
            p = HERE / name
            if not p.is_file():
                print("✗ 缺件：%s" % p)
                return 3
            payload = {"path": "plugins/dsh-mcp-bridge/%s" % name,
                       "content": p.read_text(encoding="utf-8"),
                       "note": "甲方案 DSH MCP 桥 · 仓内件成形"}
            out, ms = cap("mirror_shape", payload)
            shapes.append((name, out, ms))
            print("① mirror_shape %-20s -> %s" % (
                name, json.dumps(out.get("result") or out, ensure_ascii=False)))
        record("① mirror_shape ×%d" % len(SHAPE_FILES), "mirror_shape",
               {"paths": ["plugins/dsh-mcp-bridge/%s" % n for n in SHAPE_FILES]},
               {n: o.get("result") or o for n, o, _ in shapes}, None)

    steps = [
        ("② mirror_status", "mirror_status", {}),
        ("③ mirror_scan", "mirror_scan", {}),
        ("④ mirror_plan", "mirror_plan", {"name": PLAN_NAME,
                                          "plan": json.loads((HERE / "rehearsal-plan.json").read_text(encoding="utf-8"))}),
        ("⑤ mirror_simulate", "mirror_simulate", {"name": PLAN_NAME}),
        ("⑥ mirror_parity", "mirror_parity", {"name": PLAN_NAME}),
        ("⑦ mirror_rehearse", "mirror_rehearse", {"name": PLAN_NAME, "execute": True}),
    ]
    for label, kind, payload in steps:
        out, ms = cap(kind, payload)
        # 判红口径（首跑踩出来的，写死在这里）：唯一门是**两层信封** ——
        #   envelope = {ok, status, kind, result:{status, kind, result:<能力载荷>}}
        # 判据：envelope.ok 为真 **且** 能力载荷里没有显式的 ok=false。
        # 只判"能力载荷的 ok"会把 mirror_status/mirror_scan 这类"没有 ok 字段就当红"误判；
        # 只判信封又会漏掉"门放行但能力自报 ok=false"。两层都判才算稳。
        env_ok = bool(out.get("ok"))
        layer1 = out.get("result") if isinstance(out.get("result"), dict) else {}
        payload1 = layer1.get("result") if isinstance(layer1.get("result"), dict) else {}
        inner_ok = payload1.get("ok") if isinstance(payload1, dict) and "ok" in payload1 else None
        ok = env_ok and (inner_ok is not False)
        print("\n──── %s（%.1f ms）· 信封ok=%s 能力载荷ok=%s ────" % (label, ms, env_ok, inner_ok))
        print(json.dumps(layer1 or out, ensure_ascii=False, indent=1)[:4000])
        record(label, kind, payload, layer1 or out, ms)
        if not ok:
            red_at = label
            print("\n🔴 %s 判红 —— 按纪律**停在这一步**，不再往下跑。" % label)
            break
    transcript["ended"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    transcript["red_at"] = red_at
    transcript["verdict"] = "全绿" if red_at is None else ("红在 %s" % red_at)
    out_path = Path(a.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n== 结论：%s ==\n全文读数：%s" % (transcript["verdict"], out_path))
    return 0 if red_at is None else 1


if __name__ == "__main__":
    sys.exit(main())
