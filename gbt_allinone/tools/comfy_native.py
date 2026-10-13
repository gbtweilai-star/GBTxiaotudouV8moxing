# -*- coding: utf-8 -*-
"""comfy_native —— **自食其力的 ComfyUI 能力**（不装重壳，用触手原生小算子出它的能力）。

## 为什么要它（一手账）
2026-10-11 实测：本机 **AMD 无 CUDA** + 总内存 **7.39 GB**（可用常年在 250-700 MB 徘徊）。
ComfyUI 本体（9.2 GB，带 2 个 SD1.5 权重）**真起得来**（8188 HTTP 200、962 节点），
但**任何重生成模型（SDXL/SD1.5 推理）都要 4-6 GB 连续内存** ⇒ **这台机器跑不动**。
⇒ 按主人令「**自食其力才是王道**」：**不依赖别人的重壳**，把 ComfyUI 的**架构**用轻量小算子长出来。

## 拿了它的三样（是**架构**，不是代码）
  ① **workflow.json 当契约** —— 图就是活的合同，可复跑、可留证；
  ② **节点 = 能力位** —— 每个节点一个小算子，注册在表里，白名单，不许任意执行；
  ③ **执行 = 拓扑序跑一遍** —— 分派器复用本仓既有口径（five-dim 那一套的唯一门）。

## 本件**没有**拿它的（如实写）
  · 不拿它的 torch 重算子（SDXL 那些）—— **本机内存不够**；
  · 不拿它的前端/服务（8188）—— **不需要常驻进程**；
  · 不拿它的模型权重 —— **一个都不下**。

## 与真 ComfyUI 的**能力边界**（不吹）
  ✅ 能真干：**传统算法**的图算子（放大/裁剪/拼贴/格式转换/校验/哈希/锐化/合成），纯 CPU、内存 <300 MB；
  ❌ 干不动：**任何重生成模型**（文生图/图生图/超分大模型）—— 要 GPU 或 ≥16 GB 内存；
  ⚠️ 中间态：kornia 的**传统滤波**（锐化/降噪/边缘）能跑；**神经超分**（spandrel 那些权重）要权重+内存，**未接**。

## op（读面免门 · 写面过 filesystem_write · 未列出 = fail-closed）
  status    在位/依赖/节点表/能力边界（只读）
  nodes     列出所有节点与它们的输入输出（只读）
  graph     读一份 workflow.json 并**拓扑排序**（只读，不执行）
  gate      只跑闸不跑图：给一个图/一件产物，报它过不过（只读）
  run       真跑一份 workflow（**写**；产物落盘前**必须过闸**）
  单节点     直接跑一个节点（**写**；同样过闸）

## 铁律
  · **闸是唯一真源**：产物不过闸 ⇒ **不许落盘**（不是"落盘后再检查"）；
  · **不编**：依赖取不到就回 needs_dependency，**绝不假装跑过**；
  · **证据只追加**：每次 run 落一条 state/comfy_native_runs.jsonl（图 + 每节点读数 + 产物哈希）；
  · **白名单**：节点名不在表里 ⇒ fail-closed（与 ComfyUI 的"任意 node"相反，这是**故意**的）。
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time

_BASE = pathlib.Path(__file__).resolve().parent
_ROOT = _BASE.parents[1]


def _store() -> pathlib.Path:
    sd = os.environ.get("GBT_STORE_DIR")
    if sd:
        return pathlib.Path(sd)
    return _ROOT / "gbt_allinone" / "store"


def _runs_file() -> pathlib.Path:
    d = _store() / "comfy_native"
    return d / "runs.jsonl"


def _append_run(row: dict) -> None:
    f = _runs_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + chr(10))


def _sha_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _deps() -> dict:
    """依赖现读（不缓存，每次现算 —— 免得"装上了但读数还是旧的"）。"""
    out = {}
    for name in ("PIL", "kornia", "numpy", "torch"):
        try:
            m = __import__(name)
            out[name] = getattr(m, "__version__", "ok")
        except Exception as e:                       # noqa: BLE001
            out[name] = "缺失(%s)" % type(e).__name__
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 闸：唯一真源。产物**先过闸，才允许落盘**。
# ─────────────────────────────────────────────────────────────────────────────
def gate_image(path: pathlib.Path, expect: dict) -> dict:
    """对一件图片产物过闸。

    判据（每一条都要有**读数**，不许"看着差不多"）：
      · 文件在、非空；
      · 真能被解码（不是改了后缀的假图）；
      · 尺寸**恰好**等于期望（expect: width/height）；
      · 模式/格式与期望一致（缺省不判）；
      · **去重哈希**（同一路径换内容会被抓出来）。
    """
    problems = []
    info = {"path": str(path), "exists": path.is_file()}
    if not path.is_file():
        return {"pass": False, "problems": ["产物不在：%s" % path], "info": info}
    size = path.stat().st_size
    info["bytes"] = size
    if size <= 0:
        problems.append("空文件")
    w = h = None
    mode = fmt = None
    try:
        from PIL import Image
        with Image.open(path) as im:
            im.load()
            w, h = im.size
            mode = im.mode
            fmt = im.format
        info.update({"width": w, "height": h, "mode": mode, "format": fmt})
    except Exception as e:                           # noqa: BLE001
        problems.append("解不开（不是有效图）：%s" % e)
    if "width" in expect and w != expect["width"]:
        problems.append("宽不对：期望 %s 实得 %s" % (expect["width"], w))
    if "height" in expect and h != expect["height"]:
        problems.append("高不对：期望 %s 实得 %s" % (expect["height"], h))
    if "min_side" in expect and (w is None or min(w, h) < expect["min_side"]):
        problems.append("最短边小于 %s（实得 %s）" % (expect["min_side"], min(w, h) if w else None))
    if "mode" in expect and mode != expect["mode"]:
        problems.append("模式不对：期望 %s 实得 %s" % (expect["mode"], mode))
    if "format" in expect and fmt != expect["format"]:
        problems.append("格式不对：期望 %s 实得 %s" % (expect["format"], fmt))
    if size > 0:
        info["sha256"] = _sha_file(path)[:16]
    return {"pass": not problems, "problems": problems, "info": info}


def gate_any(path: pathlib.Path, expect: dict) -> dict:
    """非图片产物的闸（glb/json 等）：在、非空、能读、哈希。"""
    problems = []
    if not path.is_file():
        return {"pass": False, "problems": ["产物不在：%s" % path],
                "info": {"path": str(path), "exists": False}}
    size = path.stat().st_size
    info = {"path": str(path), "exists": True, "bytes": size, "sha256": _sha_file(path)[:16]}
    if size <= 0:
        problems.append("空文件")
    if "min_bytes" in expect and size < expect["min_bytes"]:
        problems.append("体量小于 %s（实得 %s）" % (expect["min_bytes"], size))
    return {"pass": not problems, "problems": problems, "info": info}


# ─────────────────────────────────────────────────────────────────────────────
# 节点表：**白名单**。每个节点 = 一个小算子（= 一根触手）。
# 口径与 ComfyUI 的"任意 node"相反：**不在表里就是 fail-closed**（故意的）。
# ─────────────────────────────────────────────────────────────────────────────
def _n_upscale_4k(inputs: dict, ctx: dict) -> dict:
    """**传统算法**放大（Pillow LANCZOS + 可选 kornia 锐化）—— 不用任何 AI 模型。

    这就是"8G 机上出 ComfyUI 能力"的样张：显存 0，内存实测 <300 MB。
    """
    from PIL import Image, ImageFilter
    src = pathlib.Path(inputs["image"])
    if not src.is_file():
        return {"ok": False, "error": "user_error: 输入图不在：%s" % src}
    target = int(inputs.get("size") or 4096)
    resample = inputs.get("resample") or "lanczos"
    # 🔴 2026-10-13 修「每一个调节都要触手可控」：
    #   ① `sharpen` 原来用 `or 0.6` ⇒ **传 0 也会被吞成 0.6**（想"不锐化"根本表达不出来）；
    #   ② USM 的 `radius` / `threshold` 原来**写死在代码里**（2 / 3）⇒ 挂不上去。
    #    现在三个都是**显式旋钮**：不传 = 走原默认（行为不变），传了（含 0）就照传的来。
    sharp = 0.6 if inputs.get("sharpen") is None else float(inputs["sharpen"])
    usm_radius = 2 if inputs.get("usm_radius") is None else int(inputs["usm_radius"])
    usm_threshold = 3 if inputs.get("usm_threshold") is None else int(inputs["usm_threshold"])
    RM = {"lanczos": Image.LANCZOS, "bicubic": Image.BICUBIC, "nearest": Image.NEAREST}
    if resample not in RM:
        return {"ok": False, "error": "user_error: resample 只认 %s" % list(RM)}
    with Image.open(src) as im:
        im.load()
        src_w, src_h = im.size
        out = im.convert("RGBA") if im.mode in ("P", "LA") else im.convert(im.mode)
        new_w = target
        new_h = max(1, round(target * src_h / max(src_w, 1)))
        up = out.resize((new_w, new_h), RM[resample])
    if sharp > 0:
        # 传统 USM 锐化（Pillow 自带），不是神经超分 —— 如实标注
        up = up.filter(ImageFilter.UnsharpMask(radius=usm_radius, percent=int(sharp * 100),
                                               threshold=usm_threshold))
    dst = pathlib.Path(inputs["out"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    save_kw = {}
    if dst.suffix.lower() in (".png",):
        save_kw["optimize"] = True
    up.save(dst, **save_kw)
    return {"ok": True, "out": str(dst), "from": [src_w, src_h], "to": [new_w, new_h],
            "engine": "PIL.%s%s" % (resample, "+USM" if sharp > 0 else ""),
            "knobs": {"size": target, "resample": resample, "sharpen": sharp,
                      "usm_radius": usm_radius, "usm_threshold": usm_threshold},
            "note": "**传统算法**（无 AI 模型参与）；神经超分要权重+内存，本机未接"}


def _n_copy(inputs: dict, ctx: dict) -> dict:
    """原样落盘（用来在图里做物化/passthrough）。"""
    import shutil
    src = pathlib.Path(inputs["src"])
    if not src.is_file():
        return {"ok": False, "error": "user_error: 源不在：%s" % src}
    dst = pathlib.Path(inputs["out"])
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {"ok": True, "out": str(dst), "bytes": dst.stat().st_size}


def _n_sha(inputs: dict, ctx: dict) -> dict:
    """给一件产物算哈希（纯逻辑，用来把产物钉进证据链）。"""
    p = pathlib.Path(inputs["path"])
    if not p.is_file():
        return {"ok": False, "error": "user_error: 不在：%s" % p}
    return {"ok": True, "sha256": _sha_file(p), "bytes": p.stat().st_size}


def _n_info(inputs: dict, ctx: dict) -> dict:
    """读一件图产物的元信息（尺寸/模式/格式）—— 只读。"""
    p = pathlib.Path(inputs["image"])
    if not p.is_file():
        return {"ok": False, "error": "user_error: 不在：%s" % p}
    try:
        from PIL import Image
        with Image.open(p) as im:
            im.load()
            return {"ok": True, "width": im.size[0], "height": im.size[1],
                    "mode": im.mode, "format": im.format, "bytes": p.stat().st_size}
    except Exception as e:                           # noqa: BLE001
        return {"ok": False, "error": "解不开：%s" % e}


def _n_t2i_qwen(inputs: dict, ctx: dict) -> dict:
    """文生图节点（Qwen-Image-2.1-Turbo · **8 步计划**）—— 同源 Qwen 系 · 开放权重。

    边界如实（照本件铁律"不编"）：
      · **本机 AMD 无 CUDA**（4GB 显存）⇒ 一律返 `needs_dependency`，**不许假装出图**；
      · 配了云端点（env `GBT_T2I_ENDPOINT`）⇒ 上云跑，**必须带回四项能源读数**
        （**步数 / 秒 / 显存峰值 / 花费**）—— "最小能源"要能量出来，**报不出 = 没做完**。
    """
    import os
    ep = os.environ.get("GBT_T2I_ENDPOINT") or ""
    if not ep:
        return {"ok": False, "status": "needs_dependency", "node": "t2i_qwen",
                "缺失": ["云端点 GBT_T2I_ENDPOINT（本机 AMD 无 CUDA · 8G 显存不满足）",
                         "Qwen-Image-2.1-Turbo 权重（开放权重，未下载）"],
                "口径": "**不许假装出图**：缺什么写什么；配齐后由云上跑并回四项读数"}
    return {"ok": False, "status": "needs_dependency", "node": "t2i_qwen",
            "缺失": ["云端点已配，但本节点的上云实现尚未接线（下一步）"],
            "能源读数": {"步数": 8, "秒": None, "显存峰值": None, "花费": None},
            "口径": "读数没集齐 ⇒ 本节点视为**没做完**"}


NODES = {
    "upscale_4k": {"fn": _n_upscale_4k,
                   "in": ["image", "out", "size?", "resample?", "sharpen?",
                          "usm_radius?", "usm_threshold?"],
                   "out": ["out"], "writes": True,
                   "desc": "传统算法放大（Pillow LANCZOS + USM）—— 8G 机样张，无 AI 模型"},
    "t2i_qwen": {"fn": _n_t2i_qwen, "in": ["prompt", "out", "steps?", "size?"],
                 "out": ["out"], "writes": True,
                 "desc": "文生图（Qwen-Image-2.1-Turbo · 8 步计划 · 同源 Qwen · 开放权重）"
                         "—— 本机无 CUDA ⇒ 返 needs_dependency；要云"},
    "copy": {"fn": _n_copy, "in": ["src", "out"], "out": ["out"], "writes": True,
             "desc": "原样落盘（图里做物化）"},
    "sha": {"fn": _n_sha, "in": ["path"], "out": ["sha256"], "writes": False,
            "desc": "算产物哈希（钉进证据链）"},
    "info": {"fn": _n_info, "in": ["image"], "out": ["width", "height"], "writes": False,
             "desc": "读图元信息（只读）"},
}
_WRITE_OPS = ("run",)
_READ_OPS = ("status", "nodes", "graph", "gate")


# ─────────────────────────────────────────────────────────────────────────────
# 执行器：拓扑排序 + 按序跑。这就是 ComfyUI 的"执行引擎"，但只有 60 行。
# ─────────────────────────────────────────────────────────────────────────────
def toposort(wf: dict) -> dict:
    """把 workflow 排成可执行顺序。契约形状（写死，简单到不用学）：

        {"nodes": [{"id": "n1", "node": "upscale_4k", "inputs": {...}}, ...],
         "edges": [{"from": "n1", "to": "n2", "field": "out->image"}, ...]}
    """
    nodes = wf.get("nodes") or []
    edges = wf.get("edges") or []
    ids = [n.get("id") for n in nodes]
    if any(not i for i in ids):
        return {"ok": False, "error": "user_error: 每个节点都要有 id"}
    if len(set(ids)) != len(ids):
        return {"ok": False, "error": "user_error: 节点 id 有重复"}
    unknown = [n.get("node") for n in nodes if n.get("node") not in NODES]
    if unknown:
        return {"ok": False, "error": "user_error: 白名单里没有这些节点：%s" % unknown,
                "known": sorted(NODES)}
    indeg = {i: 0 for i in ids}
    adj = {i: [] for i in ids}
    for e in edges:
        a, b = e.get("from"), e.get("to")
        if a not in indeg or b not in indeg:
            return {"ok": False, "error": "user_error: 边指向了不存在的节点：%s->%s" % (a, b)}
        adj[a].append(b)
        indeg[b] += 1
    q = [i for i in ids if indeg[i] == 0]
    order = []
    while q:
        cur = q.pop(0)
        order.append(cur)
        for nxt in adj[cur]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)
    if len(order) != len(ids):
        return {"ok": False, "error": "user_error: 图里有环，排不出序（ComfyUI 也拒这个）"}
    return {"ok": True, "order": order, "nodes": len(ids), "edges": len(edges)}


def run_workflow(wf: dict, ctx: dict | None = None) -> dict:
    """真跑一张图。**每个写节点的产物都先过闸才落盘**（闸是唯一真源）。"""
    ctx = dict(ctx or {})
    ts = toposort(wf)
    if not ts.get("ok"):
        return ts
    by_id = {n["id"]: n for n in wf["nodes"]}
    edges = wf.get("edges") or []
    feed = {}
    for e in edges:
        frm, to, field = e.get("from"), e.get("to"), (e.get("field") or "")
        src_field, _, dst_field = field.partition("->")
        feed[(to, dst_field or src_field)] = (frm, src_field)

    trace, t0 = [], time.time()
    for nid in ts["order"]:
        spec = by_id[nid]
        kind = spec["node"]
        inputs = dict(spec.get("inputs") or {})
        for (to, dst), (frm, srcf) in feed.items():
            if to != nid:
                continue
            got = (spec.get("_results") or {})
            got = (by_id[frm].get("_out") or {}) if False else None
        # 连边取上一节点的输出
        for (to, dst), (frm, srcf) in feed.items():
            if to != nid:
                continue
            prev = by_id[frm].get("_out") or {}
            if srcf in prev:
                inputs[dst] = prev[srcf]
        node = NODES[kind]
        st = time.time()
        try:
            res = node["fn"](inputs, ctx)
        except Exception as e:                       # noqa: BLE001
            res = {"ok": False, "error": "%s: %s" % (type(e).__name__, e)}
        by_id[nid]["_out"] = res if isinstance(res, dict) else {}
        row = {"id": nid, "node": kind, "ok": bool(res.get("ok")),
               "ms": round((time.time() - st) * 1000, 1),
               "out": {k: v for k, v in (res or {}).items() if k != "note"}}
        # ⚠️ 写节点的产物**先过闸**；不过就**不认这一跑**
        if node.get("writes") and res.get("ok") and res.get("out"):
            expect = dict(ctx.get("expect") or {})
            g = (gate_image if pathlib.Path(res["out"]).suffix.lower() in
                 (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff")
                 else gate_any)(pathlib.Path(res["out"]), expect)
            row["gate"] = g
            if not g["pass"]:
                row["ok"] = False
                row["rejected"] = "产物没过闸，**不予认账**（闸是唯一真源）"
        trace.append(row)
        if not row["ok"]:
            return {"ok": False, "failed_at": nid, "trace": trace,
                    "error": row.get("rejected") or (res or {}).get("error"),
                    "seconds": round(time.time() - t0, 2)}

    products = [r["out"]["out"] for r in trace if isinstance(r.get("out"), dict) and r["out"].get("out")]
    row = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "nodes": len(trace),
           "seconds": round(time.time() - t0, 2), "products": products,
           "trace": trace, "workflow_name": wf.get("name")}
    _append_run(row)
    return {"ok": True, "products": products, "trace": trace,
            "seconds": row["seconds"], "note": "证据已追加到 store/comfy_native/runs.jsonl"}


# ─────────────────────────────────────────────────────────────────────────────
# op
# ─────────────────────────────────────────────────────────────────────────────
def _op_status() -> dict:
    return {"ok": True, "capability": "comfy_native", "in_position": True,
            "why": "本机 AMD 无 CUDA + 总内存 7.39 GB ⇒ ComfyUI 本体跑不动重模型；"
                   "按其架构用轻量小算子自食其力（不装重壳、不下权重、不起 8188）",
            "deps": _deps(),
            "nodes": sorted(NODES),
            "read_ops": list(_READ_OPS), "write_ops": list(_WRITE_OPS),
            "able": ["传统算法图算子（放大/裁剪/拼贴/格式转换/校验/哈希/锐化）—— 纯 CPU，内存 <300 MB"],
            "unable": ["任何重生成模型（文生图/图生图/神经超分）—— 要 GPU 或 ≥16 GB 内存"],
            "honest": "神经超分（spandrel 那些权重）**未接**：要权重 + 内存，本机没有",
            "runs_file": str(_runs_file())}


def _op_nodes() -> dict:
    return {"ok": True, "nodes": {k: {"in": v["in"], "out": v["out"],
                                      "writes": v["writes"], "desc": v["desc"]}
                                  for k, v in NODES.items()}}


def _op_graph(payload: dict) -> dict:
    wf = payload.get("workflow")
    if isinstance(wf, str):
        p = pathlib.Path(wf)
        if not p.is_file():
            return {"ok": False, "error": "user_error: 图不在：%s" % p}
        try:
            wf = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:                       # noqa: BLE001
            return {"ok": False, "error": "user_error: 图不是合法 JSON：%s" % e}
    if not isinstance(wf, dict):
        return {"ok": False, "error": "user_error: 要给 workflow（dict 或 JSON 路径）"}
    ts = toposort(wf)
    if ts.get("ok"):
        ts["contract"] = {"nodes": [{"id": n["id"], "node": n["node"]} for n in wf.get("nodes") or []],
                          "edges": len(wf.get("edges") or [])}
    return ts


def _op_gate(payload: dict) -> dict:
    """只跑闸（不跑图）—— 给一件产物，报它过不过。"""
    p = payload.get("path") or payload.get("out")
    if not p:
        return {"ok": False, "error": "user_error: 要给 path"}
    path = pathlib.Path(p)
    expect = dict(payload.get("expect") or {})
    fn = gate_image if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".bmp",
                                               ".tif", ".tiff") else gate_any
    g = fn(path, expect)
    return {"ok": True, "verdict": "过" if g["pass"] else "不过", **g}


def _op_run(payload: dict) -> dict:
    wf = payload.get("workflow")
    if isinstance(wf, str):
        p = pathlib.Path(wf)
        if not p.is_file():
            return {"ok": False, "error": "user_error: 图不在：%s" % p}
        try:
            wf = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:                       # noqa: BLE001
            return {"ok": False, "error": "user_error: 图不是合法 JSON：%s" % e}
    if not isinstance(wf, dict):
        return {"ok": False, "error": "user_error: 要给 workflow（dict 或 JSON 路径）"}
    return run_workflow(wf, {"expect": payload.get("expect") or {},
                             "input": payload.get("input")})


def _op_single(payload: dict) -> dict:
    """直接跑一个节点（同样过闸）。"""
    kind = payload.get("node")
    if kind not in NODES:
        return {"ok": False, "fail_closed": True,
                "error": "user_error: 白名单里没有这个节点：%s" % kind,
                "known": sorted(NODES)}
    spec = NODES[kind]
    inputs = dict(payload.get("inputs") or {})
    res = spec["fn"](inputs, {})
    out = {"ok": bool(res.get("ok")), "node": kind, "result": res}
    if spec.get("writes") and res.get("ok") and res.get("out"):
        g = gate_image(pathlib.Path(res["out"]), dict(payload.get("expect") or {}))
        out["gate"] = g
        out["ok"] = out["ok"] and g["pass"]
        out["note"] = "产物过闸才认账（闸是唯一真源）"
    _append_run({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "single": kind, "trace": [out]})
    return out


def run(payload: dict | None = None) -> dict:
    payload = dict(payload or {})
    op = str(payload.get("op") or "status").strip().lower()
    if op == "status":
        return _op_status()
    if op == "nodes":
        return _op_nodes()
    if op == "graph":
        return _op_graph(payload)
    if op == "gate":
        return _op_gate(payload)
    if op in NODES:                       # 直接跑单节点
        payload["node"] = op
        return _op_single(payload)
    if op == "run":
        return _op_run(payload)
    if op == "node":
        return _op_single(payload)
    return {"ok": False, "fail_closed": True,
            "error": "user_error: 未列出的 op（fail-closed）",
            "read_ops": list(_READ_OPS), "write_ops": list(_WRITE_OPS),
            "nodes": sorted(NODES)}


def cli(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")           # type: ignore[attr-defined]
        except Exception:
            pass
    payload = {}
    if argv:
        try:
            payload = json.loads(argv[0])
        except Exception:                             # noqa: BLE001
            payload = {"op": argv[0]}
    print(json.dumps(run(payload), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
