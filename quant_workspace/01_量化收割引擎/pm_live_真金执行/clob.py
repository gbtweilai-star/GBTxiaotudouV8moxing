# -*- coding: utf-8 -*-
"""
pm_live.clob — Polymarket CLOB 客户端(真实下单/撤单/余额)
==========================================================
私有操作走官方 py-clob-client(EIP-712 本地签名 + API 凭证 HMAC);
公开盘口/时间/市场列表直接裸 HTTP(公开端点, 免凭证, 版本漂移免疫)。
v1 只放行限价单(市价单风险面大, 预留)。
"""
from __future__ import annotations

from typing import Optional

import requests

from .config import Config, CLOB


def _pyclob():
    """返回 (ClobClient, ApiCreds|ClobCreds, OrderArgs, OrderType, BalanceAllowanceParams, AssetType)"""
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import (OrderArgs, OrderType, BalanceAllowanceParams, AssetType)
    try:
        from py_clob_client.clob_types import ApiCreds as CredsCls
    except ImportError:
        from py_clob_client.clob_types import ClobCreds as CredsCls  # 旧版命名
    return ClobClient, CredsCls, OrderArgs, OrderType, BalanceAllowanceParams, AssetType


def make_client(cfg: Config):
    """构造已认证客户端(凭证不全抛错)。"""
    ClobClient, CredsCls, *_ = _pyclob()
    from eth_account import Account
    acct = Account.from_key(cfg.l2_private_key)
    client = ClobClient(CLOB, chain_id=137, key=cfg.l2_private_key,
                        creds=CredsCls(cfg.api_key, cfg.api_secret, cfg.api_passphrase),
                        funder=acct.address)
    return client, acct


# ---------- 公开(裸 HTTP, 无需凭证) ----------

def _pub(path: str, timeout: int = 15) -> dict:
    r = requests.get(CLOB + path, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.json()


def get_public_time() -> dict:
    j = _pub("/time")
    if isinstance(j, dict):
        return {"server_time": j.get("timestamp") or j.get("time") or j}
    return {"server_time": j}  # 当前 API 直接返回 epoch 整数


def get_public_markets(limit: int = 10) -> list:
    j = _pub(f"/markets?limit={limit}")
    return j.get("data") or (j if isinstance(j, list) else [])


def get_public_book(token_id: str) -> dict:
    j = _pub(f"/book?token_id={token_id}")
    bids = j.get("bids") or []
    asks = j.get("asks") or []
    return {"bids": [{"price": b.get("price"), "size": b.get("size")} for b in bids],
            "asks": [{"price": a.get("price"), "size": a.get("size")} for a in asks]}


# ---------- 私有(需凭证) ----------

def _require(cfg: Config):
    if not cfg.configured:
        raise RuntimeError("凭证不全: 先跑 doctor 并按提示填 .env(PM_API_KEY/SECRET/PASSPHRASE/L2_PRIVATE_KEY)")


def get_balance(cfg: Config) -> dict:
    """CLOB 抵押品余额(USDC.e 本位)。"""
    _require(cfg)
    _, _, _, _, BalanceAllowanceParams, AssetType = _pyclob()
    client, acct = make_client(cfg)
    try:
        b = client.get_balance_allowance(params=BalanceAllowanceParams(
            asset_type=AssetType.COLLATERAL, token_id=""))
        if hasattr(b, "balance"):
            bal = b.balance
        elif isinstance(b, dict):
            bal = b.get("balance")
        else:
            bal = str(b)
        return {"address": acct.address, "balance": str(bal)}
    except Exception as e:
        raise RuntimeError(f"查询 CLOB 余额失败(凭证/权限问题?): {e}") from e


def _order_to_dict(order) -> dict:
    if hasattr(order, "to_dict"):
        return order.to_dict()
    if hasattr(order, "__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(order)
    return dict(order) if isinstance(order, dict) else {"raw": str(order)}


def sign_order(cfg: Config, token_id: str, side: str, size: float,
               price: Optional[float], market_order: bool = False) -> dict:
    """本地构建限价单 + EIP-712 签名, 不发网(干跑安全)。"""
    if market_order:
        raise RuntimeError("v1 只支持限价单(市价单请在盘口校价后给限价, 更安全)")
    _require(cfg)
    _, _, OrderArgs, _, _, _ = _pyclob()
    client, acct = make_client(cfg)
    if price is None:
        raise ValueError("限价单必须给 price")
    args = OrderArgs(token_id=token_id, price=float(price), size=float(size), side=side.upper())
    try:
        signed = client.create_order(args)          # 本地 EIP-712 签名, 不提交
    except Exception as e:
        raise RuntimeError(f"订单构建/签名失败: {e}") from e
    hb = signed.order.hash_struct()
    if isinstance(hb, bytes):
        fp = "0x" + hb.hex()
    else:
        fp = str(hb or "")
        if fp and not fp.startswith("0x"):
            fp = "0x" + fp
    return {
        "signed": signed,
        "order_id": None,  # 预签名阶段无 orderID(服务器提交后返回)
        "fingerprint": fp,
        "signature": signed.signature,
        "maker": acct.address,
        "digest_summary": {"token_id": token_id, "side": side.upper(),
                           "price": float(price), "size": float(size)},
    }


def post_order(cfg: Config, token_id: str, side: str, size: float,
               price: Optional[float]) -> dict:
    """真实提交限价单(调用方已过干跑/确认闸)。"""
    signed_info = sign_order(cfg, token_id, side, size, price, market_order=False)
    client, _ = make_client(cfg)
    try:
        resp = client.post_order(signed_info["signed"])   # 直接传 SignedOrder 对象
    except Exception as e:
        raise RuntimeError(f"CLOB 下单失败: {e}") from e
    if isinstance(resp, dict):
        oid = resp.get("orderID") or resp.get("orderId")
        return {"order": oid, "response": str(resp)[:300]}
    return {"order": None, "response": str(resp)[:300]}


def cancel_order(cfg: Config, order_id: str) -> dict:
    _require(cfg)
    client, _ = make_client(cfg)
    try:
        resp = client.cancel(order_id)
    except Exception as e:
        raise RuntimeError(f"撤单失败: {e}") from e
    return {"order_id": order_id, "response": str(resp)[:300]}


def cancel_all(cfg: Config) -> dict:
    _require(cfg)
    client, _ = make_client(cfg)
    try:
        resp = client.cancel_all()
    except Exception as e:
        raise RuntimeError(f"批量撤单失败: {e}") from e
    return {"response": str(resp)[:300]}
