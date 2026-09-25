"""R-H612（2026-09-25）· **开机自检总入口**本身也要被守着。

被测对象：`tools/codex-scripts/boot-selfcheck.py`
它把六条常设判据 + 两道闸收成**一次执行、一个退出码**。立它的理由是本仓那句话：
「**判据散着 = 没人跑**」。但总入口自己会烂 —— 所以它需要自己的判据。

判据（四条，都要有牙）：
  1. 判据组**一条不许漏**（对着 `JUDGMENTS` 逐个点名跑一遍；条数**现算**，不写死 ——
     写死一次过期一次，2026-09-25 加「云端点闸行为」时这条救了一次）；
  2. 两道闸（装机副本漂移 / 重启验收单）都要在，且**跑不动时算红、不许记成跳过**
     （这是总入口最容易长歪的地方：把"没跑成"写成"没问题"）；
  3. 每个步骤都必须带 `ok` / `rc` / `now` / `cmd` 四件套 —— 少了 `now`，红了也不知道现在是什么；
  4. 结论与红数必须自洽（`ok == (red_count == 0)`），且**不许重写第二份判据**
     （它只调既有 unittest 模块，源码里不许出现断言体）。
"""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOOT = ROOT / "tools" / "codex-scripts" / "boot-selfcheck.py"


def _load():
    spec = importlib.util.spec_from_file_location("boot_selfcheck", BOOT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BOOTMOD = _load()


class BootSelfcheckShapeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # 跳过重启验收单（它要起 HTTP 请求），但**判据组与漂移闸照跑**
        cls.rep = BOOTMOD.selfcheck(quick=True)

    def test_every_judgment_is_present_and_green(self) -> None:
        steps = {s["step"]: s for s in self.rep["steps"]}
        for label, _mod in BOOTMOD.JUDGMENTS:
            key = "判据/" + label
            self.assertIn(key, steps, "总入口漏了这条判据：%s" % label)
            self.assertTrue(steps[key]["ok"], "%s 现在红了：%s" % (label, steps[key]["now"]))

    def test_both_gates_are_present(self) -> None:
        steps = {s["step"]: s for s in self.rep["steps"]}
        self.assertIn("闸/装机副本漂移", steps)
        self.assertIn("闸/重启验收单", steps)

    def test_every_step_carries_the_four_fields(self) -> None:
        for s in self.rep["steps"]:
            for k in ("ok", "rc", "now", "cmd"):
                self.assertIn(k, s, "步骤 %s 缺字段 %s" % (s.get("step"), k))
            self.assertTrue(str(s["now"]).strip(), "步骤 %s 的 now 是空的" % s["step"])

    def test_verdict_is_consistent_with_red_count(self) -> None:
        self.assertEqual(self.rep["ok"], self.rep["red_count"] == 0,
                         "结论与红数自相矛盾 ⇒ 读的人会被两头骗")


class MissingToolIsRedNotSkippedTest(unittest.TestCase):
    """第 2 条判据的负对照：工具不在盘上时，必须是**红**，不是"跳过/没问题"。"""

    def test_missing_gate_is_red(self) -> None:
        orig = BOOTMOD.DRIFT_GATE
        BOOTMOD.DRIFT_GATE = ROOT / "__no_such_gate__.mjs"
        try:
            rep = BOOTMOD.selfcheck(quick=True)
        finally:
            BOOTMOD.DRIFT_GATE = orig
        row = next(s for s in rep["steps"] if s["step"] == "闸/装机副本漂移")
        self.assertFalse(row["ok"], "闸不在盘上却判成通过 ⇒ 这就是'把没跑成写成没问题'")
        self.assertIn("不许当跳过", row["now"])
        self.assertFalse(rep["ok"])


class NoSecondCopyOfJudgmentsTest(unittest.TestCase):
    """总入口只许**调**判据，不许**抄**判据。"""

    def test_source_calls_unittest_but_writes_no_assertions(self) -> None:
        src = BOOT.read_text(encoding="utf-8", errors="replace")
        self.assertIn('"-m", "unittest"', src, "总入口没有去跑既有判据模块")
        # 它自己不该出现断言体（抄一份判据出来 = 两份会慢慢长歪）
        for bad in ("assertEqual(", "assertTrue(", "assertIn("):
            self.assertNotIn(bad, src, "总入口里出现了断言体 %s ⇒ 判据有第二份了" % bad)

    def test_judgments_point_at_real_test_modules(self) -> None:
        for label, mod in BOOTMOD.JUDGMENTS:
            rel = Path(mod.replace(".", "/") + ".py")
            self.assertTrue((ROOT / rel).is_file(),
                            "判据 %s 指向的模块不存在：%s" % (label, rel))


if __name__ == "__main__":
    unittest.main(verbosity=2)
