# gbt-capability: dh_pose
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""数字人动作控制（dh_pose）· 主人令 2026-10-13「触手化作骨架操控数字人的所有动作，都在你可控之内」+「连带手指脚趾都要绑骨」。

这一格管三件事，全部**现读、可机检**：
  · 轴系标定（`calibrate-axes.py`：用**旋转轴探针**量每根骨哪个轴是什么动作）
  · 语义表（`state/dh-pose/semantics.json`：意图 → 骨/轴/符号，**不是猜，是实测**）
  · 摆姿势 / 出动作（编译成骨角度 JSON 后交给 `blender` 位渲染）

🔴 两条实测铁律（都写进语义表的口径）：
  ① 脊柱链的**自转（转身/扭头/转腰）＝局部 Y**——v1 拿「骨末端位移」当探针时 Y 恒为 0，
     因为骨末端正好在自转轴上；**不是没驱动，是量错了地方**。换旋转轴探针才量出来。
  ② 手指脚趾**真绑上了**：65 骨 / 指骨 40 其中 30 有权重 / 趾骨 4 其中 2 有权重；
     无权的 13 根全是末端骨（`Toe_End` 与手指 `*4`），天生不带顶点。

门：`status` / `semantics` / `compile` 是**纯读**（不写盘、不起进程）；`pose` / `acts` 会写盘并起 Blender
     ⇒ 一律经 `blender` 位（那位的 `filesystem_write` 门挂在处理器层），本格不自己造第二道门。
"""
import json
import os
from pathlib import Path

WS = Path(__file__).resolve().parents[2]
SPEC = WS / "state" / "dh-pose" / "semantics.json"
PREFIX = "mixamorig:"
FING = ("Index", "Middle", "Pinky", "Ring", "Thumb")
GLB = "holo_pet/assets/digital-human/raw/rig/model-rigged-anim.glb"
RENDER = "tools/digihuman/render-shot.py"


def _spec() -> dict:
    if not SPEC.is_file():
        return {}
    return json.loads(SPEC.read_text(encoding="utf-8"))


def _side(side: str) -> str:
    return "Left" if str(side).upper().startswith("L") else "Right"


def compile_intent(intent: str, side: str, deg: float):
    """意图 × 侧 × 角度 → {骨名: [rx,ry,rz]}（度）。认不出就如实报，不瞎编。"""
    sp = _spec().get(intent)
    if not sp:
        return {}, "语义表里没有「%s」（现读 state/dh-pose/semantics.json，共 %d 条）" % (
            intent, len([k for k in _spec() if not k.startswith("_")]))
    ai = "XYZ".index(sp["axis"])
    sgn = float(sp.get("sign", 1)) * float((sp.get("side_sign") or {}).get(
        str(side).upper()[:1], 1))
    out = {}
    scale = sp.get("scale") or [1.0]
    for idx, b in enumerate(sp["bones"]):
        sc = scale[idx] if idx < len(scale) else 1.0
        if b.startswith("Hand"):
            for j in (sp.get("joints") or [1]):
                for f in FING:
                    v = [0.0, 0.0, 0.0]
                    v[ai] = sgn * float(deg) * (sc if b.startswith("Hand") else 1.0)
                    out[PREFIX + _side(side) + "Hand" + f + str(j)] = v
        else:
            v = [0.0, 0.0, 0.0]
            v[ai] = sgn * float(deg) * sc
            limb = b in ("Arm", "ForeArm", "Hand", "UpLeg", "Leg", "Foot", "ToeBase",
                         "Shoulder")
            out[PREFIX + (_side(side) if limb else "") + b] = v
    return out, None


def build_pose(cmd: list):
    """cmd = [意图, 侧, 角度, 意图, 侧, 角度…]（角度可为负；侧给 `-` 表示不带左右）。"""
    if not cmd or len(cmd) % 3:
        return None, "命令必须是 3 的倍数：[意图 侧 角度] × N"
    pose, errs = {}, []
    for i in range(0, len(cmd), 3):
        intent, side, deg = cmd[i], cmd[i + 1], cmd[i + 2]
        try:
            d = float(deg)
        except (TypeError, ValueError):
            errs.append("角度不是数：「%s」" % deg)
            continue
        part, err = compile_intent(intent, side, d)
        if err:
            errs.append(err)
            continue
        for k, v in part.items():
            cur = pose.get(k, [0.0, 0.0, 0.0])
            pose[k] = [cur[j] + v[j] for j in range(3)]
    if errs:
        return None, " / ".join(errs)
    return pose, None


def _render(pose: dict, out: str, half: bool = False) -> dict:
    """写临时 pose.json 并交给 blender 位渲染（写盘与起进程的门在那里）。"""
    from . import blender_cap as _bl
    tmp = WS / ".scratch" / "dh_pose" / "_cap_pose.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(pose, ensure_ascii=False), encoding="utf-8")
    args = ["-b", "-P", RENDER, "--", "--glb", GLB, "--pose", str(tmp), "--out", out]
    if half:
        args.append("--half")
    return _bl.run(args=args)


def status(**_kw) -> dict:
    sp = _spec()
    return {"ok": True, "op": "status", "kind": "dh_pose",
            "语义表": str(SPEC.relative_to(WS)), "条数":
                len([k for k in sp if not k.startswith("_")]),
            "骨架来源": GLB,
            "口径": "自转=局部Y（旋转轴探针实测）；指/趾骨已绑（30/40 与 2/4 有权重，其余为末端骨）",
            "不写盘": True}


def semantics(**_kw) -> dict:
    sp = _spec()
    return {"ok": True, "op": "semantics", "kind": "dh_pose", "表": sp}


def compile(cmd=None, **_kw) -> dict:
    pose, err = build_pose(cmd or [])
    if err:
        return {"ok": False, "op": "compile", "error": err, "fail_closed": True}
    return {"ok": True, "op": "compile", "kind": "dh_pose",
            "骨数": len(pose), "pose": pose}


def pose(cmd=None, out="", half=False, **_kw) -> dict:
    bones, err = build_pose(cmd or [])
    if err:
        return {"ok": False, "op": "pose", "error": err, "fail_closed": True}
    dst = out or str(WS / "outputs" / "cloud" / "digital_human_selfintro" / "dh_pose_cap.png")
    r = _render(bones, dst, bool(half))
    return {"ok": bool(r.get("ok")), "op": "pose", "kind": "dh_pose",
            "骨数": len(bones), "出图": dst, "blender": {"exit": r.get("exit"),
                                                        "denied": r.get("denied", False)},
            "尾巴": (r.get("out") or "")[-400:]}


ACTS = WS / "state" / "dh-pose" / "actions.json"


def _acts_spec() -> dict:
    if not ACTS.is_file():
        return {}
    return json.loads(ACTS.read_text(encoding="utf-8")).get("动作", {})


def _lerp_frames(defn: dict):
    """动作定义（语义关键帧）→ 逐帧骨角度：**在语义层插值**，再编译（这样每帧都仍是可读的意图）。"""
    n = int(defn["帧"])
    kfs = sorted(defn["关键帧"], key=lambda k: float(k["相位"]))
    out = []
    for i in range(n):
        p = i / max(1, n - 1)
        lo = kfs[0]
        hi = kfs[-1]
        for j in range(len(kfs) - 1):
            if float(kfs[j]["相位"]) <= p <= float(kfs[j + 1]["相位"]):
                lo, hi = kfs[j], kfs[j + 1]
                break
        span = float(hi["相位"]) - float(lo["相位"])
        t = 0.0 if span <= 1e-9 else (p - float(lo["相位"])) / span
        # 🔴 2026-10-13 主人令「所有的细节都要做到位」：原来 t 是**线性**的 ⇒ 动起来匀速机械。
        #   真人动作起停都有加减速 ⇒ 过一层 smoothstep（首尾导数为 0，中段最快）。
        t = t * t * (3.0 - 2.0 * t)
        vals = {}
        for kf, w in ((lo, 1.0 - t), (hi, t)):
            for it, side, deg in kf.get("语义", []):
                vals[(it, side)] = vals.get((it, side), 0.0) + float(deg) * w
        frame, errs = {}, []
        for (it, side), deg in vals.items():
            if abs(deg) < 1e-6:
                continue
            part, err = compile_intent(it, side, deg)
            if err:
                errs.append(err)
                continue
            for k, v in part.items():
                cur = frame.get(k, [0.0, 0.0, 0.0])
                frame[k] = [cur[q] + v[q] for q in range(3)]
        out.append((frame, errs))
    return out


def acts(action="", out_dir="", list_only=False, **_kw) -> dict:
    """把「动作定义（语义关键帧）」编译成逐帧姿势并渲染成 PNG 序列。

    这是「所有肢体动作都能实现」的正解：动作不是硬编码函数，而是 76 块语义积木的任意组合。
    """
    spec = _acts_spec()
    if not spec:
        return {"ok": False, "op": "acts", "error": "缺 %s" % ACTS, "fail_closed": True}
    if list_only or not action:
        return {"ok": True, "op": "acts", "kind": "dh_pose",
                "动作数": len(spec), "名单": sorted(spec.keys()),
                "定义": str(ACTS.relative_to(WS))}
    if action not in spec:
        return {"ok": False, "op": "acts", "fail_closed": True,
                "error": "动作定义里没有「%s」（现读 %s，共 %d 条）"
                         % (action, ACTS.name, len(spec)), "名单": sorted(spec.keys())}
    frames = _lerp_frames(spec[action])
    errs = sorted({e for _f, es in frames for e in es})
    if errs:
        return {"ok": False, "op": "acts", "fail_closed": True,
                "error": "编译有红：" + " / ".join(errs[:3])}
    dst = out_dir or str(WS / "outputs" / "cloud" / "digital_human_selfintro" / "acts_cap" / action)
    tmp = WS / ".scratch" / "dh_pose" / ("_seq_%s.json" % action)
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps([f for f, _e in frames], ensure_ascii=False), encoding="utf-8")
    from . import blender_cap as _bl
    r = _bl.run(args=["-b", "-P", RENDER, "--", "--glb", GLB, "--pose-seq", str(tmp),
                      "--out", dst])
    return {"ok": bool(r.get("ok")), "op": "acts", "kind": "dh_pose", "动作": action,
            "帧数": len(frames), "出帧目录": dst,
            "blender": {"exit": r.get("exit"), "denied": r.get("denied", False)},
            "尾巴": (r.get("out") or "")[-300:]}


def run(op="status", **params) -> dict:
    fn = {"status": status, "semantics": semantics, "compile": compile, "pose": pose,
          "acts": acts}.get(op)
    if not fn:
        return {"ok": False, "error": "未知 op：%s" % op, "fail_closed": True,
                "ops": ["status", "semantics", "compile", "pose", "acts"]}
    return fn(**params)
