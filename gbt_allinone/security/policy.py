# gbt-capability: dynamic-import
"""能力风险策略：保留全部能力，给高风险动作增加主人会话与一次性授权边界。

策略原则：
- 默认读取、健康检查、公开网络抓取继续直接可用；
- 命令执行、文件写入、远程接管、发布晋升、私有网络、浏览器操控、设备写入、
  外部 LLM 数据交换等动作，在主人本机会话中直接执行，在未受信路径中必须消耗人工授权；
- 授权只由 CLI 交互或主人手写授权文件发放，run_task 本身不能创建授权。
"""
from __future__ import annotations

import contextlib
import contextvars
import os
import urllib.parse
from dataclasses import dataclass, field
from typing import Iterator

from . import net_guard

_TRUSTED_OWNER = contextvars.ContextVar("gbt_trusted_owner", default=False)

SCOPE_DESCRIPTIONS = {
    "owner_control": "主人总控授权：一条可替代该次动作所需的全部未授权作用域（一次性消耗）",
    "process_execute": "启动进程、执行命令或连接 MCP/终端服务器",
    "filesystem_write": "写入、移动、删除或自动整理文件",
    "remote_device": "启动/停止远程设备中继或外部接管通道",
    "deploy_publish": "部署、晋升、回滚或写入生产交付区",
    "network_private": "访问本机、内网、保留地址或非标准端口",
    "browser_control": "操控系统浏览器或自动化浏览器执行点击/输入",
    "desktop_control": "调用桌面触手的输入、鼠标、键盘与窗口控制能力",
    "device_control": "连接、写入或控制蓝牙及其他外部设备",
    "external_llm": "把当前任务数据发送到外部大模型服务",
    "data_export": "把数据发送到外部服务或持久化到框架外",
    "privacy_read": "读取屏幕、摄像头、麦克风或隐私载体",
    "audit_read": "读取审计、授权或运行历史",
    "audio_output": "让本机发声（TTS 合成/播放）或写入音频产物",
}

_READ_ONLY_TENTACLE = {
    "", "status", "eye", "see", "vision_snapshot", "screen_size", "screenshot_diff",
    "read_text", "list_windows", "process_list", "see_active_window", "window_list",
    "window_info", "active_window", "monitor", "detect", "ocr", "manifest",
}

_READ_ONLY_DC_TOOLS = {
    "get_config", "get_prompts", "read_file", "read_multiple_files", "list_directory",
    "get_file_info", "list_processes", "list_sessions", "get_usage_stats",
    "get_recent_tool_calls", "get_more_search_results", "list_searches",
}

_READ_ONLY_NATIVE_BROWSER_ACTIONS = {
    "status", "list_tabs", "get_title", "get_url", "get_text", "dom_query",
    "get_cookies", "intercept_events", "intercept_status",
}

_DC_WRITE_TOOLS = {
    "set_config_value", "write_file", "write_pdf", "create_directory", "move_file",
    "edit_block",
}

_DC_PROCESS_TOOLS = {
    "start_process", "read_process_output", "interact_with_process", "force_terminate",
    "kill_process", "start_search", "stop_search",
}


@dataclass(frozen=True)
class PolicyDecision:
    kind: str
    risk: str = "low"
    scopes: tuple[str, ...] = ()
    action: str = ""
    allow_private: bool = False
    details: dict = field(default_factory=dict)

    @property
    def restricted(self) -> bool:
        return bool(self.scopes)


def owner_session() -> contextlib.AbstractContextManager:
    """标记主人的本地可信会话；仅 CLI、GUI 和已鉴权本地服务应进入。"""
    return _owner_session()


@contextlib.contextmanager
def _owner_session() -> Iterator[None]:
    token = _TRUSTED_OWNER.set(True)
    try:
        yield
    finally:
        _TRUSTED_OWNER.reset(token)


def is_trusted() -> bool:
    if _TRUSTED_OWNER.get():
        return True
    return (os.environ.get("GBT_OWNER_SESSION") or "").strip() in ("1", "true", "yes", "on")


def _url_params(payload: dict) -> list[str]:
    return [str(payload.get(k) or "") for k in ("url", "target", "base_url", "repo") if payload.get(k)]


def _needs_private_network(payload: dict) -> bool:
    for raw in _url_params(payload):
        if not raw:
            continue
        parsed = raw if "://" in raw else "https://" + raw
        try:
            net_guard.validate_url(str(parsed), allow_private=False)
        except net_guard.NetworkGuardError as exc:
            text = str(exc)
            if "非公网地址" in text or "端口" in text:
                return True
    return False


def evaluate(kind: str, payload: dict | None = None) -> PolicyDecision:
    p = dict(payload or {})
    op = str(p.get("op") or p.get("action") or p.get("method") or "").lower()
    scopes: list[str] = []
    risk = "low"
    action = op or kind
    allow_private = False
    details: dict = {}

    def add(*items: str) -> None:
        nonlocal risk
        for item in items:
            if item and item not in scopes:
                scopes.append(item)
        if any(x in scopes for x in (
            "remote_device", "process_execute", "filesystem_write", "deploy_publish",
            "network_private", "browser_control", "desktop_control", "device_control",
            "external_llm", "data_export",
        )):
            risk = "high"
        elif scopes:
            risk = "medium"

    if kind == "coze_mail":
        # R104 · 刀一（通信域）：对外发信 / 在自有账号下立地址 = data_export（收紧）；
        # status/inbox/search/read/mark/draft 是只读侧，不收口 —— 与仓库既有
        # 「写操作收紧、读不收紧」口径一致。
        if op in ("send", "reply", "register"):
            add("data_export")
    if kind == "create":
        # R104 · 刀二（创作出口）：写进 outputs/ = filesystem_write（收紧）；
        # status/configure/intent/output 不收口 —— 文本出口本刀**未接线**、不出网，
        # 故不挂 data_export（真接线那一刀再单独收紧）。
        if op == "write":
            add("filesystem_write")
    if kind == "mcp_connect":
        add("process_execute")
    elif kind == "mcp_call":
        add("process_execute")
    elif kind == "desktop_commander":
        op = op or "status"
        if op == "connect":
            add("process_execute")
        elif op in ("remote_start", "remote_stop"):
            add("remote_device")
        elif op == "call":
            tool = str(p.get("tool") or "")
            details["tool"] = tool
            if tool in _DC_WRITE_TOOLS:
                add("filesystem_write")
            elif tool in _DC_PROCESS_TOOLS:
                add("process_execute")
            elif tool not in _READ_ONLY_DC_TOOLS:
                add("desktop_control")
    elif kind == "tentacle":
        if op not in _READ_ONLY_TENTACLE:
            add("desktop_control")
    elif kind == "browser":
        op = op or "open"
        if op in ("native", "deep", "controller", "cdp"):
            action = str(p.get("action") or p.get("cmd") or "status").lower()
            if action not in _READ_ONLY_NATIVE_BROWSER_ACTIONS:
                add("browser_control")
            if action == "screenshot":
                add("filesystem_write")
            if action == "get_cookies" and bool(p.get("include_values")):
                add("privacy_read")
            if _needs_private_network(p):
                add("network_private")
                allow_private = True
        elif op == "fetch":
            if _needs_private_network(p):
                add("network_private")
                allow_private = True
        elif op in ("open", "search"):
            # R-H178 · 人类视角执行律：**打开浏览器 / 搜索 = 人的基本可逆动作 ⇒ 免卡**。
            # 旧口径把 open/search 落进最后的 else，与"读页面（native/fetch）免卡"自相矛盾；
            # 判据只有一条：**人打开电脑工作时，会卡自己这一步吗？** 不会 ⇒ 降级。
            # 保留的唯一闸：**内网判定**（访问本机/内网/保留地址仍要 network_private）。
            if _needs_private_network(p):
                add("network_private")
                allow_private = True
        elif op == "automate":
            add("browser_control")
            if _needs_private_network(p):
                add("network_private")
                allow_private = True
        else:
            add("browser_control")
            if _needs_private_network(p):
                add("network_private")
                allow_private = True
    elif kind == "osint_scan":
        if _needs_private_network(p):
            add("osint_private")
            allow_private = True
    elif kind == "file_hygiene":
        if bool(p.get("fix")):
            add("filesystem_write")
    elif kind == "inventory":
        if bool(p.get("fix")):
            add("filesystem_write")
    elif kind == "signature_guard":
        if bool(p.get("restore")):
            add("filesystem_write")
    elif kind in ("pipeline_submit", "pipeline_rollback", "mirror_ascend", "mirror_rewind",
                  "one_key_deploy", "mirror_release"):
        add("deploy_publish")
        if kind in ("one_key_deploy", "mirror_release"):
            add("process_execute", "filesystem_write")
    elif kind == "mirror_plan":
        if p.get("plan"):
            add("filesystem_write")
    elif kind == "mirror_simulate":
        add("filesystem_write")
    elif kind == "mirror_parity":
        add("filesystem_write")
    elif kind == "mirror_rehearse":
        add("process_execute", "filesystem_write")
    elif kind == "mirror_shape":
        if p.get("path"):
            add("filesystem_write")
    elif kind in ("room_create", "room_enter", "room_shape", "room_snapshot",
                  "room_observe", "room_gate", "room_namespace"):
        add("filesystem_write")
    elif kind == "room_release":
        add("deploy_publish", "filesystem_write")
    elif kind in ("room_plan", "room_simulate", "room_parity"):
        if kind != "room_plan" or p.get("plan"):
            add("filesystem_write")
    elif kind == "room_rehearse":
        add("process_execute", "filesystem_write")
    elif kind == "collab_open":
        add("remote_device", "filesystem_write")
    elif kind == "collab_close":
        add("filesystem_write")
    elif kind == "collab_server_start":
        add("process_execute", "network_private", "remote_device")
        allow_private = True
    elif kind == "collab_server_stop":
        add("process_execute", "remote_device")
    elif kind == "peer_register":
        add("remote_device", "filesystem_write")
    elif kind == "peer_request":
        add("remote_device", "network_private", "data_export")
        allow_private = True
    elif kind == "deploy_queue":
        if op == "tick" or op == "submit":
            add("deploy_publish")
    elif kind == "devour_github":
        add("data_export", "filesystem_write")
    elif kind == "devour_pulse":
        add("data_export", "filesystem_write", "external_llm")
    elif kind in ("llm_chat", "sec_llm", "autopilot", "think_loop"):
        add("external_llm")
    elif kind == "life":
        op = op or "status"
        write_ops = {"record", "event", "remember", "daily", "export",
                     "export_obsidian", "vault", "ingest", "import_sources",
                     "sync_sources"}
        if op in write_ops:
            add("filesystem_write")
        elif op == "reflect" and bool(p.get("save")):
            add("filesystem_write")
        elif op in ("chapter", "commitment", "habit"):
            action = str(p.get("action") or "list").lower()
            if action not in ("", "list", "status"):
                add("filesystem_write")
    elif kind == "bluetooth":
        if op not in ("status", "scan", "list"):
            add("device_control")
    elif kind == "bt_control":
        if op not in ("status", "scan", "list"):
            add("device_control")
    elif kind == "vision":
        if op not in ("status", "analyze_file"):
            add("privacy_read")
    elif kind == "voice":
        if p.get("out"):
            add("filesystem_write")
        if (op or "tts") in ("tts", "speak", None):
            # 风哥 2026-09-18 拍板：把「本机发声」这条隐式规则**显式化**（进注册表）。
            add("audio_output")
    elif kind == "audit_query":
        add("audit_read")
    elif kind == "notion":
        op = op or "status"
        # R-H178 · 人类视角执行律：**查 ≠ 送** —— status/recent/search/page 是只读查询 ⇒ 免卡。
        # 其余动作（含将来新增的写入/未知动作）一律 fail-closed 挂 data_export。
        if op not in ("status", "recent", "search", "page"):
            add("data_export")
    elif kind == "codex_chat":
        # 真 Codex 通道：会驱动本机代理进程与外部模型服务。
        add("process_execute", "external_llm")
    elif kind in ("codex_thread_new", "codex_turn_send", "codex_interrupt"):
        # R-H99c（由一处恒真断言占位挖出来的真洞）：这三条在注册表里一直写着
        # "官方 Codex 写操作（需 process_execute 授权）"，**策略层却从没给它们挂过作用域** ——
        # 实测改前：`policy.evaluate(...)` 三个都返回 scopes=[] · restricted=False
        # ⇒ 未授权路径可以直接开线程 / 发回合 / 打断，声明与执行漂移（同 R-H98 那个病根）。
        # turn_send 还会把文本送到外部模型，故与 codex_chat 同口径加 external_llm。
        add("process_execute")
        if kind == "codex_turn_send":
            add("external_llm")
    elif kind == "codex_models":
        add("external_llm")

    elif kind == "prompt_bridge":
        # 第一刀纯本地模板（stdlib-only，不接外部模型）：三个动作零作用域。
        # 未列出的动作一律 fail-closed —— 将来接外部模型时必须显式加 external_llm。
        op = op or "compile"
        if op not in ("compile", "passthrough", "status"):
            add("external_llm", "data_export")
    elif kind == "voice_orchestra":
        # 语音技能中枢（2026-09-18 接进能力库）：三个只读动作 list/pipeline/status 读的是
        # **仓内常量表**（voice_orchestra.VOICE_SKILL_REGISTRY），不碰数据面、不外发、不落盘，
        # 所以显式声明「零作用域」。未列出的动作一律按「可能外发/落盘」处理 —— fail-closed，
        # 免得将来加 tts/clone 动作时被静默放行（同族坑：作用域未注册）。
        op = op or "list"
        if op not in ("list", "pipeline", "status"):
            add("data_export", "external_llm")
    elif kind == "ledger_note":
        # R-H600 立 · **R-H620 改**（主人 2026-09-21 明确要求「切过去」）。
        #
        # 原口径：只有 status/rules/preview 零作用域，**唯一写原语 APPEND 挂 filesystem_write**。
        # 后果（实测）：`run_task('ledger_note', {'op':'append', ...})` 在**非可信会话**里一律
        # `denied`，于是这条「登记」的路永远走不进万能插 —— 而**同一个效果**在仓里早就
        # 用脚本直接写盘（.scratch/_rhNNN_append.py）达成 ⇒ 挂闸并没有真的挡住那次写入，
        # 只是把「走万能插」这条路堵死了（**闸挂了，路没通**）。
        #
        # 现口径：**对齐盘上 `stigmergy` 的先例**（那一族也是「只追加」的能力，policy 里
        # 没有条目 ⇒ 零作用域）。理由：本能力位的写面**窄到只剩一条**——
        #   · 目标**固定**（只能写那一份台账；**调用方传不了路径**）
        #   · **只追加**（目标末尾必须是换行，否则拒写；不修不补）
        #   · **单物理行** + **禁半角双引号** + **行首形状** + **幂等** + **缺前驱拒写**
        # ⇒ 它不是通用文件写入，是**一条有七道闸的追加口**。
        #
        # 🔴 fail-closed 保留：**未列出的动作**（含将来新增的写动作）**仍然挂**
        #    `filesystem_write` —— 免得将来加了别的写动作被静默放行
        #    （同族坑：作用域未注册）。
        #
        # 注：本规则**不动任何别的能力**；可信主人会话（CLI/GUI/已鉴权本地服务）
        # 照旧走 is_trusted() 直接放行。
        op = op or "status"
        if op not in ("status", "rules", "preview", "append"):
            add("filesystem_write")

    if kind == "code_patch":
        # 2026-09-23 新接：**改代码**从此过门。
        # 口径与 `ledger_note` 同族但方向相反：那边是"只有 APPEND 写"，这边是
        # **"只有 apply / rollback 写"**（dry_run 是默认，零作用域）。
        # 🔴 fail-closed：**不写白名单、写黑名单** —— 只把三个只读别名放行，
        # 其余任何 op（含将来新增的写动作）**一律挂 filesystem_write**。
        if op not in ("", "dry_run", "dry", "preview", "diff"):
            add("filesystem_write")

    if kind == "git_read":
        # 2026-09-23：版本库**只读面**（status/diff/log/show/branch_list/stash_list）。
        # **显式空挂**：写在这里是为了让"它零作用域"是一条**看得见的决定**，
        # 而不是"文件里没提它所以碰巧没挂"。将来谁往里加写 op，必须同时改这一行。
        pass

    if kind == "git_write":
        # 2026-09-23：版本库**写面**（stage/commit）。
        # **永远挂**，不按 op 判 —— 拆成独立能力位就是为了让这条判据平凡正确，
        # 没有"这个 op 算不算写"的判断题，也就没有判错的机会。
        add("filesystem_write")

    if kind == "pipeline_submit" and (p.get("review") or int(p.get("refine_rounds", 0) or 0) > 0):
        add("external_llm")

    # ── 授权红队内核（Owner 2026-09-25 令：黑客能力多维度全覆盖，使用需人工授权）──
    # 口径与全仓一致：**纯离线分析不挂作用域；碰隐私载体 / 设备 / 写盘 / 出网的一律挂**。
    # （Owner 同日的授权分级令让这些"日常技术动作"变成 TTL 内可多次用的时段授权 ——
    #   否则开一次输入记录就要回终端敲一次 YES，能力等于不可用。见 auth_gate.ONE_SHOT_SCOPES。）
    elif kind == "redteam_recon":
        if op == "creds":                       # 只有翻凭据落点那条碰隐私载体
            add("privacy_read")
    elif kind == "pentest":
        if op == "verify":                      # plan 只出计划不碰目标
            add("network_private")
        elif op in ("authorize", "revoke"):     # 授权清单是写盘
            add("filesystem_write")
    elif kind == "keylogger":
        if op in ("start", "stop", "purge"):
            add("privacy_read", "process_execute", "filesystem_write")
        else:                                   # status / dump 只读采集结果
            add("privacy_read")
    elif kind == "screen_sniff":
        if op in ("capture", "purge"):
            add("privacy_read", "filesystem_write")
        else:
            add("privacy_read")
    elif kind == "device_takeover":
        if op == "take":
            add("device_control")
    elif kind == "remote_domain":
        if op in ("add", "revoke"):
            add("remote_device", "filesystem_write")
    elif kind == "credential_steal":
        add("privacy_read")
    elif kind == "data_hijack":
        if op in ("baseline", "verify"):
            add("filesystem_write")
        else:
            add("privacy_read")
    # 外部 CLI 智能体（2026-09-25 补齐接线）：status/version 只探 PATH，不挂；
    # 真调 exec 是把任务数据送出去 + 起进程，两条都挂。
    elif kind in ("claude_code", "codebuddy", "ul_tars_desktop"):
        if op in ("exec", "run", "chat", "ask"):
            add("process_execute", "external_llm")
    # social_eng / paywallbuster / asset_vault_freeze / onboarding_gate：
    # 纯离线判定 + 只读体检，与 sec_surface / sec_scan 同类 —— **不挂作用域**。

    return PolicyDecision(kind=kind, risk=risk, scopes=tuple(scopes),
                          action=action, allow_private=allow_private, details=details)


def authorize(kind: str, payload: dict | None = None) -> dict:
    """评估并授权。可信主人会话直接放行；其他路径按作用域消耗人工授权。"""
    decision = evaluate(kind, payload)
    if not decision.restricted or is_trusted():
        return {
            "ok": True,
            "trusted": is_trusted(),
            "decision": decision,
            "scopes": list(decision.scopes),
            "authorizations": [],
        }
    from .. import auth_gate
    result = auth_gate.check_and_consume_many(
        decision.scopes, detail=f"{kind}:{decision.action}")
    if not result.get("ok"):
        return {
            "ok": False,
            "trusted": False,
            "decision": decision,
            "scope": result.get("missing", [None])[0],
            "missing": result.get("missing", []),
            "denied": True,
            "error": result.get("error"),
            "how_to_grant": result.get("how_to_grant"),
            "note": result.get("note"),
        }
    return {
        "ok": True,
        "trusted": False,
        "decision": decision,
        "scopes": list(decision.scopes),
        "authorizations": result.get("consumed") or result.get("authorizations") or [],
        # R-H98：总控替代要**看得见**——缺件时用的那一条 owner_control 在此如实透出，
        # 免得"用总控顶掉的"和"逐条授权的"在调用方眼里长得一模一样。
        "substituted_for": list(result.get("substituted_for") or []),
    }


def describe() -> dict:
    return {
        "trusted_owner_session": is_trusted(),
        "scope_descriptions": dict(SCOPE_DESCRIPTIONS),
        "policy": "主人会话直通；未受信调用对受限动作消耗一次性人工授权；不删除任何能力",
    }


def safe_url_parts(url: str) -> dict:
    parsed = urllib.parse.urlsplit(url)
    return {"scheme": parsed.scheme, "host": parsed.hostname, "port": parsed.port}
