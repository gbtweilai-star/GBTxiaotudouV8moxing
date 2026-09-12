"""端到端演示：交易所式托管架构（完全离线，不需要 RPC/Alchemy）。

用户钱包 = 内部数字记账；资金实体 = 平台统一资金池；
转账 = 账本内划转，仅受用户自身余额约束。

运行：python gbt_allinone/examples/wallet_ledger_demo.py
"""
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gbt_allinone.ledger import InsufficientBalance, Ledger, Pool  # noqa: E402
from gbt_allinone.wallet import hd  # noqa: E402


def main():
    tmp = Path(tempfile.mkdtemp(prefix="gbt_demo_"))
    try:
        ledger = Ledger(tmp)
        pool = Pool(tmp, ledger)

        w = hd.new_wallet()
        print("平台钱包助记词(打码):", hd.mask_mnemonic(w["mnemonic"]))
        print("-" * 60)

        a1 = pool.assign_deposit_address("alice", mnemonic=w["mnemonic"])
        a2 = pool.assign_deposit_address("bob", mnemonic=w["mnemonic"])
        print("[1] alice 充值地址:", a1["address"], "(index %d)" % a1["index"])
        print("[1] bob   充值地址:", a2["address"], "(index %d)" % a2["index"])

        pool.credit_deposit(a1["address"], "USDT", 100, txid="0xdep1")
        print("[2] 链上入金 100 USDT -> alice 余额 =", ledger.balance("alice", "USDT"))

        ledger.transfer("alice", "bob", "USDT", 30)
        print("[3] 划转 alice->bob 30 -> alice =", ledger.balance("alice", "USDT"),
              "| bob =", ledger.balance("bob", "USDT"))

        try:
            ledger.transfer("bob", "alice", "USDT", 1000)
            print("[4] !! 超额划转未被拒绝(异常)")
        except InsufficientBalance as e:
            print("[4] 超额划转已拒绝:", e)

        r = ledger.withdraw("alice", "USDT", 10, "0xDEADBEEF")
        print("[5] 出金 10 USDT ->", r["status"], "| alice 余额 =", ledger.balance("alice", "USDT"))

        print("[6] 核账:", ledger.verify())
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("-" * 60)
    print("DEMO_OK")


if __name__ == "__main__":
    main()
