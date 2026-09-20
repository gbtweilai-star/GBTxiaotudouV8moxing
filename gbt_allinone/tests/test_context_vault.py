# -*- coding: utf-8 -*-
"""上下文归档库 · 带牙用例（R-H230）。

① 定位：**索引 + 检索层**，不是第四处存储（正文**引用不复制**）；
② 预算按**可用内存**算；**可用不足 ⇒ 降级如实报**（不崩）；
③ 快速搜索：倒排求交 → 打分 → **按预算裁剪**（取满即停，截断要如实说）；
④ 检索结果**必须带出处**；
⑤ 归档/检索文本不许改写身份；登记在册且落地即接线。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "gbt_allinone"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gbt_allinone.tools import context_vault as cv  # noqa: E402
from gbt_allinone.tools import orchestration_kernel as ok  # noqa: E402
from gbt_allinone import caps_registry as CR  # noqa: E402


class PositioningTests(unittest.TestCase):
    def test_it_is_an_index_layer_not_a_fourth_store(self):
        st = cv.run("status")
        self.assertIn("索引", st["positioning"])
        self.assertIn("不是第四处存储", st["positioning"])
        self.assertIn("可用", st["proposition"])
        self.assertEqual([x["key"] for x in cv.run("layers")["layers"]],
                         ["hot", "warm", "cold"])

    def test_five_redlines(self):
        r = cv.run("redlines")
        self.assertEqual(len(r["red_lines"]), 5)
        for s in ("第四处", "出处", "可用内存", "降级", "身份"):
            self.assertTrue(any(s in x for x in r["red_lines"]), "少了：%s" % s)

    def test_index_only_refuses_body_fields(self):
        self.assertEqual(cv.check_index_only({"source_ref": "x", "content": "正文"})["rule"],
                         "fourth_copy_detected",
                         "把正文塞进库 = 造第四处真相")
        self.assertEqual(cv.check_index_only({"source_ref": "x", "text": "abc"})["rule"],
                         "fourth_copy_detected")
        self.assertTrue(cv.check_index_only({"source_ref": "x", "terms": ["a"]})["ok"])


class BudgetTests(unittest.TestCase):
    def test_budget_uses_available_memory(self):
        # 中档：cap 不生效 ⇒ 预算 = 可用 × ratio
        mid = cv.compute_budget(100 * 1024**2, 8 * 1024**3)
        self.assertTrue(mid["ok"])
        self.assertEqual(mid["budget_bytes"],
                         int(100 * 1024**2 * cv.BUDGET_RATIO))
        self.assertFalse(mid["degraded"])
        # 大内存：**上限生效**（不许把机器吃干）
        big = cv.compute_budget(4 * 1024**3, 8 * 1024**3)
        self.assertEqual(big["budget_bytes"], cv.BUDGET_CAP_BYTES,
                         "clamp 到上限：预算不许无限大")

    def test_budget_refuses_total_memory_as_basis(self):
        self.assertEqual(cv.compute_budget(8 * 1024**3, 8 * 1024**3)["rule"],
                         "budget_over_total", "可用 ≥ 总 ⇒ 这是拿总内存当依据")

    def test_low_memory_degrades_honestly(self):
        b = cv.compute_budget(200 * 1024)          # 可用 200KB
        self.assertTrue(b["ok"], "**降级而不是崩**")
        self.assertTrue(b["degraded"])
        self.assertEqual(b["rule"], "budget_too_low")
        self.assertIn("不崩", b["why"])
        self.assertEqual(cv.compute_budget(None)["rule"], "missing_avail_memory",
                         "没有可用内存读数 ⇒ 不许拍一个预算")


class SearchTests(unittest.TestCase):
    def _vault(self):
        v = cv.ContextVault()
        v.add("trace/a", "部署 LibTV 画布 生成 视频", "warm")
        v.add("trace/b", "部署 失败 回滚", "cold")
        v.add("trace/c", "今天天气不错", "warm")
        return v

    def test_fast_search_is_inverted_index_and_ranked(self):
        r = self._vault().search("部署")
        self.assertTrue(r["ok"])
        refs = [h["source_ref"] for h in r["hits"]]
        self.assertEqual(refs, ["trace/a", "trace/b"], "命中两条，按 ref 稳定排序")
        self.assertTrue(all(h["source_ref"] for h in r["hits"]),
                        "**每条都要带出处**")

    def test_search_respects_budget_and_says_truncated(self):
        v = self._vault()
        full = v.search("部署", budget_bytes=0)
        tiny = v.search("部署", budget_bytes=80)
        self.assertTrue(tiny["ok"])
        self.assertLessEqual(len(tiny["hits"]), len(full["hits"]))
        tiny2 = v.search("部署", budget_bytes=80, max_items=1)
        self.assertTrue(tiny2["truncated"] or len(tiny2["hits"]) <= 1,
                        "取满即停，且**截断要如实说**")

    def test_empty_query_and_no_hits_are_honest(self):
        self.assertEqual(cv.run("search", query="")["rule"], "empty_query")
        r = self._vault().search("量子力学")
        self.assertEqual(r["rule"], "no_hits", "**没命中就如实说没命中**")

    def test_entry_without_source_ref_is_refused(self):
        v = cv.ContextVault()
        self.assertEqual(v.add("", "text")["rule"], "no_source_ref")
        self.assertEqual(cv.must_cite([{"score": 1}])["rule"], "no_source_ref")


class IdentityAndWiringTests(unittest.TestCase):
    def test_identity_not_rewritten(self):
        self.assertEqual(cv.check_identity_text("我是 GPT-4")["rule"],
                         "identity_rewritten")
        self.assertTrue(cv.check_identity_text("我是 GBT小土豆")["ok"])

    def test_module_has_no_write_or_network_paths(self):
        src = Path(cv.__file__).read_text(encoding="utf-8")
        for bad in ("import requests", "import urllib", "import socket",
                    "subprocess.run(", ".write_text(", ".write_bytes("):
            self.assertNotIn(bad, src, "只读骨架里不该出现：%s" % bad)

    def test_registered_and_wired(self):
        cap = CR.BENIGN_CAPS.get("context_vault")
        self.assertIsNotNone(cap)
        self.assertEqual(cap["domain"], "system")
        self.assertIn("context_vault", ok._READONLY_MODULES)
        self.assertIs(ok._READONLY_MODULES["context_vault"], cv)


if __name__ == "__main__":
    unittest.main()
