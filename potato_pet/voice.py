"""语音说话：Windows SAPI 零依赖 TTS（线程化 + 限流）。

参照 Project AIRI / Open-LLM-VTuber 的语音能力，v2 用系统自带 SAPI 起步，
后续可平滑升级 edge-tts / GLM-TTS 音色复刻。
"""
from __future__ import annotations

import logging
import threading

logger = logging.getLogger("potato.voice")

_try_import = True
_engine = None
_engine_lock = threading.Lock()
_enabled = False


def init(enabled: bool = True) -> None:
    global _enabled
    _enabled = enabled
    if enabled:
        _get_engine()


def _get_engine():
    """惰性初始化（线程安全）：优先 win32com，缺失时用 PowerShell SAPI 兜底。"""
    global _engine, _try_import
    if not _try_import or _engine is not None:
        return _engine
    try:
        import win32com.client
        with _engine_lock:
            if _engine is None:
                _engine = win32com.client.Dispatch("SAPI.SpVoice")
                _engine.Rate = 4  # 语速稍快，活泼感
                logger.info("SAPI voice engine ready (win32com)")
    except ImportError:
        # win32com 不可用：改用 PowerShell System.Speech 兜底（标记为 'ps'）
        with _engine_lock:
            if _engine is None:
                _engine = "ps"
                logger.info("SAPI voice via PowerShell fallback")
    except Exception as e:
        logger.warning("SAPI unavailable (%s), voice disabled", e)
        _try_import = False
    return _engine


def speak(text: str) -> bool:
    """异步说话（不阻塞 GUI）。返回是否成功排队。"""
    if not _enabled:
        return False
    engine = _get_engine()
    if engine is None:
        return False
    # 截断超长文本，避免念个没完
    clipped = text[:120]
    threading.Thread(target=_speak_sync, args=(engine, clipped), daemon=True).start()
    return True


def _speak_sync(engine, text: str) -> None:
    try:
        if engine == "ps":
            import subprocess
            # 用 PowerShell 的 System.Speech 合成（无需 pywin32）
            subprocess.run(
                ["powershell", "-c",
                 f"Add-Type -AssemblyName System.Speech; "
                 f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{text}')"],
                timeout=30, capture_output=True)
        else:
            engine.Speak(text, 1)  # 1 = SVSFlagsAsync
    except Exception as e:
        logger.warning("speak failed: %s", e)


def is_available() -> bool:
    return _get_engine() is not None
