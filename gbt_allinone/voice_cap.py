# gbt-capability: voice
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""voice 能力 — Windows SAPI 语音合成 + **本机离线听觉**（两个真实后端）。

tts   : Windows SAPI.SpVoice（零依赖，Windows 自带）→ 播放或转 WAV 落盘
asr   : 云端 OpenAI 兼容端点（需 GBT_ASR_BASE_URL / GBT_ASR_API_KEY）
listen: **本机离线识别**（Windows 桌面识别器 System.Speech）—— 零密钥、零安装。
        主人令 2026-09-23：「打开页面就自动监听，关掉页面她也跟着关，大脑后台照常跑」
        ⇒ 这条腿的价值就是**不需要任何密钥**：本机现读有 `MS-2052-80-DESK（zh-CN）`。

────────────────────────────────────────────────────────────────────────────
🔴 **一个必须让主人知道的门盲区**（我不改 policy.py，那是主人的东西）：
   `gbt_allinone/security/policy.py` 的 `voice` 分支（第 297-302 行）现读是：
       if p.get("out"):                                  add("filesystem_write")
       if (op or "tts") in ("tts", "speak", None):       add("audio_output")
   ⇒ `op="listen"`（**打开麦克风**）**不挂任何作用域**，门拦不住它。
   而 `privacy_read` 的定义正是「读取屏幕、摄像头、麦克风或隐私载体」。
   要让它被门看见，只有主人能加这一行（**我不许改 policy.py**）：
       if op == "listen":
           add("privacy_read")
   在那之前：本能力**照实把这件事写在返回里**（`gate_blind_spot` 字段），
   不假装它已经受管。
────────────────────────────────────────────────────────────────────────────
🔴 **第 59 轮实测：`listen` 原来那条输入路在本机是死的，已改成两条腿。**
   本机现读（2026-09-23，四套音频 API 全查过）：
     · `waveInGetNumDevs() = 0` ⇒ `SetInputToDefaultAudioDevice()` 那条路是**旧版 waveIn
       映射器**，它**永远**抛 "Cannot find the requested data item"。
       ⚠️ 这跟插不插麦克风无关 —— 权威 API（MMDevice）现读录音侧 5 个端点，
       **在场的 0 个**（1 禁用 / 1 拔出 / 3 不在场），三个角色的默认录音设备**全不存在**。
     · MME 0 · DirectSound 0 · WASAPI 0 个输入端点；WDM-KS 列 4 个引脚但全部打不开。
   ⇒ `listen` 现在按顺序试两条腿，**两条腿的原因都留在 `legs` 里，不吞**：
       ① `wasapi-record.py`（PortAudio：MME/DirectSound/WASAPI/WDM-KS 都能看见）
          → 落成 16k/16bit/单声道 WAV → `asr-listen.ps1 -WavFile`
          —— PortAudio 能看见的端点**严格多于** winmm ⇒ 这条腿优先。
       ② 设备直连 `asr-listen.ps1`（无 `-WavFile`）—— 腿①不通时的兜底。
   ⚠️ 腿①会在**系统临时目录**写一个 WAV（用完即删）⇒ 本能力的"会动手"面比原来多了一项，
      这条也照实写进 `gate_blind_spot`，不藏。
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# 本机离线识别助手（Windows 桌面识别器）。放在仓的 tools/ 下，随版本管理。
_LOCAL_ASR_PS = Path(__file__).resolve().parents[1] / "tools" / "codex-scripts" / "asr-listen.ps1"
# 录音件（PortAudio/WASAPI）——绕开旧版 winmm 映射器的那条腿。见文件头第 59 轮那段。
_LOCAL_REC = Path(__file__).resolve().parents[1] / "tools" / "codex-scripts" / "wasapi-record.py"
_RECOG_CACHE = {"at": 0.0, "list": None}

# 依赖兜底：唯一真相源走 dependency_paths.activate_local_dependencies()。
# 不再手打 sys.path：手打会漏掉 ABI overlay（.pylibs/<abi>），
# 且会把 legacy 树顶到 sys.path[0]，对撞「系统包优先于 legacy 兜底」的设计。
try:
    from .dependency_paths import activate_local_dependencies
except ImportError:            # 以脚本方式直跑本文件时
    from gbt_allinone.dependency_paths import activate_local_dependencies
activate_local_dependencies()


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
        import hashlib
        from .security import net_guard as _ng
        from .security import ai_audit as _audit
        from .security import policy as _policy
        p = Path(audio)
        if not p.exists():
            raise ValueError(f"音频文件不存在: {audio}")
        boundary = "----gbtvoice"
        blob = p.read_bytes()
        model = os.environ.get("GBT_ASR_MODEL", "whisper-1")
        body = _io_boundary(boundary, p)
        url = base.rstrip("/") + "/audio/transcriptions"
        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}",
                   "Authorization": f"Bearer {key}"}
        # R120：语音原文与密钥都不进账本，只留长度/指纹。
        ctx = _audit.begin("openai-asr", url, model=model,
                           request_body={"model": model, "filename": p.name,
                                         "audio_bytes": len(blob),
                                         "audio_sha256": hashlib.sha256(blob).hexdigest()},
                           headers=headers)
        response = _ng.safe_request_json(
            url, method="POST", headers=headers, body=body, timeout=120,
            max_bytes=8_000_000, allow_private=_policy.is_trusted())
        status = int(response.get("status") or 0)
        data = response.get("json")
        if status >= 400 or not isinstance(data, dict):
            _audit.finish(ctx, status=status, ok=False, response_text=response.get("text"))
            return {"ok": False,
                    "error": "HTTP %s: %s" % (status, str(response.get("text") or "")[:200])}
        _audit.finish(ctx, status=status, ok=True, response=data,
                      response_text=data.get("text", ""))
        return {"ok": True, "backend": "cloud", "text": data.get("text", "")}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _ps_exe():
    for n in ("pwsh", "powershell"):
        p = shutil.which(n)
        if p:
            return p
    return None


def recognizers(ttl=300.0):
    """本机装了哪些**离线**识别器（只枚举，**不开任何设备**，无副作用）。

    为什么要单列一个：`op=status` 必须能如实说清"离线这条路能不能走"，
    而"能不能走"的第一步是"有没有该语言的识别器"。设备那一步故意留在 listen 里 ——
    status 一旦去开麦克风，它就不再是只读读数了。
    """
    now = time.time()
    if _RECOG_CACHE["list"] is not None and (now - _RECOG_CACHE["at"]) < ttl:
        return _RECOG_CACHE["list"]
    exe = _ps_exe()
    if not exe:
        return []
    code = ("Add-Type -AssemblyName System.Speech;"
            "[System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()"
            "|ForEach-Object{$_.Culture.Name+'|'+$_.Id}")
    try:
        cp = subprocess.run([exe, "-NoProfile", "-Command", code],
                            capture_output=True, timeout=25)
        txt = (cp.stdout or b"").decode("utf-8", "replace")
        out = [x.strip() for x in txt.splitlines() if "|" in x]
    except Exception:  # noqa: BLE001
        out = []
    _RECOG_CACHE["list"] = out
    _RECOG_CACHE["at"] = now
    return out


def _wavein_count():
    """`waveInGetNumDevs()` —— 旧版 waveIn 映射器能看见几个**输入**设备。

    **这就是本机"设备直连"那条腿的死活判据**：映射器数 0 ⇒ `SetInputToDefaultAudioDevice()`
    永远抛 "Cannot find the requested data item"，与插不插麦克风无关。
    用它当 status 的一个字段，是为了**堵掉一个假绿**：光看"有没有中文识别器"会报
    `listen 离线可用`，而实际上**一个输入端点都没有** —— 识别器在、耳朵不在。
    """
    try:
        import ctypes
        return int(ctypes.WinDLL("winmm").waveInGetNumDevs())
    except Exception:  # noqa: BLE001
        return None


def _clip(s, n):
    """把长字符串截短（`None` 原样返回）。

    🔴 **这不是装饰，是必需**：`five-dim.py` 在结果 >1100 字时会把整个 `result`
    收窄成 `{"_摘要":…, "preview":…}`，而**收窄后顶层 `status` 就没了**；
    `intercom.py watch` 正是按顶层 `status` 判"安静 / 没有设备 / 没有识别器"的
    ⇒ 实测因此把「**没有可用录音设备**」念成「**安静（没听到，不是坏）**」（假绿）。
    根因是我给 `listen` 补的 `legs` 里带着**异常原文**（很长）。
    ⇒ 两条腿的原因只留够看的前 `n` 字，把结果压回收窄阈值以内。
    """
    if s is None:
        return None
    s = str(s)
    return s if len(s) <= n else (s[:n] + "…")


def _last_json(raw):
    """从助手输出里取**最后一行** JSON（Python 侧唯一解析处，避免两处口径漂移）。"""
    for ln in reversed((raw or "").splitlines()):
        if ln.strip().startswith("{"):
            try:
                return json.loads(ln.strip())
            except Exception:  # noqa: BLE001
                return None
    return None


def _ps_run(args, to):
    """跑一次 asr-listen.ps1 并解析。**异常一律原样带出**，绝不吞成空结果。"""
    try:
        cp = subprocess.run(args, capture_output=True, timeout=to)
    except subprocess.TimeoutExpired:
        return {"ok": False, "status": "timeout", "exit": None,
                "error": "离线识别超时（%.0fs）：助手没在预期时间内返回" % to}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status": "error", "exit": None,
                "error": "起不来离线识别助手：%s" % str(e)[:160]}
    raw = (cp.stdout or b"").decode("utf-8", "replace").strip()
    out = _last_json(raw)
    if out is None:
        return {"ok": False, "status": "error", "exit": cp.returncode,
                "error": "助手没吐 JSON（exit=%s）" % cp.returncode,
                "stderr": (cp.stderr or b"").decode("utf-8", "replace")[:200]}
    out["exit"] = cp.returncode
    return out


def _record_wav(seconds, to):
    """腿①：用 PortAudio 录一段到临时 WAV（绕开旧版 winmm 映射器）。

    PortAudio 的四个主机 API（MME/DirectSound/WASAPI/WDM-KS）能看见的端点
    **严格多于** winmm ⇒ 优先试它。本机现读没有在场端点时会如实报 `no_input`。
    """
    rec = _LOCAL_REC
    if not rec.is_file():
        return {"ok": False, "status": "needs_dependency",
                "missing": "tools/codex-scripts/wasapi-record.py（录音件不在盘上）"}
    out = Path(tempfile.gettempdir()) / ("gbt_ear_%d.wav" % int(time.time() * 1000))
    # 解释器候选：先试本机 `python`（**已实测带 sounddevice**），再退回框架自己的解释器。
    # 为什么要点名逐个试：本仓声明口径是 **3.14**，而 sounddevice/pyaudio 现装在 **3.12**
    # ⇒ 用错解释器会**静默**变成"录音件起不来"，看起来像设备坏了。试过的每个都留在 attempts 里。
    cands = []
    for c in (shutil.which("python"), shutil.which("python3"), sys.executable):
        if c and c not in cands:
            cands.append(c)
    if not cands:
        return {"ok": False, "status": "needs_dependency", "missing": "找不到可用的 python 解释器"}
    attempts = []
    for py in cands:
        cmd = [py, str(rec), "--seconds", str(float(seconds)), "--out", str(out), "--json"]
        try:
            cp = subprocess.run(cmd, capture_output=True, timeout=max(20.0, min(to, 120.0)),
                                cwd=str(rec.parents[2]))
        except Exception as e:  # noqa: BLE001
            attempts.append({"interpreter": py, "error": "起不来：%s" % str(e)[:120]})
            continue
        d = _last_json((cp.stdout or b"").decode("utf-8", "replace").strip())
        if d is None:
            attempts.append({"interpreter": py, "exit": cp.returncode,
                             "stderr": (cp.stderr or b"").decode("utf-8", "replace")[:160]})
            continue
        d["exit"] = cp.returncode
        d["interpreter"] = py
        d["attempts"] = attempts
        return d
    return {"ok": False, "status": "error", "attempts": attempts,
            "error": "录音件在 %d 个解释器下都没吐 JSON（逐条见 attempts）" % len(cands)}


def asr_local(seconds=6.0, culture="zh-CN", min_confidence=0.0, timeout=None, wav=None):
    """本机离线听觉（Windows 桌面识别器）——**零密钥、零安装**。

    为什么要有它：`asr` 原来只认云端端点，没配密钥就 `needs_dependency`
    ⇒「没密钥就听不见」。而主人要的「打开页面自动监听」恰恰是**不许要密钥**的那条路。

    两条输入腿（见文件头第 59 轮那段）：先试 `wav`/录音件 → WAV → 识别器（腿①），
    不通再退回设备直连（腿②）。**两条腿各自的原因都留在 `legs` 里，绝不吞掉。**
    `wav=` 给了就用它，不再录音（便于离线复验与喂现成素材）。

    返回契约（**"安静"与"坏了"必须分开报**，这是本仓最贵的教训之一）：
      ok=True,  heard=True   → text/confidence 是真识别结果
      ok=True,  heard=False  → 跑完了但这段没听到（reason 写清是安静还是置信度不够）
      ok=False               → 后端不可用（缺 .NET / 缺该语言识别器 / **没有在场录音端点**）

    🔴 绝不伪造：任何异常原样带出，绝不拿空字符串冒充"识别成功"。
    """
    ps = _LOCAL_ASR_PS
    if not ps.is_file():
        return {"ok": False, "status": "needs_dependency",
                "missing": "tools/codex-scripts/asr-listen.ps1（离线识别助手不在盘上）"}
    exe = _ps_exe()
    if not exe:
        return {"ok": False, "status": "needs_dependency", "missing": "pwsh / powershell 都不在 PATH"}
    to = float(timeout) if timeout is not None else float(seconds) + 25.0

    def args_for(w):
        a = [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps),
             "-Seconds", str(float(seconds)), "-Culture", str(culture),
             "-MinConfidence", str(float(min_confidence))]
        if w:
            a += ["-WavFile", str(w)]
        return a

    legs = []
    target = wav
    tmp = None
    if not target:                                    # 腿① 先录音（PortAudio 看得更多）
        rec = _record_wav(seconds, to)
        legs.append({"leg": "wasapi-record", "ok": bool(rec.get("ok")),
                     "status": rec.get("status"),
                     "reason": _clip(rec.get("reason") or rec.get("error") or rec.get("missing"), 140),
                     "device": _clip(rec.get("device"), 60), "api": rec.get("api"),
                     "peak": rec.get("peak"), "rms": rec.get("rms"),
                     "interpreter": rec.get("interpreter"),
                     "attempts": [{"interpreter": a.get("interpreter"),
                                   "exit": a.get("exit"),
                                   "err": _clip(a.get("error") or a.get("stderr"), 90)}
                                  for a in (rec.get("attempts") or [])]})
        if rec.get("ok") and rec.get("wav"):
            target = rec["wav"]
            tmp = target

    out = None
    if target:
        out = _ps_run(args_for(target), to)
        legs.append({"leg": "asr-wav", "ok": bool(out.get("ok")), "status": out.get("status"),
                     "exit": out.get("exit"),
                     "reason": _clip(out.get("reason") or out.get("error"), 140)})
    if out is None or not out.get("ok"):              # 腿② 兜底：设备直连
        dev = _ps_run(args_for(None), to)
        legs.append({"leg": "asr-device", "ok": bool(dev.get("ok")), "status": dev.get("status"),
                     "exit": dev.get("exit"),
                     "reason": _clip(dev.get("reason") or dev.get("error"), 140)})
        if out is None or dev.get("ok"):
            out = dev
    if out is None:
        out = {"ok": False, "status": "no_input", "reason": "两条输入腿都没跑起来"}

    removed = None
    if tmp:
        try:
            Path(tmp).unlink()
            removed = True
        except Exception:  # noqa: BLE001
            removed = False
    out["backend"] = "win-speech"
    out["legs"] = legs
    out["source"] = out.get("source") or ("wav" if target else "device")
    if tmp:
        out["temp_wav_removed"] = removed
    out["gate_blind_spot"] = (
        "op=listen 会打开麦克风（并在系统临时目录写一个临时 WAV，用完即删），"
        "而 policy.py 的 voice 分支现读**不给它挂任何作用域**（该挂 privacy_read）"
        "—— 这是主人的决定，AI 不许改 policy.py")
    return out


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


# 每个 op **认**哪些参数。用途只有一个：**把"传了但没被用"的参数如实报出来**。
# 为什么必须有一张表（2026-09-25 实测踩到）：
#   调度层（`api.py` 的 voice 分支）当年是手写白名单转发，白名单外的参数**静默丢**；
#   而这层的 `params.get(...)` 是**第二次静默丢** —— 两层都不报错。
#   实测：传 `path=<wav路径>` 期望落盘，读数却是 `{"ok":true,"spoken":true}`（直接发声、零文件）。
#   ⇒ 修法不是"多加几个名字"（第 59 轮就是这么补的，同类病照样复发），而是**认不出就报**。
_ACCEPTED_PARAMS = {
    "tts": {"text", "voice", "rate", "out"},
    "asr": {"audio"},
    "listen": {"seconds", "culture", "min_confidence", "timeout", "wav"},
    "status": set(),
}


def _dispatch(op, params):
    if op in ("tts", "speak", None):
        return tts(params.get("text"), params.get("voice"),
                   int(params.get("rate", 0)), params.get("out"))
    if op == "asr":
        return asr(params.get("audio"))
    if op == "listen":
        return asr_local(params.get("seconds", 6.0),
                         params.get("culture", "zh-CN"),
                         params.get("min_confidence", 0.0),
                         params.get("timeout"),
                         params.get("wav"))
    if op == "status":
        base = os.environ.get("GBT_ASR_BASE_URL", "")
        key = os.environ.get("GBT_ASR_API_KEY", "")
        recs = recognizers()
        zh = [r for r in recs if r.startswith("zh")]
        w = _wavein_count()
        return {"ok": True,
                "tts": "win-sapi（可用）",
                "asr": "configured" if (base and key) else "needs_dependency",
                "listen": ("win-speech（离线可用）" if zh else "needs_dependency"),
                "recognizers": recs,
                "recognizers_zh": zh,
                # 🔴 第 59 轮补：**光看识别器会报假绿**。识别器在位 ≠ 耳朵能听 ——
                #    本机实测有 zh 识别器，而输入端点**在场的 0 个** ⇒ listen 必报 no_input。
                "listen_recognizer": ("win-speech（识别器在位）" if zh else "needs_dependency"),
                "wavein_devices": w,
                "listen_input": ("wavein 可见 %d 个输入设备" % w) if w is not None else "取不到",
                "listen_note": ("wavein_devices = 0 ⇒ 设备直连那条腿**在本机是死的**"
                                "（与插不插麦克风无关）；只听 wasapi-record 那条腿。"
                                "两条腿都写在 listen 返回的 legs 里。"),
                "note": ("listen = 本机离线识别（零密钥，两条输入腿）；asr = 云端端点（需 GBT_ASR_*）；"
                         "listen 是否要挂 privacy_read 由主人的 policy.py 决定")}
    raise ValueError(f"未知 op: {op}（可用: tts/asr/listen/status）")


def run(op="tts", **params):
    """voice 统一入口：tts（SAPI，默认）/ asr（云端）/ **listen（本机离线）** / status。

    `listen` 是 2026-09-23 为「打开页面就自动监听」加的那条腿：
    它不需要任何密钥，也不需要主人发授权（门现读不给它挂作用域 —— 见文件头那条盲区说明）。

    🔴 本函数**只加字段、不改任何既有字段**：有认不出的参数时，返回值里多一个
    `ignored_params`（+ 一句 `ignored_note`）；参数都认得时，返回体与改动前**逐字节相同**。
    """
    op_n = "tts" if op in ("tts", "speak", None) else op
    accepted = _ACCEPTED_PARAMS.get(op_n)
    extra = sorted(k for k in params if k not in accepted) if accepted is not None else []
    res = _dispatch(op, params)
    if extra and isinstance(res, dict):
        res = dict(res)
        res["ignored_params"] = extra
        res["ignored_note"] = ("这些参数本 op 不认，**已原样丢弃、未参与执行**；"
                               "本 op 认的参数是 %s —— 别把 `ok:true` 读成『你要的效果达成了』"
                               % (sorted(accepted) or "无"))
    return res
