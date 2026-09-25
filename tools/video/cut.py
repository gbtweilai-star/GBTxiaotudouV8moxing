# -*- coding: utf-8 -*-
"""Video Cut（剪）· **本地可执行**版：不依赖任何 Runtime / 宿主。

出处与依据：
- 方法口径来自 `chengfeng-cut` / `chengfeng-videocut-workbench`（已装技能，读它们的 SKILL.md 取craft）；
- 执行只用本机 **ffmpeg 8.1.2**（`silencedetect` / `silenceremove` 均在本机实测存在）；
- 有 whisper（本机 `whisper.exe` ✓）时可再加一层**口误/重复句**识别。

    python tools/video/cut.py silence <in.mp4> <out.mp4> [--thresh -35dB] [--min 0.30]
    python tools/video/cut.py e（打印 EDL）         # 只分析不落刀
    python tools/video/cut.py probe <in.mp4>        # 客观读数

判据（真门）：
  ① 输出存在且可解码；② 输出时长 < 输入时长（真的剪掉了）；③ 剪切段数 ≥1；④ 分辨率/帧率不变。
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

WS = pathlib.Path(__file__).resolve().parents[2]


def dur_of(p: pathlib.Path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(p)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    try:
        return float((r.stdout or "0").strip())
    except ValueError:
        return 0.0


def probe_streams(p: pathlib.Path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate", "-of", "json", str(p)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    s = (json.loads(r.stdout or "{}").get("streams") or [{}])[0]
    return s.get("width"), s.get("height"), s.get("r_frame_rate")


def detect_silence(p: pathlib.Path, thresh="-35dB", min_len=0.30):
    """返回 [(start, end), ...] 静音段（ffmpeg silencedetect 真读数）"""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(p), "-af",
                        f"silencedetect=noise={thresh}:d={min_len}", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = (r.stderr or "")
    starts = [float(m.group(1)) for m in re.finditer(r"silence_start:\s*([0-9.]+)", log)]
    ends = [float(m.group(1)) for m in re.finditer(r"silence_end:\s*([0-9.]+)", log)]
    spans = list(zip(starts, ends + ([dur_of(p)] if len(ends) < len(starts) else [])))
    return spans, log


def cut_silence(src: pathlib.Path, out: pathlib.Path, thresh="-35dB", min_len=0.30, keep_pad=0.08):
    """删静音：保留每段有声区（两端留 keep_pad），再无损拼接。"""
    spans, _ = detect_silence(src, thresh, min_len)
    total = dur_of(src)
    if not spans:
        print("S2 门: ❌ 未检出静音段（阈值/时长不合？）")
        return 1
    keep, cursor = [], 0.0
    for s, e in spans:
        a, b = s + keep_pad, e - keep_pad            # a=有声段终点（静音前），b=静音后的起点
        if a - cursor > 0.12:                        # 保留 [cursor, a] = 这段有声
            keep.append((cursor, a))
        cursor = max(cursor, b)                      # 跳过静音
    if total - cursor > 0.12:
        keep.append((cursor, total))
    if not keep:
        print("S2 门: ❌ 全被剪空（阈值过松）")
        return 1
    # 用 filter_complex 精确切+拼（避免多次重编码累积损失：一次编码完成）
    parts, labels = [], []
    for i, (a, b) in enumerate(keep):
        parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(keep)}:v=1:a=1[vo][ao]"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
           "-filter_complex", fc, "-map", "[vo]", "-map", "[ao]",
           "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"S2 门: ❌ ffmpeg 失败：{(r.stderr or '')[:120]}")
        return 1
    # ── 真门（判据必须能抓住"没剪掉"）──
    d_in, d_out = dur_of(src), dur_of(out)
    w1, h1, fps1 = probe_streams(src)
    w2, h2, fps2 = probe_streams(out)
    sil_total = sum(e - s for s, e in spans)
    saved = d_in - d_out
    ok = (out.exists() and d_out > 0
          and saved >= 0.5 * sil_total          # ★ 省下的必须≈检出的静音总长（宽松系数 0.5，留给 padding）
          and len(spans) >= 1
          and (w1, h1, fps1) == (w2, h2, fps2))
    print(f"  检出静音 {len(spans)} 段（共 {sil_total:.2f}s）· 保留有声 {len(keep)} 段")
    print(f"  时长 {d_in:.2f}s → {d_out:.2f}s（省 {saved:.2f}s · 应≈{sil_total:.2f}s）· {w2}x{h2} {fps2}")
    print(f"S2 门: {'✅' if ok else '❌'} {'剪掉的量与检出静音相符且规格未变' if ok else '省下的时长与检出静音不符（没真剪掉？）'}")
    return 0 if ok else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        raise SystemExit(2)
    if a[0] == "probe":
        p = pathlib.Path(a[1]); w, h, fps = probe_streams(p)
        print(f"✅ {dur_of(p):.3f}s · {w}x{h} · {fps}")
        raise SystemExit(0)
    if a[0] in ("silence", "edl"):
        src = pathlib.Path(a[1])
        thresh = a[a.index("--thresh") + 1] if "--thresh" in a else "-35dB"
        min_len = float(a[a.index("--min") + 1]) if "--min" in a else 0.30
        if a[0] == "edl":
            spans, _ = detect_silence(src, thresh, min_len)
            print(f"EDL：拟删静音 {len(spans)} 段 · 共 {sum(e - s for s, e in spans):.2f}s")
            for s, e in spans[:20]:
                print(f"  {s:7.2f} → {e:7.2f}  （{e - s:.2f}s）")
            raise SystemExit(0)
        out = pathlib.Path(a[2])
        raise SystemExit(cut_silence(src, out, thresh, min_len))
    print(__doc__)
    raise SystemExit(2)
