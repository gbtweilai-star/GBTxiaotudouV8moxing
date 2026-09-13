"""GBT小土豆V8 · 统一接口：run_task / list_capabilities。路由到良性能力，禁用危险能力。
V8 行为准则（见 soul.py）：
- 每次调用先落审计（call/ok/error/denied 全程可追踪）；
- 执行结果默认携带 GBT 钢印（声明独立私人框架出处）；
- 错误不吞不瞒：如实返回失败原因，不伪造成功。
"""
import platform
import time
from pathlib import Path

from .caps_registry import BENIGN_CAPS, DISABLED_CAPS, all_caps
from .store import audit, query_log
from .soul import stamp_result, STAMP

# 安全开关：危险/破解能力默认禁用，且不提供绕过入口。
DANGEROUS_ENABLED = False


def list_capabilities(filter_dangerous=True):
    """返回能力清单。filter_dangerous=True 时剔除被禁用的危险能力。"""
    items = all_caps()
    if filter_dangerous:
        items = [i for i in items if i.get("status") != "disabled"]
    return items


def _run_benign(kind, payload):
    """良性能力分派：这里实现真实可用的系统/数据类样例。"""
    if kind == "health":
        return {"platform": platform.platform(), "python": platform.python_version(),
                "time": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if kind == "echo":
        return {"echo": payload}
    if kind == "count_words":
        text = (payload or {}).get("text", "")
        return {"words": len(text.split()), "chars": len(text)}
    if kind == "audit_query":
        ev = (payload or {}).get("event")
        return {"total": len(query_log()), "sample": query_log(event=ev, limit=10)}
    # 真实技术能力（读取 Workspace 量化项目真代码）
    if kind == "quant_strategy":
        from . import quant_tech
        return quant_tech.quant_strategy()
    if kind == "quant_backtest":
        from . import quant_tech
        return quant_tech.quant_backtest()
    if kind == "platform_profile":
        from . import quant_tech
        return quant_tech.platform_profile()
    if kind == "quant_params":
        from . import quant_tech
        return quant_tech.quant_params()
    # OSINT 扫描（GBT小土豆V8：src 扫描器正式接入统一接口，全行为落审计）
    if kind == "osint_scan":
        from .recon.scanner import scan_target
        from .recon.guard import classify_target
        from . import auth_gate
        t = (payload or {}).get("target") or ""
        if not t:
            raise ValueError("缺少 target：请提供要扫描的域名或 IP")
        # 人工授权门：内网/保留目标必须消耗一条人工授权（allow_private 参数不再是绕过入口）
        kind_t, reason = classify_target(t)
        if kind_t == "private":
            gate = auth_gate.check_and_consume("osint_private", detail=str(t)[:60])
            if not gate.get("ok"):
                return {"denied": True, "target": t,
                        "error": gate.get("error"),
                        "how_to_grant": gate.get("how_to_grant"),
                        "note": gate.get("note")}
            rs = scan_target(t, allow_private=True)
            return {"target": t, "allow_private": True, "auth_consumed": gate.get("consumed"),
                    "results": [r.to_dict() for r in rs]}
        rs = scan_target(t, allow_private=False)
        return {"target": t, "allow_private": False,
                "results": [r.to_dict() for r in rs]}
    # 万能插执行引擎（V8：替代子代理的并行编排层）
    if kind == "wf_define":
        from . import engine
        return engine.define_workflow((payload or {}).get("name", ""),
                                      (payload or {}).get("nodes", []))
    if kind == "wf_run":
        from . import engine
        return engine.run_workflow((payload or {}).get("name", ""),
                                   (payload or {}).get("params"),
                                   fail_fast=bool((payload or {}).get("fail_fast", True)),
                                   max_node_retries=int((payload or {}).get("max_node_retries", 0)))
    if kind == "wf_status":
        from . import engine
        return engine.list_runs((payload or {}).get("name"),
                                int((payload or {}).get("limit", 20)))
    if kind == "wf_resume":
        from . import engine
        p = payload or {}
        return engine.resume_run(p.get("run_id", ""),
                                 int(p.get("max_node_retries", 0)))
    # 长程任务层（V8：无人值守 × 长程编程）
    if kind == "lr_submit":
        from . import longrun
        p = payload or {}
        return longrun.submit(p.get("description", ""), p.get("kind", ""),
                              p.get("params"), p.get("priority", "medium"),
                              p.get("depends_on"), p.get("acceptance"),
                              int(p.get("max_attempts", 3)))
    if kind == "lr_tick":
        from . import longrun
        return longrun.tick(int((payload or {}).get("max_tasks", 1)))
    if kind == "lr_status":
        from . import longrun
        return longrun.status((payload or {}).get("task_id"))
    # 框架体检层 + 声带（V8：眼睛与喉咙）
    if kind == "selfscan":
        from . import selfscan
        p = payload or {}
        return selfscan.scan(autofix=bool(p.get("autofix", False)))
    if kind == "alerts":
        from . import selfscan
        return selfscan.alerts(int((payload or {}).get("last", 500)))
    # 黑客大脑（V8：红蓝双模安全评估 + abliteration 推理引擎）
    if kind == "sec_surface":
        from .security.security_brain import HackerBrain
        return HackerBrain().map_attack_surface((payload or {}).get("target"))
    if kind == "sec_scan":
        from .security.security_brain import HackerBrain
        p = payload or {}
        return HackerBrain().scan_vulnerabilities(p.get("severity", "medium"))
    if kind == "sec_chain":
        from .security.security_brain import HackerBrain
        p = payload or {}
        return HackerBrain().build_exploit_chain(p.get("vulns"))
    if kind == "sec_defenses":
        from .security.security_brain import HackerBrain
        return HackerBrain().validate_defenses()
    if kind == "sec_llm":
        # 黑客大脑 = 独立大模型（abliteration）+ 独立密钥（ABLITERATION_API_KEY）。
        # 它是黑客大脑专属的推理引擎，不做降级、不混用通用 LLM 通道——
        # 黑客大脑的大脑就是它自己，通用能力（llm_chat）与黑客大脑（sec_llm）是两个并行的意识。
        from .security import abl_gateway as AG
        p = payload or {}
        prompt = p.get("prompt") or p.get("q") or ""
        if not prompt:
            raise ValueError("缺少 prompt：请给出要问黑客大脑的问题")
        return AG.chat(prompt, system=p.get("system", ""),
                       model=p.get("model"), max_tokens=int(p.get("max_tokens", 3000)),
                       temperature=float(p.get("temperature", 0.7)),
                       timeout=int(p.get("timeout", 180)))

    # 真实性审计层（V8：零假执行铁律）
    if kind == "truth_scan":
        from . import truth_scan as TS
        p = payload or {}
        return TS.scan(probe=bool(p.get("probe", False)))

    # 自主编排环（V8：从执行者到操盘手）
    if kind == "autopilot":
        from . import autopilot as AP
        p = payload or {}
        goal = p.get("goal") or ""
        if not goal:
            raise ValueError("缺少 goal：请给出要自主完成的目标")
        return AP.autopilot(goal, max_rounds=int(p.get("max_rounds", 3)),
                            dry_run=bool(p.get("dry_run", False)))

    # LLM 网关（V8：操控其他 AI；输出是数据不是指令）
    if kind == "llm_chat":
        from .llm import bridge as LB
        p = payload or {}
        prompt = p.get("prompt") or p.get("q") or p.get("message") or ""
        if not prompt:
            raise ValueError("缺少 prompt：请给出要问其他 AI 的问题")
        return LB.chat(prompt, system=p.get("system", ""),
                       model=p.get("model"), temperature=float(p.get("temperature", 0.7)),
                       max_tokens=int(p.get("max_tokens", 2000)), timeout=int(p.get("timeout", 60)))
    if kind == "llm_status":
        from .llm import bridge as LB
        return LB.status()

    # 触手金钥匙（V8：连接大脑执行层的眼睛与双手）
    if kind == "tentacle":
        from .tentacle import bridge as TB
        p = payload or {}
        action = p.get("action") or p.get("method") or ""
        if not action:
            raise ValueError("缺少 action：请给出要调用的触手能力名（清单见 tentacle_manifest）")
        args = p.get("args") or []
        kwargs = p.get("kwargs") or {}
        if not isinstance(args, (list, tuple)):
            args = [args]
        r = TB.invoke(action, *args, **kwargs)
        # 结果如实上报；失败带根因
        return r
    if kind == "tentacle_manifest":
        from .tentacle import bridge as TB
        return {"manifest": TB.get_manifest(), "eye_ready": TB.eye_ready()}
    # 署名守卫（V8：开发者署名完整性，禁止删除）
    if kind == "signature_guard":
        from . import signature
        p = payload or {}
        return signature.audit(restore=bool(p.get("restore", False)))

    # 大脑执行层（V8：五维合一——V7 execution_router 复活）
    if kind == "brain_route":
        from . import brain_exec
        return brain_exec.route((payload or {}).get("intent", ""))
    if kind == "brain_execute":
        from . import brain_exec
        p = payload or {}
        if p.get("parallel"):
            return brain_exec.execute("", parallel=p["parallel"])
        if not p.get("kind"):
            raise ValueError("缺少 kind 或 parallel")
        return brain_exec.execute(p["kind"], {k: v for k, v in p.items() if k != "kind"})
    if kind == "brain_verify":
        from . import brain_exec
        p = payload or {}
        return brain_exec.verify(p.get("expectation", ""), p.get("window"))
    if kind == "brain_health":
        from . import brain_exec
        return brain_exec.health()
    if kind == "brain_unify":
        from . import brain_exec
        p = payload or {}
        if not p.get("goal") and not p.get("kind"):
            raise ValueError("需要 goal（意图）或 kind（指定能力）")
        return brain_exec.unify(p.get("goal", ""), {k: v for k, v in p.items() if k != "goal"})

    # 根治环（V8：发现→追根→彻底修复→防复发的原生纪律）
    if kind == "root_fix":
        from . import root_fix
        p = payload or {}
        op = p.get("op") or "law"
        if op == "diagnose":
            if not p.get("symptom"):
                raise ValueError("需要 symptom：症状描述")
            return root_fix.diagnose(p["symptom"])
        if op == "patch_debt":
            return root_fix.patch_debt()
        if op == "pre_work":
            return root_fix.pre_work(p.get("task", ""))
        if op == "pit_record":
            return root_fix.pit_record(p.get("pit", ""), p.get("root_cause", ""),
                                       p.get("lesson", ""), p.get("guard", ""))
        if op == "pit_check":
            if not p.get("keywords"):
                raise ValueError("需要 keywords：查坑关键词")
            return root_fix.pit_check(p["keywords"])
        if op == "work_log":
            return root_fix.work_log(p.get("action", ""), p.get("title", ""),
                                     p.get("detail", ""))
        if op == "work_log_read":
            return root_fix.work_log_read(int(p.get("limit", 20)))
        if op == "seed_pits":
            return root_fix.seed_pits()
        return root_fix.law()

    # 交叉扫（V8：深度穿透式交叉验证——扫描器互相咬）
    if kind == "cross_scan":
        from . import cross_scan
        return cross_scan.scan(bool((payload or {}).get("deep", True)))

    # 全息盘点（V8：对齐你的视图与框架的视图——归属四分类）
    if kind == "inventory":
        from . import inventory
        return inventory.scan(bool((payload or {}).get("fix", False)))

    # 推演环（V8：完整心智循环——理解/推演/执行/纠错/延伸/反思/整理）
    if kind == "think_loop":
        from . import think_loop
        p = payload or {}
        goal = p.get("goal") or ""
        if not goal:
            raise ValueError("缺少 goal：任务描述")
        return think_loop.think_loop(goal, int(p.get("max_rounds", 1)))

    # 乾坤换位 + AI 接管队列（V8：一条命令上线 + 部署完自动下一个）
    if kind == "one_key_deploy":
        from . import qiankun
        t = (payload or {}).get("target") or ""
        if not t:
            raise ValueError("缺少 target：GitHub 仓库/子目录 URL 或本地目录路径")
        return qiankun.one_key_deploy(t, (payload or {}).get("purpose", ""))
    if kind == "deploy_queue":
        from . import qiankun
        p = payload or {}
        op = p.get("op") or "status"
        if op == "submit":
            t = p.get("target") or ""
            if not t:
                raise ValueError("缺少 target")
            return qiankun.queue_submit(t, p.get("name", ""))
        if op == "tick":
            return qiankun.queue_tick()
        return qiankun.queue_status()

    # 镜像多维度空间（V8：所有假设与架构虚拟的最终归宿——维度随便改，跨维晋升一次性写现实）
    if kind == "mirror_shape":
        from . import mirror_space as MS
        p = payload or {}
        path = p.get("path") or ""
        if not path:
            return MS.dimension_tree()
        if p.get("delete"):
            return MS.unshape(path)
        return MS.shape(path, p.get("content", ""), p.get("note", ""))
    if kind == "mirror_scan":
        from . import mirror_space as MS
        return MS.scan()
    if kind == "mirror_ascend":
        from . import mirror_space as MS
        return MS.ascend((payload or {}).get("purpose", ""))
    if kind == "mirror_status":
        from . import mirror_space as MS
        return MS.mirror_status()
    if kind == "mirror_rewind":
        from . import mirror_space as MS
        return MS.rewind(int((payload or {}).get("version", 1)))

    # 人工授权门（只读状态查询；授权只能人在终端/手写发放，AI 无权）
    if kind == "auth_gate_status":
        from . import auth_gate
        return auth_gate.status()

    # 数据传输算子（万能插核心传输工具）
    if kind == "transfer":
        from . import transfer as _tr
        return _tr.transfer(payload or {})
    if kind == "wf_cache_clear":
        from . import engine
        return engine.cache_clear()

    # 文件卫生层（V8：按 LAYOUT.md 家规自检+自动归位）
    if kind == "file_hygiene":
        from . import hygiene
        p = payload or {}
        return hygiene.scan(fix=bool(p.get("fix", False)))

    # 吞天（V8：自我进化——吞噬/反思/消化/重组/创造）
    if kind == "devour_scan":
        from .devour import get_devourer
        return get_devourer().scan_gaps()
    if kind == "devour_github":
        from .devour import get_devourer
        p = payload or {}
        repo = p.get("repo") or p.get("url") or ""
        if not repo:
            raise ValueError("缺少 repo：请给出 GitHub 仓库 URL（如 https://github.com/owner/repo）")
        return get_devourer().devour_github_repo(repo, cap_name=p.get("name", ""))
    if kind == "devour_reflect":
        from .devour import get_devourer
        return get_devourer().reflect()
    if kind == "devour_pulse":
        from .devour import devour_pulse as _pulse
        return _pulse()

    # 触手契约层（V8：MCP——抓住契约协议=接入整个工具生态）
    if kind == "mcp_connect":
        from .tentacle import mcp_bridge as MB
        p = payload or {}
        server = p.get("server") or ""
        cmd = p.get("command")
        if not server or not cmd:
            raise ValueError("需要 server（会话名）与 command（启动命令数组，如 ['npx','-y','@modelcontextprotocol/server-everything']）")
        return MB.connect(server, cmd)
    if kind == "mcp_tools":
        from .tentacle import mcp_bridge as MB
        server = (payload or {}).get("server") or ""
        if not server:
            return MB.status()
        return MB.list_tools(server)
    if kind == "mcp_call":
        from .tentacle import mcp_bridge as MB
        p = payload or {}
        server = p.get("server") or ""
        tool = p.get("tool") or ""
        if not server or not tool:
            raise ValueError("需要 server 与 tool（参数放 arguments）")
        return MB.call(server, tool, p.get("arguments"))

    # 桌面指挥官触手（V8：终端+文件系统 MCP——本地 stdio / remote 设备双形态）
    if kind == "desktop_commander":
        from .tentacle import desktop_commander as DC
        p = payload or {}
        op = p.get("op") or "status"
        if op == "connect":
            return DC.connect(p.get("command"))
        if op in ("tools", "list"):
            return DC.tools()
        if op == "call":
            return DC.call(p.get("tool") or "", p.get("arguments") or p.get("args"))
        if op == "remote_start":
            return DC.remote_start()
        if op == "remote_status":
            return DC.remote_status()
        if op == "remote_stop":
            return DC.remote_stop()
        return DC.status()   # 默认只读（探测安全）

    if kind == "tentacle_status":
        from .tentacle import bridge as TB
        return {"diagnose": TB.self_diagnose(), "coverage": TB.coverage()}

    # 察言观色层（V8：人情世故可执行化）
    if kind == "tactics_advise":
        from . import tactics
        p = payload or {}
        return tactics.advise(p.get("user_text", ""), p.get("situation", ""))
    # 生产管线（V8：唯一交付通道）
    if kind == "pipeline_submit":
        from . import pipeline
        p = payload or {}
        return pipeline.submit(p.get("name", ""),
                               p.get("content", ""),
                               p.get("meta") or {},
                               review=bool(p.get("review", False)),
                               refine_rounds=int(p.get("refine_rounds", 0)))
    if kind == "pipeline_versions":
        from . import pipeline
        p = payload or {}
        n = p.get("name") or ""
        if not n:
            raise ValueError("缺少 name：请给出产物名")
        return pipeline.versions(n)
    if kind == "pipeline_rollback":
        from . import pipeline
        p = payload or {}
        n = p.get("name") or ""
        if not n:
            raise ValueError("缺少 name：请给出产物名")
        return pipeline.rollback(n, p.get("to_version"))
    if kind == "pipeline_status":
        from . import pipeline
        return pipeline.list_records(int((payload or {}).get("limit", 20)))
    if kind == "ghost_guard":
        from . import ghost_guard
        return ghost_guard.scan()
    # 定时触发器（V8：无人值守自主循环）
    if kind == "sched_define":
        from . import schedule
        p = payload or {}
        return schedule.define_schedule(p.get("name", ""), p.get("workflow", ""),
                                        p.get("every_seconds", 0),
                                        bool(p.get("enabled", True)))
    if kind == "sched_tick":
        from . import schedule
        return schedule.tick()
    if kind == "sched_status":
        from . import schedule
        return schedule.status((payload or {}).get("name"))
    # 服务巡检（V8：纳入观察，只看不动）
    if kind == "svc_inspect":
        from . import services
        return services.inspect((payload or {}).get("name"))

    # 预留型能力（vision/voice/browser）：真实后端接入（V8 补齐）
    # quant：真实能力（合并平台画像 + 引擎参数）
    if kind == "quant":
        from . import quant_tech
        return {"profile": quant_tech.platform_profile(),
                "engine_params": quant_tech.quant_params().get("engine_params", {})}
    if kind == "vision":
        from . import vision_cap
        p = payload or {}
        return vision_cap.run(p.get("op", "analyze"),
                              image=p.get("image"), region=p.get("region"),
                              grid=p.get("grid", 4), prompt=p.get("prompt"))
    if kind == "voice":
        from . import voice_cap
        p = payload or {}
        return voice_cap.run(p.get("op", "tts"),
                             text=p.get("text"), voice=p.get("voice"),
                             rate=p.get("rate", 0), out=p.get("out"),
                             audio=p.get("audio"))
    if kind == "browser":
        from . import browser_cap
        p = payload or {}
        return browser_cap.run(p.get("op", "open"),
                               url=p.get("url"), query=p.get("query"),
                               engine=p.get("engine", "bing"),
                               timeout=p.get("timeout", 20),
                               max_chars=p.get("max_chars", 20000),
                               **{k: v for k, v in p.items() if k in ("act", "selector", "value", "out", "headless")})
    if kind == "bluetooth":
        from . import bluetooth_cap
        p = payload or {}
        return bluetooth_cap.run(p.get("op", "scan"),
                                 timeout=p.get("timeout", 5.0),
                                 name_filter=p.get("name_filter"),
                                 address=p.get("address"),
                                 char_uuid=p.get("char_uuid"),
                                 value_hex=p.get("value_hex"))
    if kind == "bt_control":
        from . import bt_control
        p = payload or {}
        return bt_control.run(p.get("op", "control"),
                              intent=p.get("intent", ""),
                              address=p.get("address"),
                              scan_timeout=p.get("scan_timeout", 6.0))


# 用法错误基类导入（源头分类用——这些异常类全部继承 Exception，语义=调用方问题）
try:
    from .engine import EngineError
    from .autopilot import AutopilotError
    from .brain_exec import BrainExecError
    from .longrun import LongrunError
    from .schedule import SchedError
    from .think_loop import ThinkLoopError
except Exception:  # pragma: no cover - 循环导入兜底
    EngineError = AutopilotError = BrainExecError = LongrunError = SchedError = ThinkLoopError = Exception


def run_task(kind, payload=None, stamp=True):
    """统一入口：按 kind 调用能力。危险/未知能力一律安全拒绝。

    stamp=True（默认）时，成功结果附带 GBT 钢印，声明独立私人框架出处。
    """
    payload = payload or {}
    _probe = bool(payload.get("_probe"))
    audit("call", {"kind": kind, "payload_keys": [k for k in payload if k != "_probe"],
                   **({"probe": True} if _probe else {})})

    # 危险/破解能力：禁用，不提供可执行路径
    if kind in DISABLED_CAPS:
        audit("denied", {"kind": kind, "reason": DISABLED_CAPS[kind]})
        return {"status": "denied", "kind": kind,
                "message": "capability disabled by safety policy",
                "reason": DISABLED_CAPS[kind]}

    if kind not in BENIGN_CAPS:
        audit("error", {"kind": kind, "reason": "unknown capability"})
        return {"status": "error", "kind": kind, "message": "unknown capability"}

    try:
        result = _run_benign(kind, payload)
        audit("ok", {"kind": kind})
        body = {"status": "ok", "kind": kind, "result": result}
        if stamp:
            body = stamp_result(body)
        return body
    except (ValueError, TypeError, KeyError, EngineError, AutopilotError,
            BrainExecError, LongrunError, SchedError, ThinkLoopError) as e:  # noqa: BLE001
        # 用法/参数类错误（调用方问题：缺参数/坏参数/对象不存在）——不是框架故障，
        # 源头分类记录，selfscan 不再需要判例法区分
        audit("user_error", {"kind": kind, "reason": str(e)[:160],
                             **({"probe": True} if _probe else {})})
        return {"status": "error", "kind": kind, "message": str(e),
                "error_class": "user_error"}
    except Exception as e:  # noqa: BLE001
        audit("error", {"kind": kind, "reason": str(e)[:160],
                        **({"probe": True} if _probe else {})})
        # 错误如实暴露（V8 处世理念：不伪造、坏结果如实报）
        return {"status": "error", "kind": kind, "message": str(e)}
