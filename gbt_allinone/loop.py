"""一条命令跑通全闭环：链上扫描入账 -> 自动记账到内部账本。

用法：
  set GBT_WALLET_PASS=<口令>            # 收款钱包口令（必需）
  set GBT_WALLET_DIR=<目录>             # 可选，默认 gbt_allinone/store/receive
  set GBT_LEDGER_DIR=<目录>             # 可选，默认 gbt_allinone/store
  set ALCHEMY_RPC_URL=...               # 自建钱包只读 RPC（可选）
  python gbt_allinone/loop.py [--no-scan]

--no-scan 跳过链上扫描，只做"发票已付金额 -> 账本记账"（离线可用）。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gbt_allinone.bridge import sync  # noqa: E402

if __name__ == "__main__":
    print(json.dumps(sync(scan="--no-scan" not in sys.argv), ensure_ascii=False, indent=2))
