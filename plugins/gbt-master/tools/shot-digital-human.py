"""真渲染数字人面板：等三维模型就位（或如实失败/缺料），截图存证。"""
import json, pathlib, sys
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8788/holo_pet/index.html"
OUT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\render\数字人面板-当前.png")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True, args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
    pg = b.new_page(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
    errs, bad = [], []
    pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
    pg.on("console", lambda m: errs.append("console:" + m.text[:160]) if m.type == "error" else None)
    pg.on("response", lambda r: bad.append(str(r.status) + " " + r.url[-90:]) if r.status >= 400 else None)
    pg.goto(URL, wait_until="load", timeout=40000)
    for _ in range(40):
        pg.wait_for_timeout(1500)
        st = pg.evaluate("() => document.body.dataset.localAvatar3d || 'pending'")
        if st in ("ready", "failed"):
            break
    m = pg.evaluate("""()=>({
      avatar: document.body.dataset.localAvatar3d || 'pending',
      status: (document.getElementById('avatar-status')||{}).textContent || '',
      canvas: document.querySelectorAll('canvas').length,
      canvasPx: (()=>{ const c=document.querySelector('#avatar-canvas'); return c?[c.width,c.height]:null })(),
      text: (document.body.innerText||'').replace(/\\s+/g,' ').slice(0,160)})""")
    print(json.dumps(m, ensure_ascii=False, indent=1))
    print("pageerrors:", errs[:4] if errs else "none")
    print("failed reqs:", bad[:8] if bad else "none")
    pg.screenshot(path=str(OUT))
    print("saved:", OUT)
    b.close()
