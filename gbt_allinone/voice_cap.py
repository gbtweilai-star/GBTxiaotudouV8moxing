# gbt-capability: voice
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""voice 能力 — Windows SAPI 语音合成（本机已验证的真实后端）。

tts: Windows SAPI.SpVoice（零依赖，Windows 自带）→ 转 WAV 落盘
asr: 未配置后端时如实返回 needs_dependency（不伪造识别）
"""
from __future__ import annotations

import os
import sys as _sys
from pathlib import Path

# 依赖兜底：复用框架自带 .pylibs（与 tentacle/bridge.py 同机制）
_PYLIBS = Path(__file__).resolve().parent / ".pylibs"
if _PYLIBS.exists() and str(_PYLIBS) not in _sys.path:
    _sys.path.insert(0, str(_PYLIBS))


def tts(text, voice=None, rate=0, out=None):
    """Windows SAPI 语音合成 → WAV 文件（真实发声，桌面宠物同款栈）。"""
    if not text:
        raise ValueError("缺少 text：要合成的文本")
    try:
        import comtypes.client
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status": "needs_dependency",
                "missing": "comtypes（.pylibs 已带；当前解释器未加载）",
                "detail": str(e)[:120]}
    try:
        sapi = comtypes.client.CreateObject("SAPI.SpVoice")
        if voice:
            for v in sapi.GetVoices():
                if voice.lower() in str(v.GetDescription()).lower():
                    sapi.Voice = v
                    break
        sapi.Rate = int(rate)
        if out:
            # 落盘 WAV（SAPI.SpFileStream）
            stream = comtypes.client.CreateObject("SAPI.SpFileStream")
            out_p = Path(out)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            stream.Open(str(out_p), 3)  # SSFMCreateForWrite = 3
            sapi.AudioOutputStream = stream
            sapi.Speak(text)
            stream.Close()
            return {"ok": True, "backend": "win-sapi", "wav": str(out_p),
                    "text": text[:80], "size_kb": round(out_p.stat().st_size / 1024, 1)}
        # 直接播放
        sapi.Speak(text)
        return {"ok": True, "backend": "win-sapi", "spoken": True, "text": text[:80]}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"SAPI 合成失败: {str(e)[:160]}"}


def asr(audio=None):
    """语音识别（ASR）。

    需配置 GBT_ASR_BASE_URL / GBT_ASR_API_KEY（OpenAI 兼容 /audio/transcriptions 端点）。
    未配置时如实返回 needs_dependency，不伪造转写结果。
    """
    base = os.environ.get("GBT_ASR_BASE_URL", "")
    key = os.environ.get("GBT_ASR_API_KEY", "")
    if not (base and key):
        return {"ok": False, "status": "needs_dependency",
                "missing": "GBT_ASR_BASE_URL / GBT_ASR_API_KEY",
                "note": "ASR 后端未配置；tts（SAPI）已可用"}
    if not audio:
        raise ValueError("缺少 audio：要转写的音频路径")
    try:
        import urllib.request
        p = Path(audio)
        if not p.exists():
            raise ValueError(f"音频文件不存在: {audio}")
        boundary = "----gbtvoice"
        body = _io_boundary(boundary, p)
        req = urllib.request.Request(
            base.rstrip("/") + "/audio/transcriptions",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                     "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            import json
            data = json.loads(resp.read().decode("utf-8"))
        return {"ok": True, "backend": "cloud", "text": data.get("text", "")}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _io_boundary(boundary, path):
    import io
    fields = {"model": os.environ.get("GBT_ASR_MODEL", "whisper-1"),
              "file": (path.name, path.read_bytes(), "audio/wav")}
    buf = io.BytesIO()
    for k, v in fields.items():
        if isinstance(v, tuple):
            buf.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{v[0]}\"\r\nContent-Type: {v[2]}\r\n\r\n".encode())
            buf.write(v[1])
        else:
            buf.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    buf.write(f"--{boundary}--\r\n".encode())
    return buf.getvalue()


def run(op="tts", **params):
    """voice 统一入口：tts（SAPI，默认）/ asr（需配置）。"""
    if op in ("tts", "speak", None):
        return tts(params.get("text"), params.get("voice"),
                   int(params.get("rate", 0)), params.get("out"))
    if op == "asr":
        return asr(params.get("audio"))
    if op == "status":
        base = os.environ.get("GBT_ASR_BASE_URL", "")
        key = os.environ.get("GBT_ASR_API_KEY", "")
        return {"ok": True, "tts": "win-sapi（可用）",
                "asr": "configured" if (base and key) else "needs_dependency"}
    raise ValueError(f"未知 op: {op}（可用: tts/asr/status）")
