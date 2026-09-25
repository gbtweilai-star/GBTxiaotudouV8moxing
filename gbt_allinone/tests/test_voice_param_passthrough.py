"""R-H601（2026-09-25）· voice 参数**静默丢失**的两层回归用例。

为什么要有这两条（都是**实测踩到的**，不是理论风险）：
  1. **能力层**：`voice_cap.run()` 用 `params.get(...)` 逐个取值 —— 认不出的参数
     **静默丢**，调用方只看到 `ok:true`。实测：`path=<wav路径>` 期望落盘，
     读数却是 `{"ok":true,"backend":"win-sapi","spoken":true}`（直接发声、**零文件**）。
  2. **调度层**：`api.py` 的 voice 分支当年是手写白名单转发，白名单外**同样静默丢**
     ⇒ 两层都不报错，**错在哪儿看不见**。

判据（为什么这么写）：
  · 只**加字段**、不改既有字段 ⇒ 参数都认得时返回体与改动前**逐字节相同**（第 1 条守这个）；
  · 认不出就**如实报** `ignored_params`（第 2 条守这个）；
  · 调度层必须**全量透传**：白名单之外的键也得原样到能力层（第 3 条守这个）。
"""
from __future__ import annotations

import unittest
from unittest import mock

from gbt_allinone import api
from gbt_allinone import voice_cap


class VoiceIgnoredParamsTest(unittest.TestCase):
    """能力层：认不出的参数必须被点名，而不是消失。"""

    def test_status_reports_unknown_params_without_changing_known_shape(self) -> None:
        res = voice_cap.run("status", bogus_param=1, another="x")
        self.assertTrue(res["ok"])
        self.assertEqual(res["ignored_params"], ["another", "bogus_param"])
        self.assertIn("ignored_note", res)
        # 既有字段一个都没被动：这是"只加不改"的硬约束
        for key in ("tts", "asr", "listen", "recognizers", "wavein_devices"):
            self.assertIn(key, res, "status 的既有字段 %s 不见了" % key)

    def test_no_extra_params_means_no_extra_keys(self) -> None:
        """正确调用不许被塞进新键 —— 否则等于给所有既有调用方改了契约。"""
        res = voice_cap.run("status")
        self.assertNotIn("ignored_params", res)
        self.assertNotIn("ignored_note", res)

    def test_tts_accepted_set_is_exactly_the_real_signature(self) -> None:
        """`tts` 认的参数集必须与真实签名一致（多一个 = 报了不该报的）。"""
        self.assertEqual(voice_cap._ACCEPTED_PARAMS["tts"], {"text", "voice", "rate", "out"})
        self.assertEqual(voice_cap._ACCEPTED_PARAMS["listen"],
                         {"seconds", "culture", "min_confidence", "timeout", "wav"})


class VoiceDispatchPassthroughTest(unittest.TestCase):
    """调度层：`api.py` 的 voice 分支必须**全量透传**，不许再手写白名单。"""

    def test_unknown_key_reaches_capability_layer(self) -> None:
        seen: dict = {}

        def fake_run(op="tts", **params):
            seen["op"] = op
            seen["params"] = dict(params)
            return {"ok": True, "backend": "fake"}

        decision = mock.Mock()
        decision.scopes = ()
        decision.risk = "low"
        decision.action = "tts"

        with mock.patch.object(voice_cap, "run", fake_run), \
                mock.patch("gbt_allinone.security.policy.authorize",
                           return_value={"ok": True, "decision": decision, "trusted": True,
                                         "scopes": [], "authorizations": []}):
            api.run_task("voice", {"text": "x", "path": "C:/tmp/nope.wav"})

        self.assertEqual(seen["op"], "tts")
        self.assertEqual(seen["params"].get("path"), "C:/tmp/nope.wav",
                         "白名单又把 path 丢了 —— 这正是本次要修的静默丢失")
        self.assertEqual(seen["params"].get("text"), "x")
        self.assertNotIn("op", seen["params"], "op 必须只走位置参数，重复传会 TypeError")

    def test_framework_reserved_keys_are_not_forwarded(self) -> None:
        seen: dict = {}

        def fake_run(op="tts", **params):
            seen["params"] = dict(params)
            return {"ok": True}

        decision = mock.Mock()
        decision.scopes = ()
        decision.risk = "low"
        decision.action = "tts"

        with mock.patch.object(voice_cap, "run", fake_run), \
                mock.patch("gbt_allinone.security.policy.authorize",
                           return_value={"ok": True, "decision": decision, "trusted": True,
                                         "scopes": [], "authorizations": []}):
            api.run_task("voice", {"text": "x", "_probe": True, "_verify": {"ok": True}})

        self.assertNotIn("_probe", seen["params"])
        self.assertNotIn("_verify", seen["params"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
