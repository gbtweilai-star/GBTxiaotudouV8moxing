# -*- coding: utf-8 -*-
# gbt-capability: socket, dynamic-import, subprocess, network  ⏛ 开发者：自由的风 · GBT小土豆V8 · 永久钢印
"""万能插（omni_plug）—— 把「能力位」拓成「插座」：任何外部对象（进程/文件/API/网页）
插一个**描述符**就变成一根可扫可控的分支。

由来（主人 2026-10-09）：主人点破了一件事——
  V8 的「万能插」其实只是「能力位唯一门」（名字 → 实现，244 位）；
  而 V9 的万能插（`core/pulse.py`）是**插座**（对象 → 插头，process/file/api/web）。
  一个管「能力」，一个管「对象」—— 两边**名同不同轴**，接不上。

本件**从 V8 自己的树里长出来**（不跑去 import V9：V9 是另一个仓，会动、会移，不能当运行时依赖）：
  · 插座抽象照 V9 那套（Socket / plug / dispatch / plug_and_run / energy）；
  · **但门留在 V8 这边**（policy 作用域）—— 这正是 V9 那套最缺的一环：
    V9 的 `run_plugged` 里 process 直接 subprocess、file 直接写盘，没有作用域校验；
    本件把它挂在 **能力位边界**：process→process_execute · file写→filesystem_write ·
    api→external_llm+data_export · web→desktop_control+privacy_read · 未知插座→fail-closed。

三条纪律（与 V9 逐字同源）：
  ① **不攻击**：不改目标程序、不绕它的授权校验；够不着就如实说够不着；
  ② 凭据**只从 env 取**，记录里只写「用了哪一份」，**绝不回显原文**；
  ③ 每插一次、每跑一次都**落账**（谁授权、用哪份能源、花了多久）。

op：
  status / sockets / energy / selftest   读类（零作用域）
  plug                                   探测式插入（文件存在性 / target 合法性，不动手）
  run                                    **真执行**（按插座类型走门）
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
SOCKET_KINDS = ("process", "file", "api", "web", "app")
SOCKET_ENERGY = {
    "process": "本机 CPU + 她的调度",
    "file": "本机 IO",
    "api": "她金库里的凭据（从 env 取，永不回显）",
    "web": "她的眼+手（走触手，需 desktop_control）",
    "app": "她的眼+手：插任意 APP 并操控（list_windows→see_window→click/type/hotkey…，需 desktop_control+privacy_read）",
}
WRITE_ROOTS = ("projects", "outputs", ".scratch")


@dataclass
class Socket:
    kind: str
    target: str
    options: dict = field(default_factory=dict)
    plugged_at: float = 0.0
    state: str = "unplugged"          # unplugged | plugged | failed
    detail: str = ""


class Pulse:
    def __init__(self, ledger=None, brain=None) -> None:
        self.ledger, self.brain = ledger, brain
        self.plugged: dict[str, Socket] = {}

    def _log(self, event: str, detail: str) -> None:
        if self.ledger:
            try:
                self.ledger.log("omni_plug", event, "scanned", detail)
            except Exception:                                      # noqa: BLE001
                pass

    def plug(self, socket: Socket) -> Socket:
        if socket.kind not in SOCKET_KINDS:
            socket.state = "failed"
            socket.detail = "不支持的插座类型 %s" % socket.kind
            return socket
        try:
            if socket.kind == "file":
                p = Path(socket.target)
                exists = p.exists()
                # ⚠️ 新文件也算插得上：**父目录在就能建**。原来只认 exists ⇒ 想把新件写出来
                #    反而先被自己挡住（plug failed ⇒ run 直接拒），那是自锁。
                socket.state = "plugged" if (exists or p.parent.exists()) else "failed"
                socket.detail = ("exists=True size=%s" % p.stat().st_size) if exists else (
                    "不存在但父目录在（可新建）" if p.parent.exists() else "父目录也不在")
            elif socket.kind == "process":
                socket.state = "plugged"
                socket.detail = "插座就绪（真起进程在 run 那一步，过 process_execute 门）"
            elif socket.kind == "app":
                w = _match_window(socket.target)
                if w:
                    socket.state = "plugged"
                    socket.detail = "窗口命中：%s" % str(w.get("title") or w.get("name") or "")[:60]
                else:
                    wins, err = _windows()
                    _exe = Path(socket.target)
                    if _exe.is_file() and _exe.suffix.lower() in (".exe", ".lnk", ".bat", ".cmd"):
                        socket.state = "plugged"
                        socket.detail = "没命中窗口；按可执行文件当目标，可用 do=launch 起它"
                    else:
                        socket.state = "failed"
                        socket.detail = "窗口没命中（当前 %d 个窗口）%s" % (
                            len(wins), ("：" + err) if err else "")
            else:
                scheme = socket.target.split(":", 1)[0].lower()
                socket.state = "plugged" if scheme in ("http", "https") else "failed"
                socket.detail = "scheme=%s" % scheme
        except Exception as exc:                                   # noqa: BLE001
            socket.state, socket.detail = "failed", "%s: %s" % (type(exc).__name__, exc)
        socket.plugged_at = time.time()
        self.plugged[socket.target] = socket
        self._log("plug:%s" % socket.target, "%s %s" % (socket.kind, socket.state))
        return socket

    def dispatch(self, target: str, payload: dict) -> dict:
        sock = self.plugged.get(target)
        if sock is None or sock.state != "plugged":
            return {"ok": False, "error": "未插上（先 plug 成功）。本体不做坐标兜底："
                                              "网页/GUI 走能力位 tentacle（需 desktop_control）"}
        return {"ok": True, "socket": sock.kind, "handled": True, "payload_keys": sorted(payload)}

    def unplug(self, target: str) -> bool:
        s = self.plugged.pop(target, None)
        if s:
            s.state = "unplugged"
            return True
        return False

    def snapshot(self) -> dict:
        return {"插着": {k: {"kind": v.kind, "state": v.state, "detail": v.detail}
                                 for k, v in self.plugged.items()},
                "数": len(self.plugged)}


def energy() -> dict:
    """她的能源总账（一行）：插座能源 + V8 本机现读（能读多少报多少）。"""
    import shutil
    out = {"插座能源": dict(SOCKET_ENERGY)}
    try:
        out["本机"] = {"磁盘可用GB": round(
            shutil.disk_usage(os.environ.get("SystemDrive", "C:") + "\\").free / 1e9, 1)}
    except OSError:
        pass
    for name, env in (("ABLITERATION_API_KEY", "ABLITERATION_API_KEY"),
                      ("GBT_LLM_API_KEY", "GBT_LLM_API_KEY")):
        out.setdefault("凭据位", []).append({"env": env, "已配": bool(os.environ.get(name))})
    return out




def _tentacle():
    """V8 自己的手眼（带「先看再动」拦截）。"""
    from .tentacle.omni_tentacle import get_omni
    return get_omni()


def _windows():
    try:
        r = _tentacle().list_windows()
    except Exception as exc:                                       # noqa: BLE001
        return [], "%s: %s" % (type(exc).__name__, exc)[:120]
    if not r.get("ok"):
        return [], str(r.get("why") or r.get("rule") or "列窗口失败")
    return list(r.get("windows") or []), ""


def _match_window(target: str):
    """把 target 当窗口标题子串去命中（不区分大小写）。"""
    t = str(target or "").strip().lower()
    if not t:
        return None
    for w in _windows()[0]:
        title = str(w.get("title") or w.get("name") or "")
        if t in title.lower():
            return w
    return None


APP_ACTIONS = ("click", "type", "hotkey", "scroll", "drag", "move", "press", "paste",
               "clipboard_write", "click_text", "find_text", "read_text",
               "see_window", "see_active_window")


def _guard_write(target: str) -> dict:
    """写面自收窄：只准往 projects/ · outputs/ · .scratch/ 之下写（与 V8 写面同一口径）。"""
    p = (Path(target) if Path(target).is_absolute() else (_ROOT / target)).resolve()
    try:
        rel = p.relative_to(_ROOT)
    except ValueError:
        return {"ok": False, "why": "写面只限仓内，这条到仓外了：%s" % p}
    if not rel.parts or rel.parts[0] not in WRITE_ROOTS:
        return {"ok": False, "why": "写面只限 %s（实际：%s）" % ("/".join(WRITE_ROOTS), rel.as_posix())}
    return {"ok": True, "abs": str(p)}


def plug_and_run(target: str, *, kind: str = "process", action: str = "run",
                 args: dict | None = None, timeout: float = 30.0, ledger=None) -> dict:
    """**插上并驱动它**（真执行）。不攻击、不绕授权校验。"""
    a = args or {}
    sock = Socket(kind=kind, target=target)
    Pulse(ledger=ledger).plug(sock)
    res = {"ok": False, "socket": sock.kind, "target": target, "action": action,
           "energy": SOCKET_ENERGY.get(sock.kind, "未知"), "plug": sock.state}
    if sock.state != "plugged":
        res["reason"] = "先 plug 成功再驱动：%s" % sock.detail
        return res
    t0 = time.time()
    try:
        if sock.kind == "file":
            p = Path(target) if Path(target).is_absolute() else (_ROOT / target)
            if action == "read":
                res.update({"ok": True, "read": p.read_text(encoding="utf-8", errors="replace")[:400]})
            elif action in ("write", "append"):
                g = _guard_write(target)
                if not g.get("ok"):
                    res.update({"ok": False, "reason": g["why"]})
                else:
                    q = Path(g["abs"])
                    q.parent.mkdir(parents=True, exist_ok=True)
                    if action == "append":
                        with q.open("a", encoding="utf-8") as f:
                            f.write(str(a.get("text") or ""))
                    else:
                        q.write_text(str(a.get("text") or ""), encoding="utf-8")
                    res.update({"ok": True, "wrote_bytes": q.stat().st_size})
            elif action == "exists":
                res.update({"ok": True, "exists": p.exists()})
            else:
                res.update({"ok": False, "reason": "file 插座支持 read/write/append/exists"})
        elif sock.kind == "process":
            cmd = a.get("cmd") or target
            if isinstance(cmd, str):
                if cmd.startswith("py:"):
                    cmd = [sys.executable, "-c", cmd[3:]]
                else:
                    cmd = cmd.split()
            else:
                cmd = [str(x) for x in (cmd or [])]
            # 🔴 2026-10-12 修（实测）：Windows 上 npx / npm 是 **.cmd 批处理**，CreateProcess 直接起不了
            #   （实测 plug 成功、run 报 FileNotFoundError [WinError 2]）⇒ 解析出真实后缀后走 cmd /c。
            #   判据是 shutil.which 解析出的真路径，不是猜命令名。
            import shutil as _sh
            _exe = _sh.which(cmd[0]) if cmd else None
            if os.name == "nt" and _exe and _exe.lower().endswith((".cmd", ".bat")):
                cmd = ["cmd", "/c", *cmd]
            cp = subprocess.run(cmd, capture_output=True, timeout=timeout)
            _cap = max(200, int(a.get("max_out") or 400))
            res.update({"ok": cp.returncode == 0, "rc": cp.returncode,
                        "stdout": (cp.stdout or b"").decode("utf-8", "replace")[:_cap],
                        "stderr": (cp.stderr or b"").decode("utf-8", "replace")[:200],
                        "cmd": cmd if not cmd[:1] == ["cmd"] else cmd,
                        "max_out": _cap})
        elif sock.kind == "api":
            from .security import net_guard as _ng
            url = a.get("url") or target
            cred = str(a.get("cred") or "")
            hdr = {"Content-Type": "application/json"}
            if cred:
                tok = os.environ.get(cred, "")
                if tok:
                    hdr["Authorization"] = "Bearer " + tok
            r = _ng.safe_request(url, method=str(a.get("method") or "GET"), headers=hdr,
                                 timeout=timeout)
            res.update({"ok": int(r.get("status", 0)) < 400, "http": r.get("status"),
                        "cred_slot": (cred or "（无，匿名）"),
                        "cred_configured": bool(cred and os.environ.get(cred)),
                        "body": str(r.get("text") or "")[:300]})
        elif sock.kind == "app":
            # 🔴 插任意 APP 并操控：走 V8 自己的手眼（tentacle；**条目数现算，见 tentacle_manifest**，不手写）
            om = _tentacle()
            if action in ("see", "look"):
                r = om.see_window(target) if _match_window(target) else om.see_active_window()
                res.update({"ok": bool(r.get("ok")), "看": {k: r.get(k) for k in
                            ("ok", "rule", "window", "path", "why", "missing") if k in r}})
            elif action == "launch":
                r = om.launch(target, a.get("args"))
                res.update({"ok": bool(r.get("ok")), "launch": r})
            elif action == "act":
                act = str(a.get("action") or a.get("do") or "")
                if act not in APP_ACTIONS:
                    res.update({"ok": False, "reason": "不认的动作 %s" % act,
                                "known": list(APP_ACTIONS)})
                else:
                    fn = getattr(om, act, None)
                    if fn is None:
                        res.update({"ok": False, "reason": "触手没有这个动作：%s" % act})
                    else:
                        kw = dict(a.get("kwargs") or {})
                        if act == "hotkey":
                            r = fn(*(a.get("keys") or []))
                        elif act in ("type", "click_text"):
                            r = fn(str(a.get("text") or kw.get("text") or ""))
                        elif act == "click":
                            r = fn(kw.get("x"), kw.get("y"))
                        else:
                            r = fn(**kw)
                        res.update({"ok": bool(r.get("ok")), "act": act, "回读": r})
            else:
                res.update({"ok": False, "reason": "app 插座支持 see / act / launch",
                            "提示": "看图定下一步的闭环规划器本仓尚未接线；先按动作原语驱动"})
        else:
            res.update({"ok": False,
                        "reason": "web 插座要她**自己的眼+手**：走能力位 tentacle（需 desktop_control）",
                        "how": "five-dim.py cap tentacle '{\"action\":\"see\"}'"})
    except Exception as exc:                                       # noqa: BLE001
        res.update({"ok": False, "reason": "%s: %s" % (type(exc).__name__, exc)[:180]})
    res["ms"] = int((time.time() - t0) * 1000)
    if ledger:
        try:
            ledger.log("omni_plug", "run:%s" % target, "scanned" if res.get("ok") else "vuln",
                       "%s %s %sms" % (sock.kind, action, res["ms"]))
        except Exception:                                          # noqa: BLE001
            pass
    return res


def selftest() -> dict:
    """真插几个真对象 + 真驱动一次（面板上那个数字必须来自真动作）。"""
    p = Pulse()
    items = [Socket("file", str(Path(__file__).resolve())),
             Socket("file", "projects"),
             Socket("process", "py:print(6*7)"),
             Socket("api", "https://example.com/health"),
             Socket("not_a_kind", "x")]
    done = [p.plug(x) for x in items]
    ok_items = [s for s in done if s.state == "plugged"]
    drv = plug_and_run("py:print(6*7)", kind="process", action="run", timeout=20)
    return {"ok": bool(ok_items) and bool(drv.get("ok")),
            "插座数": len(done),
            "插上": ["%s:%s" % (s.kind, s.target) for s in ok_items],
            "失败": ["%s:%s %s" % (s.kind, s.target, s.detail) for s in done if s.state != "plugged"],
            "真驱动": {"ok": drv.get("ok"), "stdout": (drv.get("stdout") or "").strip(),
                                "rc": drv.get("rc")},
            "说明": "插上是真探测（文件在/进程就绪/URL 合法）；驱动是真执行（过门）"}


def run(op: str = "status", **kw) -> dict:
    op = str(op or "status").lower()
    if op == "status":
        return {"ok": True, "op": "status", "名字": "万能插",
                "插座类型": list(SOCKET_KINDS),
                "能源观": dict(SOCKET_ENERGY),
                "与 V9 的分工": "V9 插座无作用域门；本位把门留在 V8 的能力位边界"
                                            "（process→process_execute · file写→filesystem_write · "
                                            "api→external_llm+data_export · web→desktop_control+privacy_read）",
                "注": "网页/GUI 的坐标兜底走能力位 tentacle，不在本位重造一套"}
    if op in ("sockets", "snapshot"):
        p = Pulse()
        for k, t in (("file", str(Path(__file__).resolve())), ("process", "py:print(1)"),
                     ("api", "https://example.com/health")):
            p.plug(Socket(k, t))
        return {"ok": True, "op": "sockets", "插着": p.snapshot()["插着"],
                "数": p.snapshot()["数"]}
    if op == "energy":
        return {"ok": True, "op": "energy", "energy": energy()}
    if op == "selftest":
        st = selftest()
        return dict({"op": "selftest"}, **st)
    if op == "plug":
        p = Pulse()
        s = p.plug(Socket(str(kw.get("socket") or "file"), str(kw.get("target") or "")))
        return {"ok": s.state == "plugged", "op": "plug",
                "插座": {"kind": s.kind, "target": s.target, "state": s.state, "detail": s.detail}}
    if op == "run":
        return dict({"op": "run"}, **plug_and_run(
            str(kw.get("target") or ""), kind=str(kw.get("socket") or "process"),
            action=str(kw.get("do") or "run"), args=kw.get("args"),
            timeout=float(kw.get("timeout") or 30.0)))
    return {"ok": False, "error": "不认的 op：%s" % op,
            "known": ["status", "sockets", "energy", "selftest", "plug", "run"]}
