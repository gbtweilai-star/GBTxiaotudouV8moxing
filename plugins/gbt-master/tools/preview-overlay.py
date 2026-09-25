# -*- coding: utf-8 -*-
"""浮层观感预览：把 client.js 里**真的那份 CSS** 抽出来，按**真的那段 DOM 结构**
渲染成一张图，好让"挤不挤、串不串字"这件事**先自己看一眼**，而不是让 Owner 当试纸。

⚠️ 这是**镜像预览**，不是真页面：真判据仍然只有
   ① `tools/verify-client-apply.mjs`（注册与 CSS 规则在不在）+ ② Owner 刷新后的实屏截图。
   这里只是把"肉眼那一步"提前做掉。

用法：
    python plugins/gbt-master/tools/preview-overlay.py            # 出当前版 + 旧版对照两张
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]
CLIENT = PLUGIN / "lib" / "client.js"
OUT = ROOT / ".scratch"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

PANELS = [
    ("01", "可视化面板总索引", "一屏列全活面板与渲染留影", True),
    ("02", "能力球 · 能力台", "158 项能力铺在真 3D 球面上 · 拖拽旋转 · 点节点进独立页", True),
    ("03", "上帝视角 W3", "六页签实时驾驶舱", True),
    ("04", "赏金台 · h1mcp", "本机只读 · 凭据只报已配/未配", True),
    ("05", "大脑执行层 · 五维合一", "AST 现算结构", True),
    ("06", "主控台 W1 · 数字人面板", "3D 形象走 raw/rig/model-rigged-anim.glb", True),
    ("07", "数字人形象页（成品）", "?model=bust 换半身件；两件都在 12 MB 上限内", True),
    ("08", "V22 可交互原型", "交付物 · 单文件", False),
]


def css_from_client() -> str:
    src = CLIENT.read_text(encoding="utf-8")
    m = re.search(r"const CSS = \[(.*?)\]\.join\(\"\\n\"\)", src, re.S)
    if not m:
        raise SystemExit("没抽到 CSS 数组 —— 先确认 client.js 结构没变")
    rules = []
    for line in m.group(1).splitlines():
        s = line.strip()
        if s.startswith('"') and (s.endswith('",') or s.endswith('"')):
            rules.append(s[1:-1] if s.endswith('"') else s[1:-2])
    if len(rules) < 20:
        raise SystemExit("抽到的 CSS 规则太少（%d 条），八成是解析写错了" % len(rules))
    return "\n".join(rules)


def page(css: str, old: bool) -> str:
    """old=True 时把**修复前那几个半透明值**装回去，做同屏对照。"""
    if old:
        css = (css
               .replace("background:rgba(2,4,10,.92)", "background:rgba(2,4,10,.66)")
               .replace("backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);", "")
               .replace(".gbtm-card{width:94vw;height:88vh;display:flex;flex-direction:column;background:var(--gbtm-bg)",
                        ".gbtm-card{width:94vw;height:88vh;display:flex;flex-direction:column;background:rgba(19,26,48,.94)")
               .replace(".gbtm-row:hover{background:var(--gbtm-panel)}", ".gbtm-row:hover{background:rgba(19,26,48,.72)}")
               .replace(".gbtm-rail{width:272px", ".gbtm-rail{width:230px")
               .replace("min-height:44px", "min-height:0")
               .replace("-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;", ""))
    rows = "\n".join(
        f'<div class="gbtm-row{" is-on" if i == 2 else ""}">'
        f'<span class="gbtm-idx">{n}</span>'
        f'<span class="gbtm-rname">{name}<span class="gbtm-note">{note}</span></span>'
        f'<span class="gbtm-badge{" is-off" if not ok else ""}">{"在" if ok else "缺"}</span></div>'
        for i, (n, name, note, ok) in enumerate(PANELS))
    # 背后放一层"会话列表"当干扰源：串字串得厉害不厉害，一眼就能看出来
    behind = "\n".join(
        f'<div style="padding:6px 10px;font-size:13px;color:#cfd6e6">'
        f'<b>GBT小土豆V8</b><div style="font-size:11px;color:#8b93a7">'
        f'{"全量穿透式交叉扫描把所有能力连接上并确认落实" if i % 2 == 0 else "把密钥切换成你的"} · {i + 1} 天前</div></div>'
        for i in range(14))
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>浮层预览（{'修复前' if old else '现在'}）</title>
<style>html,body{{margin:0;height:100%;background:#0b0e17;font-family:"Segoe UI","Microsoft YaHei",sans-serif}}
.gbtm-root{{position:relative;height:100vh;overflow:hidden}}
.gbtm-root .fake-side{{position:absolute;inset:0;display:flex}}
.gbtm-root .fake-rail{{width:272px;background:#0e1220;border-right:1px solid #1b2136;padding:8px}}
.gbtm-root .fake-main{{flex:1;padding:8px}}</style>
<style>{css}</style></head>
<body><div class="gbtm-root">
  <div class="fake-side"><div class="fake-rail">{behind}</div><div class="fake-main">{behind}</div></div>
  <div class="gbtm-scrim">
    <div class="gbtm-card">
      <div class="gbtm-head">
        <img class="gbtm-mark" width="40" height="40" alt="mark" src="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='40' height='40'><rect width='40' height='40' rx='12' fill='%237C4DFF'/></svg>">
        <div><div class="gbtm-word">GBT小土豆 V8 · 面板</div>
          <span class="gbtm-slogan">工作区可视化面板 · 在 12 / 12（内嵌打开，不跳转）</span></div>
        <span class="gbtm-grow"></span>
        <button class="gbtm-btn" type="button">关闭 Esc</button>
      </div>
      <div class="gbtm-bar"></div>
      <div class="gbtm-body">
        <div class="gbtm-rail">{rows}</div>
        <div class="gbtm-stage">
          <div class="gbtm-tools"><b>上帝视角 W3</b><span class="gbtm-chip">holo_pet_w3/index.html</span>
            <span class="gbtm-grow"></span><button class="gbtm-btn" type="button">重载</button>
            <button class="gbtm-btn" type="button">关闭</button></div>
          <div class="gbtm-warn">这一页的"最近调用 / 事件流"来自本机服务（127.0.0.1:8765）。宿主内已接内嵌反代；服务没起时这些读数会显示为空（不是假数据）。</div>
          <div class="gbtm-frame" style="display:flex;align-items:center;justify-content:center;color:#9AA4C4;font-size:13px">（此处是内嵌 iframe）</div>
        </div>
      </div>
      <div class="gbtm-foot">开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属</div>
    </div>
  </div>
</div></body></html>"""


def main() -> int:
    css = css_from_client()
    OUT.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    made = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True, args=["--hide-scrollbars"])
        for old in (False, True):
            html = OUT / ("_overlay_%s.html" % ("old" if old else "now"))
            html.write_text(page(css, old), encoding="utf-8")
            p = browser.new_page(viewport={"width": 1600, "height": 1000})
            p.goto(html.as_uri(), wait_until="load")
            p.wait_for_timeout(600)
            png = OUT / ("_overlay_%s.png" % ("old" if old else "now"))
            p.screenshot(path=str(png))
            made.append(str(png.relative_to(ROOT)))
            p.close()
        browser.close()
    print("CSS 规则 %d 条 · 出图: %s" % (len(css.splitlines()), ", ".join(made)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
