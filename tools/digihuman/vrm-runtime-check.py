# -*- coding: utf-8 -*-
"""S10b/S11 运行时门：用 **three-vrm 官方实现**加载 avatar.vrm，读它自己算出的 humanoid/expressions/springBone。

    python tools/digihuman/vrm-runtime-check.py [vrm路径]

判据：官方实现能读出 ≥15 根 humanoid 骨 ⇒ 我们的 VRM 合规（比自写检查强得多）。
需要本地服务（8788）在跑：node plugins/gbt-master/tools/serve-digital-human.mjs
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import sys

# 🔴 2026-09-26 补：Windows 管道/重定向下 stdout 回落 GBK，emoji 一打印就崩；与 self_model.py 同一款补丁
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


WS = pathlib.Path(__file__).resolve().parents[2]
PAGE = "/holo_pet/assets/digital-human/web/vrm-runtime-check.html"   # 必须在白名单目录（tools/ 被路由 DENY）
VRM = sys.argv[1] if len(sys.argv) > 1 else "/gbt-master/fs/holo_pet/assets/digital-human/raw/rig/avatar.vrm"
BASE = "http://127.0.0.1:3080/gbt-master/fs"


def _find_chrome() -> str:
    """🔴 2026-09-26 自纠：原来写死 x64 Program Files 一条路 —— Chrome 装在用户目录/x86 时
    launch 直接炸。现按 环境变量 → PATH → 三个常见落点 找；都找不到返回空串
    （回落 Playwright 自带内核，不硬性要求装 Chrome）。"""
    cands = [os.environ.get("GBT_CHROME_PATH") or "", shutil.which("chrome") or "",
             shutil.which("chromium") or "",
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
             str(pathlib.Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "Application" / "chrome.exe")]
    return next((c for c in cands if c and pathlib.Path(c).is_file()), "")


def main():
    from playwright.sync_api import sync_playwright
    url = f"{BASE}{PAGE}?vrm={VRM}"
    chrome = _find_chrome()
    kw = {"headless": True,
          "args": ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"]}
    if chrome:
        kw["executable_path"] = chrome
    with sync_playwright() as pw:
        b = pw.chromium.launch(**kw)
        pg = b.new_page(viewport={"width": 760, "height": 720})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.on("console", lambda m: errs.append("console:" + m.text[:160]) if m.type == "error" else None)
        pg.goto(url, wait_until="load", timeout=60000)
        rep = None
        try:
            pg.wait_for_function("() => window.__vrmReport !== undefined", timeout=90000)
            rep = pg.evaluate("() => window.__vrmReport")
        except Exception as e:
            errs.append("wait:" + str(e)[:80])
        painted = pg.evaluate("() => document.querySelector('canvas')?.dataset.painted")
        pg.screenshot(path=str(WS / "render/VRM-运行时验收.png"))
        b.close()
    ok = bool(rep and rep.get("ok"))
    print(f"运行时门: {'✅' if ok else '❌'} " + (json.dumps(rep, ensure_ascii=False) if rep else "无读数"))
    if errs:
        print("  问题: " + " | ".join(errs[:3]))
    print(f"  画面已绘制: {painted} · 截图 render/VRM-运行时验收.png")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
