"""GBT小土豆V8 · 人工授权门（Auth Gate）——被禁能力的硬性人工放行机制。

定位（Owner 定调 2026-09-11）：默认拒绝的能力不给 AI 绕过入口——
要放行只能由人亲手授权，AI 的任何调用路径（run_task / 工作流 / autopilot / 长程任务）
都无权创建授权。

授权的唯二来源：
  1. CLI 交互确认（auth grant 命令，终端人工输入 YES）
  2. 主人手写授权文件（store/auth_grants.jsonl 追加一行，格式严格校验）

授权纪律：
  - 一次性消耗：每次被门拦截的操作消耗一条匹配授权（用完即失效）
  - 过期自毁：过期授权在下次检查时自动清理
  - 全程留痕：发放/校验/消耗全部落审计
  - AI 无权发放：本模块没有任何可供 run_task 调用的"创建授权"入口

当前纳入授权门的作用域：
  osint_private   OSINT 扫描内网/保留地址（原 allow_private 直通开关废止）
"""
import json
import time
from pathlib import Path

from . import _paths

_BASE = Path(__file__).resolve().parent
_GRANTS = _paths.STORE_DIR / "auth_grants.jsonl"

SCOPES = {
    "osint_private": "OSINT 扫描自有内网/保留地址（一次性授权）",
    # 其余 13 项由 security/policy.py 的 SCOPE_DESCRIPTIONS 声明。历史上两次只改 policy、
    # 漏改本表 → 未注册作用域在 check_and_consume* 直接返回"未知授权作用域"，任何授权都
    # 满足不了 → 该能力对非主人调用者永久不可授权。
    #   2026-09-15 补 4 项（browser/desktop/external_llm/process_execute）
    #   2026-09-18 R113 补齐余下 9 项，并把空转的契约测试改成有牙版
    # 契约测试 test_policy_scopes_are_registered（真值取自 policy.SCOPE_DESCRIPTIONS）
    # + 变异负对照 test_policy_scope_registry_has_teeth 保证此处与 policy 不再漂移。
    # 2026-09-19 R-H98 修根源：本作用域此前是**纸面能力**——全仓只有这一行描述字符串，
    # check_and_consume_many 从不读它 ⇒ 主人发了也放行不了任何动作（与"门自己也要被验过"同型）。
    # 现按声明把它做成真的：本次动作缺任意作用域时，可用**一条** owner_control 顶掉**这一次**
    # （一次性消耗，审计记 substituted_for）。它不新增任何发放入口：仍然只能主人亲手发放。
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
    "audio_output": "让本机发声（TTS 合成/播放）或写入音频产物",
    #   2026-09-19 补 1 项（audio_output）—— 由契约测试 test_policy_scopes_are_registered 抓出：
    #   policy 声明了它却没注册，导致 voice.tts 对非主人调用者永久不可授权。
    "audit_read": "读取审计、授权或运行历史",
}
DEFAULT_TTL_S = 600   # 授权默认 10 分钟有效

_OPERATOR_HUMAN = "human-terminal"
_OPERATOR_OWNER = "owner-manual"


# ── 授权门自己的审计降级：**不许无声**（2026-09-22 错报治理 · 第 31 条）──────────
# 本函数原来是 `except: pass` —— 于是「这次授权/拒绝没记上」**无人知道**：
# 授权账本看起来完整、实际缺行。**这是安全门上最重的一种错报。**
# 现在的口径：**仍然不抛**（门不能因为记账失败就崩），但**出声 + 可查**。
# ⚠️ 已知边界（留给主人定夺，不擅自改安全行为）：本仓对**有后果的动作**的既有规矩是
#    「主账本写不进去，就不许把后果动作放过去」（见 file_operation / coze_mail_cap 的同款注释）。
#    这里**没有**改成 fail-closed，因为那会让「store 不可写」直接等于「门永久拒绝一切」，
#    属于**行为变更**，须主人点头。
_AUDIT_DEGRADED = {"count": 0, "reasons": {}, "last_at": None}


def audit_degraded() -> dict:
    """只读：授权门记账降级的计数与原因。

    `count > 0` ⇒ **授权账本可能缺行** —— 这是必须被看见的读数，不是内部细节。
    """
    return {"ok": True, "readonly": True, "count": _AUDIT_DEGRADED["count"],
            "reasons": dict(_AUDIT_DEGRADED["reasons"]),
            "last_at": _AUDIT_DEGRADED["last_at"],
            "note": "count>0 ⇒ 有授权/拒绝事件未落账（授权账本可能缺行）"}


def _audit(event, meta):
    try:
        from .store import audit
        audit(event, meta)
    except Exception as _e:                     # noqa: BLE001
        import time as _t
        _AUDIT_DEGRADED["count"] += 1
        _AUDIT_DEGRADED["last_at"] = round(_t.time(), 3)
        _k = type(_e).__name__
        _AUDIT_DEGRADED["reasons"][_k] = _AUDIT_DEGRADED["reasons"].get(_k, 0) + 1
        if _AUDIT_DEGRADED["reasons"][_k] == 1:      # 同类只首次出声，避免刷屏淹掉真故障
            try:
                import sys as _s
                print("⚠️ auth_gate: 审计降级（%s: %s）⇒ 授权账本可能缺行（累计 %d 次）"
                      % (_k, str(_e)[:120], _AUDIT_DEGRADED["count"]), file=_s.stderr)
            except Exception:                        # noqa: BLE001
                pass


def _load_grants() -> list:
    """读全部授权行（容错：坏行跳过）。"""
    if not _GRANTS.exists():
        return []
    out = []
    for line in _GRANTS.read_text(encoding="utf-8").strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            g = json.loads(line)
            if isinstance(g, dict) and g.get("id") and g.get("scope") in SCOPES:
                out.append(g)
        except Exception:
            continue
    return out


def _save_grants(grants: list):
    _GRANTS.parent.mkdir(parents=True, exist_ok=True)
    _GRANTS.write_text(
        "\n".join(json.dumps(g, ensure_ascii=False) for g in grants) + ("\n" if grants else ""),
        encoding="utf-8")


def _expire_stale(grants: list) -> list:
    now = time.time()
    alive = [g for g in grants if float(g.get("expires_at", 0)) > now]
    n_dead = len(grants) - len(alive)
    if n_dead:
        _save_grants(alive)
        _audit("auth_expired", {"cleaned": n_dead})
    return alive


def status() -> dict:
    """授权门状态：各作用域的可用授权数（只读，不消耗）。"""
    grants = _expire_stale(_load_grants())
    by = {}
    for g in grants:
        by[g["scope"]] = by.get(g["scope"], 0) + 1
    return {
        "ok": True,
        "scopes": {k: {"desc": v, "grants_available": by.get(k, 0)} for k, v in SCOPES.items()},
        "ai_can_grant": False,
        "grant_sources": ["CLI 交互确认（auth grant）", "主人手写 store/auth_grants.jsonl"],
        "note": "授权一次性消耗，默认 10 分钟过期；AI 无权发放",
    }


def check_and_consume(scope: str, detail: str = "") -> dict:
    """校验并消耗一条授权。有匹配的未过期授权 → 消耗并放行；没有 → 拒绝（含人工指引）。

    这是授权门唯一的校验入口，供被门拦截的操作调用。
    """
    # 单作用域版与批量版**同一套语义**（含 owner_control 替代），不再各写一份实现。
    r = check_and_consume_many([scope], detail=detail)
    if not r.get("ok"):
        return r
    consumed = list(r.get("consumed") or [])
    rest = _expire_stale(_load_grants())
    return {"ok": True,
            "consumed": consumed[0] if consumed else None,
            "substituted_for": r.get("substituted_for") or [],
            "remaining": sum(1 for x in rest if x["scope"] == scope)}


def check_and_consume_many(scopes, detail: str = "") -> dict:
    """批量校验并消耗授权（policy 层唯一入口）。

    语义：**全部满足才消耗，缺任意一个则一个都不消耗**——避免出现"消耗了 A 却因为缺 B
    被拒"的半消耗脏状态。成功返回被消耗的授权 id 列表与各作用域剩余数；失败返回缺失
    作用域列表与人工发放指引。
    """
    wanted: list[str] = []
    for scope in list(scopes or []):
        name = str(scope or "").strip()
        if name and name not in wanted:
            wanted.append(name)
    if not wanted:
        return {"ok": True, "consumed": [], "remaining": {}}

    unknown = [s for s in wanted if s not in SCOPES]
    if unknown:
        return {
            "ok": False,
            "denied": True,
            "missing": unknown,
            "error": f"未知授权作用域: {unknown[0]}",
            "note": "授权一次性消耗；AI 调用路径无权自行发放",
        }

    available: dict[str, int] = {}
    for grant in _expire_stale(_load_grants()):
        scope = grant.get("scope")
        available[scope] = available.get(scope, 0) + 1

    missing = [s for s in wanted if available.get(s, 0) <= 0]
    if missing:
        # ── 总控替代（R-H98 修根源）──
        # 声明："一条 owner_control 可替代该次动作所需的全部未授权作用域（一次性）"。
        # 只有**缺件**时才动用它；有对应作用域授权时照旧逐条消耗，总控不被动。
        if available.get("owner_control", 0) > 0:
            current = _expire_stale(_load_grants())
            for index, grant in enumerate(current):
                if grant.get("scope") != "owner_control":
                    continue
                _save_grants(current[:index] + current[index + 1:])
                _audit("auth_consumed", {
                    "scope": "owner_control",
                    "grant_id": grant.get("id"),
                    "granted_at": grant.get("granted_at"),
                    "detail": str(detail)[:60],
                    "substituted_for": list(missing),
                })
                rest = _expire_stale(_load_grants())
                remaining: dict[str, int] = {}
                for g2 in rest:
                    remaining[g2["scope"]] = remaining.get(g2["scope"], 0) + 1
                return {"ok": True, "consumed": [grant.get("id")],
                        "substituted_for": list(missing), "remaining": remaining}
        _audit("auth_denied", {"scope": missing[0], "detail": str(detail)[:60],
                               "missing": missing})
        return {
            "ok": False,
            "denied": True,
            "missing": missing,
            "error": f"需要人工授权（{missing[0]}）：{SCOPES[missing[0]]}",
            "how_to_grant": [
                f"终端运行: python -m gbt_allinone auth grant --scope {missing[0]} --ttl 600",
                "或主人手写 store/auth_grants.jsonl 追加一行（格式见 auth_gate.SCOPES 与 README）",
            ],
            "note": "授权一次性消耗；AI 调用路径无权自行发放",
        }

    consumed: list[str] = []
    for scope in wanted:
        current = _expire_stale(_load_grants())
        for index, grant in enumerate(current):
            if grant.get("scope") != scope:
                continue
            _save_grants(current[:index] + current[index + 1:])
            consumed.append(grant.get("id"))
            _audit("auth_consumed", {"scope": scope, "grant_id": grant.get("id"),
                                     "granted_at": grant.get("granted_at"),
                                     "detail": str(detail)[:60]})
            break

    remaining: dict[str, int] = {}
    for grant in _expire_stale(_load_grants()):
        scope = grant.get("scope")
        remaining[scope] = remaining.get(scope, 0) + 1
    return {"ok": True, "consumed": consumed, "remaining": remaining}


# ── 仅 CLI（人工终端）可达的发放入口 ──

def cli_grant_interactive(scope: str, ttl: int = DEFAULT_TTL_S, purpose: str = "") -> dict:
    """CLI 交互式发放：必须有人在终端亲手输入确认（getpass 防脚本注入）。

    本函数只被 cli.py 的 auth grant 命令调用——run_task 路由里不存在任何通往此处的分支。
    """
    import getpass
    if scope not in SCOPES:
        return {"ok": False, "error": f"未知作用域: {scope}"}
    print(f"[授权请求] 作用域: {scope}")
    print(f"           内容: {SCOPES[scope]}")
    print(f"           有效期: {ttl}s | 一次性消耗 | 发放后将落审计")
    try:
        answer = getpass.getpass("人工确认请输入 YES（直接回车取消）: ")
    except Exception:
        return {"ok": False, "error": "终端不可用——授权只能由人亲手发放"}
    if answer.strip() != "YES":
        _audit("auth_grant_aborted", {"scope": scope})
        return {"ok": False, "error": "未确认，授权取消"}
    return _append_grant(scope, _OPERATOR_HUMAN, ttl, purpose)


def _append_grant(scope: str, operator: str, ttl: int, purpose: str) -> dict:
    g = {
        "id": f"grant-{int(time.time()*1000)}",
        "scope": scope,
        "operator": operator,
        "purpose": str(purpose)[:120],
        "granted_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "expires_at": round(time.time() + max(30, int(ttl)), 3),
    }
    grants = _load_grants()
    grants.append(g)
    _save_grants(grants)
    _audit("auth_granted", {"scope": scope, "operator": operator,
                             "grant_id": g["id"], "ttl": ttl, "purpose": g["purpose"]})
    return {"ok": True, "grant_id": g["id"], "scope": scope,
            "expires_at": g["expires_at"], "one_shot": True}
