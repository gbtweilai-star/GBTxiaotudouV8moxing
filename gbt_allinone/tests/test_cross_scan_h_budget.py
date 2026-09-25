"""R-H605（2026-09-25）· `cross_scan` H 维**有界 + 分母闭合**回归用例。

被测故障（真跑复现过，不是推演）：
    空参 `cross_scan`（`deep=True`）**两次 >560s 不返回** —— 而 `deep=False` 只要 17.9s
    ⇒ 钱全花在 H 维。根因：H 维对每个 `safe` 且不在 `PROBE_SKIP_KINDS` 里的位
    **就地同步**真调，**没有任何预算**；而 `PROBE_SKIP_KINDS` 只排除侧效应位，
    **不排除慢的只读扫描器**。`caps-runtime-census` 现读的逐位耗时能直接对账：
    98 位只读位合计 **735.3s**，其中 ≥5s 的 6 位就占 **672.2s**。

判据（四条都要有牙）：
  1. **有界**：给 0 预算时**不许再起调用**（`checked == 0`），且必须如实置 `deadline_hit`；
  2. **分母闭合**：`checked + skipped + unsafe + not_probed + skipped_slow == len(BENIGN_CAPS)`
     —— 少一项就是"覆盖静默缩水"；
  3. **两个"没探到"的桶不许混**：超预算(`not_probed`) ≠ 慢位(`skipped_slow`)，
     混在一起读的人就分不清"没时间了"和"它本来就不算轻调用"；
  4. **慢位名册不许空、且每位都要有量到的耗时** —— 否则它退化成一句口号。
"""
from __future__ import annotations

import unittest

from gbt_allinone import cross_scan as cs
from gbt_allinone.caps_registry import BENIGN_CAPS


class HBudgetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # 0 预算 ⇒ H 维一位都不许起调用（非 H 维照旧跑，与本次改动无关）
        cls.data = cs.scan(deep=True, h_budget_s=0.0)

    def test_zero_budget_stops_before_any_call(self) -> None:
        dc = self.data["deep_coverage"]
        self.assertTrue(dc["deadline_hit"], "0 预算却没报超时 —— 预算形同虚设")
        self.assertEqual(dc["checked"], 0, "0 预算还起了调用 —— 有界没生效")
        self.assertGreater(dc["not_probed_n"], 0, "没跑到的一个都没报出来")

    def test_denominator_closes(self) -> None:
        dc = self.data["deep_coverage"]
        total = (dc["checked"] + dc["skipped_side_effect_n"] + dc["unsafe_n"]
                 + dc["not_probed_n"] + dc["skipped_slow_n"])
        self.assertEqual(total, len(BENIGN_CAPS),
                         "H 维分母不闭合：漏掉的那部分会被读成『探过了没问题』")

    def test_budget_bucket_and_slow_bucket_do_not_mix(self) -> None:
        dc = self.data["deep_coverage"]
        self.assertEqual([], [k for k in dc["not_probed"] if k in dc["skipped_slow"]],
                         "同一位同时出现在『没时间』与『慢位』两个桶里 ⇒ 读的人分不清原因")
        self.assertEqual(sorted(dc["skipped_slow"]), sorted(cs._SLOW_KINDS))

    def test_slow_roster_is_measured_not_asserted(self) -> None:
        self.assertTrue(cs._SLOW_KINDS, "慢位名册空了 —— 无界那台机器就回来了")
        for kind in cs._SLOW_KINDS:
            self.assertIsNotNone(cs._SLOW_KIND_COST_S.get(kind),
                                 "慢位 %s 没有量到的耗时 ⇒ 这份名册只是口号" % kind)
            self.assertGreaterEqual(cs._SLOW_KIND_COST_S[kind], 5.0,
                                    "慢位 %s 的量到耗时 < 5s，与入选阈值不符" % kind)

    def test_default_budget_is_finite(self) -> None:
        self.assertIsNotNone(cs.H_BUDGET_S)
        self.assertGreater(float(cs.H_BUDGET_S), 0.0)

    def test_unlimited_escape_hatch_still_exists(self) -> None:
        """`h_budget_s=None` 必须仍然可用（旧的无预算行为可**显式**取回，不是被偷偷删掉）。"""
        import inspect
        sig = inspect.signature(cs.scan)
        self.assertIn("h_budget_s", sig.parameters)
        self.assertEqual(sig.parameters["h_budget_s"].default, cs.H_BUDGET_S,
                         "默认必须是有界；无界只许显式传 None 拿到")


if __name__ == "__main__":
    unittest.main(verbosity=2)
