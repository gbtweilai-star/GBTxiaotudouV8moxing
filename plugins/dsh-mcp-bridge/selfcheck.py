# -*- coding: utf-8 -*-
"""GBT小土豆V8 · DSH MCP 桥 · 最小自证（真调，不是"应该是通的"）。

干的活：按 MCP 协议（stdio · 换行分隔 JSON-RPC）**真起** `server.py`，
逐条发真请求，把**原文读数**打出来，并按下述判据给结论：

  A. initialize 握手成功（拿到 protocolVersion / serverInfo）；
  B. tools/list 含 4 个读类工具（run_task/alerts/selfscan/capability_status）；
  C. tools/list **不含** logbook_append（写类默认不暴露 —— 这是"读类优先"的机器证据）；
  D. tools/call alerts 真回 run_task 信封（kind=alerts、status=ok、带 gbt_stamp 钢印）；
     ⚠️ 判据口径（自证首跑抓到的）：`gate` 字段是 `five-dim.py cap` **包装器**加的，
     唯一门 `run_task` 的信封里**没有**它 —— 断言必须按门自己的真身字段判，
     不许把包装器的形状当成门的形状。
  E. tools/call capability_status 真回 240 位目录；
  F. tools/call selfscan 真回五维体检；
  G. tools/call run_task(kind=mirror_shape) 被**桥**拒（refused_by=gbt-mcp-bridge）——
     写类 kind 不进唯一门；
  H. tools/call logbook_append 未知工具（默认没暴露）。

退出码：全过 0（并打 `SELFCHECK OK`），任一不过 1（打 `SELFCHECK FAIL`）。
这条判据同时被镜像排练计划里的 acceptance 命令用（`expect.stdout_contains: SELFCHECK OK`）。

用法：
    py -3.14 plugins/dsh-mcp-bridge/selfcheck.py [--server 路径] [--repo-root 仓根] [--timeout 180]

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
"""
from __future__ import annotations

import argparse
import json
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent


class Server:
    """真起服务器 + 线程读帧（读帧永不阻塞主判据）。"""

    def __init__(self, argv, cwd, env=None, timeout=180.0):
        self.timeout = timeout
        self.proc = subprocess.Popen(
            argv, cwd=str(cwd), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace",
            bufsize=1, env=env,
        )
        self.q: queue.Queue = queue.Queue()
        self.stderr_tail: list = []
        threading.Thread(target=self._pump_out, daemon=True).start()
        threading.Thread(target=self._pump_err, daemon=True).start()
        self._id = 0

    def _pump_out(self):
        for line in self.proc.stdout:
            self.q.put(line)

    def _pump_err(self):
        for line in self.proc.stderr:
            self.stderr_tail.append(line.rstrip())
            if len(self.stderr_tail) > 60:
                self.stderr_tail.pop(0)

    def send(self, method, params=None, notify=False):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        mid = None
        if not notify:
            self._id += 1
            mid = self._id
            msg["id"] = mid
        self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()
        return mid

    def wait(self, mid, timeout=None):
        """等 id=mid 的响应（中间通知/其它响应丢弃——自证是串行发起的）。"""
        deadline = time.time() + (timeout or self.timeout)
        while time.time() < deadline:
            try:
                line = self.q.get(timeout=min(1.0, max(0.05, deadline - time.time())))
            except queue.Empty:
                continue
            try:
                msg = json.loads(line)
            except Exception:                                     # noqa: BLE001
                continue
            if isinstance(msg, dict) and msg.get("id") == mid:
                return msg
        raise TimeoutError("等 id=%s 的响应超时（%.0fs）" % (mid, timeout or self.timeout))

    def call(self, method, params=None, timeout=None):
        return self.wait(self.send(method, params), timeout=timeout)

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:                                         # noqa: BLE001
            pass
        try:
            self.proc.wait(timeout=10)
        except Exception:                                         # noqa: BLE001
            self.proc.kill()


def _text_of(resp: dict) -> str:
    try:
        return resp["result"]["content"][0]["text"]
    except Exception:                                             # noqa: BLE001
        return ""


def _show(tag: str, text: str, cap: int = 1200) -> None:
    body = text if len(text) <= cap else text[:cap] + "\n…（自证输出截断：全量 %d 字符）" % len(text)
    print("── %s ──\n%s\n" % (tag, body))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="DSH MCP 桥 · 最小自证")
    ap.add_argument("--server", default=str(HERE / "server.py"))
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--timeout", type=float, default=300.0)
    a = ap.parse_args(argv)

    server = Path(a.server).resolve()
    root = Path(a.repo_root).resolve() if a.repo_root else None
    if root is None:
        for cand in [server.parent, *server.parents]:
            if (cand / "gbt_allinone" / "__init__.py").is_file():
                root = cand
                break
    if root is None:
        print("✗ 找不到仓根（--repo-root 显式给）")
        return 1

    argv_srv = [sys.executable, str(server), "--repo-root", str(root)]
    print("== GBT DSH MCP 桥 · 最小自证 ==")
    print("命令: %s" % " ".join('"%s"' % x if " " in x else x for x in argv_srv))
    print("仓根: %s" % root)
    print()
    checks = []
    srv = Server(argv_srv, cwd=root, timeout=a.timeout)
    try:
        t0 = time.time()
        init = srv.call("initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "gbt-selfcheck", "version": "0.1"},
        })
        checks.append(("A/initialize", bool(init.get("result", {}).get("serverInfo"))))
        _show("A · initialize 原文",
              json.dumps(init, ensure_ascii=False)[:800] + ("\n耗时 %.2fs" % (time.time() - t0)))
        srv.send("notifications/initialized", {}, notify=True)

        tools = srv.call("tools/list")
        names = [t.get("name") for t in tools.get("result", {}).get("tools") or []]
        checks.append(("B/读类工具齐", all(n in names for n in
                                            ("run_task", "alerts", "selfscan", "capability_status"))))
        checks.append(("C/写类默认不出现", "logbook_append" not in names))
        _show("B+C · tools/list 原文", json.dumps(tools, ensure_ascii=False, indent=1))

        t1 = time.time()
        alerts = srv.call("tools/call", {"name": "alerts", "arguments": {"last": 200}})
        at = _text_of(alerts)
        try:
            a_obj = json.loads(at)
        except Exception:                                         # noqa: BLE001
            a_obj = {}
        checks.append(("D/alerts 真回 run_task 信封",
                       a_obj.get("kind") == "alerts" and a_obj.get("status") == "ok"
                       and bool(a_obj.get("gbt_stamp"))))
        _show("D · tools/call alerts 原文（%.2fs）" % (time.time() - t1), at, cap=2500)

        t2 = time.time()
        caps = srv.call("tools/call", {"name": "capability_status", "arguments": {}})
        ct = _text_of(caps)
        try:
            c_obj = json.loads(ct)
        except Exception:                                         # noqa: BLE001
            c_obj = {}
        checks.append(("E/capability_status 240 位", c_obj.get("total") == 240))
        _show("E · tools/call capability_status 原文（%.2fs）" % (time.time() - t2),
              json.dumps({k: c_obj.get(k) for k in ("ok", "total", "domains", "count", "source")},
                         ensure_ascii=False, indent=1), cap=1500)

        t3 = time.time()
        scan = srv.call("tools/call", {"name": "selfscan", "arguments": {}})
        st = _text_of(scan)
        try:
            s_obj = json.loads(st)
        except Exception:                                         # noqa: BLE001
            s_obj = {}
        checks.append(("F/selfscan 真回体检", bool(s_obj)))
        _show("F · tools/call selfscan 原文（%.2fs）" % (time.time() - t3), st, cap=1800)

        # G：写类 kind 必须被**桥**拦下（不进唯一门）——这是"读类优先"的带牙判据。
        t4 = time.time()
        refuse = srv.call("tools/call", {
            "name": "run_task",
            "arguments": {"kind": "mirror_shape",
                          "payload": {"path": "x.txt", "content": "should-not-land"}},
        })
        rt = _text_of(refuse)
        try:
            r_obj = json.loads(rt)
        except Exception:                                         # noqa: BLE001
            r_obj = {}
        checks.append(("G/写类 kind 被桥拒", r_obj.get("refused_by") == "gbt-mcp-bridge"))
        _show("G · tools/call run_task(mirror_shape) 原文（%.2fs）" % (time.time() - t4), rt, cap=1200)

        lg = srv.call("tools/call", {"name": "logbook_append",
                                     "arguments": {"kind": "note", "what": "should-not-exist"}})
        checks.append(("H/logbook_append 未暴露", lg.get("result", {}).get("isError") is True))
        _show("H · tools/call logbook_append 原文", _text_of(lg), cap=600)
    except Exception as exc:                                      # noqa: BLE001
        print("✗ 自证过程中异常：%s: %s" % (type(exc).__name__, exc))
        checks.append(("异常", False))
    finally:
        srv.close()

    print("== 判定 ==")
    for name, ok in checks:
        print("  %s %s" % ("✓" if ok else "✗", name))
    if srv.stderr_tail:
        print("\n（服务器 stderr 尾 %d 行，佐证用）" % len(srv.stderr_tail))
        for line in srv.stderr_tail[-8:]:
            print("  | " + line)
    ok_all = all(ok for _, ok in checks)
    print("\n%s（%d/%d）" % ("SELFCHECK OK" if ok_all else "SELFCHECK FAIL",
                            sum(1 for _, ok in checks if ok), len(checks)))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
