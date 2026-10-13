"""骨架复核截图（**存证工具**）：同一模型三个时刻（静止 / idle / walk），骨架画成红色链 + 青色关节点。

🔴 2026-09-22 晚 · 本工具修掉三处会让"存证"变成"撒谎"的毛病：
  1. **模型路径是死路**：viewer 里写死 `assets/digital-human/tripo-human.glb`，那个文件
     **全树不存在**（资产已整理进 `assets/digital-human/raw/` 分层）⇒ 每次都在**空场景**上
     截图，图上还印着"骨架复核 · 关节数 —"。现默认指向真身
     `assets/digital-human/raw/rig/model-rigged-anim.glb`。
  2. **依赖一份幽灵副本**：旧稿去开 `/.scratch/_skeleton_viewer.html`，而 `.scratch/` 里那份
     早已不存在 ⇒ 工具根本跑不起来。现在**直接服务工具本体真身**，不再需要任何副本。
  3. **静默出图**：旧稿即使加载失败也只 print 一句 `err=…` 就退出 0，图和读数照旧落盘。
     现在 **关节数 / 顶点数为 0 或 err 非空 ⇒ 退出码 1**（存证工具不许在坏读数上打绿灯）。

服务方式：本脚本自己起一个**只读静态服务**（127.0.0.1 随机空闲端口，根 = 工作区），
所以它不再依赖"外部先有个 8788 在跑"。

用法：py -3.14 plugins/gbt-master/tools/shot-skeleton.py            # 出 5 张存证图
      py -3.14 plugins/gbt-master/tools/shot-skeleton.py --negctl   # 负控：坏路径必须红字报出
退出码：0 = 全部正读数；1 = 有坏读数 / 负控未通过；3 = 前置不可达（与"读数坏"分开）。
"""
import functools
import http.server
import pathlib
import sys
import threading

try:                                    # 控制台是 GBK，中文文件名直接 print 会炸（已踩过）
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

WS = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
VIEWER = "plugins/gbt-master/tools/skeleton-viewer.html"
RIG = "holo_pet/assets/digital-human/raw/rig"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = WS / "render"

# 两件资产，两套期望值 —— **期望写在明处**，别让闸去猜：
#   面板档 `model-rigged-anim.glb`：22 关节 / 16017 顶点 / **0 弹簧骨**（它的骨里没有弹簧链）
#   弹簧档 `model-springs-hair.glb`：29 关节 / 7 弹簧骨（SkirtF/B/L/R + HairB/L/R）
# 🔴 教训：本脚本第一版对**每一张**都断言"弹簧骨 > 0"，于是面板档三张全被自己判红 ——
#    那不是资产坏了，是**闸写粗了**。期望值必须跟着"在测哪件资产"走。
PANEL_URL = f"/{RIG}/model-rigged-anim.glb"
SPRING_URL = f"/{RIG}/model-springs-hair.glb"

shots = [
    ("bind", "none", 0.0, "骨架复核-数字人静止态.png", PANEL_URL, 22, 0, ""),
    ("idle", "preset:idle", 0.0, "骨架复核-数字人idle.png", PANEL_URL, 22, 0, ""),
    ("walk", "preset:walk", 1.2, "骨架复核-数字人walk.png", PANEL_URL, 22, 0, ""),
    # 弹簧档走 `body=0`（只画骨架不画皮）：它的绑定姿态会把弹簧头发拉成一柱冲天，
    # 半透明图会被误读成"头发坏了"—— 那是**没接动力学**的正常表现，不是缺陷。
    ("spring-bind", "none", 0.0, "骨架复核-弹簧档静止态.png", SPRING_URL, 29, 7, "&body=0"),
    ("spring-idle", "preset:idle", 0.0, "骨架复核-弹簧档idle.png", SPRING_URL, 29, 7, "&body=0"),
]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):          # 别把每个请求刷屏
        pass


def serve(root: pathlib.Path):
    """只读静态服务，随机空闲端口；返回 (url_base, shutdown_fn)。"""
    handler = functools.partial(Quiet, directory=str(root))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return f"http://127.0.0.1:{port}", httpd.shutdown


def preflight():
    """前置不可达就说清是哪一件，别让它伪装成"模型坏了"。"""
    bad = []
    for url in (PANEL_URL, SPRING_URL):
        if not (WS / url.lstrip("/")).exists():
            bad.append(f"模型不在盘上：{url}")
    if not (WS / "holo_pet/node_modules/three/build/three.module.js").exists():
        bad.append("three 未装（形象页依赖）")
    if not (WS / VIEWER).exists():
        bad.append(f"viewer 不在：{WS / VIEWER}")
    if not pathlib.Path(CHROME).exists():
        bad.append(f"Chrome 不在：{CHROME}")
    return bad


def negctl() -> int:
    """负控：把 viewer 指向**不存在的模型**，验证它"红字报出"而不是静默出图。

    为什么它必须常驻：本次抓到的原缺陷就是**静默失败**（空场景照旧截图、照旧自称存证）。
    所以这个工具的失败路径本身要有闸 —— 坏了必须红，不许再退化成"没看出来"。
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        print(f"🔴 前置不可达：playwright 未装（{e}）")
        return 3
    bogus = f"/{RIG}/__definitely_not_here__.glb"
    base, shutdown = serve(WS)
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(executable_path=CHROME, headless=True,
                                   args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
            pg = b.new_page(viewport={"width": 760, "height": 900})
            pg.goto(f"{base}/{VIEWER}?model={bogus}&clip=none&t=0", wait_until="load", timeout=40000)
            try:
                pg.wait_for_function("() => window.__shot === true || window.__err", timeout=30000)
            except Exception as e:
                print("wait 超时（既没成功也没报错）:", str(e)[:100])
            err = pg.evaluate("() => window.__err || ''")
            shot = pg.evaluate("() => window.__shot === true")
            shown = pg.evaluate("() => { const e = document.getElementById('err');"
                                "return {shown: getComputedStyle(e).display !== 'none', text: e.textContent}; }")
            b.close()
    finally:
        shutdown()
    ok = bool(err) and not shot and shown["shown"] and bool(shown["text"])
    print(f"__err={err!r}\n__shot={shot}\n红字横幅={shown}")
    print("✅ 负控通过：模型不在盘上时 viewer 红字报出、不落 __shot" if ok
          else "🔴 负控失败：坏路径没被诚实报出 —— 原缺陷又回来了")
    return 0 if ok else 1


def main() -> int:
    if "--negctl" in sys.argv:
        return negctl()
    miss = preflight()
    if miss:
        for m in miss:
            print("🔴 前置不可达：" + m)
        return 3                                    # 3 = 前置问题，与"读数坏"分开

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as e:
        print(f"🔴 前置不可达：playwright 未装（{e}）")
        return 3

    OUT.mkdir(parents=True, exist_ok=True)
    base, shutdown = serve(WS)
    print(f"静态服务 {base}（根 = 工作区，只读）")
    bad = []
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch(executable_path=CHROME, headless=True,
                                   args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader"])
            for tag, clip, t, name, model, exp_j, exp_s, extra in shots:
                pg = b.new_page(viewport={"width": 760, "height": 900})
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
                pg.goto(f"{base}/{VIEWER}?model={model}&clip={clip}&t={t}{extra}",
                        wait_until="load", timeout=40000)
                try:
                    pg.wait_for_function("() => window.__shot === true || window.__err", timeout=90000)
                except Exception as e:
                    errs.append("wait:" + str(e)[:80])
                pg.wait_for_timeout(800)
                joints = pg.evaluate("() => document.getElementById('j').textContent")
                verts = pg.evaluate("() => document.getElementById('v').textContent")
                pg.evaluate("() => document.getElementById('s').textContent")
                err = pg.evaluate("() => window.__err || ''")
                dbg = pg.evaluate("() => window.__dbg || null")
                pg.screenshot(path=str(OUT / name))
                pg.close()

                kn = int(joints) if str(joints).isdigit() else -1
                vn = int(verts) if str(verts).isdigit() else -1
                sn = len((dbg or {}).get("springs") or [])
                print(f"[{tag}] {pathlib.PurePosixPath(model).name} 关节={joints}(期{exp_j}) "
                      f"顶点={verts} 弹簧骨={sn}(期{exp_s}) clip={clip} t={t} "
                      f"err={err or 'none'} pageerrors={errs[:2] if errs else 'none'} -> {name}")
                # 🔴 判据（这才是本工具存在的意义）：坏读数不许打出"存证成功"
                if err:
                    bad.append(f"{tag}: 加载失败 {err}")
                elif kn <= 0:
                    bad.append(f"{tag}: 关节数不是正数（{joints}）—— 骨架没读到")
                elif vn <= 0:
                    bad.append(f"{tag}: 顶点数不是正数（{verts}）—— 网格没读到")
                elif kn != exp_j:
                    bad.append(f"{tag}: 关节数 {kn} ≠ 期望 {exp_j}（资产换代了，或测错了件）")
                elif sn != exp_s:
                    bad.append(f"{tag}: 弹簧骨 {sn} ≠ 期望 {exp_s}（弹簧链没了 / 期望值过期）")
            b.close()
    finally:
        shutdown()

    if bad:
        print("🔴 存证失败（坏读数不落成结论）：")
        for x in bad:
            print("   - " + x)
        print("   注意：图已经落盘了，但上面这些张**不能当证据用**。")
        return 1
    print(f"✅ {len(shots)} 张骨架存证都拿到正读数（面板档 22 关节 · 弹簧档 29 关节/7 弹簧骨）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
