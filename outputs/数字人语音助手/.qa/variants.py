# -*- coding: utf-8 -*-
"""数字人形象三个方向对比出图（A 现版胸像 / B 带手臂剪影 / C 线框面孔）。"""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\outputs\数字人语音助手")
PROTO = (ROOT / "V1 数字人语音助手-可交互原型.html").as_uri()
OUT = ROOT / ".qa"

BODY_B = ("M100 78 C 86 78 74 82 66 92 C 58 102 55 112 56 124 "
          "C 57 148 63 168 63 192 C 63 218 61 246 62 272 "
          "L 138 272 C 139 246 137 218 137 192 "
          "C 137 168 143 148 144 124 C 145 112 142 102 134 92 "
          "C 126 82 114 78 100 78 Z")

ARM_L = ("M62 100 C 52 114 46 134 44 156 C 42 180 42 206 43 232 "
         "C 43 248 44 262 45 274 L 57 274 "
         "C 56 262 55 248 55 232 C 54 206 54 180 56 158 "
         "C 58 138 62 122 68 108 Z")

ARM_R = ("M138 100 C 148 114 154 134 156 156 C 158 180 158 206 157 232 "
         "C 157 248 156 262 155 274 L 143 274 "
         "C 144 262 145 248 145 232 C 146 206 146 180 144 158 "
         "C 142 138 138 122 132 108 Z")

FACE = ("M100 18 C 124 18 140 38 140 62 C 140 78 136 92 128 102 "
        "C 119 113 110 118 100 118 C 90 118 81 113 72 102 "
        "C 64 92 60 78 60 62 C 60 38 76 18 100 18 Z")

SKULL = "M60 60 C 60 30 78 14 100 14 C 122 14 140 30 140 60"
BROW_L = "M74 60 C 80 55 90 55 96 60"
BROW_R = "M104 60 C 110 55 120 55 126 60"
EYE_L = "M76 70 C 81 65 89 65 94 70 C 89 75 81 75 76 70 Z"
EYE_R = "M106 70 C 111 65 119 65 124 70 C 119 75 111 75 106 70 Z"
NOSE = "M100 68 L100 86 C 100 90 97 92 94 92 M100 86 C 100 90 103 92 106 92"
LIPS = "M88 100 C 94 96 106 96 112 100 C 106 105 94 105 88 100 Z"
JAW = "M74 96 C 80 110 89 116 100 116 C 111 116 120 110 126 96"
EAR_L = "M60 66 C 55 66 53 72 54 78 C 55 84 58 86 60 86"
EAR_R = "M140 66 C 145 66 147 72 146 78 C 145 84 142 86 140 86"
NECK = "M88 116 L87 134 M112 116 L113 134"
SHOULDER = ("M84 144 C 66 150 52 160 45 176 C 39 190 37 206 36 224 L 34 300 "
            "L 166 300 L 164 224 C 163 206 161 190 155 176 "
            "C 148 160 134 150 116 144")

PANEL = """
<div class="pv">
  <div class="pv__fig">
    <div class="pv__floor"></div>
    {svg}
  </div>
  <div class="pv__cap"><b>{tag}</b><span>{name}</span><em>{note}</em></div>
</div>
"""

A_SVG = '<svg viewBox="0 0 200 300" class="pv__svg"><use href="#holoFigure"/><use href="#holoFigureScan"/></svg>'

B_SVG = (
    '<svg viewBox="0 0 200 300" class="pv__svg">'
    '<g mask="url(#holoMask)">'
    '<ellipse cx="100" cy="44" rx="20" ry="24" fill="url(#holoFill)" stroke="url(#holoEdge)" stroke-width="1.3"/>'
    '<path d="M91 62 L109 62 L111 84 L89 84 Z" fill="url(#holoFill)" stroke="url(#holoEdge)" stroke-width="1.2"/>'
    f'<path d="{ARM_L}" fill="url(#holoFill)" stroke="url(#holoEdge)" stroke-width="1.2"/>'
    f'<path d="{ARM_R}" fill="url(#holoFill)" stroke="url(#holoEdge)" stroke-width="1.2"/>'
    f'<path d="{BODY_B}" fill="url(#holoFill)" stroke="url(#holoEdge)" stroke-width="1.3"/>'
    '</g>'
    '<g mask="url(#holoMask)" fill="url(#holoScan)" stroke="none">'
    '<ellipse cx="100" cy="44" rx="20" ry="24"/>'
    '<path d="M91 62 L109 62 L111 84 L89 84 Z"/>'
    f'<path d="{ARM_L}"/><path d="{ARM_R}"/><path d="{BODY_B}"/>'
    '</g></svg>'
)

C_SVG = (
    '<svg viewBox="0 0 200 300" class="pv__svg">'
    '<g mask="url(#holoMask)">'
    f'<path d="{SHOULDER}" fill="rgba(0,212,255,.10)" stroke="url(#holoEdge)" stroke-width="1"/>'
    f'<path d="{FACE}" fill="rgba(0,212,255,.12)" stroke="url(#holoEdge)" stroke-width="1.4"/>'
    f'<path d="{SKULL}" fill="none" stroke="url(#holoEdge)" stroke-width="1.1"/>'
    f'<path d="{EAR_L}" fill="none" stroke="url(#holoEdge)" stroke-width="1"/>'
    f'<path d="{EAR_R}" fill="none" stroke="url(#holoEdge)" stroke-width="1"/>'
    f'<path d="{BROW_L}" fill="none" stroke="url(#holoEdge)" stroke-width="1.3"/>'
    f'<path d="{BROW_R}" fill="none" stroke="url(#holoEdge)" stroke-width="1.3"/>'
    f'<path d="{EYE_L}" fill="rgba(0,212,255,.35)" stroke="url(#holoEdge)" stroke-width="1.1"/>'
    f'<path d="{EYE_R}" fill="rgba(0,212,255,.35)" stroke="url(#holoEdge)" stroke-width="1.1"/>'
    f'<path d="{NOSE}" fill="none" stroke="url(#holoEdge)" stroke-width="1"/>'
    f'<path d="{LIPS}" fill="none" stroke="url(#holoEdge)" stroke-width="1.1"/>'
    f'<path d="{JAW}" fill="none" stroke="rgba(0,212,255,.5)" stroke-width="1"/>'
    f'<path d="{NECK}" fill="none" stroke="url(#holoEdge)" stroke-width="1.2"/>'
    '</g>'
    '<g mask="url(#holoMask)" fill="url(#holoScan)" stroke="none">'
    f'<path d="{FACE}"/><path d="{SHOULDER}"/>'
    '</g></svg>'
)

JS = """
"""

BODY_D = ("M100 118 C 88 118 78 122 70 130 C 62 140 58 152 59 166 "
          "C 60 188 66 208 66 230 C 66 250 64 270 65 292 "
          "L 135 292 C 136 270 134 250 134 230 "
          "C 134 208 140 188 141 166 C 142 152 138 140 130 130 "
          "C 122 122 112 118 100 118 Z")

D_SVG = (
    '<svg viewBox="0 0 200 300" class="pv__svg">'
    '<g mask="url(#holoMask)">'
    f'<path d="{BODY_D}" fill="url(#holoFill)" stroke="url(#holoEdge)" stroke-width="1.3"/>'
    f'<g transform="translate(0,26)">'
    f'<path d="{ARM_L}" fill="url(#holoFill)" stroke="url(#holoEdge)" stroke-width="1.2"/>'
    f'<path d="{ARM_R}" fill="url(#holoFill)" stroke="url(#holoEdge)" stroke-width="1.2"/>'
    f'</g>'
    f'<path d="{FACE}" fill="rgba(0,212,255,.12)" stroke="url(#holoEdge)" stroke-width="1.4"/>'
    f'<path d="{SKULL}" fill="none" stroke="url(#holoEdge)" stroke-width="1.1"/>'
    f'<path d="{EAR_L}" fill="none" stroke="url(#holoEdge)" stroke-width="1"/>'
    f'<path d="{EAR_R}" fill="none" stroke="url(#holoEdge)" stroke-width="1"/>'
    f'<path d="{BROW_L}" fill="none" stroke="url(#holoEdge)" stroke-width="1.3"/>'
    f'<path d="{BROW_R}" fill="none" stroke="url(#holoEdge)" stroke-width="1.3"/>'
    f'<path d="{EYE_L}" fill="rgba(0,212,255,.35)" stroke="url(#holoEdge)" stroke-width="1.1"/>'
    f'<path d="{EYE_R}" fill="rgba(0,212,255,.35)" stroke="url(#holoEdge)" stroke-width="1.1"/>'
    f'<path d="{NOSE}" fill="none" stroke="url(#holoEdge)" stroke-width="1"/>'
    f'<path d="{LIPS}" fill="none" stroke="url(#holoEdge)" stroke-width="1.1"/>'
    f'<path d="{JAW}" fill="none" stroke="rgba(0,212,255,.5)" stroke-width="1"/>'
    f'<path d="{NECK}" fill="none" stroke="url(#holoEdge)" stroke-width="1.2"/>'
    '</g>'
    '<g mask="url(#holoMask)" fill="url(#holoScan)" stroke="none">'
    f'<path d="{BODY_D}"/>'
    f'<g transform="translate(0,26)"><path d="{ARM_L}"/><path d="{ARM_R}"/></g>'
    f'<path d="{FACE}"/>'
    '</g></svg>'
)

JS = """
() => {
  const style = document.createElement('style');
  style.textContent = `
    #pv-stage{position:fixed;inset:0;z-index:9999;background:#05070d;display:flex;gap:40px;
              align-items:center;justify-content:center;padding:48px 40px;font-family:"Inter",sans-serif}
    .pv{display:flex;flex-direction:column;align-items:center;gap:20px}
    .pv__fig{position:relative;width:300px;height:450px}
    .pv__svg{position:relative;width:300px;height:450px;overflow:visible;
             filter:drop-shadow(0 0 22px rgba(0,212,255,.3))}
    .pv__floor{position:absolute;left:50%;bottom:5%;width:70%;height:9%;margin-left:-35%;
               border-radius:50%;background:radial-gradient(ellipse,rgba(0,212,255,.4),transparent 70%)}
    .pv__cap{text-align:center;line-height:1.6}
    .pv__cap b{display:block;font-family:"JetBrains Mono",monospace;font-size:11px;
               letter-spacing:.1em;color:#00D4FF;text-transform:uppercase}
    .pv__cap span{display:block;font-size:14px;color:#E8F0FE;margin-top:4px}
    .pv__cap em{display:block;font-style:normal;font-size:11.5px;color:#4A6080;margin-top:2px}
  `;
  document.head.appendChild(style);
  const d = document.createElement('div');
  d.id = 'pv-stage';
  d.innerHTML = __PANELS__;
  document.body.appendChild(d);
}
"""

JS = JS.replace("__PANELS__", "`" + (
    PANEL.format(tag="A", name="现版 · 胸像", note="小尺寸够用，放大像棋子", svg=A_SVG)
    + PANEL.format(tag="B", name="带手臂的剪影", note="一眼是人，动作戏更好编", svg=B_SVG)
    + PANEL.format(tag="C", name="线框面孔", note="最像数字人，冲击最强", svg=C_SVG)
    + PANEL.format(tag="D", name="C 的头 + B 的身子", note="脸认得出人，身上有手脚", svg=D_SVG)
) + "`")

with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome")
    ctx = b.new_context(viewport={"width": 1180, "height": 720}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.goto(PROTO, wait_until="networkidle")
    pg.wait_for_timeout(600)
    pg.evaluate(JS)
    pg.wait_for_timeout(700)
    pg.screenshot(path=str(OUT / "avatar-variants.png"))
    ctx.close()
    b.close()
print("ok")
