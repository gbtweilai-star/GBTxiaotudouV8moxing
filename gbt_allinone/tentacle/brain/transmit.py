"""GBT小土豆V8 · brain 兼容垫片。

触手硬件层（omni_*）从旧 brain/ 目录结构迁移而来，其中"穿透传输"引用
brain.tentacle_transmission.transmit。V8 复活期本垫片提供同形降级实现：
数据落到 V8 审计总线（store），不再依赖旧 brain/ 目录结构。
后续可替换为直连 V8 事件总线。
"""
import sys
from pathlib import Path

# 让 `import brain.tentacle_transmission` 与 `import brain.xxx` 可寻址到本垫片包
_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))


def transmit(data, source="unknown", channel="default", priority="normal"):
    """穿透传输降级实现：落 V8 审计总线（轻量，不阻塞硬件层）。"""
    try:
        from gbt_allinone.store import audit
        audit("tentacle_tx", {"source": str(source)[:60], "channel": str(channel)[:20],
                              "priority": str(priority)[:10],
                              "size": len(str(data))})
    except Exception:  # noqa: BLE001
        pass  # 传输层绝不阻塞触手本体
    return {"ok": True, "degraded": "v8_audit_bus"}
