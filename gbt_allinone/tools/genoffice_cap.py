# gbt-capability: genoffice
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""GenOffice 办公文档能力（本地 CLI 引擎 0.10+）· 2026-09-26 主人令接入。

双向绑定四处互锁：caps_registry(kind=genoffice, domain=creation) ↔ api.py 路由 ↔
本处理器 ↔ 托管技能（~/.openclaw-autoclaw/skills/genoffice/SKILL.md）。
岗位：三套自动化闭环的内容生产段 —— 短视频分镜 PPT、电影剧本 docx、变现台账 xlsx。

边界（不碰 security/policy.py，闸挂处理器层，与仓内「写面过门」同律）：
  * 读类操作直连：info / capabilities / guide / 各域 read / skill list|path；
  * **一切写类操作过 auth_gate(filesystem_write)**，拒绝时如实带 how_to_grant；
  * 缺 CLI/缺 app 如实报缺（launcher → ~/.genoffice/launcher → 默认安装位）；
  * 子进程 argv 直传、无 shell、timeout 120s、输出截断 4KB。

ops：
  status                    版本 + capabilities（只读体检）
  run    args=[...]         透传 genoffice CLI（读类直连，写类过门）
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_MAX_OUT = 4000
_MAX_TIMEOUT = 120

# 读类白名单：这些 CLI 形状不动盘、不出网，直连
_READ_HEADS = {"info", "capabilities", "guide"}


def _cli() -> tuple[str | None, str]:
    """定位 genoffice CLI：launcher 文件 → 默认安装位。缺则如实报。"""
    launcher = Path.home() / ".genoffice" / "launcher"
    if launcher.is_file():
        d = launcher.read_text(encoding="utf-8").strip().strip('"')
        if d:
            for name in ("genoffice.cmd", "genoffice", "genoffice.exe"):
                p = Path(d) / name
                if p.is_file():
                    return str(p), ""
    for base in (Path.home() / "AppData/Local/Programs/GenOffice/resources/cli",):
        for name in ("genoffice.cmd", "genoffice", "genoffice.exe"):
            p = base / name
            if p.is_file():
                return str(p), ""
    return None, ("未找到 genoffice CLI（launcher 与默认安装位都没有）—— "
                  "先装 GenOffice 桌面本体，或把 CLI 目录写进 ~/.genoffice/launcher")


def _is_read(args: list) -> bool:
    if not args:
        return False
    head = str(args[0]).lower()
    if head in _READ_HEADS:
        return True
    if head == "skill" and len(args) > 1 and str(args[1]).lower() in ("list", "path"):
        return True
    if len(args) > 1 and str(args[1]).lower() == "read":
        return True
    return False


def status(**_kw) -> dict:
    cli, miss = _cli()
    out = {"ok": True, "op": "status", "kind": "genoffice",
           "cli": cli or "",
           "口径": "读类直连 · 写类过 filesystem_write 门 · 文档处理全本地 · "
                  "AI 引擎走主人已配的 Genspark 登录态（claude-opus-4-7 · 免 key · 留在免费），"
                  "search/image/media 三个命令经 Genspark 云端会耗积分，其余零消耗",
           "billing": {"local_ops": "免费", "search_image_media": "Genspark 积分"}}
    if not cli:
        out.update({"installed": False, "error": miss, "hint": "安装 GenOffice 桌面本体（genoffice.ai）"})
        return out
    try:
        p = subprocess.run([cli, "--version"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=30, cwd=str(_ROOT))
        out["version"] = (p.stdout or p.stderr).strip()[:80]
        cap = subprocess.run([cli, "capabilities"], capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=30, cwd=str(_ROOT))
        out["capabilities_head"] = ((cap.stdout or "") + (cap.stderr or ""))[:600]
    except Exception as exc:                                   # noqa: BLE001
        out["error"] = "CLI 体检失败：%s: %s" % (type(exc).__name__, str(exc)[:120])
    return out


def run(args: list | None = None, **_kw) -> dict:
    if not isinstance(args, list) or not all(isinstance(a, (str, int, float)) for a in args):
        return {"ok": False, "error": "args 必须是字符串/数字列表（genoffice CLI 参数序列）",
                "fail_closed": True}
    argv = [str(a) for a in args]
    cli, miss = _cli()
    if not cli:
        return {"ok": False, "error": miss, "hint": "安装 GenOffice 桌面本体（genoffice.ai）"}
    if not _is_read(argv):
        # 🔴 写面过门：不碰 security/policy.py，在本处理器挂 filesystem_write 闸
        from .. import auth_gate
        from ..security import policy as _policy
        if not _policy.is_trusted():
            gate = auth_gate.check_and_consume("filesystem_write",
                                               detail="genoffice:" + " ".join(argv)[:60])
            if not gate.get("ok"):
                return {"ok": False, "denied": True, "gate": "filesystem_write",
                        "error": gate.get("error"), "how_to_grant": gate.get("how_to_grant"),
                        "note": "写类操作（create/apply/convert/skill install…）需人工授权"}
    try:
        p = subprocess.run([cli] + argv, capture_output=True, text=True,
                           encoding="utf-8", errors="replace",
                           timeout=_MAX_TIMEOUT, cwd=str(_ROOT))
        out_text = ((p.stdout or "") + (p.stderr or "")).strip()
        return {"ok": p.returncode == 0, "op": "run", "args": argv,
                "exit": p.returncode, "out": out_text[:_MAX_OUT],
                "口径": "exit 0=OK · 1=用法/拒绝 · 2=文件问题 · 3=转换失败 · 4=app 不可用"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "CLI 超时（>%ds）" % _MAX_TIMEOUT, "fail_closed": True}
    except Exception as exc:                                   # noqa: BLE001
        return {"ok": False, "error": "%s: %s" % (type(exc).__name__, str(exc)[:160]),
                "fail_closed": True}


def run_op(op: str = "status", **params) -> dict:
    op = (op or "status").lower()
    if op == "status":
        return status(**params)
    if op == "run":
        return run(args=params.get("args"), **{k: v for k, v in params.items() if k != "args"})
    return {"ok": False, "error": "未知 op:%s（可用：status / run）" % op, "fail_closed": True}


if __name__ == "__main__":
    _r = run_op(sys.argv[1] if len(sys.argv) > 1 else "status",
                args=sys.argv[2:] if len(sys.argv) > 2 else None)
    print(_r)
