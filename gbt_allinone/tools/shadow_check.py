# -*- coding: utf-8 -*-
"""影子检查器 · 常驻防线（**只读**）。

判据来源：O49（家根影子大扫）+《影子大扫方案稿》第八条。
规则：**工作区根**存在与 `gbt_allinone/` 同名的 `*.py`，或与 `gbt_allinone/<name>/` 同名的子目录 -> 报红。
`__pycache__` **单列**，不计入红（字节码缓存不是影子模块）。

用法：
    py -3.10 gbt_allinone/tools/shadow_check.py [--root <dir>] [--pkg <dir>] [--json]
退出码：0 = 绿（无影子）· 1 = 红（有影子）· 2 = 参数错。

供门禁复用：`from gbt_allinone.tools.shadow_check import shadow_report`
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "gbt_allinone"


def shadow_report(root: Path | str = ROOT, pkg: Path | str = PKG) -> dict:
    """只读扫描：返回根级影子清单。不做任何写盘。"""
    root = Path(root).resolve()
    pkg = Path(pkg).resolve()
    pkg_py = {p.name for p in pkg.glob("*.py")}
    pkg_dirs = {p.name for p in pkg.iterdir() if p.is_dir()}

    shadow_files = sorted(p.name for p in root.glob("*.py") if p.name in pkg_py)
    shadow_dirs, cache_dirs = [], []
    for p in sorted(x for x in root.iterdir() if x.is_dir()):
        if p.name not in pkg_dirs:
            continue
        (cache_dirs if p.name == "__pycache__" else shadow_dirs).append(p.name)
    red = len(shadow_files) + len(shadow_dirs)
    return {
        "root": str(root),
        "pkg": str(pkg),
        "shadow_files": shadow_files,
        "shadow_dirs": shadow_dirs,
        "cache_dirs": cache_dirs,
        "pkg_py_total": len(pkg_py),
        "red": red,
        "ok": red == 0,
        "verdict": "GREEN" if red == 0 else "RED_SHADOW_PRESENT",
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="家根影子检查器（只读）")
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--pkg", default=str(PKG))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        rep = shadow_report(a.root, a.pkg)
    except Exception as e:
        print("shadow_check: 参数/路径错误：%s" % e)
        return 2
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print("root  :", rep["root"])
        print("verdict:", rep["verdict"], "(red=%d)" % rep["red"])
        if rep["shadow_files"]:
            print("  同名 .py :", ", ".join(rep["shadow_files"]))
        if rep["shadow_dirs"]:
            print("  同名子目录:", ", ".join(rep["shadow_dirs"]))
        if rep["cache_dirs"]:
            print("  单列(不入红):", ", ".join(rep["cache_dirs"]))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

# 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
