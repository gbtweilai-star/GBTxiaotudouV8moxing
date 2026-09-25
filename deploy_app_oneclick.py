# -*- coding: utf-8 -*-
"""GBT小土豆V8 · APP 成品一次性部署（主人一键入口）

用途：把 `delivery/桌面数字人GBT小土豆`（APP 成品源）用**统一接口（万能插口径）**的一次性部署
      能力 `one_key_deploy` 真发一次。按 Owner 2026-09-19 红线，写生产/镜像的动作一律走
      `run_task`，且**授权只能主人在终端亲手发放** —— 所以本脚本只做三件事：

        ① 逐条向主人索取三个作用域的一次性授权（终端里亲手输入 YES，getpass 防脚本注入）
        ② 三个都拿到后，走 api.run_task 发一次 `one_key_deploy`
        ③ 原样打印结果（ok/version/files 或 blocked/missing），成功与否都如实报

落点（必须显式声明，谁都不许默认堆进生产）：
  · 默认 `--production`：into_global_production=true —— 真写全局生产面（就是"上线"）
  · 想只在隔离房间排练：python deploy_app_oneclick.py --room desktop-human-app

用法（在仓库根目录，主人自己的终端里跑）：
    py -3.10 deploy_app_oneclick.py --check          # 只看授权现状（只读，不消耗）
    py -3.10 deploy_app_oneclick.py                  # 授权 + 一次性部署上线（默认生产）
    py -3.10 deploy_app_oneclick.py --room desktop-human-app

纪律：
  · 本脚本**不写授权文件**、不设 GBT_OWNER_SESSION、不调模块函数绕过门。
  · 任何一个作用域没拿到 YES ⇒ 立刻停手，一步都不写。
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TARGET = str(ROOT / "delivery" / "桌面数字人GBT小土豆")
SCOPES = ("deploy_publish", "process_execute", "filesystem_write")
MASTER_SCOPES = ("owner_control",)   # R-H98：总控一条顶掉该次动作所需的全部未授权作用域
DEFAULT_TTL = 600
LOG = ROOT / ".scratch" / "_deploy_app_last.json"
REPORT = ROOT / "部署结果.md"


def _log(entry: dict) -> None:
    """把每一次运行的结果落盘——窗口是开在主人桌面上的，这边要能事后读回真相。"""
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), **entry}
        LOG.write_text(json.dumps(entry, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"（结果日志写不进去：{exc}）")


def _write_report(landing: str, view: dict, steps=None) -> None:
    """把结果写成一份给人看的交代（主人不用问我，也不用翻 JSON）。"""
    ok = bool(view.get("ok"))
    lines = [
        "# APP 一次性部署 · 结果",
        "",
        f"- 时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 落点：{landing}",
        f"- 目标：`{TARGET}`",
        f"- 结果：**{'已晋升上线 ✔' if ok else '未晋升 ✖'}**",
    ]
    if view.get("version"):
        lines.append(f"- 版本号：v{view['version']}")
    if view.get("files"):
        lines.append(f"- 文件数：{view['files']}")
    if view.get("elapsed_s") is not None:
        lines.append(f"- 耗时：{view['elapsed_s']} s")
    if not ok:
        for key, label in (("status", "状态"), ("reason", "原因"),
                           ("error", "错误"), ("missing", "缺授权"),
                           ("how_to_grant", "怎么放行")):
            if view.get(key):
                lines.append(f"- {label}：{view[key]}")
    if steps:
        lines += ["", "## 步骤", "", "```", json.dumps(steps, ensure_ascii=False, indent=1), "```"]
    lines += ["", "> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属", ""]
    try:
        REPORT.write_text("\n".join(lines), encoding="utf-8")
        print(f"（结果交代已写好：{REPORT}）")
    except Exception as exc:  # noqa: BLE001
        print(f"（结果交代写不进去：{exc}）")


def show_status() -> dict:
    from gbt_allinone import auth_gate
    st = auth_gate.status()
    avail = {k: v["grants_available"] for k, v in st["scopes"].items() if v["grants_available"]}
    print(f"授权现状：可用授权 {avail or '（全部为 0）'}")
    print(f"AI 能否自行发放：{st['ai_can_grant']}")
    return st


def gather_grants(ttl: int = DEFAULT_TTL, master: bool = False) -> list:
    """逐条向主人索取授权；任何一条没确认就返回空列表（调用方必须停手）。"""
    from gbt_allinone import auth_gate
    got = []
    wanted = MASTER_SCOPES if master else SCOPES
    for idx, scope in enumerate(wanted, 1):
        # 大声说清"要打 YES、回车=取消"——实测两次被回车误杀（10:43:50 / 10:50:07）
        print()
        print(f"▶▶ 第 {idx}/{len(wanted)} 条：{scope}")
        print("   ↓↓↓ 下一行请输入三个字母 YES 再按回车；**直接回车 = 取消，前功尽弃** ↓↓↓")
        r = auth_gate.cli_grant_interactive(scope, ttl, purpose="APP 成品一次性部署（deploy_app_oneclick）")
        if not r.get("ok"):
            print(f"✖ {scope} 未授权：{r.get('error')}")
            return []
        print(f"✔ {scope} 已授权（一次性 · {ttl}s 有效 · {r.get('grant_id')}）")
        got.append(r.get("grant_id"))
    return got


def _ready_banner(master: bool = False) -> bool:
    """开跑前把话说透：这一步最容易被'回车'误杀（实测 2026-09-19 10:43 就发生过一次）。"""
    print()
    print("=" * 68)
    if master:
        print("★ 现在只问 1 次：owner_control（总控）—— 按声明它可替代本次动作所需的全部未授权作用域")
    else:
        print("★ 现在开始连问 3 次授权（deploy_publish / process_execute / filesystem_write）")
    print("★ 每一次都要**手打三个字母 YES 再回车**")
    print("★ 千万别按空回车：这个窗口里『回车』就是取消，三次白问")
    print("★ 三次都确认后，脚本自动发一次一次性部署，结果写进")
    print("   .scratch\\_deploy_app_last.json（我这边会读它并复核给你）")
    print("=" * 68)
    print("（3 秒后开始，直接接着打 YES 就行）")
    time.sleep(3)
    return True


def deploy(room: str = "") -> dict:
    from gbt_allinone import api
    payload = {
        "target": TARGET,
        "purpose": "APP 成品一次性部署（主人一键入口 deploy_app_oneclick）",
        "name": "desktop-human-app",
    }
    if room:
        payload["room"] = room
    else:
        payload["into_global_production"] = True

    res = api.run_task("one_key_deploy", payload, safe=True)
    inner = res.get("result") if isinstance(res.get("result"), dict) else {}
    view = {k: (inner.get(k) if inner else res.get(k))
            for k in ("ok", "status", "blocked", "denied", "reason", "missing",
                      "how_to_grant", "error", "version", "files", "elapsed_s")}
    view["kind"] = res.get("kind")
    _log({"stage": "deployed", "landing": payload.get("room") or "global_production",
          "target": TARGET, "result": view,
          "steps": inner.get("steps") or None})
    _write_report(payload.get("room") or "全局生产面（into_global_production=true）",
                  view, inner.get("steps"))
    print(json.dumps(view, ensure_ascii=False, indent=1))
    if inner.get("steps"):
        print("steps:", json.dumps(inner["steps"], ensure_ascii=False))
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description="APP 成品一次性部署（主人一键入口）")
    ap.add_argument("--check", action="store_true", help="只读：看授权现状，不做任何事")
    ap.add_argument("--room", default="", help="落点=隔离房间（只写房间，生产分毫不动）")
    ap.add_argument("--ttl", type=int, default=DEFAULT_TTL, help="授权有效期秒数（默认 600）")
    ap.add_argument("--owner", action="store_true",
                    help="主人本机会话：由框架自己的 policy.is_trusted() 判定，免逐条授权（AI 无权替主人开这个开关）")
    ap.add_argument("--master", action="store_true",
                    help="只讨一条 owner_control（总控）：按声明可替代该次动作所需的全部未授权作用域，只需一次 YES")
    args = ap.parse_args()

    print("== APP 成品一次性部署 · 万能插（统一接口 run_task）口径 ==")
    print(f"目标：{TARGET}")
    print(f"落点：{'隔离房间 ' + args.room if args.room else '全局生产面（into_global_production=true）'}")

    if args.check:
        show_status()
        return 0

    if args.owner:
        # 开关不由本脚本认可，而是交给框架自己的主人会话判定——AI 无法伪造。
        from gbt_allinone.security import policy as _policy
        if not _policy.is_trusted():
            print("✖ 这不是主人会话（policy.is_trusted=False）⇒ 不开绿灯。")
            print("  主人本机终端里先跑：$env:GBT_OWNER_SESSION=1  再执行本脚本；")
            print("  或者去掉 --owner，走三次 YES 的授权路。")
            _log({"stage": "owner_flag_but_untrusted"})
            return 1
        print("主人会话已确认（policy.is_trusted=True）⇒ 不消耗一次性授权，直接发枪。")
        res = deploy(args.room)
        body = res.get("result") if isinstance(res.get("result"), dict) else {}
        ok = bool(body.get("ok")) if body else bool(res.get("ok"))
        print("== 结果：" + ("已晋升上线 ✔" if ok else "未晋升 ✖") + " ==")
        return 0 if ok else 1

    # 防呆：非交互终端下 getpass 会静默卡住（本脚本实测踩过）——先拒绝，别让人对着假死窗口等。
    if not sys.stdin.isatty():
        print("✖ 当前不是交互终端：授权必须由人在终端里亲手输入 YES。")
        print("  请双击 deploy-app-one-click.bat（或在主人自己的终端窗口里跑本脚本）。")
        _log({"stage": "refused_non_tty"})
        return 1

    _ready_banner(args.master)

    ids = gather_grants(args.ttl, master=args.master)
    if not ids:
        # 给一次补救机会：回车误杀在实测里真的发生过（10:43:50 auth_grant_aborted）
        print()
        print("—— 这一轮被取消了（回车＝取消）。要重来就在窗口里手打 YES；")
        print("   不想重来直接关窗口，或者在这儿手打 RETRY 回车再试一轮。")
        try:
            again = input("输入 RETRY 再试一轮 >> ").strip().upper() == "RETRY"
        except Exception:  # noqa: BLE001
            again = False
        if again:
            ids = gather_grants(args.ttl, master=args.master)
        if not ids:
            print("停在授权门之前：一步都没写。授权只能主人在终端亲手发放。")
            _log({"stage": "grant_aborted"})
            return 1

    res = deploy(args.room)
    body = res.get("result") if isinstance(res.get("result"), dict) else {}
    ok = bool(body.get("ok")) if body else bool(res.get("ok"))
    print("== 结果：" + ("已晋升上线 ✔" if ok else "未晋升 ✖") + " ==")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
