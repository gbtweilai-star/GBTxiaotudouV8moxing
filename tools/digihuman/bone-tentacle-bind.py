# -*- coding: utf-8 -*-
"""骨级触手绑定（bone-tentacle-bind）—— 把数字人的**每根骨做成触手可寻址的驱动点**。

主人原话（2026-10-09）：
  「这绑骨说白了就是使用**类似触手的框架以线条的形式固定好驱动**，直接使用**触手扫空身体**
    不是你想干嘛就干嘛？」

口径（照主人的话落地）：
  · **线条** = 骨链（parent 关系）—— 它把身体"固定好"；
  · **驱动** = 动画通道（每条 clip × 每根骨 × T/R/S）—— 它让点"动起来"；
  · **寻址** = 每根骨在 skin.joints 里的下标 + 名字 + VRM 标准名 —— 触手据此点名；
  · **双向绑定** = 骨→驱动地址（这根骨被谁驱动）**且** 驱动→骨（这条通道驱动谁）；
  · **无死角** = 每根骨都必须：① 可寻址 ② 有线（除根）③ 有驱动（或**显式申报**它就该静止）。

用法：
  py -3.14 -X utf8 tools/digihuman/bone-tentacle-bind.py            # 扫并落 state/bone-bindings.json
  py -3.14 -X utf8 tools/digihuman/bone-tentacle-bind.py --check    # 判据（有死角即 rc=1）
  py -3.14 -X utf8 tools/digihuman/bone-tentacle-bind.py --selftest
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "digihuman"))
import pipeline as P                                                 # noqa: E402

SRC = ROOT / "projects" / "digital-human" / "out" / "dh_rigged.glb"
OUT = ROOT / "state" / "bone-bindings.json"
# 显式申报：本来就该静止的骨（没申报的"无驱动"一律算死角）
DECLARED_STATIC: dict = {}


def read_glb(p: Path):
    b = p.read_bytes()
    ln = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + ln])


def scan() -> dict:
    j = read_glb(SRC)
    nodes = j["nodes"]
    skin = (j.get("skins") or [{}])[0]
    jidx = skin.get("joints") or []
    names = [nodes[x].get("name") for x in jidx]
    # 线条（骨链）：谁是谁的父
    parent = {}
    for i, ni in enumerate(jidx):
        for c in nodes[ni].get("children") or []:
            if c in jidx:
                parent[nodes[c].get("name")] = nodes[ni].get("name")
    # 驱动：动画 → 骨 → 通道
    drv: dict = {n: {"clips": {}, "paths": set()} for n in names}
    for a in j.get("animations") or []:
        for ch in a.get("channels") or []:
            t = ch.get("target") or {}
            nm = nodes[t.get("node")].get("name")
            if nm in drv:
                drv[nm]["clips"].setdefault(a.get("name"), set()).add(t.get("path"))
                drv[nm]["paths"].add(t.get("path"))
    bones = []
    for i, n in enumerate(names):
        vrm = P.BLENDER_TO_VRM.get(n) or P.MIXAMO_TO_VRM.get(n)
        d = drv.get(n, {"clips": {}, "paths": set()})
        bones.append({
            "寻址": i, "骨": n, "VRM": vrm,
            "线": parent.get(n),                       # 父骨（根为 None）
            "是根": n not in parent,
            "驱动条数": len(d["clips"]),
            "驱动通道": sorted(d["paths"]),
            "被哪些动画驱动": sorted(d["clips"].keys()),
            "静止申报": DECLARED_STATIC.get(n),
        })
    blind = [b["骨"] for b in bones
             if (not b["是根"] and not b["线"]) or (b["驱动条数"] == 0 and not b["静止申报"])]
    return {"at": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"), "真源": str(SRC),
            "骨数": len(bones), "死角": blind, "逐骨": bones,
            "动画条数": len(j.get("animations") or []),
            "口径": "每根骨必须：① 可寻址 ② 有线（根除外）③ 有驱动（或显式申报静止）⇒ 才算扫空无死角"}


def check() -> int:
    r = scan()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print("骨级触手绑定：%d 根骨 · %d 条动画 · **死角 %d**"
          % (r["骨数"], r["动画条数"], len(r["死角"])))
    for b in r["逐骨"]:
        mark = "🔴" if b["骨"] in r["死角"] else "✅"
        print("  %s #%-2d %-14s VRM=%-14s 线=%-12s 驱动 %d 条 %s"
              % (mark, b["寻址"], b["骨"], b["VRM"] or "—", b["线"] or "(根)",
                 b["驱动条数"], ",".join(b["驱动通道"])))
    print("\n判据：%s" % ("PASS" if not r["死角"] else "FAIL"))
    return 0 if not r["死角"] else 1


def selftest() -> int:
    """负对照：清空驱动 ⇒ 必须冒出 18 个死角（根以外的骨全无驱动）。"""
    real = P.BLENDER_TO_VRM
    r0 = scan()
    print("正例·现读死角 =", len(r0["死角"]), "（应为 0）")
    # 造负面对照：把动画拔掉再扫
    import copy
    global SRC
    tmp = ROOT / ".scratch" / "_blind.glb"
    j = read_glb(SRC)
    j["animations"] = []
    tmp.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(j, ensure_ascii=False).encode("utf-8")
    pad = (4 - len(body) % 4) % 4
    body += b" " * pad
    head = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(body))
    chunk = struct.pack("<II", len(body), 0x4E4F534A) + body
    tmp.write_bytes(head + chunk)
    old = SRC
    SRC = tmp
    r1 = scan()
    SRC = old
    print("负对照·拔掉全部动画 ⇒ 死角 =", len(r1["死角"]), "（必须 >0）")
    ok = (len(r0["死角"]) == 0 and len(r1["死角"]) > 0)
    print("自检：%s" % ("全过" if ok else "不过"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="骨级触手绑定（扫空身体 · 无死角）")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.check:
        return check()
    r = scan()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print("已落 %s · %d 根骨 · 死角 %d" % (OUT, r["骨数"], len(r["死角"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
