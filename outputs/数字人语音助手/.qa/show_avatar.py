# -*- coding: utf-8 -*-
"""把数字人形象单独拎出来放大出图，方便当面看。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\outputs\数字人语音助手")
PROTO = (ROOT / "V1 数字人语音助手-可交互原型.html").as_uri()
OUT = ROOT / ".qa"

BIG = r"""
() => {
  const d = document.createElement('div');
  d.id = 'avatar-stage';
  d.style.cssText = 'position:fixed;inset:0;z-index:9999;background:#05070d;display:grid;place-items:center';
  d.innerHTML = `
    <div style="position:relative;width:520px;height:780px">
      <div style="position:absolute;left:50%;bottom:74px;width:340px;height:52px;margin-left:-170px;border-radius:50%;
                  background:radial-gradient(ellipse,rgba(0,212,255,.42),transparent 70%)"></div>
      <svg viewBox="0 0 200 300" width="520" height="780" style="position:relative;overflow:visible;
           filter:drop-shadow(0 0 26px rgba(0,212,255,.34))">
        <use href="#holoFigure"/><use href="#holoFigureScan"/>
      </svg>
    </div>`;
  document.body.appendChild(d);
}
"""

LADDER = r"""
() => {
  const mk = (w, h, label) => {
    const box = document.createElement('div');
    box.style.cssText = 'display:flex;flex-direction:column;align-items:center;gap:16px';
    const fig = document.createElement('div');
    fig.style.cssText = 'position:relative;width:' + w + 'px;height:' + h + 'px';
    fig.innerHTML = `
      <div style="position:absolute;left:50%;bottom:6%;width:66%;height:9%;margin-left:-33%;border-radius:50%;
                  background:radial-gradient(ellipse,rgba(0,212,255,.4),transparent 70%)"></div>
      <svg viewBox="0 0 200 300" width="${w}" height="${h}" style="position:relative;overflow:visible;
           filter:drop-shadow(0 0 ${Math.round(w / 14)}px rgba(0,212,255,.32))">
        <use href="#holoFigure"/><use href="#holoFigureScan"/>
      </svg>`;
    const cap = document.createElement('span');
    cap.textContent = label;
    cap.style.cssText = 'font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.08em;color:#4A6080';
    box.append(fig, cap);
    return box;
  };
  const d = document.createElement('div');
  d.style.cssText = 'position:fixed;inset:0;z-index:9999;background:#05070d;display:flex;align-items:center;' +
                    'justify-content:center;gap:64px;padding:60px';
  d.append(
    mk(110, 165, 'SM 110x165'),
    mk(180, 270, 'MD 180x270'),
    mk(300, 450, 'LG 300x450')
  );
  document.body.appendChild(d);
}
"""


with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    ctx = b.new_context(viewport={"width": 760, "height": 900}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.goto(PROTO, wait_until="networkidle")
    pg.wait_for_timeout(600)

    pg.evaluate(BIG)
    pg.wait_for_timeout(500)
    pg.locator("#avatar-stage").screenshot(path=str(OUT / "avatar-big.png"))

    pg.evaluate("document.getElementById('avatar-stage').remove()")
    pg.evaluate(LADDER)
    pg.wait_for_timeout(500)
    pg.screenshot(path=str(OUT / "avatar-ladder.png"))

    ctx.close()
    b.close()
print("ok")
