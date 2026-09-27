# -*- coding: utf-8 -*-
"""数字人 · 单一编排器（**模型无关**版）

    python tools/digihuman/pipeline.py status              # 全链机检门 + 写账本
    python tools/digihuman/pipeline.py providers           # 本机有哪些后端可用 / 每个能力位会落到谁
    python tools/digihuman/pipeline.py map                 # 阶段地图（含能力位/契约/回退）
    python tools/digihuman/pipeline.py run S3 --dry        # 只打印将由哪个后端执行什么命令
    python tools/digihuman/pipeline.py run S3 --provider blender
    python tools/digihuman/pipeline.py use mesh.decimate=blender   # 写进 .digihuman/config.json

口径（Owner 2026-09-22）：
- **契约与门固定**（阶段/输入输出/判据见技能 references/full-pipeline.md）；
- **"谁来做"可换**：阶段只声明**能力位**（geom.generate / mesh.decimate / rig.auto …），
  由 providers.py 的注册表解析后端；缺后端就**如实说缺**，绝不假装能跑。
"""
from __future__ import annotations

import json
import pathlib
import struct
import subprocess
import sys
import time

# 🔴 2026-09-26 补：Windows 管道/重定向下 stdout 回落 GBK，emoji 一打印就崩；与 self_model.py 同一款补丁
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import providers as P                                                    # noqa: E402

WS = pathlib.Path(__file__).resolve().parents[2]
DH = WS / "holo_pet/assets/digital-human"
RIG = DH / "raw/rig"
LEDGER = WS / ".digihuman/ledger.json"
DEEP = "--deep" in sys.argv          # --deep：跑重门（官方运行时验收，需本地服务 8788）

VRM_REQUIRED = ["hips", "spine", "head", "leftUpperArm", "leftLowerArm", "leftHand",
                "rightUpperArm", "rightLowerArm", "rightHand",
                "leftUpperLeg", "leftLowerLeg", "leftFoot",
                "rightUpperLeg", "rightLowerLeg", "rightFoot"]
MIXAMO_TO_VRM = {
    "Hips": "hips", "Spine": "spine", "Spine1": "chest", "Spine2": "upperChest",
    "Neck": "neck", "Head": "head",
    "LeftShoulder": "leftShoulder", "LeftArm": "leftUpperArm", "LeftForeArm": "leftLowerArm",
    "LeftHand": "leftHand", "RightShoulder": "rightShoulder", "RightArm": "rightUpperArm",
    "RightForeArm": "rightLowerArm", "RightHand": "rightHand",
    "LeftUpLeg": "leftUpperLeg", "LeftLeg": "leftLowerLeg", "LeftFoot": "leftFoot",
    "LeftToeBase": "leftToes", "RightUpLeg": "rightUpperLeg", "RightLeg": "rightLowerLeg",
    "RightFoot": "rightFoot", "RightToeBase": "rightToes",
}


def read_glb(path: pathlib.Path):
    raw = path.read_bytes()
    jl, = struct.unpack_from("<I", raw, 12)
    J = json.loads(raw[20:20 + jl].decode("utf-8"))
    off = 20 + jl + ((-jl) % 4)
    bl, = struct.unpack_from("<I", raw, off)
    return J, raw[off + 8: off + 8 + bl]


# ── 门（纯标准库 · 与后端无关）─────────────────────────────────────────────
def gate_glb_refs(path: pathlib.Path):
    J, _ = read_glb(path)
    bv, acc = len(J.get("bufferViews", [])), len(J.get("accessors", []))
    bad = []
    for i, a in enumerate(J.get("accessors", [])):
        if a.get("bufferView", -1) >= bv:
            bad.append(f"accessor{i}")
    for i, im in enumerate(J.get("images", [])):
        if im.get("bufferView", -1) >= bv:
            bad.append(f"image{i}")
    for m in J.get("meshes", []):
        for p in m.get("primitives", []):
            if p.get("indices", 0) >= acc:
                bad.append("indices")
            for tg in p.get("targets", []):
                for v in tg.values():
                    if v >= acc:
                        bad.append("target")
    return (not bad), ("全部合法" if not bad else "越界:" + ",".join(bad[:4]))


def gate_rig(path: pathlib.Path):
    J, BIN = read_glb(path)
    skins = J.get("skins") or []
    if not skins:
        return False, "无 skin"
    joints = skins[0]["joints"]
    mapped = {(J["nodes"][j].get("name", "").split(":")[-1] and
               MIXAMO_TO_VRM.get(J["nodes"][j].get("name", "").split(":")[-1])) for j in joints}
    miss = [b for b in VRM_REQUIRED if b not in mapped]
    prim = J["meshes"][0]["primitives"][0]
    has_jw = "JOINTS_0" in prim["attributes"] and "WEIGHTS_0" in prim["attributes"]
    import array
    a = J["accessors"][prim["attributes"]["WEIGHTS_0"]]
    b = J["bufferViews"][a["bufferView"]]
    arr = array.array("f"); arr.frombytes(BIN[b.get("byteOffset", 0): b.get("byteOffset", 0) + a["count"] * 16])
    s = [sum(arr[i * 4:i * 4 + 4]) for i in range(a["count"])]
    ok = len(joints) >= 20 and has_jw and not miss and abs(min(s) - 1) < 1e-3 and abs(max(s) - 1) < 1e-3
    return ok, (f"关节 {len(joints)} · VRM 必需骨缺 {len(miss)} · 权重和 {min(s):.4f}~{max(s):.4f}")


def gate_size(path: pathlib.Path, max_mb: float):
    mb = path.stat().st_size / 1024 / 1024
    return mb <= max_mb, f"{mb:.2f} MB（上限 {max_mb}）"


def gate_exists(paths):
    paths = [pathlib.Path(x) for x in paths]
    # 目录也算存在（Windows 上目录 st_size 常为 0 —— 踩过两次）
    miss = [p for p in paths if not p.exists() or (p.is_file() and p.stat().st_size == 0)]
    return (not miss), ("齐全" if not miss else "缺: " + ", ".join(p.name for p in miss))


def gate_sub(script: str, args=()):
    r = subprocess.run([sys.executable, str(WS / script), *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    lines = (r.stdout or r.stderr or "").strip().splitlines()
    return r.returncode == 0, (lines[-1].replace("S10 门: ", "").replace("S7 门: ", "") if lines else "无输出")


S = lambda **kw: kw                                                     # noqa: E731
STAGES = [
    S(id="S0", name="素材与合规", cap=None, ins=[], outs=[DH / "raw/S0/ref.png"],
      gate=lambda: gate_exists([DH / "raw/phase2a-tpose/T-pose参考-规范化.png"]),
      note="参考图（本仓现有：phase2a-tpose/T-pose参考-规范化.png）", fallback="换更清晰正面全身图"),
    S(id="S1", name="几何生成", cap="geom.generate", ins=[], outs=[DH / "raw/phase1/model.glb"],
      gate=lambda: gate_exists([DH / "raw/phase1/tripo-out"]),
      note="任一图生 3D 后端；产出带贴图的网格", fallback="多视图 / 换模型 / 本地 GPU 模型"),
    S(id="S2", name="姿态规范(T-pose)", cap=None, ins=[], outs=[],
      gate=lambda: gate_sub("tools/digihuman/tpose-check.py"),
      note="机检 4 项（双臂水平/双腿直立/直立/白底）+ 人眼 1 项（无遮挡）", fallback="重生成或手摆"),
    S(id="S3", name="重拓扑/分部位LOD", cap="mesh.decimate", ins=[], outs=[RIG / "model-springs-chains.glb"],
      gate=lambda: gate_size(RIG / "model-springs-chains.glb", 12),
      note="分部位 LOD：脸保密度、身体狠削；保 UV 需 blender/pymeshlab(PLY)", fallback="本地 QEM(PLY) → Blender"),
    S(id="S4", name="UV + PBR 贴图", cap="geom.texture", ins=[], outs=[],
      gate=lambda: gate_sub("tools/digihuman/gates.py",
                            ("textures", str(RIG / "avatar.vrm"))), note="材质槽解析（真读 images 尺寸）", fallback="4K 重烘 / 本地重采样"),
    S(id="S5", name="标准骨架(VRM Humanoid)", cap="rig.auto", ins=[], outs=[RIG / "skeleton.json"],
      gate=lambda: gate_exists([RIG / "skeleton.json"]), note="15 必需骨 + 父子固定关系", fallback="Mixamo / SkinTokens(需 Blender)"),
    S(id="S6", name="蒙皮权重", cap="skin.auto", ins=[], outs=[RIG / "model-rigged-anim.glb"],
      gate=lambda: gate_rig(RIG / "model-rigged-anim.glb") if (RIG / "model-rigged-anim.glb").exists() else (False, "缺"),
      note="权重和=1 · 布料归髋", fallback="区域规则手改"),
    S(id="S7", name="表情/BlendShape", cap="expr.make", ins=[], outs=[RIG / "model-expressions.glb"],
      gate=lambda: gate_sub("tools/digihuman/expr-make.py") if (RIG / "model-expressions.glb").exists() else (False, "缺"),
      note="morph targets + VRMC_vrm.expressions（blink/aa/happy）", fallback="材质驱动表情"),
    S(id="S8", name="动画/重定向", cap="anim.make", ins=[], outs=[RIG / "model-rigged-anim.glb"],
      gate=lambda: gate_sub("tools/digihuman/gates.py",
                            ("anim", str(RIG / "model-rigged-anim.glb"))),
      note="循环类必须闭合（**实测**首末帧差，不写死在注释里）", fallback="Mixamo/动捕重定向（同骨架可换库）"),
    S(id="S9", name="次级动力学", cap="mesh.spring", ins=[], outs=[RIG / "model-springs-chains.glb"],
      gate=lambda: gate_exists([RIG / "model-springs-chains.glb"]), note="链 ≥2 关节（VRM 硬要求）", fallback="先修父骨激励"),
    S(id="S10", name="标准格式封装(VRM)", cap="pack.vrm", ins=[], outs=[RIG / "avatar.vrm"],
      gate=lambda: gate_sub("tools/digihuman/vrm-pack.py", ("--check",)),
      note="VRMC_vrm.humanoid/expressions + VRMC_springBone + meta", fallback="纯 GLB + 自定义扩展"),
    S(id="S11", name="Web 运行时", cap=None, ins=[], outs=[DH / "web/avatar.html"],
      gate=lambda: (gate_exists([DH / "web/avatar.html"]) if not DEEP else
                    (gate_sub("tools/digihuman/vrm-runtime-check.py",
                              ("/gbt-master/fs/holo_pet/assets/digital-human/raw/rig/avatar-vrm-check.glb",))
                     if gate_exists([DH / "web/avatar.html"]) else (False, "缺 avatar.html"))),
      note="three.js / three-vrm · --deep 时用**官方运行时**亲自读 avatar.vrm", fallback="自写 springBone（本仓已实现）"),
    S(id="S12", name="验收(客观+人眼)", cap="render.shot", ins=[], outs=[DH / "STATUS.json"],
      gate=lambda: gate_sub("tools/digihuman/gates.py", ("status", str(DH / "STATUS.json"))),
      note="状态源**字段结构**机检（审计 P0=0/截图另在 --deep）", fallback="人眼看图"),
    S(id="S13", name="发布与账本", cap=None, ins=[], outs=[LEDGER],
      gate=lambda: gate_exists([DH / "STATUS.json"]), note="哈希/来源/许可；废物不上线", fallback="—"),
]


def run_gates(verbose=True):
    rows = []
    for st in STAGES:
        try:
            ok, note = st["gate"]()
        except Exception as e:
            ok, note = False, f"门异常: {type(e).__name__}: {str(e)[:60]}"
        rows.append((st["id"], st["name"], ok, note))
        if verbose:
            print(f"  {'✅' if ok else '❌'} {st['id']:>3} {st['name']:<22} {note}")
    return rows


def ledger_write(rows):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    data = {"updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "stages": [{"id": i, "name": n, "ok": ok, "note": note} for i, n, ok, note in rows],
            "pass": sum(1 for r in rows if r[2]), "total": len(rows),
            "providers": {k: v for k, v in P.availability().items()}}
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def cmd_providers():
    print("后端可用性（本机实测）")
    av = P.availability()
    for k, v in av.items():
        flag = "✅" if v["ok"] is True else ("⚠️" if v["ok"] is None else "❌")
        print(f"  {flag} {k:<10} {v['note']}")
    print("\n能力位 → 当前会落到谁（模型无关解析：显式 → 配置 → 可用顺序）")
    for cap in P.CAPS:
        who, why = P.resolve(cap)
        print(f"  {'✅' if who else '❌'} {cap:<16} → {who or ('无可用：' + (why or ''))}")


def cmd_map():
    print("阶段地图（能力位驱动 · 模型无关）")
    for st in STAGES:
        print(f"\n{st['id']} · {st['name']}   能力位: {st['cap'] or '（人工/本仓固定）'}")
        print(f"  判据  : {st['gate']()[1]}")
        print(f"  说明  : {st['note']}")
        print(f"  回退  : {st['fallback']}")


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "status"
    if cmd == "providers":
        cmd_providers(); return
    if cmd == "map":
        cmd_map(); return
    if cmd in ("status", "verify"):
        print("数字人流水线 · 全链门检（机检项 · 与后端无关）")
        d = ledger_write(run_gates())
        print(f"\n  通过 {d['pass']}/{d['total']} · 账本 → {LEDGER.relative_to(WS)}")
        return
    if cmd == "use":
        if len(a) < 2 or "=" not in a[1]:
            print("用法: use <能力位>=<后端>   例: use mesh.decimate=blender"); return
        cap, prov = a[1].split("=", 1)
        if cap not in P.CAPS:
            print(f"未知能力位 {cap}；可选：{', '.join(P.CAPS)}"); return
        if prov not in P.PROVIDERS:
            print(f"未知后端 {prov}；可选：{', '.join(P.PROVIDERS)}"); return
        cfg = P.load_config(); cfg[cap] = prov; P.save_config(cfg)
        print(f"已写入配置：{cap} → {prov}（.digihuman/config.json）"); return
    if cmd == "run":
        if len(a) < 2:
            print("用法: run <S0..S13> [--dry] [--provider <后端>]"); return
        st = next((s for s in STAGES if s["id"].lower() == a[1].lower()), None)
        if not st:
            print(f"没有这个阶段: {a[1]}"); return
        # 🔴 2026-09-26 自纠：--provider 恰为末参时 a[i+1] 会 IndexError
        _pi = a.index("--provider") if "--provider" in a else -1
        prefer = a[_pi + 1] if _pi != -1 and _pi + 1 < len(a) else None
        dry = "--dry" in a
        if not st["cap"]:
            print(f"[{st['id']}] {st['name']}：人工/本仓固定环节\n  {st['note']}\n  回退: {st['fallback']}")
            if not dry:
                ok, note = st["gate"]()
                print(f"  门: {'✅' if ok else '❌'} {note}")
            return
        who, why = P.resolve(st["cap"], prefer=prefer)
        if not who:
            print(f"❌ {st['id']} 需要能力位 {st['cap']}，但本机没有可用后端：{why}")
            print(f"   → 装/登录任一支持该能力的后端，或 `use {st['cap']}=<后端>` 指定"); return
        if prefer and who != prefer:
            print(f"ℹ️ 指定后端 {prefer} 不可用 ⇒ 按可用顺序回退到 **{who}**")
        tmpl = (P.PROVIDERS[who]["cmds"] or {}).get(st["cap"], "")
        print(f"[{st['id']}] {st['name']} · 能力位 {st['cap']} → 后端 **{who}**")
        print(f"  成本: {P.PROVIDERS[who]['cost']}\n  坑: {P.PROVIDERS[who]['notes']}\n  命令: {tmpl or '（该后端未声明模板）'}")
        if dry:
            return
        if not tmpl:
            print("  该后端未声明可执行模板 ⇒ 按它的 notes 人工执行"); return
        r = subprocess.run(tmpl, shell=True, cwd=str(WS))
        ok, note = st["gate"]()
        print(f"  退出码 {r.returncode} · 门: {'✅' if ok else '❌'} {note}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
