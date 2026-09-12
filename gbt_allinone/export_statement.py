"""按用户维度导出对账。

用法：
  python gbt_allinone/export_statement.py --user alice
  python gbt_allinone/export_statement.py --user alice --asset USDT --out alice.csv

说明：读内部账本（GBT_LEDGER_DIR 可覆盖默认 store/），输出对账汇总 + 流水 CSV。
写文件时加 UTF-8 BOM，方便 Excel 直接打开中文不乱码。
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gbt_allinone.ledger import Ledger  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="按用户维度导出对账")
    ap.add_argument("--user", required=True, help="用户 ID")
    ap.add_argument("--asset", default=None, help="可选：仅该资产")
    ap.add_argument("--out", default=None, help="可选：CSV 输出路径")
    a = ap.parse_args()

    ledger = Ledger()
    print("对账汇总:" if False else "对账汇总:")
    print(json.dumps(ledger.reconcile(a.user), ensure_ascii=False, indent=2))
    csv_text = ledger.export_csv(a.user, a.asset)
    if a.out:
        Path(a.out).write_text("\ufeff" + csv_text, encoding="utf-8")
        print("CSV 已写出: %s | 数据行数: %d" % (a.out, len(csv_text.splitlines()) - 1))
    else:
        print("流水 CSV（前 10 行）:")
        for line in csv_text.splitlines()[:10]:
            print("   ", line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
