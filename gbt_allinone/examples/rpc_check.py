"""链上只读连通性检查（需 gbt_allinone/.env 的 ALCHEMY_RPC_URL）。

运行：python gbt_allinone/examples/rpc_check.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gbt_allinone.wallet import rpc  # noqa: E402


def main():
    if not rpc.configured():
        print("未配置 ALCHEMY_RPC_URL（写入 gbt_allinone/.env）")
        return 1
    print("网络信息:", rpc.network_info())
    addr = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    print("示例地址 %s... 余额 = %s ETH" % (addr[:10], rpc.balance_eth(addr)))
    print("RPC_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
