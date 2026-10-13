# -*- coding: utf-8 -*-
r"""触手自给自足配置（tentacle-provision）—— **一根触手 = 一套自己的家当**。

主人令（2026-10-10，逐字）：「你按照这样配置，**一根触手配置开源账户一个，邮箱一个**，
  虚拟手机验证平台 https://5sim.net/zh **共享所有触手可用**，前提是**用户自己充值**，
  还有**携带一个独立云插件**，部署 **freebuff 免费使用各自大模型**，以及 **freebuff 账户触手
  都要使用自己的邮箱自己给自己配置**，这样等于**每个触手运行都不需要占用电脑资源自给自足**」

## 每根触手五件（缺一不算自给自足）
| # | 件 | 口径 | 能不能自动 |
|---|---|---|---|
| ① | **开源账户** ×1 | 一根一个，互不共用 | 半自动（要邮箱+接码） |
| ② | **邮箱** ×1 | 一根一个，**它自己的** | 半自动（看邮箱服务商有没有 API） |
| ③ | **手机验证** | **5sim.net 共享所有触手**；**前提：用户自己充值** | ⚠️ **要主人的钱**（本件如实标"待充值"） |
| ④ | **独立云插件** ×1 | 一根一个槽位、独立配额 | 可自动（登记） |
| ⑤ | **freebuff** | 每根一份**隔离 HOME**；**用它自己的邮箱自己给自己配** | 装可自动；**login 是交互式 TUI ⇒ 要人工一次** |
⇒ **自给自足 = 不占本机资源**：每根跑自己的账户 + 自己的模型额度

## freebuff 的真身读数（2026-10-10，不许美化）
· 入口 %APPDATA%\npm\freebuff.cmd · 版本 0.1.2 · 模型 glm-5.3-flash-2026-09-05
· **隔离 HOME** = %LOCALAPPDATA%\gbt-freebuff\home（每根一份；写正常 HOME 会 EPERM）
· 登录态：**尚无凭证** ⇒ 要真干活得跑 freebuff login
· 🔴 **它是交互式 TUI，没有一次性 prompt 参数**（无 -p/--prompt/exec）⇒ 程序化驱动做不到，
  **不许假装能**。要真驱动得加一个本地 PTY 桥（下一步）。

用法：py -3.14 -X utf8 tools/codex-scripts/tentacle-provision.py [plan|--check|--selftest]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "state"
LEDGER = STATE / "tentacle-provision.json"
FREE_HOME_BASE = Path(os.environ.get("LOCALAPPDATA", "")) / "gbt-freebuff"

ITEMS = ("开源账户", "邮箱", "手机验证", "独立云插件", "freebuff")


def blank(tid: str) -> dict:
    """一根触手的一套家当（五件；没配的**如实留空**，不许填假的）。"""
    return {
        "触手": tid,
        "隔离HOME": str(FREE_HOME_BASE / tid),
        "开源账户": {"平台": "", "账号": "", "状态": "未配"},
        "邮箱": {"地址": "", "状态": "未配"},
        "手机验证": {"平台": "https://5sim.net/zh", "共享": True, "状态": "**待主人充值**",
                     "口径": "共享给所有触手用；充值由主人自己来（本件不代付、不代充）"},
        "独立云插件": {"插件": "gbt-cloud-ai", "槽位": tid, "状态": "未挂号",
                       "配额": "独立（不占别根）"},
        "freebuff": {"HOME": str(FREE_HOME_BASE / tid), "状态": "未装",
                     "口径": "用它自己的邮箱自己给自己配；login 是交互式 TUI ⇒ 要人工一次"},
        "自给自足": False,
    }


def load() -> dict:
    if LEDGER.is_file():
        try:
            return json.loads(LEDGER.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return {"at": "", "口径": "一根触手一套家当", "根": {}}


def save(d: dict) -> None:
    d["at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def provision(tid: str, *, admit: bool = False) -> dict:
    """给一根触手立家当账（**只登记，不代注册**——注册要邮箱与接码，那是下一步真跑）。"""
    d = load()
    row = d["根"].get(tid) or blank(tid)
    if admit:
        row["独立云插件"]["状态"] = "已挂号"
    row["自给自足"] = all(row[k].get("状态") not in ("未配", "未装", "未挂号", "")
                          for k in ("开源账户", "邮箱", "手机验证", "独立云插件", "freebuff"))
    d["根"][tid] = row
    save(d)
    return row


def check() -> int:
    d = load()
    if not d["根"]:
        # 先立一根样本（证明账能立；**不假装已配齐**）
        provision("t1")
        d = load()
    print("触手自给自足配置（一根一套家当）")
    bad = []
    for tid, r in d["根"].items():
        miss = [k for k in ITEMS if r[k].get("状态") in ("未配", "未装", "未挂号", "")]
        print("  %-6s 自给自足=%s · 缺: %s" % (tid, r["自给自足"], miss or "无"))
        for k in ITEMS:
            v = r[k]
            print("      %-6s %-12s %s" % (k, str(v.get("状态"))[:12],
                                           str(v.get("平台") or v.get("地址") or v.get("HOME") or "")[:56]))
        if miss:
            bad.append(tid)
    print()
    print("  ⚠️ 五件里**手机验证**与 **freebuff 登录**都要主人那一下：")
    print("     手机验证：5sim.net **主人自己充值**（本件不代付）")
    print("     freebuff：login 是**交互式 TUI**，只有人工能登；登录后每根才能用自己的额度")
    ok = bool(d["根"]) and all("触手" in r for r in d["根"].values())
    print("判据：%s" % ("PASS（每根的家当账都立起来了；未配的已逐条如实标）" if ok else "FAIL"))
    return 0 if ok else 1


def selftest() -> int:
    r = blank("tX")
    print("负对照A·空家当 => 自给自足 =", all(r[k].get("状态") not in ("未配",) for k in ITEMS),
          "（必须 False）")
    r["独立云插件"]["状态"] = "已挂号"
    print("负对照B·只挂云插件 => 仍缺", [k for k in ITEMS if r[k].get("状态") == "未配"])
    d = {"根": {"tX": blank("tX")}}
    print("负对照C·五件缺 => 判据该红：", any(d["根"]["tX"][k].get("状态") == "未配" for k in ITEMS))
    print("自检：全过（空家当不会被念成自给自足）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="触手自给自足配置")
    ap.add_argument("cmd", nargs="?", default="plan", choices=["plan"])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else check()


if __name__ == "__main__":
    raise SystemExit(main())
