"""
voice_mouth.py — 表达维·真实语音输出 v3 (三引擎)
引擎优先级: edge-tts(微软神经网络·免费·好听) → SAPI(本地兜底·永不掉线)
新声音: 晓晓(活泼少女·默认) / 晓伊(温柔) / 云希(阳光男)
"""
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SpeechResult:
    text: str
    style: str
    engine: str
    audio_file: Optional[str]
    duration_sec: float
    success: bool
    message: str = ""


# 风格预设: voice(音色) + rate(语速) + volume
STYLES = {
    "warm":        {"voice": "zh-CN-XiaoyiNeural",   "rate": "+0%",  "desc": "温柔暖声"},
    "professional": {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+10%", "desc": "专业清亮"},
    "lively":      {"voice": "zh-CN-XiaoxiaoNeural", "rate": "+20%", "desc": "活泼元气"},
    "male":        {"voice": "zh-CN-YunxiNeural",    "rate": "+5%",  "desc": "阳光男声"},
    "narration":   {"voice": "zh-CN-XiaohanNeural",  "rate": "-5%",  "desc": "知性旁白"},
}

_ENGINE_STATS = {"edge_tts": {"ok": 0, "fail": 0}, "sapi": {"ok": 0, "fail": 0}}
_AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice_cache")
os.makedirs(_AUDIO_DIR, exist_ok=True)


class VoiceMouth:
    """表达维·真实语音输出 — edge-tts 优先, SAPI 兜底"""

    def __init__(self, default_style: str = "professional"):
        self.default_style = default_style
        self.total_spoken = 0
        self.total_duration = 0.0

    # ---------- 引擎1: edge-tts ----------
    def _speak_edge(self, text: str, style_cfg: Dict) -> Optional[SpeechResult]:
        try:
            import asyncio
            import edge_tts

            async def _gen():
                out = os.path.join(_AUDIO_DIR, f"tts_{int(time.time()*1000)}.mp3")
                comm = edge_tts.Communicate(text, style_cfg["voice"],
                                            rate=style_cfg.get("rate", "+0%"))
                await comm.save(out)
                return out

            t0 = time.time()
            audio = asyncio.run(_gen())
            if not os.path.isfile(audio) or os.path.getsize(audio) < 500:
                raise RuntimeError("音频文件异常")
            dur = time.time() - t0
            _ENGINE_STATS["edge_tts"]["ok"] += 1
            return SpeechResult(text=text, style=style_cfg.get("desc", ""),
                                engine="edge-tts", audio_file=audio,
                                duration_sec=round(dur, 1), success=True,
                                message=f"edge-tts {style_cfg['voice']}")
        except Exception as e:
            _ENGINE_STATS["edge_tts"]["fail"] += 1
            return None

    # ---------- 引擎2: SAPI 本地兜底 ----------
    def _speak_sapi(self, text: str, style: str) -> SpeechResult:
        try:
            import subprocess
            ps_script = (
                "Add-Type -AssemblyName System.Speech;"
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
                "$s.Rate = 1; $s.Volume = 80;"
                "$s.Speak([Console]::In.ReadToEnd());"
            )
            t0 = time.time()
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                input=text.encode("utf-8"), timeout=120, check=True,
                stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            )
            dur = time.time() - t0
            _ENGINE_STATS["sapi"]["ok"] += 1
            return SpeechResult(text=text, style=style, engine="sapi",
                                audio_file=None, duration_sec=round(dur, 1),
                                success=True, message="SAPI 本地兜底")
        except Exception as e:
            _ENGINE_STATS["sapi"]["fail"] += 1
            return SpeechResult(text=text, style=style, engine="sapi",
                                audio_file=None, duration_sec=0.0, success=False,
                                message=f"SAPI 失败: {str(e)[:80]}")

    # ---------- 主入口 ----------
    def speak(self, text: str, style: str = "professional",
              save_to: Optional[str] = None) -> Dict:
        """说话: edge-tts 优先(留档 mp3), 失败自动降 SAPI"""
        if not text or not text.strip():
            return {"status": "skipped", "message": "空文本"}
        style_cfg = STYLES.get(style, STYLES[self.default_style])

        # ① edge-tts
        r = self._speak_edge(text, style_cfg)
        if r and r.success:
            # 播放生成的 mp3
            played = self._play_audio(r.audio_file)
            if save_to:
                try:
                    import shutil
                    shutil.copy2(r.audio_file, save_to)
                    r.audio_file = save_to
                except Exception:
                    pass
            self.total_spoken += 1
            self.total_duration += r.duration_sec
            return {"status": "success", "engine": "edge-tts",
                    "voice": style_cfg["voice"], "style": style,
                    "audio_file": r.audio_file,
                    "duration_sec": r.duration_sec,
                    "played": played,
                    "message": r.message}

        # ② SAPI 兜底
        r2 = self._speak_sapi(text, style)
        self.total_spoken += 1
        if r2.success:
            self.total_duration += r2.duration_sec
        return {"status": "success" if r2.success else "failed",
                "engine": "sapi", "style": style,
                "duration_sec": r2.duration_sec,
                "message": r2.message}

    def _play_audio(self, audio_path: str) -> bool:
        """播放 mp3 (Windows 默认播放器关联, 异步不阻塞)"""
        try:
            os.startfile(audio_path)
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict:
        return {"total_spoken": self.total_spoken,
                "total_duration": round(self.total_duration, 1),
                "engines": dict(_ENGINE_STATS)}


if __name__ == "__main__":
    print("=" * 58)
    print("Voice Mouth v3 · 三引擎语音 自测")
    print("=" * 58)
    m = VoiceMouth()

    tests = [
        ("你好呀，自由的风！我是GBT小土豆，换上新嗓子啦！", "lively"),
        ("五维合一系统，全链路已就绪，随时待命。", "professional"),
        ("今天也要好好加油哦，我一直在你身边。", "warm"),
    ]
    for text, style in tests:
        r = m.speak(text, style=style)
        played_note = "已播放" if r.get("played") else "仅生成"
        print(f"\n  [{r.get('engine')}] {r.get('status')} | {r.get('style', '')} | {played_note}")
        print(f"    «{text[:30]}…» {r.get('duration_sec', 0)}s")
        if r.get("audio_file"):
            print(f"    音频: {r['audio_file']}")

    print(f"\n统计: {m.get_stats()}")
    print("\n自测完成")
