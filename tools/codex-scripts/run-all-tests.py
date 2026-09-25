#!/usr/bin/env python
# gbt-capability: subprocess
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""run-all-tests.py —— 全仓测试**普查**（不是抽样）。

为什么要有它
------------
2026-09-25 排雷时发现：仓里长期存在**红着的判据没人管**（`test_false_report_audit.py`
因为两条行号锚失效而长期 FAILED，而处置方法就写在被审计文件自己的注释里）。
零散跑十几个文件看不出全貌 —— 必须**全量跑一遍，把所有红收上来**，
再逐个归因（是我改坏的？还是老账？），否则"自检全过"这句话永远没有依据。

做法
----
逐个 `test_*.py` 直接跑（本仓口径：`python -m unittest` 在绑生产 store 时会拒绝，
所以**逐个文件直跑**），每个文件独立进程 + 独立超时，互不污染。

产出
----
* 屏幕：一行一文件的 通过/失败/超时 + 末尾汇总
* `--json out.json`：完整明细（含每个失败用例名），供后续归因

用法
----
    python tools/codex-scripts/run-all-tests.py                 # 全量
    python tools/codex-scripts/run-all-tests.py --filter contract
    python tools/codex-scripts/run-all-tests.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / "gbt_allinone" / "tests"
PY = sys.executable


def run_one(path: Path, timeout: float, env: dict) -> dict:
    t0 = time.time()
    try:
        p = subprocess.run([PY, str(path)], cwd=str(ROOT), env=env,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"file": path.name, "result": "TIMEOUT", "ran": None,
                "secs": round(time.time() - t0, 1), "fails": [], "tail": ""}
    out = (p.stdout or "") + (p.stderr or "")
    ran = None
    m = re.search(r"Ran (\d+) tests?", out)
    if m:
        ran = int(m.group(1))
    if re.search(r"(?m)^OK", out):
        res = "OK"
    elif re.search(r"(?m)^FAILED", out):
        res = "FAILED"
    elif p.returncode != 0:
        res = "ERROR"
    else:
        res = "?"
    fails = re.findall(r"(?m)^(?:FAIL|ERROR): (\S+)", out)
    return {"file": path.name, "result": res, "ran": ran,
            "secs": round(time.time() - t0, 1), "fails": fails[:20],
            "tail": "\n".join(out.strip().splitlines()[-4:])[:400]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", default=None, help="只跑文件名含该子串的")
    ap.add_argument("--timeout", type=float, default=300.0, help="单文件超时秒数")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    env = dict(os.environ)
    # 本仓口径：必须隔离 store（否则测试包守卫会拒绝，或写脏生产）
    env.setdefault("GBT_STORE_DIR", str(ROOT / ".scratch" / "alltests-store"))
    env.setdefault("PYTHONIOENCODING", "utf-8")

    files = sorted(TESTS.glob("test_*.py"))
    if args.filter:
        files = [f for f in files if args.filter in f.name]
    print("全量普查：%d 个测试文件（单文件超时 %.0fs，store=%s）"
          % (len(files), args.timeout, env["GBT_STORE_DIR"]))
    print()

    rows = []
    t_all = time.time()
    for i, f in enumerate(files, 1):
        r = run_one(f, args.timeout, env)
        rows.append(r)
        flag = {"OK": "✅", "FAILED": "❌", "ERROR": "❌", "TIMEOUT": "⏰", "?": "?"}[r["result"]]
        print("%3d/%d %s %-46s ran=%-4s %5.1fs %s"
              % (i, len(files), flag, r["file"], r["ran"], r["secs"],
                 ("失败 %d 个: %s" % (len(r["fails"]), ", ".join(r["fails"][:3]))) if r["fails"] else ""))

    ok = [r for r in rows if r["result"] == "OK"]
    bad = [r for r in rows if r["result"] != "OK"]
    print()
    print("=" * 78)
    print("通过 %d / %d ；未过 %d 个（用时 %.1f 分钟）"
          % (len(ok), len(rows), len(bad), (time.time() - t_all) / 60))
    if bad:
        print()
        print("未过清单：")
        for r in bad:
            print("  [%s] %-46s ran=%-4s" % (r["result"], r["file"], r["ran"]))
            for x in r["fails"][:6]:
                print("        · %s" % x)
    if args.json:
        Path(args.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
        print()
        print("明细已写", args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
