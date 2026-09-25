# -*- coding: utf-8 -*-
"""面板内联 JS 的**语法闸**：把 `<script>…</script>`（不带 src 的那种）抽出来逐段 `node --check`。

为什么需要它：面板是**手写的单文件 HTML**，改一行 JS 没有编译期兜底 —— 浏览器只会白屏，
而"白屏"在 `/gbt-master` 目录里只表现为 `size` 正常、`exists=true`（**看目录是看不出来的**）。
本会话改 `capabilities.html`（把写死的 183/31 改成现读重建）时就是靠它先过语法、再上真 Chrome 验证。

用法：
    py -3.14 plugins/gbt-master/tools/check-panel-syntax.py capabilities.html
    py -3.14 plugins/gbt-master/tools/check-panel-syntax.py --all      # 走 /gbt-master 目录把 12 个面板全过一遍
    py -3.14 plugins/gbt-master/tools/check-panel-syntax.py --negctl   # 负控：坏夹具必须变红（不碰真面板）
退出码：0 = 各段都过；1 = 有语法错/importmap 坏（--negctl 失败也退 1）；3 = 取不到面板目录（前置不可达）。
查两样：① 内联 JS（含 `type="module"`）走 `node --check`；② `type="importmap"` 按 JSON 验合法性 + 形状。
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
CATALOG = "http://127.0.0.1:3080/gbt-master"


def targets(argv: list[str]) -> list[pathlib.Path]:
    if "--all" in argv:
        # ⚠️ 「取不到面板目录」≠「面板语法坏了」—— 本轮实测踩到一次：宿主目录接口偶发超时，
        #    旧写法直接 print 一句 + exit 1，看起来像"12 个面板有语法错"，**是假红**。
        #    现在：重试 3 次（退避）；仍取不到就**用 3 号退出码**明确报"前置不可达"，
        #    并提示可用显式文件列表绕过（`check-panel-syntax.py a.html b.html`）。
        last = ""
        for attempt, wait in enumerate((0, 1.5, 3.0)):
            if wait:
                time.sleep(wait)
            try:
                cat = json.loads(urllib.request.urlopen(CATALOG, timeout=20).read().decode("utf-8"))
                return [ROOT / (p.get("path") or p.get("file") or "") for p in cat.get("panels", [])]
            except Exception as e:  # noqa: BLE001
                last = "%s: %s" % (type(e).__name__, e)
                print("   ⚠ 第 %d 次取面板目录失败：%s" % (attempt + 1, last))
        print("🔴 取不到面板目录（重试 3 次后仍失败）：%s" % last)
        print("   这**不是**语法结论 —— 前置不可达（宿主目录接口没答）。"
              "可直接给文件列表绕过：check-panel-syntax.py index.html capabilities.html …")
        raise SystemExit(3)
    return [pathlib.Path(a) for a in argv if not a.startswith("--")]


def check(f: pathlib.Path, tmp: pathlib.Path) -> int:
    if not f.is_file():
        print("🔴 不在：%s" % f)
        return 1
    html = f.read_text(encoding="utf-8", errors="replace")
    # ⚠️ 只查**JS**：`<script type="importmap">` 里是 JSON，`node --check` 必然报
    #    `Unexpected token ':'` —— 第一版没看 type，于是把 avatar.html / index.html 的
    #    importmap 误报成"语法错"（**门报红先怀疑门**，第 7 次）。
    # 🔴 但"跳过它"当时跳**过头**了（2026-09-22 晚抓到的门盲区）：`continue` 一走了之，
    #    于是 importmap **一次都没被验过**。它是**载荷声明**：JSON 坏 / `imports` 不是对象 ⇒
    #    模块解析直接失败 ⇒ 页面白屏，而宿主目录里 `exists=true`、`size` 正常，
    #    **恰是本闸存在的理由**（"白屏看不出"）。现在按 JSON 单独验一遍，不再往下漏。
    blocks, importmaps = [], []
    for m in re.finditer(r"<script([^>]*)>(.*?)</script>", html, re.S):
        attrs, body = m.group(1), m.group(2)
        if "src=" in attrs.lower():
            continue
        tm = re.search(r'type\s*=\s*["\']?([\w/+.-]+)', attrs, re.I)
        kind = (tm.group(1) if tm else "text/javascript").lower()
        if kind == "importmap":
            importmaps.append(body)
            continue
        if kind not in ("text/javascript", "module", "application/javascript", "text/ecmascript"):
            continue
        blocks.append(body)

    bad = 0
    # ① importmap（JSON 侧）：合法性 + 形状
    for i, body in enumerate(importmaps):
        try:
            d = json.loads(body)
        except Exception as e:  # noqa: BLE001
            bad += 1
            print("   🔴 %s importmap %d 不是合法 JSON：%s" % (f.name, i, str(e)[:140]))
            continue
        if not isinstance(d, dict):
            bad += 1
            print("   🔴 %s importmap %d 顶层不是对象（是 %s）" % (f.name, i, type(d).__name__))
        elif "imports" in d and not isinstance(d["imports"], dict):
            bad += 1
            print("   🔴 %s importmap %d 的 `imports` 不是对象（是 %s）"
                  % (f.name, i, type(d["imports"]).__name__))

    # ② 内联 JS（语法侧）
    for i, b in enumerate(blocks):
        p = tmp / ("%s-%d.mjs" % (f.stem, i))
        p.write_text(b, encoding="utf-8")
        r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
        if r.returncode != 0:
            bad += 1
            first = (r.stderr or "").strip().splitlines()
            print("   🔴 %s 段 %d 语法错：%s" % (f.name, i, first[0][:160] if first else "?"))
            for line in first[1:5]:
                print("      " + line[:160])
    # 汇总行**必须把 importmap 段数报出来** —— 只报 "script 0 段 · 通过" 会让
    # 一个只有 importmap 的页面看起来"没查也通过"。
    print("   %s %-34s 内联 script %d 段 + importmap %d 段 · %s"
          % ("✅" if bad == 0 else "🔴", f.name, len(blocks), len(importmaps),
             "通过" if bad == 0 else "%d 处有错" % bad))
    return bad


def negctl() -> int:
    """负控：四种夹具必须给出**四种预设结论**。夹具写在临时目录里，**不碰真面板**。

    为什么它必须常驻：本闸曾经把 `importmap` 整个 `continue` 掉 ⇒ **一次都没验过**，
    而"没验过"在输出上长得跟"验过了没问题"一模一样（`内联 script 0 段 · 通过`）。
    只有把"坏输入必须变红"钉成可复跑的检查，这道门才不会第二次烂掉。
    """
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="panel-syntax-negctl-"))
    cases = [
        # (夹具名, 内容, 期望"变红"吗)
        ("imap_bad_json",
         '<!doctype html><script type="importmap">'
         '{"imports":{"three":"/a.js",}}</script><script>const ok=1;</script>', True),
        ("imap_wrong_shape",
         '<!doctype html><script type="importmap">{"imports":"three"}</script>'
         '<script>const ok=1;</script>', True),
        ("imap_not_object",
         '<!doctype html><script type="importmap">[1,2]</script>'
         '<script>const ok=1;</script>', True),
        ("js_syntax_error",
         '<!doctype html><script type="importmap">{"imports":{"three":"/a.js"}}</script>'
         '<script>const a = (1;</script>', True),
        ("clean_positive",
         '<!doctype html><script type="importmap">{"imports":{"three":"/a.js"}}</script>'
         '<script type="module">import * as T from "three"; const ok = T;</script>', False),
    ]
    wrong = []
    for name, html, want_red in cases:
        p = tmp / (name + ".html")
        p.write_text(html, encoding="utf-8")
        got_red = check(p, tmp) > 0
        mark = "✅" if got_red == want_red else "🔴"
        print("   %s 负控 %-18s 期望%s · 实得%s" % (mark, name, "红" if want_red else "绿",
                                                "红" if got_red else "绿"))
        if got_red != want_red:
            wrong.append(name)
    if wrong:
        print("🔴 负控失败：%s —— 闸对自己的坏输入不敏感（等于没这道门）" % "、".join(wrong))
        return 1
    print("✅ 负控通过：%d 支夹具全部给出预设结论（importmap 坏/形状错/非对象/JS 语法错都变红，干净页保持绿）"
          % len(cases))
    return 0


def main(argv: list[str]) -> int:
    if "--negctl" in argv:
        return negctl()
    files = targets(argv)
    if not files:
        print("用法：check-panel-syntax.py <面板.html> … 或 --all")
        return 1
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="panel-syntax-"))
    bad = sum(check(f, tmp) for f in files)
    print("结论：%d 个面板 · %s" % (len(files), "全部通过" if bad == 0 else "%d 段有语法错" % bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
