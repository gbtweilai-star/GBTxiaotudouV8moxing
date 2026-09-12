"""GBT小土豆V8 · 统一数据后台：追加式 JSONL 审计日志 + 只读查询。

记录调用、配置变更、错误、被拒（危险能力）等事件，供审计复核。

V8 修复的两个暗伤：
1. query_log 改为反序流式读取（从文件尾往前拿 limit 条），不再全量读入内存；
2. 写入失败的内存缓冲提供 flush_memory_log() 回写路径，并在查询时自动尝试回写，
   不再静默丢失审计记录。
"""
import json
import os
import threading
import time
from pathlib import Path

from ._paths import STORE_DIR as _STORE_DIR  # 统一基址（支持 GBT_STORE_DIR 隔离）
_LOG = _STORE_DIR / "audit.jsonl"

# 内存缓冲区：当文件系统写入失败时的回退
_memory_log = []

# V8 极限打磨修复：并发追加审计曾出现行交错（10 路并发实测半截行）。
# 进程内所有写入/回写必须持同一把锁，保证 JSONL 每行完整。
_audit_lock = threading.Lock()


def _ensure():
    _STORE_DIR.mkdir(parents=True, exist_ok=True)


def audit(event, meta=None):
    """写入一条审计记录，返回该记录。

    优先写入文件，失败时存入内存缓冲区（后续 flush_memory_log / query 时回写）。
    """
    _ensure()
    rec = {
        "ts": round(time.time(), 3),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "event": event,
        "meta": meta or {},
    }
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    with _audit_lock:
        try:
            with open(_LOG, "a", encoding="utf-8") as f:
                f.write(line)
        except (PermissionError, OSError):
            # gatekeeper 或其他原因导致写入失败时，存入内存缓冲区
            _memory_log.append(rec)
    return rec


def flush_memory_log() -> int:
    """把内存缓冲中的审计记录回写落盘，返回成功回写条数。"""
    if not _memory_log:
        return 0
    written = 0
    with _audit_lock:
        try:
            _ensure()
            with open(_LOG, "a", encoding="utf-8") as f:
                while _memory_log:
                    rec = _memory_log.pop(0)
                    try:
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        written += 1
                    except (PermissionError, OSError):
                        _memory_log.insert(0, rec)
                        break
        except (PermissionError, OSError):
            pass
    return written


def _iter_log_reversed():
    """从文件尾往前按行产出（反序流式，不全量驻留内存）。"""
    if not _LOG.exists():
        return
    with open(_LOG, "rb") as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        buf = b""
        while pos > 0:
            step = min(8192, pos)
            pos -= step
            f.seek(pos)
            chunk = f.read(step)
            buf = chunk + buf
            lines = buf.split(b"\n")
            buf = lines.pop(0)  # 首段是未完整行，留到下一轮
            for line in reversed(lines):
                yield line
        if buf.strip():
            yield buf


def query_log(event=None, limit=200):
    """只读返回审计日志（可过滤 event），近期在前 -> 按时间升序返回最近 limit 条。

    兼容旧语义：返回列表按 ts 升序排列（最旧在前、最新在后），条数为最近 limit 条。
    """
    flush_memory_log()
    picked = []
    scanned = 0
    for raw in _iter_log_reversed():
        try:
            rec = json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            continue
        if event is not None and rec.get("event") != event:
            continue
        picked.append(rec)
        scanned += 1
        if scanned >= limit:
            break
    picked.reverse()
    if _memory_log:
        picked.extend(_memory_log[-limit:])
        picked.sort(key=lambda x: x.get("ts", 0))
    return picked[-limit:]


def log_count():
    """审计日志总条数（流式统计，不全量驻留内存）。"""
    flush_memory_log()
    n = 0
    if _LOG.exists():
        with open(_LOG, "rb") as f:
            for line in f:
                if line.strip():
                    n += 1
    return n + len(_memory_log)
