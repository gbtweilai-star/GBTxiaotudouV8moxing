#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GBT小土豆V8 · 上帝视角 · 四路账本常驻化（W3 · 产物 5）

把探针态的账本扶正为常驻：``store/ledger/`` 下四路 append-only jsonl。

纪律三条（《W3上帝视角镜像方案.md》§3.2）：
  1. **append-only** —— 只追加，不许改写历史行。
  2. **不记 payload 全文** —— 只记指纹与字节数（与《凭据不离屏律》同源）。
  3. **四路同一帧的 ``frame_bytes_hash`` 必须一致** —— 这是对齐判据的物理证明。

字段名沿用仓内权威名 ``frame_bytes_hash``（**不是** ``frame_sha256_16``——那是历史笔误）。

本模块**只在自己被第一次追加时才建目录/建文件**：空文件会让"看账本"那一格假绿，
没行就是没行，按《反空壳律》如实显示。

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

LAYERS = ("panel.send", "bridge", "route.recv", "mock.recv")

LEDGER_FILES = {
    "panel.send": "panel.send.jsonl",
    "bridge": "bridge.jsonl",
    "route.recv": "route.recv.jsonl",
    "mock.recv": "mock.recv.jsonl",
}

HERE = Path(__file__).resolve().parent


def repo_root(start: Path | None = None) -> Path | None:
    """向上找到含 ``gbt_allinone/`` 的仓库根。维度内与晋升后的现实里都能定位。"""
    cur = Path(start or HERE).resolve()
    while True:
        if (cur / "gbt_allinone").is_dir():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent


def ledger_dir(root: Path | None = None) -> Path:
    base = Path(root) if root is not None else repo_root()
    if base is None:
        raise RuntimeError("定位不到仓库根（缺 gbt_allinone/）")
    return base / "gbt_allinone" / "store" / "ledger"


def frame_fingerprint(payload) -> tuple[int, str]:
    """把一帧压成 (字节数, 前 16 位 sha256)。**不返回原文**。"""
    if isinstance(payload, (bytes, bytearray)):
        raw = bytes(payload)
    elif isinstance(payload, str):
        raw = payload.encode("utf-8")
    else:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return len(raw), hashlib.sha256(raw).hexdigest()[:16]


def _row(layer: str, event: str, frame_bytes: int, frame_bytes_hash: str, **extra) -> dict:
    row = {
        "event": event,
        "layer": layer,
        "frame_bytes": int(frame_bytes),
        "frame_bytes_hash": str(frame_bytes_hash),
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    for key, value in extra.items():
        if value is not None:
            row[key] = value
    return row


def append(layer: str, row: dict, root: Path | None = None) -> dict:
    """追加一行。返回回执（含落盘路径与行数），**不回显 payload**。"""
    if layer not in LEDGER_FILES:
        raise ValueError("未知账本层: %s（只认 %s）" % (layer, "/".join(LAYERS)))
    directory = ledger_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / LEDGER_FILES[layer]
    line = json.dumps(row, ensure_ascii=False) + "\n"
    with open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    return {"ok": True, "layer": layer, "path": str(path), "bytes": len(line.encode("utf-8"))}


def note_roundtrip(round_id: str, payload, route_from: str = "", route_to: str = "",
                   method: str = "", layer_events: dict | None = None,
                   root: Path | None = None) -> dict:
    """一次往返：同一帧落四路，指纹一致——这就是 V2 要的可复算证据。"""
    size, digest = frame_fingerprint(payload)
    events = dict(layer_events or {})
    out = {"round_id": round_id, "frame_bytes": size, "frame_bytes_hash": digest, "wrote": []}
    for layer in LAYERS:
        row = _row(
            layer,
            events.get(layer, "ledger.%s" % layer),
            size,
            digest,
            round_id=round_id,
            route_from=route_from or None,
            route_to=route_to or None,
            method=method or None,
        )
        out["wrote"].append(append(layer, row, root))
    return out


def tail(layer: str, n: int = 20, root: Path | None = None) -> list:
    """只读尾部 N 行。文件不存在 → 返回空表，不建文件。"""
    if layer not in LEDGER_FILES:
        raise ValueError("未知账本层: %s" % layer)
    path = ledger_dir(root) / LEDGER_FILES[layer]
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    rows = []
    for line in lines[-n:]:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:  # noqa: BLE001
            rows.append({"raw": line[:160]})
    return rows


def verify(round_id: str, root: Path | None = None) -> dict:
    """四路对齐判据：同一 ``round_id`` 的四路指纹必须一致。

    任一路缺行 → **INCONCLUSIVE**（不是 PASS 也不是 FAIL，见《M9判据收口.md》§四）。
    """
    seen = {}
    for layer in LAYERS:
        hits = [r for r in tail(layer, 200, root) if r.get("round_id") == round_id]
        seen[layer] = hits[-1].get("frame_bytes_hash") if hits else None
    missing = [k for k, v in seen.items() if not v]
    if missing:
        return {"verdict": "INCONCLUSIVE", "round_id": round_id,
                "missing": missing, "seen": seen,
                "note": "缺观测点 = 没验成，必须重跑；不许折算 PASS"}
    unique = set(seen.values())
    if len(unique) == 1:
        return {"verdict": "PASS", "round_id": round_id, "hash": seen[LAYERS[0]], "seen": seen}
    return {"verdict": "FAIL", "round_id": round_id, "seen": seen, "note": "四路指纹不一致"}


def self_test(root: Path | None = None) -> dict:
    """在临时目录里真跑一次"落四路 → 校验对齐"，**不碰真账本**。"""
    with tempfile.TemporaryDirectory(prefix="gbt_ledger_self_test_") as tmp:
        fake = Path(tmp)
        (fake / "gbt_allinone" / "store").mkdir(parents=True, exist_ok=True)
        payload = {"method": "initialize", "req_id": 1, "probe": "w3-self-test"}
        res = note_roundtrip("selftest", payload, route_from="panel", route_to="mock", root=fake)
        verdict = verify("selftest", root=fake)
        rows = {layer: len(tail(layer, 10, root=fake)) for layer in LAYERS}
    return {"ok": verdict["verdict"] == "PASS", "roundtrip": res, "verdict": verdict, "rows": rows}


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:  # noqa: BLE001
        pass
    print(json.dumps(self_test(), ensure_ascii=True))
