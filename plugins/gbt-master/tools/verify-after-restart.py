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
| ⑨ 三块上下文进了进程 | `/gbt-master` 的 `contexts` 字段（**进程自报**我注册成功了哪几块） | 面板/数字人/台账三块都在且 ok |

🔴 ⑨ 是 2026-09-26 第 53 轮补的（F18）。此前 ④⑥ 两项都从**盘上**的装机副本渲染 ——
它们能证明"代码对"，**证明不了"进程里有没有"**。代价已经付过一次：台账块
2026-09-25 21:03:15 加进宿主半边时**没动版本号**，进程又是 10:33:32 启动的 ⇒
① 读「1.8.1 == 1.8.1」判 ✅，而进程里**根本没有台账块**，
主人要的「重启之后自动读取」一直没生效，所有闸却全绿。

用法：py -3.14 plugins/gbt-master/tools/verify-after-restart.py
退出码：0 = 各项都到位；1 = 还有没到位的（逐条列出"现在是什么、该是什么、怎么做"）。
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
# 🔴 2026-09-25 自纠（实测到的一次**假红**）：② 的判据是
#    `latency < 1.5`，而这是**本机 HTTP 往返**的墙钟读数 —— 我自己的后台活儿
#    （跑全套测试/审计器）压着 CPU 与内存时，同一发能读到 >1.5 s ⇒ ② 变 ⏳。
#    现场：20:51 那次靴自检读到「还有 2 项没到位」，而单独跑同一张单只有 1 项（⑤）。
#    本条**不是把判据改松**（阈值、口径一字未动）：慢发**重测一次**，
#    判据仍用同一个 1.5 s，读数把两次都印出来 —— 只把"我自己占用机器"造成的
#    抖动与"实现真的慢"分开。重测还慢 ⇒ 照红，并且明说重测过。
cat, latency, err = None, None, ""
lat_first = None
for attempt in range(3):
    t0 = time.time()
    try:
        with urllib.request.urlopen(BASE, timeout=30) as r:
            cat = json.loads(r.read().decode("utf-8"))
        latency = time.time() - t0
        # 第一次就慢 ⇒ 再测一次（不换判据，只把抖动与真慢分开）
        if latency >= 1.5 and lat_first is None:
            lat_first = latency
            time.sleep(0.2)
            continue
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
    _lat_now = ("本次 %.2f s" % (latency or -1)) if lat_first is None else \
               ("本次 %.2f s（上一发 %.2f s 偏慢，按同一阈值重测过一次）" % (latency or -1, lat_first))
    add(latency is not None and latency < 1.5, "② 目录路由提速",
        "%s（旧实现是 13 个顺序 await，实测 8–10 s）" % _lat_now,
        "< 1.5 s ⇒ 说明 Promise.all 那版已装载（重测仍超才算慢）")
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

# ── ⑥ 排查台账块（Owner 令：重启后自动读取；正/负对照都要在） ─────────────────
# 🔴 2026-09-25 加：验收单原来**只验了两块**（面板 / 数字人），台账这块是新加的第三块 ——
#    不验它，就等于"新增的自动读取"没人管。判据四条：块在 · 四个字段都在 ·
#    负对照如实说"读不到" · **且真的跑了装机副本**（否则"重启后生效"无从谈起）。
probe_ok = probe.exists()
if probe_ok:
    try:
        r = subprocess.run(["node", str(probe)], cwd=str(ROOT), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
        out = (r.stdout or "") + (r.stderr or "")
        has_block = "【GBT小土豆V8 · 故障排查台账" in out
        has_fields = all(k in out for k in ("台账时间点", "没做", "未清故障", "等你拍板"))
        neg_honest = "台账文件读不到" in out
        ran_installed = "正对照·装机副本" in out
        add(has_block and has_fields and neg_honest and ran_installed,
            "⑥ 排查台账块（正/负对照 · 含装机副本）",
            "块=%s · 四字段=%s · 负对照如实=%s · 跑了装机副本=%s"
            % (has_block, has_fields, neg_honest, ran_installed),
            "台账块在、四字段齐、读不到时如实上报，且装机副本也真跑了一遍")
    except Exception as e:  # noqa: BLE001
        add(False, "⑥ 排查台账块（正/负对照 · 含装机副本）", "跑不动：%s" % e,
            "node plugins/gbt-master/tools/verify-state-injection.mjs")
else:
    add(False, "⑥ 排查台账块（正/负对照 · 含装机副本）", "探针不在：%s" % probe,
        "node plugins/gbt-master/tools/verify-state-injection.mjs")

# ── ⑦ 装机副本漂移闸（**改了源稿就得同步，否则重启也白搭**） ─────────────────
# 🔴 2026-09-25 加。当天实测：装机副本的 host.js 比源稿**少 3,309 B** ⇒
#    光改工作区源稿、重启加载的还是旧副本（"看起来改了、其实没改"）。
#    ④ 项自称"装机副本实跑"，但它当时 import 的是**源稿** ⇒ 这类漂移它根本测不出来。
#    所以单列一项，直接跑那个专门管漂移的闸。
drift_gate = ROOT / "plugins" / "gbt-master" / "tools" / "verify-installed-copy.mjs"
if drift_gate.exists():
    try:
        r = subprocess.run(["node", str(drift_gate)], cwd=str(ROOT), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=120)
        ok = r.returncode == 0
        add(ok, "⑦ 装机副本与源稿逐字节一致",
            "漂移闸退出码=%d%s" % (r.returncode, "" if ok else "（有漂移 ⇒ 跑 --fix 同步）"),
            "node plugins/gbt-master/tools/verify-installed-copy.mjs 退出码 0")
    except Exception as e:  # noqa: BLE001
        add(False, "⑦ 装机副本与源稿逐字节一致", "跑不动：%s" % e, "node verify-installed-copy.mjs")
else:
    add(False, "⑦ 装机副本与源稿逐字节一致", "漂移闸不在：%s" % drift_gate,
        "plugins/gbt-master/tools/verify-installed-copy.mjs 应当在")

# ── ⑧ 注入面诚实性（**下一轮会话读到的每一段字都得是真的**） ───────────────────
# 🔴 2026-09-25 加。理由：第 20-25 轮发现「喂给模型的文本」连撞四处假账
#    （总数打架 / 调用法是死的 / 自检命令崩 / 安全段是假的）。台账块是**新加的一段注入** ——
#    它自己也可能变成第五处。⇒ 单列一项，跑那条收口判据。
honesty = ROOT / "tools" / "codex-scripts" / "audit-injection-honesty.py"
if honesty.exists():
    try:
        r = subprocess.run([sys.executable, str(honesty), "--json"], cwd=str(ROOT),
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=300)
        raw = r.stdout or ""
        i = raw.find("{")
        rep = json.loads(raw[i:]) if i >= 0 else {}
        n = int(rep.get("problem_count") or 0)
        add(n == 0, "⑧ 注入面诚实性（0 假账）",
            "查了 %s 段注入 · 假账 %d 条%s" % (rep.get("blocks"), n,
                                        "" if n == 0 else "：" + str(rep.get("problems"))[:160]),
            "python tools/codex-scripts/audit-injection-honesty.py 退出码 0")
    except Exception as e:  # noqa: BLE001
        add(False, "⑧ 注入面诚实性（0 假账）", "跑不动：%s" % e,
            "python tools/codex-scripts/audit-injection-honesty.py --json")
else:
    add(False, "⑧ 注入面诚实性（0 假账）", "判据不在：%s" % honesty,
        "tools/codex-scripts/audit-injection-honesty.py 应当在")

# ── ⑨ 三块上下文**真的进了进程**（第 53 轮 · F18）────────────────────────────
# 🔴 为什么要单列这一项：宿主半边**只在进程启动时装载**，而 ④⑥ 两项都是拿**盘上**的
#    装机副本渲染出来的 ⇒ 它们能证明"代码对"，**证明不了"进程里有没有"**。
#    实测代价：台账块 2026-09-25 21:03:15 加进宿主半边，而 version 留在 1.8.1 没动，
#    进程是 10:33:32 启动的 ⇒ ① 读「1.8.1 == 1.8.1」判 ✅，**而进程里根本没有台账块**。
#    用 Cordis 探针现读进程内已注册上下文，只有 4 块：
#    `sandbox:policy` / `approval:policy` / `gbt-master-panels` / `gbt-digital-human`。
#    主人要的「重启之后自动读取」因此**一直没生效**，而所有闸全绿。
#    ⇒ 本条直接读 `/gbt-master` 的 `contexts` 字段（进程自报"我注册成功了哪几块"）。
EXPECT_CONTEXTS = ("gbt-master-panels", "gbt-digital-human", "gbt-progress-ledger")
if cat is None:
    add(False, "⑨ 三块上下文进了进程", "取不到 /gbt-master", "contexts 含 %s" % (EXPECT_CONTEXTS,))
else:
    live_ctx = cat.get("contexts")
    if not isinstance(live_ctx, list):
        add(False, "⑨ 三块上下文进了进程",
            "payload 里没有 contexts 字段（现读 version=%s）" % cat.get("version"),
            "宿主半边自报 contexts=[[name,order,ok,error],…] ⇒ 说明跑的还是没这个字段的旧代码，重启")
    else:
        got = {str(c.get("name")): bool(c.get("ok")) for c in live_ctx if isinstance(c, dict)}
        missing = [n for n in EXPECT_CONTEXTS if n not in got]
        failed = [n for n in EXPECT_CONTEXTS if got.get(n) is False]
        add(not missing and not failed, "⑨ 三块上下文进了进程",
            "进程自报 %d 块：%s · 缺=%s · 注册失败=%s"
            % (len(got), "、".join(sorted(got)), missing or "无", failed or "无"),
            "contexts 必须含 %s 且三块 ok 都为真（缺哪块就说明宿主代码没换到那一版）"
            % (EXPECT_CONTEXTS,))

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
# 结论**不许写死项数**：这张单从 5 项长到 9 项，写死一次就过期一次（本仓老账）。
print("结论：%s" % ("%d 项全部到位 ✅" % len(rows) if not bad
                  else "共 %d 项，还有 %d 项没到位（上面带 ⏳ 的）" % (len(rows), len(bad))))
raise SystemExit(1 if bad else 0)
