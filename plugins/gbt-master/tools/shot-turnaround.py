# -*- coding: utf-8 -*-
"""转面渲染器：给任意 GLB 出 正/侧/背/四分之三 视图 PNG（存证用）。

与 shot-skeleton.py 的分工：
  · shot-skeleton.py  —— 画**骨架**（红色骨链 + 青关节），验的是绑定
  · 本工具           —— 画**网格本体**（影棚光 + 不透明皮），验的是"长相对不对"

为什么单独做一件：看长相时骨架线会盖住脸，半透明皮又会把颜值冲淡 —— 那是两件事，
混在一张图上必然两头都不准。

判据（坏读数不许打绿灯）：
  · 顶点数 ≤ 0 或 window.__err 非空 ⇒ 退出码 1（图已落盘，但不许当证据）
  · 负控 --negctl：指向不存在的模型，必须红字报出而不是静默出空图
用法：
  py -3.14 plugins/gbt-master/tools/shot-turnaround.py <模型相对路径> [--out 前缀] [--views front,left]
  py -3.14 plugins/gbt-master/tools/shot-turnaround.py --negctl
退出码：0 = 全正读数；1 = 有坏读数 / 负控未过；3 = 前置不可达。
"""
import functools
import http.server
import pathlib
import sys
import threading

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

WS = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
VIEWER = "plugins/gbt-master/tools/model-turnaround.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = WS / "render"
DEFAULT_MODEL = "holo_pet/assets/digital-human/raw/phase1-owner/model.glb"
SIZE = 900


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve(root: pathlib.Path):
    handler = functools.partial(Quiet, directory=str(root))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}", httpd.shutdown


def preflight(model_rel: str):
    bad = []
    if not (WS / model_rel).is_file():
        bad.append(f"模型不在盘上：{model_rel}")
    if not (WS / "holo_pet/node_modules/three/build/three.module.js").exists():
        bad.append("three 未装（渲染器依赖）")
    if not (WS / VIEWER).is_file():
        bad.append(f"viewer 不在：{WS / VIEWER}")
    if not pathlib.Path(CHROME).exists():
        bad.append(f"Chrome 不在：{CHROME}")
    try:
        import playwright  # noqa: F401
    except ImportError as e:
        bad.append(f"playwright 未装（{e}）")
    return bad


def negctl() -> int:
    from playwright.sync_api import sync_playwright
    bogus = "/holo_pet/assets/digital-human/raw/__definitely_not_here__.glb"
    base, shutdown = serve(WS)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(executable_path=CHROME, headless=True,
                                   args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
            pg = b.new_page(viewport={"width": SIZE, "height": SIZE})
            pg.goto(f"{base}/{VIEWER}?model={bogus}&view=front", wait_until="load", timeout=40000)
            try:
                pg.wait_for_function("() => window.__shot === true || window.__err", timeout=30000)
            except Exception as e:
                print("wait 超时（既没成功也没报错）:", str(e)[:100])
            err = pg.evaluate("() => window.__err || ''")
            shot = pg.evaluate("() => window.__shot === true")
            shown = pg.evaluate("() => { const e=document.getElementById('err');"
                                "return {shown:getComputedStyle(e).display!=='none', text:e.textContent}}")
            b.close()
    finally:
        shutdown()
    ok = bool(err) and not shot and shown["shown"] and bool(shown["text"])
    print(f"__err={err!r}\n__shot={shot}\n红字横幅={shown}")
    print("✅ 负控通过：坏路径红字报出、不落 __shot" if ok
          else "🔴 负控失败：坏路径没被诚实报出")
    return 0 if ok else 1


def parse_args(argv):
    """按顺序扫，把 `--flag value` 的值一起吃掉，剩下的裸参数才是位置参数。

    🔴 教训：第一版写成「过滤掉所有 -- 开头的」，于是 `--out X` 里的 X 被当成模型路径
    （报「模型不在盘上：Owner数字人-Phase1」）—— 参数解析也会撒谎。"""
    opts, pos, i = {}, [], 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            key = a[2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                opts[key] = argv[i + 1]
                i += 2
            else:
                opts[key] = True
                i += 1
        else:
            pos.append(a)
            i += 1
    return opts, pos


def main() -> int:
    if "--negctl" in sys.argv:
        return negctl()

    opts, pos = parse_args(sys.argv[1:])
    model_rel = (pos[0] if pos else DEFAULT_MODEL).replace("\\", "/")
    prefix = opts.get("out") or "转面"
    views = (opts.get("views") or "front,left,back,three-quarter")
    views = views.split(",") if isinstance(views, str) else ["front", "left", "back", "three-quarter"]
    # 透传给 viewer 的额外查询串（例：--extra "&real=0" 做"真人化前/后"对照）
    extra = opts.get("extra") or ""
    if isinstance(extra, str) and extra and not extra.startswith("&"):
        extra = "&" + extra

    miss = preflight(model_rel)
    if miss:
        for m in miss:
            print("🔴 前置不可达：" + m)
        return 3

    from playwright.sync_api import sync_playwright
    OUT.mkdir(parents=True, exist_ok=True)
    base, shutdown = serve(WS)
    print(f"静态服务 {base}（根 = 工作区，只读）· 模型 {model_rel}")
    zh = {"front": "正面", "left": "左侧", "right": "右侧", "back": "背面", "three-quarter": "四分之三"}
    bad = []
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(executable_path=CHROME, headless=True,
                                   args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
            # 🔴 预热（丢弃式）：浏览器**第一个**页面的 WebGL 首帧在 software-GL 下不会按时合成，
            #    截出来是**全黑**，而 window.__shot 已经是 true、读数全绿。
            #    2026-09-25 实测：yaw 扫描里只有第一个角度覆盖 100%（= 全黑像素不同于背景色），
            #    其余每个角度都是正常的 9–11%。上一版因此把"正面全空"误判成**网格绕序反了**，
            #    还顺带去查了面向 —— 那是**工具在撒谎**，不是模型坏了。故正式出图前先烧掉一页。
            warm = b.new_page(viewport={"width": SIZE, "height": SIZE})
            warm.goto(f"{base}/{VIEWER}?model=/{model_rel}&view=front&size={SIZE}",
                      wait_until="load", timeout=40000)
            try:
                warm.wait_for_function("() => window.__shot === true || window.__err", timeout=120000)
            except Exception:
                pass
            warm.wait_for_timeout(1500)
            warm.close()
            print("预热完成（首帧已丢弃）")

            for v in views:
                name = f"{prefix}-{zh.get(v, v)}.png"
                pg = b.new_page(viewport={"width": SIZE, "height": SIZE})
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
                pg.goto(f"{base}/{VIEWER}?model=/{model_rel}&view={v}&size={SIZE}{extra}",
                        wait_until="load", timeout=40000)
                try:
                    pg.wait_for_function("() => window.__shot === true || window.__err", timeout=120000)
                except Exception as e:
                    errs.append("wait:" + str(e)[:80])
                pg.wait_for_timeout(600)
                err = pg.evaluate("() => window.__err || ''")
                dbg = pg.evaluate("() => window.__dbg || null")
                # 覆盖度 + 近黑占比：
                #   · coverage = 与背景色 (16,19,25) 差 >24 的像素占比
                #   · darkFrac = 亮度 < 6 的像素占比（**未合成帧**的特征）
                # 🔴 教训：一开始只用 coverage>95% 判"全黑"，结果**脸部特写**被误判
                #    （特写时人物本来就占满画面，coverage 97% 是正常的）。
                #    要区分"全黑未合成"与"主体占满"，看的是**近黑像素占比**，不是覆盖度。
                px = pg.evaluate("""() => {
                  const c = document.querySelector('canvas');
                  const g = document.createElement('canvas'); g.width = c.width; g.height = c.height;
                  const x = g.getContext('2d'); x.drawImage(c, 0, 0);
                  const d = x.getImageData(0, 0, c.width, c.height).data;
                  let cov = 0, dark = 0, n = c.width * c.height;
                  for (let i = 0; i < d.length; i += 4) {
                    if (Math.abs(d[i]-16) + Math.abs(d[i+1]-19) + Math.abs(d[i+2]-25) > 24) cov++;
                    if (d[i] + d[i+1] + d[i+2] < 18) dark++;
                  }
                  return { cover: +(cov / n * 100).toFixed(2), dark: +(dark / n * 100).toFixed(2) };
                }""")
                cov, dark = (px or {}).get("cover"), (px or {}).get("dark")
                pg.screenshot(path=str(OUT / name))
                pg.close()
                vn = int((dbg or {}).get("verts") or -1)
                print(f"[{v}] 视角={zh.get(v, v)} 顶点={vn} 贴图={(dbg or {}).get('tex')} "
                      f"远景距离={(dbg or {}).get('dist')} far={(dbg or {}).get('far')} "
                      f"原始包围盒={(dbg or {}).get('rawSize')} 中心={(dbg or {}).get('rawCenter')} "
                      f"覆盖={cov}% 近黑={dark}% err={err or 'none'} "
                      f"pageerrors={errs[:2] if errs else 'none'} -> {name}")
                if err:
                    bad.append(f"{v}: 加载失败 {err}")
                elif vn <= 0:
                    bad.append(f"{v}: 顶点数不是正数（{vn}）—— 网格没读到")
                elif dark is None or dark > 90:
                    bad.append(f"{v}: 近黑像素 {dark}% —— **首帧未合成**（全黑），不能当证据")
                elif cov is None or cov < 1:
                    bad.append(f"{v}: 覆盖 {cov}% —— 画面基本是空的，模型没进画面")
            b.close()
    finally:
        shutdown()

    if bad:
        print("🔴 渲染失败（坏读数不落成结论）：")
        for x in bad:
            print("   - " + x)
        return 1
    print(f"✅ {len(views)} 张转面图正读数 → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
