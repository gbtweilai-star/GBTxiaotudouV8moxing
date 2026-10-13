"""GBT小土豆V8 · 面板面「全量穿透式交叉扫描」。

穿透四层，每层都拿真读数，不许猜：

  ① **宿主层** —— `/gbt-master` 目录 JSON 与盘上源码的 PANELS 登记表交叉对账
     （现役登记表 vs 源码登记表 vs 盘上真身，三份互相咬，差集就是断点）
  ② **路由层** —— 每个面板 + 额外高价值页走真 HTTP，记状态码 / 字节 / 类型
  ③ **运行时层** —— 真 Chrome 逐页渲染，抓控制台错 / 失败请求 / 实际文本 / canvas
  ④ **数据层** —— 每个页面的 `/api/*` 后端（8765 本机服务）逐个探，区分
     「服务没起（503）」与「端点不存在（404）」—— 不许把两者混成一句"没数据"

用法：
    C:\\Python312\\python.exe plugins/gbt-master/tools/cross-scan.py

产出：`.scratch/_cross_scan_panels.json`（机读）+ 屏幕摘要。
"""
import json
import pathlib
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# 控制台按 UTF-8 说中文（Windows 默认 GBK 会把中文读数糊成乱码）
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

BASE = "http://127.0.0.1:3080"
WS = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
PROFILE_NM = pathlib.Path.home() / ".dsh/profiles/web/node_modules"
OUT = WS / ".scratch/_cross_scan_panels.json"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# 额外高价值页：不在现役登记表里，但盘上存在、且有独立数据通道
EXTRA = [
    ("h1", "赏金台 · h1mcp", "holo_pet_w3/h1/index.html", True),
    ("brain", "大脑执行层 · 五维合一", "brain.html", True),
    ("avatar", "数字人形象页（成品）", "holo_pet/assets/digital-human/web/avatar.html", False),
]

# 面板的数据端点**不写死**：从 `holo_pet/panel_server.py` 的 `APP_SURFACE` 现读
# （那是它自己声明的单一来源，带 method；仓里还有双向对账测试守着它）。
# 🔴 上一版这里写死一串路径、且一律用 GET 探 —— 于是把 POST 路由（/api/social、
#    /api/research、/api/capability …）全误报成 404。**探针必须按对方声明的方法探。**
SURFACE_SRC = WS / "holo_pet/panel_server.py"


def panel_routes():
    """现读面板服务的路由表：[(route, method, title), ...]。读不到就如实回空。"""
    import re
    try:
        src = SURFACE_SRC.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out = []
    for m in re.finditer(r'\{"route":\s*"(/api/[^"]+)",\s*"method":\s*"(\w+)",\s*"title":\s*"([^"]*)"',
                         src):
        out.append((m.group(1), m.group(2), m.group(3)))
    return out


# 请求体转发的判别口令：**未知 kind** ⇒ 上游只做合法性检查就拒，零副作用（不跑任何能力），
# 而它的回话形状**取决于 body 到没到**：
#   body 到了 → `未知能力: <口令>`
#   body 丢了 → `缺少 kind`
# 这是唯一能一眼分辨「到达」与「丢失」的稳定差分。
BODY_PROBE = "/api/capability"
BODY_PROBE_PAYLOAD = '{"kind":"__gbt_cross_scan_probe__"}'
BODY_LOST_SIGN = "缺少 kind"

PORTS = [3080, 8765, 8788, 8799, 19681]


def needs_shim(rel):
    """源码登记表里声明 apiShim 的页 —— 它们的内容会被注入同源改写脚本。"""
    import re
    src = (WS / "plugins/gbt-master/lib/host.js").read_text(encoding="utf-8", errors="replace")
    return bool(re.search(r"file: '" + re.escape(rel) + r"'[^}]*apiShim: true", src))


def url_of_file(rel):
    """把工作区相对路径编成可请求的 URL 路径（中文/空格必须按段编码）。"""
    return "/".join(urllib.parse.quote(seg) for seg in rel.replace("\\", "/").split("/"))


def sse_status(url, timeout=5):
    """SSE 长流只读响应头：用裸 socket 读状态行，不读 body。

    为什么不能用 http_get：SSE 永不结束，urllib 必然超时 ⇒ 报 None，
    读的人分不清「通道断了」还是「通道正常但流不完」。裸 socket 读第一行就是真状态码。
    """
    import urllib.parse as _up
    u = _up.urlsplit(url)
    host = u.hostname or "127.0.0.1"
    port = u.port or (443 if u.scheme == "https" else 80)
    path = u.path + (("?" + u.query) if u.query else "")
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.sendall(("GET %s HTTP/1.0\r\nHost: %s:%d\r\nAccept: text/event-stream\r\n\r\n"
                   % (path, host, port)).encode())
        head = b""
        while b"\r\n\r\n" not in head and len(head) < 4096:
            chunk = s.recv(512)
            if not chunk:
                break
            head += chunk
        text = head.decode("utf-8", "replace")
        first = text.split("\r\n", 1)[0]
        code = None
        parts = first.split()
        if len(parts) >= 2 and parts[1].isdigit():
            code = int(parts[1])
        ctype = ""
        for line in text.split("\r\n"):
            if line.lower().startswith("content-type:"):
                ctype = line.split(":", 1)[1].strip()
        return (code, ctype, first[:80])
    except Exception as e:  # noqa: BLE001
        return (None, "", "%s: %s" % (type(e).__name__, str(e)[:60]))
    finally:
        try:
            s.close()
        except OSError:
            pass


def http_get(url, timeout=25):
    """返回 (status, bytes, content_type, snippet)；不改写、不跟随重定向。"""
    req = urllib.request.Request(url, headers={"User-Agent": "gbt-cross-scan/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return (r.status, len(body), r.headers.get("content-type", ""),
                    body[:120].decode("utf-8", "replace").replace("\n", " "))
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read()
        except Exception:
            pass
        return (e.code, len(body), e.headers.get("content-type", "") if e.headers else "",
                body[:120].decode("utf-8", "replace").replace("\n", " "))
    except Exception as e:  # noqa: BLE001
        return (None, 0, "", "%s: %s" % (type(e).__name__, str(e)[:90]))


def http_json(url, method="GET", payload=None, timeout=15):
    """按**声明的方法**请求，返回 (status, body_text)。

    urllib 在带 data 时会自己补 `Content-Length` —— 这一点很关键：
    反代若不把 content-length 转给上游，上游（HTTP/1.0 的 Python）读 0 字节 ⇒ 请求体丢失。
    """
    data = None
    headers = {"User-Agent": "gbt-cross-scan/1.0", "accept": "application/json"}
    if payload is not None:
        data = payload.encode("utf-8")
        headers["content-type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return (r.status, r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "replace")
        except Exception:
            pass
        return (e.code, body)
    except Exception as e:  # noqa: BLE001
        return (None, "%s: %s" % (type(e).__name__, str(e)[:80]))


def port_up(port, host="127.0.0.1", timeout=1.5):
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        try:
            s.close()
        except OSError:
            pass


def catalog():
    """目录 JSON。

    ⚠ 两个坑都长在这一条路由上，写死在这：
    ① 宿主半边原来把 `content-length` 报成 **JS 字符串字符数**（不是 UTF-8 字节数）：
       中文一多，严格客户端只读头里那个数 ⇒ **JSON 半截**（实测 4671 字节被切到 3415，
       报 Unterminated string）。v1.2.0 已修（按 Buffer.byteLength 报头）⇒ 现在能直取。
    ② 就算头修好了，**PowerShell 管道**读 curl 的 stdout 会按 GBK 解码 ⇒ 同样半截。
       要过 shell 就 `curl -o` 落盘再按 UTF-8 读，别走管道。
    """
    import subprocess as _sp  # 只在回退路径用
    try:
        req = urllib.request.Request(BASE + "/gbt-master",
                                     headers={"User-Agent": "gbt-cross-scan/1.0"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        print("  ⚠ 直取目录 JSON 失败（%s: %s）" % (type(e).__name__, str(e)[:70]))
    tmp = WS / ".scratch/_cat_probe.json"
    try:
        _sp.run(["curl.exe", "-sS", "-m", "20", "-o", str(tmp), BASE + "/gbt-master"],
                check=True, timeout=40)
        return json.loads(tmp.read_bytes().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        print("  ⚠ curl 落盘取目录也失败（%s）" % type(e).__name__)
    snap = WS / ".scratch/_gbt_catalog.json"
    if snap.exists():
        print("  ⚠ 回退到预存快照 .scratch/_gbt_catalog.json")
        return json.loads(snap.read_text(encoding="utf-8"))
    return {"error": "目录 JSON 取不到（直取 / curl / 快照 三条都失败）"}


def source_panels():
    """从盘上源码现读 PANELS 登记表的 id / file（源码是真身，不是抄来的）。"""
    src = (WS / "plugins/gbt-master/lib/host.js").read_text(encoding="utf-8", errors="replace")
    import re
    out = []
    for m in re.finditer(r"\{ id: '([a-z0-9]+)', name: '([^']*)', file: '([^']*)'", src):
        out.append({"id": m.group(1), "name": m.group(2), "file": m.group(3)})
    return out


def installed_panels():
    """从 profile 里**已装**（= 进程会加载的那份）现读登记表。

    不写死包名：profile 里可能有历史世代残留，取当前**唯一**那个 gbt-potato-master* 目录。
    找不到就如实报「没装」—— 不猜、不拿源码冒充已装。
    """
    import re
    if not PROFILE_NM.exists():
        return {"path": str(PROFILE_NM), "exists": False, "panels": []}
    cands = sorted([d for d in PROFILE_NM.iterdir()
                    if d.is_dir() and d.name.startswith("gbt-potato-master")])
    if not cands:
        return {"path": str(PROFILE_NM), "exists": False, "panels": [],
                "note": "profile 里没有 gbt-potato-master* 目录 ⇒ 没装"}
    p = cands[-1] / "lib/host.js"
    if not p.exists():
        return {"path": str(p), "exists": False, "panels": []}
    src = p.read_text(encoding="utf-8", errors="replace")
    ids = [m.group(1) for m in re.finditer(r"\{ id: '([a-z0-9]+)',", src)]
    return {"path": str(p), "exists": True, "size": p.stat().st_size,
            "panels": ids, "all_generations": [d.name for d in cands]}


def render_audit(pages):
    """真 Chrome 逐页渲染。pages = [(id, url)]"""
    from playwright.sync_api import sync_playwright
    rows = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path=CHROME, headless=True)
        for pid, url in pages:
            pg = b.new_page(viewport={"width": 1440, "height": 900})
            errs, bad = [], []
            pg.on("pageerror", lambda e: errs.append("pageerror:" + str(e)[:180]))
            pg.on("console", lambda m: errs.append("console:" + m.text[:160])
                  if m.type == "error" else None)
            pg.on("response", lambda r: bad.append("%s %s" % (r.status, r.url[:130]))
                  if r.status >= 400 else None)
            status = None
            try:
                resp = pg.goto(url, wait_until="load", timeout=40000)
                status = resp.status if resp is not None else None
            except Exception as e:  # noqa: BLE001
                errs.append("goto:" + str(e)[:140])
            pg.wait_for_timeout(5000)
            # 🔴 2026-09-22 补：**等页面安定再读数**。原来固定等 5s 就抓文字，
            # 于是数字人形象页（3.96 MB GLB + three.js 解析）被抓成
            # 「顶点 — · 三角形 — · 关节 — · 动作 —」——**看起来像页面坏了，其实只是还没加载完**
            # （本会话实测：同一页 @20s 才出 `16,017 顶点 · 12,836 三角形 · 29 关节 · idle,walk · 弹簧骨 7`）。
            # ⚠️ 只等"文字长度不变"**不够**：慢加载页在加载期间文字长度可以长时间不变 ⇒ 照样早退。
            # 所以三条任一满足才停：① 页面**自报信号**出现（`__painted` / `__gbtPanelCaps` / `#live-src` 填好）
            # ② 文字连续两次不变 ③ 上限 25s。并把"等了多久"记进读数 —— **让"慢"和"坏"分开**。
            # ⚠️ 第二轮修正：**光看"文字稳定"不够，光看"有没有画过第一帧"也不够**。
            #    数字人页的 HUD 在模型加载完之前**一直是「顶点 —」**（长度恒定）⇒ 稳定性判据会在 ~8s 早退，
            #    读数还是「—」（**误报仍在**）。所以要看**页面自己声明的"还欠着"的信号**：
            #      · 有 `#verts` 但还没数字      ⇒ 数字人页：模型还没解析完
            #      · 有 `#live-src` 但还不是 LIVE/取不到 ⇒ 总索引：台账还没读回来
            #      · 有 `#hint` 但 `__gbtPanelCaps` 还没出 ⇒ 能力球：现读还没到手
            #    任何一条"还欠着"就**不许用稳定性早退**，一直等到它到或到上限（30s）。
            PENDING_JS = ("()=>{try{"
                          "var v=document.getElementById('verts');"
                          "if(v) return /\\d/.test(v.textContent||'')?'':'verts';"
                          "var s=document.getElementById('live-src');"
                          "if(s) return /^(LIVE|取不到)/.test((s.textContent||'').trim())?'':'ledger';"
                          "if(typeof window.__gbtPanelCaps==='undefined'&&document.getElementById('hint')) return 'panelCaps';"
                          "return '';}catch(e){return '';}}")
            settle_ms, last, stable, pending0 = 0, None, 0, ""
            while settle_ms < 25000:
                try:
                    pending0 = pg.evaluate(PENDING_JS) or ""
                    cur = pg.evaluate("()=>(document.body.innerText||'').length")
                except Exception:  # noqa: BLE001
                    break
                if not pending0:
                    if cur == last:
                        stable += 1
                        if stable >= 2:
                            break
                    else:
                        stable = 0
                last = cur
                pg.wait_for_timeout(1500)
                settle_ms += 1500
            m = {"pendingAtExit": pending0}
            try:
                m = pg.evaluate("()=>({t:document.title,"
                                "txt:(document.body.innerText||'').replace(/\\s+/g,' ').trim(),"
                                "c:document.querySelectorAll('canvas').length,"
                                "h:document.body.scrollHeight,"
                                "painted:!!document.querySelector('canvas')})")
                m["pendingAtExit"] = pending0
            except Exception as e:  # noqa: BLE001
                m = {"t": "", "txt": "", "c": 0, "h": 0, "painted": False, "pendingAtExit": pending0}
                errs.append("eval:" + str(e)[:100])
            m["settleMs"] = 5000 + settle_ms
            # 画面自证：读**页面自己声明**的标志，不用我猜的位。
            # 数字人形象页声明的是 window.__painted / __spread（paintCheck 采样 24×24 亮度差 >12），
            # 主控台声明的是 body.dataset.localAvatar3d。上一版我查 body.dataset.painted ⇒ 恒为
            # null，把"页面没自证"和"我没查对地方"混成了一件事。
            proof = {}
            try:
                proof = pg.evaluate(
                    "()=>({painted:(typeof window.__painted==='boolean'?window.__painted:null),"
                    "spread:(typeof window.__spread==='number'?window.__spread:null),"
                    "paintErr:(window.__paintErr||null),"
                    "avatar3d:(document.body&&document.body.dataset?document.body.dataset.localAvatar3d:null)||null,"
                    "clip:(window.__clip||null)})")
            except Exception as e:  # noqa: BLE001
                proof = {"probe_error": str(e)[:80]}
            rows.append({"id": pid, "http": status, "title": m["t"][:70],
                         "textLen": len(m["txt"]), "canvas": m["c"],
                         "painted": m["painted"], "height": m["h"],
                         "settleMs": m.get("settleMs"),
                         "self_proof": proof,
                         "canvasSize": (pg.evaluate(
                             "()=>{const c=document.querySelector('canvas');"
                             "return c?[c.width,c.height]:null}") if m["c"] else None),
                         "head": m["txt"][:150],
                         "errCount": len(errs), "errs": errs[:4],
                         "badCount": len(bad), "bad": bad[:10]})
            pr = ""
            if proof.get("painted") is not None:
                pr = " 画面自证=%s(Δ亮度 %s)" % (proof.get("painted"), proof.get("spread"))
            elif proof.get("avatar3d"):
                pr = " 3D=%s" % proof.get("avatar3d")
            print("  [%-8s] http=%s text=%-6d canvas=%s err=%-2d bad=%-2d settle=%sms%s %s" % (
                pid, status, len(m["txt"]), m["c"], len(errs), len(bad), m.get("settleMs"), pr,
                m["txt"][:42]), flush=True)
            pg.close()
        b.close()
    return rows


def main():
    t0 = time.time()
    print("═══ ① 宿主层：三份登记表交叉对账 ═══")
    cat = catalog()
    live_ids = [p["id"] for p in cat.get("panels", [])]
    src = source_panels()
    src_ids = [p["id"] for p in src]
    inst = installed_panels()
    print("  现役（进程加载的那份）: %s  → %d 条" % (",".join(live_ids), len(live_ids)))
    print("  源码 PANELS          : %s  → %d 条" % (",".join(src_ids), len(src_ids)))
    print("  已装包登记表          : %s  → %d 条  (%s)" % (
        ",".join(inst["panels"]), len(inst["panels"]), inst["path"]))
    only_src = [i for i in src_ids if i not in live_ids]
    only_live = [i for i in live_ids if i not in src_ids]
    src_extra = [i for i in src_ids if i not in inst["panels"]]
    print("  🔴 源码有、现役没有  : %s" % (only_src or "无"))
    print("  🔴 现役有、源码没有  : %s" % (only_live or "无"))

    print("\n═══ ② 路由层：盘上真身逐个走真 HTTP ═══")
    files = []
    for p in src:
        files.append((p["id"], p["name"], p["file"], True))
    known = {f[2] for f in files}
    for e in EXTRA:
        if e[2] not in known:
            files.append(e)

    route_rows = []
    for pid, name, rel, in_src in files:
        disk = WS / rel
        # 🔴 URL 必须按段百分号编码：文件名里有中文和空格（'V22 GBT小土豆V8-可交互原型.html'），
        # 不编码的话 urllib 直接拒（InvalidURL）—— 上一版就这么把 4 个活面板误判成"路由断了"。
        url_rel = url_of_file(rel)
        st, n, ct, snip = http_get("%s/gbt-master/fs/%s" % (BASE, url_rel))
        route_rows.append({
            "id": pid, "name": name, "file": rel, "in_source_registry": in_src,
            "disk_exists": disk.exists(),
            "disk_size": disk.stat().st_size if disk.exists() else None,
            "http": st, "bytes": n, "ctype": ct, "snippet": snip[:70],
            # 声明 apiShim 的页会被注入同源改写脚本 ⇒ 字节数**本来就该**比盘上大。
            # 把「该大」和「对不上」分开报，别把正常注入当成缺陷。
            "shim_expected": bool(needs_shim(rel)),
            "size_match": (disk.exists() and (
                n == disk.stat().st_size or (needs_shim(rel) and n > disk.stat().st_size))),
        })
        print("  [%-8s] http=%-4s %8sB 盘上=%-8s 一致=%-5s%s %s" % (
            pid, st, n, disk.stat().st_size if disk.exists() else "缺失",
            str(route_rows[-1]["size_match"]),
            " (含注入)" if needs_shim(rel) else "        ", name))

    print("\n═══ ③ 运行时层：真 Chrome 逐页渲染 ═══")
    pages = [(r["id"], BASE + "/gbt-master/fs/" + url_of_file(r["file"]))
             for r in route_rows if r["http"] == 200]
    render_rows = render_audit(pages)

    print("\n═══ ④ 数据层：本机服务 + 面板路由表逐个探（按它声明的 method） ═══")
    ports = {str(p): port_up(p) for p in PORTS}
    for p, up in ports.items():
        print("  port %-6s %s" % (p, "UP" if up else "DOWN"))

    routes = panel_routes()
    print("  面板路由表（现读 panel_server.APP_SURFACE）: %d 条%s" % (
        len(routes), "" if routes else "  ⚠ 读不到"))

    # 🔴 零副作用铁律（本扫描器第一版在这里犯过错，写死当教训）：
    #   26 条路由里有一批是**会改状态**的 POST（开新线程 / 打断回合 / 受理蓝牙 / 受理对话 /
    #   审批决定 / 星云与 EigenFlux 外发 …）。第一版拿 `{}` 把 26 条**全打了一遍** ——
    #   实测后果：`/api/new-thread` 回 `{"ok": true}`（真开了新线程）、`/api/bluetooth`
    #   回 `accepted: true`（真受理了）、`/api/interrupt` 真打断了回合。
    #   ⇒ **GET 才允许真打（路由表自己声明只读）；POST 一律不盲打**，
    #     改用**静态对账**（它自己的测试口径：目录列一条，源码里就要有一条对应处理），
    #     端到端只留**一条**安全的动态钉子（`/api/capability` + 未知 kind ⇒ 只做合法性
    #     检查就拒，零副作用，且响应形状能分辨 body 到没到）。
    surface_src = SURFACE_SRC.read_text(encoding="utf-8", errors="replace")

    api_rows = []
    for path, method, title in routes:
        if path == "/api/events":       # SSE 长流：裸 socket 读状态行，不读 body
            # 🔴 上一版这里漏了 /gbt-master 前缀 ⇒ 打到 DSH 自己的网关，回 401，
            # 被我误报成"事件流断了"。真路由是 200 text/event-stream，实测过。
            code, ctype, line = sse_status(BASE + "/gbt-master" + path)
            ok = (code == 200 and "event-stream" in (ctype or ""))
            api_rows.append({"path": path, "method": method, "title": title,
                             "mode": "live-sse", "http": code, "ctype": ctype,
                             "snippet": line, "channel_ok": ok, "direct_8765": None})
            print("  %-4s %-24s 经宿主=%-5s %-30s %s" % (
                method, path, code, ctype or "—", "✅SSE通" if ok else "🔴SSE断"))
            continue

        if method != "GET":
            # POST / 其它：**不盲打**。静态对账它自己的两条真相：
            #   ① 路由表里列了这条
            #   ② 源码里有一条对应的 `parsed.path == "<route>"` 处理
            handled = ('parsed.path == "%s"' % path) in surface_src
            api_rows.append({"path": path, "method": method, "title": title,
                             "mode": "static-only(零副作用)", "handler_present": handled,
                             "http": None, "direct_8765": None})
            print("  %-4s %-24s 静态对账: 源码有处理=%s  %s" % (
                method, path, str(handled), "（会改状态 ⇒ 不盲打）"))
            continue

        # GET：路由表自己声明只读 ⇒ 允许真打（含经宿主反代这一跳）
        st, body = http_json(BASE + "/gbt-master" + path, method)
        direct = None
        if ports.get("8765"):
            dst, dbody = http_json("http://127.0.0.1:8765" + path, method, timeout=10)
            direct = {"http": dst, "body": dbody[:120]}
        api_rows.append({"path": path, "method": method, "title": title,
                         "mode": "live-get", "http": st, "body": body[:200],
                         "direct_8765": direct})
        print("  %-4s %-24s 经宿主=%-5s 直连=%-5s  %s" % (
            method, path, st, direct["http"] if direct else "n/a",
            body[:58].replace("\n", " ")))

    # ── 请求体转发钉子（缺陷 #7 的回归判据）────────────────────────────────
    # body 到了 → 上游回「未知能力: <口令>」；body 丢了 → 回「缺少 kind」。一眼可辨。
    # 选它当钉子正是因为**零副作用**：未知 kind 只做合法性检查就拒，不跑任何能力。
    post_probe = {"path": BODY_PROBE, "payload": BODY_PROBE_PAYLOAD}
    if ports.get("8765"):
        dst, dbody = http_json("http://127.0.0.1:8765" + BODY_PROBE, "POST",
                               BODY_PROBE_PAYLOAD, timeout=10)
        pst, pbody = http_json(BASE + "/gbt-master" + BODY_PROBE, "POST",
                               BODY_PROBE_PAYLOAD, timeout=15)
        post_probe.update({
            "direct_http": dst, "direct_body": dbody[:160],
            "via_host_http": pst, "via_host_body": pbody[:160],
            "body_lost_via_host": BODY_LOST_SIGN in pbody,
            "ok": (BODY_LOST_SIGN not in pbody) and (BODY_LOST_SIGN not in dbody),
        })
        print("  请求体转发钉子（零副作用）：直连 %s | 经宿主 %s → %s" % (
            dbody[:40].replace("\n", " "), pbody[:40].replace("\n", " "),
            "✅ 请求体到达" if post_probe["ok"] else "🔴 请求体丢失（反代没转 content-length）"))
    else:
        post_probe.update({"ok": None, "note": "本机服务没起，无法对照"})

    report = {
        "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "base": BASE,
        "layer1_registry": {
            "live_ids": live_ids, "source_ids": src_ids,
            "installed": inst,
            "source_not_live": only_src, "live_not_source": only_live,
            "source_not_installed": src_extra,
            "live_catalog_total": cat.get("total"), "live_catalog_present": cat.get("present"),
            "live_renders": cat.get("renders"),
        },
        "layer2_routes": route_rows,
        "layer3_render": render_rows,
        "layer4_data": {"ports": ports, "surface_count": len(routes),
                        "api": api_rows, "post_body_forwarding": post_probe},
        "elapsed_s": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n落盘：%s  (%.1fs)" % (OUT, report["elapsed_s"]))

    # ── 结论 ──
    broken = [r for r in route_rows if r["http"] != 200]
    dark = [r for r in render_rows if r["errCount"] or r["badCount"]]
    # 只读端点（GET）：经宿主拿不到任何 HTTP 响应才算断
    api_bad = [a for a in api_rows
               if a.get("mode") == "live-get" and a["http"] is None]
    # 会改状态的 POST：只查静态对账 —— 路由表列了、源码里必须有一条对应处理
    static_missing = [a["path"] for a in api_rows
                      if a.get("mode", "").startswith("static-only")
                      and not a.get("handler_present")]
    sse = [a for a in api_rows if a["path"] == "/api/events"]
    n_get = len([a for a in api_rows if a.get("mode") == "live-get"])
    n_post = len([a for a in api_rows if a.get("mode", "").startswith("static-only")])
    print("\n═══ 结论 ═══")
    print("  登记表断点: 源码有现役没有 %s ｜ 现役有源码没有 %s" % (only_src or "无", only_live or "无"))
    print("  路由断点  : %s" % ([r["id"] for r in broken] or "无"))
    print("  运行时带错: %s" % ([r["id"] for r in dark] or "无"))
    print("  数据端点  : %d 条（现读 APP_SURFACE）＝ 只读真打 %d + 会改状态静态对账 %d" % (
        len(routes), n_get, n_post))
    print("    只读连不上: %s" % ([a["path"] for a in api_bad] or "无"))
    print("    静态缺处理: %s" % (static_missing or "无"))
    print("  事件流SSE : %s" % ("✅ 通（200 text/event-stream）" if sse and sse[0].get("channel_ok")
                             else "🔴 断"))
    print("  请求体转发: %s" % (
        "✅ POST body 到达上游" if post_probe.get("ok") else
        ("🔴 POST body 丢了（反代没转 content-length）" if post_probe.get("ok") is False
         else "（本机服务没起，未对照）")))
    print("  本机服务  : %s" % {k: ("UP" if v else "DOWN") for k, v in ports.items()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
