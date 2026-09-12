"""平台统一资金池 + 充值地址分配。

- 每个用户分配一个充值地址（BIP44 本地派生），地址→用户 映射持久化。
- 扫链检测到充值 → 记账为用户内部余额（资金实体在平台池地址）。
- 用户余额与链上资金是两套：链上是"池"，账本是"数字"。
"""
import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from .core import Ledger, LedgerError

_BASE = __import__("gbt_allinone._paths", fromlist=["STORE_DIR"]).STORE_DIR


def _now():
    return datetime.now(timezone.utc).isoformat()


class Pool:
    def __init__(self, base=None, ledger=None):
        self.base = Path(base) if base else _BASE
        self.base.mkdir(parents=True, exist_ok=True)
        self.pool_file = self.base / "pool.json"
        self.ledger = ledger or Ledger(self.base)
        self._lock = threading.Lock()

    def _load(self):
        if self.pool_file.exists():
            return json.loads(self.pool_file.read_text(encoding="utf-8"))
        return {"users": {}, "addresses": {}, "next_index": 0}

    def _save(self, d):
        self.pool_file.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    def assign_deposit_address(self, user, mnemonic=None):
        """给用户分配（或返回已有）充值地址；地址由本地 HD 钱包派生。

        mnemonic 可显式传入（离线/测试用）；不传则读取本地钱包 store/wallet.json。
        """
        from ..wallet import hd
        with self._lock:
            d = self._load()
            if user in d["users"]:
                rec = d["users"][user]
                return {"user": user, "address": rec["address"], "index": rec["index"], "existing": True}
            if mnemonic is None:
                try:
                    mnemonic = hd.load_wallet()
                except Exception:
                    raise LedgerError("本地无钱包：先 wallet_new 并 hd.save_wallet() 保存助记词")
            idx = d["next_index"]
            addr = hd.derive(mnemonic, idx)["address"]
            d["users"][user] = {"address": addr, "index": idx, "assigned_at": _now()}
            d["addresses"][addr.lower()] = user
            d["next_index"] = idx + 1
            self._save(d)
            return {"user": user, "address": addr, "index": idx, "existing": False}

    def user_of(self, address):
        return self._load()["addresses"].get(address.lower())

    def address_of(self, user):
        rec = self._load()["users"].get(user)
        return rec["address"] if rec else None

    def total_addresses(self):
        return len(self._load()["users"])

    def credit_deposit(self, address, asset, amount, txid=None):
        """链上检测到某充值地址进账 → 记账给对应用户。"""
        user = self.user_of(address)
        if not user:
            raise LedgerError("该地址未分配给任何用户: %s" % address)
        r = self.ledger.deposit(user, asset, amount, ref=txid or ("chain:" + address[:10]),
                                meta={"source": "chain", "address": address, "txid": txid})

        r["credited_user"] = user
        return r

    def detect_deposits(self, asset="ETH", mnemonic=None):
        """扫所有已分配充值地址的链上余额；相对上次已记余额有增量则记账（幂等）。

        需 ALCHEMY_RPC_URL。逐地址记录 last_credited，避免重复入账。
        """
        from ..wallet import rpc as _rpc
        if not _rpc.configured():
            return {"configured": False, "hint": "先配置 ALCHEMY_RPC_URL"}
        with self._lock:
            d = self._load()
            results = []
            for user, rec in d["users"].items():
                addr = rec["address"]
                try:
                    bal = _rpc.balance_eth(addr)
                except Exception as e:  # noqa: BLE001
                    results.append({"user": user, "address": addr, "error": str(e)})
                    continue
                last = float(rec.get("last_credited", 0.0))
                delta = round(bal - last, 12)
                if delta > 0:
                    self.ledger.deposit(user, asset, str(delta), ref="chain:" + addr,
                                        meta={"source": "chain", "address": addr, "balance": bal})
                    rec["last_credited"] = bal
                    results.append({"user": user, "address": addr,
                                    "credited": str(delta), "balance": bal})
                else:
                    results.append({"user": user, "address": addr,
                                    "credited": "0", "balance": bal})
            self._save(d)
            return {"configured": True, "asset": asset, "checked": len(results), "results": results}
