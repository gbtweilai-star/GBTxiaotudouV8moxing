# -*- coding: utf-8 -*-
import pathlib, json
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\outputs\数字人语音助手")
PROTO = (ROOT / "V1 数字人语音助手-可交互原型.html").as_uri()
OUT = ROOT / ".qa"

JS = r"""
() => {
  const r = (sel) => { const e = document.querySelector(sel); if(!e) return null;
    const b = e.getBoundingClientRect(); return [Math.round(b.x), Math.round(b.y), Math.round(b.width), Math.round(b.height)]; };
  const pts = [[220,450],[205,500],[185,550],[168,575],[140,300],[240,300]];
  const hits = pts.map(([x,y]) => {
    const e = document.elementFromPoint(x,y);
    return [x, y, e ? (e.tagName + '.' + (e.getAttribute('class')||'')) : 'null'];
  });
  return {
    holo: r('#screen-intro .holo'),
    svg: r('#screen-intro .holo svg'),
    floor: r('#screen-intro .holo__floor'),
    wave: r('#screen-intro .wave'),
    subtitle: r('#screen-intro .subtitle'),
    stage: r('#screen-intro .intro__stage'),
    hits: hits
  };
}
"""

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3)
    pg = ctx.new_page()
    pg.goto(PROTO, wait_until="networkidle")
    pg.fill("#in-url", "https://api.your-service.com/v1")
    pg.fill("#in-key", "sk-4f2a9c77e1b08d")
    pg.click("#btn-connect")
    pg.wait_for_timeout(1400)
    pg.click("#screen-enter")
    pg.wait_for_timeout(1100)
    print(json.dumps(pg.evaluate(JS), ensure_ascii=False, indent=1))
    pg.screenshot(path=str(OUT / "pr5-full.png"))
    pg.locator("#screen-intro .holo").screenshot(path=str(OUT / "pr5-holo.png"))
    ctx.close()
    b.close()
