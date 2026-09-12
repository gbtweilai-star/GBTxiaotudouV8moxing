"""Alchemy RPC 适配（只读）— 从 .env 读 ALCHEMY_RPC_URL；未配置则不联网、明确报错。

只做只读查询：chainId / getBalance / getTransactionCount。
不签名、不广播（广播由后续专门的执行模块负责，且默认 dry-run）。
"""
import json
import os
import urllib.request
from pathlib import Path

_ENV = Path(__file__).resolve().parent.parent / ".env"


def _load_env():
    if _ENV.exists():
        for raw in _ENV.read_text(encoding="utf-8-sig").splitlines():
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ[k.strip()] = v.strip()


def rpc_url():
    _load_env()
    return os.environ.get("ALCHEMY_RPC_URL", "").strip()


def configured():
    return bool(rpc_url())


def _rpc(method, params):
    url = rpc_url()
    if not url:
        raise RuntimeError("ALCHEMY_RPC_URL 未配置（把 Alchemy 的 HTTPS 端点写入 .env）")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    if "error" in data:
        raise RuntimeError("RPC error: %s" % data["error"])
    return data.get("result")


def chain_id():
    return int(_rpc("eth_chainId", []), 16)


def block_number():
    return int(_rpc("eth_blockNumber", []), 16)


def balance_wei(address):
    return int(_rpc("eth_getBalance", [address, "latest"]), 16)


def balance_eth(address):
    return balance_wei(address) / 1e18


def nonce(address):
    return int(_rpc("eth_getTransactionCount", [address, "latest"]), 16)


_NET_CACHE = {"ts": 0.0, "data": None}


def network_info(ttl: int = 15):
    """只读网络信息；未配置 ALCHEMY_RPC_URL 时返回 configured=False。

    TTL 缓存 15 秒：链上状态秒级变化可接受，而 RPC 往返 300ms+ 不宜高频。
    """
    import time as _t
    if _NET_CACHE["data"] is not None and _t.time() - _NET_CACHE["ts"] < ttl:
        r = dict(_NET_CACHE["data"])
        r["cached"] = True
        return r
    if not configured():
        return {"configured": False,
                "hint": "在 .env 写入 ALCHEMY_RPC_URL=https://<net>.g.alchemy.com/v2/<KEY>"}
    r = {"configured": True, "chain_id": chain_id(), "block": block_number()}
    _NET_CACHE["ts"] = _t.time()
    _NET_CACHE["data"] = r
    return dict(r)
