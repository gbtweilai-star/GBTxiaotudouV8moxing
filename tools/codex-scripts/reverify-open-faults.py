#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""**未清故障的『前提还成立吗』复核器**（只读 · 离线为主）

为什么要有这一件（一手账）：
  第 37 轮我抓到一件难看的事 —— **F1 与 F6 两条高危故障挂了十几轮，而它们的前提
  （"4 批改动没部署"）是我推的、从来没验过**；只花一个免费 GET 就读出来前提早就不成立了。
  ⇒ 故障清单会**无声腐烂**：写下的那一刻是真的，之后没人再读一次，就变成账里的假话。
  所以：**每条未清故障都要能回答"凭什么现在还算数"**，答不上来的要么补读数、要么结掉。

它怎么做：从 `state/排查台账.json` 的 `open_faults` 取现有条目，按 id 跑一条**探针**，
给出**新鲜读数**，并判三态之一：
  · `仍成立`   —— 探针读出来，前提现在还是真的
  · `已不成立` —— 读出来前提已经没了（**这一条会让本器退出码非零**，逼人回去改账）
  · `需人读`   —— 机器判不了（静态引用、语义问题），如实说"要人看"，**不假装判过**

口径（三条）：
  1. **没有探针 ≠ 通过**：没写探针的 id 一律报 `需人读`，不许默认绿。
  2. **凭据只报存在与长度**，绝不打印值（连掩码都只给前 4 位）。
  3. 只读：不改台账、不写盘、默认不出网（F4 那条是**回环** TCP，不算出网）。

用法：python tools/codex-scripts/reverify-open-faults.py [--json]
退出码：0 = 没有"已不成立"；1 = 至少一条前提已垮（回台账改去）；2 = 台账读不动。
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "state" / "排查台账.json"

KEY_NAMES = ["DEEPSEEK_API_KEY", "MOONSHOT_API_KEY", "KIMI_API_KEY", "OPENAI_API_KEY",
             "TRIPO_API_KEY", "AGNES_API_KEY", "FREELLMAPI_API_KEY", "ABLITERATION_API_KEY"]


def _mask(v: str) -> str:
    v = (v or "").strip()
    return (v[:4] + "****(%d)" % len(v)) if v else "（空）"


# ── F2：密钥在 User 作用域，进程/子进程看不到 ──────────────────────────────
def probe_f2() -> tuple:
    env_hits = {k: _mask(os.environ.get(k, "")) for k in KEY_NAMES if os.environ.get(k)}
    user_hits = {}
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            i, names = 0, []
            while True:
                try:
                    names.append(winreg.EnumValue(k, i)[0])
                    i += 1
                except OSError:
                    break
        for n in KEY_NAMES:
            if n in names:
                user_hits[n] = "在（长度不读）"
    except Exception as exc:  # noqa: BLE001
        user_hits["<注册表读不到>"] = type(exc).__name__
    dotenv = ROOT / ".env"
    dot = {}
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k = line.split("=", 1)[0].strip()
                if k:
                    dot[k] = "有值" if line.split("=", 1)[1].strip() else "空"
    still = (not env_hits) and bool(user_hits)
    return ("仍成立" if still else "已不成立"), {
        "进程可见": env_hits or "一个都没有",
        "User 作用域在册": user_hits,
        ".env 里的键": dot or "（无 .env 或无键）",
    }


# ── F3：preflight 异常 fail-open ───────────────────────────────────────────
def probe_f3() -> tuple:
    f = ROOT / "gbt_allinone" / "api.py"
    if not f.is_file():
        return "需人读", {"说明": "api.py 不在"}
    lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    hits = [(i + 1, l.strip()) for i, l in enumerate(lines)
            if "preflight" in l.lower() and ("except" in l or "log" in l or "except" in l)]
    seg = [(i + 1, l.rstrip()) for i, l in enumerate(lines[1570:1600], start=1570)]
    has_return_in_except = any("return" in l or "raise" in l for _n, l in seg)
    return "需人读", {
        "api.py 里带 preflight 的异常/留痕行": ["%d: %s" % h for h in hits[:6]],
        "原引用段 1571-1600 里有没有 return/raise（有=已收紧）": has_return_in_except,
        "结论": "机器判不了『该不该收紧』—— 这是语义问题，需人读（甲=收紧 / 乙=只加可观测）",
    }


# ── F4：gbt-free 死路由 127.0.0.1:31415 ───────────────────────────────────
def probe_f4() -> tuple:
    cfg_hits = []
    for p in list((ROOT / "gbt_allinone").rglob("*.py")) + list((ROOT / "tools" / "codex-scripts").glob("*.py")):
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "31415" in t:
            cfg_hits.append(str(p.relative_to(ROOT)))
    alive = False
    s = socket.socket()
    s.settimeout(1.0)
    try:
        s.connect(("127.0.0.1", 31415))
        alive = True
    except Exception:  # noqa: BLE001
        alive = False
    finally:
        s.close()
    return ("已不成立" if alive else "仍成立"), {
        "回环 127.0.0.1:31415": "通（有东西在听）" if alive else "不通（超时/拒绝）",
        "还引用 31415 的源码": cfg_hits[:6],
    }


# ── F5：cross_scan 的 D/E/F/V 只有名字没有实现 ─────────────────────────────
def probe_f5() -> tuple:
    """⚠️ 首版这里栽了一次，记下来：`_DIMS_NOT_IMPL` 是**定义在函数内部**的常量
    （`cross_scan.py:459`，缩进 4 空格）⇒ `getattr(module, ...)` 拿不到 ⇒ 我的探针
    把"**没读到**"直接判成了"**已不成立**"。那正是本器存在的理由的反面。
    ⇒ 改成两层：先试模块属性；拿不到就**静态读源码**（`ast.literal_eval` 解析那行字面量）；
    两层都拿不到才报 `需人读`。**永远不允许由"读不到"推出"已不成立"。**
    """
    # 一层：模块属性
    sys.path.insert(0, str(ROOT))
    try:
        from gbt_allinone import cross_scan as cs
        not_impl = getattr(cs, "_DIMS_NOT_IMPL", None)
        if not_impl is not None:
            return ("仍成立" if not_impl else "已不成立"), {
                "来源": "模块属性 _DIMS_NOT_IMPL（模块级）",
                "声明未实现的维度": list(not_impl),
            }
    except Exception as exc:  # noqa: BLE001
        _imp = "%s: %s" % (type(exc).__name__, str(exc)[:80])
    else:
        _imp = "模块属性里没有这个名字（它定义在函数内部）"

    # 二层：静态读源码
    f = ROOT / "gbt_allinone" / "cross_scan.py"
    if f.is_file():
        import ast
        import re
        txt = f.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"_DIMS_NOT_IMPL\s*=\s*(\[[^\]]*\])", txt)
        if m:
            try:
                vals = ast.literal_eval(m.group(1))
            except Exception:  # noqa: BLE001
                vals = None
            if vals is not None:
                ln = txt[: m.start()].count("\n") + 1
                return ("仍成立" if vals else "已不成立"), {
                    "来源": "静态读源码 cross_scan.py:%d（模块属性拿不到）" % ln,
                    "声明未实现的维度": vals,
                    "为什么走这条": _imp,
                }
    return "需人读", {"说明": "模块属性与源码两处都没读到 _DIMS_NOT_IMPL —— **读不到 ≠ 不成立**",
                     "模块属性一层": _imp, "_读不到_主数据": True}


# ── F8：mcporter 引用的目录没进版本库 ─────────────────────────────────────
def probe_f8() -> tuple:
    d = "tools/shortvideo-music-mcp"
    tracked = subprocess.run(["git", "ls-files", d], cwd=str(ROOT), capture_output=True,
                             text=True, encoding="utf-8", errors="replace").stdout.strip()
    exists = (ROOT / d).is_dir()
    cfg = ROOT / "config" / "mcporter.json"
    referenced = False
    if cfg.is_file():
        referenced = d.replace("/", "\\") in cfg.read_text(encoding="utf-8", errors="replace") or d in cfg.read_text(encoding="utf-8", errors="replace")
    return ("仍成立" if (exists and not tracked and referenced) else "已不成立"), {
        "目录在盘上": exists, "已跟踪文件数": len(tracked.splitlines()) if tracked else 0,
        "mcporter.json 仍引用它": referenced,
    }


# ── F9：28 个技能根 / 多人份第三方技能 ────────────────────────────────────
def probe_f9() -> tuple:
    import importlib.util
    spec = importlib.util.spec_from_file_location("skill_vet", ROOT / "tools" / "codex-scripts" / "skill-vet.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    roots = mod.discover_roots()
    total = 0
    for r in roots:
        if r.is_dir():
            total += len([x for x in r.iterdir() if x.is_dir() and (x / "SKILL.md").is_file()])
    return ("仍成立" if len(roots) > 8 else "已不成立"), {
        "自动发现的技能根": len(roots), "在场技能": total,
        "样本": [str(r) for r in roots[:4]],
    }


# ── F10：生产许可账里有不以 projects/ 开头的路径 ──────────────────────────
def probe_f10() -> tuple:
    """可机检：直接问那本账要 list，数出不以 `projects/` 开头的条目。

    给它写探针是**有意的** —— 这条故障的前提机器判得了，就不该留在"需人读"里。
    而且主人一旦处置掉（挪件重登记或撤登记），本探针会自己报 `已不成立`，
    提醒回台账结条目 —— **不需要谁记得回来手工关它**。
    """
    sys.path.insert(0, str(ROOT))
    try:
        from gbt_allinone.tools import media_license as ML
        lst = ML.run("list")
    except Exception as exc:  # noqa: BLE001
        return "需人读", {"说明": "读不到许可账：%s: %s" % (type(exc).__name__, str(exc)[:100]),
                          "_读不到_主数据": True}
    ents = lst.get("entries") or []
    bad = [str(e.get("file")) for e in ents if not str(e.get("file") or "").startswith("projects/")]
    return ("仍成立" if bad else "已不成立"), {
        "账总条数": len(ents),
        "不以 projects/ 开头的条数": len(bad),
        "那几条": bad,
        "边界": "本探针只判**路径口径**；条目的 sha256/字节是否与真件一致要另核（本轮已核过 3/3 一致）",
    }


# ── F11：同一个密钥两份存量已分叉（agnes）─────────────────────────────────
def probe_f11() -> tuple:
    """可机检：逐 profile 比「保险箱」与「User 作用域注册表」。

    主人一旦把分叉同步掉，本探针会自己报 `已不成立`，提醒回台账结条目 —— 不用谁记得回来关。
    只印掩码与指纹，明文只在内存里比。
    """
    try:
        import hashlib
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            i, reg = 0, {}
            while True:
                try:
                    n, v, _t = winreg.EnumValue(k, i)
                    reg[n] = v
                    i += 1
                except OSError:
                    break
    except Exception as exc:  # noqa: BLE001
        return "需人读", {"说明": "读不到注册表：%s: %s" % (type(exc).__name__, str(exc)[:80]),
                          "_读不到_主数据": True}
    sys.path.insert(0, str(ROOT))
    from gbt_allinone import deepseek_key as dk

    def fp(v: str) -> str:
        v = (v or "").strip()
        return "%d/%s" % (len(v), hashlib.sha256(v.encode("utf-8")).hexdigest()[:12]) if v else ""

    split, nonempty = [], 0
    for name in sorted(dk._PROFILES):
        vk, _s = dk.load_from_vault(name)
        rv = (reg.get(dk._PROFILES[name]["env"]) or "").strip()
        if vk:
            nonempty += 1
        if vk and rv and vk != rv:
            split.append({"profile": name, "库": dk.mask(vk), "库指纹": fp(vk),
                          "注册表": dk.mask(rv), "注册表指纹": fp(rv)})
    # 🔴 自纠（本题第一次跑就栽了）：**整个保险箱是空的**时，上面会得出"没有分叉"⇒ 判"已不成立"。
    #    而空保险箱**不代表主人的分叉修好了**，只代表**我这次看的 store 不对**
    #    （开机自检强制跑在隔离 store 里，所以它必然看到空库）。
    #    ⇒ 一个库都没读到 ⇒ 报 `需人读` + 打机器键 `_读不到_主数据`，**绝不由"没读到"推出"已不成立"**。
    if nonempty == 0:
        return "需人读", {
            "说明": "整个保险箱一个 profile 都没读到 ⇒ **不能**据此判『分叉已修好』"
                    "（多半是本次 store 不是生产 store —— 开机自检就是跑在隔离 store 里的）",
            "本器看到的 vault 路径": str(ROOT / "gbt_allinone" / "store" / "secrets"),
            "权威读数在哪": "python tools/codex-scripts/key-consistency-check.py（对生产 store 跑）",
            "_读不到_主数据": True,
        }
    return ("仍成立" if split else "已不成立"), {
        "有内容的库数": nonempty, "分叉条数": len(split), "分叉明细": split,
        "边界": "只比**存量**；不判密钥是否有效（那要真打一次接口 = 出网）",
    }


PROBES = {"F2": probe_f2, "F3": probe_f3, "F4": probe_f4, "F5": probe_f5,
          "F8": probe_f8, "F9": probe_f9, "F10": probe_f10, "F11": probe_f11}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="未清故障的前提复核（只读）")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not LEDGER.is_file():
        print("台账不在：%s" % LEDGER)
        return 2
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    faults = led.get("open_faults") or []

    rows = []
    for f in faults:
        fid = f.get("id")
        probe = PROBES.get(fid)
        if probe is None:
            verdict, reading = "需人读", {"说明": "本器没有这条的探针 —— **没有探针 ≠ 通过**，要人看"}
        else:
            try:
                verdict, reading = probe()
            except Exception as exc:  # noqa: BLE001
                verdict, reading = "需人读", {"说明": "探针自己出错：%s: %s" % (type(exc).__name__, str(exc)[:120])}
        # 🔴 **结论不许与读数自相矛盾** —— 这一条我改了两版，两版各错一个方向，都记在下面：
        #    第一版：读数写着"拿不到这个名字"，结论却报了"已不成立"（**由读不到推出结论**）。
        #    第二版：改成"读数里只要有『拿不到/出错』字样就降级"⇒ 把 F5 **误降级**了 ——
        #            它的静态读源码那层**明明读到了** `['D','E','F','V']`，只是旁边有一句
        #            *解释为什么走了这条路* 的说明里带了"拿不到"三个字。
        #    ⇒ 教训：**靠散文推断机器状态，两个方向都会错**。
        #    现在改为**机器键**：探针只在"主数据真的没读到"时打 `_读不到_主数据: True`，
        #    本器只认这个键。散文归散文，判定归判定。
        if reading.get("_读不到_主数据") and verdict != "需人读":
            verdict = "需人读"
            reading = dict(reading, **{"被本器降级": "探针自报『主数据没读到』 ⇒ 结论强制降为"
                                                  "『需人读』（不许由读不到推出已不成立）"})
        rows.append({"id": fid, "what": f.get("what"), "verdict": verdict, "reading": reading,
                     "台账原记的 state": f.get("state")})

    broken = [r for r in rows if r["verdict"] == "已不成立"]
    if a.json:
        print(json.dumps({"ok": not broken, "at": led.get("updated_at"), "rows": rows},
                         ensure_ascii=False, indent=2))
    else:
        print("═══ 未清故障 · 前提复核（%d 条）═══" % len(rows))
        for r in rows:
            tag = {"仍成立": "✅ 仍成立", "已不成立": "🔴 已不成立", "需人读": "🟡 需人读"}[r["verdict"]]
            print("\n%s  %s" % (tag, r["id"]))
            print("   台账记的是：%s" % str(r["what"])[:96])
            for k, v in r["reading"].items():
                print("     · %s：%s" % (k, v))
        print("")
        print("结论：仍成立 %d · **已不成立 %d** · 需人读 %d"
              % (sum(1 for r in rows if r["verdict"] == "仍成立"), len(broken),
                 sum(1 for r in rows if r["verdict"] == "需人读")))
        if broken:
            print("🔴 这些条目的前提已经垮了 ⇒ **回台账改账**（结掉或重写），不许让它继续挂着：%s"
                  % "、".join(r["id"] for r in broken))
        print("边界：**没有探针 ≠ 通过**；本器不改台账、不出网（F4 那条是回环 TCP）。")
    return 1 if broken else 0


if __name__ == "__main__":
    raise SystemExit(main())
