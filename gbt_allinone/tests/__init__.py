
"""测试包入口 —— 测试隔离的唯一兜底（2026-09-17 立）。

为什么需要它：`gbt_allinone/__init__.py` 会 import `.store`，而 `store.py` **在 import 时**
就把 `_paths.STORE_DIR` 绑成常量。若测试模块在"还没设 GBT_STORE_DIR"的进程里被导入
（典型：`python -m unittest discover` 先导入父包 `gbt_allinone`，再执行测试模块体），
**父包这一步就把生产 store 绑上了** —— 测试模块体里再设环境变量已经来不及。

第一次实证（2026-09-17）：`unittest discover` 跑回归，把 `t-sched-run`
（`every_seconds=1` / `enabled=true`）写进了**生产** `gbt_allinone/store/schedules.json`；
契约测试 `test_framework.TestProductionStoreIsolation` 从此守住这条线。

本文件做两件事：
  ① 在任何测试模块体之前，把隔离 store 设好（setdefault，不覆盖调用方显式指定的值）；
  ② 若父包已经绑成生产 store（事后无法纠正），**立刻报错停下** ——
     宁可红，也不许带着生产 store 跑测试。
"""
import os
import tempfile
from pathlib import Path

_PRODUCTION_STORE = (Path(__file__).resolve().parent.parent / "store").resolve()

os.environ.setdefault("GBT_STORE_DIR", tempfile.mkdtemp(prefix="gbt_test_store_"))

from .. import _paths as _paths_mod  # noqa: E402

if Path(_paths_mod.STORE_DIR).resolve() == _PRODUCTION_STORE:
    raise RuntimeError(
        "拒绝在绑定【生产 store】的进程里跑测试：%s\n"
        "原因：gbt_allinone 包在导入时已绑定 STORE_DIR，早于任何测试模块设置环境变量。\n"
        "解法（二选一）：\n"
        "  ① 起 Python 之前先设环境变量：\n"
        '     PowerShell:  $env:GBT_STORE_DIR="$env:TEMP\\gbt_test_store"; '
        "py -3.10 -m unittest discover -s gbt_allinone\\tests -t . -p \"test_checkpoint.py\"\n"
        "  ② 直接跑测试文件（文件头先设环境变量再导包）：\n"
        "     py -3.10 gbt_allinone\\tests\\test_framework.py\n"
        % _paths_mod.STORE_DIR)

# ---- create 写根一次性隔离钩子（R107 · 风哥 2026-09-18 拍）----
# 为什么需要它：create 写根在**调用时**解析 GBT_CREATE_ROOT，不像 store 那样 import 期绑定，
# 所以没有任何"导入顺序"能兜底 —— 只能在包入口把它钉到隔离目录，并拒绝生产根。
# 实测（改动前）：隔离 store + 不设 GBT_CREATE_ROOT + import 本包 -> write_root() 返回生产
# outputs/ —— 任何"忘了设 env"的测试模块只要调一次 create.write 就写生产。
os.environ.setdefault("GBT_CREATE_ROOT", tempfile.mkdtemp(prefix="gbt_test_create_root_"))

from .. import file_operation as _fo  # noqa: E402

if _fo.write_root() == _fo.DEFAULT_WRITE_ROOT:
    raise RuntimeError(
        "拒绝在指向【生产 outputs】的进程里跑测试：%s\n"
        "原因：create 写根在**调用时**解析 GBT_CREATE_ROOT；未隔离时一次 create.write "
        "就会把产物写进生产 outputs/。\n"
        "解法：起进程前显式设 GBT_CREATE_ROOT 到隔离目录；或让 gbt_allinone.tests "
        "包先加载（它会 setdefault 到临时根）。" % _fo.write_root())
