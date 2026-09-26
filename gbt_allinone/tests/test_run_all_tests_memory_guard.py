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
    """第 5 条：闸必须在跑之前。

    ⚠️ 自纠（2026-09-26 第 50 轮，**这条用例当场抓到了我自己的重构**）：
    第一版这里找的是**逐字的源码串** `memory_verdict(free_mb, args.min_free_mb)`。
    第 50 轮我把调用改成按范围取阈值（`scope_threshold(...)` + `memory_verdict(free_mb, _thr)`），
    那条用例立刻红 —— **它抓得对（那段代码确实变了），但抓的方式太脆**：
    它锁的是"某一行的字面写法"，而不是"闸在循环之前"这个**结构**。
    ⇒ 现在改成钉**顺序**与**范围感知**，重构只要不改变这两件事就不会误红。
    """

    def test_guard_runs_before_the_test_loop(self) -> None:
        src = TOOL.read_text(encoding="utf-8")
        i_guard = src.find("memory_verdict(")
        i_loop = src.find("for i, f in enumerate(files, 1):")
        self.assertNotEqual(-1, i_guard, "main() 里找不到那道闸的调用（`memory_verdict(`）")
        self.assertNotEqual(-1, i_loop, "找不到跑测试的循环（判据要跟着源码走）")
        self.assertLess(i_guard, i_loop,
                        "闸在循环**之后** ⇒ 跑完才标注就晚了，红已经产生并被读成结论了")

    def test_threshold_is_scope_aware(self) -> None:
        """全量与定向**不该用同一把尺子**（第 50 轮加）。

        实测动机：连续 6 轮内存都在 200–550MB，全量被闸挡着 ⇒ **想做的验证一直做不了**；
        而"挡全量"与"挡三个文件的定向跑"是两件事。所以钉两条：
          · `scope_threshold` 必须真被用上（否则范围感知会被悄悄去掉）；
          · **全量那把尺子不许被降低**（`scope_threshold(x, False) == x`）。
        """
        src = TOOL.read_text(encoding="utf-8")
        self.assertIn("scope_threshold(", src, "范围感知的阈值函数没被用上")
        self.assertEqual(MOD.scope_threshold(700.0, False), 700.0,
                         "全量档的阈值被改小了 ⇒ 那是放水（全量结论的信用全靠它）")
        self.assertLessEqual(MOD.scope_threshold(700.0, True), 250.0,
                             "定向档应当松于全量档（否则加了 --filter 也还是跑不动）")
        self.assertLess(MOD.scope_threshold(700.0, True), MOD.scope_threshold(700.0, False),
                        "定向档必须严格松于全量档")

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
