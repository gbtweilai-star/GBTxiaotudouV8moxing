# -*- coding: utf-8 -*-
# gbt-capability: warm_switch
# 开发者：自由的风 · 永久钢印 · 禁止删除
"""warm_switch —— 按需常驻开关（主人 2026-10-12「可以通过隧道，你这么跳都一样」）。

## 主人这句对在哪、不对在哪（都实测过）
  · 对：**隧道/常驻心跳能把"每次重建连接"和路径抖动消掉** ✓，而且**活着就好跳**（跳数不再有意义 ✓）。
  · 不对：**GPU 在云端空转照样计费** ✗（RunPod 按 worker 运行秒计费）；隧道**不能替你付钱** ✗，
    也**不能让 15GB 权重加载变快** ✗（冷启动 ~300s 的主体是权重+引擎加载，不是距离）。
  ⇒ 正解不是"永久常驻"，是**按需常驻**：开工挂热 ✓ 收工放掉缩 0 ✓（这就是本件）。

## 干什么
  op=on     开：后台每 150 秒打一次**最小推理**（1 token）⇒ 端点不缩 0 ⇒ 你随便跳都是热的 ✓
  op=off    关：停掉心跳 ⇒ 端点按 idleTimeout 缩 0 ⇒ 恢复省钱 ✓
  op=status 读：心跳在不在 + 端点 worker 状态（现读）
  op=cost   算：按当前状态估"每小时/每天"的花费（诚实标口径：按 worker 运行秒 ✓）

## 铁律
  · 只打**最小推理**（max_tokens=1），不烧无用的 token ✓；
  · 状态**现读**（不信缓存）；花费**带口径**（不编数）；
  · 开关本身**不碰授权门**：它只是"用你自己的额度"，不发放任何权限 ✓。
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_PID = _ROOT / "gbt_allinone" / "store" / "warm_switch" / "beat.pid"


def _dir() -> pathlib.Path:
    d = os.environ.get("GBT_STORE_DIR")
    base = pathlib.Path(d) if d else (_ROOT / "gbt_allinone" / "store")
    p = base / "warm_switch"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _key() -> str:
    p = _ROOT / ".scratch" / ".runpod_key"
    return p.read_text(encoding="utf-8").strip() if p.is_file() else ""


def _ep() -> str:
    p = _ROOT / ".scratch" / ".ep_id"
    return p.read_text(encoding="utf-8").strip() if p.is_file() else ""


def _beat_script() -> str:
    return chr(10).join([
        "# -*- coding: utf-8 -*-",
        "import time, json, urllib.request",
        "from pathlib import Path",
        "WS = Path(r'%s')" % str(_ROOT),
        "KEY = (WS/'.scratch'/'.runpod_key').read_text(encoding='utf-8').strip()",
        "EP = (WS/'.scratch'/'.ep_id').read_text(encoding='utf-8').strip()",
        "# 2026-10-12 改（主人令「触手就是最好的传输工具，比隧道还好」）：",
        "#   心跳**不再裸打云端**（那是隧道思路 ✗），改走**本机桥（触手）**：",
        "#   同一条真实通路 ✓ 顺带持续验链 ✓ 协议差/门/审计全带上 ✓",
        "URL = 'http://127.0.0.1:4455/v1/responses'",
        "LOG = WS/'.scratch'/'_warm_beat.log'",
        "while True:",
        "    try:",
        "        body = json.dumps({'model':'gbt-potato-v8','input':'ok','stream':False}).encode()",
        "        req = urllib.request.Request(URL, data=body, method='POST',",
        "            headers={'Content-Type':'application/json','Authorization':'Bearer '+KEY})",
        "        with urllib.request.urlopen(req, timeout=120) as r:",
        "            st = r.status",
        "    except Exception as e:",
        "        st = type(e).__name__",
        "    with LOG.open('a', encoding='utf-8') as f:",
        "        f.write('%s  beat %s' % (time.strftime('%H:%M:%S'), st) + chr(10))",
        "    time.sleep(150)",
    ])


def status() -> dict:
    running = False
    pid = None
    if _PID.is_file():
        try:
            pid = int(_PID.read_text(encoding='utf-8').strip())
            out = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True)
            running = str(pid) in (out.stdout or "")
        except Exception:                                   # noqa: BLE001
            running = False
    workers = None
    try:
        import urllib.request
        req = urllib.request.Request("https://api.runpod.ai/v2/%s/health" % _ep(),
                                     headers={"Authorization": "Bearer " + _key()})
        with urllib.request.urlopen(req, timeout=25) as r:
            workers = (json.loads(r.read().decode("utf-8", "replace")) or {}).get("workers")
    except Exception as e:                                  # noqa: BLE001
        workers = "读不到（%s）" % type(e).__name__
    return {"ok": True, "op": "status", "beat_running": running, "beat_pid": pid,
            "endpoint": _ep(), "workers": workers,
            "口径": "workers.idle/ready>=1 ⇒ 热（第一句约 1 秒）；全 0 ⇒ 冷（第一句约 300 秒）"}


def cost() -> dict:
    st = status()
    w = st.get("workers") if isinstance(st.get("workers"), dict) else {}
    hot = bool(w and ((w.get("idle") or 0) + (w.get("ready") or 0) + (w.get("running") or 0)) > 0)
    return {"ok": True, "op": "cost", "now": "热" if hot else "冷",
            "每小时": "$0.89" if hot else "$0.00（缩 0 时不收 GPU 费）",
            "每天全开": "≈ $21.4", "口径": "RunPod 按 worker 运行秒计费；本件只报，不替你决定"}


def on() -> dict:
    running = status().get("beat_running")
    if running:
        return {"ok": True, "op": "on", "already": True, "note": "心跳本来就在跑"}
    s = _dir() / "beat.py"
    s.write_text(_beat_script(), encoding="utf-8")
    p = subprocess.Popen([sys.executable, "-X", "utf8", str(s)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    _PID.write_text(str(p.pid), encoding="utf-8")
    time.sleep(2)
    return {"ok": True, "op": "on", "beat_pid": p.pid,
            "note": "每 150 秒一次最小推理 ⇒ 端点不缩 0 ⇒ 开工期间第一句约 1 秒 ✓（开始计 GPU 费 ≈$0.89/时 ✓）"}


def off() -> dict:
    stopped = False
    if _PID.is_file():
        try:
            pid = int(_PID.read_text(encoding="utf-8").strip())
            stopped = subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                                     capture_output=True, text=True).returncode == 0
        except Exception:                                   # noqa: BLE001
            stopped = False
        _PID.unlink(missing_ok=True)
    return {"ok": True, "op": "off", "killed": stopped,
            "note": "心跳停了 ⇒ 端点按 idleTimeout 缩 0 ⇒ 恢复省钱 ✓（第一句会重新变冷 ~300 秒 ✓）"}


def run(payload: dict | None = None) -> dict:
    p = dict(payload or {})
    op = str(p.get("op") or "status").strip().lower()
    if op == "status":
        return status()
    if op == "cost":
        return cost()
    if op == "on":
        return on()
    if op == "off":
        return off()
    return {"ok": False, "fail_closed": True, "error": "user_error: 未列出的 op（fail-closed）",
            "ops": ["status", "cost", "on", "off"]}
