# gbt-capability: vision
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""vision 能力 — 本地真实视觉分析（PIL 像素级）+ 可选云端识别。

三级后端，如实报告，不伪造结果：
1. analyze（本地 PIL）：尺寸/主色/亮度/对比度/边缘密度/区域网格分析——零依赖即可跑
2. screen（dxcam 截屏）：复用触手视觉栈，屏幕区域分析
3. cloud（可选 AutoGLM/OpenAI 兼容端点）：需配置 GBT_VISION_BASE_URL+KEY，
   未配置时如实返回 needs_dependency
"""
from __future__ import annotations

import base64
import io as _io
import json
import os
import sys as _sys
import urllib.request
from pathlib import Path

# 依赖兜底：复用框架自带 .pylibs（与 tentacle/bridge.py 同机制）
_PYLIBS = Path(__file__).resolve().parent / ".pylibs"
if _PYLIBS.exists() and str(_PYLIBS) not in _sys.path:
    _sys.path.insert(0, str(_PYLIBS))


def _img_bytes_to_pil(data):
    from PIL import Image
    if isinstance(data, (bytes, bytearray)):
        return Image.open(_io.BytesIO(bytes(data))).convert("RGB")
    if isinstance(data, str):
        if data.startswith("data:image"):
            data = data.split(",", 1)[1]
        try:
            raw = base64.b64decode(data, validate=False)
            return Image.open(_io.BytesIO(raw)).convert("RGB")
        except Exception:
            p = Path(data)
            if p.exists():
                return Image.open(p).convert("RGB")
            raise ValueError("无法解析图像数据：请传图像路径/base64/bytes")
    if isinstance(data, Path):
        return Image.open(data).convert("RGB")
    raise ValueError("图像数据类型不支持: %s" % type(data).__name__)


def analyze(image=None, region=None, grid=4):
    """本地像素级图像分析（真实执行，无网络依赖）。"""
    from PIL import Image
    import numpy as np

    src = None
    if image is not None:
        src = _img_bytes_to_pil(image)
    else:
        # 无入图 → 截屏（复用触手 dxcam 栈）
        try:
            import dxcam
            cam = dxcam.create()
            frame = cam.grab(region=region)
            if frame is None:
                return {"ok": False, "error": "截屏失败：dxcam 未返回帧"}
            src = Image.fromarray(frame[:, :, ::-1])  # BGR->RGB
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "error": f"截屏后端不可用: {str(e)[:120]}", 
                    "hint": "传 image 参数（路径/base64）做文件分析，无需截屏"}

    a = np.asarray(src)
    h, w = a.shape[:2]
    gray = a.mean(axis=2)
    # 主色（量化后统计）
    q = (a // 32 * 32).reshape(-1, 3)
    colors, counts = np.unique(q, axis=0, return_counts=True)
    order = counts.argsort()[::-1][:5]
    top = [{"rgb": [int(c) for c in colors[i]], "share": round(float(counts[i]) / counts.sum(), 3)}
           for i in order]
    # 网格亮度图（变化分布）
    gh, gw = grid, grid
    cells = []
    for gy in range(gh):
        for gx in range(gw):
            cell = gray[gy*h//gh:(gy+1)*h//gh, gx*w//gw:(gx+1)*w//gw]
            cells.append(round(float(cell.mean()), 1))
    # 边缘密度（梯度幅值均值，近似清晰度/纹理复杂度）
    gy, gx = np.gradient(gray)
    edge = float(np.sqrt(gy**2 + gx**2).mean())
    return {
        "ok": True, "backend": "local-pil", "size": [w, h],
        "brightness": round(float(gray.mean()), 1),
        "contrast": round(float(gray.std()), 1),
        "edge_density": round(edge, 2),
        "top_colors": top,
        "grid_brightness": cells, "grid": grid,
        "format": "analysis",
    }


def cloud_recognize(image=None, prompt="描述这张图片"):
    """云端图像识别（可选后端：OpenAI 兼容 vision 端点）。

    需环境变量 GBT_VISION_BASE_URL / GBT_VISION_API_KEY / GBT_VISION_MODEL。
    未配置时如实返回 needs_dependency，不伪造识别结果。
    """
    base = os.environ.get("GBT_VISION_BASE_URL", "")
    key = os.environ.get("GBT_VISION_API_KEY", "")
    model = os.environ.get("GBT_VISION_MODEL", "")
    if not (base and key and model):
        return {"ok": False, "status": "needs_dependency",
                "missing": "GBT_VISION_BASE_URL / GBT_VISION_API_KEY / GBT_VISION_MODEL",
                "note": "云端识别未配置；本地分析请用 op=analyze（已可用）"}
    try:
        pil = _img_bytes_to_pil(image) if image is not None else None
        if pil is None:
            return {"ok": False, "error": "cloud_recognize 需要 image 参数"}
        buf = _io.BytesIO()
        pil.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        body = {"model": model, "messages": [{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]}]}
        req = urllib.request.Request(
            base.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "backend": "cloud", "model": model,
                "description": data["choices"][0]["message"]["content"]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def run(op="analyze", **params):
    """vision 统一入口：analyze（本地，默认）/ cloud（云端可选）。"""
    if op in ("analyze", "screen", None):
        return analyze(params.get("image"), params.get("region"), int(params.get("grid", 4)))
    if op == "cloud":
        return cloud_recognize(params.get("image"), params.get("prompt", "描述这张图片"))
    if op == "status":
        base = os.environ.get("GBT_VISION_BASE_URL", "")
        key = os.environ.get("GBT_VISION_API_KEY", "")
        return {"ok": True, "local_analyze": True,
                "cloud": bool(base and key),
                "hint": "本地 analyze 随时可用；cloud 需 GBT_VISION_* 环境变量"}
    raise ValueError(f"未知 op: {op}（可用: analyze/cloud/status）")
