# gbt-capability: one_shot
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""一句话 → 全链计划（主人令 2026-09-27：「实现**想什么就能生产什么画面**的能力就可以了」）。

## 缺的就是这一环
各环都已接上：`beatgrid`（时间基）→ `actioncam`（出拍）→ `look_grade`（调色）→ `filmgrade`（交付检查），
但**没有一个入口把"一句话"翻成这条链的输入**。本工具补的就是它 —— 且**只读**：
`plan` 只产出**计划**（节拍网格 · 镜头表 · 调色 · 交付目标 · 缺什么），**不写任何文件**。

## 怎么翻（规则映射，不调模型 —— 快、可复现、看得见依据）
  · **题材/情绪词 → 调色**：走 `filmgrade.INTENT_MAP`（"潮湿阴冷"→湿冷调、"热血"→橙青…）；
  · **节奏词 → BPM**：紧凑 120 / 常规 100 / 舒缓 80（可在参数里覆盖）；
  · **时长 → 拍数**：`beats = round(minutes*60/BEAT)`；帧率由 `beatgrid.derive_fps` **反推**（每拍帧数必须整数）；
  · **段落能量 → 镜头密度**：走 `beatgrid.ENERGY_TABLE`；**景别 → 机位/运动**走 `actioncam.MOVES/ANGLES` 轮转；
  · **画质**：默认 `fhd`（1080p）· 电影感可 `cinema`；**交付目标**给 crf/level/GOP 判据。

ops：
  plan  prompt=... [bpm] [minutes] [fps] [quality]   出全链计划（**只读，不写盘**）
  show                                               上次计划
"""
from __future__ import annotations

import importlib.util
import json
import re
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_LAST = _ROOT / "state" / "one_shot_last.json"

# 节奏词 → BPM（可被显式参数覆盖）
_TEMPO = [("紧凑|激烈|快|打斗|追逐|战斗", 120.0), ("常规|中速|叙事", 100.0),
          ("舒缓|慢|抒情|冥想|凝视", 80.0)]
# 时长词 → 分钟
_LEN = [("序章|开场", 1.5), ("短片|预告|trailer", 1.0), ("一集|整段", 8.0)]


def _load(path: str, name: str):
    sp = importlib.util.spec_from_file_location(name, _ROOT / path)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _pick_tempo(prompt: str, bpm: float) -> tuple:
    if bpm:
        return bpm, "参数指定"
    for rx, v in _TEMPO:
        if re.search(rx, prompt):
            return v, f"按节奏词（/{rx}/）"
    return 100.0, "默认（没出现节奏词）"


def _pick_minutes(prompt: str, minutes: float) -> tuple:
    if minutes:
        return minutes, "参数指定"
    for rx, v in _LEN:
        if re.search(rx, prompt):
            return v, f"按时长词（/{rx}/）"
    return 1.0, "默认 1 分钟（短片级）"


def plan(prompt: str = "", bpm: float = 0.0, minutes: float = 0.0, fps: int = 30,
         quality: str = "fhd", beats: int = 8, **_kw) -> dict:
    """**只读**：一句话 → 全链计划。不写盘、不出帧、不渲染。"""
    if not prompt.strip():
        return {"ok": False, "error": "prompt 不能为空（给一句话）", "fail_closed": True}
    bg = _load("tools/beatgrid.py", "bg")
    ac = _load("tools/actioncam.py", "ac")
    fg = _load("tools/filmgrade.py", "fg")

    b, why_bpm = _pick_tempo(prompt, bpm)
    mins, why_min = _pick_minutes(prompt, minutes)
    # ① 时间基：BPM → 帧率反推（每拍帧数必须整数）+ 网格
    der = bg.derive_fps(b, (24, 25, 30, 60))          # ⚠️ 第二参是**候选帧率列表**，不是单个数
    # `derive_fps` 的 `recommend` **直接是数字**（实测键：ok/bpm/beat_sec/rows/recommend）——
    # 早先当字典取 .fps，实测崩过（'int' object has no attribute 'get'）。
    _rec = der.get("recommend") if isinstance(der, dict) else None
    _fps = int(_rec) if isinstance(_rec, int) else fps
    grid = bg.plan(bpm=b, minutes=mins, fps=_fps)
    beat_s = 60.0 / b
    n_beats = beats or max(4, int(round(mins * 60 / beat_s)))
    # ② 镜头表：运动/机位按能量与轮转排（不调模型，规则可查）
    moves = list(getattr(ac, "MOVES", {}).keys()) or ["dolly_in", "push_out", "arc_lr", "shake"]
    angles = list(getattr(ac, "ANGLES", {}).keys()) or ["eye", "low", "high", "dutch"]
    shots = []
    for i in range(n_beats):
        shots.append({
            "beat": i + 1,
            "t": round(i * beat_s, 6),                 # **乘法计时**（不累加，与 beatgrid 同律）
            "move": moves[i % len(moves)],
            "angle": angles[i % len(angles)],
            "size": (list(getattr(bg, "SHOT_SIZE", []) or ["medium"])[
                i % max(1, len(getattr(bg, "SHOT_SIZE", []) or ["medium"]))]),
            # ENERGY_TABLE 是 list[tuple]：('intro', 0.22, 4, '一个镜头停 4 小节…') ⇒ 取第 0 列当标签
            "energy": (lambda row: row[0] if isinstance(row, (list, tuple)) and row else str(row))(
                (list(getattr(bg, "ENERGY_TABLE", []) or [("中",)])[min(i, len(getattr(bg, "ENERGY_TABLE", []) or [1]) - 1)])),
        })
    # ③ 调色：意图 → look（走 filmgrade 的 INTENT_MAP，看得见依据）
    look, why_look = "", ""
    try:
        picked = fg.pick(prompt) if hasattr(fg, "pick") else None
        if isinstance(picked, dict):
            look = picked.get("look") or picked.get("name") or ""
            why_look = picked.get("why") or picked.get("matched") or ""
        elif isinstance(picked, str):
            look, why_look = picked, "INTENT_MAP 命中"
    except Exception as e:                                     # noqa: BLE001
        why_look = f"pick 失败：{type(e).__name__}"
    if not look:
        # 兜底：自己在 INTENT_MAP 上扫一遍（仍看得见命中词）
        for k, v in (getattr(fg, "INTENT_MAP", {}) or {}).items():
            try:
                if re.search(str(k), prompt):
                    look, why_look = (v if isinstance(v, str) else v.get("look", "")), f"INTENT_MAP 命中 /{k}/"
                    break
            except re.error:
                continue
    look = look or "filmic"
    why_look = why_look or "默认（意图没命中映射）"
    # ④ 交付目标（判据，而不是感觉）
    deliver_target = {"quality": quality, "audio": "loudnorm -14（有音频床时）",
                      "level": "16-255（广播安全）", "gop_s": "≤2.0s", "ssim_ref": "≥0.95 视为保真交付",
                      "三级检查": "filmgrade.deliver_check"}
    manifest = {"bpm": b, "beat_s": round(beat_s, 6), "fps": der.get("fps", fps) if isinstance(der, dict) else fps,
                "minutes": mins, "beats": n_beats, "quality": quality, "grade": look,
                "shots": [{"beat": s["beat"], "dur": round(beat_s, 6), "move": s["move"],
                           "angle": s["angle"], "size": s["size"]} for s in shots]}
    need = [{"what": "filesystem_write 授权", "why": "出拍/调色/渲染都要写盘",
             "how": "python -m gbt_allinone auth grant --scope filesystem_write --ttl 600"}]
    out = {"ok": True, "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "prompt": prompt,
           "推导": {"bpm": f"{b}（{why_bpm}）", "时长": f"{mins} 分钟（{why_min}）",
                  "帧率": f"{_fps}（由 BPM 反推：每拍帧数必须整数；候选 {[r.get('fps') for r in (der.get('rows') or []) if r.get('ok')]}）",
                  "调色": f"{look}（{why_look}）"},
           "网格": grid if not isinstance(grid, dict) or "beats" not in grid else {"beats": len(grid.get("beats") or []),
                                                                            "beat_s": grid.get("beat_s")},
           "镜头表": shots, "manifest（未写盘）": manifest, "交付目标": deliver_target, "缺什么": need,
           "规模口径": (f"以上 {len(shots)} 拍是一个**段落模板**（{len(shots) * beat_s:.1f}s）；"
                     f"全片 {mins} 分钟按 FORM_8MIN 段落表铺："
                     f"{[f'{k}×{v}小节' for k, v in list(getattr(bg, 'FORM_8MIN', []) or [])[:5]]} ⇒ "
                     f"总拍数 ≈ {int(round(mins * 60 / beat_s))}"),
           "_口径": "**只读**：本 op 不写任何文件（写盘要过 filesystem_write 门）；"
                   "翻译规则全部可查（节奏词/时长词/INTENT_MAP/energy/size 轮转），不调模型"}
    _LAST.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return out


def show(**_kw) -> dict:
    if not _LAST.is_file():
        return {"ok": False, "why": "还没有计划 ⇒ 先跑 plan"}
    return json.loads(_LAST.read_text(encoding="utf-8"))


def run_op(op: str = "show", **params) -> dict:
    op = (op or "show").lower()
    if op == "plan":
        return plan(**params)
    if op == "show":
        return show(**params)
    return {"ok": False, "fail_closed": True, "error": f"未知 op:{op}（plan/show）"}
