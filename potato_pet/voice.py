"""语音说话（GBT小土豆V8）：Windows SAPI 中文音色 + 编码安全（修"鬼叫"）。

修因：
- 旧版 PowerShell 兜底把中文直接拼进命令行 → 编码乱 + 英文音色读中文 = 鬼叫
- 新版：中文音色优先（Huihui/Yaoyao/Xiaoxiao/晓晓）+ 文本走临时文件（UTF-8 BOM）
  PowerShell 用 UTF8 读文件再朗读，彻底规避命令行编码
"""
from __future__ import annotations

import base64
import logging
import os
import subprocess
import tempfile
import threading

logger = logging.getLogger("potato.voice")

_engine = None
_engine_kind = None
_engine_lock = threading.Lock()
_enabled = False

# 中文音色候选（SAPI 描述里常见的中文语音）
_ZH_VOICE_HINTS = ("huihui", "yaoyao", "kangkang", "xiaoxiao", "yunxi", "yunjian",
                   "晓晓", "云希", "慧慧", "瑶瑶", "中文", "chinese", "zh-cn")


def init(enabled: bool = True) -> None:
    global _enabled
    _enabled = enabled
    if enabled:
        _get_engine()


def _pick_zh_voice(voices):
    """从 SAPI 音色列表中挑中文音色（挑不到返回 None=用默认）。"""
    for v in voices:
        try:
            desc = str(v.GetDescription()).lower()
        except Exception:
            continue
        if any(h in desc for h in _ZH_VOICE_HINTS):
            return v
    return None


def _get_engine():
    """惰性初始化（线程安全）：优先 win32com SAPI（可选中文音色），
    缺失时用 PowerShell + UTF-8 文件兜底（编码安全）。"""
    global _engine, _engine_kind
    if _engine is not None:
        return _engine
    try:
        import win32com.client
        with _engine_lock:
            if _engine is None:
                voice = win32com.client.Dispatch("SAPI.SpVoice")
                zh = _pick_zh_voice(voice.GetVoices())
                if zh is not None:
                    voice.Voice = zh
                    logger.info("SAPI zh voice: %s", zh.GetDescription())
                else:
                    logger.warning("SAPI 无中文音色，用默认（可能读中文不准）")
                voice.Rate = 2   # 略快，活泼但不刺耳
                voice.Volume = 90
                _engine = voice
                _engine_kind = "win32com"
                logger.info("SAPI voice engine ready (win32com)")
    except ImportError:
        with _engine_lock:
            if _engine is None:
                _engine = "ps"
                _engine_kind = "ps"
                logger.info("SAPI voice via PowerShell fallback (UTF-8 file)")
    except Exception as e:
        logger.warning("SAPI unavailable (%s), voice disabled", e)
        _engine = None
    return _engine


def speak(text: str) -> bool:
    """异步说话（不阻塞 GUI）。返回是否成功排队。"""
    if not _enabled:
        return False
    engine = _get_engine()
    if engine is None:
        return False
    clipped = (text or "").strip()[:160]
    if not clipped:
        return False
    threading.Thread(target=_speak_sync, args=(engine, clipped), daemon=True).start()
    return True


def _speak_sync(engine, text: str) -> None:
    try:
        if engine == "ps":
            _speak_ps_utf8(text)
        else:
            engine.Speak(text, 1)  # 1 = SVSFlagsAsync
    except Exception as e:
        logger.warning("speak failed: %s", e)


def _speak_ps_utf8(text: str) -> None:
    """PowerShell 兜底（编码安全）：文本走 UTF-8 文件，脚本读文件后选中文音色朗读。"""
    # 文本写入临时文件（UTF-8 with BOM，PowerShell 5.1 的 Get-Content -Encoding UTF8 可读）
    fd, txt_path = tempfile.mkstemp(suffix=".txt", prefix="gbt_tts_")
    os.close(fd)
    with open(txt_path, "w", encoding="utf-8-sig") as f:
        f.write(text)

    fd2, ps_path = tempfile.mkstemp(suffix=".ps1", prefix="gbt_tts_")
    os.close(fd2)
    script = f'''
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
# 挑中文音色
$zh = $synth.GetInstalledVoices() | Where-Object {{
    $_.VoiceInfo.Culture.Name -like "zh*" -or $_.VoiceInfo.Name -match "Huihui|Yaoyao|Kangkang|Xiaoxiao|Yunxi|晓晓|中文"
}} | Select-Object -First 1
if ($zh) {{ $synth.SelectVoice($zh.VoiceInfo.Name) }}
$synth.Rate = 2
$synth.Volume = 90
$txt = Get-Content -Path "{txt_path}" -Encoding UTF8 -Raw
$synth.Speak($txt)
$synth.Dispose()
'''
    with open(ps_path, "w", encoding="utf-8-sig") as f:
        f.write(script)
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_path],
            timeout=40, capture_output=True)
    finally:
        for p in (txt_path, ps_path):
            try:
                os.remove(p)
            except Exception:
                pass


def list_voices() -> list:
    """列出可用 SAPI 音色（诊断用）。"""
    engine = _get_engine()
    if engine in (None, "ps"):
        return []
    try:
        return [str(v.GetDescription()) for v in engine.GetVoices()]
    except Exception:
        return []


def is_available() -> bool:
    return _get_engine() is not None
