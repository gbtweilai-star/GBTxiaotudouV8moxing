# -*- coding: utf-8 -*-
"""工作区总索引（`index.html`）的**现读一致性**验收：真 Chrome + 真宿主源。

为什么要有它：这张页的卖点是"**台账现读**"—— 顶部 PANELS / RENDERS / PAYLOAD / MISSING
与每张卡片的字节数，都是打开这一页时读 `GET /gbt-master` 现填的。
但"现读"这三个字**只有真浏览器跑一遍才能证明**：取不到时它会显示「取不到」，
而 Static 检查（语法/生成一致性）都看不出这一点。

判据：
  · 页面无 pageerror / console.error；
  · `#live-src` 以 `LIVE` 开头（= 真读到了宿主目录，不是「取不到」）；
  · `#t-panels` == 宿主目录 `total`；`#s-panels` == `present`；`#s-missing` == total-present；
  · 卡片数 == 页面登记的面板数（多/少都要报：orphan 或漏卡）。

用法：py -3.14 plugins/gbt-master/tools/verify-index-panel.py
退出码：0 = 一致；1 = 不一致（含取不到现读）。
"""
from __future__ import annotations

import json
import sys
import urllib.request

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PANEL = "http://127.0.0.1:3080/gbt-master/fs/index.html"
CATALOG = "http://127.0.0.1:3080/gbt-master"

cat = json.loads(urllib.request.urlopen(CATALOG, timeout=10).read().decode("utf-8"))
panels = cat.get("panels") or []
present = [p for p in panels if p.get("exists")]
problems: list[str] = []

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 1200})
    errs: list[str] = []
    pg.on("pageerror", lambda e: errs.append("pageerror:" + str(e)[:200]))
    pg.on("console", lambda m: errs.append("console:" + m.text[:180]) if m.type == "error" else None)
    resp = pg.goto(PANEL, wait_until="load", timeout=45000)
    status = resp.status if resp else None
    try:
        pg.wait_for_function("()=>{var e=document.getElementById('live-src');"
                             "return !!e&&/LIVE|取不到/.test(e.textContent)}", timeout=15000)
    except Exception as e:  # noqa: BLE001
        problems.append("等不到台账现读完成（%s）" % str(e)[:80])
    got = pg.evaluate(
        "()=>({live:(document.getElementById('live-src')||{}).textContent||'',"
        "panels:(document.getElementById('t-panels')||{}).textContent||'',"
        "renders:(document.getElementById('t-renders')||{}).textContent||'',"
        "sPanels:(document.getElementById('s-panels')||{}).textContent||'',"
        "sMissing:(document.getElementById('s-missing')||{}).textContent||'',"
        "cards:document.querySelectorAll('a.card').length,"
        "hrefs:Array.prototype.map.call(document.querySelectorAll('a.card'),function(a){return a.getAttribute('href')}),"
        "title:document.title})"
    )
    shot = r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.scratch\_verify_index_live.png"
    pg.screenshot(path=str(shot), full_page=True)
    b.close()

# ⚠️ 卡片数**不该**等于登记数：总索引页**不给自己列卡片**（自链接没有意义）。
#    第一版这里直接比 `cards == total` ⇒ 误报 11≠12（**门报红先怀疑门**，第 8 次）。
#    正确口径：卡片 href 必须都在登记表里；登记表里**除 index.html 自己**之外的每一条都要有卡片。
reg_files = [p.get("file") for p in panels]
expect_cards = [f for f in reg_files if f and f != "index.html"]
got_hrefs = [h for h in got.get("hrefs", []) if h]

if status != 200:
    problems.append("页面 HTTP %s" % status)
if errs:
    problems.append("页面报错 %d 条：%s" % (len(errs), "；".join(errs[:3])))
if not str(got["live"]).startswith("LIVE"):
    problems.append("台账没进 LIVE（live-src=%r）—— 说明没读到宿主目录" % got["live"][:80])
if str(got["panels"]).strip() != str(cat.get("total")):
    problems.append("顶部 PANELS=%r，宿主 total=%r" % (got["panels"], cat.get("total")))
if str(got["sPanels"]).strip() != str(cat.get("present")):
    problems.append("台账 PANELS LIVE=%r，宿主 present=%r" % (got["sPanels"], cat.get("present")))
if str(got["sMissing"]).strip() != str(len(panels) - len(present)):
    problems.append("台账 MISSING=%r，宿主实际缺 %d" % (got["sMissing"], len(panels) - len(present)))
if int(got["cards"]) != len(expect_cards):
    problems.append("卡片数 %s，登记表（除本页自己）应有 %s" % (got["cards"], len(expect_cards)))
missing_cards = [f for f in expect_cards if f not in got_hrefs]
orphan_cards = [h for h in got_hrefs if h not in reg_files]
if missing_cards:
    problems.append("登记表里有、页面上没卡片：%s" % "、".join(missing_cards[:5]))
if orphan_cards:
    problems.append("页面上有卡片、登记表里没有（孤儿卡）：%s" % "、".join(orphan_cards[:5]))

print("=" * 84)
print("工作区总索引 · 现读一致性验收")
print("=" * 84)
print("页面 HTTP %s · 标题 %s" % (status, got["title"]))
print("宿主目录：total=%s · present=%s · renders=%s" % (cat.get("total"), cat.get("present"), cat.get("renders")))
print("页面台账：PANELS=%s · RENDERS=%s · PANELS LIVE=%s · MISSING=%s · 卡片 %s"
      % (got["panels"], got["renders"], got["sPanels"], got["sMissing"], got["cards"]))
print("卡片核对：登记表（除本页自己 %d 条）↔ 页面 %d 张卡片"
      % (len(expect_cards), len(got_hrefs)))
print("现读状态：%s" % got["live"][:110])
print("截图：%s" % shot)
for p in problems:
    print("🔴 %s" % p)
print("-" * 84)
print("结论：%s" % ("台账与宿主目录一致 ✅" if not problems else "**不一致**（%d 处）" % len(problems)))
sys.exit(0 if not problems else 1)
