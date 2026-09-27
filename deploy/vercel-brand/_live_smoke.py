# -*- coding: utf-8 -*-
"""GBT小土豆V8 · 品牌主页 · 真实 socket 冒烟（本地起服 → 打真实端口 → 关服）

⛔ 开发者：自由的风 · 永久钢印 · 禁止删除

为什么不用 test_client：test_client 走的是 WSGI 短路，不经过 socket、不经过
Werkzeug 的 HTTP 解析。这里要证的是「真的起得来、真的答得了」。

为什么用 http.client 而不是 urllib/requests：
  本机存在环境代理劫持（http_proxy/https_proxy 指向回环端口），
  urllib 会读环境变量，把「服务没起」伪装成「502 Bad Gateway」。
  http.client 不读任何代理环境变量 —— 从机理上绕开，而不是靠参数祈祷。

用法：python _live_smoke.py [port]
退出码：0 = 四路全绿；1 = 有 FAIL。
"""
from __future__ import annotations

import http.client
import json
import socket
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from api import index as site  # noqa: E402
from werkzeug.serving import make_server  # noqa: E402


def _free_port(prefer: int) -> int:
    for p in range(prefer, prefer + 40):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise RuntimeError("找不到空闲端口")


def main() -> int:
    port = _free_port(int(sys.argv[1]) if len(sys.argv) > 1 else 5099)
    srv = make_server("127.0.0.1", port, site.app, threaded=True)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    print("=" * 78)
    print("GBT小土豆V8 · 品牌主页 · 真实 socket 冒烟")
    print("=" * 78)
    print("监听：http://127.0.0.1:%d   （http.client 直连，不读代理环境变量）" % port)
    print("-" * 78)

    # 等端口真的 accept（最多 3s）
    t0 = time.time()
    while time.time() - t0 < 3:
        with socket.socket() as s:
            s.settimeout(0.2)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(0.05)

    fails = []

    def probe(path: str, want_code: int, note: str, want_png: bool = False):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            c.request("GET", path)
            r = c.getresponse()
            body = r.read()
        finally:
            c.close()
        code_ok = r.status == want_code
        png_ok = (body[:8] == b"\x89PNG\r\n\x1a\n") if want_png else True
        ok = code_ok and png_ok
        print("[%s] %-14s → %d  %-32s %7d B  %s"
              % ("OK  " if ok else "FAIL", path, r.status,
                 r.getheader("Content-Type") or "-", len(body), note))
        for h in ("X-GBT-Brand", "Cache-Control", "Server"):
            v = r.getheader(h)
            if v:
                print("        %s: %s" % (h, v))
        if not ok:
            fails.append("%s (code=%d want=%d png=%s)" % (path, r.status, want_code, png_ok))

        # 附带断言
        if path == "/":
            txt = body.decode("utf-8", "replace")
            needle = [site.BRAND, site.SIGNATURE, "Capability Hub", "--gbt-violet:#7C4DFF"]
            miss = [n for n in needle if n not in txt]
            print("        断言：品牌名/署名/顶栏副标/三色定义 → %s"
                  % ("全部命中" if not miss else "缺 %s" % miss))
            if miss:
                fails.append("/ 断言缺 %s" % miss)
        if path == "/api/status":
            try:
                j = json.loads(body.decode("utf-8"))
                print("        JSON：%s" % json.dumps(j, ensure_ascii=False))
            except Exception as exc:
                fails.append("/api/status JSON 解析失败 %r" % (exc,))
        if path == "/healthz":
            print("        体：%s" % body.decode("utf-8", "replace"))
        return r

    probe("/", 200, "服务端渲染品牌主页")
    probe("/api/status", 200, "站点自身读数")
    probe("/og.png", 200, "分享卡图（PNG 魔数校验）", want_png=True)
    probe("/healthz", 200, "探活")

    srv.shutdown()
    print("-" * 78)
    if fails:
        print("结论：FAIL —— %s" % "; ".join(fails))
        return 1
    print("结论：ALL PASS —— 真端口四路全绿。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
