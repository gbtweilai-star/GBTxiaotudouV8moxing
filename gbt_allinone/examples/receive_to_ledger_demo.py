"""全闭环演示：链上到账 -> 自动记账到内部账本（一条命令）。

运行：python gbt_allinone/examples/receive_to_ledger_demo.py

说明：真实链上到账由 gbt_wallet.scan() 检测（Polygon）；本演示在隔离临时目录里
用"等价事件"（发票被扫描判定为已付）驱动同一段记账逻辑，避免依赖真实资金。
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

TMP = Path(tempfile.mkdtemp(prefix="gbt_loop_"))
os.environ["GBT_WALLET_DIR"] = str(TMP / "wallet")
os.environ["GBT_LEDGER_DIR"] = str(TMP / "ledger")
os.environ["GBT_WALLET_PASS"] = "demo-pass"

from gbt_allinone.adapters import wallet_adapter as WA          # noqa: E402
from gbt_allinone.bridge import deposit_bridge as B             # noqa: E402
from gbt_allinone.ledger import Ledger                          # noqa: E402
from gbt_wallet import store as S                               # noqa: E402


def main():
    WA.ensure_init()
    inv = B.bind_invoice("alice", 2.5, "USDT", label="闭环演示")
    print("[1] 开收款发票 -> alice")
    print("    invoice_id =", inv["invoice_id"])
    print("    收款地址   =", inv["address"], "| 金额 =", inv["amount"], inv["currency"])

    # 等价于链上扫描命中后 gbt_wallet 把发票置为 paid
    invs = S.load_invoices()
    for i in invs["invoices"]:
        if i["invoice_id"] == inv["invoice_id"]:
            i["status"] = "paid"
            i["paid_amount_int"] = i["amount_int"]
            i["paid_at"] = int(time.time())
            i["tx_hashes"] = ["0xsimulated"]
    S.save_invoices(invs)
    print("[2] 链上扫描判定到账（等价事件）")

    r = B.sync(scan=False)
    print("[3] 自动记账:", json.dumps(r["credit"], ensure_ascii=False))
    print("    alice 账本余额 =", Ledger().balance("alice", "USDT"), "USDT")

    r2 = B.sync(scan=False)
    print("[4] 幂等复跑: 新增记账", r2["credit"]["count"], "笔（应为 0）")
    print("[5] 核账:", Ledger().verify())
    print("LOOP_OK")


if __name__ == "__main__":
    try:
        main()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
        for k in ("GBT_WALLET_DIR", "GBT_LEDGER_DIR", "GBT_WALLET_PASS"):
            os.environ.pop(k, None)
