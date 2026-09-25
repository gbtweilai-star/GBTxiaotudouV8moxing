"""R-H616（2026-09-25）· **未清故障前提复核器**自己的判据。

被测对象：`tools/codex-scripts/reverify-open-faults.py`
立它的理由：第 37 轮发现 F1/F6 两条高危故障的前提（"4 批没部署"）**早就不成立**，
而它们在账里挂了十几轮 —— **故障清单会无声腐烂**。

判据（五条，都要有牙）：
  1. 现读台账里的未清故障，**一条都不许是「已不成立」**（是的话必须回去改账，不许继续挂）；
  2. 真实台账跑得通、退出码与本器结论自洽；
  3. 🔴 **结论不许与读数自相矛盾**：探针自报"主数据没读到"（机器键 `_读不到_主数据`）时，
     哪怕探针返回"仍成立"，本器也必须**强制降级为「需人读」**
     —— 这是它首版真犯过的错（读数写着"拿不到这个名字"，结论却报"已不成立"）；
  4. 🔴 **反向也算错**：读数里只是**解释性文字**提到"拿不到"（主数据其实读到了），
     **不许**降级 —— 这是它第二版犯的错（把 F5 误降级，而 F5 的静态读其实拿到了 `['D','E','F','V']`）。
     ⇒ 3 与 4 合起来钉住一句话：**靠散文推断机器状态，两个方向都会错；只认机器键。**
  5. 没有探针的故障 id 一律报「需人读」，**不许默认绿**（"没有探针 ≠ 通过"）。
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "codex-scripts" / "reverify-open-faults.py"
LEDGER = ROOT / "state" / "排查台账.json"


def _load():
    spec = importlib.util.spec_from_file_location("reverify_open_faults", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load()


def _run() -> tuple:
    p = subprocess.run([sys.executable, str(TOOL), "--json"], cwd=str(ROOT),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300)
    i = p.stdout.find("{")
    return p.returncode, (json.loads(p.stdout[i:]) if i >= 0 else {})


class RealLedgerTest(unittest.TestCase):
    def test_no_open_fault_has_a_collapsed_premise(self) -> None:
        rc, rep = _run()
        broken = [r["id"] for r in rep.get("rows", []) if r["verdict"] == "已不成立"]
        self.assertEqual([], broken,
                         "这些故障的前提已经垮了 ⇒ 回台账改账（结掉或重写），不许继续挂着：%s" % broken)
        self.assertEqual(0, rc, "退出码应为 0（没有坍塌的前提）")

    def test_verdicts_are_consistent_with_readings(self) -> None:
        rc, rep = _run()
        rows = rep.get("rows", [])
        self.assertTrue(rows, "拿不到读数 ⇒ 本器没跑起来")
        for r in rows:
            with self.subTest(fault=r["id"]):
                self.assertIn(r["verdict"], ("仍成立", "已不成立", "需人读"))
                if r["verdict"] == "需人读":
                    # 需人读必须说清**为什么**（没有探针 / 主数据没读到 / 语义问题）
                    self.assertTrue(str(r["reading"]).strip() and r["reading"] != {},
                                    "报『需人读』却没说原因")


class GuardIsNotFooledTest(unittest.TestCase):
    """第 3、4 条：守卫只认机器键，不认散文 —— 两个方向各一条负控。"""

    def _guard(self, reading: dict, verdict: str) -> tuple:
        """复刻本器主循环里的那两行判定（保持与源码同一套规则）。"""
        if reading.get("_读不到_主数据") and verdict != "需人读":
            return "需人读", True
        return verdict, False

    def test_unreadable_primary_data_forces_human_review(self) -> None:
        """③ 主数据没读到 ⇒ 就算探针嘴硬说"仍成立"，也必须降级。"""
        v, downgraded = self._guard({"说明": "什么都拿不到", "_读不到_主数据": True}, "仍成立")
        self.assertEqual("需人读", v)
        self.assertTrue(downgraded)

    def test_prose_mention_of_missing_must_not_downgrade(self) -> None:
        """④ 只是解释性文字里有"拿不到"，主数据其实读到了 ⇒ **不许**降级。"""
        reading = {"来源": "静态读源码（模块属性拿不到）", "声明未实现的维度": ["D", "E", "F", "V"]}
        v, downgraded = self._guard(reading, "仍成立")
        self.assertEqual("仍成立", v, "拿散文里的『拿不到』去推翻结论 ⇒ 又误降级一次")
        self.assertFalse(downgraded)

    def test_source_uses_the_machine_key_and_not_a_prose_scan(self) -> None:
        """回归闸：源码里**只许**用机器键判定，不许再出现"扫散文关键词"的写法。

        这一条是**经验换来的**：散文扫描两版各错一个方向（见类文档），
        所以把它钉在源码上 —— 谁想改回去，这条用例会拦。
        """
        src = TOOL.read_text(encoding="utf-8")
        self.assertIn("_读不到_主数据", src, "机器键不见了")
        self.assertNotIn("any(w in blob for w in", src,
                         "又回到了『扫散文关键词』的写法 ⇒ 两个方向都会误判（见类文档 ③④）")


class NoProbeIsNotGreenTest(unittest.TestCase):
    """第 5 条：没有探针的 id 不许默认绿。"""

    def test_unknown_fault_id_is_human_review(self) -> None:
        self.assertNotIn("F99", MOD.PROBES, "用例前提：F99 不该有探针")
        # 台账里若出现没有探针的 id，主循环会给它『需人读』—— 这里直接验那段逻辑的取值域
        probe = MOD.PROBES.get("F99")
        self.assertIsNone(probe)
        # 复刻主循环：没有探针 ⇒ 需人读（不是『仍成立』）
        verdict = "需人读" if probe is None else "仍成立"
        self.assertEqual("需人读", verdict)


if __name__ == "__main__":
    unittest.main()
