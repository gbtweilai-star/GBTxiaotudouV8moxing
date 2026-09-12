"""gbt_wallet 链上入账 -> 内部账本 自动记账桥。

闭环：用户向充值地址转账 -> gbt_wallet.scan() 检测链上到账(发票转 paid)
     -> 本桥按"发票新增已付金额"调用 ledger.deposit() 记账(逐发票 credited_int 幂等)。

一条命令：python -m gbt_allinone.bridge
"""
from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path

from ..adapters import wallet_adapter as WA
from ..ledger import Ledger


def _dir() -> Path:
    d = os.environ.get("GBT_WALLET_DIR")
    if d:
        return Path(d)
    return __import__("gbt_allinone._paths", fromlist=["STORE_DIR"]).STORE_DIR / "receive"


def _map_path() -> Path:
    return _dir() / "invoice_user.json"


def load_map() -> dict:
    p = _map_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def save_map(m: dict) -> None:
    p = _map_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def bind_invoice(user, amount, currency="USDT", label="", expires_hours=72):
    """为用户开收款发票，并登记 发票->用户 映射（供自动记账）。"""
    inv = WA.create_invoice(amount, currency, label, expires_hours)
    m = load_map()
    m[inv["invoice_id"]] = {"user": user, "asset": currency.upper(),
                            "decimals": int(inv.get("decimals", 6)), "credited_int": 0}
    save_map(m)
    return inv


def credit_from_invoices():
    """把发票"新增已付金额"记账到账本（逐发票幂等）。"""
    ledger = Ledger()
    m = load_map()
    by_id = {i["invoice_id"]: i for i in WA.list_invoices()}
    credited = []
    for inv_id, rec in m.items():
        inv = by_id.get(inv_id)
        if not inv:
            continue
        paid = int(inv.get("paid_amount_int") or 0)
        already = int(rec.get("credited_int") or 0)
        delta = paid - already
        if delta <= 0:
            continue
        amt = Decimal(delta) / (Decimal(10) ** int(rec.get("decimals", 6)))
        r = ledger.deposit(rec["user"], rec["asset"], str(amt), ref="chain:" + inv_id,
                           meta={"invoice_id": inv_id, "address": inv.get("address"),
                                 "tx": inv.get("tx_hashes") or []})
        rec["credited_int"] = paid
        item = {"invoice_id": inv_id, "user": rec["user"], "asset": rec["asset"],
                "amount": str(amt), "balance": r["balance"]}
        credited.append(item)
        try:  # 到账通知（本地事件流 + 可选 Webhook）；失败不影响记账
            from .. import notify as _n
            _n.deposit_credited(rec["user"], rec["asset"], amt, inv_id,
                                inv.get("address"), inv.get("tx_hashes") or [], r.get("balance"))
        except Exception:  # noqa: BLE001
            pass
    save_map(m)
    return {"count": len(credited), "credited": credited}


def sync(scan=True):
    """全闭环：(可选)链上扫描 -> 自动记账。"""
    scan_result = None
    if scan:
        try:
            scan_result = WA.scan()
        except Exception as e:  # noqa: BLE001
            scan_result = {"error": str(e)[:200]}
    return {"scan": scan_result, "credit": credit_from_invoices()}
