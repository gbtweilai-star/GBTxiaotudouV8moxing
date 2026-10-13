# -*- coding: utf-8 -*-
"""渲染自检：把原型与画布用 Playwright 真跑一遍并出图。"""
import sys, pathlib, time
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\outputs\数字人语音助手")
OUT = ROOT / ".qa"
OUT.mkdir(exist_ok=True)

PROTO = (ROOT / "V1 数字人语音助手-可交互原型.html").as_uri()
CANVAS = (ROOT / "V1 数字人语音助手-无限画布.html").as_uri()

errors = []


def shoot_proto(pw):
    b = pw.chromium.launch(channel="chrome")
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.on("console", lambda m: errors.append(("console", m.type, m.text)) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append(("pageerror", str(e))))
    pg.goto(PROTO, wait_until="networkidle")
    pg.wait_for_timeout(700)
    pg.screenshot(path=str(OUT / "p01-key-empty.png"))

    # 校验失败态
    pg.click("#demo-fail")
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "p02-key-error.png"))

    # 正常填完 -> 校验 -> 黑屏
    pg.fill("#in-url", "https://api.your-service.com/v1")
    pg.fill("#in-key", "sk-4f2a9c77e1b08d")
    pg.wait_for_timeout(150)
    pg.screenshot(path=str(OUT / "p03-key-filled.png"))
    pg.click("#btn-connect")
    pg.wait_for_timeout(600)
    pg.screenshot(path=str(OUT / "p04-blackout.png"))

    # 出场
    pg.wait_for_timeout(1400)
    pg.screenshot(path=str(OUT / "p05-entrance.png"))
    pg.wait_for_timeout(900)
    pg.screenshot(path=str(OUT / "p06-entrance-late.png"))

    # 自我介绍
    pg.wait_for_timeout(2600)
    pg.screenshot(path=str(OUT / "p07-intro.png"))

    # 首页
    pg.click("#btn-go-home")
    pg.wait_for_timeout(700)
    pg.screenshot(path=str(OUT / "p08-home-idle.png"))

    # 聆听 / 回应
    box = pg.locator("#mic").bounding_box()
    pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    pg.mouse.down()
    pg.wait_for_timeout(260)
    pg.screenshot(path=str(OUT / "p09-home-listen.png"))
    pg.mouse.up()
    pg.wait_for_timeout(1400)
    pg.screenshot(path=str(OUT / "p10-home-speak.png"))

    # 对话流四态
    pg.wait_for_timeout(3200)
    pg.click('#seg-state button[data-state="loading"]')
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "p11-state-loading.png"))
    pg.click('#seg-state button[data-state="empty"]')
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "p12-state-empty.png"))
    pg.click('#seg-state button[data-state="error"]')
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "p13-state-error.png"))
    pg.click('#seg-state button[data-state="populated"]')

    # 设置页 + 悬浮数字人
    pg.click('#dock button[data-nav="settings"]')
    pg.wait_for_timeout(400)
    pg.click("#orb")
    pg.wait_for_timeout(500)
    pg.screenshot(path=str(OUT / "p14-settings-orb.png"))

    ctx.close()
    b.close()


def shoot_canvas(pw):
    b = pw.chromium.launch(channel="chrome")
    ctx = b.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
    pg = ctx.new_page()
    pg.on("pageerror", lambda e: errors.append(("canvas-pageerror", str(e))))
    pg.goto(CANVAS, wait_until="networkidle")
    pg.wait_for_timeout(900)
    pg.screenshot(path=str(OUT / "c01-canvas-overview.png"))
    pg.evaluate("document.getElementById('zoom-reset').click()")
    pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "c02-canvas-row12.png"))
    pg.click('[data-jump="row3"]')
    pg.wait_for_timeout(400)
    pg.screenshot(path=str(OUT / "c03-canvas-row3.png"))
    pg.screenshot(path=str(OUT / "c04-canvas-row3-full.png"), full_page=False)
    ctx.close()
    b.close()


with sync_playwright() as pw:
    shoot_proto(pw)
    shoot_canvas(pw)

print("ERRORS:", len(errors))
for e in errors[:20]:
    print(" -", e)
