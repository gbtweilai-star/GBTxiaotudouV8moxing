# -*- coding: utf-8 -*-
"""视频流水线 · 单一编排器（模型无关 · 真门 · 账本）
对应封面「给 Harness 装上这六个插件，整条流程自动完成」。

    python tools/video/pipeline.py map            # 阶段地图（能力位/判据/回退）
    python tools/video/pipeline.py providers      # 后端可用性（本机实测）
    python tools/video/pipeline.py status         # 全链门检 + 写账本
    python tools/video/pipeline.py probe <mp4>    # 单片客观读数（时长/分辨率/帧率/音轨）
    python tools/video/pipeline.py run S3 --dry   # 看某阶段会落到谁、跑什么

六个插件 → 七个阶段（剪/批量/动效/素材/创意/精修 + 验收发布）：
  S0 素材       Generative Media（media-use / autoglm 生图族）
  S1 创意       Seedance Art（Ark：arkcli-gen → Seedance/Seedream；计费动作须先报价确认）
  S2 剪         Video Cut（videocut-skills 或 ffmpeg 兜底）
  S3 动效       HyperFrames（HTML→确定性 MP4）
  S4 批量       Remotion（React 模板 × N 数据）
  S5 精修       Video Use（EDL 混剪+自评估）或 ffmpeg 收尾
  S6 验收       客观读数（ffprobe）+ 人眼（截图/预览）
  S7 发布       账本 + 清单（废物不上线）
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import time

# 🔴 2026-09-26 补：Windows 管道/重定向下 stdout 回落 GBK，emoji 一打印就崩；与 self_model.py 同一款补丁
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


WS = pathlib.Path(__file__).resolve().parents[2]
OUT = WS / "video-out"                      # 成片/中间件落点（不入仓核心目录）
LEDGER = WS / ".video/ledger.json"

# ── 能力位（阶段只认它，不写死厂商）────────────────────────────────────────
CAPS = {
    "media.assets": "素材：生图/抠图/找图/BGM/SFX/图标",
    "media.creative": "创意：文/图 → 视频片段（云端模型）",
    "video.cut": "剪：切分/删段/拼接/口播清理",
    "video.motion": "动效：HTML/代码 → 确定性 MP4",
    "video.batch": "批量：模板 × 数据 → N 条成片",
    "video.finish": "精修：混剪/调色/字幕/音频收尾",
    "video.probe": "客观读数：时长/分辨率/帧率/音轨",
}

PROVIDERS = {
    "hyperframes": {
        "caps": ["video.motion"],
        "probe": ["npx", "--yes", "hyperframes@latest", "--version"],
        "notes": "Apache-2.0 · HTML+data-* → headless Chrome 逐帧 seek → FFmpeg 编码（确定性：同输入同输出）· 需 Node≥22+FFmpeg",
        "cmds": {"video.motion": "cd \"{project}\" && npx hyperframes render"},
    },
    "remotion": {
        "caps": ["video.batch", "video.motion"],
        "probe": ["npm", "view", "remotion", "version"],   # 引擎按项目安装；这里判"包可达+网络通"
        "notes": "帧编程（React）· 1 模板 × N 数据 = N 视频 · ⚠️ 本体为 source-available 许可，商用需确认",
        "cmds": {"video.batch": "cd \"{project}\" && npx remotion render {comp} \"{out}\""},
    },
    "ffmpeg": {
        "caps": ["video.cut", "video.finish", "video.probe"],
        "probe": ["ffmpeg", "-version"],
        "notes": "本机 8.1.2 · 无依赖、离线、可作任何环节的兜底",
        "cmds": {
            "video.cut": "ffmpeg -y -i \"{in}\" -ss {start} -to {end} -c copy \"{out}\"",
            "video.finish": "ffmpeg -y -i \"{in}\" -vf \"scale={w}:{h}\" -c:v libx264 -crf 18 -pix_fmt yuv420p \"{out}\"",
            "video.probe": "ffprobe -v error -show_entries format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate -of json \"{in}\"",
        },
    },
    "videocut": {
        "caps": ["video.cut"],
        "probe": None,          # 需 Codex 宿主 + Runtime ≥0.5.9（公开 v0.4.11 不满足）
        "notes": "中文口播专精（口误/停顿/重复句）；⚠️ 需 Codex CLI 宿主 + 独立 Runtime≥0.5.9 —— 公开版 0.4.11 不达标，暂不可用",
        "cmds": {},
    },
    "video-use": {
        "caps": ["video.finish", "video.cut"],
        "probe": None,          # 需 uv + ELEVENLABS_API_KEY（付费）⇒ 未装
        "notes": "多素材混剪 · 转录→EDL→渲染→**自评估**（每刀边界查跳切/爆音）· 需 uv + ElevenLabs Key（可换本仓 openai-whisper 免付费）",
        "cmds": {},
    },
    "arkcli": {
        "caps": ["media.creative", "media.assets"],
        "probe": ["arkcli", "--version"],
        "notes": "Seedance/Seedream（Ark 云端）· 走 gbt-arkcli 规程：调用前缀 + 登录闸 + 账号闸 + **计费先报价后确认**",
        "cmds": {"media.creative": "arkcli +gen ...（按 gbt-arkcli 规程；计费动作须人确认）"},
    },
    "autoglm": {
        "caps": ["media.assets"],
        "probe": ["python", "-c", "import PIL"],
        "notes": "本仓已装：autoglm-generate-image / -seedream / -remove-bg / -search-image",
        "cmds": {"media.assets": "（技能调用，不出命令行）"},
    },
}


def probe(provider: str):
    p = PROVIDERS[provider]
    if p["probe"] is None:
        return None, "需人工/额外前置（见 notes）"
    exe = p["probe"][0]
    found = shutil.which(exe)
    if found:
        exe = found
    else:
        import os
        cand = [pathlib.Path(os.environ.get("APPDATA", "")) / "npm" / f"{exe}.cmd"]
        hit = next((c for c in cand if c.exists()), None)
        if hit is None:
            return False, f"命令不在 PATH：{p['probe'][0]}"
        exe = str(hit)
    try:
        argv = [exe] + list(p["probe"][1:])
        shell = exe.lower().endswith((".cmd", ".bat", ".ps1"))
        r = subprocess.run(" ".join(f'"{x}"' if " " in x else x for x in argv) if shell else argv,
                           shell=shell, capture_output=True, text=True, timeout=90,
                           encoding="utf-8", errors="replace")
        return r.returncode == 0, ((r.stdout or r.stderr or "").strip().splitlines() or [""])[-1][:70]
    except Exception as e:
        return False, f"探测异常 {type(e).__name__}"


def resolve(cap: str, prefer: str | None = None):
    order = ([prefer] if prefer else []) + [k for k in PROVIDERS if k != prefer]
    tried = []
    for k in order:
        if cap not in PROVIDERS[k]["caps"]:
            continue
        ok, note = probe(k)
        if ok is True:
            return k, None
        tried.append(f"{k}({note})")
    return None, "无可用后端；已试：" + "; ".join(tried)


# ── 真门（ffprobe 读数，不认我写的字）──────────────────────────────────────
def video_probe(path: pathlib.Path):
    if not path.exists() or path.stat().st_size == 0:
        return None, f"缺文件 {path.name}"
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size:stream=codec_type,codec_name,width,height,r_frame_rate",
                        "-of", "json", str(path)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        return None, f"ffprobe 失败：{(r.stderr or '')[:80]}"
    d = json.loads(r.stdout or "{}")
    streams = d.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), None)
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    dur = float((d.get("format") or {}).get("duration") or 0)
    return {"duration": round(dur, 3), "video": v, "audio": a,
            "size": int((d.get("format") or {}).get("size") or path.stat().st_size)}, None


def gate_video(path: pathlib.Path, min_dur=0.4, need_audio=False, min_w=320):
    info, err = video_probe(path)
    if err:
        return False, err
    v = info["video"]
    if not v:
        return False, "无视频流"
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    checks = [info["duration"] >= min_dur, min(w, h) >= min_w, (info["audio"] is not None) or not need_audio]
    note = (f"{info['duration']}s · {w}x{h} · {v.get('r_frame_rate')} · "
            f"音轨{'有' if info['audio'] else '无'} · {info['size']/1024:.0f}KB")
    return all(checks), note


S = lambda **kw: kw                                                      # noqa: E731
STAGES = [
    S(id="S0", name="素材", cap="media.assets", gate=lambda: (True, "素材就位（人工/技能产出）"),
      note="生图/抠图/找图/BGM/SFX", fallback="media-use 目录 + autoglm 技能"),
    S(id="S1", name="创意(生成)", cap="media.creative", gate=lambda: (True, "云片段产出（计费动作须确认）"),
      note="Seedance/Seedream（Ark）", fallback="本地录制/录屏代替"),
    S(id="S2", name="剪", cap="video.cut", gate=lambda: (True, "切分/删段"),
      note="videocut（中文口播）或 ffmpeg", fallback="ffmpeg -c copy 无损切"),
    S(id="S3", name="动效(HyperFrames)", cap="video.motion",
      gate=lambda: gate_video(OUT / "motion.mp4") if (OUT / "motion.mp4").exists() else (False, "待产出 video-out/motion.mp4"),
      note="HTML → 确定性 MP4", fallback="Remotion 渲染同段"),
    S(id="S4", name="批量(Remotion)", cap="video.batch",
      gate=lambda: gate_video(OUT / "batch.mp4") if (OUT / "batch.mp4").exists() else (False, "待产出 video-out/batch.mp4"),
      note="模板 × 数据", fallback="HyperFrames 循环出多条"),
    S(id="S5", name="精修", cap="video.finish",
      gate=lambda: gate_video(OUT / "final.mp4", need_audio=False) if (OUT / "final.mp4").exists() else (False, "待产出 video-out/final.mp4"),
      note="混剪/调色/字幕/音频", fallback="ffmpeg 收尾（scale+crf18+yuv420p）"),
    S(id="S6", name="验收", cap="video.probe",
      gate=lambda: gate_video(OUT / "final.mp4") if (OUT / "final.mp4").exists() else (False, "无成片可验"),
      note="客观读数（ffprobe）+ 人眼预览", fallback="人工看片"),
    S(id="S7", name="发布与账本", cap=None,
      gate=lambda: (LEDGER.exists(), "账本已落盘" if LEDGER.exists() else "跑一次 status 即生成"),
      note="清单/来源/许可；废物不上线", fallback="—"),
]


def run_gates(verbose=True):
    rows = []
    for st in STAGES:
        try:
            ok, note = st["gate"]()
        except Exception as e:
            ok, note = False, f"门异常 {type(e).__name__}: {str(e)[:50]}"
        rows.append((st["id"], st["name"], ok, note))
        if verbose:
            print(f"  {'✅' if ok else '❌'} {st['id']:>3} {st['name']:<20} {note}")
    return rows


def ledger_write(rows):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    data = {"updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "stages": [{"id": i, "name": n, "ok": o, "note": t} for i, n, o, t in rows],
            "pass": sum(1 for r in rows if r[2]), "total": len(rows),
            "providers": {k: probe(k)[0] for k in PROVIDERS}}
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "status"
    if cmd == "map":
        print("视频流水线 · 阶段地图（能力位驱动）")
        for st in STAGES:
            print(f"\n{st['id']} · {st['name']}   能力位 {st['cap'] or '（人工）'}")
            print(f"  判据: {st['gate']()[1]}\n  说明: {st['note']}\n  回退: {st['fallback']}")
        return
    if cmd == "providers":
        print("后端可用性（本机实测）")
        for k, p in PROVIDERS.items():
            ok, note = probe(k)
            flag = "✅" if ok is True else ("⚠️" if ok is None else "❌")
            print(f"  {flag} {k:<12} {note}")
        print("\n能力位 → 当前落到谁")
        for cap in CAPS:
            who, why = resolve(cap)
            print(f"  {'✅' if who else '❌'} {cap:<16} → {who or ('无可用：' + (why or ''))}")
        return
    if cmd == "probe":
        if len(a) < 2:
            print("用法: probe <video>"); return
        ok, note = gate_video(pathlib.Path(a[1]))
        print(f"{'✅' if ok else '❌'} {note}")
        return
    if cmd == "status":
        print("视频流水线 · 全链门检（ffprobe 真读数）")
        d = ledger_write(run_gates())
        print(f"\n  通过 {d['pass']}/{d['total']} · 账本 → {LEDGER.relative_to(WS)}")
        return
    if cmd == "run":
        if len(a) < 2:
            print("用法: run <S0..S7> [--dry] [--provider <k>]"); return
        st = next((s for s in STAGES if s["id"].lower() == a[1].lower()), None)
        if not st:
            print("无此阶段"); return
        prefer = a[a.index("--provider") + 1] if "--provider" in a else None
        who, why = resolve(st["cap"], prefer) if st["cap"] else (None, "人工阶段")
        if st["cap"] and not who:
            print(f"❌ {st['id']} 需要 {st['cap']}：{why}"); return
        print(f"[{st['id']}] {st['name']} · 能力位 {st['cap']} → {who or '人工'}")
        if who:
            print(f"  坑: {PROVIDERS[who]['notes']}\n  命令: {(PROVIDERS[who]['cmds'] or {}).get(st['cap'], '（见 notes）')}")
        if "--dry" in a:
            return
        ok, note = st["gate"]()
        print(f"  门: {'✅' if ok else '❌'} {note}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
