# -*- coding: utf-8 -*-
"""
pm_live.chain — Polygon 链上真金层(充值/提现/余额)
==================================================
最小依赖(eth_account + requests JSON-RPC, 无 web3):
  - ERC20 approve / 余额 / symbol 自检
  - CTF Exchange deposit(uint256) / withdraw(uint256)   (标准市场抵押品路径)
  - NegRisk Adapter deposit(uint256)                     (负风险市场路径, 逐市场)
  - 广播前 eth_call 自检目标合约, 干跑默认只打印拟广播交易。
真实广播三闸: .env PM_DRY_RUN=0 + 命令 --yes + doctor --chain 自检通过。
"""
from __future__ import annotations

import time
from typing import Optional

import requests
from eth_account import Account
from eth_account.datastructures import SignedTransaction
from eth_hash.auto import keccak

from .config import Config, POLYGON_CHAIN_ID, USDC_E, CTF_EXCHANGE, RPC_FALLBACKS

# ---- 极简 ABI 编码(只覆盖本模块用到的调用) ----

def _sel(sig: str) -> str:
    return keccak(sig.encode()).hex()[:8]


def _u256(v: int) -> str:
    return f"{v:064x}"


def _addr(a: str) -> str:
    return a.lower().replace("0x", "").rjust(64, "0")


APPROVE = _sel("approve(address,uint256)")
DEPOSIT = _sel("deposit(uint256)")
WITHDRAW = _sel("withdraw(uint256)")
BALANCE_OF = _sel("balanceOf(address)")
SYMBOL = _sel("symbol()")
DECIMALS = _sel("decimals()")
CODE_AT = _sel("code()")


class Rpc:
    def __init__(self, url: str):
        self.url = url
        self._id = 0

    def call(self, method: str, params: list, timeout: int = 20):
        self._id += 1
        body = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        last = None
        urls = [self.url] + [u for u in RPC_FALLBACKS if u != self.url]
        for u in urls:
            try:
                r = requests.post(u, json=body, timeout=timeout)
                j = r.json()
                if "error" in j:
                    last = j["error"]
                    continue
                return j.get("result")
            except Exception as e:
                last = str(e)
                continue
        raise RuntimeError(f"RPC 全部不可用: {last}")


def _eth_call(rpc: Rpc, to: str, data: str) -> str:
    res = rpc.call("eth_call", [{"to": to, "data": "0x" + data}, "latest"])
    if res is None:
        raise RuntimeError("eth_call 返回空")
    return res[2:] if res.startswith("0x") else res


def _parse_u256(hexstr: str) -> int:
    return int(hexstr, 16)


def _parse_str(hexstr: str) -> str:
    if len(hexstr) < 64:
        return ""
    off = int(hexstr[0:64], 16) * 2
    ln = int(hexstr[off:off + 64], 16)
    body = hexstr[off + 64: off + 64 + ln * 2]
    return bytes.fromhex(body).decode("utf-8", "replace")


def _broadcast_and_wait(rpc: Rpc, signed: SignedTransaction, label: str, wait_s: int = 90) -> dict:
    tx = rpc.call("eth_sendRawTransaction", ["0x" + signed.raw_transaction.hex()])
    if not tx:
        raise RuntimeError("eth_sendRawTransaction 无返回(网络被拒?)")
    h = tx if isinstance(tx, str) else tx.get("hash")
    deadline = time.time() + wait_s
    while time.time() < deadline:
        rec = rpc.call("eth_getTransactionReceipt", [h])
        if rec:
            status = int(rec.get("status", "0x0"), 16)
            return {"label": label, "tx_hash": h, "status": "confirmed" if status == 1 else f"FAILED(status={status})",
                    "block": rec.get("blockNumber"), "gas_used": rec.get("gasUsed")}
        time.sleep(4)
    return {"label": label, "tx_hash": h, "status": "pending(超时, 用 hash 自查)"}


def _build_tx(cfg: Config, to: str, data: str, value: int = 0) -> SignedTransaction:
    acct = Account.from_key(cfg.l2_private_key)
    rpc = Rpc(cfg.rpc_url)
    nonce = int(rpc.call("eth_getTransactionCount", [acct.address, "pending"]), 16)
    gas_price = int(rpc.call("eth_gasPrice", []), 16)
    tx = {
        "chainId": POLYGON_CHAIN_ID, "nonce": nonce, "gasPrice": gas_price,
        "gas": 400_000, "to": to, "value": value, "data": "0x" + data,
    }
    return acct.sign_transaction(tx), rpc


# ---------- 公开只读 ----------

def wallet_address(cfg: Config) -> str:
    return Account.from_key(cfg.l2_private_key).address


def token_meta(cfg: Config, token: str = USDC_E) -> dict:
    rpc = Rpc(cfg.rpc_url)
    code = rpc.call("eth_getCode", [token, "latest"])
    sym = _parse_str(_eth_call(rpc, token, SYMBOL + _u256(0)))
    dec = _parse_u256(_eth_call(rpc, token, DECIMALS + _u256(0)))
    return {"code_size": len(code or "") // 2, "symbol": sym, "decimals": dec}


def balance_of(cfg: Config, token: str = USDC_E, who: Optional[str] = None) -> int:
    rpc = Rpc(cfg.rpc_url)
    who = who or wallet_address(cfg)
    raw = _eth_call(rpc, token, BALANCE_OF + _addr(who))
    return _parse_u256(raw)


def allowance(cfg: Config, token: str, spender: str) -> int:
    rpc = Rpc(cfg.rpc_url)
    who = wallet_address(cfg)
    data = _sel("allowance(address,address)") + _addr(who) + _addr(spender)
    return _parse_u256(_eth_call(rpc, token, data))


def chain_selfcheck(cfg: Config) -> dict:
    """doctor --chain: 广播前必跑的自检。"""
    out = {"wallet": wallet_address(cfg)}
    try:
        meta = token_meta(cfg)
        out["usdc_e"] = meta
        out["usdc_e_ok"] = meta.get("code_size", 0) > 0 and (meta.get("symbol") or "").upper().startswith("USDC")
    except Exception as e:
        out["usdc_e"] = {"error": str(e)[:200]}
        out["usdc_e_ok"] = False
    for name, addr in (("ctf_exchange", CTF_EXCHANGE),):
        try:
            rpc = Rpc(cfg.rpc_url)
            code = rpc.call("eth_getCode", [addr, "latest"])
            out[name] = {"code_size": len(code or "") // 2, "ok": len(code or "") > 4}
        except Exception as e:
            out[name] = {"error": str(e)[:200], "ok": False}
    try:
        out["usdc_balance"] = str(balance_of(cfg) / 1e6)
    except Exception as e:
        out["usdc_balance"] = f"err:{str(e)[:120]}"
    return out


# ---------- 写链(真实广播) ----------

def approve(cfg: Config, spender: str, amount_int: int, token: str = USDC_E, yes: bool = False) -> dict:
    """approve spender 可花 amount_int(USDC.e 6 位小数整数)。"""
    data = APPROVE + _addr(spender) + _u256(amount_int)
    signed, _ = _build_tx(cfg, token, data)
    print(f"[approve] {token} -> {spender} amount={amount_int} (0x{signed.hash.hex()[:16]}…)")
    if not yes:
        return {"status": "dry-run(需 --yes)", "data_hash": "0x" + signed.hash.hex()}
    return _broadcast_and_wait(Rpc(cfg.rpc_url), signed, "approve")


def deposit_collateral(cfg: Config, amount_int: int, yes: bool = False,
                       adapter: Optional[str] = None) -> dict:
    """
    充值 USDC.e 到 Polymarket 抵押品。
      adapter=None  -> CTF Exchange.deposit(uint256)(标准市场)
      adapter=0x…   -> NegRiskAdapter.deposit(uint256)(负风险市场专用)
    先自动 approve(足额), 再 deposit。amount_int 为 6 位小数整数。
    """
    target = adapter or CTF_EXCHANGE
    cur = allowance(cfg, USDC_E, target)
    if cur < amount_int:
        appr = approve(cfg, target, amount_int, yes=yes)
        if appr.get("status") not in ("confirmed",):
            if not yes:
                print("  ↑ 需先 --yes 完成 approve")
            else:
                raise RuntimeError(f"approve 未确认: {appr}")
    data = DEPOSIT + _u256(amount_int)
    signed, _ = _build_tx(cfg, target, data)
    print(f"[deposit] {amount_int/1e6} USDC.e -> {target} ({'CTF' if not adapter else 'NegRiskAdapter'})")
    if not yes:
        return {"status": "dry-run(需 --yes)", "data_hash": "0x" + signed.hash.hex(), "target": target}
    return _broadcast_and_wait(Rpc(cfg.rpc_url), signed, "deposit")


def withdraw_collateral(cfg: Config, amount_int: int, yes: bool = False,
                        adapter: Optional[str] = None) -> dict:
    """从 CTF Exchange / NegRiskAdapter 提回 USDC.e。"""
    target = adapter or CTF_EXCHANGE
    data = WITHDRAW + _u256(amount_int)
    signed, _ = _build_tx(cfg, target, data)
    print(f"[withdraw] {amount_int/1e6} USDC.e <- {target}")
    if not yes:
        return {"status": "dry-run(需 --yes)", "data_hash": "0x" + signed.hash.hex()}
    return _broadcast_and_wait(Rpc(cfg.rpc_url), signed, "withdraw")
