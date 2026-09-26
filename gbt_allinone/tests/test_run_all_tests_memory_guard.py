"""R-H620（2026-09-25）· **满仓横扫的负载闸**自己的判据。

被测对象：`tools/codex-scripts/run-all-tests.py` 的 `available_mb()` / `memory_verdict()` /
以及 `main()` 里那道**开跑前**的闸。

为什么要这道闸（两次实跑换来的，不是理论风险）：
  · 第 42 轮：满仓横扫里 `test_isolation_sweep` 报 rc=2，子进程 tail 逐字是
    `FileNotFoundError [WinError 2]` + `Interrupted: 1 error during collection`
    —— **内层 pytest 一个测试都没跑**；卸掉负载后同一个探针连跑两次都是绿。
  · 第 43 轮：复跑**26 分钟没回来**（常态 4–5 分钟）⇒ 去量机器：**可用 0.08 GB**、
    提交 30.8 GB vs 物理 7.5 GB（重度换页）。
⇒ **一个由负载决定的对错，就是错报。** 认不出来的"红"比没有读数更坏：
  它会被人当成"代码坏了"拿去修，**把假红制度化**。

判据五条：
  1. 低于阈值 ⇒ **不开跑**；
  2. 等于阈值 ⇒ 放行（边界含等号，写清楚）；
  3. 高于阈值 ⇒ 放行；
  4. **读不到**可用内存 ⇒ 放行但**必须如实标注"读不到"**（不许静默当没问题）；
  5. 源码顺序：这道闸必须在**跑测试的循环之前**（跑完再标注就晚了 —— 红已经产生了）。
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "codex-scripts" / "run-all-tests.py"


def _load():
    spec = importlib.util.spec_from_file_location("run_all_tests", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load()


class MemoryVerdictTest(unittest.TestCase):
    def test_below_threshold_refuses(self) -> None:
        ok, why = MOD.memory_verdict(100, 700)
        self.assertFalse(ok, "内存只剩 100MB 还放行 ⇒ 假红会被当成代码坏了")
        self.assertIn("假红", why, "拒绝时要说清为什么（否则读的人只会以为工具坏了）")

    def test_at_threshold_is_allowed(self) -> None:
        ok, _why = MOD.memory_verdict(700, 700)
        self.assertTrue(ok, "边界应当含等号（>= 阈值放行）")

    def test_above_threshold_is_allowed(self) -> None:
        self.assertTrue(MOD.memory_verdict(5000, 700)[0])

    def test_unknown_memory_is_allowed_but_labelled(self) -> None:
        ok, why = MOD.memory_verdict(None, 700)
        self.assertTrue(ok, "读不到内存不该把非 Windows 平台一刀切挡掉")
        self.assertIn("读不到", why, "读不到就必须**如实说读不到**，不许静默当没问题")


class GuardOrderTest(unittest.TestCase):
    """第 5 条：闸必须在跑之前。"""

    def test_guard_runs_before_the_test_loop(self) -> None:
        src = TOOL.read_text(encoding="utf-8")
        i_guard = src.find("memory_verdict(free_mb, args.min_free_mb)")
        i_loop = src.find("for i, f in enumerate(files, 1):")
        self.assertNotEqual(-1, i_guard, "main() 里找不到那道闸的调用")
        self.assertNotEqual(-1, i_loop, "找不到跑测试的循环（判据要跟着源码走）")
        self.assertLess(i_guard, i_loop,
                        "闸在循环**之后** ⇒ 跑完才标注就晚了，红已经产生并被读成结论了")

    def test_refusal_exit_code_is_distinct(self) -> None:
        """拒绝开跑要用**独立退出码**（3），别跟"有测试失败"（非 0 但另有含义）混成一个。"""
        src = TOOL.read_text(encoding="utf-8")
        self.assertIn("return 3", src, "拒绝开跑没有独立退出码 ⇒ 调用方分不清'没跑'与'跑红了'")

    def test_force_is_explicit_and_warned(self) -> None:
        src = TOOL.read_text(encoding="utf-8")
        self.assertIn("--force", src, "没有显式 override ⇒ 要么永远跑不了、要么偷偷放宽")
        self.assertIn("不许当权威读数", src, "--force 必须明说结果不可当权威（否则就是绕过判据）")


if __name__ == "__main__":
    unittest.main()
