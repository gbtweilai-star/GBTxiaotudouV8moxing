"""逐个面板真渲染审计：走 /gbt-master 路由，抓状态码 / 控制台错 / 失败请求 / 实际内容。"""
import json, pathlib, sys, urllib.request
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3080"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.scratch\_panel_audit.json")

def get_json(url):
    """目录 JSON 由 pwsh/Invoke-WebRequest 先落盘（urllib 走这条路由会被截断，浏览器与 IWR 均正常）。"""
    p = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.scratch\_gbt_catalog.json")
    return json.loads(p.read_text(encoding="utf-8"))


cat = get_json(BASE + "/gbt-master")
rows = []
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True)
    for p in cat.get("panels", []):
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        errs, bad = [], []
        pg.on("pageerror", lambda e: errs.append(str(e)[:200]))
        pg.on("console", lambda m: errs.append("console:" + m.text[:160]) if m.type == "error" else None)
        pg.on("response", lambda r: bad.append(str(r.status) + " " + r.url[:130]) if r.status >= 400 else None)
        status = None
        url = BASE + p["url"]
        try:
            resp = pg.goto(url, wait_until="load", timeout=35000)
            status = resp.status if resp is not None else None
        except Exception as e:
            errs.append("goto:" + str(e)[:140])
        pg.wait_for_timeout(4000)
        try:
            m = pg.evaluate("()=>({t:document.title,txt:(document.body.innerText||'').replace(/\\s+/g,' ').trim(),c:document.querySelectorAll('canvas').length,h:document.body.scrollHeight})")
        except Exception as e:
            m = {"t": "", "txt": "", "c": 0, "h": 0}
            errs.append("eval:" + str(e)[:100])
        rows.append({
            "id": p["id"], "name": p["name"], "exists": p["exists"], "http": status,
            "title": m["t"][:60], "textLen": len(m["txt"]), "canvas": m["c"], "height": m["h"],
            "head": m["txt"][:110],
            "errCount": len(errs), "errs": errs[:3],
            "badCount": len(bad), "bad": bad[:8],
        })
        print(f"[{p['id']}] http={status} text={len(m['txt'])} canvas={m['c']} err={len(errs)} bad={len(bad)}", flush=True)
        pg.close()
    b.close()

OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print("saved:", OUT)
