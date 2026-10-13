# -*- coding: utf-8 -*-
"""三档 viewport（手机 / 平板 / 桌面）渲染自检。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\outputs\数字人语音助手")
PROTO = (ROOT / "V1 数字人语音助手-可交互原型.html").as_uri()
OUT = ROOT / ".qa"

SIZES = {
    "phone": {"width": 390, "height": 844},
    "tablet": {"width": 834, "height": 1112},
    "desktop": {"width": 1440, "height": 900},
}

errors = []

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    for name, vp in SIZES.items():
        ctx = b.new_context(viewport=vp, device_scale_factor=1)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append((name, str(e))))
        pg.goto(PROTO, wait_until="networkidle")
        pg.wait_for_timeout(500)
        pg.fill("#in-url", "https://api.your-service.com/v1")
        pg.fill("#in-key", "sk-4f2a9c77e1b08d")
        pg.click("#btn-connect")
        pg.wait_for_timeout(1500)
        pg.click("#screen-enter")
        pg.wait_for_timeout(800)
        pg.click("#btn-go-home")
        pg.wait_for_timeout(700)
        pg.screenshot(path=str(OUT / ("r-" + name + "-home.png")))
        ctx.close()
    b.close()

print("ERRORS:", errors)
