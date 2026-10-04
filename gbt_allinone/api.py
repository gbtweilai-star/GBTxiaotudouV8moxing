"""GBT小土豆V8 · 统一接口：run_task / list_capabilities。路由到良性能力，禁用危险能力。
V8 行为准则（见 soul.py）：
- 每次调用先落审计（call/ok/error/denied 全程可追踪）；
- 执行结果默认携带 GBT 钢印（声明独立私人框架出处）；
- 错误不吞不瞒：如实返回失败原因，不伪造成功。
"""
import platform
import time
from pathlib import Path

# 🔴 2026-09-25 事故对策：**不再硬 import `caps_registry` 的表**。
#    它在 05:14–05:45 之间被另一个作者并发重写，多次删掉 `UNIMPLEMENTED_CAPS`/`DISABLED_CAPS`
#    ⇒ 硬 import 直接 ImportError ⇒ **整个能力 API 起不来**，连 `framework_gate` 也一起躺下
#    （它 import 包 ⇒ 撞同一处）⇒ **连护照都开不了**。取表改走容错的 `caps_tables`；
#    "表必须齐"由哨兵闸 `caps-registry-guard check` 响亮报（判据在那里，不在这里）。
from .caps_tables import BENIGN_CAPS, DISABLED_CAPS, UNIMPLEMENTED_CAPS, all_caps
from .store import audit, query_log
from .soul import stamp_result, STAMP


def _near_cap_names(name, limit=4):
    """给**打偏的能力位名**找最近邻（只读；只给候选，绝不替人改路由）。

    🔴 为什么加这一条（2026-09-23 磨三层流畅度时自己撞的）：
    我把大脑执行层的读口 `wf_status` 记成了 `wf_list`，拿到的只有一句
    `unknown capability` —— **死路**：输出里看不出这个域到底有哪些名字，
    只能去翻注册表源码。三层（万能插 / 五维合一 / 面板 / CLI）**全过这道门**，
    所以修在这里是**一处修、四层受益**，而不是四个入口各补一次。

    为什么用 difflib 而不是自己写编辑距离：那已经是标准解，自造一份只会多一处会过期的实现。
    候选面 = **全部注册名 + 只登记未实现的名字** —— 后者也要能指出来，
    否则人会把「名字打错」和「名字对但没实现」这两种**完全不同的死法**混成一种。
    """
    import difflib
    pool = list(BENIGN_CAPS.keys()) + list(UNIMPLEMENTED_CAPS.keys())
    if not pool:
        return []
    close = difflib.get_close_matches(str(name), pool, n=limit, cutoff=0.6)
    if close:
        return close
    # 编辑距离兜不住"同族但字面差得远"（如 `caps` 之于 `caps_called_audit`）
    # ⇒ 再补一层**同前缀**候选，让人至少看得到同族有哪些，不至于连方向都没有。
    pre = str(name).split("_")[0]
    if not pre:
        return []
    fam = sorted(p for p in pool if p.startswith(pre + "_"))
    return fam[:limit]

# 历史开关：2026-09-23 Owner 令把禁止全部解开后，这里**不再拦任何名字**。
# 保号原因：外部/旧脚本仍会读它（读到 False 以为"危险能力被关着"是**过度解读**——
# 真正把关的是 policy.py 的作用域门 + 落点门，不是这个常量）。
DANGEROUS_ENABLED = False


def list_capabilities(filter_dangerous=True):
    """返回能力清单。

    filter_dangerous=True（默认）只留**真能调**的能力（`status == "enabled"`）：
      · 解禁前，被拒名单的 11 条状态是 `"disabled"` —— 要剔掉；
      · 解禁后它们状态是 `"unimplemented"`（只有名字、没有实现）—— **同样要剔掉**。
        否则面板/CLI 会把 11 个空名字当"良性能力"播出去，那是**假绿**：
        报得出名字、点下去只会得到 `unknown capability`。
    filter_dangerous=False 才把登记未实现的 11 条一并列出（口径 = 全登记面；**条数现算，别写死**
    —— 2026-09-23 接 `code_patch` 时这里写死的"158"当场过期）。
    """
    items = all_caps()
    if filter_dangerous:
        items = [i for i in items if i.get("status") == "enabled"]
    return items


def _external_capability(module_name, capability):
    """挂载框架外的业务扩展模块（如量化项目桥）。

    框架本体保持纯粹：业务模块不内置分发。模块挂回 → 正常调用；
    不在场 → 如实返回 needs_dependency，绝不伪造结果、也绝不假装能力不存在。
    """
    import importlib
    try:
        return importlib.import_module(f"{__package__}.{module_name}"), None
    except ImportError as exc:
        return None, {
            "ok": False,
            "status": "needs_dependency",
            "missing": module_name,
            "capability": capability,
            "detail": (
                f"{capability} 属于外部业务模块 {module_name}，"
                "本框架不内置分发；把该模块挂回 gbt_allinone/ 即自动可用"
            ),
            "reason": str(exc)[:160],
        }


# codex thread/start 的官方 Schema（app-server v2）参数白名单：effort 只属于 turn/start。
CODEX_THREAD_PARAMS = ("model", "sandbox", "approval_policy", "approvals_reviewer",
                       "developer_instructions", "base_instructions", "ephemeral",
                       "runtime_workspace_roots", "dynamic_tools")


def _codex_thread_params(payload, kind):
    """thread/start 白名单透传；effort 显式拒绝并落审计，不再盲传导致静默降级。"""
    params = {k: payload[k] for k in CODEX_THREAD_PARAMS if k in payload}
    if "effort" in payload:
        audit("codex_param_deprecated", {
            "kind": kind,
            "param": "effort",
            "raw_value": payload.get("effort"),
            "type": type(payload.get("effort")).__name__,
            "note": "thread/start（app-server v2）无 effort；已拒绝下发，"
                    "推理强度请放到 codex_turn_send",
        })
    return params

def _policy_allow_private(policy_decision) -> bool:
    """从策略判定里取 allow_private —— 调用面两形都认，缺省 False。

    R114 实测根因：`run_task` 传下来的是 `policy.authorize()` 的**整包字典**，
    真正的 `PolicyDecision` 在 `decision["decision"]`。旧代码把 `getattr` 直接作用在
    dict 上 -> 恒 False，于是**策略层已经放行的内网目标，到传输层又被 net_guard 拒**：
    授权拿到手也打不通（与 R113「作用域登记了却不可授权」同族，都是判据在、链路断）。
    缺省 False = 内网目标默认拒绝，不放宽任何边界。
    """
    if policy_decision is None:
        return False
    inner = policy_decision
    if isinstance(policy_decision, dict):
        inner = policy_decision.get("decision") or policy_decision
    return bool(getattr(inner, "allow_private", False))


def _run_benign(kind, payload, policy_decision=None):
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
    # 本地数据工具（第 54–55 轮接入）：**只读**，结果从返回里给 ⇒ 作用域天然为空。
    # 口径见 `tools/datakit.py` 的模块 docstring：不给落盘版（会写盘却没有 policy 分支＝绕门）。
    if kind == "datakit":
        from .tools import datakit as _dk
        kw = dict(payload or {})
        op = str(kw.pop("op", "tools"))
        return _dk.run(op, **kw)
    # 外部业务能力（量化项目桥）：模块挂载即用，未挂载如实报缺口
    if kind in ("quant_strategy", "quant_backtest", "platform_profile",
                "quant_params"):
        module, gap = _external_capability("quant_tech", kind)
        if gap:
            return gap
        handler = getattr(module, kind, None)
        if not callable(handler):
            return {"ok": False, "status": "needs_dependency",
                    "missing": f"quant_tech.{kind}",
                    "detail": f"外部模块 quant_tech 未提供 {kind}()"}
        return handler()
    # OSINT 扫描（GBT小土豆V8：src 扫描器正式接入统一接口，全行为落审计）
    if kind == "osint_scan":
        from .recon.scanner import scan_target
        from .recon.guard import classify_target
        t = (payload or {}).get("target") or ""
        if not t:
            raise ValueError("缺少 target：请提供要扫描的域名或 IP")
        kind_t, _reason = classify_target(t)
        allow_private = kind_t == "private"
        rs = scan_target(t, allow_private=allow_private)
        return {"target": t, "allow_private": allow_private,
                "results": [r.to_dict() for r in rs]}
    # 行式记录网格（数据域：陌生文本先画像、再解析、可回写自证）
    if kind == "record_grid":
        from . import record_grid as RG
        p = payload or {}
        return RG.run_op(str(p.get("op") or "profile"), p)
    # 话题追踪（topic_watch）：只做发现与命中；技能本体留在技能目录，不复制实现。
    if kind == "topic_watch":
        from . import topic_watch
        p = payload or {}
        return topic_watch.run(str(p.get("op") or "route"), p)
    # R116 · 生命档案 / 心智引擎 / 项目上下文（三个模块都自带 run(op, **params) 统一入口）。
    # 为什么补在这里：codex_bridge 早已把它们挂成 gbt_life / gbt_mind / gbt_project_context
    # 三个动态工具，但 caps_registry 没登记、本分派也没有分支 —— 工具挂出去了、入口没接上，
    # 调一次就返回 "unknown capability"（死工具）。语义与模块自身一致，不新增授权边界。
    if kind in ("life", "mind", "project_context"):
        from . import life_archive, mind_engine, project_context
        p = dict(payload or {})
        op = p.pop("op", None) or p.pop("action", None)
        mod = {"life": life_archive, "mind": mind_engine,
               "project_context": project_context}[kind]
        return mod.run(op, **p) if op else mod.run(**p)
    # 万能插执行引擎（V8：替代子代理的并行编排层）
    if kind == "wf_define":
        from . import engine
        p = payload or {}
        # 🔴 2026-09-23 磨（三层操作流畅度）：支持 `{"file": "state/xxx.json"}`。
        # 为什么非做不可：一条 5 节点的工作流写成 JSON 有 300+ 字符，塞进命令行要同时打赢
        # PowerShell / cmd / bash 三层引号规则 —— 实测我自己第一次传都得先 `Get-Content -Raw`
        # 才敢传。**要人先学会转义才肯用的入口，等于没有入口。**
        # 口径收紧：只认**仓内 `state/` 下的相对路径**，绝对路径与 `..` 一律拒 ——
        # 免得这个便利口悄悄变成"任意文件读取"。
        _src = p.get("file")
        if _src and not p.get("nodes"):
            import json as _json
            _base = (Path(__file__).resolve().parents[1] / "state").resolve()
            _rel = str(_src).replace("\\", "/").lstrip("/")
            if _rel.startswith("state/"):
                _rel = _rel[len("state/"):]
            _cand = (_base / _rel).resolve()
            try:
                _cand.relative_to(_base)
            except ValueError:
                # 🔴 配方 #5（`docs/无限制创作流水线.md §十三`）：拿到 `filesystem_write`
                # 授权 ⇒ 越界校验**授权即过**；拿不到 ⇒ **逐字节走原分支**（这就是回滚面）。
                # fail-closed 写死：门不可用（导入炸/抛异常）一律**不放行**。
                _authz5 = False
                try:
                    from . import auth_gate as _ag5
                    _authz5 = bool(_ag5.check_and_consume_many(
                        ["filesystem_write"],
                        detail="api._run_benign.wf_define_file").get("ok"))
                except Exception:                            # noqa: BLE001
                    _authz5 = False
                if not _authz5:
                    return {"status": "error", "kind": kind, "error_class": "user_error",
                            "message": "wf_define 的 file 只允许仓内 state/ 下的相对路径（不许绝对路径或 ..）"}
            if not _cand.is_file():
                return {"status": "error", "kind": kind, "error_class": "user_error",
                        "message": "工作流定义文件不存在: state/%s" % _rel}
            try:
                _d = _json.loads(_cand.read_text(encoding="utf-8"))
            except Exception as e:                               # noqa: BLE001
                return {"status": "error", "kind": kind, "error_class": "user_error",
                        "message": "工作流定义文件不是合法 JSON: %s" % type(e).__name__}
            p = {**_d, **{k: v for k, v in p.items() if k != "file"}}
            _out = engine.define_workflow(p.get("name", ""), p.get("nodes", []))
            if isinstance(_out, dict):
                _out["_source_file"] = "state/%s" % _rel     # 可审计：这条定义是从哪个文件读的
            return _out
        return engine.define_workflow(p.get("name", ""), p.get("nodes", []))
    if kind == "wf_run":
        from . import engine
        return engine.run_workflow((payload or {}).get("name", ""),
                                   (payload or {}).get("params"),
                                   fail_fast=bool((payload or {}).get("fail_fast", True)),
                                   max_node_retries=int((payload or {}).get("max_node_retries", 0)))
    if kind == "wf_status":
        from . import engine
        return engine.list_runs((payload or {}).get("name"),
                                int((payload or {}).get("limit", 20)),
                                include_workflows=bool((payload or {}).get("include_workflows", False)))
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
        # R-H295：透传 limit —— 原来固定截断 20 条且未排序，critical 永远取不到，
        # 连带 sec_chain 拿到空料。现在先按严重度排序再截断，并允许调用方取回全量。
        # 同时透传 include_non_production：默认只把生产层结论算进 total/critical，
        # 非生产层（.scratch 备份/快照/镜像、archive、tests 夹具）跳过多少如实报。
        return HackerBrain().scan_vulnerabilities(
            p.get("severity", "medium"), limit=p.get("limit"),
            include_non_production=bool(p.get("include_non_production", False)))
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
                       timeout=int(p.get("timeout", 180)),
                       _coding_discipline=p.get("_coding_discipline"))

    # ── 外部 CLI 智能体：接通（2026-09-25 补齐）─────────────────────────────
    # 这 3 位长期**登记了却没有分派分支** ⇒ 真调落到本函数末尾那条兜底，
    # 返回 `status: not_wired`（更早是 `status: ok` + `result: None` = 报成功但什么都没干）。
    # 哨兵闸 ⑥「登记 vs 接线」一直在点它们的名。现在接真实现：security→cli_agents.py。
    if kind == "claude_code":
        from . import cli_agents
        return cli_agents.claude_code(payload)
    if kind == "codebuddy":
        from . import cli_agents
        return cli_agents.codebuddy(payload)
    if kind == "ul_tars_desktop":
        from . import cli_agents
        return cli_agents.ul_tars_desktop(payload)

    # ── 授权红队内核（Owner 2026-09-25 令：黑客能力多维度全覆盖，使用需人工授权）──
    # 这 12 位此前在 UNIMPLEMENTED_CAPS 里只有名字、没有实现（调用得到 unknown capability）。
    # 实现层：security/redteam.py；作用域：security/policy.py 的 evaluate()。
    # 接线三处必须同时在位（本表 + 本分支 + policy 作用域），少一处门就看不见它。
    if kind in ("redteam_recon", "pentest", "keylogger", "screen_sniff",
                "device_takeover", "remote_domain", "credential_steal",
                "social_eng", "paywallbuster", "asset_vault_freeze",
                "data_hijack", "onboarding_gate"):
        from .security import redteam as _RT
        return _RT.run(kind, payload or {})

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
        # 统一口（Owner 2026-09-19：全部统一大模型）——本处只做**入口与授权**，
        # 通道实现在 llm/unified.py 一处。旧写法直连 bridge 且多传了一个
        # bridge.chat 不认识的 `_coding_discipline` ⇒ 一旦过了授权门就 TypeError；
        # 因为授权门默认拦在前面，这个错**从来没露过面**（统一时抓出）。
        from .llm import unified as LLM
        p = payload or {}
        prompt = p.get("prompt") or p.get("q") or p.get("message") or ""
        if not prompt:
            raise ValueError("缺少 prompt：请给出要问其他 AI 的问题")
        return LLM.ask(prompt, system=p.get("system", ""),
                       model=p.get("model"), temperature=float(p.get("temperature", 0.7)),
                       max_tokens=int(p.get("max_tokens", 2000)), timeout=int(p.get("timeout", 60)),
                       purpose="llm_chat",
                       _coding_discipline=p.get("_coding_discipline"))
    if kind == "llm_status":
        from .llm import bridge as LB
        return LB.status()
    # ── 2026-09-28 补接线（主人令：新增能力必须与触手双向绑定）──────────────
    # 三个模块此前在 `api.py` 里是**零引用**：没有分派 ⇒ 即便登记了名字也只在
    # "能力位三处齐"的 A 项缺一格（framework_state 读数 undispatched）。
    # 口径（与本域既有写法一致，别再各造一套）：
    #   · 作用域声明**挂在 cap 边界** —— `security/policy.py::evaluate` 的
    #     `kind == "<名>"` 分支；不是写在本模块里，见 `llm/unified.py::status()`
    #     的 `gate` 字段（"external_llm 人工授权门装在 cap 边界"）。
    #   · 此处只做**分派**：op + 其余 payload 原样透传给处理器。
    #   · 读类直连 / 写类过门，由中央 `_policy.authorize()` 在分派**之前**统一施加，
    #     不需要在这里再挂第二道闸（重挂 = 同一件事两处真相，迟早漂移）。
    if kind == "key_gateway":
        from .llm import key_gateway as _kg
        p = payload or {}
        return _kg.run(p.get("op", "status"),
                       **{k: v for k, v in p.items() if k != "op"})
    if kind == "multimodal_port":
        from .llm import multimodal_port as _mp
        p = payload or {}
        return _mp.run(p.get("op", "status"),
                       **{k: v for k, v in p.items() if k != "op"})
    if kind == "genoffice_bridge":
        from .llm import genoffice_bridge as _gb
        p = payload or {}
        return _gb.run(p.get("op", "status"),
                       **{k: v for k, v in p.items() if k != "op"})

    # 触手金钥匙（V8：连接大脑执行层的眼睛与双手）
    if kind == "tentacle":
        from .tentacle import bridge as TB
        p = payload or {}
        # 2026-09-19（Owner：触手全部都可以调用本体的全部能力）：
        #   op=caps → 报出触手视野里的本体全部能力（清单读 caps_registry，不复制）
        #   只给 intent 不给 action → 走 auto 自动路由（§2.2 意图默认接线）
        op = str(p.get("op") or "").strip().lower()
        if op in ("caps", "capabilities"):
            return TB.capabilities()
        action = (p.get("action") or p.get("method")
                  or ("auto" if str(p.get("intent") or "").strip() else ""))
        if not action:
            raise ValueError("缺少 action：给触手能力名（tentacle_manifest）、"
                             "给 intent 走自动路由、或 op=caps 看全部能力")
        args = p.get("args") or []
        kwargs = p.get("kwargs") or {}
        # auto 路由要把 intent 送到 invoke 手里（此前只转 args/kwargs，intent 被吞掉）
        if str(p.get("intent") or "").strip():
            kwargs = {**kwargs, "intent": p.get("intent")}
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
    # ── 只读能力（R-H162）：今日 5 个新模块接进万能插（全部只读，无执行能力）──
    if kind == "projection_card":
        from .tools import projection_skill
        return projection_skill.skill_card()
    if kind == "trace_store":
        from . import trace_store
        return trace_store.status()
    if kind == "wave_probe":
        from .tools import wave_probe
        return wave_probe.measure()          # 只读：默认只量不写
    if kind == "dream_replay":
        from .tools import dream_replay
        return dream_replay.dream_once()     # 只读重演：不写、不执行
    if kind == "meta_cognition":
        from .tools import meta_cognition as _mc
        p = payload or {}
        return _mc.run(p.get("op", "law"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "gods_eye":
        # 上帝之眼：眼睛 + 两顾问（权限机器可读）+ 每日汇报 + 计划与决策。
        from .tools import gods_eye as _ge
        p = payload or {}
        return _ge.run_op(p.get("op", "see"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "obsidian_vault":
        from .tools import obsidian_vault as _obs
        p = payload or {}
        return _obs.run_op(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "cap_tags":
        from .tools import cap_tags as _cap
        p = payload or {}
        return _cap.run_op(p.get("op", "tags"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "action_gate":
        from .tools import action_gate as _act
        p = payload or {}
        return _act.run_op(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "growth_hooks":
        from .tools import growth_hooks as _gro
        p = payload or {}
        return _gro.run_op(p.get("op", "shortboard"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "devour_fusion":
        from .tools import devour_fusion as _dev
        p = payload or {}
        return _dev.run_op(p.get("op", "list"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "memory_bank":
        from .tools import memory_bank as _mem
        p = payload or {}
        return _mem.run_op(p.get("op", "aliases"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "agent_console":
        from .tools import agent_console as _age
        p = payload or {}
        return _age.run_op(p.get("op", "board"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "code_audit":
        from .tools import code_audit as _cod
        p = payload or {}
        return _cod.run_op(p.get("op", "report"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "agent_rig":
        from .tools import agent_rig as _age
        p = payload or {}
        return _age.run_op(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "room_space":
        # F12：镜像房间空间 —— 隔离开间/规划/排练，**不覆盖全局现实**
        from . import room_space as _rs
        p = payload or {}
        op = p.get("op", "status")
        if op == "create":
            return _rs.create(p.get("room_id", ""), p.get("purpose", ""))
        if op == "enter":
            return _rs.enter(p.get("room_id", ""), p.get("actor", "owner"), p.get("role", "member"))
        if op == "define_plan":
            return _rs.define_plan(p.get("room_id", ""), p.get("plan"))
        if op == "get_plan":
            return _rs.get_plan(p.get("room_id", ""))
        if op == "gate":
            return _rs.gate(p.get("room_id", ""))
        return {"ok": True, "op": "status", "note": "room_space 可用 op：create/enter/define_plan/get_plan/frame/gate/namespace"}
    if kind == "collab_gateway":
        # F12：协作网关（会话/信箱/同伴）
        from . import collab_gateway as _cg
        p = payload or {}
        op = p.get("op", "status")
        if op == "open_session":
            return _cg.open_session(p.get("topic", ""), p.get("members"))
        if op == "close_session":
            return _cg.close_session(p.get("session_id", ""))
        if op == "inbox":
            return _cg.inbox(p.get("session_id"), p.get("limit", 20))
        if op == "register_peer":
            return _cg.register_peer(p.get("peer_id", ""), p.get("kind", ""))
        if op == "peer_status":
            return _cg.peer_status(p.get("peer_id", ""))
        if op == "server_status":
            return _cg.server_status()
        return _cg.status(p.get("session_id"))
    if kind == "freebuff_term":
        from .tools import freebuff_term as _fbt
        p = payload or {}
        return _fbt.run_op(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "hf_voice":
        from .tools import hf_voice as _hv
        p = payload or {}
        return _hv.run_op(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "console_hub":
        from .tools import console_hub as _chub
        p = payload or {}
        return _chub.run_op(p.get("op", "pages"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "console_pages":
        from .tools import console_pages as _cpg
        p = payload or {}
        return _cpg.run_op(p.get("op", "render"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "lobehub":
        # LobeHub 桌面端全控：七大面 76 把可控制键；启动/关闭过 process_execute 门，
        # 设置写走白名单 + filesystem_write 门；凭据只回形状（按键名掩码）。
        from .tools import lobehub as _lh
        p = payload or {}
        return _lh.run_op(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "comfyui":
        # ComfyUI 全控：966 节点 + API 端点 + 模型清单；出网硬钉（只许本机 8188）。
        from .tools import comfyui_surface as _cs
        p = payload or {}
        return _cs.run_op(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "one_shot":
        # 一句话 → 全链计划（只读；写盘要过门）
        from .tools import one_shot as _os
        p = payload or {}
        return _os.run_op(p.get("op", "show"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "surface_bind":
        # 通用可控制面绑定器：让工具自己报键 → 绑触手 → 重扫对比（消失即断连）。
        from .tools import surface_bind as _sb
        p = payload or {}
        return _sb.run_op(p.get("op", "keys"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "memory_manager":
        # 记忆管理 + 万能秒搜（FTS5 全文；中文可检索）+ 同时端出匹配的能力位。
        from .tools import memory_manager as _mm
        p = payload or {}
        return _mm.run_op(p.get("op", "stats"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "sec_sweeper":
        # 安全棒：每半天全量穿透式交叉扫描 + 健康账/面板 + 专用口 + 上下文复用（不重扫）
        # 外加：框架**垃圾清理**与**加速**（主人 2026-09-27 追加）。
        from .tools import sec_sweeper as _ss
        p = payload or {}
        return _ss.run_op(p.get("op", "health"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "task_manager":
        # 任务管理器：读真进程（psutil）；stop 过门；page 生成静态页。
        from .tools import task_manager as _tm
        p = payload or {}
        return _tm.run_op(p.get("op", "list"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "transformer":
        # 变压器（09-22 原设计 · 2026-09-27 接上）：输入侧压缩 + 输出侧缓存；可旁路 fail-open。
        from .tools import transformer_cap as _tc
        p = payload or {}
        return _tc.run_op(p.get("op", "stats"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "automation_keys":
        # 自动化配置密钥口（主人令 2026-09-27）：只存引用、只回掩码、改配置过门、真密钥走 model_key_pool。
        from .tools import automation_keys as _ak
        p = payload or {}
        return _ak.run_op(p.get("op", "status"),
                          **{k: v for k, v in p.items() if k != "op"})
    if kind == "model_key_pool":
        from .tools import model_key_pool as _mkp
        p = payload or {}
        return _mkp.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "coverage_auditor":
        from .tools import coverage_auditor as _cov
        p = payload or {}
        return _cov.run(p.get("op", "matrix"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "tentacle_cognition":
        from .tools import tentacle_cognition as _tc
        p = payload or {}
        return _tc.run(p.get("op", "redlines"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "caps_called_audit":
        from .tools import caps_called_audit as _ca
        p = payload or {}
        return _ca.run(p.get("op", "audit"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "render_evolution":
        from .tools import render_evolution as _rv
        p = payload or {}
        return _rv.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "orchestration_kernel":
        from .tools import orchestration_kernel as _ok
        p = payload or {}
        return _ok.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "code_art":
        from .tools import code_art_kernel as _ca
        p = payload or {}
        return _ca.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "scene_anchor":
        from .tools import scene_anchor as _sa
        p = payload or {}
        return _sa.run(p.get("op", "classes"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "hook_registry":
        from .tools import hook_registry as _hr
        p = payload or {}
        return _hr.run(p.get("op", "catalogue"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "emotion_projection":
        from .tools import emotion_projection as _ep
        p = payload or {}
        return _ep.run(p.get("op", "model"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "proactive_report":
        from .tools import proactive_report as _pr
        p = payload or {}
        return _pr.run(p.get("op", "model"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "observer_anchor":
        from .tools import observer_anchor as _oa
        p = payload or {}
        return _oa.run(p.get("op", "axioms"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "persona_kernel":
        from .tools import persona_kernel as _pk
        p = payload or {}
        # 空参落到只读 constitution（与其余能力口径一致）；evolve 才写盘。
        return _pk.run(p.get("op", "constitution"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "brand_outro":
        from .tools import brand_outro as _bo
        p = payload or {}
        # R-H295：空参必须落到只读 status（与其余 139 个能力口径一致）。
        # 原先这里默认 "render"，空参直接去干活 → 「作品名不能为空」→ 被误判成缺参数。
        return _bo.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "shared_resources":
        from .tools import shared_resources as _sr
        p = payload or {}
        return _sr.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "verification_watch":
        from .tools import verification_watch as _vw
        p = payload or {}
        return _vw.run(p.get("op", "status"), group=p.get("group"),
                       **{k: v for k, v in p.items() if k not in ("op", "group")})
    if kind == "account_registry":
        from .tools import account_registry as _ar
        p = payload or {}
        return _ar.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind in ("music_intel", "video_intel", "film_intel"):
        from .tools import research_intel as _ri
        p = payload or {}
        return _ri.run(p.get("op", "group"), group=kind,
                       **{k: v for k, v in p.items() if k not in ("op", "group")})
    if kind == "music_publishing":
        from .tools import music_publishing as _mp
        p = payload or {}
        return _mp.run(p.get("op", "status"))      # 只读：不写盘、不出网
    if kind == "director_mood":
        from .tools import director_mood as _dm
        p = payload or {}
        return _dm.run(p.get("op", "status"),
                       **{k: v for k, v in p.items() if k != "op"})   # 只读：不写盘、不执行
    if kind == "libtv_skill":
        # 只读骨架：**不装技能包、不调 API、不出网**；密钥只能从密钥池借
        from .tools import libtv_skill as _lt
        p = payload or {}
        return _lt.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "a1art_skill":
        # 只读骨架：**不调 API、不出网、不落盘**；密钥只能从 DPAPI/密钥池借
        from .tools import a1art_skill as _a1
        p = payload or {}
        return _a1.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "energy_pool":
        # 只读骨架：**不调模型、不出网、不落盘、不发密钥**（模型=燃料）
        from .tools import energy_pool as _ep
        p = payload or {}
        return _ep.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "local_brain":
        # 只读骨架：**不加载模型、不起服务、不出网、不落盘**
        from .tools import local_brain as _lb
        p = payload or {}
        return _lb.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "auto_switch":
        # 只读骨架：**不调模型、不出网、不落盘**（接线点只有 Intent JSON）
        from .tools import auto_switch as _as
        p = payload or {}
        return _as.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "scrapling":
        # 网页抓取（公网限定）：每个 URL 过 net_guard 边界；缺库如实报缺（2026-09-26 主人令接入）
        from .tools import scrapling_cap as _sl
        p = payload or {}
        return _sl.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "genoffice":
        # 办公文档（local-first）：读类直连、写类过 filesystem_write 门（处理器层挂闸）
        from .tools import genoffice_cap as _go
        p = payload or {}
        return _go.run_op(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "blender":
        # 三维电影引擎（local-first）：status 免门，run（渲染/脚本）过 filesystem_write 门
        from .tools import blender_cap as _bl
        p = payload or {}
        return _bl.run_op(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "gs_h3":
        # GS-prompt-extend 三节点接线：读面免门；expand 过 external_llm；loader/unload 过 filesystem_write
        # （主人令「把工作流里的智能体全部一个不差的跟触手连接」· 2026-09-27）
        from .tools import gs_h3_cap as _gs
        p = payload or {}
        return _gs.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "n8n_wf":
        # 我们自己的 n8n：status/list 直连；export/import/active/hook 过门
        from .tools import n8n_wf_cap as _n8
        p = payload or {}
        return _n8.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "tentacle_bind":
        # 资产↔触手穿透式绑定（只读 scan/coverage 直连；bind/unbind 等过门由 CLI 执行）
        import importlib.util as _iu
        from pathlib import Path as _P
        _spec = _iu.spec_from_file_location("tentacle_bind", _P(__file__).resolve().parents[1] / "tools" / "tentacle_bind.py")
        _tb = _iu.module_from_spec(_spec)
        _spec.loader.exec_module(_tb)
        p = payload or {}
        op = p.get("op", "scan")
        if op == "scan":
            return _tb.scan()
        if op == "coverage" and p.get("dir"):
            return _tb.coverage(str(p["dir"]))
        if op == "ledger":
            return {"ok": True, "path": str(_tb.LEDGER),
                    "lines": (len(_tb.LEDGER.read_text(encoding="utf-8").splitlines())
                              if _tb.LEDGER.is_file() else 0)}
        if op == "gaps":
            return _tb.gaps(sample=int(p.get("sample") or 20))
        return {"ok": False, "error": f"未知/受限 op:{op}（读面：scan/coverage/ledger/gaps）", "fail_closed": True}
    if kind == "filmkit":
        # 柔性影片产线（清单制）：status/plan 只读直连；gen/seg/build/add/rm 过 filesystem_write 门
        # （2026-09-26 补接线：此前只在 caps_registry 登记、_run_benign 无分支 ⇒ 调用得到 not_wired）
        from .tools import filmkit_cap as _fk
        p = payload or {}
        return _fk.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "actioncam":
        # 动作镜头控制系统（拍子表制）：plan/status 只读直连；gen/seg/build/add/rm 过 filesystem_write 门
        from .tools import actioncam_cap as _ac
        p = payload or {}
        return _ac.run(p.get("op", "plan"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "look_grade":
        # 外观库触手（词即指令）：list/pick/qc 免门；preview 写盘过 filesystem_write
        from .tools import look_grade_cap as _lg
        p = payload or {}
        return _lg.run(p.get("op", "list"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "zimage_rewash":
        # 洗图流水线（Owner 2026-09-27 立项）：读面免门；upscale 过 filesystem_write；reverse/rewash 如实报缺
        from .tools import zimage_rewash_cap as _zr
        p = payload or {}
        return _zr.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind in ("penetrating_cross_scan", "hook_enforcer", "omission_detector"):
        # 穿透式交叉扫描三件套（Owner 2026-09-27 立项）：钩子强制/步骤锁/交叉互扫/遗漏检测/留痕
        # 三个 kind 共用同一引擎，用不同入口分权：scan=全管线 · verify=只验钩子 · check=只算覆盖
        import importlib.util as _iu
        from pathlib import Path as _P
        _spec = _iu.spec_from_file_location(
            "pcs", _P(__file__).resolve().parents[1] / "tools" / "penetrating_cross_scan.py")
        _pcs = _iu.module_from_spec(_spec)
        _spec.loader.exec_module(_pcs)
        p = payload or {}
        op = (p.get("op") or "status").lower()
        if op == "status":
            return _pcs.status()
        if op == "report":
            return _pcs.report(int(p.get("tail") or 5))
        target = str(p.get("target") or "bindings")
        want = {"penetrating_cross_scan": ("scan", "run"),
                "hook_enforcer": ("verify", "scan"),
                "omission_detector": ("check", "scan")}[kind]
        if op in want:
            return _pcs.run_pipeline(target, mode="check" if kind == "omission_detector" else "scan")
        return {"ok": False, "error": f"未知 op:{op}（status/report/{'/'.join(want)}）",
                "fail_closed": True}
    if kind == "asset_index":
        # 资产索引：整树连接 + 秒查（主人令 2026-09-27）。**读多写少**：build/wire 会写盘
        # （索引库与绑定台账），find/stats 只读。输出全走 JSON 契约，不打印人读行。
        import importlib.util as _iu3
        from pathlib import Path as _P3
        _spec3 = _iu3.spec_from_file_location(
            "asset_idx", _P3(__file__).resolve().parents[1] / "tools" / "asset_index.py")
        _ai = _iu3.module_from_spec(_spec3)
        _spec3.loader.exec_module(_ai)
        p = payload or {}
        op = (p.get("op") or "stats").lower()
        if op == "stats":
            return _ai.stats()
        if op == "find":
            return _ai.find(str(p.get("q") or ""), int(p.get("limit") or 20),
                            str(p.get("label") or ""), str(p.get("ext") or ""))
        if op == "build":
            return _ai.build(verbose=False)
        if op == "wire":
            return _ai.wire(dry=bool(p.get("dry", True)), limit=int(p.get("limit") or 0))
        return {"ok": False, "error": f"未知 op:{op}（build/wire/find/stats）", "fail_closed": True}
    if kind == "control_loop":
        # 快慢双脑控制回路（蒸馏自 Jev/TypeSafe System One）：**只决策不动手**，动作仍走 desktop_control 等门。
        # ⚠️ `selftest`/`demo` 会打印人读行 —— run_task 的返回是 **JSON 契约**，人读行混进 stdout 会把严格消费者
        #    打挂（2026-09-26 实测教训：`five-dim.py cap tentacle_bind` 的输出无法被 json.load 解析）。
        #    ⇒ 这里把它们的输出**收进缓冲区**再作为字段返回。
        import contextlib
        import importlib.util as _iu2
        import io
        from pathlib import Path as _P2
        _spec2 = _iu2.spec_from_file_location(
            "ctl_loop", _P2(__file__).resolve().parents[1] / "tools" / "control_loop.py")
        _ctl = _iu2.module_from_spec(_spec2)
        _spec2.loader.exec_module(_ctl)
        p = payload or {}
        op = (p.get("op") or "selftest").lower()
        if op == "selftest":
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                bad = _ctl.selftest()
            return {"ok": bad == 0, "failures": bad, "report": buf.getvalue()[-1500:],
                    "note": "6 路反向自检：枚举外动作/过期观测/遮挡/DONE 无证据/预算闸/慢脑升级"}
        if op == "decide":
            return _ctl.decide(p.get("obs") or {})
        if op == "observe":
            return _ctl.observe_real(p.get("via") or "vision", p.get("payload") or {},
                                     goal=p.get("goal") or "")
        if op == "act":
            return _ctl.act_real(p.get("via") or "desktop_control", p.get("decision") or {},
                                 execute=bool(p.get("execute")))
        if op == "demo":
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                for _name, _obs in _ctl.SCENES.items():
                    _r = _ctl.decide(_obs)
                    print(f"{_name:<26} op={_r['decision'].get('op')}")
            return {"ok": True, "report": buf.getvalue()}
        return {"ok": False, "error": f"未知 op:{op}（decide/observe/act/demo/selftest）",
                "fail_closed": True}
    if kind == "context_vault":
        # 只读骨架：**不写盘、不建真索引、不出网**（只索引与引用，不复制正文）
        from .tools import context_vault as _cv
        p = payload or {}
        return _cv.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "feishu_embed":
        # 只读骨架：**不打开浏览器、不出网、不落盘、不发密钥**
        from .tools import feishu_embed as _fe
        p = payload or {}
        return _fe.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "libtv_workflow":
        # 只读骨架：**不建节点、不连线、不跑任务、不出网、不落盘**
        from .tools import libtv_workflow as _lw
        p = payload or {}
        return _lw.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "gate_visibility":
        # 只读骨架：**不改门、不动监视范围、不写 store**（只把三态算出来）
        from .tools import gate_visibility as _gv
        p = payload or {}
        return _gv.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "h3_video_gen":
        # 只读骨架：**不装技能、不出网、不落盘、不发密钥**（只登记契约与判据）
        from .tools import h3_video_gen as _h3
        p = payload or {}
        return _h3.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "absorb_loop":
        # 只读骨架：**不跑吞噬、不删文件、不写 store**（只算三阶段与四条闸）
        from .tools import absorb_loop as _al
        p = payload or {}
        return _al.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "cloud_pc":
        # 只读骨架：**不开通、不连、不释放**（只给形状与五个闸）
        from .tools import cloud_pc as _cpc
        p = payload or {}
        return _cpc.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "auto_publish":
        # 只读骨架：**不发、不提、不改价**（只给边界与六个闸）
        from .tools import auto_publish as _ap
        p = payload or {}
        return _ap.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "awesome_tools_index":
        # 只读骨架（**地图**）：**不装工具、不跑工具、不拼请求**
        from .tools import awesome_tools_index as _ati
        p = payload or {}
        return _ati.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "stigmergy":
        # 协作层·间接通道：**只有 DEPOSIT 会写（只追加）**，其余全是读数
        from .tools import stigmergy as _stg
        p = payload or {}
        return _stg.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "ledger_note":
        # 台账登记（R-H600）：RULES/PREVIEW 只读；**只有 APPEND 会写**，
        # 且只往**固定那一份**台账的文件尾追加**一行**（目标由模块自己推，调用方传不了路径）
        from .tools import ledger_note as _led
        p = payload or {}
        return _led.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "capability_net":
        from .tools import ai_capability_net as _net
        _b = _net.build_net()
        return {"ok": True, "readonly": True, "seven_columns": _b["seven_columns"],
                "needs_review": _b["needs_review"],
                "counts": {"total": len(_b["nodes"]), "local": len(_b["local"]),
                           "external": len(_b["external"])},
                "honest_boundary": _b["honest_boundary"]}
    if kind == "code_patch":
        # **改代码的唯一过门入口**（2026-09-23 接）。
        # 为什么放在能力位而不是让 agent 直接编辑：走这里 ⇒ 天然带上唯一门的
        # 授权 / 审计 / 信封 / preflight；**改前改后哈希与回执**也一并落盘。
        # 🔴 **不吞异常**：本能力的 `CodePatchError(ValueError)` 让它往上抛，
        # 由下面统一的 `except (ValueError, …)` 收敛成 `status: error` + `error_class: user_error`。
        # （第一版在这里 catch 成错误 dict ⇒ 外层被判成 `status: ok`：读数自相矛盾。）
        from .tools import code_patch as _cp
        return _cp.run(payload or {})
    if kind == "git_read":
        # 版本库**只读面**：零作用域（policy 里不挂任何 scope），永远 shell=False。
        from .tools import git_repo as _gr
        return _gr.run_read(payload or {})
    if kind == "git_write":
        # 版本库**写面**：policy 里**永远**挂 filesystem_write（不按 op 判）。
        from .tools import git_repo as _gr2
        return _gr2.run_write(payload or {})
    if kind == "omni_web":
        # 万能触手·Web六态：看结构/读源码/读讲解/改文件/交给AI/跑项目
        # 2026-10-04：按能力位真名导入（真名门面 omni_web.py → 实现 omni_web_cap.py）
        from . import omni_web as _ow
        p = payload or {}
        op = str(p.get("op") or "read_structure")
        return _ow.run(op=op, **{k: v for k, v in p.items() if k != "op"})
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
        p = payload or {}
        # 🔴 2026-09-25：H 维加**整体预算**（默认 240s），且**预算可显式关掉**。
        #    起因：无预算时空参 `cross_scan` 实测 >560s 不返回（H 维逐个真调，
        #    里面躺着 sec_scan / sec_chain 这类 5 分钟级的只读扫描器）。
        #    为什么默认有界：无界 = **根本跑不起来**，覆盖率是 0，比"有界 + 如实报没跑到"更差。
        #    要旧的无预算行为：`{"deep": true, "h_budget_s": null}`（显式、看得见）。
        return cross_scan.scan(bool(p.get("deep", True)),
                               h_budget_s=p["h_budget_s"] if "h_budget_s" in p
                               else cross_scan.H_BUDGET_S)

    # 全息盘点（V8：对齐你的视图与框架的视图——归属四分类）
    if kind == "inventory":
        from . import inventory
        return inventory.scan(bool((payload or {}).get("fix", False)))

    # 脑库接入（R-H94）：把 Obsidian 记忆库接成"跟着一起上线"的记忆
    if kind == "brain_vault":
        from . import brain_vault
        p = payload or {}
        op = str(p.get("op") or "status").strip().lower()
        if op == "status":
            return brain_vault.status()
        if op == "recall":
            return brain_vault.recall(int(p.get("limit", 10)))
        if op == "remember":
            return brain_vault.remember(p.get("text", ""))
        return {"status": "error", "kind": kind, "message": "未知动作: %s" % op,
                "error_class": "user_error"}

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
        p = payload or {}
        t = p.get("target") or ""
        if not t:
            raise ValueError("缺少 target：GitHub 仓库/子目录 URL 或本地目录路径")
        return qiankun.one_key_deploy(
            t,
            p.get("purpose", ""),
            p.get("plan") if isinstance(p.get("plan"), dict) else None,
            p.get("name") or "one-key",
            p.get("room") or "",
            bool(p.get("into_global_production", False)),
        )
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
    if kind == "mirror_plan":
        from . import deployment_rehearsal as DR
        p = payload or {}
        name = p.get("name") or "default"
        plan = p.get("plan")
        if isinstance(plan, dict):
            return DR.define_plan(name, plan)
        return DR.get_plan(name)
    if kind == "mirror_simulate":
        from . import deployment_rehearsal as DR
        p = payload or {}
        return DR.simulate(
            p.get("name") or "default",
            p.get("plan") if isinstance(p.get("plan"), dict) else None,
        )
    if kind == "mirror_parity":
        from . import deployment_rehearsal as DR
        p = payload or {}
        name = p.get("name") or "default"
        plan = p.get("plan") if isinstance(p.get("plan"), dict) else None
        if str(p.get("op") or "").lower() == "capture":
            return DR.capture_profile(name, plan)
        return DR.parity(
            name,
            production=p.get("production") if isinstance(
                p.get("production"), dict) else None,
            plan=plan,
        )
    if kind == "mirror_rehearse":
        from . import deployment_rehearsal as DR
        p = payload or {}
        return DR.rehearse(
            p.get("name") or "default",
            p.get("plan") if isinstance(p.get("plan"), dict) else None,
            execute=bool(p.get("execute", True)),
        )
    if kind == "mirror_release":
        from . import deployment_rehearsal as DR
        p = payload or {}
        return DR.release(
            p.get("name") or "default",
            p.get("purpose", ""),
            p.get("plan") if isinstance(p.get("plan"), dict) else None,
        )
    if kind == "mirror_ascend":
        from . import mirror_space as MS
        p = payload or {}
        # R113 · 修法甲：mirror_space.ascend() 真身签名是 ascend(purpose: str = "")，
        # 只有单形参。旧代码把 require_rehearsal / rehearsal_name 直接透传，走能力层
        # 必抛 TypeError（R110 实测带出）。现改为：本层只做真实调用；调用方要演练
        # 前置门时 fail-closed 返回指引，不静默忽略。演练门由 mirror_rehearse +
        # mirror_release 承担，不塞进"唯一写 production 的函数"。
        if bool(p.get("require_rehearsal", False)):
            return {
                "ok": False,
                "blocked": True,
                "reason": "本层不支持演练前置门（require_rehearsal）",
                "how_to": "先调 mirror_rehearse 取演练结论，通过后再调 mirror_ascend；"
                          "正式发布走 mirror_release(name=...)。",
                "name": p.get("name") or "default",
                "cap": "mirror_ascend",
            }
        return MS.ascend(p.get("purpose", ""))
    if kind == "mirror_status":
        from . import deployment_rehearsal as DR
        from . import mirror_space as MS
        p = payload or {}
        result = MS.mirror_status()
        if p.get("include_rehearsal"):
            result["rehearsal"] = DR.status(p.get("name") or "default")
        return result
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
    if kind == "agency_tentacles":
        from .tools import agency_tentacles as _at
        p = payload or {}
        return _at.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "media_pipeline":
        from .tools import media_pipeline as _mp
        p = payload or {}
        return _mp.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "edit_pipeline":
        from .tools import edit_core as _ec
        p = payload or {}
        return _ec.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "audio_extract":
        # 从视频里取声音（本机 ffmpeg，零出网）。写面由模块自己收窄 ——
        # 理由见 `tools/audio_extract.py` 模块头：policy 对未登记 kind 零作用域，而 policy.py 只有主人能改。
        from .tools import audio_extract as _ae
        p = payload or {}
        return _ae.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "audio_mix":
        # 混音 + 母带（三方向音乐维度的 04-mix / 05-master 两格）。同一套纪律。
        from .tools import audio_mix as _am
        p = payload or {}
        return _am.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "media_publish":
        # 三方向发布到赚钱平台：备好发布包 → **停在主人的授权门**（零出网、绝不假装已发布）
        from .tools import media_publish as _mp
        p = payload or {}
        return _mp.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "media_run":
        # 三方向自动化工作流执行器：一次调用跑完一条链（每步落真件 + 同批登记许可）
        from .tools import media_run as _mr
        p = payload or {}
        return _mr.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "media_license":
        # 素材许可账（三方向流程台「家规第 2 条」的**逐件**数据源）。
        # 写面只落 projects/_shared/licenses/；media_flow 的门只读它（判定归门，登记归能力位）。
        from .tools import media_license as _ml
        p = payload or {}
        return _ml.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "tentacle_pipeline":
        from .tools import tentacle_pipeline as _tp
        p = payload or {}
        return _tp.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})
    if kind == "long_run_supervisor":
        from .tools import long_run_supervisor as _lrs
        p = payload or {}
        return _lrs.run(p.get("op", "status"), **{k: v for k, v in p.items() if k != "op"})

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

    # 通信域（R104 · 刀一 coze_mail）：对主人自有单一地址做收发与整理。
    if kind == "coze_mail":
        from . import coze_mail_cap as CM
        return CM.run((payload or {}).get("op") or "status", payload or {})

    # 创作出口（R104 · 刀二 create）：意图/产物登记 ＋ 仅限 outputs/ 的写入。
    if kind == "create":
        from . import file_operation as FO
        return FO.run((payload or {}).get("op") or "status", payload or {})

    # 短剧/影视链路 · 模块1 剧本理解引擎（接口1 剧本→分镜）
    if kind == "drama":
        from . import drama as DR
        p = dict(payload or {})
        return DR.run(p.pop("op", "status"), **p)

    # 爆火作品观察 + 用户偏好台账（Owner 2026-09-19）
    if kind == "trend_watch":
        from . import trend_watch as TWD
        p = dict(payload or {})
        return TWD.run(p.pop("op", "status"), **p)

    if kind == "tentacle_status":
        from .tentacle import bridge as TB
        return {"diagnose": TB.self_diagnose(), "coverage": TB.coverage()}

    # 察言观色层（V8：人情世故可执行化）
    if kind == "tactics_advise":
        from . import tactics
        p = payload or {}
        return tactics.advise(p.get("user_text", ""), p.get("situation", ""))
    # ── 官方 Codex 能力化（B 档 · 注册与路由是同一个原子单元，一次落地）──
    # R122：补 codex_chat / codex_models —— 作用域在 policy.py、实现在 codex_bridge.py，
    # 注册与路由两环从未接上，统一入口此前一律 unknown capability。
    if kind in ("codex_status", "codex_tools", "codex_thread_new",
                "codex_turn_send", "codex_interrupt",
                "codex_chat", "codex_models"):
        from . import codex_bridge as _CB
        p = payload or {}
        if kind == "codex_status":
            return _CB.status()
        if kind == "codex_tools":
            return {"ok": True, "tools": [t.get("name") for t in _CB.dynamic_tool_specs()]}
        if kind == "codex_models":
            return {"models": _CB.get_shared_server().list_models()}
        if kind == "codex_chat":
            message = str(p.get("message") or p.get("text") or "").strip()
            if not message:
                raise ValueError("缺少 message：请给出要发送给 Codex 的文本")
            opt = {}
            if p.get("model"):
                opt["model"] = str(p["model"])
            if p.get("cwd"):
                opt["cwd"] = str(p["cwd"])
            if p.get("thread_id"):
                opt["thread_id"] = str(p["thread_id"])
            if p.get("timeout"):
                opt["timeout"] = float(p["timeout"])
            # 2026-09-22：生产路由默认把这轮输出收进自进化知识库
            # （Owner：「记录大模型的技术输出来提升自己、进化自己」）。
            # 默认开在**路由层**而不是 run_once 的默认值上 —— 这样单元测试直接调
            # run_once 时不会往真 store 里写东西，两边都不脏。
            opt["record_kb"] = bool(p.get("record_kb", True))
            return _CB.run_once(message, **opt)
        thread_id = str(p.get("thread_id") or "").strip()
        if kind == "codex_thread_new":
            # thread/start 只认白名单（app-server v2 无 effort），effort 显式拒绝 + 落审计；
            # 盲传会在出网前一帧都发不出就 TypeError，并被上层 except 静默降级。
            return _CB.get_shared_server().start_thread(**_codex_thread_params(p, kind))
        if not thread_id:
            raise ValueError("缺少 thread_id：请先调用 codex_thread_new")
        if kind == "codex_turn_send":
            return _CB.get_shared_server().start_turn(
                thread_id, str(p.get("text") or ""), effort=p.get("effort"))
        return _CB.get_shared_server().interrupt(thread_id, p.get("turn_id"))

    # 生产管线（V8：唯一交付通道）
    if kind == "pipeline_submit":
        from . import pipeline
        p = payload or {}
        return pipeline.submit(p.get("name", ""),
                               p.get("content", ""),
                               p.get("meta") or {},
                               review=bool(p.get("review", False)),
                               refine_rounds=int(p.get("refine_rounds", 0)))
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
    # quant：外部业务模块（量化项目桥）——合并平台画像 + 引擎参数
    if kind == "quant":
        module, gap = _external_capability("quant_tech", kind)
        if gap:
            return gap
        return {"profile": module.platform_profile(),
                "engine_params": module.quant_params().get("engine_params", {})}
    if kind == "vision":
        from . import vision_cap
        p = payload or {}
        return vision_cap.run(p.get("op", "analyze"),
                              image=p.get("image"), region=p.get("region"),
                              grid=p.get("grid", 4), prompt=p.get("prompt"))
    if kind == "prompt_bridge":
        from . import prompt_bridge as _pb
        p = payload or {}
        return _pb.run(p.get("op", "compile"), text=p.get("text"))
    if kind == "voice":
        from . import voice_cap
        p = payload or {}
        # 🔴 2026-09-23 第 59 轮修：这里原先是**白名单派发**，只转发 text/voice/rate/out/audio
        #    ⇒ `op=listen` 的 seconds/culture/min_confidence/timeout **从来传不进去**
        #    （永远用默认 6 秒），而调用方看不出被丢了参数 —— 静默失效。
        #    实测抓法：传 `"wav": "<路径>"` 走门，读数里 `wasapi-record` 那条腿**照样跑**
        #    ⇒ 说明载荷没到。补全 listen 的全部参数（不改变任何作用域判定）。
        #
        # 🔴 2026-09-25 第 61 轮修（**同一类病的第二个样本，第 59 轮只补了这一例的参数**）：
        #    上面那次只是把**已知的** listen 参数补进白名单 —— 白名单之外的一切**照样静默丢**。
        #    实测（真跑过，不是推演）：`voice` 传 `path=<wav路径>` 期望落盘，读数回的是
        #      `{"ok": true, "backend": "win-sapi", "spoken": true}` —— **没有文件、0 字节**，
        #    而信封 `status:"ok"`、退出码 0。调用方只看到"成功了"，看不到"你的参数没到"。
        #    修法与 `browser` 分支（见下方同款注释）**完全一致**：不再手写白名单，**全量透传**，
        #    认不认得出交给能力层；认不出的由能力层如实报 `ignored_params`。
        #    保留 `_fw` 排除框架保留字（`op` 已由位置参数占位，重复会 TypeError）。
        _fw = {"op", "_probe", "_verify", "force", "_force"}
        return voice_cap.run(p.get("op", "tts"),
                             **{k: v for k, v in p.items() if k not in _fw})
    if kind == "voice_orchestra":
        from . import voice_orchestra as _vo
        p = payload or {}
        # R-H295：空参落到只读 status（先报本机可跑性），与其余能力口径一致。
        return _vo.run(p.get("op", "status"), domain=p.get("domain"),
                       keyword=p.get("keyword"), scene=p.get("scene"))
    if kind == "browser":
        from . import browser_cap
        p = payload or {}
        # 原生浏览器（op=native/deep/controller/cdp）由 browser_cap 这一层门面转 native_browser，
        # 分发细节见 browser_cap.native()；作用域判定仍完全在 security/policy.py。
        #
        # 🔴 2026-09-25 **参数静默丢失修复**（实测踩到，不是理论风险）：
        #    这里原来是一张**手写白名单**
        #      `k in ("act","action","cmd","selector","value","out","headless")`
        #    ⇒ 白名单之外的一切参数**被静默丢掉**，而且**不报错**（调用方只看到引擎报「缺参数」）。
        #    实测后果（逐条真跑过）：
        #      · execute_script / inject_script → `js` 被丢 ⇒ 连 `1+1` 都报
        #        `execute_script() missing 1 required positional argument: 'js'`
        #      · type_text → `text` 被丢
        #      · activate_tab / close_tab → `tab_id` 被丢
        #      · pin_window → `rect` / `topmost` 被丢（手动置顶落位失效）
        #      · dom_query → `limit` 被丢（永远退回默认 50）
        #    而 browser_cap.native() 的设计注释写着「按**目标动作的真实签名**裁剪」——
        #    参数根本走不到它那儿就被这里砍了：**意图与实现脱节**。
        #    ⇒ 修法：native 系**全量转发**（只排掉门面自己的键），把裁剪权交还给 native()
        #      的真签名裁剪（它本来就是干这个的）；非 native 系保持原白名单，行为零变化。
        op = p.get("op", "open")
        facade = {"op", "url", "query", "engine", "max_chars", "timeout", "allow_private"}
        if op in browser_cap.NATIVE_BROWSER_OPS:
            extra = {k: v for k, v in p.items() if k not in facade}
        else:
            extra = {k: v for k, v in p.items()
                     if k in ("act", "action", "cmd", "selector", "value", "out", "headless")}
        return browser_cap.run(op,
                               url=p.get("url"), query=p.get("query"),
                               engine=p.get("engine", "bing"),
                               timeout=p.get("timeout", 20),
                               max_chars=p.get("max_chars", 20000),
                               allow_private=_policy_allow_private(policy_decision),
                               **extra)
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
    # 🔴 2026-09-25 **假绿修复**：这里原来**没有兜底 return** —— 函数走到末尾就**隐式返回 None**，
    #    而 `run_task` 在 L1543 无条件把它包成 `{"status": "ok", "kind": kind, "result": None}`。
    #    实测后果：登记在 `BENIGN_CAPS` 却**没有分派分支**的位（`claude_code` / `codebuddy` /
    #    `ul_tars_desktop`）真调返回 **`status: ok` + 内层 `result: None`** ⇒
    #    **报成功，但什么都没干**（比"没这个能力"更坏：调用方分不清"干了没输出"和"根本没干"）。
    #    ⇒ 兜底必须**如实说**：「登记了、门没接」。这条与 `caps_registry` 无关（那个文件正被
    #    另一个作者并发改写），所以不冲突。
    return {"status": "not_wired", "kind": kind, "ok": False,
            "error_class": "not_wired",
            "message": ("能力位「%s」**已登记，但没有分派分支** —— "
                        "`_run_benign` 里找不到 `if kind == \"%s\"`。" % (kind, kind)),
            "读法": "**不是「实现坏了」，也不是「被门拒」**，是「**名字有了、门没接**」",
            "怎么修": "在 `gbt_allinone/api.py::_run_benign` 里给它接一个分支；"
                   "或把它从 `BENIGN_CAPS` 移进 `UNIMPLEMENTED_CAPS`（只有名字、没有实现）"}


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


# ═══════════ 信封 ok 的判据表（2026-09-25 fail-closed 修复）═══════════════
# 🔴 原实现是 **fail-open（默认放行）**：
#       ok = status not in ("error", "denied", "failed", "needs_dependency")
#    凡是不在这张 4 项表里的状态一律算成功。全仓实扫 **63 种 status**，实测
#    **59 种落到 ok=True**，其中这些一眼就是「没成」：
#       timeout · not_implemented · unimplemented · needs_implementation ·
#       not_wired · needs_browser_debug（一个标签页都没连上）· blocked ·
#       refused · rejected · input_rejected · unverified · contradicted ·
#       missing · not_found · no_input · no_window · no_engine_found ·
#       pending · awaiting_input · transcription_not_started ·
#       unsupported · disabled · no_enabled · skipped · degraded …
#    ⇒ 这就是「自检全过」反复误报的**机制性来源**：不是谁粗心，
#      是**契约层的默认值站在"成功"那一边**。
#
# 修法三条纪律：
#   ① **fail-closed**：`ok` 只有在**明确列进成功表**时才算真；
#   ② **生产者优先**：生产者自己给了 `ok`（或给了 `error`）就一律听它的 ——
#      这保证逐字节向后兼容，改动只影响"靠默认值蒙过去"的那些；
#   ③ **不猜语义**：既不在成功表、也不在已知失败表里的状态，判失败**并**打
#      `unknown_status` 标记，把残余问题**变成可枚举的清单，而不是靠人猜**。
_ENVELOPE_OK_STATUS = frozenset({
    # 明确断言「做成了」的状态语
    "ok", "done", "ready", "completed", "green", "verified", "published",
    "ran", "launched", "fetched", "prepared", "released", "winner",
    "acquired", "reuse", "already_running", "already_satisfied",
})
_ENVELOPE_FAIL_STATUS = frozenset({
    # 已知的失败/拒绝/未就绪语义（只用于「不把已知失败误标成 unknown」）
    "error", "denied", "failed", "needs_dependency",
    "timeout", "blocked", "refused", "rejected", "input_rejected",
    "not_implemented", "unimplemented", "needs_implementation", "not_wired",
    "needs_browser_debug", "unsupported", "disabled", "no_enabled",
    "missing", "not_found", "no_input", "no_topics", "no_window",
    "no_engine_found", "pending", "awaiting_input", "not_running",
    "transcription_not_started", "source_bound_pending_review",
    "unverified", "contradicted", "input_unjudged", "not_guarded",
    "skipped", "degraded", "boundary", "need_address",
    "needs_pairing_or_protocol",
})


def _normalize_envelope(kind: str, raw) -> dict:
    """把任意历史返回结构归一成统一契约。

    统一契约（对外承诺，永远存在这四个字段）::

        {"ok": bool, "kind": str, "result": Any, "error": str | None}

    旧字段（``status`` / ``gbt_stamp`` / ``gbt_result`` / 分支专属字段）全部保留，
    因此旧的调用方无需改动；新调用方只看 ``ok`` 与 ``result`` 即可。

    另加两个**读数溯源**字段（新调用方可选读，旧调用方无感）::

        ok_source   "explicit"（生产者自己给的） | "status"（按状态表推的）
        unknown_status  仅在「状态既不在成功表也不在已知失败表」时出现 —— 它表示
                        **这里有一条没被归类的状态语义，需要人工归位**（不是失败）。
    """
    if not isinstance(raw, dict):
        raw = {"result": raw}
    out = dict(raw)
    inner = raw.get("gbt_result")
    if inner is None:
        inner = raw.get("result")
    if inner is None:
        # 错误 / 拒绝类信封：载荷就是信封自身（含 error / message / denied /
        # missing / how_to_grant 等），不能只给"去掉 error 的残壳"——否则按
        # r.get("result", r) 取值的调用方会拿到空 error，丢掉真实原因。
        inner = dict(raw)
    status = str(raw.get("status") or "").strip().lower()
    ok = raw.get("ok")
    ok_source = "explicit"
    if ok is None:
        # 顶层没给 ok —— **先把证据找全再判**，别一上来就 fail-closed。
        # 旧信封把状态藏在 gbt_result / result 里（实测：file_operation 的信封
        # 顶层只有 gbt_stamp + gbt_result，status:ok 在内层）⇒ 只读顶层会把
        # 一次**真成功**判成失败（这是我第一版的回归，已修）。
        nested = inner if isinstance(inner, dict) else {}
        nested_is_raw = nested is raw
        nested_ok = nested.get("ok") if not nested_is_raw else None
        eff_status = status
        if nested_ok is None and not eff_status and not nested_is_raw:
            eff_status = str(nested.get("status") or "").strip().lower()
        if nested_ok is not None:
            ok = nested_ok
            ok_source = "gbt_result.ok"
        else:
            # fail-closed：只有进成功表才算成功；同时把没归类的状态标出来
            ok = eff_status in _ENVELOPE_OK_STATUS
            ok_source = "status"
            if ok and raw.get("error"):
                ok = False
            if eff_status and eff_status not in _ENVELOPE_OK_STATUS \
                    and eff_status not in _ENVELOPE_FAIL_STATUS:
                out["unknown_status"] = eff_status
    out["ok_source"] = ok_source
    out["ok"] = bool(ok)
    out["kind"] = raw.get("kind") or kind
    out["result"] = inner
    out["error"] = None if out["ok"] else (raw.get("error") or raw.get("message")
                                           or raw.get("reason") or status or "unknown error")
    out.setdefault("status", "ok" if out["ok"] else "error")
    return out


def run_task(kind, payload=None, stamp=True, safe=False, probe=False):
    """统一入口（契约层）。

    无论能力内部走哪条分支（成功 / 未知 / 拒绝 / 异常），对外都返回同一信封::

        {"ok": bool, "kind": str, "result": Any, "error": str | None, ...旧字段}

    这层只做**形状归一化**，不改变任何能力的行为与安全检查顺序。

    异常语义保持向后兼容：默认 ``safe=False`` 时，能力内部抛出的异常照旧向上传播
    （既有调用方与测试依赖这个行为）；只有显式传 ``safe=True`` 时才把异常收敛成
    ``{"ok": False, "error": ...}`` 信封，供面板/桥接层这类需要"永不炸"的调用方使用。

    探针口径（O8 · 2026-09-17）：``probe=True`` 表示**这一次调用是内部状态探针**——
    本次调用**一处审计都不写**（``call`` / ``ok`` / ``denied`` / ``user_error`` / ``error`` /
    ``preflight_*`` 全免）。豁免按「**哪一次调用**」开关，**不按 kind 开关**：
    同一个 kind 在别的调用方那里照旧留痕（否则等于给一个能力永久摘掉审计）。
    默认 ``probe=False``（既有调用方零改动）；payload 里的 ``_probe`` 继续认。
    """
    if __import__("os").environ.get("GBT_CONTRACT_LEGACY") == "1":
        # 基线对照开关：临时绕过归一化层，用于回归归因；默认关闭，不影响正常运行。
        return _run_task_core(kind, payload, stamp=stamp, probe=probe)
    if safe:
        try:
            raw = _run_task_core(kind, payload, stamp=stamp, probe=probe)
        except Exception as exc:  # noqa: BLE001
            if not probe:
                audit("error", {"kind": kind, "error_class": "runtime_fault",
                                "error": str(exc)[:200]})
            raw = {"status": "error", "kind": kind, "error": str(exc)[:200],
                   "error_class": "runtime_fault"}
    else:
        raw = _run_task_core(kind, payload, stamp=stamp, probe=probe)
    # 产出即绑（2026-09-26 · 主人问「穿透都连好了嘛」抓出的配置缺口）：
    # 此前自动绑定只挂在 filmkit 一处 ⇒ "产出即绑"只在电影产线成立，别的触手产出
    # 要靠人工 sweep 才进账。这里提升成**总闸级**：任何一次非 probe 调用返回后，
    # 把这次调用期间**新出现/新改动**的资产自动绑标签（先按属性自判，判不出才用 kind 兜底）。
    # 三条保险：只看资产根（不做全仓遍历）· 模块内 3 秒节流 · **异常全吞**（绝不许弄坏一次真调用）。
    if not probe:
        try:
            _autobind_hook(kind)
        except Exception:  # noqa: BLE001
            pass
    return _verify_result(kind, payload, _normalize_envelope(kind, raw), probe=probe)


_AUTOBIND_MOD = [None]


def _autobind_hook(kind: str) -> None:
    """惰性加载 `tools/tentacle_bind.py`（仓根 tools，不在包内）并跑节流版 autobind。"""
    if _AUTOBIND_MOD[0] is None:
        import importlib.util as _iu
        from pathlib import Path as _P
        spec = _iu.spec_from_file_location(
            "tentacle_bind", _P(__file__).resolve().parents[1] / "tools" / "tentacle_bind.py")
        mod = _iu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _AUTOBIND_MOD[0] = mod
    _AUTOBIND_MOD[0].autobind(kind_hint=str(kind or ""))


# ═══════════ 机检门：让**她自己**执行时也自检（Owner 2026-09-22「乙」）═══════════
# Owner：「把这套门接到 run_task 上，让她自己执行时也走五维 + 机检 ——
#         这才是'框架打磨成高难度任务都可轻松完成'的正题，而不是只锁住我一个人」
#
# 设计要点（为什么这样接不会自噬）：
#   · 门只看**结果**，**不重跑路径** ⇒ 不会有 sync_exec.run → run_task → sync_exec.run 的递归。
#   · 载荷里没有 `_verify` 时，行为与改动前**逐字节等价**（零影响）。
#   · 载荷里带 `_verify` 时，声明被满足才算成功：不满足 ⇒ `ok` 置 False 并列出哪一条没过。
#     这与 step_close 那套同源：**判据是机器算的，不是谁嘴上说的**。
#
# 声明写法（都可机检）：
#     "_verify": {"ok": True}                      # 信封 ok 必须为真
#     "_verify": {"equals": {"status": "ok"}}      # result 里的字段必须等于
#     "_verify": {"has_keys": ["out", "bytes"]}    # result 里必须有这些键
#     "_verify": {"min": {"frames_got": 1}}        # result 里的数值必须 >=
#     "_verify": {"not_empty": ["path"]}           # result 里的字段非空
def _verify_result(kind, payload, env, *, probe=False):
    """按 `_verify` 声明机检结果。没有声明 ⇒ 原样返回（零影响）。"""
    decl = None
    try:
        if isinstance(payload, dict):
            decl = payload.get("_verify")
    except Exception:                                               # noqa: BLE001
        decl = None
    if not isinstance(decl, dict) or not decl:
        return env

    res = env.get("result") if isinstance(env, dict) else None
    resd = res if isinstance(res, dict) else {}

    def _get(key):
        """**两层信封都要找**（2026-09-22 实测教训）。

        本框架是双层：`env["result"]` 其实是 `{kind, result, status}`，
        真正的数据在 `env["result"]["result"]` 里。我第一版只看浅层，
        于是 `has_keys: ["platform"]` 明明该满足却被判失败 —— **尺子量错了层**。
        ⇒ 先看浅层，找不到再下钻一层。
        """
        if key in resd:
            return resd[key], True
        inner = resd.get("result")
        if isinstance(inner, dict) and key in inner:
            return inner[key], True
        return None, False

    failed = []

    if "ok" in decl and bool(env.get("ok")) != bool(decl["ok"]):
        failed.append(f"ok: 期望 {bool(decl['ok'])} 实得 {bool(env.get('ok'))}")
    for k, v in (decl.get("equals") or {}).items():
        got, found = _get(k)
        if not found:
            got = env.get(k)
        if got != v:
            failed.append(f"equals[{k}]: 期望 {v!r} 实得 {got!r}")
    for k in (decl.get("has_keys") or []):
        if not _get(k)[1]:
            failed.append(f"has_keys: result 里缺 {k!r}（浅层与内层都找过了）")
    for k, v in (decl.get("min") or {}).items():
        got, found = _get(k)
        try:
            if not found or float(got) < float(v):
                failed.append(f"min[{k}]: 期望 >= {v} 实得 {got!r}")
        except Exception:                                           # noqa: BLE001
            failed.append(f"min[{k}]: 实得 {got!r} 不是可比较的数值")
    for k in (decl.get("not_empty") or []):
        got, found = _get(k)
        if not found:
            got = env.get(k)
        if got in (None, "", [], {}):
            failed.append(f"not_empty[{k}]: 实得空")

    if isinstance(env, dict):
        env["verified"] = not failed
        env["verify_declared"] = True
        if failed:
            env["verify_failed"] = failed[:6]
            env["ok"] = False           # 声明没被满足 ⇒ 这次调用**不算成功**
    if not probe:
        try:
            audit("verify_pass" if not failed else "verify_fail",
                  {"kind": kind, "failed": failed[:4], "checked": len(decl)})
        except Exception:                                           # noqa: BLE001
            pass
    return env


def _run_task_core(kind, payload=None, stamp=True, probe=False):
    """**唯一那道门**（2026-09-23 加默认同步）。

    这一层只做一件事：进门先 `auto_envelope()` —— 没在信封里就自己开一个，
    已经在里头就原样不动。为什么收在这里而不是给三层各写一遍：

      · 五维合一（`five-dim.py cap`）本来就有自己的信封，这里是 `outer`，**不覆盖**；
      · 万能插（`omni.py run`）走 `five-dim.py cap` 子进程，同上；
      · **大脑执行层**（`engine.py` 是 `from .api import _run_task_core as run_task` 直连内层，
        `brain_execute` / `brain_unify` / `think_loop` 也都在进程内往下调）**原先没有自己的默认** ——
        面板 `panel_server.capability()`、`python -m gbt_allinone`、任何直调都算"信封外"。
      收在门口 ⇒ 三条主道 + 面板 + CLI + 复合能力**一处生效**，不靠谁记得先 open。

    归属如实分格：`auto` = 门口替你开的默认同步；`outer` = 外层早就开着（主动信封）。
    两者**不是一回事**，混成一格就会把"我把默认打开了"冒充成"纪律执行得好"。
    """
    from .tools.sync_exec import auto_envelope
    with auto_envelope():
        return _run_task_core_body(kind, payload, stamp=stamp, probe=probe)


def _run_task_core_body(kind, payload=None, stamp=True, probe=False):
    """统一入口：按 kind 调用能力。危险/未知能力一律安全拒绝。

    stamp=True（默认）时，成功结果附带 GBT 钢印，声明独立私人框架出处。

    probe=True（O8 · 2026-09-17）时本次调用不写任何审计——这是**写账层唯一的合法豁免口**，
    由调用方逐次声明，不做 kind 级白名单（见 :func:`run_task` 的探针口径）。
    """
    payload = payload or {}
    from . import coding_discipline
    payload = coding_discipline.prepare_payload(kind, payload)
    _probe = bool(probe) or bool(payload.get("_probe"))

    def _audit(event, meta=None):
        """探针调用不写账；非探针调用与改动前逐字节等价。

        ── 2026-09-22 加一笔：**信封归属**（Owner：「五维合一必须给我钉死」）──
        只**记录**"这次调用有没有走在五维合一的信封里"，**不改任何行为**：
        不挡路、不降级、不改返回值。为什么要记：
          `sync_exec.audit_sync()` 量的"无脑操作率"原先只能靠文本配对
          （数 sync_ear…sync_mouth 之间夹了什么），一旦有嵌套或异常就配不准。
          这里由入口**亲笔**记一笔，尺子就从"猜"变成"读"。
        读不到标记（比如 api 被单独 import）时按 False 记，并**不报错** ——
        记录本身绝不能把执行弄崩。
        """
        if _probe:
            return
        m = dict(meta or {})
        try:
            # 2026-09-23 加 `synced_via`：信封归属**要说清是靠什么进的** ——
            # "ctx"=同进程真信封；"env"=继承来的标记（跨进程传播，可伪造，只当传播机制）；
            # None=确实在信封外。不分这一格，"靠继承标记"就会冒充"真在信封里"。
            from .tools.sync_exec import envelope_source, envelope_entry
            _src = envelope_source()
            m["synced"] = _src is not None
            if _src:
                m["synced_via"] = _src
            # 2026-09-23 补：**不在信封里也要记"为什么"**。
            # 病根（本轮实测）：`--no-envelope` 的负对照调用在账本上与"没人开信封"**长得一模一样**
            #   ⇒ 审计视角没法区分"显式负对照"与"真漏了"，只能一律报 PENDING（假警报）。
            # 记法：只要 `envelope_entry()` 有值就写出来（`off`=显式不进 / `auto`/`outer`=在里头）。
            _ent = envelope_entry()
            if _ent:
                m["synced_entry"] = _ent
        except Exception:                                           # noqa: BLE001
            m["synced"] = False
            m["synced_probe_error"] = True
        audit(event, m)

    _audit("call", {"kind": kind, "payload_keys": [k for k in payload if k != "_probe"],
                    "coding_discipline": bool(payload.get("_coding_discipline")),
                    **({"probe": True} if _probe else {})})

    # 2026-09-23 Owner 令：**禁止已全部解开**。
    # 原处是 `if kind in DISABLED_CAPS: return {"status":"denied", ...}`。
    # 解禁前实测：那 11 条**没有实现**（不在 BENIGN_CAPS、api.py 零引用、全仓无实现文件）。
    # ⇒ 旧分支挡的是空气；旧消息还**误导诊断**（让人以为"是策略挡住所以扫不出问题"，
    #    而真相是"根本没做"）。现在让它们走到下面的 unknown_capability 分支，
    #    得到**如实**的"未实现"，而不是"被安全策略禁用"。
    # 名字不丢：`caps_registry.UNIMPLEMENTED_CAPS` 仍登记着它们。
    if kind not in BENIGN_CAPS:
        # 🔴 2026-09-23 磨（三层流畅度）：原来只回一句 `unknown capability` —— **死路**。
        # 现在返回值里带上最近邻候选。纪律不变：**只给建议，不替人改路由** ——
        # 自动改路 = 猜着替人干活，比报错更危险。名字打偏了就应该停下来问人。
        _suggest = _near_cap_names(kind)
        # 🔴 2026-09-23 **为什么账本这一段逐字节不动**（这条是拿一次红灯换来的）：
        # 第一版我把建议也写进了 `_audit(... reason=..., did_you_mean=[...])`，
        # 结果 `test_api_probe.py::test_default_sequence_matches_pre_change_golden` 立刻判红 ——
        # 那条金标比的是**整份 meta 逐字节**（`_canonical` = 全字段 json.dumps），
        # 它守的是「默认行为相对改前不许漂」。那是**绊线，不是绊脚石**。
        # 我本可以像前两次那样"重冻金标"，但那是**第三次**，而且只为一个措辞 ——
        # 重冻次数一多，绊线就废了。更干净的切法：**账本只记稳定、可解析的事实**
        # （`reason_code: "unknown_capability"` 已经足够机器消费），
        # 而"人读的那句话"属于**表现层**，放返回值里。两边各归其位，绊线一根不动。
        _audit("user_error", {
            "kind": kind,
            "reason": "unknown capability",
            "reason_code": "unknown_capability",
            "error_class": "user_error",
            **({"probe": True} if _probe else {}),
        })
        _msg = "unknown capability（没有这个能力位名）"
        if _suggest:
            _msg += "。你是不是要：%s" % " / ".join(_suggest)
        _r = {"status": "error", "kind": kind, "message": _msg,
              "error_class": "user_error"}
        if _suggest:
            _r["did_you_mean"] = _suggest
            _r["how_to_list"] = ("看全部真名：python tools/codex-scripts/omni.py list --domain <域>"
                                 "（域清单：omni.py list）")
        return _r

    from .security import policy as _policy
    decision = _policy.authorize(kind, payload)
    if not decision.get("ok"):
        _audit("denied", {
            "kind": kind,
            "reason": "authorization required",
            "scopes": list(getattr(decision.get("decision"), "scopes", ())),
            "missing": decision.get("missing", []),
            **({"probe": True} if _probe else {}),
        })
        return {
            "status": "denied",
            "kind": kind,
            "denied": True,
            "message": "capability requires human authorization",
            "reason": decision.get("error"),
            "error": decision.get("error"),
            "scopes": list(getattr(decision.get("decision"), "scopes", ())),
            "missing": decision.get("missing", []),
            "how_to_grant": decision.get("how_to_grant"),
            "note": decision.get("note"),
        }

    from . import preflight as _preflight
    force_requested = bool(payload.get("force") or payload.get("_force"))
    force = force_requested and bool(decision.get("trusted"))
    if force_requested and not force:
        _audit("preflight_force_ignored", {
            "kind": kind,
            "reason": "只有主人可信会话可显式要求重复执行",
            **({"probe": True} if _probe else {}),
        })
    try:
        guard = _preflight.before_action(
            kind,
            payload,
            decision=decision.get("decision"),
            force=force,
        )
    except Exception as e:  # noqa: BLE001
        # 感知层故障不能伪造"已检查" —— 但**也不能静默放行有副作用的调用**。
        # ⚠️ F3（2026-09-28 修，原为 fail-open）：这里原来一律 `not_guarded` 后照跑，
        #    理由是"不能阻止原有能力"。可**只有读类**才有这个说法：**要作用域的**调用一旦
        #    跳过守卫，就等于"守卫坏了 = 没人管了" ⇒ 现在按风险分流：
        #      · 读类/安全类：照旧放行（audit 已留 preflight_error，可见）；
        #      · **要作用域**：**按拒处理（fail-closed）**，并说清"是感知层故障、怎么恢复"。
        _audit("preflight_error", {
            "kind": kind,
            "reason": str(e)[:160],
            **({"probe": True} if _probe else {}),
        })
        _scopes = list(getattr(decision.get("decision"), "scopes", ()) or ())
        # ⚠️ 分类用**权威判据** `preflight.is_side_effect()`（它含 11 个状态改变类 + room_* 特例 +
        #    "新动作默认不假定安全"），而不是我自己看作用域 —— 一处真相，别造第二把尺。
        _side = False
        try:
            _side = bool(_preflight.is_side_effect(kind, payload, decision.get("decision")))
        except Exception:                                      # noqa: BLE001
            _side = True                                        # 判不出来 ⇒ 按有副作用算（严）
        if _scopes or _side:
            _audit("preflight_fail_closed", {
                "kind": kind, "scopes": _scopes, "reason": str(e)[:160],
                **({"probe": True} if _probe else {}),
            })
            return {
                "status": "denied",
                "kind": kind,
                "denied": True,
                "message": "preflight unavailable; side-effect action refused",
                "reason": ("感知层（preflight）故障，而这次调用**有副作用** ⇒ **按拒处理**（fail-closed）。"
                           "F3：异常路径不再 fail-open。"),
                "error": "preflight_error: " + str(e)[:120],
                "scopes": _scopes,
                "missing": decision.get("missing", []),
                "how_to_grant": ("先重试一次；若持续故障，请主人检查 `gbt_allinone/preflight.py`"
                                 "（**感知层坏了 ≠ 授权没了**）"),
                "note": "读类调用不受此影响（只留痕）；这条只拦有副作用的。",
            }
        guard = {"status": "not_guarded", "side_effect": False, "degraded": True,
                 "error": str(e)[:160]}

    if guard.get("status") in ("acquired", "reuse", "already_running"):
        _audit("preflight_checked", {
            "kind": kind,
            "fingerprint": guard.get("fingerprint"),
            "status": guard.get("status"),
            "side_effect": True,
            "observation": guard.get("observation"),
            **({"probe": True} if _probe else {}),
        })

    if guard.get("status") == "reuse":
        observation = guard.get("observation") or {}
        _audit("preflight_reuse", {
            "kind": kind,
            "fingerprint": guard.get("fingerprint"),
            "method": observation.get("method"),
            "host": observation.get("host"),
            **({"probe": True} if _probe else {}),
        })
        # R-H170 · 契约补全（**不是把用例放宽**）：幂等命中同样是"这次调用达成了目标"，
        # 旧返回体只有 status/reused、**没有 ok 键** ⇒ 调用方拿不到可判定的结论
        # （用例 `r["result"]["ok"]` 直接 KeyError）。口径：ok=True = 目标达成
        # （无论新做还是复用）；status 保留细分原因。
        result = {
            "ok": True,
            "status": "already_satisfied",
            "reused": True,
            "action": kind,
            "fingerprint": guard.get("fingerprint"),
            "observation": observation,
            "note": observation.get("note") or "目标已满足，未重复执行。",
        }
        body = {"status": "ok", "kind": kind, "result": result}
        if decision.get("scopes"):
            body["authorization"] = {
                "trusted": decision.get("trusted", False),
                "scopes": decision.get("scopes", []),
                "consumed": decision.get("authorizations", []),
            }
            if isinstance(body.get("result"), dict):
                body["result"]["auth_consumed"] = (decision.get("authorizations") or [None])[0]
        if stamp:
            body = stamp_result(body)
        return body

    if guard.get("status") == "already_running":
        running = guard.get("running") or {}
        _audit("preflight_already_running", {
            "kind": kind,
            "fingerprint": guard.get("fingerprint"),
            "running_pid": running.get("pid"),
            "running_since": running.get("started_iso"),
            **({"probe": True} if _probe else {}),
        })
        result = {
            "status": "already_running",
            "reused": True,
            "in_flight": True,
            "action": kind,
            "fingerprint": guard.get("fingerprint"),
            "running": {
                "pid": running.get("pid"),
                "started_at": running.get("started_iso"),
            },
            "observation": guard.get("observation"),
            "note": "同一动作已在执行，本次没有重复动手。",
        }
        body = {"status": "ok", "kind": kind, "result": result}
        if decision.get("scopes"):
            body["authorization"] = {
                "trusted": decision.get("trusted", False),
                "scopes": decision.get("scopes", []),
                "consumed": decision.get("authorizations", []),
            }
            # 人环授权真正被消耗时，把授权 id 透传到能力载荷，供调用方与审计核对
            if isinstance(body.get("result"), dict):
                body["result"]["auth_consumed"] = (decision.get("authorizations") or [None])[0]
        if stamp:
            body = stamp_result(body)
        return body

    lease = guard.get("lease")
    try:
        result = _run_benign(kind, payload, decision)
        if lease is not None:
            lease.finish("ok", {
                "ok": bool(result.get("ok", True)) if isinstance(result, dict) else True,
                "result_status": result.get("status") if isinstance(result, dict) else None,
            })
        _audit("ok", {"kind": kind})
        body = {"status": "ok", "kind": kind, "result": result}
        if decision.get("scopes"):
            body["authorization"] = {
                "trusted": decision.get("trusted", False),
                "scopes": decision.get("scopes", []),
                "consumed": decision.get("authorizations", []),
            }
            if isinstance(body.get("result"), dict):
                body["result"]["auth_consumed"] = (decision.get("authorizations") or [None])[0]
        if stamp:
            body = stamp_result(body)
        return body
    except (ValueError, TypeError, KeyError, EngineError, AutopilotError,
            BrainExecError, LongrunError, SchedError, ThinkLoopError) as e:  # noqa: BLE001
        # 用法/参数类错误（调用方问题：缺参数/坏参数/对象不存在）——不是框架故障，
        # 源头分类记录，selfscan 不再需要判例法区分
        if lease is not None:
            lease.finish("user_error", {"error": str(e)[:160]})
        _audit("user_error", {"kind": kind, "reason": str(e)[:160],
                              **({"probe": True} if _probe else {})})
        # 2026-09-23 加 `reason_code` 透传：能力自己带的机读错误码（`e.code`）一起交出去。
        # 为什么：光有一句中文 message，"没找到"和"找到多处"读起来是同一类错，
        # 调用方只能靠猜。带码之后 `code_patch` / `git_*` 这类能力的失败**可机读**。
        # 通用改动（任何 raise 出带 `.code` 的 ValueError 的能力都受益），不是特例。
        _rc = getattr(e, "code", None)
        return {"status": "error", "kind": kind, "message": str(e),
                "error_class": "user_error",
                **({"reason_code": _rc} if isinstance(_rc, str) and _rc else {})}
    except Exception as e:  # noqa: BLE001
        if lease is not None:
            lease.finish("error", {"error": str(e)[:160]})
        _audit("error", {"kind": kind, "reason": str(e)[:160],
                         **({"probe": True} if _probe else {})})
        # 错误如实暴露（V8 处世理念：不伪造、坏结果如实报）
        return {"status": "error", "kind": kind, "message": str(e)}
