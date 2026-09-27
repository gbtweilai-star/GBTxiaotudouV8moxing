# gbt-capability: zimage_rewash
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""zimage_rewash · 洗图流水线（看图 → 反推提示词 → 重绘 → 放大）
⛔ 开发者：自由的风 · GBT小土豆V8 · 永久钢印

立项（Owner 2026-09-27）：把"Z-Image 图生图 + 免费 API 反推"整合成本仓能力。
**诚实前置（三处依赖现读，不编）**：
  · **反推**（图→提示词）：本仓**没有**现成的图像理解能力位——`vision` 域那位是**屏幕**视觉（`privacy_read` 门），
    不吃文件；云 LLM 链（`cloud_llm._KEY_CHAIN`）的 `ask()` 是**纯文本**通道，没有 image content part。
    ⇒ 现状：**未接线**。可行路子两条：①给 `cloud_llm` 加 image part（Agnes 2.5 flash 若认
    `image_url` 就直接通）②接本地 VLM（要装）。**在接通之前，反推由"我"（模型本体）或
    `autoglm-image-recognition` 技能代劳——不是能力位，如实标注。**
  · **重绘**（Z-Image 图生图）：本机**未装 ComfyUI**（GS 插件那次确认过）；
    pollinations 的 img2img 需要**公网可达的图 URL**（本地盘上的图它拉不到）⇒ **未验**。
  · **放大**：✅ **这条今天就能真跑**——ffmpeg lanczos + unsharp 实现在 `op=upscale`，零依赖。

降噪强度（denoise）口径表（Owner 给的原表，存为数据，随 `op=denoise_table` 取）：
  0.15–0.25 抛光（几乎不动，只调色彩/光影/质感）· 0.30–0.45 受控重绘（保结构、重塑细节）·
  0.50–0.65 大胆重绘（保"感觉"与布局）· 0.70–0.85 新想法（原图只当灵感）

门：读面（status/denoise_table）免门；`upscale` 写盘 ⇒ 过 `filesystem_write`。
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

ROOT = Path(r"C:\Users\ADMIN\Desktop\GBT小土豆V8")
READ_OPS = ("status", "denoise_table")
WRITE_OPS = ("upscale", "reverse", "rewash")

DENOISE_TABLE = [
    {"range": "0.15-0.25", "effect": "抛光：几乎完全保留原图，仅微调色彩/光影/质感",
     "use": "照片精修、轻微美化"},
    {"range": "0.30-0.45", "effect": "受控重绘：保主体结构与构图，细节明显重塑",
     "use": "人像精修、风格轻微迁移"},
    {"range": "0.50-0.65", "effect": "大胆重绘：保'感觉'与大致布局，内容可能大变",
     "use": "创意重塑、换风格"},
    {"range": "0.70-0.85", "effect": "新想法：原图只当灵感，生成近乎全新的图",
     "use": "以图为灵感的全新创作"},
]


def _gate(what: str) -> dict | None:
    from .. import auth_gate
    from ..security import policy as _policy
    if _policy.is_trusted():
        return None
    g = auth_gate.check_and_consume("filesystem_write", detail=f"zimage_rewash:{what}"[:60])
    if g.get("ok"):
        return None
    return {"ok": False, "denied": True, "gate": "filesystem_write",
            "error": g.get("error"), "how_to_grant": g.get("how_to_grant")}


def _probe() -> dict:
    comfy = None
    for cand in (Path.home() / "ComfyUI", Path("D:/AI/comfyui"), Path("C:/ComfyUI")):
        if cand.is_dir():
            comfy = str(cand)
            break
    return {
        "reverse": {"ready": False, "why": "无图像理解能力位（vision 是屏幕视觉；云链 ask() 是纯文本）",
                    "unblock": "给 cloud_llm 加 image content part（Agnes 2.5 flash 认 image_url 即通）或装本地 VLM"},
        "rewash": {"ready": False, "why": "本机未装 ComfyUI；pollinations img2img 需公网可达图 URL（本地盘图拉不到）",
                   "unblock": "装 ComfyUI（Z-Image 工作流）或把参考图放到公网可达处再走 pollinations kontext"},
        "upscale": {"ready": shutil.which("ffmpeg") is not None, "why": "ffmpeg lanczos+unsharp（零依赖）",
                    "unblock": "已可用"},
        "comfyui_dir": comfy,
    }


def status(**_kw) -> dict:
    p = _probe()
    return {"ok": True, "op": "status", "kind": "zimage_rewash",
            "read_ops": list(READ_OPS), "write_ops": list(WRITE_OPS),
            "deps": p,
            "口径": "反推/重绘两环**未接线**（如实标缺）；放大环已可用；洗图的降噪口径见 op=denoise_table"}


def denoise_table(**_kw) -> dict:
    return {"ok": True, "op": "denoise_table", "table": DENOISE_TABLE,
            "口径": "降噪强度=图生图的油门；数值越高越偏离原图"}


def upscale(src: str = "", out: str = "", factor: float = 2.0, unsharp: float = 0.6, **_kw) -> dict:
    """高清放大（**今天就能跑的那一环**）：lanczos 重采样 + unsharp 提锐。"""
    deny = _gate("upscale")
    if deny:
        return deny
    if not src:
        return {"ok": False, "error": "需要 src=源图路径"}
    s = Path(src) if Path(src).is_absolute() else ROOT / src
    if not s.is_file():
        return {"ok": False, "error": f"源图不存在：{s}"}
    o = Path(out) if out else s.with_name(f"{s.stem}-x{factor:g}{s.suffix}")
    if not o.is_absolute():
        o = ROOT / o
    o.parent.mkdir(parents=True, exist_ok=True)
    vf = f"scale=iw*{factor}:ih*{factor}:flags=lanczos,unsharp=5:5:{unsharp}"
    r = subprocess.run(["ffmpeg", "-y", "-i", str(s), "-vf", vf, "-q:v", "2", str(o)],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=300, cwd=str(ROOT))
    ok = r.returncode == 0 and o.is_file() and o.stat().st_size > 0
    out_d = {"ok": ok, "op": "upscale", "src": str(s), "out": str(o),
             "bytes": o.stat().st_size if o.is_file() else 0, "vf": vf}
    if not ok:
        out_d["error"] = (r.stderr or "")[-200:]
    return out_d


def reverse(image: str = "", **_kw) -> dict:
    """图像反推（图→提示词）——**未接线**，如实报缺 + 给出接线条件。"""
    return {"ok": False, "op": "reverse", "error_class": "not_wired",
            "error": "本仓没有图像理解能力位（vision 域是屏幕视觉、云链 ask() 是纯文本）",
            "image": image,
            "怎么修": _probe()["reverse"]["unblock"],
            "临时替代": "由模型本体或 autoglm-image-recognition 技能代劳（不是能力位，别当能力位念）"}


def rewash(image: str = "", style: str = "", denoise: float = 0.4, **_kw) -> dict:
    """洗图重绘——**未接线**（缺 ComfyUI / 缺公网图 URL），如实报缺。"""
    band = next((r["range"] for r in DENOISE_TABLE
                 if any(abs(denoise - v) < 0.06 for v in
                        (0.2, 0.375, 0.575, 0.775))), "")
    return {"ok": False, "op": "rewash", "error_class": "not_wired",
            "error": "本机未装 ComfyUI；pollinations img2img 需公网可达图 URL",
            "image": image, "style": style, "denoise": denoise, "denoise_band": band,
            "怎么修": _probe()["rewash"]["unblock"]}


def run(op: str = "status", **kw) -> dict:
    op = (op or "status").lower()
    if op in ("status", "denoise_table"):
        return {"status": status, "denoise_table": denoise_table}[op](**kw)
    if op == "upscale":
        return upscale(**kw)
    if op in ("reverse", "rewash"):
        return {"reverse": reverse, "rewash": rewash}[op](**kw)
    return {"ok": False, "error": f"未知 op:{op}（{'/'.join(READ_OPS + WRITE_OPS)}）",
            "fail_closed": True}
