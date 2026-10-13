# -*- coding: utf-8 -*-
"""GBT小土豆V8 · DSH MCP 桥（甲方案）——把 `run_task` 唯一门暴露成官方 APP 的第一等 MCP 工具。

## 这是什么

DeepSeek Harness 官方 APP 现读装着一个**未启用**的官方包 `@deepseek-ai/dsh-mcp-client`
（"MCP client bridge: connects to MCP servers and registers their tools on ctx.tools"）。
本件就是那台服务器的**我方一侧**：一个最小 MCP 服务（stdio），
把我们的 **`gbt_allinone.run_task` 唯一门**桥成官方 APP 模型能直接调的原生工具
（`mcp__gbt__*`），不再需要经 `tool-pwsh` 敲 CLI。

## 为什么这样设计（三件，写死防漂移）

1. **单向只读优先**：默认只暴露**读类**工具；写类（`logbook_append`、以及 `run_task`
   的非白名单 kind）**默认整个不出现在工具列表里**。要开写，必须显式
   `--enable-writes`（或环境变量 `GBT_MCP_BRIDGE_WRITES=1`）——没有"默认开一半"。
2. **两道机械闸（读也过）**：
   第①道 = **显式白名单** `READ_KINDS`（kind 不在名单里 → 直接拒，不问策略层）；
   第②道 = **框架自己的策略层** `gbt_allinone.security.policy.evaluate(kind,payload)`
   —— 只要 `scopes` 非空（要票/要写/要出网）就拒，**payload 一级也拦**
   （例：`selfscan` 带 `autofix=true` 会被第②道拦下 —— 框架策略层对它是 fail-open，
   本桥不跟着 fail-open）。两道都过才放行。
3. **身份不继承主人的"全通"**：本桥进程启动时**主动摘掉** `GBT_OWNER_SESSION`
   （除非显式 `--trusted`），因此它在框架眼里是**未受信会话**：
   任何要票的动作都走真票闸（`auth_gate`），没票就如实报缺、给出主人要跑的那一行。
   理由：官方 APP 里的**模型**能调这些工具，模型不该继承主人的一次放行。

## 攻击面（诚实写在这，也得写进 README）

- 本桥把**读类能力面**单向暴露给官方 APP 的模型会话；
- 写类默认不暴露；开了写也是**过票**（没票即拒，不绕过）；
- 凭据：本桥**一个凭据都不需要**（不读密钥服务、不读环境里的钥匙）。
  `dsh-mcp-client` 的 stdio 环境是**清洗过的**（删 `*KEY|PASSWORD|SECRET|TOKEN*` 与 `DSH_*`），
  本桥再往上没有加任何 `env` —— 所以子进程手里没有主人的钥匙。

## 起法（真命令）

    py -3.14 plugins/dsh-mcp-bridge/server.py --repo-root "C:/Users/ADMIN/Desktop/GBT小土豆V8"

MCP 传输 = stdio（换行分隔的 JSON-RPC 2.0，MCP 规范）；**stdout 只许走协议**——
本文件启动就把 `sys.stdout` 换成 stderr，协议帧走另存的原始句柄，
任何库里的 print 都不会污染帧流。

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import traceback
from pathlib import Path

# ── 协议帧专用通道：先抢下原始 stdout，再把 sys.stdout 指向 stderr ──────────────
# 为什么必须第一件事就做：gbt_allinone 的若干模块会用 print 说话；
# stdout 一旦被掺进非协议字节，官方 SDK 的 stdio 传输会直接判协议损坏。
_OUT = sys.stdout
if hasattr(_OUT, "reconfigure"):
    try:
        _OUT.reconfigure(encoding="utf-8", errors="replace", newline="\n")
    except Exception:                                            # noqa: BLE001
        pass
# 🔴 stderr 也要转 utf-8：实测（interop 自证首跑）官方 SDK 把子进程 stderr 原样转给宿主，
#   若本进程 stderr 还是 GBK，中文诊断行会变成乱码（`[gbt-mcp-bridge] ����`）——
#   不影响协议，但"看得见的诊断"就废了。诊断必须读得懂，否则等于没有。
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass
sys.stdout = sys.stderr                     # 此后一切普通 print 都去 stderr


def _log(msg: str) -> None:
    """诊断一律去 stderr（官方 dsh-mcp-client 把服务器 stderr 收进日志，不当作协议）。"""
    try:
        sys.stderr.write("[gbt-mcp-bridge] %s\n" % msg)
        sys.stderr.flush()
    except Exception:                                            # noqa: BLE001
        pass


# ── 默认只读面：白名单（第①道闸）──────────────────────────────────────────────
# 口径：**只放"读了就知道"的位**；每个都写明它读什么。名单是显式的、可被测试钉住的，
# 不是"想想它应该没写吧"。
READ_KINDS = {
    # 框架声带 / 体检（system 域）
    "alerts": "近期异常摘要+根源线索（按能力聚合）",
    "selfscan": "五维自检（路由/模块/存储/审计/桩缺口）——autofix 由第②道拦",
    "health": "系统健康信息（平台/Python/时间）",
    "count_words": "纯计算（联调用）",
    # 授权/审计/账本类（只读；audit_query 要 audit_read 票 ⇒ 没票时如实报缺）
    "auth_gate_status": "各作用域可用授权数（只读）",
    "audit_query": "只读查询统一数据后台日志（要 audit_read 票）",
    # 盘点/卫生/署名（不带 fix/restore 时是纯读）
    "inventory": "全息盘点：视图对照（fix 由第②道拦）",
    "signature_guard": "署名完整性扫描（restore 由第②道拦）",
    "file_hygiene": "文件卫生自检（fix 由第②道拦）",
    # 镜像维度（只读）
    "mirror_status": "镜像/现实指纹与漂移检测",
    "mirror_scan": "镜像维度体检（不写、不晋升）",
    # 脑层与路由（只读）
    "brain_route": "意图→能力动态路由（只回建议，不执行）",
    "brain_health": "五维自检评分",
    # 密钥/端口/接线状态（只读，永不含明文）
    "llm_status": "LLM 网关密钥链配置情况（不调 LLM）",
    "key_gateway": "统一密钥网关读类 op（mint/revoke 等被第②道拦）",
    "multimodal_port": "多模态 Y 字端口读类 op（返回值永不含明文）",
    "genoffice_bridge": "登记桥接线状态（只读）",
    # 触手/契约（读类 op 白名单在框架策略层 `_READ_ONLY_TENTACLE`）
    "tentacle": "触手本体：读类 op（see/read_text/list_windows…）；写类 op 被第②道拦",
    "mcp_tools": "已连接 MCP 服务器的工具契约清单（只读）",
}

# 第②道之外再加一层"payload 键"保险：这些键在对应 kind 上等于写/修/铸。
# 为什么单列：框架策略层对个别 kind 是 fail-open（如 selfscan 的 autofix 没有条目），
# 本桥**不跟着 fail-open**。命中的直接拒，并在返回里点名是哪个键。
FORBIDDEN_PAYLOAD_KEYS = {
    "selfscan": ("autofix",),
    "inventory": ("fix",),
    "signature_guard": ("restore",),
    "file_hygiene": ("fix",),
    "key_gateway": ("key", "secret", "value"),          # 读类 op 不该带"钥匙本体"
    "multimodal_port": ("key", "secret", "value"),
}
# 全局兜底（对任何 kind 都拒的键名）：这些键名的存在就说明调用方想做写类动作。
GLOBAL_FORBIDDEN_KEYS = (
    "delete", "remove", "unlink", "rmdir", "migrate", "promote", "ascend",
    "publish", "deploy", "release", "commit", "push",
)

WRITE_TOOL_NAMES = ("logbook_append",)


def _repo_root_from(here: Path) -> Path | None:
    """从本文件向上找仓根：判据 = 同时存在 `gbt_allinone/__init__.py` 与 `tools/codex-scripts/`。

    为什么要"找"而不是写死：镜像维度里的同一份件位于
    `<仓根>/gbt_allinone/store/mirror_space/dimension/plugins/dsh-mcp-bridge/`，
    向上走同样能命中仓根 ⇒ **镜像排练里跑的是同一段寻根逻辑**，不靠传参特判。
    """
    for cand in [here, *here.parents]:
        if (cand / "gbt_allinone" / "__init__.py").is_file() and \
           (cand / "tools" / "codex-scripts").is_dir():
            return cand
    return None


class Bridge:
    """桥本体：持门、持白名单、持票闸；对 MCP 层只暴露 tools/list 与 tools/call。"""

    def __init__(self, repo_root: Path, enable_writes: bool, trusted: bool,
                 max_chars: int, server_name: str = "gbt") -> None:
        self.repo_root = repo_root
        self.enable_writes = enable_writes
        self.trusted = trusted
        self.max_chars = max_chars
        self.server_name = server_name
        self._api = None
        self._policy = None
        self._auth_gate = None

    # ── 惰性导入（真调时才 import，起服务器本身要快、要能报清错）──

    def api(self):
        if self._api is None:
            if str(self.repo_root) not in sys.path:
                sys.path.insert(0, str(self.repo_root))
            from gbt_allinone import api as _api
            self._api = _api
        return self._api

    def policy(self):
        if self._policy is None:
            if str(self.repo_root) not in sys.path:
                sys.path.insert(0, str(self.repo_root))
            from gbt_allinone.security import policy as _policy
            self._policy = _policy
        return self._policy

    def auth_gate(self):
        if self._auth_gate is None:
            if str(self.repo_root) not in sys.path:
                sys.path.insert(0, str(self.repo_root))
            from gbt_allinone import auth_gate as _ag
            self._auth_gate = _ag
        return self._auth_gate

    # ── 工具目录（读类恒在；写类只在显式开启时出现）──

    def tool_specs(self) -> list:
        tools = [
            {
                "name": "run_task",
                "description": (
                    "GBT小土豆V8 唯一门（gbt_allinone.run_task）· 读类子集。"
                    "kind=能力位名，payload=该位的 JSON 参数。"
                    "默认只放行读类白名单（" + "、".join(sorted(READ_KINDS)) + "）；"
                    "写类/出网/要票的位会被本桥拒绝并回明原因（不静默）。"
                    "要看有哪些能力位，先调 capability_status。"
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "description": "能力位名，如 alerts / mirror_status"},
                        "payload": {"type": "object", "description": "该能力位的参数对象（可省）"},
                    },
                    "required": ["kind"],
                },
                "annotations": {"readOnlyHint": True},
            },
            {
                "name": "alerts",
                "description": "框架声带：近期异常摘要 + 根源线索（只读）。等于 run_task(kind='alerts')。",
                "inputSchema": {
                    "type": "object",
                    "properties": {"last": {"type": "integer", "description": "回看最近多少条审计（默认 500）"}},
                },
                "annotations": {"readOnlyHint": True},
            },
            {
                "name": "selfscan",
                "description": "框架五维自检：路由/模块/存储/审计/桩缺口（只读；不含 autofix）。",
                "inputSchema": {"type": "object", "properties": {}},
                "annotations": {"readOnlyHint": True},
            },
            {
                "name": "capability_status",
                "description": (
                    "能力位目录（我方 240 位的名字/域/状态）。可给 domain 过滤；"
                    "这是静态目录读取，不过 run_task，也不落任何账。"
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domain": {"type": "string", "description": "按域过滤，如 system / pipeline / llm（不填=全量计数）"},
                        "include_desc": {"type": "boolean", "description": "是否带一句话说明（默认 false，省 token）"},
                    },
                },
                "annotations": {"readOnlyHint": True},
            },
        ]
        if self.enable_writes:
            tools.append({
                "name": "logbook_append",
                "description": (
                    "【写类·要票】往工程记录本追加一条（tools/codex-scripts/logbook.py append）。"
                    "会消耗 process_execute + filesystem_write 两张票；没票即拒并给出主人要跑的那一行。"
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": ["scan", "change", "decision", "deliver", "note"]},
                        "what": {"type": "string", "description": "干了什么（一句话，必填）"},
                        "where": {"type": "array", "items": {"type": "string"}, "description": "涉及路径（可省）"},
                        "actor": {"type": "string", "description": "谁做的（建议写模型/会话标识）"},
                    },
                    "required": ["kind", "what"],
                },
                "annotations": {"readOnlyHint": False, "destructiveHint": False},
            })
        return tools

    # ── 闸门 ──

    def _refuse(self, kind: str, why: str, **meta) -> dict:
        out = {
            "ok": False,
            "kind": kind,
            "refused_by": "gbt-mcp-bridge",
            "reason": why,
            "note": "本桥默认只读；写类要么开 --enable-writes，要么让主人在终端发票。",
            "how_to_list": "调 capability_status 看 240 位目录；写类动作请主人在本机跑。",
        }
        out.update(meta)
        return out

    def gate(self, kind: str, payload: dict) -> dict | None:
        """两道闸；返回 None = 放行，否则返回拒件（直接当工具结果回给模型）。"""
        kind = str(kind or "").strip()
        payload = payload if isinstance(payload, dict) else {}
        if not kind:
            return self._refuse(kind, "缺少 kind")

        if kind not in READ_KINDS and not self.enable_writes:
            near = [k for k in READ_KINDS if kind and (kind[:4] in k or k[:4] in kind)][:5]
            return self._refuse(
                kind, "kind 不在本桥的读类白名单里（默认只读）", did_you_mean=near)

        for key in GLOBAL_FORBIDDEN_KEYS:
            if key in payload:
                return self._refuse(kind, "payload 带写类键 %r（全局兜底拦截）" % key)
        for key in FORBIDDEN_PAYLOAD_KEYS.get(kind, ()):
            if key in payload:
                return self._refuse(
                    kind, "payload 带只读位禁止的键 %r（该键等于写/铸/修）" % key)

        try:
            decision = self.policy().evaluate(kind, payload)
        except Exception as exc:                                 # noqa: BLE001
            return self._refuse(kind, "策略层评估异常：%s: %s" % (type(exc).__name__, str(exc)[:120]))
        scopes = list(getattr(decision, "scopes", ()) or ())
        if scopes:
            if not self.enable_writes:
                return self._refuse(
                    kind, "框架策略层判定它要票/要写/要出网（scopes=%s），本桥默认只读" % scopes,
                    required_scopes=scopes)
            # 开了写也不放水：照样走真票闸（auth_gate），没票就报缺。
            res = self.auth_gate().check_and_consume_many(
                scopes, detail="mcp-bridge:%s" % kind)
            if not res.get("ok"):
                return self._refuse(
                    kind, "缺人工授权（票闸拒绝）", required_scopes=scopes,
                    missing=res.get("missing"), how_to_grant=res.get("how_to_grant"))
        return None

    # ── 工具执行 ──

    def call_tool(self, name: str, args: dict) -> dict:
        args = args if isinstance(args, dict) else {}
        if name == "run_task":
            kind = str(args.get("kind") or "").strip()
            payload = args.get("payload") if isinstance(args.get("payload"), dict) else {}
            refusal = self.gate(kind, payload)
            if refusal:
                return self._result(refusal, is_error=True)
            return self._result(self._run(kind, payload))
        if name == "alerts":
            payload = {}
            if isinstance(args.get("last"), int):
                payload["last"] = args["last"]
            refusal = self.gate("alerts", payload)
            if refusal:
                return self._result(refusal, is_error=True)
            return self._result(self._run("alerts", payload))
        if name == "selfscan":
            refusal = self.gate("selfscan", {})
            if refusal:
                return self._result(refusal, is_error=True)
            return self._result(self._run("selfscan", {}))
        if name == "capability_status":
            return self._result(self.capability_status(args))
        if name == "logbook_append":
            if not self.enable_writes:
                return self._result(self._refuse("logbook_append", "写类工具默认不暴露（未开 --enable-writes）"),
                                    is_error=True)
            return self._result(self.logbook_append(args))
        return self._result({"ok": False, "error": "unknown tool: %s" % name}, is_error=True)

    def _run(self, kind: str, payload: dict) -> dict:
        """走唯一门：run_task(kind, payload, safe=True) —— 异常收敛成信封，桥永不炸。"""
        try:
            out = self.api().run_task(kind, payload, safe=True)
        except Exception as exc:                                 # noqa: BLE001
            return {"ok": False, "kind": kind,
                    "error": "%s: %s" % (type(exc).__name__, str(exc)[:200])}
        return out

    def capability_status(self, args: dict) -> dict:
        """静态目录读取（不调 run_task、不落账）：240 位的名字/域/状态 + 绑定计数。"""
        try:
            if str(self.repo_root) not in sys.path:
                sys.path.insert(0, str(self.repo_root))
            from gbt_allinone import caps_tables
            caps = caps_tables.all_caps()
        except Exception as exc:                                 # noqa: BLE001
            return {"ok": False, "error": "读能力目录失败：%s: %s" % (type(exc).__name__, str(exc)[:160])}
        domain = str(args.get("domain") or "").strip()
        include_desc = bool(args.get("include_desc"))
        by_domain: dict = {}
        rows = []
        for cap in caps:
            dom = str(cap.get("domain") or "?")
            by_domain[dom] = by_domain.get(dom, 0) + 1
            if not domain or dom == domain:
                row = {"name": cap.get("name"), "domain": dom, "status": cap.get("status")}
                if include_desc:
                    row["desc"] = cap.get("desc")
                rows.append(row)
        out = {
            "ok": True,
            "total": len(caps),
            "domains": dict(sorted(by_domain.items())),
            "filter": domain or None,
            "count": len(rows),
            "caps": rows,
            "source": "gbt_allinone.caps_tables.all_caps()（静态目录，不含运行态）",
        }
        try:
            bind = json.loads((self.repo_root / "state" / "cap-bindings.json").read_text(encoding="utf-8"))
            out["bindings"] = {"counts": bind.get("counts"), "orphans": bind.get("orphans")}
        except Exception:                                        # noqa: BLE001
            out["bindings"] = {"note": "state/cap-bindings.json 未读到（不影响目录读数）"}
        return out

    def logbook_append(self, args: dict) -> dict:
        """写类：先过票闸（process_execute + filesystem_write），再 spawn 记录本 CLI。

        🔴 口径（写清，免得被读成"绕过唯一门"）：框架里**没有** logbook 能力位，
        故这条不走 run_task；它用的是**同一条票闸**（auth_gate.check_and_consume_many），
        消耗真实票、留 `auth_consumed` 审计。没票 => 拒，并给出主人要跑的那一行。
        """
        kind = str(args.get("kind") or "").strip()
        what = str(args.get("what") or "").strip()
        if kind not in ("scan", "change", "decision", "deliver", "note"):
            return {"ok": False, "error": "kind 必须是 scan/change/decision/deliver/note"}
        if not what:
            return {"ok": False, "error": "what 不许为空"}
        res = self.auth_gate().check_and_consume_many(
            ["process_execute", "filesystem_write"], detail="mcp-bridge:logbook_append")
        if not res.get("ok"):
            return {"ok": False, "error": "缺人工授权",
                    "missing": res.get("missing"), "how_to_grant": res.get("how_to_grant"),
                    "note": "记录本写入口要 process_execute + filesystem_write 两张票"}
        import subprocess
        argv = [sys.executable, str(self.repo_root / "tools" / "codex-scripts" / "logbook.py"),
                "append", "--kind", kind, "--what", what,
                "--actor", str(args.get("actor") or "dsh-app-model")]
        for w in (args.get("where") or []):
            argv += ["--where", str(w)]
        try:
            proc = subprocess.run(argv, cwd=str(self.repo_root), capture_output=True,
                                  text=True, errors="replace", timeout=60)
        except Exception as exc:                                 # noqa: BLE001
            return {"ok": False, "error": "spawn 记录本失败：%s: %s" % (type(exc).__name__, str(exc)[:160]),
                    "consumed": res.get("consumed")}
        return {"ok": proc.returncode == 0, "exit_code": proc.returncode,
                "stdout": (proc.stdout or "")[-2000:], "stderr": (proc.stderr or "")[-500:],
                "consumed": res.get("consumed")}

    def _result(self, payload, is_error: bool = False) -> dict:
        """把任意结果压成 MCP 工具结果（文本块）——过大就截，并**明说截了**。"""
        try:
            text = json.dumps(payload, ensure_ascii=False, default=str)
        except Exception:                                        # noqa: BLE001
            text = repr(payload)
        truncated = False
        if len(text) > self.max_chars:
            text = text[: self.max_chars] + "…（本桥截断：原始 %d 字符）" % len(text)
            truncated = True
        out = {"content": [{"type": "text", "text": text}], "isError": bool(is_error)}
        if truncated:
            out["content"][0]["text"] += "\n[gbt-mcp-bridge] 结果超长已截断（上限 %d 字符）" % self.max_chars
        return out


# ── MCP 协议层（stdio · 换行分隔 JSON-RPC 2.0）────────────────────────────────

def _send(msg: dict) -> None:
    _OUT.write(json.dumps(msg, ensure_ascii=False, default=str))
    _OUT.write("\n")
    _OUT.flush()


def _reply(mid, result=None, error=None) -> None:
    msg = {"jsonrpc": "2.0"}
    if mid is not None:
        msg["id"] = mid
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result if result is not None else {}
    _send(msg)


PROTOCOL_FALLBACK = "2024-11-05"


def serve(bridge: Bridge) -> int:
    _log("起服务器 · repo_root=%s · writes=%s · trusted=%s" % (
        bridge.repo_root, bridge.enable_writes, bridge.trusted))
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception as exc:                                 # noqa: BLE001
            _log("非 JSON 帧（跳过）：%s: %s" % (type(exc).__name__, str(exc)[:120]))
            continue
        if not isinstance(msg, dict):
            continue
        mid = msg.get("id")
        method = str(msg.get("method") or "")
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        is_notification = mid is None
        try:
            if method == "initialize":
                want = str(params.get("protocolVersion") or "")
                _reply(mid, {
                    "protocolVersion": want or PROTOCOL_FALLBACK,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "gbt-mcp-bridge", "version": "0.1.0"},
                    "instructions": (
                        "GBT小土豆V8 桥：默认只读。run_task 走我们的唯一门（读类白名单 + "
                        "框架策略层双闸）。写类工具默认不出现；要写得主人在本机发票。"
                    ),
                })
            elif method in ("notifications/initialized", "initialized"):
                pass                                             # 通知，无回
            elif method == "ping":
                _reply(mid, {})
            elif method == "tools/list":
                _reply(mid, {"tools": bridge.tool_specs()})
            elif method == "tools/call":
                name = str(params.get("name") or "")
                args = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
                _reply(mid, bridge.call_tool(name, args))
            elif method in ("resources/list", "prompts/list"):
                key = "resources" if method.startswith("resources") else "prompts"
                _reply(mid, {key: []})
            elif method in ("logging/setLevel", "resources/templates/list"):
                _reply(mid, {})
            else:
                if not is_notification:
                    _reply(mid, error={"code": -32601, "message": "method not found: %s" % method})
        except Exception as exc:                                 # noqa: BLE001
            _log("处理 %s 异常：%s\n%s" % (method, exc, traceback.format_exc()[:1200]))
            if not is_notification:
                _reply(mid, error={"code": -32603, "message": "internal error: %s" % str(exc)[:200]})
    _log("stdin 结束，退出")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="GBT小土豆V8 · DSH MCP 桥（甲方案）")
    ap.add_argument("--repo-root", default="", help="仓根（默认向上找 gbt_allinone/__init__.py）")
    ap.add_argument("--enable-writes", action="store_true",
                    help="暴露写类工具（logbook_append / 非白名单 kind）——默认关")
    ap.add_argument("--trusted", action="store_true",
                    help="保留 GBT_OWNER_SESSION（默认主动摘掉，走真票闸）")
    ap.add_argument("--max-chars", type=int, default=20000, help="单次工具结果字符上限")
    ap.add_argument("--server-name", default="gbt", help="（仅记录用）MCP serverName")
    a = ap.parse_args(argv)

    root = Path(a.repo_root).resolve() if a.repo_root else None
    if root is None:
        env_root = os.environ.get("GBT_MCP_BRIDGE_REPO_ROOT")
        root = Path(env_root).resolve() if env_root else None
    if root is None or not (root / "gbt_allinone" / "__init__.py").is_file():
        found = _repo_root_from(Path(__file__).resolve().parent)
        if found is not None:
            root = found
    if root is None or not (root / "gbt_allinone" / "__init__.py").is_file():
        _log("找不到仓根（gbt_allinone/__init__.py）—— 用 --repo-root 显式给")
        return 2

    # 身份纪律：默认摘掉主人的"全通"标记 —— 模型在官方 APP 里调这些工具时，
    # 不该继承主人某一次的放行；要票的动作走真票闸。
    if not a.trusted:
        if os.environ.pop("GBT_OWNER_SESSION", None) is not None:
            _log("已摘除 GBT_OWNER_SESSION（默认未受信；--trusted 可保留）")
        os.environ["GBT_MCP_BRIDGE_UNTRUSTED"] = "1"

    enable_writes = bool(a.enable_writes) or \
        str(os.environ.get("GBT_MCP_BRIDGE_WRITES") or "").strip() in ("1", "true", "yes", "on")
    bridge = Bridge(root, enable_writes=enable_writes, trusted=bool(a.trusted),
                    max_chars=max(1000, int(a.max_chars)), server_name=a.server_name)
    return serve(bridge)


if __name__ == "__main__":
    sys.exit(main())
