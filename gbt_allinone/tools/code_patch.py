# -*- coding: utf-8 -*-
"""GBT小土豆V8 · `code_patch` —— **把「改代码」收进唯一门**（2026-09-23 接）。

## 为什么必须做这一件

在此之前，**改代码不过门**：agent 直接 `edit` / `write` 落盘 ——
没有审计、没有信封、没有步账、没有"改前改后"的凭据。
而"专业级编程AI"的第一块地基恰恰是：**每一次改动都能自证**（改了哪个文件、改前是什么、
改后是什么、能不能退回去）。

⇒ 本件把它做成一个**过门的能力位**：`run_task("code_patch", {...})`
—— 于是它天然带上唯一门的全部纪律（授权、审计、信封、preflight）。

## 机械闸（每一条都有牙，不是提醒）

    1. 路径必须在**仓内**（`path` 解析后必须落在 ROOT 下）—— 不许伸到仓外
    2. `find` 必须**恰好出现一次**：0 次 ⇒ `not_found`；>1 次 ⇒ `ambiguous`
       （**绝不替你挑一个** —— 挑错就是改错地方）
    3. `find != replace`（空改动直接拒，不做无意义写盘）
    4. `expect_sha256` 给了就必须对上（防"拿陈旧内容去改"）
    5. **二进制文件拒改**（前 8KB 有 NUL）：把 PNG/GLB 当文本读写 = 当场弄成废物
    6. 文件 > `MAX_BYTES` 拒改（防手滑改大文件）
    7. **逐字节替换**（不是文本替换）：只在 `find` 那几个字节上动手，
       `\\n` / CRLF / BOM 一个字节都不动
       （教训：`write_text` 会把 `\\n` 变成 `\\r\\n` —— 文本层替换会连带改掉整个文件的行尾）
    8. **原子写**：临时文件 + `os.replace`（写一半被杀不会留半个文件）
    9. `op=dry_run`（**默认**）只算不写；`op=apply` 才落盘

## 回执与可回滚

`apply` 会把**这次替换的三件套**（`find` / `replace` / 改前改后哈希）写进
`store/code_patch/<at>-<after8>.json` —— 于是 `op=rollback` 只要：
① 读回执 ② 确认当前文件哈希 == `after_sha256`（**文件要是又被人动过就拒绝回滚**，不猜）
③ 把 `replace` 换回 `find`。**回执里不写整份文件**，只写被替换的那几行。

## 用法（经唯一门）

    py -3.14 tools/codex-scripts/five-dim.py cap code_patch '{"path":"a.py","find":"x","replace":"y"}'
    # 默认 dry_run：只报 diff 与哈希，不写盘
    py -3.14 tools/codex-scripts/five-dim.py cap code_patch '{"op":"apply","path":"a.py","find":"x","replace":"y"}'
    # 需要 filesystem_write 授权（门会拦；缺授权如实报缺）
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]      # 仓根（gbt_allinone 的父目录）
MAX_BYTES = 4 * 1024 * 1024                       # 4 MB：手滑改大文件直接拒
_BIN_SNIFF = 8192


class CodePatchError(ValueError):
    """本能力自己的错误类型（带上机读的 reason_code）。

    🔴 **为什么继承 `ValueError`**：框架的约定是"用法/参数类错误要**抛**"，
    由 `api._run_task_core` 的 `except (ValueError, TypeError, …)` 收敛成
    `{"status": "error", "error_class": "user_error"}` 并记 `user_error` 审计。
    第一版我在这里**吞掉异常、返回错误 dict** ⇒ 外层被判成 `status: "ok"`
    （框架把"返回了 dict"读成"执行成功，结果在里面"）—— **读数自相矛盾**：
    外面 ok、里面 option_injection。跟着框架的约定抛，才是对的。
    """

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _store_dir() -> Path:
    try:
        from .. import _paths
        return _paths.STORE_DIR / "code_patch"
    except Exception:                                            # noqa: BLE001
        return _ROOT / "gbt_allinone" / "store" / "code_patch"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _resolve_inside(path: str) -> Path:
    """解析到**仓内**的绝对路径；伸出去就拒。"""
    raw = str(path or "").strip()
    if not raw:
        raise CodePatchError("missing_path", "没有给 path")
    p = Path(raw)
    p = (p if p.is_absolute() else (_ROOT / p)).resolve()
    try:
        p.relative_to(_ROOT)
    except ValueError:
        raise CodePatchError("outside_repo",
                             "路径不在仓内（拒绝）：%s" % str(p)[:120]) from None
    return p


def _load(p: Path) -> bytes:
    if not p.is_file():
        raise CodePatchError("not_a_file", "不是文件（或不存在）：%s" % p.name)
    b = p.read_bytes()
    if len(b) > MAX_BYTES:
        raise CodePatchError("too_large", "文件 %d 字节 > 上限 %d —— 拒改" % (len(b), MAX_BYTES))
    if b"\x00" in b[:_BIN_SNIFF]:
        raise CodePatchError("binary_file", "看起来是二进制（前 8KB 有 NUL）—— 拒改")
    return b


def _compute(path: str, find: str, replace: str, expect_sha256: str = "") -> dict:
    """算清楚"要改什么" —— **不写盘**。dry_run 与 apply 共用同一条计算路径。"""
    if not find:
        raise CodePatchError("empty_find", "find 不能为空（空白替换只会误伤）")
    if find == replace:
        raise CodePatchError("no_change", "find 与 replace 相同 ⇒ 空改动，拒绝写盘")
    p = _resolve_inside(path)
    before = _load(p)
    want = str(expect_sha256 or "").strip().lower()
    cur = _sha(before)
    if want and want != cur:
        raise CodePatchError("stale_content",
                             "expect_sha256 对不上：给了 %s，实际 %s" % (want[:12], cur[:12]))
    fb, rb = find.encode("utf-8"), replace.encode("utf-8")
    n = before.count(fb)
    if n == 0:
        raise CodePatchError("not_found", "find 在文件里一次都没出现（没改）")
    if n > 1:
        raise CodePatchError("ambiguous",
                             "find 出现了 %d 次 —— 拒绝替你挑一个（改错地方比不改更糟）" % n)
    after = before.replace(fb, rb, 1)
    return {
        "path": str(p.relative_to(_ROOT)).replace("\\", "/"),
        "abs": str(p),
        "occurrences": n, "find": find, "replace": replace,
        "before_sha256": cur, "after_sha256": _sha(after),
        "bytes_before": len(before), "bytes_after": len(after),
        "bytes_delta": len(after) - len(before),
        "_before": before, "_after": after,
    }


def _atomic_write(p: Path, data: bytes) -> None:
    tmp = p.with_name(p.name + ".gbtpatch%d" % os.getpid())
    try:
        tmp.write_bytes(data)
        os.replace(str(tmp), str(p))
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass


def dry_run(path: str, find: str, replace: str, expect_sha256: str = "") -> dict:
    r = _compute(path, find, replace, expect_sha256)
    r.pop("_before", None)
    r.pop("_after", None)
    r.update({"op": "dry_run", "wrote": False, "ok": True,
              "note": "只算不写。要落盘再用 op=apply（那一支要过 filesystem_write 门）"})
    return r


def apply(path: str, find: str, replace: str, expect_sha256: str = "") -> dict:
    r = _compute(path, find, replace, expect_sha256)
    p = Path(r["abs"])
    _atomic_write(p, r.pop("_after"))
    r.pop("_before", None)
    d = _store_dir()
    d.mkdir(parents=True, exist_ok=True)
    at = time.strftime("%Y-%m-%dT%H:%M:%S")
    rid = "%s-%s" % (time.strftime("%Y%m%dT%H%M%S"), r["after_sha256"][:8])
    rec = {"receipt_id": rid, "at": at, "path": r["path"],
           "find": find, "replace": replace,
           "before_sha256": r["before_sha256"], "after_sha256": r["after_sha256"],
           "note": "回滚三件套：确认当前哈希==after_sha256，再把 replace 换回 find"}
    (d / (rid + ".json")).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    r.update({"op": "apply", "wrote": True, "ok": True, "receipt_id": rid,
              "receipt": str(d.joinpath(rid + ".json")), "at": at})
    return r


def rollback(receipt_id: str = "", path: str = "") -> dict:
    """按回执回滚。**当前文件必须先对上 `after_sha256`**，对不上就拒（文件被人动过，不猜）。"""
    d = _store_dir()
    if not receipt_id:
        cands = sorted(d.glob("*.json")) if d.is_dir() else []
        if not cands:
            raise CodePatchError("no_receipt", "没有回执可回滚（store/code_patch 下是空的）")
        rec = json.loads(cands[-1].read_text(encoding="utf-8"))
    else:
        f = d / ("%s.json" % receipt_id)
        if not f.is_file():
            raise CodePatchError("no_such_receipt", "找不到回执 %s" % receipt_id)
        rec = json.loads(f.read_text(encoding="utf-8"))
    if path and str(path) != rec.get("path"):
        raise CodePatchError("receipt_mismatch",
                             "回执是给 %s 的，你给的是 %s" % (rec.get("path"), path))
    r = _compute(rec["path"], rec["replace"], rec["find"],
                 expect_sha256=rec["after_sha256"])
    p = Path(r["abs"])
    _atomic_write(p, r.pop("_after"))
    r.pop("_before", None)
    r.update({"op": "rollback", "wrote": True, "ok": True,
              "rolled_back_receipt": rec.get("receipt_id"),
              "note": "已按回执退回；当前哈希 == 该回执的 before_sha256"})
    return r


def run(payload: dict | None = None) -> dict:
    """能力位入口。`op` 默认 `dry_run`（**默认不写**）。"""
    p = dict(payload or {})
    op = str(p.get("op") or "dry_run").strip().lower()
    if op in ("dry_run", "dry", "preview", "diff"):
        return dry_run(p.get("path"), p.get("find"), p.get("replace"),
                       p.get("expect_sha256"))
    if op in ("apply", "write", "patch"):
        return apply(p.get("path"), p.get("find"), p.get("replace"),
                     p.get("expect_sha256"))
    if op in ("rollback", "revert", "undo"):
        return rollback(p.get("receipt_id"), p.get("path"))
    raise CodePatchError("unknown_op",
                         "不认识的 op=%s（只认 dry_run / apply / rollback）" % op)
