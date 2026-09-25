# -*- coding: utf-8 -*-
"""能力球面板的**现读一致性**验收：真 Chrome + 真宿主源，比对页面自报与现读 API。

为什么要它：`capabilities.html` 原来把 183 项/31 域/图例五个数字**写死**，而现读是 158 项/30 域 ——
面板自称"现读"却在骗人（同一族的第三次）。现在面板改成"快照先画 → 现读重建"，
并把结果自报在 `window.__gbtPanelCaps`；本器就是读那份自报，与 `/api/capabilities` 逐项对。

判据：
  · `source` 必须是 `live`（取不到现读要如实变成 snapshot，那也算不通过 —— 说明现读链断了）；
  · `count` / `domains` / `byState` 必须与现读 API 对得上；
  · 页面不许有 pageerror / console.error。

用法：py -3.14 plugins/gbt-master/tools/verify-panel-live.py
退出码：0 = 一致；1 = 不一致（含取不到现读）。
"""
from __future__ import annotations

import json
import sys
import urllib.request

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PANEL = "http://127.0.0.1:3080/gbt-master/fs/capabilities.html"
API = "http://127.0.0.1:8765/api/capabilities"

live = json.loads(urllib.request.urlopen(API, timeout=10).read().decode("utf-8"))
ark = ((live.get("app") or {}).get("ark") or {}).get("skills") or []
# 现读接口自己写明：「能力分四条通道 …… `total` 只数第一条，别拿它当全量」。
# 所以面板该画的 = registry(items) + ark(app.ark.skills)；域数 = registry 域 + ark 这 1 个。
want = {"count": live["total"] + len(ark),
        "domains": len(live.get("domains") or {}) + (1 if ark else 0),
        "ark": len(ark)}

problems: list[str] = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    errs: list[str] = []
    pg.on("pageerror", lambda e: errs.append("pageerror:" + str(e)[:200]))
    pg.on("console", lambda m: errs.append("console:" + m.text[:180]) if m.type == "error" else None)
    resp = pg.goto(PANEL, wait_until="load", timeout=45000)
    status = resp.status if resp else None
    pg.wait_for_timeout(1500)
    try:
        pg.wait_for_function("()=>!!window.__gbtPanelCaps", timeout=15000)
    except Exception as e:  # noqa: BLE001
        problems.append("等不到页面自报 window.__gbtPanelCaps（%s）" % str(e)[:80])
    report = pg.evaluate("()=>window.__gbtPanelCaps||null")
    hint = pg.evaluate("()=>{var e=document.getElementById('hint');return e?(e.textContent||'').replace(/\\s+/g,' ').trim():''}")
    legend = pg.evaluate(
        "()=>['lg-free','lg-guarded','lg-stub','lg-disabled','lg-external']"
        ".map(function(i){var e=document.getElementById(i);return (e?e.textContent:'?')})"
    )
    shot = r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.scratch\_verify_panel_live.png"
    pg.screenshot(path=shot, full_page=True)
    b.close()

if status != 200:
    problems.append("面板 HTTP %s" % status)
if errs:
    problems.append("页面报错 %d 条：%s" % (len(errs), "；".join(errs[:3])))
if isinstance(report, dict):
    if report.get("source") != "live":
        problems.append("面板自报 source=%s（要求 live —— 说明没接上现读）" % report.get("source"))
    if report.get("count") != want["count"]:
        problems.append("面板自报 count=%s，现读 total=%s" % (report.get("count"), want["count"]))
    if report.get("domains") != want["domains"]:
        problems.append("面板自报 domains=%s，现读域数=%s" % (report.get("domains"), want["domains"]))
    by = report.get("byState") or {}
    live_disabled = sum(1 for x in live["items"] if x.get("enabled") is False)
    if by.get("disabled") != live_disabled:
        problems.append("面板图例「禁用」=%s，现读 disabled=%s" % (by.get("disabled"), live_disabled))
    if ark and by.get("external") != len(ark):
        problems.append("面板图例「Ark 云端」=%s，现读 ark 通道=%s" % (by.get("external"), len(ark)))
    if report.get("arkMissing"):
        problems.append("面板自报 arkMissing=true（Ark 只报了数没给条目）")
else:
    problems.append("页面自报不是对象：%r" % (report,))

print("=" * 84)
print("能力球面板 · 现读一致性验收")
print("=" * 84)
print("面板 HTTP %s · 现读 API total=%s / 域 %s" % (status, want["count"], want["domains"]))
print("页面自报：%s" % json.dumps(report, ensure_ascii=False))
print("提示语：%s" % hint[:160])
print("图例：[免卡, 要授权, 桩, 禁用, Ark] = %s" % legend)
print("截图：%s" % shot)
for p in problems:
    print("🔴 %s" % p)
print("-" * 84)
print("结论：%s" % ("面板数字与现读一致 ✅" if not problems else "**不一致**（%d 处）" % len(problems)))
sys.exit(0 if not problems else 1)
