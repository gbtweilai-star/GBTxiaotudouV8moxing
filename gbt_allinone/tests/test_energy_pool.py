# -*- coding: utf-8 -*-
"""能源池 · 带牙用例（R-H223）。

① 五条红线都在，且各自有机械闸；
② 红线①：**模型是燃料，不是身份**（owner_ai_id 填模型名 ⇒ 拒）；
③ 红线②：能源可换、**原生栈不动**（指纹漂移 ⇒ 拒）；
④ 红线③：**衍生代码必须走原生路由**（SDK 直连 / 自己拼请求 ⇒ 拒）；
⑤ 红线④⑤：按需分配 + **没有能源如实报缺**（不硬撑）；
⑥ 取证如实：能源数从盘上动态读；**免费/付费盘上判不出 ⇒ 标 unknown**（不编）；
⑦ 只读骨架里不许有网络 / 写盘 / 发密钥路径；登记在册且**落地即接线**。
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "gbt_allinone"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gbt_allinone.tools import energy_pool as ep  # noqa: E402
from gbt_allinone.tools import orchestration_kernel as ok  # noqa: E402
from gbt_allinone import caps_registry as CR  # noqa: E402


class RedLineTests(unittest.TestCase):
    def test_five_redlines_each_have_a_gate(self):
        r = ep.run("redlines")
        self.assertEqual(len(r["red_lines"]), 5)
        for s in ("燃料", "身份", "原生栈", "原生路由", "按需", "如实报缺"):
            self.assertTrue(any(s in x for x in r["red_lines"]),
                            "五条红线里少了：%s" % s)
        self.assertEqual(len(r["side_rules"]), 3, "附带三条也要在")

    def test_model_is_not_identity(self):
        self.assertEqual(ep.check_identity_not_model("")["rule"],
                         "missing_owner_ai_id")
        bad = ep.check_identity_not_model("deepseek")
        self.assertEqual(bad["rule"], "model_is_not_identity",
                         "模型是燃料，不是身份 —— owner_ai_id 不能填模型名")
        self.assertEqual(ep.check_identity_not_model("agnes")["rule"],
                         "model_is_not_identity")
        self.assertTrue(ep.check_identity_not_model("ai-video-1")["ok"])

    def test_stack_must_not_drift(self):
        self.assertEqual(ep.check_stack_unchanged()["rule"],
                         "missing_stack_fingerprint")
        self.assertEqual(ep.check_stack_unchanged("abc", "xyz")["rule"],
                         "stack_drift", "换能源不许把原生栈也换了")
        self.assertTrue(ep.check_stack_unchanged("abc", "abc")["ok"])

    def test_derived_code_must_use_native_route(self):
        self.assertEqual(ep.check_derived_code("")["rule"],
                         "empty_derived_code", "未测不按绿")
        bad = ep.check_derived_code("import openai\nclient = openai.Client()")
        self.assertEqual(bad["rule"], "derived_bypasses_route")
        bad2 = ep.check_derived_code("requests.post('https://api.x/v1/gen')")
        self.assertEqual(bad2["rule"], "derived_bypasses_route")
        good = ep.check_derived_code(
            "from gbt_allinone import api\napi.run_task('llm_chat', {})\n")
        self.assertTrue(good["ok"], "走原生路由的衍生代码要放行")

    def test_no_energy_is_reported_honestly(self):
        self.assertEqual(ep.lease_energy("")["rule"], "missing_owner_ai_id")
        out = ep.lease_energy("ai-not-configured-xyz")
        self.assertFalse(out["ok"])
        self.assertTrue(out.get("honest"), "**没有能源 ⇒ 如实报缺**，不硬撑")
        self.assertEqual(out["rule"], "no_key_for_owner")


class ForensicsAndSkeletonTests(unittest.TestCase):
    def test_energies_are_read_from_disk_not_hardcoded(self):
        st = ep.run("status")
        self.assertEqual(st["count"], len(st["energies"]))
        names = [x["name"] for x in st["energies"]]
        self.assertIn("deepseek", names)
        self.assertIn("agnes", names)
        for x in st["energies"]:
            self.assertEqual(x["tier"], "unknown",
                             "免费/付费盘上判不出 ⇒ 一律 unknown，不许编")
        self.assertEqual(st["tier_known"], [])

    def test_dpapi_missing_is_reported(self):
        st = ep.run("status")
        self.assertIn("deepseek", st["dpapi_on_disk"])
        self.assertIn("agnes", st["dpapi_missing"],
                      "agnes_api.dpapi 不在盘上 ⇒ 必须如实报缺")

    def test_module_has_no_network_or_write_paths(self):
        src = Path(ep.__file__).read_text(encoding="utf-8")
        for bad in ("import requests", "import urllib", "import socket",
                    "import subprocess", ".write_text(", ".write_bytes(",
                    "unlink("):
            self.assertNotIn(bad, src, "只读骨架里不该出现：%s" % bad)


class WiringTests(unittest.TestCase):
    def test_registered_and_wired(self):
        cap = CR.BENIGN_CAPS.get("energy_pool")
        self.assertIsNotNone(cap)
        self.assertEqual(cap["handler"], "energy_pool")
        self.assertIn("energy_pool", ok._READONLY_MODULES)
        self.assertIs(ok._READONLY_MODULES["energy_pool"], ep)


class AbstractionAndDeriverTests(unittest.TestCase):
    """R-H224 · 能源抽象层 + 原生能力衍生器（**自己生成的代码要过自己的红线**）。"""

    def test_energy_source_has_the_seven_fields(self):
        from dataclasses import fields
        got = {f.name for f in fields(ep.EnergySource)}
        self.assertEqual(got, {"source_id", "grade", "kind", "endpoint",
                               "key_ref", "capability", "status"})
        src = ep.EnergySource(source_id="x")
        self.assertEqual(src.grade, "未知", "盘上无该字段 ⇒ 默认未知，不编")
        self.assertEqual(src.kind, "未知", "荤素只是比喻，不参与判据")
        self.assertIn(src.status, ep.STATUSES)

    def test_sources_built_from_disk(self):
        r = ep.run("sources")
        self.assertEqual(r["count"], 2)
        by = {s["source_id"]: s for s in r["sources"]}
        self.assertEqual(by["deepseek"]["status"], "可用",
                         "deepseek_api.dpapi 在盘上")
        self.assertEqual(by["agnes"]["status"], "缺key",
                         "agnes_api.dpapi 不在盘上 ⇒ 缺key（如实）")
        self.assertTrue(all(s["grade"] == "未知" for s in r["sources"]))
        # 判据卡在真问题上：key_ref 必须是 **DPAPI 引用**，且**不含密钥形状**
        # （上一版我拿 "secret" 做子串判据 ⇒ 被路径 `store/secrets/` 误伤，属判据扩大化）
        for s in r["sources"]:
            self.assertTrue(s["key_ref"].endswith(".dpapi"),
                            "key_ref 必须是 DPAPI 引用：%s" % s["key_ref"])
            self.assertIsNone(
                re.search(r"\b(?:sk|ak|lt)[-_][A-Za-z0-9_\-]{16,}\b", s["key_ref"]),
                "key_ref 里不许出现密钥形状")

    def test_derived_code_passes_our_own_redline(self):
        """🔴 自洽带牙：**衍生器生成的代码，必须能过红线③自己的闸**。"""
        r = ep.run("derive_code", source_id="deepseek")
        self.assertTrue(r["self_check"]["ok"],
                        "自己生成的代码没过自己的闸：%s" % r["self_check"])
        self.assertIn("run_task", r["code"], "必须走原生路由")
        self.assertNotIn("import requests", r["code"])
        self.assertNotIn("openai", r["code"])

    def test_missing_energy_derives_nothing(self):
        r = ep.run("derive_code", source_id="agnes")
        self.assertIn("不生成调用代码", r["code"],
                      "缺 key 的能源 ⇒ 不生成代码，如实报缺")
        self.assertIn("raise RuntimeError", r["code"])
        self.assertEqual(ep.run("derive_code", source_id="不存在")["rule"],
                         "unknown_source")

    def test_video_pipeline_by_capability(self):
        t2v = ep.run("derive_pipeline", capability="文生视频")
        self.assertTrue(t2v["ok"])
        self.assertIn("提示词", t2v["steps"][0])
        i2v = ep.run("derive_pipeline", capability="image")
        self.assertIn("上传参考图(OSS)", i2v["steps"][0])
        ext = ep.run("derive_pipeline", capability="video")
        self.assertIn("上传已有视频(OSS)", ext["steps"][0])
        self.assertEqual(ep.run("derive_pipeline", capability="魔法")["rule"],
                         "unknown_capability", "不硬凑蓝图")


class PoolAndSelfDevTests(unittest.TestCase):
    """R-H225 · 能源池（**不挑食但有优先级**）+ 视频自研八层图。"""

    def test_pool_registers_and_picks_free_first(self):
        pool = ep.EnergyPool()
        pool.register(ep.EnergySource(source_id="paid-1", grade="付费",
                                      capability=("text",), status="可用",
                                      key_ref="store/secrets/a.dpapi"))
        pool.register(ep.EnergySource(source_id="free-1", grade="免费",
                                      capability=("text",), status="可用",
                                      key_ref="store/secrets/b.dpapi"))
        got = pool.pick("text", prefer="免费")
        self.assertEqual(got.source_id, "free-1",
                         "**免费优先**（荤素之别，不是好坏之别）")
        got2 = pool.pick("text", prefer="付费")
        self.assertEqual(got2.source_id, "paid-1", "偏好可换 ⇒ 说明只是偏好")

    def test_pool_does_not_pick_unavailable_or_unmatched(self):
        pool = ep.EnergyPool()
        pool.register(ep.EnergySource(source_id="nokey", capability=("text",),
                                      status="缺key"))
        self.assertIsNone(pool.pick("text"),
                          "**没有可用能源 ⇒ 如实返回 None**（不硬撑）")
        pool.register(ep.EnergySource(source_id="vid", capability=("video",),
                                      status="可用", key_ref="store/secrets/c.dpapi"))
        self.assertIsNone(pool.pick("text"), "能力不匹配不挑")
        self.assertEqual(pool.pick("video").source_id, "vid", "不挑食：能跑就行")

    def test_pool_refuses_plaintext_key_ref(self):
        pool = ep.EnergyPool()
        bad = pool.register(ep.EnergySource(source_id="x", key_ref="sk-plain-key-123456"))
        self.assertEqual(bad["rule"], "key_must_be_dpapi")

    def test_pool_loads_from_disk(self):
        r = ep.run("pool", capability="text")
        self.assertEqual(r["registered"], ["agnes", "deepseek"])
        self.assertEqual(r["picked"]["source_id"], "deepseek",
                         "agnes 缺key ⇒ 只有 deepseek 可用")

    def test_self_dev_eight_layers_vs_six_step_pipeline(self):
        s = ep.run("self_dev_layers")
        self.assertEqual(s["count"], 8)
        names = [x["layer"] for x in s["layers"]]
        self.assertEqual(names[0], "脚本/分镜")
        self.assertEqual(names[-1], "原生剪辑 + 品牌片尾")
        native = [n for n in names if "原生" in n]
        self.assertEqual(len(native), 4,
                         "四层带『原生』⇒ 这份讲的是**自研边界**")
        self.assertEqual(len(s["vs_pipeline"]), 3, "三处差异都要照报")
        self.assertIn("并存", s["note"], "两个维度并不同，不许合并")
        self.assertEqual(
            [x["module"] for x in s["layers"] if x["module"]],
            ["caps_registry", "orchestration_kernel", "render_evolution",
             "render_evolution", "brand_outro"])


class NativeStackFourTests(unittest.TestCase):
    """R-H226 · 「原生栈」= 触手/记忆/门禁/审计 —— 换模型时**逐项**验，不看总指纹。"""

    def test_five_redlines_all_have_gates(self):
        r = ep.run("native_stack")
        self.assertEqual(len(r["redlines"]), 5)
        for x in r["redlines"]:
            self.assertTrue(str(x["gate"]).strip(), "%s 没写闸" % x["cn"])

    def test_native_stack_is_the_four_named_things(self):
        ns = ep.run("native_stack")["native_stack"]
        self.assertEqual([x["cn"] for x in ns], ["触手", "记忆", "门禁", "审计"])

    def test_four_items_checked_individually_not_by_total_fingerprint(self):
        """🔴 关键：总指纹一样，也可能"触手换了、审计没换"互相抵消。"""
        before = {"tentacle": "A", "memory": "B", "gate": "C", "audit": "D"}
        after_same = dict(before)
        self.assertTrue(ep.check_stack_four(before, after_same)["ok"])
        # 只有"触手"变了 ⇒ 逐项查验必须抓到（总指纹可能因别的抵消而看不出）
        after_one = dict(before, tentacle="X")
        out = ep.check_stack_four(before, after_one)
        self.assertEqual(out["rule"], "native_stack_changed")
        self.assertEqual(out["changed"], ["触手"])
        self.assertEqual(ep.check_stack_four({}, {})["rule"],
                         "missing_stack_snapshot")

    def test_all_four_are_guarded(self):
        before = {"tentacle": "A", "memory": "B", "gate": "C", "audit": "D"}
        for k, cn in (("tentacle", "触手"), ("memory", "记忆"),
                      ("gate", "门禁"), ("audit", "审计")):
            out = ep.check_stack_four(before, dict(before, **{k: "changed"}))
            self.assertEqual(out["rule"], "native_stack_changed",
                             "%s 变了必须抓到" % cn)
            self.assertIn(cn, out["changed"])


if __name__ == "__main__":
    unittest.main()
