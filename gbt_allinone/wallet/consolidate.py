"""资金归集（先 dry-run）—— 扫描子地址余额，规划归集到主地址。

默认只输出计划（dry-run），不广播任何交易。真广播需另接执行模块并显式确认。
"""
from . import hd, rpc


def scan(mnemonic, count, start=0):
    """扫描 [start, start+count) 子地址的余额（需 ALCHEMY_RPC_URL）。只读。"""
    if not rpc.configured():
        return {"configured": False, "hint": "先配置 ALCHEMY_RPC_URL"}
    rows = []
    for d in hd.derive_many(mnemonic, count, start):
        try:
            rows.append({"address": d["address"], "index": d["index"],
                         "balance_eth": rpc.balance_eth(d["address"])})
        except Exception as e:  # noqa: BLE001
            rows.append({"address": d["address"], "index": d["index"], "error": str(e)})
    funded = [r for r in rows if r.get("balance_eth", 0) > 0]
    return {"scanned": len(rows), "funded": funded, "rows": rows}


def plan_sweep(mnemonic, master_index=0, count=50, start=0):
    """规划：把有余额的子地址归集到 master_index 地址。**dry-run，仅出计划**。"""
    s = scan(mnemonic, count, start)
    if not s.get("configured"):
        return s
    master = hd.derive(mnemonic, master_index)["address"]
    plan = [{"from": r["address"], "to": master, "amount_eth": r["balance_eth"],
             "action": "sweep(dry-run，未广播)"} for r in s.get("funded", [])]
    return {"mode": "DRY-RUN", "master": master, "planned": len(plan), "plan": plan}
