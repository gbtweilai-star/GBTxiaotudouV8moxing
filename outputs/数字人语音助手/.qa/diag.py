# -*- coding: utf-8 -*-
import pathlib, json
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\outputs\数字人语音助手")
PROTO = (ROOT / "V1 数字人语音助手-可交互原型.html").as_uri()

JS = r"""
() => {
  const out = {};
  const g = document.getElementById('holoFigure');
  out.figureFound = !!g;
  out.figureBox = g ? g.getBoundingClientRect().toJSON() : null;
  out.uses = [...document.querySelectorAll('use')].map(u => ({
    href: u.getAttribute('href'),
    box: u.getBoundingClientRect().toJSON(),
    svgBox: u.ownerSVGElement.getBoundingClientRect().toJSON(),
    screen: u.closest('.screen') ? u.closest('.screen').id : 'none'
  }));
  const holo = document.querySelector('#screen-home .holo');
  out.homeHoloBox = holo.getBoundingClientRect().toJSON();
  out.homeHoloCS = { w: getComputedStyle(holo).width, h: getComputedStyle(holo).height };
  const svg = holo.querySelector('svg');
  out.homeSvgBox = svg.getBoundingClientRect().toJSON();
  out.homeSvgCS = { w: getComputedStyle(svg).width, h: getComputedStyle(svg).height };
  const grad = document.getElementById('holoFill');
  out.gradFound = !!grad;
  out.gradStops = grad ? grad.querySelectorAll('stop').length : 0;
  return out;
}
"""

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    pg = b.new_context(viewport={"width": 390, "height": 844}).new_page()
    pg.goto(PROTO, wait_until="networkidle")
    pg.wait_for_timeout(500)
    pg.fill("#in-url", "https://api.your-service.com/v1")
    pg.fill("#in-key", "sk-4f2a9c77e1b08d")
    pg.click("#btn-connect")
    pg.wait_for_timeout(1400)
    pg.click("#screen-enter")
    pg.wait_for_timeout(900)
    pg.click("#btn-go-home")
    pg.wait_for_timeout(600)
    d = pg.evaluate(JS)
    print("homeHoloBox:", d["homeHoloBox"])
    print("homeHoloCS :", d["homeHoloCS"])
    print("homeSvgBox :", d["homeSvgBox"])
    print("homeSvgCS  :", d["homeSvgCS"])
    print("heroBox    :", pg.locator("#screen-home .hero").bounding_box())
    for u in d["uses"]:
        print("use", u["screen"], u["href"], u["box"]["width"], "x", u["box"]["height"])
    print("firstPathFill:", pg.evaluate(
        "() => { const p = document.querySelector('#screen-home .holo svg use'); "
        "return p ? getComputedStyle(p).display + ' / ' + getComputedStyle(p).fill : 'no-use'; }"))
    pg.locator("#screen-home .hero").screenshot(path=str(ROOT / ".qa" / "z-hero.png"))
    b.close()
