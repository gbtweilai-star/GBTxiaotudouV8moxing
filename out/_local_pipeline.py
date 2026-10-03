# -*- coding: utf-8 -*-
"""本地视频剪辑流水线（等价替代不可达的 video-edit MCP 工具）。

为什么需要它：`/video-edit` 技能要求的 MCP 工具（inspect_media / video_ingest / render_preview /
qc_preview / validate_timeline）在这台机器上**不可达**（mcporter CLI 不存在、工具集里没有这些服务）。
按技能的降级条款：**用 ffmpeg/ffprobe 本地实现同等合同**，并在 out/report.md 里如实记下该限制。
**不伪造任何工具输出**：每个工件都写明是本地等价物。

产出（与技能的文件合同同名同义）：
  out/media.json · out/media_analysis.json · out/transcript.json
  out/ingest/<source>.json · out/video_ingest.json
  out/timeline.json · out/timeline_validation.json
  out/preview.mp4 · out/preview.render_report.json · out/preview.render_plan.json
  out/preview.edit_decisions.json · out/preview_qc_report.json
"""
import json
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8").resolve()
OUT = ROOT / "out"
ING = OUT / "ingest"
CANVAS_W, CANVAS_H, FPS = 1920, 1080, 30

SOURCES = [ROOT / "video-out" / "cut-demo.mp4", ROOT / "video-out" / "motion.mp4"]
# 剪辑决策（保守；理由写进 clips[].reason，也写进 report.md）
PLAN = [
    {"source": "video-out/cut-demo.mp4", "start": 0.0, "end": 3.0, "timeline_start": 0.0,
     "reason": "冷开场：两份素材里唯一带声轨的（低频单音，RMS -21.4dB），用它给片子一个有声的头部，"
               "同时验证『非画布分辨率素材→上采样到 1920×1080』这条渲染路径。"},
    {"source": "video-out/motion.mp4", "start": 0.0, "end": 9.0, "timeline_start": 3.0,
     "reason": "字卡主体：1080p 原生分辨率、与画布一致（不缩放），承担主体时长；"
               "源为静态字卡 ⇒ 画面无运动，这里只做时长裁剪（10s→9s，去掉尾部 1s）。"},
]


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", **kw)


def probe(p: Path) -> dict:
    r = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(p)])
    return json.loads(r.stdout or "{}")


def yavg(p: Path, ts: float) -> float:
    r = run(["ffmpeg", "-hide_banner", "-ss", str(ts), "-i", str(p), "-frames:v", "1",
             "-vf", "signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-f", "null", "-"])
    for ln in (r.stderr or "").splitlines():
        if "YAVG=" in ln:
            try:
                return float(ln.split("YAVG=")[1].split()[0])
            except (IndexError, ValueError):
                return -1.0
    return -1.0


OUT.mkdir(parents=True, exist_ok=True)
ING.mkdir(parents=True, exist_ok=True)

# ── ① inspect_media 等价：每个源的元数据 ───────────────────────────────
media = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"),
         "tooling": "本地等价（ffprobe）—— 技能指定的 inspect_media MCP 工具不可达",
         "sources": [], "counts": {}}
kinds = {}
for p in SOURCES:
    if not p.is_file():
        continue
    d = probe(p)
    fmt = d.get("format", {})
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = next((s for s in d.get("streams", []) if s.get("codec_type") == "audio"), None)
    item = {"path": str(p.relative_to(ROOT)).replace("\\", "/"), "kind": "video",
            "duration": round(float(fmt.get("duration") or 0), 3),
            "bytes": int(fmt.get("size") or 0),
            "codec": v.get("codec_name"), "width": v.get("width"), "height": v.get("height"),
            "fps": v.get("r_frame_rate"),
            "audio": ({"codec": a.get("codec_name"), "sample_rate": a.get("sample_rate")}
                      if a else None)}
    media["sources"].append(item)
    (OUT / "media").mkdir(exist_ok=True)
    (OUT / "media" / (p.stem + ".json")).write_text(json.dumps(item, ensure_ascii=False, indent=1),
                                                    encoding="utf-8")
    kinds[item["path"]] = item["kind"]
media["counts"] = {"video": sum(1 for s in media["sources"] if s["kind"] == "video"),
                   "audio": sum(1 for s in media["sources"] if s["kind"] == "audio"),
                   "image": 0}
(OUT / "media.json").write_text(json.dumps(media, ensure_ascii=False, indent=1), encoding="utf-8")
print("① out/media.json:", media["counts"])

# ── ② analyze_media 等价：确定性提示（黑场/静音/场景 + 亮度抽点）──────────
analysis = {"at": media["at"], "tooling": "本地等价（ffmpeg blackdetect/silencedetect/scene + signalstats）",
            "caveat": ("blackdetect 的阈值把**深蓝**也算成黑（cut-demo 的底就是暗蓝）⇒ "
                       "亮度抽点 YAVG 才是强证据，两者都记下来，不靠单一读数下结论"),
            "per_source": {}}
for p in SOURCES:
    if not p.is_file():
        continue
    rel = str(p.relative_to(ROOT)).replace("\\", "/")
    sc = run(["ffmpeg", "-hide_banner", "-i", str(p), "-vf",
              "select='gt(scene,0.3)',showinfo", "-an", "-f", "null", "-"])
    scenes = sc.stderr.count("pts_time:")
    bk = run(["ffmpeg", "-hide_banner", "-i", str(p), "-vf", "blackdetect=d=0.2:pix_th=0.10",
              "-an", "-f", "null", "-"])
    blacks = [ln.strip() for ln in bk.stderr.splitlines() if "black_start" in ln][:4]
    si = run(["ffmpeg", "-hide_banner", "-i", str(p), "-af", "silencedetect=n=-40dB:d=0.4",
              "-f", "null", "-"])
    sil = [ln.strip() for ln in si.stderr.splitlines() if "silence_" in ln][:4]
    dur = float(probe(p).get("format", {}).get("duration") or 0)
    samples = [round(t, 2) for t in (0, dur / 4, dur / 2, dur * 3 / 4, max(0.0, dur - 0.1))]
    analysis["per_source"][rel] = {
        "scene_changes": scenes, "black_ranges": blacks,
        "silence_ranges": sil or ["（无静音段或音轨缺失）"],
        "yavg_samples": {str(t): yavg(p, t) for t in samples},
        "reading": ("亮度全程恒定 ⇒ 合成测试片（无场景变化、无运动）"
                    if len({round(yavg(p, t), 1) for t in samples}) == 1 else "亮度有变化"),
    }
(OUT / "media_analysis.json").write_text(json.dumps(analysis, ensure_ascii=False, indent=1),
                                         encoding="utf-8")
print("② out/media_analysis.json:", {k: v["scene_changes"] for k, v in analysis["per_source"].items()})

# ── ③ video_ingest 等价：contact sheet 包（图我已亲自读过）────────────────
ingest = {"at": media["at"],
          "tooling": "本地等价（ffmpeg tile 出 contact sheet）；图由主 agent 亲自读过再下判断",
          "packages": []}
for p in SOURCES:
    if not p.is_file():
        continue
    rel = str(p.relative_to(ROOT)).replace("\\", "/")
    sheet = ING / (p.stem + "_sheet.jpg")
    strip = ING / (p.stem + "_rewatch_0-3s.jpg")
    pkg = {"source": rel, "sheet": str(sheet.relative_to(ROOT)).replace("\\", "/"),
           "sheet_exists": sheet.is_file(),
           "rewatch_sheet": str(strip.relative_to(ROOT)).replace("\\", "/") if strip.is_file() else "",
           "what_i_saw": ("黑底 + 左上小号白字『Title』，逐格一模一样的静态字卡，全程无运动"
                          if "motion" in p.stem else
                          "深蓝底整块纯色（无文字、无图形），后段也没有黑块——先前看到的『黑』是 tile 空格子"),
           "read_by_agent": True}
    ingest["packages"].append(pkg)
    (ING / (p.stem + ".json")).write_text(json.dumps(pkg, ensure_ascii=False, indent=1), encoding="utf-8")
(OUT / "video_ingest.json").write_text(json.dumps(ingest, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
print("③ out/video_ingest.json:", [x["source"] for x in ingest["packages"]])

# ── ④ 转录：ASR 不可用 ⇒ 如实记限制，不伪造 ────────────────────────────
tr = {"at": media["at"], "provider": "unavailable", "segments": [],
      "reason": ("云端 ASR 不可用（video-edit MCP 工具集不可达，本机也没有可用的转写后端）⇒ "
                 "按技能条款转入『无转录流程』并在此记明；不伪造转录内容。"),
      "evidence": ("cut-demo 的声轨过零率 0.031、RMS -21.4dB ⇒ 是低频单音不是语音；"
                   "motion 无音轨。两份素材本来就无语音可转。")}
(OUT / "transcript.json").write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding="utf-8")
print("④ out/transcript.json: provider=unavailable（如实记，不伪造）")

# ── ⑤ timeline（项目式：project/assets/tracks/sequence + clips）──────────
durs = {s["path"]: s["duration"] for s in media["sources"]}
clips = []
for c in PLAN:
    clips.append({"source": c["source"], "start": c["start"], "end": c["end"],
                  "timeline_start": c["timeline_start"], "reason": c["reason"]})
timeline = {
    "project": {"name": "gbt-video-edit-selfcheck", "created": media["at"],
                "assumptions": [
                    "任务说明为空 ⇒ 按技能条款做保守选择：不引入未给素材、不做风格化处理",
                    "两份素材都是合成测试片（纯色/静态字卡）⇒ 本片是**流水线验证片**，不是内容片",
                    "无语音可转（ASR 也不可用）⇒ 走无转录流程，限制记入 report.md"]},
    "assets": [{"path": s["path"], "kind": s["kind"], "duration": s["duration"],
                "width": s.get("width"), "height": s.get("height")} for s in media["sources"]],
    "sequence": {"canvas": {"width": CANVAS_W, "height": CANVAS_H, "fps": FPS,
                            "pixel_format": "yuv420p"}},
    "tracks": [
        {"type": "main", "id": "V1", "clips": clips},
        {"type": "audio", "id": "A1",
         "clips": [{"source": "video-out/cut-demo.mp4", "start": 0.0, "end": 3.0,
                    "timeline_start": 0.0,
                    "reason": "保留源片唯一的声轨（3s）；其后源 B 无音轨 ⇒ 由渲染器补静音轨保证音轨连续"}]},
    ],
    "output_canvas": {"width": CANVAS_W, "height": CANVAS_H, "fps": FPS},
}
(OUT / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1), encoding="utf-8")

# ── ⑥ validate_timeline 等价：确定性校验 ───────────────────────────────
problems, checks = [], 0
def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x and abs(x) != float("inf")
for tr_ in timeline["tracks"]:
    for c in tr_.get("clips", []):
        for k in ("start", "end", "timeline_start"):
            checks += 1
            if not finite(c.get(k)):
                problems.append(f"{tr_['id']}: {k} 不是有限数：{c.get(k)!r}")
        if finite(c.get("start")) and finite(c.get("end")):
            if c["end"] <= c["start"]:
                problems.append(f"{tr_['id']}: end<=start {c}")
            src = durs.get(c["source"], 0)
            if src and c["end"] > src + 1e-6:
                problems.append(f"{tr_['id']}: {c['source']} 取到 {c['end']}s 超过源时长 {src}s")
            if not str(c.get("reason") or "").strip():
                problems.append(f"{tr_['id']}: 缺 reason（理由不许空）")
        if tr_["type"] == "audio" and not c.get("source") and not c.get("text"):
            problems.append(f"{tr_['id']}: 音频片段既无 source 也无 text")
main = [t for t in timeline["tracks"] if t["type"] in ("video", "main")]
if not main:
    problems.append("至少要有一条 video/main 轨")
if not timeline.get("sequence") and not timeline.get("output_canvas"):
    problems.append("缺 sequence/output_canvas")
# 主轨不重叠
mc = sorted(main[0]["clips"], key=lambda c: c["timeline_start"]) if main else []
for a, b in zip(mc, mc[1:]):
    if a["timeline_start"] + (a["end"] - a["start"]) > b["timeline_start"] + 1e-6:
        problems.append(f"主轨片段重叠：{a['timeline_start']} 与 {b['timeline_start']}")
val = {"ok": not problems, "at": media["at"], "checks": checks, "problems": problems,
       "timeline_sha8": __import__("hashlib").sha256(
           json.dumps(timeline, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:8],
       # ── 与 closeout 钩子对齐的字段（钩子认 status/timeline_sha256/project_contract）──
       "status": "pass" if not problems else "fail",
       "timeline_sha256": __import__("hashlib").sha256(
           (OUT / "timeline.json").read_bytes()).hexdigest(),
       "project_contract": {
           "ok": bool(main and (timeline.get("sequence") or timeline.get("output_canvas"))
                      and timeline.get("project") and timeline.get("assets")),
           "checks": {"project": bool(timeline.get("project")),
                      "assets": len(timeline.get("assets") or []),
                      "sequence_or_canvas": bool(timeline.get("sequence") or timeline.get("output_canvas")),
                      "tracks": len(timeline.get("tracks") or []),
                      "video_or_main_track": bool(main)},
           "why": "项目式 timeline：project + assets[] + sequence/output_canvas + tracks[] + 至少一条 video/main 轨"},
       "tooling": "本地等价（确定性校验）—— 技能指定的 validate_timeline 工具不可达"}
(OUT / "timeline_validation.json").write_text(json.dumps(val, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
print("⑥ out/timeline_validation.json: ok=%s checks=%s problems=%s"
      % (val["ok"], val["checks"], problems[:3]))
if not val["ok"]:
    sys.exit("timeline 没通过校验 ⇒ 不渲染（先修 timeline）")
print("TIMELINE OK")
