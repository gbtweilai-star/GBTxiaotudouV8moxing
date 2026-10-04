# -*- coding: utf-8 -*-
"""
pm_live.engine — 真金执行编排(干跑优先 / 双闸放行 / 全量审计)
==============================================================
所有动作走 audit.jsonl; 私钥/凭证永不落审计、永不打印。
放行规则:
  - CLOB 下单/撤单: 配置 PM_DRY_RUN=0 且 CLI/API 显式 live=True
  - 链上 approve/deposit/withdraw: 配置 PM_DRY_RUN=0 且 yes=True
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from .config import Config, ENV_FILE, PKG_DIR
from . import clob as C
from . import chain as Ch
from . import gamma as G

# 审计默认落到 ~/.gbt(gatekeeper 白名单, 项目外), 可用 PM_AUDIT_FILE 覆盖
AUDIT = Path(os.environ.get("PM_AUDIT_FILE") or str(Path.home() / ".gbt" / "pm_live_audit.jsonl"))

_SECRET_KEYS = {"api_key", "api_secret", "api_passphrase", "l2_private_key",
                "signature", "private_key", "secret", "passphrase"}


def _sanitize(d: dict) -> dict:
    return {k: ("***" if k in _SECRET_KEYS or "sig" in k.lower() else v) for k, v in d.items()}


def _audit(action: str, params: dict, ok: bool, note: str = "") -> None:
    rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "action": action,
           "params": _sanitize(params), "ok": ok, "note": str(note)[:500]}
    try:
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[pm_live] 审计写入失败({AUDIT}): {e}")


# ---------- 只读 ----------

def doctor(cfg: Config) -> dict:
    out = {"env_file": ENV_FILE.exists(), "config": cfg.describe()}
    # gamma 公开连通
    try:
        ev = G.search_events("bitcoin", limit=1)
        out["gamma"] = {"ok": True, "sample": str((ev[0].get("title") if ev else "无结果"))[:60]}
    except Exception as e:
        out["gamma"] = {"ok": False, "error": str(e)[:160]}
    # clob 公开连通
    try:
        t = C.get_public_time()
        mk = C.get_public_markets(limit=3)
        out["clob"] = {"ok": True, "server_time": t.get("server_time"),
                       "market_sample": len(mk)}
    except Exception as e:
        out["clob"] = {"ok": False, "error": str(e)[:160]}
    # 链上自检(有 L2 key 才跑)
    if cfg.has_l2_key:
        try:
            out["chain"] = Ch.chain_selfcheck(cfg)
        except Exception as e:
            out["chain"] = {"error": str(e)[:200]}
    out["verdict"] = []
    if not cfg.has_clob_creds:
        out["verdict"].append("缺 CLOB 凭证: 在 Polymarket 设置页生成 API Key 后填入 .env(PM_API_KEY/SECRET/PASSPHRASE)")
    if not cfg.has_l2_key:
        out["verdict"].append("缺 L2 私钥: .env 填 PM_L2_PRIVATE_KEY(与 API Key 绑定的钱包)")
    if cfg.dry_run:
        out["verdict"].append("当前为干跑模式(PM_DRY_RUN=1): 只签名不广播。真金需设 PM_DRY_RUN=0")
    _audit("doctor", {}, True, "; ".join(out["verdict"]) or "ok")
    return out


def search(cfg: Config, query: str, limit: int = 6) -> dict:
    evs = G.search_events(query, limit=limit)
    rows = []
    for e in evs:
        for m in (e.get("markets") or [])[:2]:
            fm = G.flatten(m)
            toks = fm.get("clob_token_ids") or []
            rows.append({
                "question": str(fm.get("question") or "")[:80],
                "event": str(e.get("title") or "")[:60],
                "neg_risk": fm.get("neg_risk"),
                "token0": (toks[0] if toks else ""),
                "price0": (fm.get("outcome_prices") or [""])[0],
                "end": fm.get("end_date"),
            })
    _audit("search", {"query": query}, True, f"{len(rows)} rows")
    return {"query": query, "results": rows}


def book(cfg: Config, token_id: str, depth: int = 5) -> dict:
    b = C.get_public_book(token_id)
    cut = {"bids": b["bids"][:depth], "asks": b["asks"][:depth]}
    _audit("book", {"token": token_id[:16] + "…"}, True, f"bids={len(b['bids'])} asks={len(b['asks'])}")
    return cut


def balance(cfg: Config) -> dict:
    out = {}
    if cfg.configured:
        out["clob"] = C.get_balance(cfg)
    if cfg.has_l2_key:
        out["chain_usdc_e"] = str(Ch.balance_of(cfg) / 1e6)
        out["wallet"] = Ch.wallet_address(cfg)
    _audit("balance", {}, True)
    return out


# ---------- 写操作(双闸) ----------

def order(cfg: Config, query_or_token: str, side: str, size: float,
          price: Optional[float] = None, market_order: bool = False,
          live: bool = False, market_index: int = 0) -> dict:
    """token 可直接给 clob token_id; 也可给关键词(自动解析市场第一个 token)。"""
    if not cfg.configured:
        raise RuntimeError("凭证不全: 先跑 doctor 并按提示补 .env")
    if live and cfg.dry_run:
        raise RuntimeError("干跑模式下禁止真金下单: 请设 PM_DRY_RUN=0 并确认资金/滑点后再 --live")
    token = query_or_token
    resolved = None
    if not (query_or_token.startswith("0x") or len(query_or_token) > 60):
        resolved = G.pick_market(query_or_token, index=market_index)
        if not resolved:
            raise RuntimeError(f"关键词找不到市场: {query_or_token}")
        toks = resolved.get("clob_token_ids") or []
        if not toks:
            raise RuntimeError("该市场无 CLOB token(clobTokenIds 为空)")
        token = toks[0]
        price = price if price is not None else _mid(resolved)
        print(f"[resolve] {resolved['question'][:70]} | token={token[:24]}… | negRisk={resolved['neg_risk']}")
    # 校价(限价且有盘口时)
    guard = None
    if not market_order and price:
        guard = G.market_price_guard({"clob_token_ids": [token]}, side, size, price)
        if not guard["ok"]:
            raise RuntimeError(f"校价拦截: {guard['reason']}")
    signed = C.sign_order(cfg, token, side, size, price, market_order=market_order)
    if not live:
        _audit("order", {"token": token[:16], "side": side, "size": size,
                         "price": price, "market": market_order}, True, "dry-run 签名完成")
        sig = signed.get("signature") or ""
        return {"status": "DRY-RUN(已本地签名, 未广播)", **signed.get("digest_summary", {}),
                "fingerprint": signed.get("fingerprint"),
                "signature": sig[:24] + "…" if sig else None,
                "how_to_go_live": "设 PM_DRY_RUN=0 后重跑加 --live"}
    resp = C.post_order(cfg, token, side, size, price)
    _audit("order", {"token": token[:16], "side": side, "size": size,
                     "price": price, "market": market_order}, True, str(resp)[:200])
    return {"status": "LIVE-SUBMITTED", **resp}


def _mid(market: dict) -> Optional[float]:
    try:
        p = market.get("outcome_prices")
        if p:
            vals = [float(x) for x in p if x not in (None, "")]
            return sum(vals) / len(vals)
    except Exception:
        pass
    return None


def cancel(cfg: Config, order_id: str) -> dict:
    if cfg.dry_run:
        raise RuntimeError("干跑模式: 撤单为真实操作, 需 PM_DRY_RUN=0")
    r = C.cancel_order(cfg, order_id)
    _audit("cancel", {"order_id": order_id}, True)
    return {"status": "cancel-submitted", **r}


def deposit(cfg: Config, usdc_amount: float, yes: bool = False,
            adapter: Optional[str] = None) -> dict:
    if not cfg.has_l2_key:
        raise RuntimeError("缺 PM_L2_PRIVATE_KEY")
    if cfg.dry_run or not yes:
        note = "干跑/未确认: 仅打印拟广播交易"
    else:
        note = "LIVE"
    amount_int = int(round(usdc_amount * 1e6))
    r = Ch.deposit_collateral(cfg, amount_int, yes=(not cfg.dry_run and yes), adapter=adapter)
    _audit("deposit", {"usdc": usdc_amount, "adapter": adapter}, True, note + " " + str(r)[:200])
    return {"status": "dry-run(需 PM_DRY_RUN=0 + --yes)" if (cfg.dry_run or not yes) else "submitted", **r}


def withdraw(cfg: Config, usdc_amount: float, yes: bool = False,
             adapter: Optional[str] = None) -> dict:
    if not cfg.has_l2_key:
        raise RuntimeError("缺 PM_L2_PRIVATE_KEY")
    amount_int = int(round(usdc_amount * 1e6))
    r = Ch.withdraw_collateral(cfg, amount_int, yes=(not cfg.dry_run and yes), adapter=adapter)
    _audit("withdraw", {"usdc": usdc_amount}, True, str(r)[:200])
    return {"status": "dry-run(需 PM_DRY_RUN=0 + --yes)" if (cfg.dry_run or not yes) else "submitted", **r}
