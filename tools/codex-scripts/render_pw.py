# -*- coding: utf-8 -*-
"""用 Playwright 驱动系统 Chrome，真渲染交付件并截图（不是合成样张）。"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / ".scratch" / "render"
OUT.mkdir(exist_ok=True)

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
targets = [
    ("proto", BASE / "V17 GBT小土豆V8-可交互原型.html", 1680, 1050),
    ("canvas", BASE / "V17 GBT小土豆V8-无限画布.html", 1680, 1050),
]

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        executable_path=CHROME,
        headless=True,
        args=["--hide-scrollbars", "--force-device-scale-factor=2", "--allow-file-access-from-files"],
    )
    for name, path, w, h in targets:
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
        page.on("console", lambda m: print("   [console:%s] %s" % (m.type, m.text[:120])))
        page.on("pageerror", lambda e: print("   [pageerror] %s" % str(e)[:200]))
        page.goto(path.as_uri(), wait_until="load", timeout=60000)
        page.wait_for_timeout(3500)
        shot = OUT / ("%s.png" % name)
        page.screenshot(path=str(shot))
        print("✓ %-8s %8d B  %s" % (name, shot.stat().st_size, shot.name))
        page.close()
    browser.close()
