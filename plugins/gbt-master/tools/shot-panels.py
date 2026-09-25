"""定性：赏金台那处「文字叠压」到底是**真布局缺陷**还是 full_page 截图伪影。

做法：同一页面、同一数据，只改截图方式 ——
  A) 视口截图（full_page=False，窗口 1020x1400 装得下全内容）→ 真实观感
  B) 再取一次关键元素的实际几何（getBoundingClientRect）→ 有没有真的互相覆盖
判据：若 A 里不再叠压、且 B 的矩形两两不重叠 ⇒ 是伪影；
      若 A 里仍叠压、或 B 里有实矩形相交 ⇒ 是真缺陷。

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
"""
import json
import pathlib

from playwright.sync_api import sync_playwright

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "http://127.0.0.1:3080/gbt-master/fs/holo_pet_w3/h1/index.html"
OUT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8\.scratch")

with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=CHROME, headless=True)
    pg = b.new_page(viewport={"width": 1020, "height": 1400}, device_scale_factor=1)
    pg.goto(URL, wait_until="load", timeout=45000)
    pg.wait_for_timeout(6000)
    shot = OUT / "_shot_h1_viewport.png"
    pg.screenshot(path=str(shot), full_page=False)

    geo = pg.evaluate("""() => {
      const out = [];
      document.querySelectorAll('article.gbt-card, header.gbt-topbar, footer.gbt-statusbar, footer.gbt-signature').forEach((el,i) => {
        const r = el.getBoundingClientRect();
        out.push({i, tag: el.tagName.toLowerCase(),
                  cls: el.className,
                  head: (el.querySelector('h2') ? el.querySelector('h2').textContent.trim().slice(0,26) : ''),
                  x: Math.round(r.x), y: Math.round(r.y),
                  w: Math.round(r.width), h: Math.round(r.height)});
      });
      return {boxes: out,
              doc: {scrollH: document.documentElement.scrollHeight, clientH: document.documentElement.clientHeight},
              bodyOverflow: getComputedStyle(document.body).overflow,
              cards: document.querySelectorAll('article.gbt-card').length,
              credRows: document.querySelectorAll('#h1-cred-body tr').length};
    }""")

    boxes = geo["boxes"]
    clashes = []
    for a in range(len(boxes)):
        for c in range(a + 1, len(boxes)):
            A, B = boxes[a], boxes[c]
            ox = min(A["x"] + A["w"], B["x"] + B["w"]) - max(A["x"], B["x"])
            oy = min(A["y"] + A["h"], B["y"] + B["h"]) - max(A["y"], B["y"])
            if ox > 2 and oy > 2:
                clashes.append({"a": A["head"] or A["cls"], "b": B["head"] or B["cls"],
                                "overlap_x": ox, "overlap_y": oy})
    print("cards      =", geo["cards"])
    print("credRows   =", geo["credRows"])
    print("scrollH/clientH =", geo["doc"]["scrollH"], "/", geo["doc"]["clientH"])
    print("body.overflow   =", geo["bodyOverflow"])
    print("矩形数      =", len(boxes))
    for x in boxes:
        print("   y={0:>5} h={1:>5}  {2}".format(x["y"], x["h"], (x["head"] or x["cls"])[:40]))
    print("实际相交的矩形对 =", len(clashes))
    for c in clashes:
        print("   ", c)
    (OUT / "_verify_h1_geometry.json").write_text(
        json.dumps({"geometry": geo, "clashes": clashes}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("shot:", shot)
    b.close()
