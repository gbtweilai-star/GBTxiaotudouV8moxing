# -*- coding: utf-8 -*-
"""
pm_live.gamma — Polymarket Gamma 行情/市场元数据(公开只读)
==========================================================
用于: 关键词找市场 -> 取 clobTokenIds / conditionId / negRisk / outcomePrices,
再结合 CLOB 盘口做下单前校价。失败不伪造数据。
"""
from __future__ import annotations

import json
from typing import Optional

import requests

from .config import GAMMA


def _jlist(v):
    """gamma 的数组字段可能是真 list 也可能是 JSON 字符串(当前 API 多为后者)。"""
    if isinstance(v, (list, tuple)):
        return list(v)
    if isinstance(v, str) and v.strip().startswith("["):
        try:
            return json.loads(v)
        except Exception:
            return []
    return []


def _get(path: str, params: dict, timeout: int = 15) -> list:
    r = requests.get(GAMMA + path, params=params, timeout=timeout,
                     headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    data = r.json()
    return data if isinstance(data, list) else [data]


def search_events(query: str, limit: int = 8) -> list:
    """
    按关键词搜索事件(BTC/ETH/选举/…), 返回带 markets 的事件列表。
    扫描最高 600 个按 24h 成交量排序的热门事件, 关键词匹配事件标题
    或任一市场问题(大小写不敏感)。
    """
    words = [w for w in query.strip().lower().split() if w]
    if not words:
        return []
    out = []
    for offset in range(0, 600, 50):
        try:
            evs = _get("/events", {"active": "true", "closed": "false", "limit": 50,
                                   "offset": offset, "order": "volume24hr", "ascending": "false"})
        except Exception:
            break
        if not evs:
            break
        for e in evs:
            title = str(e.get("title") or "").lower()
            qs = [str((m.get("question") or "")).lower() for m in (e.get("markets") or [])]
            if all(w in title for w in words) or any(all(w in q for w in words) for q in qs):
                out.append(e)
        if len(out) >= limit * 3:  # 候选足够即停, 供 pick_market 精挑
            break
    return out[:limit]


def flatten(m: dict) -> dict:
    """把 gamma market 解析成安全 dict(tokens/prices 已反序列化)。"""
    tokens = _jlist(m.get("clobTokenIds"))
    prices = _jlist(m.get("outcomePrices"))
    return {
        "market_id": m.get("id"),
        "question": m.get("question"),
        "outcomes": _jlist(m.get("outcomes")),
        "outcome_prices": [str(p) for p in prices],
        "clob_token_ids": tokens,
        "condition_id": m.get("conditionId"),
        "neg_risk": bool(m.get("negRisk")),
        "end_date": m.get("endDate"),
        "liquidity": m.get("liquidity"),
        "volume24hr": m.get("volume24hr"),
    }


def pick_market(query: str, index: int = 0) -> Optional[dict]:
    """取第一个匹配事件的第 index 个市场, 扁平化关键字段。"""
    evs = search_events(query, limit=3)
    if not evs:
        return None
    e = evs[0]
    mkts = e.get("markets") or []
    if not mkts:
        return None
    m = mkts[min(index, len(mkts) - 1)]
    out = flatten(m)
    out["event_id"] = e.get("id")
    out["event_title"] = e.get("title")
    return out


def market_price_guard(market: dict, side: str, size: float, price: float) -> dict:
    """
    下单前校价(公开 CLOB 盘口交叉校验):
      - side BUY  -> 价格不得高于盘口 best ask 可成交档 5%;
      - side SELL -> 价格不得低于盘口 best bid 5%。
    远超盘口视为滑点风险阻断; 盘口不可得则不阻断(记录)。
    """
    token = (market.get("clob_token_ids") or [None])[0]
    if not token:
        return {"ok": False, "reason": "no token", "book": None}
    try:
        from .clob import get_public_book
        book = get_public_book(token)
        best_bid = float(book["bids"][0]["price"]) if book.get("bids") else None
        best_ask = float(book["asks"][0]["price"]) if book.get("asks") else None
        drift = None
        if side.upper() == "BUY" and best_ask is not None:
            drift = (price - best_ask) / best_ask
        elif side.upper() == "SELL" and best_bid is not None:
            drift = (best_bid - price) / best_bid
        ok = drift is None or abs(drift) <= 0.05
        return {"ok": ok, "reason": "" if ok else f"price {drift*100:+.1f}% off best (book best_bid={best_bid} ask={best_ask})",
                "book": {"best_bid": best_bid, "best_ask": best_ask}, "drift": drift}
    except Exception as e:
        return {"ok": True, "reason": f"book unavailable ({e})", "book": None}
