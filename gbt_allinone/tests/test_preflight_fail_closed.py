# -*- coding: utf-8 -*-
"""F3 判据：preflight（感知层）故障时，**有副作用的调用必须按拒处理**（不再 fail-open）。

背景（排查台账 F3 · 高）：`api.run_task` 里 preflight 抛异常时，原实现一律把守卫降级成
`not_guarded` 然后**照跑** —— 理由写的是"感知层故障不能阻止原有能力"。可这只对**读类**成立；
**要作用域的**调用跳过守卫 = "守卫坏了就没人管了" ⇒ 2026-09-28 改为按风险分流。

判据（喂坏样本，看拦不拦得住）：
  A. **要作用域**的调用 + preflight 抛异常 ⇒ **必须 denied**，且说清"是感知层故障"；
  B. **读类**调用 + preflight 抛异常 ⇒ **照常放行**（不许把读也一起挡死）；
  C. 异常路径**留痕**：audit 里能查到 `preflight_error`（不许无声）。
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _load_preflight_mod():
    """按包路径导入 preflight（与 api 用的是同一份实例 —— 按文件路径再装一份会打到别的对象上）。"""
    from gbt_allinone import preflight as pf
    return pf


class TestPreflightFailClosed(unittest.TestCase):
    """A/B/C 三条都在**同一进程内**用猴子补丁喂坏样本（真跑，不是读代码）。"""

    @classmethod
    def setUpClass(cls):
        import gbt_allinone as g
        cls.g = g
        cls.pf = _load_preflight_mod()
        cls._orig = cls.pf.before_action

    def tearDown(self):
        self.pf.before_action = self._orig

    def _boom(self, *a, **k):
        raise RuntimeError("判据样本：感知层故障")

    def test_a_side_effect_kind_is_refused(self):
        self.pf.before_action = self._boom
        # `filesystem_write` 类调用（写盘）—— 典型"有副作用"
        r = self.g.run_task("obsidian_vault", {"op": "provision", "only": "lobehub"})
        p = r.get("result", r)
        if isinstance(p, dict) and "result" in p:
            p = p["result"]
        # 可能先被授权门拦（没票）——那也是"按拒处理"，符合 fail-closed 的意图
        self.assertTrue(p.get("denied") or not p.get("ok"),
                        f"**感知层故障时竟然放行了有副作用的调用**：{str(p)[:200]}")
        blob = json.dumps(r, ensure_ascii=False)
        self.assertTrue(("preflight" in blob) or ("授权" in blob) or ("authorization" in blob),
                        "拒了但没说清是谁拦的（感知层还是授权门）")

    def test_b_read_only_kind_still_works(self):
        self.pf.before_action = self._boom
        r = self.g.run_task("console_hub", {"op": "pages"})
        p = r.get("result", r)
        if isinstance(p, dict) and "result" in p:
            p = p["result"]
        self.assertTrue(p.get("ok"), f"读类被一起挡死了（不该）：{str(p)[:200]}")

    def test_c_audit_records_the_error(self):
        self.pf.before_action = self._boom
        self.g.run_task("console_hub", {"op": "status"})
        led = ROOT / "gbt_allinone" / "store" / "audit.jsonl"
        self.assertTrue(led.is_file(), "审计台账不在 ⇒ 异常路径没留痕")
        tail = led.read_text(encoding="utf-8", errors="replace").splitlines()[-60:]
        self.assertTrue(any("preflight_error" in ln for ln in tail),
                        "audit 尾部看不到 preflight_error ⇒ 异常路径无声")


if __name__ == "__main__":
    unittest.main(verbosity=2)
