"""上帝之眼判据（主人令 2026-09-27）。

主人原话：「上帝之眼是能看到**创作页面**这些…**克劳德**给意见和建议、商量架构与方向，**决策权在你这里**；
把 **CodeBuddy 也部署进上帝之眼**，做杂事，**主项目她没有执行权**，只有服从安排和随时候命；
以及**每日的 GBT 探针汇报和每日全量扫描框架**指出**缺点、短板、卡点**；然后你自己跟克劳德
在上帝之眼里面**计划优化和提升整体实力**。」

**判据（都可判定）**：
  A. **眼睛**：创作页面 ≥7 个且**文件真在**；服务读数来自**真连端口**（不是"应该开着"）；
  B. **顾问权限是机器可读的**：两位顾问都在册，且各自带 `may` / `may_not`；
  C. **CodeBuddy 越权必拒**：给它一个点了主项目路径的任务 ⇒ 必须 `refused=True`；
  D. **每日汇报三张清单**：缺点/短板/卡点都在，且**每条带 `src`**（来源）；
  E. **计划面留痕**：提案与决策都能写进 `state/gods_eye_plan.jsonl`（决策权在主体）。
"""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "gbt_allinone" / "tools" / "gods_eye.py"
PLAN = ROOT / "state" / "gods_eye_plan.jsonl"
PANEL = ROOT / "holo_pet" / "assets" / "godview" / "index.html"


def _load():
    spec = importlib.util.spec_from_file_location("gods_eye_probe", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestGodsEye(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _load()

    def test_a_eye_sees_creation_pages(self):
        """A. 眼睛：创作页面 ≥7 且真在（不是登记了看不见）。"""
        s = self.m.see()
        self.assertGreaterEqual(s["pages_total"], 7, "创作页面少于 7 个（眼睛看不全）")
        self.assertEqual(s["pages_ok"], s["pages_total"],
                         f"有页面文件不在：{[p['page'] for p in s['pages'] if not p['exists']]}")
        for svc in s["services"]:
            self.assertIn("listening", svc, "服务读数缺字段（必须是真连端口的结果）")

    def test_b_advisors_machine_readable(self):
        """B. 两位顾问在册，权限为机器可读表（may / may_not）。"""
        a = self.m.advisors()
        self.assertEqual({"claude", "codebuddy"}, set(a["advisors"]),
                         f"顾问位不对：{sorted(a['advisors'])}")
        for k, v in a["advisors"].items():
            self.assertTrue(v.get("may"), f"{k} 缺 may")
            self.assertTrue(v.get("may_not"), f"{k} 缺 may_not")
        self.assertIn("决策", a.get("decider", ""), "必须写明决策权在主体")

    def test_c_codebuddy_has_no_exec_authority(self):
        """C. **CodeBuddy 对主项目没有执行权**：点主项目路径必须被拒。"""
        r = self.m.ask("codebuddy", "把 projects/movie/产线 里的清单都改一遍")
        self.assertTrue(r.get("refused"), f"竟然没拒：{r}")
        self.assertFalse(r.get("ok"), "越权请求不许通过")

    def test_d_daily_three_lists_with_src(self):
        """D. 每日汇报：缺点/短板/卡点三张清单都在，且每条带来源。"""
        d = self.m.daily()
        s = d["全量扫描"]
        for cat in ("缺点", "短板", "卡点"):
            self.assertIn(cat, s, f"缺 {cat} 清单")
            for x in s[cat]:
                self.assertTrue(x.get("src"), f"{cat} 里有条目没写来源：{x}")
        self.assertIn("探针汇报", d, "缺探针汇报")

    def test_e_plan_has_trail(self):
        """E. 计划面留痕：提案与决策都能落进台账。"""
        self.m.plan("add", item="判据自检用提案", src="test_gods_eye")
        r = self.m.plan("decide", item="判据自检用提案", decision="采纳")
        self.assertTrue(r.get("ok"), f"决策没记上：{r}")
        self.assertTrue(PLAN.is_file(), "计划台账不存在")
        self.assertIn("决策权在主体", self.m.plan("list").get("decider", ""))
        self.assertTrue(PANEL.is_file(), "上帝之眼页面不存在 ⇒ 跑 panel")


if __name__ == "__main__":
    unittest.main(verbosity=2)
