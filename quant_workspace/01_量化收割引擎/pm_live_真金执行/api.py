# -*- coding: utf-8 -*-
"""
pm_live.api — 本地真金执行 API(供平台 UI 接线)
==============================================
默认端口 8096。只监听本机(127.0.0.1), CORS 放开供 file:// 平台页调用。
安全: 真金下单需 live=true 且配置 PM_DRY_RUN=0; 每次调用落 audit.jsonl。
启动:  C:/Python312/python.exe -m pm_live.api --port 8096
"""
from __future__ import annotations

import argparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import Config
from . import engine

cfg = Config()
app = FastAPI(title="pm_live executor", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def _resp(fn):
    try:
        return JSONResponse({"ok": True, "data": fn()})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.get("/api/pm/health")
def health():
    return {"ok": True, "mode": "LIVE" if not cfg.dry_run else "DRY-RUN",
            "creds": cfg.has_clob_creds, "l2": cfg.has_l2_key,
            "address": engine.doctor(cfg).get("config", {}).get("l2_address", "")}


@app.get("/api/pm/doctor")
def doctor():
    return _resp(lambda: engine.doctor(cfg))


@app.get("/api/pm/search")
def search(q: str = "bitcoin up", limit: int = 5):
    return _resp(lambda: engine.search(cfg, q, limit))


@app.get("/api/pm/book")
def book(token_id: str):
    return _resp(lambda: engine.book(cfg, token_id))


@app.get("/api/pm/balance")
def balance():
    return _resp(lambda: engine.balance(cfg))


class OrderReq(BaseModel):
    q: str = Field(..., description="clob token_id 或市场关键词")
    side: str = "BUY"
    size: float = 1.0
    price: float | None = None
    market_order: bool = False
    live: bool = False


@app.post("/api/pm/order")
def order(req: OrderReq):
    return _resp(lambda: engine.order(cfg, req.q, req.side.upper(), req.size,
                                      req.price, req.market_order, live=req.live))


class FundReq(BaseModel):
    amount: float = Field(..., gt=0)
    yes: bool = False          # 需显式 true 才会广播(链上交易无法撤回)
    adapter: str | None = None


@app.post("/api/pm/deposit")
def deposit(req: FundReq):
    return _resp(lambda: engine.deposit(cfg, req.amount, yes=req.yes, adapter=req.adapter))


@app.post("/api/pm/withdraw")
def withdraw(req: FundReq):
    return _resp(lambda: engine.withdraw(cfg, req.amount, yes=req.yes, adapter=req.adapter))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8096)
    p.add_argument("--host", default="127.0.0.1")
    a = p.parse_args()
    import uvicorn
    uvicorn.run(app, host=a.host, port=a.port, log_level="warning")


if __name__ == "__main__":
    main()
