"""R-H609（2026-09-25）· **排查台账的字段契约**（Owner 令：「重启之后自动读取」）。

背景（Owner 原话的意思）：
    「你必须要有个习惯：今天做到哪里、哪里没做、问题故障、排查记录以及时间点，
      全部都要记得清清楚楚；重启之后自动读取。」
⇒ 台账 `state/排查台账.json` 由宿主插件 `plugins/gbt-master/lib/host.js` 渲染成会话头的
   第三块上下文（与「总面板」「数字人工作流」同一机制、同一刷新节奏）。

为什么需要这条用例（**渲染器只渲染、不编造**）：
    渲染器对缺字段的处理是**写「（未写）」**——这对人是诚实的，但**对机器是静默的**：
    台账哪天丢了一个 `id` 或 `severity`，注入出来的块照样"看着正常"，只是内容变成占位符。
    ⇒ 所以字段契约必须由**判据**守着，而不是靠"我会记得写"。

判据（四条，都要有牙）：
  1. 台账能解析，且顶层键齐全（`updated_at` / `rounds_done` / `in_progress` / `not_done` /
     `open_faults` / `owner_decisions` / `today_done` / `log`）；
  2. `updated_at` 是**可解析的 ISO 时间**（"时间点"是 Owner 明确要的，不许写成"昨天"）；
  3. 三个清单里每一项都必须有**稳定 id**，`open_faults` 还必须有 `severity`
     （渲染器要读它，缺了就变占位符）；
  4. `log` 每笔都要有 `at`（时间点）与 `what`，且**时间不倒流**（后一笔不早于前一笔）。
"""
from __future__ import annotations

import json
import re
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "state" / "排查台账.json"
HOST_JS = ROOT / "plugins" / "gbt-master" / "lib" / "host.js"

REQUIRED_TOP = ("updated_at", "rounds_done", "in_progress", "not_done",
                "open_faults", "owner_decisions", "today_done", "log")


def _load() -> dict:
    with LEDGER.open(encoding="utf-8") as fh:
        return json.load(fh)


class LedgerContractTest(unittest.TestCase):
    def test_file_exists_and_parses(self) -> None:
        self.assertTrue(LEDGER.is_file(), "台账文件不存在：%s" % LEDGER)
        self.assertIsInstance(_load(), dict)

    def test_required_top_keys(self) -> None:
        led = _load()
        missing = [k for k in REQUIRED_TOP if k not in led]
        self.assertEqual([], missing,
                         "台账缺顶层键：%s ⇒ 注入块会静默变成『（未写）』" % missing)

    def test_updated_at_is_a_real_timestamp(self) -> None:
        raw = str(_load().get("updated_at") or "")
        self.assertTrue(raw, "updated_at 空了 —— 时间点是 Owner 明确要的")
        # 允许 `2026-09-25T18:05:00+08:00` / `2026-09-25 18:05` 两种写法
        text = raw.replace(" ", "T")
        try:
            datetime.fromisoformat(text)
        except ValueError:
            self.fail("updated_at 不是可解析的时间戳：%r（不许写『昨天』这类相对说法）" % raw)

    def test_items_have_stable_ids(self) -> None:
        led = _load()
        for key in ("not_done", "open_faults", "owner_decisions"):
            items = led.get(key) or []
            self.assertIsInstance(items, list, "%s 必须是列表" % key)
            for it in items:
                self.assertIsInstance(it, dict, "%s 里出现非对象项：%r" % (key, it))
                self.assertTrue(str(it.get("id") or "").strip(),
                                "%s 里有一项没有 id（渲染器按 id 点名，缺了就没法引用）" % key)
        for it in led.get("open_faults") or []:
            self.assertTrue(str(it.get("severity") or "").strip(),
                            "未清故障 %s 没写 severity" % it.get("id"))

    def test_log_entries_have_time_and_are_monotonic(self) -> None:
        log = _load().get("log") or []
        self.assertTrue(log, "log 空 —— 台账就退化成一张清单，不是『排查记录』")
        seen = []
        for row in log:
            self.assertTrue(str(row.get("at") or "").strip(), "有记录没写时间点：%r" % row)
            self.assertTrue(str(row.get("what") or "").strip(), "有记录没写做了什么：%r" % row)
            seen.append(row["at"].replace(" ", "T"))
        parsed = [datetime.fromisoformat(t) for t in seen]
        for a, b in zip(parsed, parsed[1:]):
            self.assertLessEqual(a, b, "排查记录时间倒流：%s → %s" % (a, b))


class InjectionIsWiredTest(unittest.TestCase):
    """台账必须真的被插件读并注入 —— 否则"重启自动读取"只是愿望。"""

    def test_host_js_reads_the_ledger_and_injects_it(self) -> None:
        src = HOST_JS.read_text(encoding="utf-8", errors="replace")
        self.assertIn("state/排查台账.json", src, "插件没去读台账文件")
        self.assertIn("gbt-progress-ledger", src, "插件没注册台账那块注入")
        self.assertRegex(src, re.escape("ctx.systemPrompt.context({"),
                         "没有走既有的 systemPrompt.context 注入机制")
        # 与数字人状态同一条口径：读不到就说读不到，不许猜
        self.assertIn("台账文件读不到", src, "读不到台账时没有如实上报")

    def test_renderer_reads_exactly_the_fields_this_test_guards(self) -> None:
        """渲染器读哪些字段 ⇒ 本文件就守哪些字段（防两边慢慢漂开）。"""
        src = HOST_JS.read_text(encoding="utf-8", errors="replace")
        for field in ("not_done", "open_faults", "owner_decisions", "today_done",
                      "log", "updated_at", "rounds_done", "in_progress"):
            self.assertIn(field, src, "渲染器不再读 %s ⇒ 本用例守的字段该同步改" % field)


if __name__ == "__main__":
    unittest.main(verbosity=2)
