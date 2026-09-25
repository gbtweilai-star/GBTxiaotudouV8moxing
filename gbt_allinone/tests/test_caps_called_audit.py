# -*- coding: utf-8 -*-
"""能力位调用点审计 · 带牙用例（R-H192）。

① 审计覆盖全部已登记能力位（total == len(BENIGN_CAPS)）；
② wired ∪ orphan == 全部，且二者不重叠（内部一致性）；
③ **已知真接线的能力必须在 wired 里**（防"接线被拆掉"的回退）：
   `scene_anchor`（被 4 个模块 + 编排内核引用）· `trace_store`（被 selfscan 引用）；
④ 审计**不把自己算成调用方**（自己引用自己的名字不算接线）；
⑤ 诚实边界写在返回值里；只读：无网络/写盘路径。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "gbt_allinone"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gbt_allinone.caps_registry import BENIGN_CAPS  # noqa: E402
from gbt_allinone.tools import caps_called_audit as cca  # noqa: E402

KNOWN_WIRED = ("scene_anchor", "trace_store")

_AUDIT_CACHE: dict = {}


def _audit(kinds=None):
    """进程内缓存：`audit()` 实测每次约 2s（改前 19.5–33.2s），本文件要调 6 次。

    源码树在一次测试会话内不会变，重复做同一份全仓审计只是白烧 CPU ——
    代价很实：串跑时（叠加别处泄漏的采集线程抢 CPU）本文件单测被顶过
    30s 硬超时，于是**整条全量回归连判决都给不出来**。
    """
    key = None if kinds is None else tuple(sorted(kinds))
    if key not in _AUDIT_CACHE:
        _AUDIT_CACHE[key] = cca.audit(kinds)
    return _AUDIT_CACHE[key]


class AuditTests(unittest.TestCase):
    def test_covers_every_registered_capability(self):
        data = _audit()
        self.assertEqual(data["total"], len(BENIGN_CAPS))
        self.assertGreater(data["scanned_files"], 100, "扫描面太小 = 口径错了")

    def test_wired_and_orphan_are_a_partition(self):
        data = _audit()
        wired = {r["kind"] for r in data["wired"]}
        orphan = set(data["orphans"])
        entries = set(data["external_entries"])       # R-H194：入口型是第三支
        self.assertEqual(wired | orphan | entries, set(BENIGN_CAPS),
                         "三支必须覆盖全部已登记能力位")
        self.assertEqual(wired & orphan, set(), "两者不许重叠")
        self.assertEqual(entries & orphan, set(), "入口型与孤儿不许重叠")
        self.assertEqual(data["wired_count"] + data["orphan_count"] + len(entries),
                         data["total"], "三支计数相加必须等于总数")

    def test_known_wired_capabilities_stay_wired(self):
        """防回退：这几条已知真的被别的模块引用，掉出 wired 就是接线被拆了。"""
        data = _audit(list(KNOWN_WIRED))
        wired = {r["kind"] for r in data["wired"]}
        for kind in KNOWN_WIRED:
            self.assertIn(kind, wired, "%s 应当有真调用方" % kind)

    def test_self_reference_does_not_count(self):
        """审计器不许把自己算成调用方。"""
        data = _audit(["caps_called_audit"])
        row = data["wired"][0] if data["wired"] else {
            "kind": "caps_called_audit", "callers": [], "self_refs": []}
        # 口径：它自己的文件（caps_called_audit.py）里写着这个名字 —— **不算调用方**
        self.assertNotIn("gbt_allinone/tools/caps_called_audit.py", row["callers"],
                         "同名模块自己提自己的名字 ≠ 有人调用它")
        # 但编排内核**真的** import 了它 ⇒ 它如今是有调用方的（这不矛盾：真接线才算）
        self.assertIn("gbt_allinone/tools/orchestration_kernel.py", row["callers"],
                      "编排内核已真 import 它 ⇒ 应当算接线")

    def test_ops_and_honest_boundary(self):
        orph = cca.run("orphans")
        self.assertTrue(orph["readonly"])
        self.assertEqual(orph["orphan_count"], len(orph["orphans"]))
        self.assertIn("候选接线", cca.HONEST_BOUNDARY)

    def test_capability_types_split_orphans_from_entries(self):
        """甲第二步（R-H194）：**先分类型，再报孤儿** —— 入口型不报孤儿。"""
        data = _audit()
        self.assertEqual(cca.cap_type("codex_tools"), "external")
        self.assertEqual(cca.cap_type("auth_gate_status"), "external")
        self.assertEqual(cca.cap_type("projection_card"), "internal",
                         "内调型默认：没分类的能力位按『该被调用』要求")
        for kind in data["external_entries"]:
            self.assertNotIn(kind, data["orphans"], "%s 是入口型，不该报孤儿" % kind)
        self.assertEqual(sorted(data["unwired_by_name"]),
                         sorted(list(data["orphans"]) + list(data["external_entries"])),
                         "两支必须覆盖全部未接线能力位（不洗白数字）")

    def test_no_internal_orphans_left_and_sec_chain_is_a_gate(self):
        """R-H202：内调型孤儿应清零；`sec_chain` 是**安全面入口**（判定为门，不是漏接）。"""
        data = _audit()
        self.assertEqual(data["orphans"], [], "内调型孤儿必须清零")
        self.assertIn("sec_chain", data["external_entries"])
        self.assertEqual(cca.cap_type("sec_chain"), "external")

    def test_module_has_no_network_or_write_paths(self):
        src = Path(cca.__file__).read_text(encoding="utf-8")
        for bad in ("import requests", "import urllib", "import socket", "import subprocess",
                    ".write_text(", ".write_bytes(", "unlink(", "from ..store"):
            self.assertNotIn(bad, src, "只读审计里不该出现：%s" % bad)


if __name__ == "__main__":
    unittest.main()
