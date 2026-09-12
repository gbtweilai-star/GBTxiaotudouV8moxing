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

_BASE = Path(__file__).resolve().parent
_GRANTS = _BASE / "store" / "auth_grants.jsonl"

SCOPES = {
    "osint_private": "OSINT 扫描自有内网/保留地址（一次性授权）",
}
DEFAULT_TTL_S = 600   # 授权默认 10 分钟有效

_OPERATOR_HUMAN = "human-terminal"
_OPERATOR_OWNER = "owner-manual"


def _audit(event, meta):
    try:
        from .store import audit
        audit(event, meta)
    except Exception:
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
    if scope not in SCOPES:
        return {"ok": False, "error": f"未知授权作用域: {scope}"}
    grants = _expire_stale(_load_grants())
    now = time.time()
    for i, g in enumerate(grants):
        if g["scope"] != scope:
            continue
        # 消耗该条（一次性）
        rest = grants[:i] + grants[i + 1:]
        _save_grants(rest)
        _audit("auth_consumed", {"scope": scope, "grant_id": g["id"],
                                  "granted_at": g.get("granted_at"),
                                  "detail": str(detail)[:60]})
        return {"ok": True, "consumed": g["id"],
                "remaining": sum(1 for x in rest if x["scope"] == scope)}
    _audit("auth_denied", {"scope": scope, "detail": str(detail)[:60]})
    return {
        "ok": False,
        "denied": True,
        "error": f"需要人工授权（{scope}）：{SCOPES[scope]}",
        "how_to_grant": [
            "终端运行: python -m gbt_allinone auth grant --scope osint_private --ttl 600",
            "或主人手写 store/auth_grants.jsonl 追加一行（格式见 auth_gate.SCOPES 与 README）",
        ],
        "note": "授权一次性消耗；AI 调用路径无权自行发放",
    }


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
