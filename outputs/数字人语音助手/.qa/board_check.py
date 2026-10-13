# -*- coding: utf-8 -*-
"""检查形象看板页：图有没有断、有没有报错，并出一张整页图。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\outputs\数字人语音助手")
PAGE = (ROOT / "形象候选" / "看板.html").as_uri()

errs = []
with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    pg = b.new_context(viewport={"width": 1200, "height": 900}).new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(PAGE, wait_until="networkidle")
    pg.wait_for_timeout(1200)
    bad = pg.evaluate(
        "() => [...document.images]"
        ".filter(i => !i.complete || i.naturalWidth === 0)"
        ".map(i => i.getAttribute('src'))"
    )
    print("broken images:", bad)
    pg.screenshot(path=str(ROOT / ".qa" / "board-check.png"), full_page=True)
    b.close()
print("pageerrors:", errs)
