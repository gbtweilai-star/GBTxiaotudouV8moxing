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
import re
import json
import os
import urllib.request
from pathlib import Path

# 依赖兜底：唯一真相源走 dependency_paths.activate_local_dependencies()。
# 不再手打 sys.path：手打会漏掉 ABI overlay（.pylibs/<abi>），
# 且会把 legacy 树顶到 sys.path[0]，对撞「系统包优先于 legacy 兜底」的设计。
try:
    from .dependency_paths import activate_local_dependencies
except ImportError:            # 以脚本方式直跑本文件时
    from gbt_allinone.dependency_paths import activate_local_dependencies
activate_local_dependencies()


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


def _mask_key(value: str) -> str:
    """掩码：前 4 后 2，其余打码（**返回值里永远不出现明文 key**）。"""
    s = str(value or "")
    if len(s) <= 6:
        return "*" * len(s)
    return s[:4] + "*" * (len(s) - 6) + s[-2:]


_PLAINTEXT_KEY_RX = re.compile(r"\b(?:sk|ak)[-_][A-Za-z0-9_\-]{16,}\b")


def assert_no_plaintext(payload, where: str = "") -> dict:
    """带牙守卫（R-H201）：**返回值里出现明文 key ⇒ 拒**（plaintext_key_in_return）。"""
    blob = json.dumps(payload, ensure_ascii=False, default=str)
    if _PLAINTEXT_KEY_RX.search(blob):
        return {"ok": False, "denied": True, "rule": "plaintext_key_in_return",
                "where": str(where or ""),
                "why": "密钥只能从 DPAPI/密钥池取，**返回值不许带明文**（只回 key_id/掩码/leased）"}
    return {"ok": True, "readonly": True}


def _vision_key() -> str:
    """**唯一取明文 key 的地方**（内部，绝不出返回值）：走 `deepseek_key` DPAPI 保险箱。

    R-H201 · 收口第二套密钥路径：
      · 不再读 `GBT_VISION_API_KEY`（环境变量明文）；
      · 不再回落到 `cloud_llm.API_KEY`（模块常量明文）；
      · 取不到就返回空串，由调用方**如实报 needs_dependency**（不伪造、不回落）。
    profile 由 `GBT_VISION_PROFILE` 指定（默认 `agnes`，与统一大模型口一致）。
    """
    profile = os.environ.get("GBT_VISION_PROFILE", "agnes")
    try:
        from . import deepseek_key as _dk
        # 🔴 必须用 `load_from_vault`（**只读保险箱、忽略环境变量**），不许用 `load_key`：
        # `load_key` 的优先级是 **先环境变量、后保险箱** ⇒ 用它等于"声明走保险箱、其实走环境变量"
        # （R-H201 实测：`load_key('agnes')` 返回 `env:AGNES_API_KEY`，而保险箱里 `agnes_api.dpapi` 不存在）。
        key, _source = _dk.load_from_vault(profile)
        return str(key or "")
    except Exception:  # noqa: BLE001
        return ""


def _safe_headers(headers: dict) -> dict:
    """给审计/日志用的**脱敏头**：`Authorization` 只留掩码（R-H201 · key_leaked_to_log）。"""
    out = {}
    for k, v in (headers or {}).items():
        if str(k).lower() == "authorization":
            raw = str(v).split(" ", 1)[-1]
            out[k] = "Bearer " + _mask_key(raw)
        else:
            out[k] = v
    return out


def resolve_vision_backend():
    """解析云端 vision 后端配置（R120 立 · R-H201 收口）。

    **返回值里不含明文 key** —— 只给 `key_id` / `key_present` / `key_masked`；
    明文由内部 `_vision_key()` 取用（走 DPAPI 保险箱），**绝不出函数**。
    地址与模型**只有一处真相**：优先 `GBT_VISION_*`，否则借用统一大模型口已解析的结果。
    """
    profile = os.environ.get("GBT_VISION_PROFILE", "agnes")
    key = _vision_key()
    provider = os.environ.get("GBT_VISION_PROVIDER", "vision-cloud")
    base = os.environ.get("GBT_VISION_BASE_URL", "")
    model = os.environ.get("GBT_VISION_MODEL", "")
    via = "GBT_VISION_*"
    if not (base and model):
        try:
            from .llm import cloud_llm as _cl
            base = base or _cl.BASE_URL or ""
            model = model or _cl.MODEL or ""
            provider = _cl.PROVIDER or provider
            via = "unified"
        except Exception:  # noqa: BLE001
            pass
    return {"provider": provider, "base_url": base, "model": model, "via": via,
            "key_id": "vision:%s" % profile, "key_present": bool(key),
            "key_masked": _mask_key(key) if key else ""}


def cloud_recognize(image=None, prompt="描述这张图片"):
    """云端图像识别（可选后端：OpenAI 兼容 vision 端点）。

    需环境变量 GBT_VISION_BASE_URL / GBT_VISION_API_KEY / GBT_VISION_MODEL。
    未配置时如实返回 needs_dependency，不伪造识别结果。
    """
    backend = resolve_vision_backend()
    base = backend.get("base_url") or ""
    key = _vision_key()                      # R-H201：明文只在内部，从不出返回值
    model = backend.get("model") or ""
    if not (base and key and model):
        return {"ok": False, "status": "needs_dependency",
                "missing": "DPAPI 保险箱密钥（profile=%s）/ base_url / model"
                           % backend.get("key_id", "agnes"),
                "note": "云端识别未配置；本地分析请用 op=analyze（已可用）"}
    # R120：出站统一走 net_guard + 应用层 AI 审计（此前直连 urlopen，两道门都没过）。
    from .security import net_guard as _ng
    from .security import ai_audit as _audit
    from .security import policy as _policy
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
        url = base.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
        # R-H201：**审计只收脱敏头** —— Authorization 变成 Bearer ****（key 不进审计）
        ctx = _audit.begin(str(backend.get("provider") or "vision-cloud"), url,
                           model=model, request_body=body,
                           headers=_safe_headers(headers))
        response = _ng.safe_request_json(
            url, method="POST", headers=headers,
            body=json.dumps(body).encode("utf-8"), timeout=60,
            max_bytes=8_000_000, allow_private=_policy.is_trusted())
        status = int(response.get("status") or 0)
        data = response.get("json")
        if status >= 400 or not isinstance(data, dict):
            _audit.finish(ctx, status=status, ok=False, response_text=response.get("text"))
            return {"ok": False,
                    "error": "HTTP %s: %s" % (status, str(response.get("text") or "")[:200])}
        _audit.finish(ctx, status=status, ok=True, response=data,
                      response_text=(data["choices"][0]["message"]["content"]))
        out = {"ok": True, "backend": "cloud", "via": backend.get("via"),
               "provider": backend.get("provider"), "model": model,
               "key_id": backend.get("key_id"), "key_masked": backend.get("key_masked"),
               "description": data["choices"][0]["message"]["content"]}
        guard = assert_no_plaintext(out, where="cloud_recognize.return")
        return out if guard.get("ok") else {
            "ok": False, "denied": True, "rule": guard["rule"], "why": guard["why"]}
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
        backend = resolve_vision_backend()
        base = base or (backend.get("base_url") or "")
        return {"ok": True, "local_analyze": True,
                "cloud": bool(base and backend.get("key_present")),
                "key_id": backend.get("key_id"), "key_masked": backend.get("key_masked"),
                "hint": "本地 analyze 随时可用；cloud 需 DPAPI 保险箱密钥（profile）"}
    raise ValueError(f"未知 op: {op}（可用: analyze/cloud/status）")
