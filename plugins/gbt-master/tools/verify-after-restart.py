# -*- coding: utf-8 -*-
"""**重启后验收单** —— 把"等主人动手"的那几件变成一条命令，逐条给"好了 / 还没"。

背景：本轮之前有几件事**必须由进程重启或页面重载才生效**（宿主半边在启动时装载、
客户端 bundle 靠一次 F5）。它们散在 README 各处，容易"以为做了"。这份验收单把它们收成一张表：

| 项 | 判据（现读） | 现在该是 |
|---|---|---|
| ① 宿主机代码换代 | `GET /gbt-master` 的 `version`（源稿现报 **1.8.1**；旧进程报 1.8.0） | 1.8.1 |
| ② 目录路由提速 | 同一请求的耗时（旧实现 = **13 个顺序 await**，实测 8–10 s；新实现 ≈1 次往返） | < 1500 ms |
| ③ 品牌位真的生效 | `/gbt-master` 的 `clientDiag`：`gen == gbt-potato-master-v9` 且 `diag` 含 hero/sideMark/sideName 三个 ok（**页面自报**） | 三项 ok |
| ④ 注入上下文是新文案 | 把**装机副本**的 host.js 装进假 ctx 跑一遍，读两段上下文：品牌行必须是三分支里的"已按本代加载"、数字人块不许出现 `undefined` | 是 |
| ⑤ 旧 specifier 可清 | profile 依赖里 `gbt-potato-master-v6 / -v8` 是否还在（在 = 还没清，见 README §4.8；**清之前必须先重启**） | 已清 |

用法：py -3.14 plugins/gbt-master/tools/verify-after-restart.py
退出码：0 = 五项都到位；1 = 还有没到位的（逐条列出"现在是什么、该是什么、怎么做"）。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "gbt_allinone").is_dir())
BASE = "http://127.0.0.1:3080/gbt-master"
SRC_VERSION = None
try:
    _h = (ROOT / "plugins" / "gbt-master" / "lib" / "host.js").read_text(encoding="utf-8")
    SRC_VERSION = (re.search(r"version:\s*'([\d.]+)'", _h) or [None, None])[1]
except OSError:
    pass

rows: list[tuple[bool, str, str, str]] = []   # (ok, 项, 现读, 该是/怎么做)


def add(ok: bool, name: str, now: str, want: str) -> None:
    rows.append((bool(ok), name, now, want))


# ── ①②③ 一次 GET 拿三样 ───────────────────────────────────────────────────
cat, latency, err = None, None, ""
for attempt in range(3):
    t0 = time.time()
    try:
        with urllib.request.urlopen(BASE, timeout=30) as r:
            cat = json.loads(r.read().decode("utf-8"))
        latency = time.time() - t0
        break
    except Exception as e:  # noqa: BLE001
        err = "%s: %s" % (type(e).__name__, e)
        time.sleep(1.5)
if cat is None:
    add(False, "① 宿主机代码换代", "取不到 /gbt-master（%s）" % err, "HTTP 200 + version=%s" % SRC_VERSION)
    add(False, "② 目录路由提速", "同上", "< 1500 ms")
    add(False, "③ 品牌位真的生效", "同上", "clientDiag.gen=v9 且三项 ok")
else:
    live_ver = str(cat.get("version"))
    add(live_ver == str(SRC_VERSION), "① 宿主机代码换代",
        "进程自报 version=%s" % live_ver, "源稿是 %s ⇒ 重启后应报 %s" % (SRC_VERSION, SRC_VERSION))
    add(latency is not None and latency < 1.5, "② 目录路由提速",
        "本次 %.2f s（旧实现是 13 个顺序 await，实测 8–10 s）" % (latency or -1),
        "< 1.5 s ⇒ 说明 Promise.all 那版已装载")
    cd = cat.get("clientDiag") or {}
    diag = cd.get("diag") or []
    ok3 = (cd.get("gen") == "gbt-potato-master-v9"
           and all(any(d.startswith(k + ":ok") for d in diag) for k in ("hero", "sideMark", "sideName")))
    add(ok3, "③ 品牌位真的生效（页面自报）",
        "gen=%s · diag=%s · at=%s" % (cd.get("gen"), diag, cd.get("at")),
        "gen=gbt-potato-master-v9 且 hero/sideMark/sideName 三个 ok（没做过就按一次 F5）")

# ── ④ 装机副本的注入上下文（用假 ctx 真跑一遍） ─────────────────────────────
INSTALLED = Path.home() / ".dsh" / "profiles" / "web" / "node_modules" / "gbt-potato-master-v9" / "lib" / "host.js"
probe = ROOT / "plugins" / "gbt-master" / "tools" / "verify-state-injection.mjs"
if INSTALLED.exists() and probe.exists():
    try:
        r = subprocess.run(["node", str(probe)], cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        out = (r.stdout or "") + (r.stderr or "")
        has_branch = "已按本代加载" in out or "尚未在任何页面生效" in out
        no_undef = "undefined" not in out
        # 内存里的进程文案与装机副本无关；这里只断言"装机副本装出来的上下文是新文案且无 undefined"
        add(has_branch and no_undef, "④ 注入上下文是新文案（装机副本实跑）",
            "品牌三分支文案=%s · 含 undefined=%s" % (has_branch, not no_undef),
            "有三分支文案且不含 undefined（verify-state-injection.mjs 实跑）")
    except Exception as e:  # noqa: BLE001
        add(False, "④ 注入上下文是新文案（装机副本实跑）", "跑不动：%s" % e, "node verify-state-injection.mjs")
else:
    add(False, "④ 注入上下文是新文案（装机副本实跑）",
        "装机副本或探针不在（%s）" % INSTALLED, "先跑 verify-installed-copy.mjs --fix")

# ── ⑤ 旧 specifier 清理（可选，重启后才允许） ───────────────────────────────
pkg = Path.home() / ".dsh" / "profiles" / "web" / "package.json"
stale = []
try:
    deps = json.loads(pkg.read_text(encoding="utf-8")).get("dependencies", {})
    stale = [k for k in deps if re.match(r"^gbt-potato-master-v\d+$", k) and k != "gbt-potato-master-v9"]
except Exception:  # noqa: BLE001
    pass
add(not stale, "⑤ 旧 specifier 已清（可选）",
    "还在：%s" % ("、".join(stale) if stale else "无"),
    "重启**之后**才允许清（README §4.8：先重启再删，顺序反了就是红页事故）")

# ── 输出 ──────────────────────────────────────────────────────────────────
print("=" * 92)
print("重启后验收单 · 共 %d 项" % len(rows))
print("=" * 92)
for ok, name, now, want in rows:
    print("  %s %-34s" % ("✅" if ok else "⏳", name))
    print("       现读：%s" % now)
    if not ok:
        print("       该是：%s" % want)
bad = [r for r in rows if not r[0]]
print("-" * 92)
print("结论：%s" % ("五项都到位 ✅（宿主机换代 · 提速 · 品牌生效 · 上下文新文案 · 旧 specifier 已清）"
                  if not bad else "还有 %d 项没到位（上面带 ⏳ 的）" % len(bad)))
raise SystemExit(1 if bad else 0)
