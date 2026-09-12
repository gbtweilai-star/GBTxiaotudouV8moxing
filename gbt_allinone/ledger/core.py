"""交易所式内部账本（托管型 custodial internal ledger）。

架构（用户明确）：
- 用户钱包 = 内部数字记账；资金实体永远在平台统一资金池。
- 转账 = 账本内划转，仅受"用户自身余额"约束。
- 本模块只记账（不链上动钱）；链上由 wallet/ 负责。

合规（AML/风控，用户口径）：
- 冻结/解冻仅作用于【平台托管余额】(frozen 桶)，用于涉诈/洗钱排查止损。
- 不接触用户外部钱包私钥，不作用于平台未托管的资产。
- 每笔冻结/解冻留痕 case_id / reason / actor，可审计。

原则：
- 复式记账：每笔转账=转出(-1)+转入(+1)；append-only，余额由条目派生。
- available 与 frozen 两个桶；转账/提现只看 available。
- 余额不足一律拒绝；不允许负余额。
- 金额用 Decimal 并以字符串序列化，避免浮点误差。
"""
import csv
import io
import json
import os
import threading
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

_BASE = __import__("gbt_allinone._paths", fromlist=["STORE_DIR"]).STORE_DIR


def _now():
    return datetime.now(timezone.utc).isoformat()


def _pos(amount):
    try:
        d = Decimal(str(amount))
    except Exception:
        raise LedgerError("非法金额: %r" % (amount,))
    if d <= 0:
        raise LedgerError("金额必须 > 0")
    return d


def _is_all(x):
    return x is None or x == "" or (isinstance(x, str) and x.lower() == "all")


class LedgerError(Exception):
    pass


class InsufficientBalance(LedgerError):
    pass


class Ledger:
    def __init__(self, base=None):
        self.base = Path(base or os.environ.get("GBT_LEDGER_DIR") or _BASE)
        self.base.mkdir(parents=True, exist_ok=True)
        self.ledger_file = self.base / "ledger.jsonl"
        self.accounts_file = self.base / "accounts.json"
        self._lock = threading.Lock()

    # ---- 账户 ----
    def _load_accounts(self):
        if self.accounts_file.exists():
            return json.loads(self.accounts_file.read_text(encoding="utf-8"))
        return {}

    def _save_accounts(self, d):
        self.accounts_file.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    def open_account(self, user_id, meta=None):
        a = self._load_accounts()
        if user_id in a:
            return {"user": user_id, "created": False}
        a[user_id] = {"created_at": _now(), "meta": meta or {}}
        self._save_accounts(a)
        return {"user": user_id, "created": True}

    # ---- 条目 ----
    def entries(self):
        if not self.ledger_file.exists():
            return []
        out = []
        for line in self.ledger_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out

    def _append(self, entries):
        start = len(self.entries())
        with self.ledger_file.open("a", encoding="utf-8") as f:
            for i, e in enumerate(entries):
                e["seq"] = start + i
                f.write(json.dumps(e, ensure_ascii=False) + "\n")

    def _signed(self, e):
        amt = Decimal(e["amount"])
        return amt if e["direction"] == "credit" else -amt

    def _mk(self, etype, user, asset, amount, direction, ref, meta=None, bucket="available"):
        return {"ts": _now(), "type": etype, "user": user, "asset": asset,
                "amount": str(Decimal(str(amount))), "direction": direction,
                "bucket": bucket, "ref": ref or "", "meta": meta or {}}

    # ---- 余额（available / frozen）----
    def balance(self, user, asset):
        """可动用余额（available 桶）。"""
        total = Decimal(0)
        for e in self.entries():
            if e["user"] == user and e["asset"] == asset and e.get("bucket", "available") != "frozen":
                total += self._signed(e)
        return total

    def frozen(self, user, asset):
        """冻结余额（frozen 桶）。"""
        total = Decimal(0)
        for e in self.entries():
            if e["user"] == user and e["asset"] == asset and e.get("bucket") == "frozen":
                total += self._signed(e)
        return total

    def balances(self, user):
        out = {}
        for e in self.entries():
            if e["user"] == user and e.get("bucket", "available") != "frozen":
                out[e["asset"]] = out.get(e["asset"], Decimal(0)) + self._signed(e)
        return {k: str(v) for k, v in out.items()}

    def holdings(self, user):
        """{asset: {available, frozen}}。"""
        assets = sorted({e["asset"] for e in self.entries() if e["user"] == user})
        return {a: {"available": str(self.balance(user, a)),
                    "frozen": str(self.frozen(user, a))} for a in assets}

    # ---- 操作 ----
    def deposit(self, user, asset, amount, ref=None, meta=None):
        amt = _pos(amount)
        with self._lock:
            if user not in self._load_accounts():
                self.open_account(user)
            self._append([self._mk("DEPOSIT", user, asset, amt, "credit", ref, meta)])
            return {"ok": True, "type": "DEPOSIT", "user": user, "asset": asset,
                    "amount": str(amt), "balance": str(self.balance(user, asset))}

    def transfer(self, from_user, to_user, asset, amount, ref=None, meta=None):
        amt = _pos(amount)
        with self._lock:
            if from_user == to_user:
                raise LedgerError("不能转给自己")
            bal = self.balance(from_user, asset)
            if bal < amt:
                raise InsufficientBalance(
                    "余额不足: %s %s 可用 %s，需要 %s" % (from_user, asset, bal, amt))
            if to_user not in self._load_accounts():
                self.open_account(to_user)
            m = dict(meta or {})
            self._append([
                self._mk("TRANSFER", from_user, asset, amt, "debit", ref, {**m, "counterparty": to_user}),
                self._mk("TRANSFER", to_user, asset, amt, "credit", ref, {**m, "counterparty": from_user}),
            ])
            return {"ok": True, "type": "TRANSFER", "from": from_user, "to": to_user,
                    "asset": asset, "amount": str(amt),
                    "from_balance": str(self.balance(from_user, asset)),
                    "to_balance": str(self.balance(to_user, asset))}

    def withdraw(self, user, asset, amount, address, ref=None, broadcast=False):
        amt = _pos(amount)
        with self._lock:
            bal = self.balance(user, asset)
            if bal < amt:
                raise InsufficientBalance(
                    "余额不足: %s %s 可用 %s，需要 %s" % (user, asset, bal, amt))
            self._append([self._mk("WITHDRAW", user, asset, amt, "debit", ref,
                                   {"address": address, "broadcast": bool(broadcast)})])
            return {"ok": True, "type": "WITHDRAW", "user": user, "asset": asset,
                    "amount": str(amt), "address": address,
                    "status": "broadcast" if broadcast else "dry-run(未广播)",
                    "balance": str(self.balance(user, asset))}

    # ---- 冻结 / 解冻（AML/风控；仅平台托管余额）----
    def freeze(self, user, asset, amount=None, case_id="", reason="", actor="system"):
        with self._lock:
            avail = self.balance(user, asset)
            amt = avail if _is_all(amount) else _pos(amount)
            if amt <= 0:
                raise LedgerError("无可用余额可冻结")
            if amt > avail:
                raise InsufficientBalance("可冻余额不足: %s %s 可用 %s，需冻 %s" % (user, asset, avail, amt))
            meta = {"case_id": case_id, "reason": reason, "actor": actor}
            self._append([
                self._mk("FREEZE", user, asset, amt, "debit", "freeze:" + case_id, meta, "available"),
                self._mk("FREEZE", user, asset, amt, "credit", "freeze:" + case_id, meta, "frozen"),
            ])
            return {"ok": True, "type": "FREEZE", "user": user, "asset": asset,
                    "frozen_amount": str(amt), "case_id": case_id, "actor": actor,
                    "available": str(self.balance(user, asset)),
                    "frozen_total": str(self.frozen(user, asset))}

    def unfreeze(self, user, asset, amount=None, case_id="", reason="", actor="system"):
        with self._lock:
            fr = self.frozen(user, asset)
            amt = fr if _is_all(amount) else _pos(amount)
            if amt <= 0:
                raise LedgerError("无可解冻余额")
            if amt > fr:
                raise InsufficientBalance("冻结余额不足: %s %s 冻结 %s，需解 %s" % (user, asset, fr, amt))
            meta = {"case_id": case_id, "reason": reason, "actor": actor}
            self._append([
                self._mk("UNFREEZE", user, asset, amt, "debit", "unfreeze:" + case_id, meta, "frozen"),
                self._mk("UNFREEZE", user, asset, amt, "credit", "unfreeze:" + case_id, meta, "available"),
            ])
            return {"ok": True, "type": "UNFREEZE", "user": user, "asset": asset,
                    "unfrozen_amount": str(amt), "case_id": case_id, "actor": actor,
                    "available": str(self.balance(user, asset)),
                    "frozen_total": str(self.frozen(user, asset))}

    def freeze_cases(self):
        """冻结/解冻留痕（供审计/对账）。"""
        rows = []
        for e in self.entries():
            if e["type"] in ("FREEZE", "UNFREEZE"):
                m = e.get("meta") or {}
                rows.append({"seq": e.get("seq"), "ts": e["ts"], "type": e["type"],
                             "user": e["user"], "asset": e["asset"], "amount": e["amount"],
                             "case_id": m.get("case_id", ""), "reason": m.get("reason", ""),
                             "actor": m.get("actor", "")})
        return rows

    # ---- 流水 / 对账 / 导出 ----
    def statement(self, user, asset=None, since_seq=None):
        """用户流水（可按资产过滤；since_seq 为排他下界）。"""
        rows = [e for e in self.entries()
                if e["user"] == user
                and (asset is None or e["asset"] == asset)
                and (since_seq is None or (e.get("seq") or 0) > int(since_seq))]
        return rows

    def reconcile(self, user):
        """按用户维度的对账汇总：入金/出金/转入/转出/可用/冻结。"""
        entries = [e for e in self.entries() if e["user"] == user]
        out = {}
        for a in sorted({e["asset"] for e in entries}):
            es = [e for e in entries if e["asset"] == a]

            def _sum(etype, direction=None):
                return sum((Decimal(e["amount"]) for e in es
                            if e["type"] == etype and (direction is None or e["direction"] == direction)),
                           Decimal(0))

            out[a] = {"deposit": str(_sum("DEPOSIT")), "withdraw": str(_sum("WITHDRAW")),
                      "transfer_in": str(_sum("TRANSFER", "credit")),
                      "transfer_out": str(_sum("TRANSFER", "debit")),
                      "frozen": str(self.frozen(user, a)),
                      "available": str(self.balance(user, a))}
        return {"user": user, "assets": out}

    def export_csv(self, user=None, asset=None):
        """导出流水 CSV（可按用户/资产过滤）。返回 CSV 文本。"""
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["seq", "ts", "type", "user", "asset", "amount", "direction",
                    "bucket", "ref", "counterparty", "case_id"])
        for e in self.entries():
            if user and e["user"] != user:
                continue
            if asset and e["asset"] != asset:
                continue
            m = e.get("meta") or {}
            w.writerow([e.get("seq"), e["ts"], e["type"], e["user"], e["asset"], e["amount"],
                        e["direction"], e.get("bucket", "available"), e.get("ref", ""),
                        m.get("counterparty", ""), m.get("case_id", "")])
        return buf.getvalue()

    # ---- 校验 ----
    def verify(self):
        problems = []
        users = self._load_accounts()
        entries = self.entries()
        assets = sorted({e["asset"] for e in entries})
        for u in users:
            for a in assets:
                if self.balance(u, a) < 0:
                    problems.append("负可用余额: %s %s" % (u, a))
                if self.frozen(u, a) < 0:
                    problems.append("负冻结余额: %s %s" % (u, a))
        for a in assets:
            ub = sum((self.balance(u, a) + self.frozen(u, a) for u in users), Decimal(0))
            dep = sum((Decimal(e["amount"]) for e in entries
                       if e["asset"] == a and e["type"] == "DEPOSIT"), Decimal(0))
            wd = sum((Decimal(e["amount"]) for e in entries
                      if e["asset"] == a and e["type"] == "WITHDRAW"), Decimal(0))
            if ub != dep - wd:
                problems.append("守恒失衡 %s: 用户合计 %s != 充值 %s - 出金 %s" % (a, ub, dep, wd))
        return {"ok": not problems, "problems": problems,
                "users": len(users), "entries": len(entries)}
