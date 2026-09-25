"""赏金台 / 大脑执行层 · 在**真宿主源**下的真渲染验收。

做法照抄 plugins/gbt-master/tools/audit-panels.py（真 Chrome + Playwright）：
抓 状态码 / pageerror / console.error / 任何 >=400 的响应 / 页面可见文字 / 截图。
只读：不点任何按钮、不改任何状态。

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
# 走 DSH 宿主源 —— 这才是「在面板里」的真实处境（不是 8765 面板端口）
BASE = "http://127.0.0.1:3080/gbt-master/fs/"
OUT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.scratch")

TARGETS = [
    ("index", "index.html", 1440, 1200),
    ("h1", "holo_pet_w3/h1/index.html", 1020, 860),
    ("brain", "brain.html", 1320, 900),
]

rows = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True)
    for pid, path, w, h in TARGETS:
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        errs, bad = [], []
        pg.on("pageerror", lambda e: errs.append("pageerror:" + str(e)[:200]))
        pg.on(
            "console",
            lambda m: errs.append("console:" + m.text[:180]) if m.type == "error" else None,
        )
        pg.on(
            "response",
            lambda r: bad.append(str(r.status) + " " + r.url[:150]) if r.status >= 400 else None,
        )
        status = None
        try:
            resp = pg.goto(BASE + path, wait_until="load", timeout=45000)
            status = resp.status if resp is not None else None
        except Exception as e:  # noqa: BLE001
            errs.append("goto:" + str(e)[:170])
        pg.wait_for_timeout(6000)
        try:
            m = pg.evaluate(
                "()=>({t:document.title,"
                "txt:(document.body.innerText||'').replace(/\\s+/g,' ').trim(),"
                "h:document.body.scrollHeight,"
                "cards:document.querySelectorAll('a.card').length,"
                "warnShown:(function(){var w=document.getElementById('warn');"
                "return !!(w&&getComputedStyle(w).display!=='none')})()})"
            )
        except Exception as e:  # noqa: BLE001
            m = {"t": "", "txt": "", "h": 0, "cards": 0, "warnShown": None}
            errs.append("eval:" + str(e)[:120])
        shot = OUT / ("_verify_" + pid + ".png")
        try:
            pg.screenshot(path=str(shot), full_page=True)
        except Exception as e:  # noqa: BLE001
            errs.append("shot:" + str(e)[:120])
        rows.append({
            "id": pid, "url": BASE + path, "http": status, "title": m["t"][:70],
            "textLen": len(m["txt"]), "cards": m["cards"], "warnShown": m["warnShown"],
            "height": m["h"], "shot": str(shot),
            "errCount": len(errs), "errs": errs[:4],
            "badCount": len(bad), "bad": bad[:8],
            "text": m["txt"][:1400],
        })
        print(
            "[{0}] http={1} text={2} cards={3} warn={4} err={5} bad={6}".format(
                pid, status, len(m["txt"]), m["cards"], m["warnShown"], len(errs), len(bad)
            ),
            flush=True,
        )
        pg.close()
    b.close()

(OUT / "_verify_panels.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8"
)
print("saved:", OUT / "_verify_panels.json")
sys.exit(0)
