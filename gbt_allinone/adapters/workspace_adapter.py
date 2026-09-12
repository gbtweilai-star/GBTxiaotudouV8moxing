"""Workspace 量化交易平台集成适配器（安全版）。

对接项目 C:\\Users\\ADMIN\\Desktop\\Workspace（GBT 量化交易平台）。
只读、不读取 .env / 密钥 / 敏感配置；不集成任何危险能力。
"""
import os
from pathlib import Path

WORKSPACE = Path(r"C:\Users\ADMIN\Desktop\Workspace")
QUANT_DIR = WORKSPACE / "01_量化收割引擎"

# 平台已知本地服务健康端点（只读 GET，无鉴权要求）
SERVICES = {
    "cap_bridge": "http://127.0.0.1:18900/api/health",
    "payment_gateway": "http://127.0.0.1:8081/api/payment/list",
    "blockchain_bridge": "http://127.0.0.1:8082/api/health",
}


def _count_py(path):
    if not path.exists():
        return 0
    return sum(1 for _ in path.rglob("*.py") if "__pycache__" not in _.parts and ".git" not in _.parts)


def profile():
    """项目档案：顶层结构 + 代码规模（真实数据）。"""
    dirs = []
    if WORKSPACE.exists():
        dirs = sorted(d.name for d in WORKSPACE.iterdir() if d.is_dir())
    return {
        "workspace": str(WORKSPACE),
        "exists": WORKSPACE.exists(),
        "top_level_dirs": dirs,
        "total_py": _count_py(WORKSPACE),
        "quant_py": _count_py(QUANT_DIR),
        "note": "只读测绘；未读取 .env/密钥",
    }


def modules():
    """列出量化收割引擎下的模块（真实文件名）。"""
    if not QUANT_DIR.exists():
        return {"quant_dir": str(QUANT_DIR), "modules": []}
    mods = sorted(d.name for d in QUANT_DIR.iterdir() if d.is_dir())
    files = sorted(f.name for f in QUANT_DIR.rglob("*.py") if "__pycache__" not in f.parts)
    return {"quant_dir": str(QUANT_DIR), "module_dirs": mods, "py_files": files[:120], "count": len(files)}


def health():
    """检测部署平台的服务可达性（只读 GET；服务未启动则标记 unreachable）。"""
    import socket
    import urllib.request
    import urllib.error
    out = {}
    for name, url in SERVICES.items():
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                out[name] = {"reachable": True, "status": r.status}
        except urllib.error.HTTPError as e:
            out[name] = {"reachable": True, "status": e.code}  # 服务在但返回错误
        except Exception as e:  # noqa: BLE001
            out[name] = {"reachable": False, "error": type(e).__name__}
    return {"services": out, "note": "只读探活；未发送任何交易/写操作"}
