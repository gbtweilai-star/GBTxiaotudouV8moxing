# -*- coding: utf-8 -*-
"""
pm_live CLI — 真金执行控制台
用法示例(在 GBT小土豆 目录下):
  python -m pm_live.cli doctor                 # 环境/连通性/链上自检
  python -m pm_live.cli search "bitcoin up"    # 真实市场检索
  python -m pm_live.cli book <token_id>        # 真实盘口
  python -m pm_live.cli balance                # CLOB + 链上余额(需凭证)
  python -m pm_live.cli order "bitcoin up" BUY 5 0.55          # 干跑: 本地签名
  python -m pm_live.cli order <token_id> SELL 5 0.45 --live    # 真金(需 PM_DRY_RUN=0)
  python -m pm_live.cli cancel <order_id>
  python -m pm_live.cli deposit 100 --yes      # 链上充值 USDC.e(需 PM_DRY_RUN=0)
  python -m pm_live.cli withdraw 50 --yes
"""
from __future__ import annotations

import argparse
import json
import sys

from .config import Config
from . import engine


def _print(d: dict) -> None:
    print(json.dumps(d, ensure_ascii=False, indent=2, default=str))


def main() -> int:
    cfg = Config()
    p = argparse.ArgumentParser(prog="pm_live", description="Polymarket 真金执行层(干跑优先)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor")
    s = sub.add_parser("search"); s.add_argument("q"); s.add_argument("--limit", type=int, default=6)
    b = sub.add_parser("book"); b.add_argument("token_id")
    sub.add_parser("balance")

    o = sub.add_parser("order")
    o.add_argument("q", help="token_id 或市场关键词")
    o.add_argument("side", choices=["BUY", "SELL"])
    o.add_argument("size", type=float)
    o.add_argument("price", type=float, nargs="?", default=None)
    o.add_argument("--market", action="store_true", help="市价单(需给 max 保护场景慎用)")
    o.add_argument("--live", action="store_true", help="真金提交(需 PM_DRY_RUN=0)")
    o.add_argument("--idx", type=int, default=0, help="关键词命中多个市场时选第几个")

    c = sub.add_parser("cancel"); c.add_argument("order_id")
    d = sub.add_parser("deposit"); d.add_argument("usdc", type=float); d.add_argument("--yes", action="store_true")
    d.add_argument("--adapter", default=None)
    w = sub.add_parser("withdraw"); w.add_argument("usdc", type=float); w.add_argument("--yes", action="store_true")
    w.add_argument("--adapter", default=None)

    a = p.parse_args()
    try:
        if a.cmd == "doctor":
            _print(engine.doctor(cfg))
        elif a.cmd == "search":
            _print(engine.search(cfg, a.q, a.limit))
        elif a.cmd == "book":
            _print(engine.book(cfg, a.token_id))
        elif a.cmd == "balance":
            _print(engine.balance(cfg))
        elif a.cmd == "order":
            _print(engine.order(cfg, a.q, a.side, a.size, a.price, a.market, live=a.live, market_index=a.idx))
        elif a.cmd == "cancel":
            _print(engine.cancel(cfg, a.order_id))
        elif a.cmd == "deposit":
            _print(engine.deposit(cfg, a.usdc, yes=a.yes, adapter=a.adapter))
        elif a.cmd == "withdraw":
            _print(engine.withdraw(cfg, a.usdc, yes=a.yes, adapter=a.adapter))
        return 0
    except Exception as e:
        print(f"[pm_live] 失败: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
