"""通知层：关键事件（到账记账、冻结等）写本地事件流 + 可选 Webhook。

- 默认追加写 `store/notifications.jsonl`，并打印一行摘要。
- 若设置 `GBT_NOTIFY_WEBHOOK`，则 POST JSON（标准库 urllib，超时 5s）；失败只记录、不抛，不影响主流程。
- 目录可用 `GBT_NOTIFY_DIR` 覆盖；否则跟随 `GBT_LEDGER_DIR`；再否则 `gbt_allinone/store`。
"""
from __future__ import annotations

import json
import os
import time
import urllib.request
from pathlib import Path

_BASE = __import__("gbt_allinone._paths", fromlist=["STORE_DIR"]).STORE_DIR


def _dir() -> Path:
    d = os.environ.get("GBT_NOTIFY_DIR") or os.environ.get("GBT_LEDGER_DIR")
    return Path(d) if d else _BASE


def _file() -> Path:
    return _dir() / "notifications.jsonl"


def emit(event, **payload):
    """写一条通知（本地事件流一定写；Webhook 尽力而为）。返回记录。"""
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "epoch": round(time.time(), 3), "event": event}
    rec.update(payload)
    p = _file()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("[notify] %s %s" % (event, json.dumps(payload, ensure_ascii=False)))
    url = os.environ.get("GBT_NOTIFY_WEBHOOK", "").strip()
    if url:
        try:
            body = json.dumps(rec, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(url, data=body,
                                         headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                rec["webhook_status"] = resp.status
        except Exception as e:  # noqa: BLE001
            rec["webhook_error"] = str(e)[:200]
    return rec


def deposit_credited(user, asset, amount, invoice_id="", address="", tx=None, balance=None):
    """到账并已记账的通知。"""
    return emit("deposit_credited", user=user, asset=asset, amount=str(amount),
                invoice_id=invoice_id, address=address, tx=tx or [],
                balance=(str(balance) if balance is not None else None))


def list_notifications(user=None, limit=200):
    p = _file()
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:  # noqa: BLE001
            continue
    if user:
        rows = [r for r in rows if r.get("user") == user]
    return rows[-limit:]
