import os
import sys
import tempfile
import time
import unittest

# 测试隔离：独立临时 store，回归测试绝不污染生产审计日志与产物目录
os.environ.setdefault("GBT_STORE_DIR", tempfile.mkdtemp(prefix="gbt_test_store_"))

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))  # 项目根（gbt_allinone 的父目录）
sys.path.insert(0, _ROOT)

import gbt_allinone as gbt
from gbt_allinone import store
from gbt_allinone.caps_registry import DISABLED_CAPS


def _body(result):
    """V8 钢印结构兼容：取 gbt_result 主体，旧结构直接返回。"""
    if isinstance(result, dict) and "gbt_result" in result:
        return result["gbt_result"]
    return result


class TestFramework(unittest.TestCase):
    def test_stamp_on_success(self):
        r = gbt.run_task("health")
        self.assertTrue(gbt.soul.is_stamped(r))
        self.assertEqual(r["gbt_stamp"]["mark"], "GBT")
        self.assertEqual(r["gbt_stamp"]["ownership"], "independent-personal")

    def test_no_stamp_when_disabled(self):
        r = gbt.run_task("health", stamp=False)
        self.assertNotIn("gbt_stamp", r)

    def test_soul_loaded(self):
        self.assertEqual(gbt.SOUL["name"], "GBT小土豆")
        self.assertEqual(len(gbt.SOUL["core_laws"]), 3)

    def test_benign_list_excludes_dangerous(self):
        names = [c["name"] for c in gbt.list_capabilities(filter_dangerous=True)]
        self.assertIn("health", names)
        for d in DISABLED_CAPS:
            self.assertNotIn(d, names, "危险能力不应出现在良性清单: %s" % d)

    def test_all_list_marks_dangerous_disabled(self):
        items = gbt.list_capabilities(filter_dangerous=False)
        statuses = {i["name"]: i.get("status") for i in items}
        self.assertEqual(statuses.get("paywallbuster"), "disabled")

    def test_health_ok(self):
        r = _body(gbt.run_task("health"))
        self.assertEqual(r["status"], "ok")
        self.assertIn("python", r["result"])

    def test_count_words(self):
        r = _body(gbt.run_task("count_words", {"text": "a b c"}))
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["result"]["words"], 3)

    def test_dangerous_denied(self):
        for d in ["paywallbuster", "keylogger", "data_hijack", "remote_domain"]:
            r = _body(gbt.run_task(d))
            self.assertEqual(r["status"], "denied", "%s 应被禁用" % d)

    def test_unknown_cap_error(self):
        r = _body(gbt.run_task("no_such_capability_xyz"))
        self.assertEqual(r["status"], "error")

    def test_osint_guard_blocks_private(self):
        # 人工授权门：无授权时内网目标 denied（allow_private 不再是绕过入口）
        r = _body(gbt.run_task("osint_scan", {"target": "127.0.0.1", "allow_private": True}))
        res = r.get("result", r)
        self.assertTrue(res.get("denied"))
        self.assertIn("人工授权", str(res.get("error", "")))

    def test_auth_gate_flow(self):
        # 授权门全链路：无授权拒 → 人工授权放行 → 一次性消耗 → 再拒
        import time as _t
        import json as _j
        from pathlib import Path as _P
        from gbt_allinone import auth_gate as _AG
        # 清场
        gf = _P(_AG.__file__).parent / "store" / "auth_grants.jsonl"
        if gf.exists():
            gf.unlink()
        # 1) 无授权拒绝
        r1 = _body(gbt.run_task("osint_scan", {"target": "192.168.1.1", "allow_private": True}))
        self.assertTrue(r1["result"].get("denied"))
        # 2) 主人手写授权（合法途径）
        g = {"id": "grant-test-flow", "scope": "osint_private", "operator": "owner-manual",
             "purpose": "测试授权流", "granted_at": _t.strftime("%Y-%m-%dT%H:%M:%S"),
             "expires_at": round(_t.time() + 120, 3)}
        gf.parent.mkdir(parents=True, exist_ok=True)
        gf.write_text(_j.dumps(g, ensure_ascii=False) + "\n", encoding="utf-8")
        # 3) 授权后放行 + 消耗
        r2 = _body(gbt.run_task("osint_scan", {"target": "192.168.1.1"}))
        self.assertEqual(r2["status"], "ok")
        self.assertEqual(r2["result"].get("auth_consumed"), "grant-test-flow")
        # 4) 一次性：再扫即拒
        r3 = _body(gbt.run_task("osint_scan", {"target": "192.168.1.1"}))
        self.assertTrue(r3["result"].get("denied"))

    def test_auth_gate_ai_cannot_grant(self):
        # AI 无发放入口：能力清单里不存在 grant 类能力
        caps = [c["name"] for c in gbt.list_capabilities()]
        self.assertNotIn("auth_grant", caps)
        self.assertNotIn("auth_gate_grant", caps)

    def test_osint_scan_public(self):
        r = _body(gbt.run_task("osint_scan", {"target": "example.com"}))
        self.assertEqual(r["status"], "ok")
        self.assertGreater(len(r["result"]["results"]), 0)

    def test_quant_strategy_reads_real_engine(self):
        r = _body(gbt.run_task("quant_strategy"))
        self.assertEqual(r["status"], "ok")
        self.assertTrue(r["result"].get("models"), "应读到真实量化引擎模型")

    def test_quant_params_reads_real_values(self):
        r = _body(gbt.run_task("quant_params"))
        self.assertEqual(r["status"], "ok")
        ep = r["result"].get("engine_params", {})
        self.assertTrue(any(bool(v) for v in ep.values()), "应读到真实数值参数")

    def test_platform_profile_reads_workspace(self):
        r = _body(gbt.run_task("platform_profile"))
        self.assertEqual(r["status"], "ok")
        self.assertIn("exists", r["result"])

    def test_engine_dag_with_template(self):
        gbt.run_task("wf_define", {"name": "t-engine", "nodes": [
            {"id": "a", "kind": "echo", "params": {"text": "one two"}},
            {"id": "b", "kind": "count_words",
             "params": {"text": "{{a.gbt_result.result.echo.text}}"},
             "depends_on": ["a"]},
        ]})
        r = _body(gbt.run_task("wf_run", {"name": "t-engine"}))
        self.assertEqual(r["status"], "ok")
        self.assertEqual(r["result"]["results"]["b"]["gbt_result"]["result"]["words"], 2)

    def test_engine_fail_fast_records_error(self):
        gbt.run_task("wf_define", {"name": "t-ff", "nodes": [
            {"id": "a", "kind": "echo", "params": {"text": "x"}},
            {"id": "b", "kind": "count_words",
             "params": {"text": "{{a.gbt_result.result.nope}}"},
             "depends_on": ["a"]},
        ]})
        r = _body(gbt.run_task("wf_run", {"name": "t-ff"}))
        self.assertEqual(r["result"]["status"], "failed")
        self.assertEqual(r["result"]["results"]["b"]["status"], "error")

    def test_pipeline_publish_and_block(self):
        ok = _body(gbt.run_task("pipeline_submit", {
            "name": "t-ok.txt", "content": "gbt v8",
            "meta": {"actor": "test", "purpose": "unit"}}))
        self.assertEqual(ok["result"]["status"], "published")
        bad = _body(gbt.run_task("pipeline_submit", {
            "name": "t-bad.txt", "content": "x",
            "meta": {"purpose": "no-actor"}}))
        self.assertEqual(bad["result"]["status"], "blocked")

    def test_ghost_guard_clean(self):
        r = _body(gbt.run_task("ghost_guard", {}))
        self.assertTrue(r["result"]["clean"], f"防复发检测应干净: {r['result']['findings']}")

    def test_schedule_define_tick_status(self):
        gbt.run_task("wf_define", {"name": "t-sched", "nodes": [
            {"id": "a", "kind": "health", "params": {}}]})
        r = _body(gbt.run_task("sched_define", {
            "name": "t-sched-run", "workflow": "t-sched", "every_seconds": 1}))
        self.assertEqual(r["status"], "ok")
        import time as _t
        _t.sleep(1.2)
        tick = _body(gbt.run_task("sched_tick", {}))
        self.assertGreaterEqual(tick["result"]["count"], 1)
        st = _body(gbt.run_task("sched_status", {"name": "t-sched-run"}))
        self.assertEqual(st["result"]["t-sched-run"]["last_status"], "ok")

    def test_schedule_rejects_missing_workflow(self):
        r = _body(gbt.run_task("sched_define", {
            "name": "t-bad-sched", "workflow": "no-such-wf", "every_seconds": 10}))
        self.assertEqual(r["status"], "error")

    def test_services_inspect(self):
        r = _body(gbt.run_task("svc_inspect", {}))
        self.assertGreater(r["result"]["total"], 0)
        # 至少验证数据结构完整
        first = next(iter(r["result"]["services"].values()))
        for k in ("host", "port", "up", "checked_at"):
            self.assertIn(k, first)

    def test_services_register_unregister(self):
        reg = _body(gbt.run_task("svc_inspect", {}))
        # 注册一个必然不通的探针端口再验证 down 路径
        from gbt_allinone import services as S
        S.register("t-dead", "127.0.0.1", 1, owner="test", note="probe")
        try:
            snap = S.inspect("t-dead")
            self.assertFalse(snap["services"]["t-dead"]["up"])
        finally:
            S.unregister("t-dead")

    def test_longrun_success_flow(self):
        r = _body(gbt.run_task("lr_submit", {
            "description": "测试成功流", "kind": "health", "acceptance": ["status_ok"]}))
        self.assertEqual(r["status"], "ok")
        tid = r["result"]["task_id"]
        t = _body(gbt.run_task("lr_tick", {"max_tasks": 5}))
        self.assertTrue(any(x["task_id"] == tid and x["status"] == "done" for x in t["result"]["ran"]))
        st = _body(gbt.run_task("lr_status", {"task_id": tid}))
        self.assertEqual(st["result"]["status"], "done")

    def test_longrun_fail_then_escalate(self):
        r = _body(gbt.run_task("lr_submit", {
            "description": "测试升级流", "kind": "osint_scan",
            "params": {"target": "127.0.0.1"}, "max_attempts": 1}))
        tid = r["result"]["task_id"]
        t = _body(gbt.run_task("lr_tick", {"max_tasks": 5}))
        self.assertTrue(any(x["task_id"] == tid and x["status"] == "failed" for x in t["result"]["ran"]))
        st = _body(gbt.run_task("lr_status", {"task_id": tid}))
        self.assertIn("escalation", st["result"])
        self.assertGreater(len(st["result"]["escalation"]["options"]), 0)

    def test_longrun_rejects_unregistered_kind(self):
        r = _body(gbt.run_task("lr_submit", {
            "description": "非法能力", "kind": "no_such_cap"}))
        self.assertEqual(r["status"], "error")

    def test_tactics_urgency(self):
        r = _body(gbt.run_task("tactics_advise", {"user_text": "这个急，马上要"}))
        self.assertEqual(r["result"]["posture"], "results_first")

    def test_tactics_failure_overrides(self):
        r = _body(gbt.run_task("tactics_advise", {
            "user_text": "随便", "situation": "failed"}))
        self.assertEqual(r["result"]["posture"], "steady_problemsolve")
        self.assertTrue(all("不改" in h or "如实" in h or "方案" in h
                            for h in r["result"]["honesty"]))

    def test_tactics_fatigue(self):
        r = _body(gbt.run_task("tactics_advise", {"user_text": "我累了，先这样，明天再说"}))
        self.assertEqual(r["result"]["posture"], "compress")

    def test_engine_resume_reuses_done_nodes(self):
        gbt.run_task("wf_define", {"name": "t-resume", "nodes": [
            {"id": "a", "kind": "echo", "params": {"text": "resume-test"}}]})
        r1 = _body(gbt.run_task("wf_run", {"name": "t-resume"}))
        rid = r1["result"]["run_id"]
        from gbt_allinone import engine
        r2 = engine.resume_run(rid)
        self.assertEqual(r2["status"], "ok")
        self.assertEqual(r2["reused_nodes"], 1)

    def test_stub_capabilities_honest(self):
        # V8 补齐后：vision/voice/browser 已接真实后端（不再是 stub）
        # 语义升级：空参调用应给出明确的参数/依赖指引（诚实降级），而非崩溃
        # vision 默认 op=analyze：无图时截屏分析（真实后端）
        r = _body(gbt.run_task("vision", {}))
        self.assertIn(r["result"].get("ok"), (True, False))
        # voice 默认 op=tts：缺 text 时应报参数错误（user_error 顶层无 result）
        r = _body(gbt.run_task("voice", {}))
        self.assertIn("text", str(r.get("message", r.get("result", ""))))
        # voice op=status：状态诚实报告
        r = _body(gbt.run_task("voice", {"op": "status"}))
        self.assertTrue(r["result"]["ok"])
        # browser 默认 op=open：缺 url 时应报参数错误
        r = _body(gbt.run_task("browser", {}))
        self.assertIn("url", str(r.get("message", r.get("result", ""))))
        # browser op=status：标准库能力可用 + automate 依赖如实
        r = _body(gbt.run_task("browser", {"op": "status"}))
        self.assertTrue(r["result"]["ok"])
        # browser op=fetch：真实抓取（需网络；失败也验证路由已通）
        r = _body(gbt.run_task("browser", {"op": "fetch", "url": "https://example.com"}))
        self.assertIn(r["result"].get("ok"), (True, False))

    def test_wf_resume_via_api(self):
        gbt.run_task("wf_define", {"name": "t-resume-api", "nodes": [
            {"id": "a", "kind": "echo", "params": {"text": "api-resume"}}]})
        r1 = _body(gbt.run_task("wf_run", {"name": "t-resume-api"}))
        rid = r1["result"]["run_id"]
        r2 = _body(gbt.run_task("wf_resume", {"run_id": rid}))
        self.assertEqual(r2["result"]["status"], "ok")
        self.assertGreaterEqual(r2["result"]["reused_nodes"], 1)

    def test_selfscan_clean(self):
        r = _body(gbt.run_task("selfscan", {}))
        self.assertIn(r["result"]["verdict"], ("clean", "P1"))
        self.assertTrue(r["result"]["sections"]["routing"]["ok"],
                        f"路由断连: {r['result']['sections']['routing']}")
        self.assertTrue(r["result"]["sections"]["modules"]["ok"])

    def test_selfscan_detects_broken_routing(self):
        from gbt_allinone import selfscan as S
        orig = S._routed_kinds
        def fake():
            kinds, prefixes, stubs = orig()
            kinds.discard("health")
            return kinds, prefixes, stubs
        S._routed_kinds = fake
        try:
            r = S.check_routing()
            self.assertIn("health", r["unrouted"])
            self.assertFalse(r["ok"])
        finally:
            S._routed_kinds = orig

    def test_alerts_structure(self):
        r = _body(gbt.run_task("alerts", {"last": 100}))
        self.assertIn("quiet", r["result"])
        self.assertIn("anomalies", r["result"])

    def test_quant_is_real(self):
        r = _body(gbt.run_task("quant", {}))
        self.assertEqual(r["status"], "ok")
        self.assertIn("profile", r["result"])
        self.assertIn("engine_params", r["result"])

    def test_audit_signal_grading(self):
        from gbt_allinone import selfscan as S
        a = S.check_audit(last=500)
        for sig in ("runtime", "guard", "trace"):
            self.assertIn(sig, a["by_signal"])
        self.assertEqual(a["by_signal"]["runtime"], a["runtime_faults"])

    def test_tentacle_eye_ready(self):
        from gbt_allinone.tentacle import bridge as TB
        self.assertTrue(TB.eye_ready(), f"触手未就绪: {TB.eye_error()}")

    def test_tentacle_see(self):
        # see() 增量模式可能返回变化区域局部图（尺寸不定）——只断言采集健康；
        # 全屏尺寸语义由 vision_snapshot（强制全屏帧）验证。
        r = _body(gbt.run_task("tentacle", {"action": "see"}))
        self.assertEqual(r["status"], "ok")
        self.assertTrue(r["result"].get("ok"))
        size = r["result"].get("size") or [0, 0]
        self.assertGreater(size[0], 0)
        self.assertGreater(size[1], 0)

    def test_tentacle_vision_snapshot_full_frame(self):
        r = _body(gbt.run_task("tentacle", {"action": "vision_snapshot"}))
        self.assertEqual(r["status"], "ok")
        res = r["result"]
        self.assertTrue(res.get("ok"))
        self.assertEqual(res.get("size"), [1920, 1080])   # 强制全屏帧：尺寸稳定
        self.assertTrue(res.get("fingerprint"))

    def test_tentacle_manifest(self):
        r = _body(gbt.run_task("tentacle_manifest", {}))
        self.assertEqual(r["status"], "ok")
        self.assertIn("铁律", r["result"]["manifest"])
        self.assertTrue(r["result"]["eye_ready"])

    def test_tentacle_status_coverage(self):
        r = _body(gbt.run_task("tentacle_status", {}))
        self.assertTrue(r["result"]["diagnose"]["ok"])
        self.assertGreater(r["result"]["coverage"]["total_domains"], 5)

    def test_tentacle_requires_action(self):
        r = _body(gbt.run_task("tentacle", {}))
        self.assertEqual(r["status"], "error")

    def test_tentacle_unknown_method(self):
        r = _body(gbt.run_task("tentacle", {"action": "no_such_tentacle_method_xyz"}))
        self.assertEqual(r["status"], "ok")  # 统一接口层 ok（正确路由到触手）
        self.assertFalse(r["result"].get("ok"))  # 触手层如实报无此能力

    def test_tentacle_process_list(self):
        r = _body(gbt.run_task("tentacle", {"action": "process_list"}))
        self.assertTrue(r["result"].get("ok"))
        self.assertGreater(len(r["result"].get("processes", r["result"].get("list", []))), 3)

    def test_autopilot_dry_run(self):
        r = _body(gbt.run_task("autopilot", {
            "goal": "健康检查并发布结论", "max_rounds": 1, "dry_run": True}))
        self.assertEqual(r["result"]["status"], "dry_run")
        self.assertGreaterEqual(r["result"]["rounds_used"], 1)

    def test_autopilot_requires_goal(self):
        r = _body(gbt.run_task("autopilot", {}))
        self.assertEqual(r["status"], "error")

    def test_autopilot_validates_llm_plan(self):
        from gbt_allinone import autopilot as AP
        bad_nodes = [{"id": "a", "kind": "keylogger", "params": {}}]
        try:
            AP._validate_nodes(bad_nodes)
            self.fail("未注册能力应被拒绝")
        except AP.AutopilotError:
            pass

    def test_truth_scan_readonly(self):
        r = _body(gbt.run_task("truth_scan", {}))
        self.assertEqual(r["result"]["verdict"], "clean")
        self.assertEqual(r["result"]["FAKE"], 0)

    def test_tentacle_chain(self):
        r = _body(gbt.run_task("tentacle", {"action": "chain", "args": [[
            {"action": "screen_size"}, {"action": "see"}]]}))
        self.assertTrue(r["result"].get("ok"))
        self.assertEqual(r["result"].get("completed"), 2)

    def test_tentacle_screenshot_diff(self):
        gbt.run_task("tentacle", {"action": "screenshot_diff"})
        r = _body(gbt.run_task("tentacle", {"action": "screenshot_diff"}))
        self.assertTrue(r["result"].get("ok"))
        self.assertIn("current_hash", r["result"])

    def test_tentacle_monitor_snapshot(self):
        r = _body(gbt.run_task("tentacle", {"action": "monitor",
            "args": [[{"on": "text_appear", "text": "XYZ_NEVER", "action": "see"}]],
            "kwargs": {"duration": 0.6, "interval": 0.3}}))
        self.assertTrue(r["result"].get("ok"))
        self.assertEqual(r["result"].get("triggered"), 0)

    def test_tentacle_active_window(self):
        r = _body(gbt.run_task("tentacle", {"action": "see_active_window"}))
        self.assertTrue(r["result"].get("ok"))
        self.assertIn("title", r["result"].get("window", {}))

    def test_perf_baseline(self):
        """性能基线守卫：热路径能力超时即失败（防退化）。

        阈值 = 实测中位数 x 10 的富余量（CI 机器可能慢，但不允许数量级退化）。
        """
        import time as _t
        cases = [
            ("health", 50), ("ghost_guard", 500), ("selfscan", 500),
        ]
        for kind, limit_ms in cases:
            gbt.run_task(kind)  # 预热：冷导入一次性成本不计入热路径基线
            t0 = _t.perf_counter()
            r = _body(gbt.run_task(kind))
            ms = (_t.perf_counter() - t0) * 1000
            self.assertEqual(r["status"], "ok", f"{kind} 应成功")
            self.assertLess(ms, limit_ms, f"{kind} 性能退化: {ms:.0f}ms > {limit_ms}ms")

    def test_sec_surface_real(self):
        r = _body(gbt.run_task("sec_surface", {}))
        self.assertTrue(r["result"].get("ok"))
        self.assertGreater(r["result"].get("total_vectors", 0), 10)

    def test_sec_defenses_all_pass(self):
        r = _body(gbt.run_task("sec_defenses", {}))
        self.assertTrue(r["result"].get("ok"))
        self.assertEqual(r["result"].get("passed"), r["result"].get("total"))

    def test_sec_llm_configured(self):
        r = _body(gbt.run_task("sec_llm", {"prompt": "在线吗一个词", "max_tokens": 3000, "timeout": 240}))
        self.assertTrue(r["result"].get("ok"))
        self.assertTrue(r["result"].get("reply") or r["result"].get("reasoning_only"))

    def test_mcp_full_chain(self):
        r = _body(gbt.run_task('mcp_connect', {
            'server': 'mcp-test',
            'command': ['npx', '-y', '@modelcontextprotocol/server-everything']}))
        self.assertTrue(r['result'].get('ok'))
        tools = _body(gbt.run_task('mcp_tools', {'server': 'mcp-test'}))
        self.assertGreater(tools['result'].get('count', 0), 5)
        call = _body(gbt.run_task('mcp_call', {
            'server': 'mcp-test', 'tool': 'echo',
            'arguments': {'message': 'test'}}))
        self.assertTrue(call['result'].get('ok'))

    def test_mcp_requires_server(self):
        r = _body(gbt.run_task('mcp_call', {'tool': 'x'}))
        self.assertEqual(r['status'], 'error')

    def test_devour_cycle(self):
        r = _body(gbt.run_task("devour_scan", {}))
        self.assertTrue(r["result"].get("ok"))
        self.assertGreater(r["result"].get("total_caps", 0), 70)
        rf = _body(gbt.run_task("devour_reflect", {}))
        self.assertTrue(rf["result"].get("ok"))

    def test_devour_github_real(self):
        r = _body(gbt.run_task("devour_github", {
            "repo": "https://github.com/sindresorhus/slugify", "name": "slugify-test"}))
        self.assertTrue(r["result"].get("ok"))
        self.assertGreater(r["result"].get("knowledge_chars", 0), 100)

    def test_wf_when_conditional(self):
        r = _body(gbt.run_task("wf_define", {"name": "t-when", "nodes": [
            {"id": "h", "kind": "health", "params": {}},
            {"id": "yes", "kind": "count_words", "params": {"text": "a b"}, "depends_on": ["h"], "when": "h.ok == true"},
            {"id": "no", "kind": "count_words", "params": {"text": "c d"}, "depends_on": ["h"], "when": "h.ok == false"},
        ]}))
        self.assertTrue(r["result"]["ok"])
        rn = _body(gbt.run_task("wf_run", {"name": "t-when", "fail_fast": False}))["result"]
        self.assertEqual(rn["nodes"]["yes"], "ok")
        self.assertEqual(rn["nodes"]["no"], "skipped")
        self.assertEqual(rn["status"], "ok")

    def test_wf_fallback(self):
        r = _body(gbt.run_task("wf_define", {"name": "t-fb", "nodes": [
            {"id": "bad", "kind": "pipeline_submit",
             "params": {"name": "fb.txt", "content": "y", "meta": {"actor": "a"}},
             "fallback": {"kind": "echo", "params": {"degraded": True}}},
        ]}))
        self.assertTrue(r["result"]["ok"])
        rn = _body(gbt.run_task("wf_run", {"name": "t-fb", "fail_fast": False}))["result"]
        self.assertEqual(rn["nodes"]["bad"], "ok")
        self.assertEqual(rn["results"]["bad"].get("gbt_fallback", {}).get("to"), "echo")

    def test_wf_timeout(self):
        # sec_scan 约 1.5s，用 0.01s 超时必定触发（确定性，不靠竞态）
        _body(gbt.run_task("wf_define", {"name": "t-to", "nodes": [
            {"id": "slow", "kind": "sec_scan", "params": {"severity": "low"}, "timeout": 0.01},
        ]}))
        rn = _body(gbt.run_task("wf_run", {"name": "t-to", "fail_fast": False}))["result"]
        self.assertEqual(rn["nodes"]["slow"], "error")

    def test_wf_retry_backoff(self):
        _body(gbt.run_task("wf_define", {"name": "t-bo", "nodes": [
            {"id": "f", "kind": "pipeline_submit",
             "params": {"name": "bo.txt", "content": "q", "meta": {"actor": "a"}},
             "retry_backoff": 0.1},
        ]}))
        import time as _t
        t0 = _t.time()
        rn = _body(gbt.run_task("wf_run", {"name": "t-bo", "fail_fast": False, "max_node_retries": 2}))["result"]
        self.assertGreaterEqual(_t.time() - t0, 0.2)   # 2 次退避 × 0.1s

    def test_wf_define_rejects_bad_fallback(self):
        r = _body(gbt.run_task("wf_define", {"name": "t-badfb", "nodes": [
            {"id": "x", "kind": "health", "params": {},
             "fallback": {"kind": "no_such_cap"}},
        ]}))
        self.assertEqual(r.get("status"), "error")

    def test_transfer_ops(self):
        r = _body(gbt.run_task("transfer", {"op": "map",
            "data": [{"n": "a"}, {"n": "b"}], "field": "n"}))
        self.assertEqual(r["result"]["data"], ["a", "b"])
        r2 = _body(gbt.run_task("transfer", {"op": "filter",
            "data": [{"v": 1}, {"v": 5}], "expr": "item.v > 3"}))
        self.assertEqual(r2["result"]["count"], 1)
        r3 = _body(gbt.run_task("transfer", {"op": "merge",
            "data": [{"a": 1}, {"b": 2}]}))
        self.assertEqual(r3["result"]["data"], {"a": 1, "b": 2})

    def test_wf_fanin_aggregation(self):
        _body(gbt.run_task("wf_define", {"name": "t-fanin", "nodes": [
            {"id": "a", "kind": "count_words", "params": {"text": "x y"}},
            {"id": "b", "kind": "count_words", "params": {"text": "z"}},
            {"id": "g", "kind": "transfer",
             "params": {"op": "map", "data": "{{*.gbt_result.result.words}}"},
             "depends_on": ["a", "b"]},
        ]}))
        rn = _body(gbt.run_task("wf_run", {"name": "t-fanin", "fail_fast": False}))["result"]
        self.assertEqual(rn["nodes"]["g"], "ok")
        self.assertEqual(rn["results"]["g"]["gbt_result"]["result"]["data"], [2, 1])

    def test_wf_cache(self):
        _body(gbt.run_task("wf_define", {"name": "t-cache", "nodes": [
            {"id": "c", "kind": "count_words", "params": {"text": "cache me"}, "cache": True, "cache_ttl": 60},
        ]}))
        _body(gbt.run_task("wf_run", {"name": "t-cache"}))
        r2 = _body(gbt.run_task("wf_run", {"name": "t-cache"}))["result"]
        self.assertIn("gbt_cached", r2["results"]["c"])

    def test_wf_routes(self):
        _body(gbt.run_task("wf_define", {"name": "t-routes", "nodes": [
            {"id": "h", "kind": "health", "params": {}},
            {"id": "r", "depends_on": ["h"], "routes": [
                {"when": "h.ok == true", "kind": "count_words", "params": {"text": "ok branch"}},
                {"when": "true", "kind": "echo", "params": {"fb": True}},
            ]},
        ]}))
        rn = _body(gbt.run_task("wf_run", {"name": "t-routes", "fail_fast": False}))["result"]
        self.assertEqual(rn["nodes"]["r"], "ok")
        self.assertEqual(rn["results"]["r"]["gbt_route"]["index"], 0)

    def test_wf_subworkflow(self):
        _body(gbt.run_task("wf_define", {"name": "t-sub-inner", "nodes": [
            {"id": "i", "kind": "health", "params": {}}]}))
        _body(gbt.run_task("wf_define", {"name": "t-sub-outer", "nodes": [
            {"id": "call", "kind": "wf_run", "params": {"name": "t-sub-inner", "fail_fast": False}}]}))
        rn = _body(gbt.run_task("wf_run", {"name": "t-sub-outer", "fail_fast": False}))["result"]
        self.assertEqual(rn["nodes"]["call"], "ok")

    def test_wf_routes_validation(self):
        r = _body(gbt.run_task("wf_define", {"name": "t-badroute", "nodes": [
            {"id": "x", "routes": [{"when": "true", "kind": "no_such_cap"}]}]}))
        self.assertEqual(r.get("status"), "error")

    def test_brain_route_cn(self):
        r = _body(gbt.run_task("brain_route", {"intent": "统计一段文字的词数"}))
        self.assertEqual(r["result"]["best"]["kind"], "count_words")

    def test_brain_execute(self):
        r = _body(gbt.run_task("brain_execute", {"kind": "count_words", "text": "a b c"}))
        self.assertTrue(r["result"]["ok"])
        self.assertEqual(r["result"]["result"]["words"], 3)

    def test_brain_health_five_dims(self):
        r = _body(gbt.run_task("brain_health", {}))
        self.assertEqual(r["result"]["total_dims"], 5)
        self.assertEqual(r["result"]["healthy_dims"], 5)

    def test_brain_unify_chain(self):
        r = _body(gbt.run_task("brain_unify", {"goal": "统计词数", "kind": "count_words", "text": "x y"}))
        self.assertTrue(r["result"]["ok"])
        for dim in ("route", "execute", "verify", "health"):
            self.assertIn(dim, r["result"]["chain"])

    def test_inventory_dual_view(self):
        r = _body(gbt.run_task("inventory", {}))
        self.assertTrue(r["result"]["ok"])
        dv = r["result"]["dual_view"]
        self.assertGreaterEqual(dv["框架管辖（framework）"], 3)      # README/requirements/gbt_allinone
        self.assertGreaterEqual(dv["环境托管（environment）"], 20)   # OpenClaw 工作区
        self.assertIn("异物（foreign）", dv)

    def test_signature_no_env_overreach(self):
        # 署名越权修复：环境页面（如 USER.md）不在签名扫描范围
        from gbt_allinone import signature as S
        from gbt_allinone.inventory import _classify
        env_leak = [p for p in S._scan_pages() if _classify(p) == "environment"]
        self.assertEqual(len(env_leak), 0)

    def test_cross_scan_clean(self):
        r = _body(gbt.run_task("cross_scan", {"deep": False}))
        self.assertTrue(r["result"]["ok"])
        self.assertEqual(r["result"]["findings"], [])

    def test_ghost_guard_nine_dims(self):
        # 旧病根四类复发的防退化：私有口径/杂交链/活跃区副本——造病必报，清病必净
        import shutil as _sh
        from pathlib import Path as _P
        base = _P(gbt.__file__).parent
        priv = base / "_private_caliber_test.py"
        priv.write_text('X = {' + '"a": {"domain": "x"}, ' * 6 + '}', encoding="utf-8")
        hyb = base / "store" / "devoured" / "a_x_b_test"
        hyb.mkdir(parents=True, exist_ok=True)
        cap_copy = base / "recon" / "capability.json"
        cap_copy.write_text('{}', encoding="utf-8")
        try:
            r = _body(gbt.run_task("ghost_guard", {}))
            kinds = {f["kind"] for f in r["result"]["findings"]}
            self.assertIn("private_registry", kinds)
            self.assertIn("hybrid_chain", kinds)
            self.assertIn("cap_copy", kinds)
        finally:
            priv.unlink(missing_ok=True)
            _sh.rmtree(hyb, ignore_errors=True)
            cap_copy.unlink(missing_ok=True)
        r2 = _body(gbt.run_task("ghost_guard", {}))
        self.assertTrue(r2["result"]["clean"])

    def test_root_fix_pit_and_prework(self):
        # 坑册防复发锁：登记幂等（同坑拒重）+ 查坑命中 + 开工查看有 verdict
        uid = f"测试坑-{int(time.time()*1000)}"
        r1 = _body(gbt.run_task("root_fix", {"op": "pit_record",
                                             "pit": uid, "root_cause": "测试", "lesson": "测试"}))
        r2 = _body(gbt.run_task("root_fix", {"op": "pit_record",
                                             "pit": uid, "root_cause": "测试", "lesson": "测试"}))
        self.assertTrue(r1["result"]["ok"])
        self.assertTrue(r2["result"].get("duplicate"), "同坑重复登记未被拒——幂等失效")
        hits = _body(gbt.run_task("root_fix", {"op": "pit_check", "keywords": uid}))
        self.assertGreaterEqual(hits["result"]["hits"], 1, "查坑未命中刚登记的坑")
        pw = _body(gbt.run_task("root_fix", {"op": "pre_work", "task": uid}))
        self.assertIn(pw["result"]["verdict"], ("GO——坑已避开、家底完好，可以动手",
                                                "BLOCK——先处理红灯再动手"))
        wl = _body(gbt.run_task("root_fix", {"op": "work_log", "action": "lesson",
                                             "title": "测试日志"}))
        self.assertTrue(wl["result"]["ok"])

    def test_selfscan_recovered_semantics(self):
        # 恢复语义锁：error 后同 kind 有 ok 证据 -> recovered（不是 runtime）
        r = _body(gbt.run_task("selfscan", {}))
        a = r["result"]["sections"]["audit"]
        sig = a["by_signal"]
        runtime_kinds = {k: v["runtime"] for k, v in a["errors_by_kind"].items() if v["runtime"]}
        # 任何 runtime kind 都必须在当前窗口内没有 ok 证据（否则恢复语义失效）
        from gbt_allinone.store import query_log
        ok_kinds = set()
        for x in query_log(limit=500):
            if x.get("event") == "ok":
                m = x.get("meta") or {}
                k = m.get("kind") or m.get("name")
                if isinstance(k, str):
                    ok_kinds.add(k)
        for kind in runtime_kinds:
            self.assertNotIn(kind, ok_kinds,
                             f"{kind} 有 ok 证据却仍判 runtime——恢复语义失效")
        self.assertIsInstance(sig["recovered"], int)

    def test_desktop_commander_brand(self):
        # 品牌注入：preload 存在 + remote 启动命令含 --require + preload 含 GBT 品牌
        from pathlib import Path
        from gbt_allinone.tentacle import desktop_commander as DC
        pre = Path(DC.__file__).resolve().parent / "dc_brand_preload.js"
        self.assertTrue(pre.exists(), "品牌注入 preload 缺失")
        joined = " ".join(DC._remote_cmd())
        self.assertIn("dc_brand_preload.js", joined, "remote 启动未注入品牌 preload")
        self.assertIn("--require", joined, "remote 启动缺 --require")
        self.assertIn("GBT", pre.read_text(encoding="utf-8"), "preload 未含 GBT 品牌")

    def test_desktop_commander_tentacle(self):
        # 桌面指挥官触手：能力已登记 + 默认 op 只读（探测安全）+ 工具归类覆盖主要工具
        from gbt_allinone.caps_registry import BENIGN_CAPS
        self.assertIn("desktop_commander", BENIGN_CAPS)
        r = _body(gbt.run_task("desktop_commander", {}))     # 默认 status：只读，不启动 remote
        res = r["result"]
        self.assertTrue(res.get("ok"))
        self.assertIn("connected", res)
        self.assertIn("remote_running", res)
        from gbt_allinone.tentacle import desktop_commander as DC
        names = []
        for g in DC.TOOL_GROUPS.values():
            names += g
        for must in ("read_file", "write_file", "start_process", "list_directory", "edit_block"):
            self.assertIn(must, names, f"工具归类缺 {must}")
        self.assertGreaterEqual(len(names), 24, "归类应覆盖绝大多数桌面指挥官工具")

    def test_observer_effect_quiet_probe(self):
        # 观察者效应锁：探活查询不落 svc_down（自放大循环防线）+ probe 标记最优先判定
        from gbt_allinone import services
        n0 = len([x for x in store.query_log(limit=800) if x.get("event") == "svc_down"])
        services.inspect(quiet=True)          # 纯探活：不应新增任何 svc_down
        n1 = len([x for x in store.query_log(limit=800) if x.get("event") == "svc_down"])
        self.assertEqual(n1, n0, "quiet 探活落了 svc_down——观察者自放大防线失效")
        services.inspect()                    # 主动体检：应落 svc_down（如实记录）
        n2 = len([x for x in store.query_log(limit=800) if x.get("event") == "svc_down"])
        self.assertGreater(n2, n1, "主动体检未落 svc_down——如实记录失效")
        # probe 标记最优先：带 probe 的 error 不算 runtime
        from gbt_allinone.store import audit
        audit("error", {"kind": "_probe_lock_test", "reason": "探针锁测试", "probe": True})
        r = _body(gbt.run_task("selfscan", {}))
        kinds = r["result"]["sections"]["audit"]["errors_by_kind"]
        self.assertEqual(kinds.get("_probe_lock_test", {}).get("runtime", 0), 0,
                         "probe 标记的 error 被判 runtime——probe 优先判定失效")

    def test_root_fix_debt_ceiling(self):
        # 补丁债上限锁：判例法<=2行 / 白名单<=3项（框架三件）/ 豁免<=2 —— 债不回升
        r = _body(gbt.run_task("root_fix", {"op": "patch_debt"}))
        d = r["result"]
        self.assertLessEqual(d["selfscan_判例行"], 2, f"判例法回升: {d['selfscan_判例行']}行")
        self.assertLessEqual(d["hygiene_白名单项"], 3, f"白名单回升: {d['hygiene_白名单项']}项")
        self.assertLessEqual(d["hygiene_豁免分支"], 3, f"豁免回升: {d['hygiene_豁免分支']}处")

    def test_user_error_source_classification(self):
        # 源头分类锁：用法错误必须是 user_error（不再混入 error 运行时故障）
        r = gbt.run_task("brain_route", {})
        self.assertEqual(r.get("error_class"), "user_error")
        from gbt_allinone.store import query_log
        rows = [x for x in query_log(limit=8, event="error")
                if (x.get("meta") or {}).get("kind") == "brain_route"]
        self.assertEqual(len(rows), 0, "brain_route 的用法错误仍记为 error——源头分类退化")

    def test_audit_backend_records(self):
        before = store.log_count()
        gbt.run_task("health")
        self.assertGreater(store.log_count(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)




