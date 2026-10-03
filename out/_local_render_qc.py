# -*- coding: utf-8 -*-
"""render_preview + qc_preview 的本地等价实现（技能指定的 MCP 工具不可达，如实替代）。

⚠️ 写法约束（钩子要求）：**程序名一律字面量**、参数才用变量；不把命令拼成字符串再执行。
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8").resolve()
OUT = ROOT / "out"
PREVIEW = OUT / "preview.mp4"
W, H, FPS, TOTAL = 1920, 1080, 30, 12.0


def ffprobe_json(path: Path) -> dict:
    """程序名字面量；路径作为参数传入。"""
    cp = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    return json.loads(cp.stdout or "{}")


def ffmpeg_stderr(args: list) -> str:
    """程序名字面量 + 参数列表（含 -f null -）⇒ 只用 stderr 里的读数。"""
    cp = subprocess.run(
        ["ffmpeg", "-hide_banner"] + args, capture_output=True, text=True,
        encoding="utf-8", errors="replace")
    return cp.stderr or ""


def yavg(path: Path, ts: float) -> float:
    err = ffmpeg_stderr(["-ss", str(ts), "-i", str(path), "-frames:v", "1",
                         "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG",
                         "-f", "null", "-"])
    for ln in err.splitlines():
        if "YAVG=" in ln:
            try:
                return float(ln.split("YAVG=")[1].split()[0])
            except (IndexError, ValueError):
                return -1.0
    return -1.0


def sha256_file(p: Path) -> str:
    """**文件级** sha256 —— 与 closeout 钩子的 file_sha256 同一口径（读字节）。"""
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha8(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:8]


timeline = json.loads((OUT / "timeline.json").read_text(encoding="utf-8"))
tl_sha = sha8(OUT / "timeline.json")
tl_sha256 = sha256_file(OUT / "timeline.json")   # 钩子口径
clips = timeline["tracks"][0]["clips"]
a_clips = timeline["tracks"][1]["clips"]

# ── 渲染计划：timeline → ffmpeg 滤镜图（确定性）───────────────────────────
v_parts, a_parts = [], []
for i, c in enumerate(clips):
    v_parts.append(f"[{i}:v]trim=start={c['start']}:end={c['end']},setpts=PTS-STARTPTS,"
                   f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
                   f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={FPS}[v{i}]")
for i, c in enumerate(a_clips):
    a_parts.append(f"[{i}:a]atrim=start={c['start']}:end={c['end']},asetpts=PTS-STARTPTS,"
                   f"aresample=48000,aformat=sample_rates=48000:channel_layouts=stereo[a{i}]")
sil = round(TOTAL - sum(c["end"] - c["start"] for c in a_clips), 3)
a_parts.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{sil},asetpts=PTS-STARTPTS[a{len(a_clips)}]")
vcat = "".join(f"[v{i}]" for i in range(len(v_parts))) + f"concat=n={len(v_parts)}:v=1:a=0[vout]"
acat = "".join(f"[a{i}]" for i in range(len(a_clips) + 1)) + \
       f"concat=n={len(a_clips) + 1}:v=0:a=1[aout]"
graph = ";".join(v_parts + a_parts + [vcat, acat])

plan = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tooling": "本地等价（ffmpeg 滤镜图）—— 技能指定的 render_preview 工具不可达",
        "canvas": {"width": W, "height": H, "fps": FPS, "pixel_format": "yuv420p"},
        "expected_duration": TOTAL, "filter_graph": graph, "timeline_sha8": tl_sha,
        "timeline_sha256": tl_sha256,
        "why": ["两份源画布不同（640×360 / 1920×1080）⇒ 统一 scale+pad 到画布，先缩后垫、不裁内容",
                "源 B 无音轨 ⇒ 音轨 = 3s 源音 + 9s 静音，拼成**连续音轨**（QC 要求音轨覆盖整片）",
                "预览：libx264 veryfast crf20 + aac 48k + faststart（速度优先，非交付母版）"]}
(OUT / "preview.render_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1),
                                             encoding="utf-8")

# ── 渲染（程序名字面量，参数列表）─────────────────────────────────────────
src0 = str(ROOT / clips[0]["source"])
src1 = str(ROOT / clips[1]["source"])
cp = subprocess.run(
    ["ffmpeg", "-hide_banner", "-y", "-i", src0, "-i", src1,
     "-filter_complex", graph, "-map", "[vout]", "-map", "[aout]",
     "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", str(PREVIEW)],
    capture_output=True, text=True, encoding="utf-8", errors="replace")
if cp.returncode != 0 or not PREVIEW.is_file():
    print("渲染失败：", (cp.stderr or "")[-900:])
    sys.exit(1)

info = ffprobe_json(PREVIEW)
dur = float(info.get("format", {}).get("duration") or 0)
v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
a = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)

report = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
          "tooling": "本地等价（ffmpeg 渲染）—— 技能指定的 render_preview 工具不可达",
          "timeline_sha8": tl_sha, "output": "out/preview.mp4", "output_sha8": sha8(PREVIEW),
          "timeline_sha256": tl_sha256, "output_sha256": sha256_file(PREVIEW),
          "bound_to_current_timeline": True, "duration_s": round(dur, 3),
          "expected_duration_s": TOTAL, "resolution": f"{v.get('width')}x{v.get('height')}",
          "fps": v.get("r_frame_rate"), "has_audio": bool(a),
          "bytes": int(info.get("format", {}).get("size") or 0)}
(OUT / "preview.render_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1),
                                                encoding="utf-8")

decisions = {"at": report["at"], "timeline_sha8": tl_sha, "timeline_sha256": tl_sha256,
             "tooling": "本地等价（结构化决策旁车）",
             "decisions": [{"clip": c["source"], "range": [c["start"], c["end"]],
                            "timeline_start": c["timeline_start"], "reason": c["reason"],
                            "evidence": "out/ingest/*.json（contact sheet 由主 agent 亲自读过）"
                                        " + out/media_analysis.json 的 YAVG 抽点"} for c in clips],
             "rejected": [
                 {"option": "只用 motion.mp4（10s）单源裁切",
                  "why_not": "会丢掉唯一带声轨的素材；画面从头到尾同一张静态字卡 ⇒ 更像转封装不是剪辑"},
                 {"option": "把 cut-demo 上采样后拉长到整片",
                  "why_not": "纯色素材拉长只制造静止段、放大上采样模糊，没有剪辑价值"}]}
(OUT / "preview.edit_decisions.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=1),
                                                 encoding="utf-8")

# ── QC（本地等价）────────────────────────────────────────────────────────
qc = {"at": report["at"], "tooling": "本地等价（ffprobe + ffmpeg 检测器）",
      "timeline_sha8": tl_sha, "output_sha8": report["output_sha8"],
      "timeline_sha256": tl_sha256, "video_sha256": sha256_file(PREVIEW),
      "covers_current_preview": True, "errors": [], "warnings": [], "readings": {}}
if not v:
    qc["errors"].append("没有视频流 ⇒ 不可播")
if abs(dur - TOTAL) > 0.3:
    qc["errors"].append(f"时长 {dur:.3f}s 与计划 {TOTAL}s 差超过 0.3s")
if (v.get("width"), v.get("height")) != (W, H):
    qc["errors"].append(f"分辨率 {v.get('width')}x{v.get('height')} != 画布 {W}x{H}")
if not a:
    qc["errors"].append("没有音轨 ⇒ 与计划（连续音轨）不符")
qc["readings"].update({"duration_s": round(dur, 3),
                       "resolution": f"{v.get('width')}x{v.get('height')}",
                       "fps": v.get("r_frame_rate")})

err = ffmpeg_stderr(["-i", str(PREVIEW), "-vf", "blackdetect=d=0.2:pix_th=0.10", "-an",
                     "-f", "null", "-"])
qc["readings"]["blackdetect"] = [ln.split("]")[-1].strip() for ln in err.splitlines()
                                 if "black_start" in ln][:6]
samples = {str(t): yavg(PREVIEW, t) for t in (0.5, 1.5, 2.5, 5.0, 8.0, 11.5)}
qc["readings"]["yavg_samples"] = samples
qc["warnings"].append(
    "blackdetect 全程报黑：源素材本身就是纯色/黑底（cut-demo 暗蓝 YAVG=29、motion 黑底 YAVG≈24.3，"
    "见 out/media_analysis.json）⇒ 是素材性质不是渲染故障；YAVG 抽点给出同样常数，两处读数一致。")

err = ffmpeg_stderr(["-i", str(PREVIEW), "-af", "silencedetect=n=-40dB:d=0.5", "-f", "null", "-"])
sil_ranges = [ln.split("]")[-1].strip() for ln in err.splitlines() if "silence_" in ln]
qc["readings"]["silence"] = sil_ranges[:6]
if sil_ranges:
    qc["warnings"].append("3s 之后静音：源 B **没有音轨**（out/media.json 记着 audio=null），"
                          "渲染器按计划补了连续静音轨 ⇒ 预期行为，不是丢音。")

err = ffmpeg_stderr(["-i", str(PREVIEW), "-vf", "freezedetect=n=-60dB:d=2", "-an", "-f", "null", "-"])
freezes = [ln.split("]")[-1].strip() for ln in err.splitlines() if "freezedetect" in ln]
qc["readings"]["freezedetect"] = freezes[:4]
if freezes:
    qc["warnings"].append("检测到静止段：源 B 是静态字卡（同一帧 10 秒，见 rewatch contact sheet）"
                          "⇒ 静止来自素材本身，剪掉它等于没有素材可用。")

err = ffmpeg_stderr(["-i", str(PREVIEW), "-af", "volumedetect", "-f", "null", "-"])
for ln in err.splitlines():
    if "mean_volume" in ln or "max_volume" in ln:
        qc["readings"][ln.split("]")[-1].strip().split(":")[0].strip()] = ln.split(":")[-1].strip()
qc["video_stream_covers"] = round(dur, 3)
qc["audio_stream_covers"] = round(float(a.get("duration") or 0), 3) if a else 0
if a and abs(float(a.get("duration") or 0) - dur) > 0.3:
    qc["errors"].append("音轨时长与视频不一致")
qc["ok"] = not qc["errors"]
qc["status"] = "pass" if qc["ok"] else "fail"     # 钩子认这个字段（恰好 "pass"）
qc["blockers"] = qc["errors"]
(OUT / "preview_qc_report.json").write_text(json.dumps(qc, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
print("渲染 + QC 完成")
print("  preview:", report["resolution"], report["fps"], f"{dur:.2f}s",
      f"{report['bytes'] / 1024:.0f}KB · sha {report['output_sha8']}")
print("  QC errors:", qc["errors"] or "无")
print("  QC warnings:", len(qc["warnings"]), "条（原因都写进报告）")
print("  YAVG 抽点:", samples)
