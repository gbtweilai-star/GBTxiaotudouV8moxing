# gbt-capability: pod_link
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""pod_link —— **云卡触手**（本机 ⇄ 租来的 GPU 卡：来回传文件 · 在卡上跑命令 · 看状态）。

## 来历（主人令：「把触手GPU-CPU传输让她学会不要每次都要我提醒」）

之前每次上云都要**现写临时脚本**（`.scratch/_up_lora.py` / `_dl_lora.py`），
还要主人提醒才想起来 —— 那就不是器官，是**一次性的手工活**。本件把它做成**一根触手**：

    status → 卡上现在有什么、多少钱、连不连得上（读）
    ls     → 卡上某个目录里有什么（读）
    up     → **本机 → 卡**（字节级，回读对账 sha256）
    down   → **卡 → 本机**（字节级，回读对账 sha256）
    run    → **在卡上跑一段 Python**（JupyterLab 内核通道 · WebSocket）

## 走的路（现成的两条，不新造）

- **文件**：JupyterLab HTTP —— `PUT /api/contents/<path>`（base64，任何文件都行）· `GET /files/<path>` 取回
- **命令**：JupyterLab **内核通道** —— `POST /api/kernels` 建核 + `wss://…/api/kernels/<id>/channels` 发 `execute_request`
- **卡在哪**：RunPod REST（`/v1/pods`）现读 —— 钥匙取 `GBT_RUNPOD_API_KEY` 或 `.scratch/.runpod_key`

## 铁律

1. **令牌一律不回显**：只报「已配/未配」；pod 的 `JUPYTER_PASSWORD` 从 API 现读、**不打进任何返回**。
2. **传完必须回读对账**（`sha256` 两头比）—— 不许拿"完成"文案当成功。
3. **只传、只跑，不替人做花钱决定**：本件**不创建、不删除、不重启**任何 Pod（那要主人点头）。
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_OPS = ("status", "ls", "up", "down", "run", "where")
_API = "https://rest.runpod.io/v1"
_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")


def _key() -> str:
    """钥匙：先环境变量，再仓内 `.scratch/.runpod_key`（**只报已配/未配，不回显**）。"""
    k = (os.environ.get("GBT_RUNPOD_API_KEY") or "").strip()
    if k:
        return k
    p = _ROOT / ".scratch" / ".runpod_key"
    return p.read_text(encoding="utf-8").strip() if p.is_file() else ""


def _pods() -> list:
    k = _key()
    if not k:
        return []
    r = urllib.request.Request(_API + "/pods", headers={"Authorization": "Bearer " + k,
                                                        "User-Agent": _UA})
    return json.loads(urllib.request.urlopen(r, timeout=30).read().decode())


def _pick(pod: str = "") -> dict:
    """选卡：显式给 → `GBT_POD_ID` → `.scratch/.pod_id` → 第一条 RUNNING。"""
    want = str(pod or os.environ.get("GBT_POD_ID") or "").strip()
    if not want:
        p = _ROOT / ".scratch" / ".pod_id"
        want = p.read_text(encoding="utf-8").strip() if p.is_file() else ""
    pods = _pods()
    if want:
        for x in pods:
            if x.get("id") == want:
                return x
    for x in pods:
        if x.get("desiredStatus") == "RUNNING":
            return x
    return pods[0] if pods else {}


def _base(p: dict) -> tuple:
    """(JupyterLab base url, token) —— token 只在这里活着，不进任何返回。"""
    pid = p.get("id") or ""
    tok = (p.get("env") or {}).get("JUPYTER_PASSWORD") or ""
    return ("https://%s-8888.proxy.runpod.net" % pid, tok)


def _req(url: str, method: str = "GET", body: bytes | None = None,
         ctype: str = "application/json", timeout: int = 120) -> tuple:
    r = urllib.request.Request(url, method=method, data=body,
                               headers={"User-Agent": _UA, "Content-Type": ctype})
    try:
        resp = urllib.request.urlopen(r, timeout=timeout, context=ssl.create_default_context())
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def _q(base: str, path: str, tok: str) -> str:
    return base + path + ("?token=" + urllib.parse.quote(tok) if tok else "")


def status(pod: str = "", **_kw) -> dict:
    """**读**：卡清单（id/状态/价/卷/端口）+ 钥匙是否已配 + 目标卡的 Jupyter 通不通。"""
    key_ok = bool(_key())
    if not key_ok:
        return {"ok": False, "status": "needs_key",
                "note": "没配卡钥匙 ⇒ 放 `GBT_RUNPOD_API_KEY` 或 `.scratch/.runpod_key`（只报已配/未配）"}
    pods = _pods()
    rows = [{"id": p.get("id"), "name": p.get("name"), "状态": p.get("desiredStatus"),
             "$/h": p.get("costPerHr"), "卷": p.get("networkVolumeId"),
             "盘G": p.get("containerDiskInGb"), "端口": p.get("portMappings") or {},
             "公网IP": p.get("publicIp"),
             "img": (p.get("imageName") or "").split(":")[0].split("/")[-1]} for p in pods]
    tgt = _pick(pod)
    jup = None
    if tgt:
        base, tok = _base(tgt)
        st, b = _req(_q(base, "/api/status", tok), timeout=25)
        jup = {"http": st, "body": (b or b"")[:120].decode("utf-8", "replace") if st == 200 else ""}
    return {"ok": True, "op": "status", "kind": "pod_link", "key_configured": True,
            "pods": rows, "pod_count": len(rows),
            "目标卡": tgt.get("id"), "jupyter": jup, "ops": list(_OPS),
            "_口径": "只读；token 取卡 env 的 JUPYTER_PASSWORD，**永不出现在返回里**"}


def ls(path: str = "/", pod: str = "", **_kw) -> dict:
    """**读**：列卡上某个目录。"""
    tgt = _pick(pod)
    if not tgt:
        return {"ok": False, "status": "no_pod", "error": "没选到卡"}
    base, tok = _base(tgt)
    st, b = _req(_q(base, "/api/contents/" + path.strip("/"), tok), timeout=40)
    if st != 200:
        return {"ok": False, "http": st, "error": b[:200].decode("utf-8", "replace")}
    d = json.loads(b)
    items = [{"name": x.get("name"), "type": x.get("type"), "bytes": x.get("size")}
             for x in (d.get("content") or [])]
    return {"ok": True, "op": "ls", "pod": tgt.get("id"), "path": path, "count": len(items),
            "items": items[:200]}


def up(local: str = "", remote: str = "", pod: str = "", **_kw) -> dict:
    """**本机 → 卡**：字节级上传（base64），**传完回读对账 sha256**。"""
    if not local or not remote:
        return {"ok": False, "fail_closed": True, "error": "要 local（本机文件）与 remote（卡上路径）"}
    src = Path(local)
    if not src.is_absolute():
        src = _ROOT / src
    if not src.is_file():
        return {"ok": False, "status": "not_found", "error": "本机没有：%s" % local}
    raw = src.read_bytes()
    tgt = _pick(pod)
    if not tgt:
        return {"ok": False, "status": "no_pod", "error": "没选到卡"}
    base, tok = _base(tgt)
    payload = json.dumps({"type": "file", "format": "base64",
                          "content": base64.b64encode(raw).decode()}).encode()
    st, b = _req(_q(base, "/api/contents/" + remote.strip("/"), tok), "PUT", payload, timeout=300)
    if st not in (200, 201):
        return {"ok": False, "http": st, "error": b[:220].decode("utf-8", "replace")}
    # 🔴 回读对账（不许拿"完成"文案当成功）
    st2, back = _req(_q(base, "/files/" + remote.strip("/"), tok), timeout=300)
    ok = (st2 == 200 and _sha(back) == _sha(raw) and len(back) == len(raw))
    return {"ok": ok, "op": "up", "pod": tgt.get("id"), "local": str(src.relative_to(_ROOT))
            if src.is_relative_to(_ROOT) else str(src), "remote": remote,
            "bytes": len(raw), "sha256_16": _sha(raw), "回读": {"http": st2, "bytes": len(back),
            "sha256_16": _sha(back)}, "_口径": "回读哈希一致才算成；不一致 ⇒ ok=false（不许念成成功）"}


def down(remote: str = "", local: str = "", pod: str = "", **_kw) -> dict:
    """**卡 → 本机**：字节级取回（`/files`），落盘后**对账 sha256**。"""
    if not remote or not local:
        return {"ok": False, "fail_closed": True, "error": "要 remote 与 local"}
    tgt = _pick(pod)
    if not tgt:
        return {"ok": False, "status": "no_pod", "error": "没选到卡"}
    base, tok = _base(tgt)
    st, b = _req(_q(base, "/files/" + remote.strip("/"), tok), timeout=600)
    if st != 200:
        return {"ok": False, "http": st, "error": b[:220].decode("utf-8", "replace")}
    dst = Path(local)
    if not dst.is_absolute():
        dst = _ROOT / dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(b)
    back = dst.read_bytes()
    ok = _sha(back) == _sha(b) and len(back) == len(b)
    return {"ok": ok, "op": "down", "pod": tgt.get("id"), "remote": remote,
            "local": str(dst.relative_to(_ROOT)) if dst.is_relative_to(_ROOT) else str(dst),
            "bytes": len(b), "sha256_16": _sha(b), "落盘": {"bytes": len(back), "sha256_16": _sha(back)}}


def run(code: str = "", path: str = "", timeout: int = 300, pod: str = "", **_kw) -> dict:
    """**在卡上跑一段 Python**（JupyterLab 内核通道）。`path` 给本机 `.py` 文件则读它。"""
    if path and not code:
        p = Path(path)
        if not p.is_absolute():
            p = _ROOT / p
        if not p.is_file():
            return {"ok": False, "status": "not_found", "error": "本机没有：%s" % path}
        code = p.read_text(encoding="utf-8")
    if not code:
        return {"ok": False, "fail_closed": True, "error": "要 code 或 path"}
    tgt = _pick(pod)
    if not tgt:
        return {"ok": False, "status": "no_pod", "error": "没选到卡"}
    base, tok = _base(tgt)
    st, b = _req(_q(base, "/api/kernels", tok), "POST",
                 json.dumps({"name": "python3"}).encode(), timeout=60)
    if st not in (200, 201):
        return {"ok": False, "http": st, "error": b[:200].decode("utf-8", "replace")}
    kid = json.loads(b).get("id")
    try:
        import websocket                                        # websocket-client
    except Exception:                                           # noqa: BLE001
        return {"ok": False, "status": "needs_dependency", "missing": ["websocket-client"],
                "note": "在卡上跑命令要 WebSocket：`py -3.14 -m pip install websocket-client`"}
    ws_url = "wss://%s-8888.proxy.runpod.net/api/kernels/%s/channels%s" % (
        tgt.get("id"), kid, ("?token=" + urllib.parse.quote(tok)) if tok else "")
    mid = "gbt-%d" % int(time.time() * 1000)
    out, t0 = [], time.time()
    try:
        ws = websocket.create_connection(ws_url, timeout=30)
        ws.send(json.dumps({
            "header": {"msg_id": mid, "username": "gbt", "session": "gbt",
                       "msg_type": "execute_request", "version": "5.3"},
            "parent_header": {}, "metadata": {},
            "content": {"code": code, "silent": False, "store_history": False,
                        "user_expressions": {}, "allow_stdin": False}, "channel": "shell"}))
        while time.time() - t0 < int(timeout):
            m = json.loads(ws.recv())
            t = (m.get("header") or {}).get("msg_type")
            c = m.get("content") or {}
            if t == "stream":
                out.append(c.get("text") or "")
            elif t in ("execute_result", "display_data"):
                out.append((c.get("data") or {}).get("text/plain") or "")
            elif t == "error":
                out.append("ERROR %s: %s" % (c.get("ename"), c.get("evalue")))
            elif t == "status" and c.get("execution_state") == "idle" \
                    and (m.get("parent_header") or {}).get("msg_id") == mid:
                break
        ws.close()
    except Exception as e:                                      # noqa: BLE001
        return {"ok": False, "error": "%s: %s" % (type(e).__name__, str(e)[:160]),
                "seconds": round(time.time() - t0, 1), "out": "".join(out)[:2000]}
    finally:
        _req(_q(base, "/api/kernels/" + str(kid), tok), "DELETE", None, timeout=30)
    return {"ok": True, "op": "run", "pod": tgt.get("id"), "seconds": round(time.time() - t0, 1),
            "out": "".join(out)[-4000:], "chars": sum(len(x) for x in out)}


def where(**_kw) -> dict:
    return {"ok": True, "op": "where", "kind": "pod_link",
            "entry": "run_task('pod_link', {'op':'up','local':'x.jsonl','remote':'/workspace/data/x.jsonl'})",
            "ops": list(_OPS),
            "what": "**云卡触手**：本机 ⇄ GPU 卡（传文件 · 在卡上跑命令 · 看状态）",
            "走的路": {"文件": "JupyterLab HTTP（PUT /api/contents base64 · GET /files）",
                       "命令": "JupyterLab 内核通道（POST /api/kernels + wss execute_request）",
                       "卡在哪": "RunPod REST /v1/pods（钥匙取 GBT_RUNPOD_API_KEY 或 .scratch/.runpod_key）"},
            "hard_rules": ["令牌不回显（只报已配/未配）；卡的 JUPYTER_PASSWORD 只在本件内部用",
                           "**传完回读对账 sha256**，不一致一律 ok=false",
                           "**不创建/不删除/不重启 Pod** —— 花钱动作要主人点头"],
            "作用域": {"status/ls/down/where": "零（公网读）", "up": "filesystem_write + data_export",
                       "run": "process_execute", "未知名": "fail-closed（挂满三项）"}}


def run_dispatch(op: str = "status", **params) -> dict:
    op = str(op or "status").lower()
    for nm, fn in (("status", status), ("ls", ls), ("up", up), ("down", down),
                   ("run", run), ("where", where)):
        if op == nm:
            return fn(**params)
    return {"ok": False, "fail_closed": True, "error": "未知 op：%s" % op, "ops": list(_OPS)}


if __name__ == "__main__":                                   # 主人的终端入口
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                    # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="云卡触手（本机 ⇄ GPU 卡）")
    ap.add_argument("cmd", nargs="?", default="status")
    ap.add_argument("--json", default="{}")
    a = ap.parse_args()
    print(json.dumps(run_dispatch(a.cmd, **json.loads(a.json or "{}")), ensure_ascii=False, indent=1))

# 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
