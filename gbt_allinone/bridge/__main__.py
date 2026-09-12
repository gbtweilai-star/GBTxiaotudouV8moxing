"""一条命令跑全闭环: python -m gbt_allinone.bridge [--no-scan]"""
import json
import sys

from .deposit_bridge import sync

print(json.dumps(sync(scan="--no-scan" not in sys.argv), ensure_ascii=False, indent=2))
