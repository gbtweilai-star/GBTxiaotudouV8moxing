"""GBT小土豆V8 · CLI 交互壳（标准库实现，可运行验证）。"""
import sys

from .api import list_capabilities, run_task
from .store import audit, query_log, log_count
from .caps_registry import UNIMPLEMENTED_CAPS


def cmd_list():
    print("== 可用能力（真能调，可执行）==")
    for c in list_capabilities(filter_dangerous=True):
        print(f"  - {c['name']:<14} [{c['domain']}] {c['desc']}")
    print("== 登记未实现的能力（只有名字、没有实现；禁止已解开，它们**不是**被挡住的）==")
    for k, reason in UNIMPLEMENTED_CAPS.items():
        print(f"  - {k:<16} unimplemented: {reason}")
    print(f"== 审计日志条数: {log_count()} ==")


def cmd_run(kind, payload=None):
    r = run_task(kind, payload)
    print(r)


def cmd_audit():
    for row in query_log(limit=20):
        print(f"  {row['iso']}  {row['event']:<7} {row['meta']}")


def cmd_auth(argv):
    """auth 子命令：grant（人工交互发放）/ status（只读查询）。

    grant 是授权的唯二发放途径之一（另一条是主人手写授权文件）。
    run_task 的任何路由都到不了这里。
    """
    from . import auth_gate
    sub = argv[1] if len(argv) > 1 else "status"
    if sub == "status":
        import json
        print(json.dumps(auth_gate.status(), ensure_ascii=False, indent=2))
        return 0
    if sub == "grant":
        # 解析 --scope / --ttl / --purpose
        scope, ttl, purpose = "osint_private", auth_gate.DEFAULT_TTL_S, ""
        i = 2
        while i < len(argv):
            if argv[i] == "--scope" and i + 1 < len(argv):
                scope = argv[i + 1]; i += 2
            elif argv[i] == "--ttl" and i + 1 < len(argv):
                ttl = int(argv[i + 1]); i += 2
            elif argv[i] == "--purpose" and i + 1 < len(argv):
                purpose = argv[i + 1]; i += 2
            else:
                i += 1
        r = auth_gate.cli_grant_interactive(scope, ttl, purpose)
        import json
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r.get("ok") else 1
    print("用法: gbt_allinone auth [status|grant --scope <s> --ttl <s> --purpose <text>]")
    return 1


def main(argv):
    if not argv or argv[0] in ("list", "-l"):
        cmd_list()
        return 0
    if argv[0] in ("audit", "log"):
        cmd_audit()
        return 0
    if argv[0] == "auth":
        return cmd_auth(argv)
    if argv[0] in ("run", "call"):
        kind = argv[1] if len(argv) > 1 else "health"
        payload = None
        if len(argv) > 2:
            import json
            try:
                payload = json.loads(argv[2])
            except Exception:
                payload = {"text": argv[2]}
        cmd_run(kind, payload)
        return 0
    print("用法: gbt_allinone [list|audit|auth|run <kind> [json]]")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
