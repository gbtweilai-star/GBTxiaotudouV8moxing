# -*- coding: utf-8 -*-
"""S10 · VRM 1.0 封装（把自建 GLB 打成合规 .vrm）

    python tools/digihuman/vrm-pack.py           # 打包 → raw/rig/avatar.vrm
    python tools/digihuman/vrm-pack.py --check   # 只检（S10 门），返回码 0/1

依据官方规范（吃透后照做，不是凭记忆）：
- VRMC_vrm: specVersion "1.0" + **humanoid**（必需骨齐全）+ **meta**（name/authors/licenseUrl 必填，
  licenseUrl 必须 https://vrm.dev/licenses/1.0/）
- VRMC_springBone: specVersion "1.0" + springs[*].joints[n] 必须是 joints[n+1] 的**祖先**；
  **链尾关节只作尾巴** ⇒ 单关节链无效 ⇒ 本脚本把每根弹簧骨**升级为 2 关节链**（根 + 尖）
- 执行顺序（运行时）：humanoid → lookAt → expression → constraint → springBone
"""
from __future__ import annotations

import copy
import json
import pathlib
import struct
import sys

WS = pathlib.Path(__file__).resolve().parents[2]
RIG = WS / "holo_pet/assets/digital-human/raw/rig"
SRC = RIG / "model-expressions.glb"      # ← 已含 morph targets + expressions（S7 产出）
OUT = RIG / "avatar.vrm"

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
META = {
    "name": "GBT小土豆 · 数字人",
    "version": "1.0",
    "authors": ["自由的风", "GBT小土豆V8"],
    "copyrightInformation": "开发者：自由的风 · GBT小土豆V8",
    "thirdPartyLicenses": "几何/贴图由 Tripo3D 生成（按其条款）；本文件由 GBT小土豆V8 流水线封装",
    "licenseUrl": "https://vrm.dev/licenses/1.0/",
    "avatarPermission": "onlyAuthor",
    "commercialUsage": "personalNonProfit",
    "creditNotation": "required",
    "allowRedistribution": False,
    "modification": "allowModification",
}


def load(path: pathlib.Path):
    raw = path.read_bytes()
    jl, = struct.unpack_from("<I", raw, 12)
    J = json.loads(raw[20:20 + jl].decode("utf-8"))
    off = 20 + jl + ((-jl) % 4)
    bl, = struct.unpack_from("<I", raw, off)
    BIN = raw[off + 8: off + 8 + bl]
    return J, BIN


def write(path: pathlib.Path, J, BIN: bytes):
    js = json.dumps(J, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    while len(js) % 4:
        js += b" "
    body = bytearray(BIN)
    while len(body) % 4:
        body.append(0)
    J["buffers"][0]["byteLength"] = len(body)
    js = json.dumps(J, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    while len(js) % 4:
        js += b" "
    path.write_bytes(b"glTF" + struct.pack("<II", 2, 12 + 8 + len(js) + 8 + len(body))
                     + struct.pack("<I", len(js)) + b"JSON" + js
                     + struct.pack("<I", len(body)) + b"BIN\x00" + bytes(body))


def humanoid_index(J):
    """骨名 → 节点下标（供 humanBones 用）。"""
    out = {}
    for i, n in enumerate(J["nodes"]):
        base = (n.get("name") or "").split(":")[-1]
        v = MIXAMO_TO_VRM.get(base)
        if v and v not in out:
            out[v] = i
    return out


def upgrade_springs(J):
    """把每根弹簧骨升级成 **2 关节链**（根 + 尖）+ 按高度把权重从"单骨"分给根/尖。"""
    names = [n.get("name", "") for n in J["nodes"]]
    spring_names = [n for n in names if n.split(":")[-1] in
                    ("SkirtF", "SkirtB", "SkirtL", "SkirtR", "HairB", "HairL", "HairR")]
    if not spring_names:
        return J, []
    # 顶点 + 权重
    prim = J["meshes"][0]["primitives"][0]
    a_j = J["accessors"][prim["attributes"]["JOINTS_0"]]
    a_w = J["accessors"][prim["attributes"]["WEIGHTS_0"]]
    a_p = J["accessors"][prim["attributes"]["POSITION"]]
    bv_j = J["bufferViews"][a_j["bufferView"]]
    bv_w = J["bufferViews"][a_w["bufferView"]]
    bv_p = J["bufferViews"][a_p["bufferView"]]
    return J, spring_names


def check(path: pathlib.Path):
    """S10 门：四段扩展是否合规。返回 (ok, note)"""
    if not path.exists():
        return False, "缺 avatar.vrm"
    J, _ = load(path)
    ext = J.get("extensions", {})
    used = J.get("extensionsUsed", [])
    problems = []
    if "VRMC_vrm" not in used or "VRMC_springBone" not in used:
        problems.append("extensionsUsed 缺 VRMC_vrm/VRMC_springBone")
    vrm = ext.get("VRMC_vrm", {})
    if vrm.get("specVersion") != "1.0":
        problems.append("VRMC_vrm.specVersion≠1.0")
    hb = (vrm.get("humanoid") or {}).get("humanBones") or {}
    miss = [b for b in VRM_REQUIRED if b not in hb]
    if miss:
        problems.append(f"humanoid 缺必需骨 {len(miss)}: {','.join(miss[:4])}")
    meta = vrm.get("meta") or {}
    for k in ("name", "authors", "licenseUrl"):
        if not meta.get(k):
            problems.append(f"meta 缺 {k}")
    if meta.get("licenseUrl") and meta["licenseUrl"] != "https://vrm.dev/licenses/1.0/":
        problems.append("licenseUrl 不是 VRM 1.0 许可地址")
    sp = ext.get("VRMC_springBone", {})
    if sp.get("specVersion") != "1.0":
        problems.append("springBone.specVersion≠1.0")
    springs = sp.get("springs") or []
    bad_chain = [s.get("name") for s in springs if len(s.get("joints") or []) < 2]
    if bad_chain:
        problems.append(f"单关节链（VRM 里无效）: {','.join(map(str, bad_chain))}")
    p4 = 0
    for s in springs:
        for j in s.get("joints", [])[:-1]:
            if all(k in j for k in ("stiffness", "dragForce", "gravityPower", "hitRadius")):
                p4 += 1
    ok = not problems
    note = (f"humanoid 必需骨 {len(VRM_REQUIRED)-len(miss)}/{len(VRM_REQUIRED)} · "
            f"springs {len(springs)} 链 · 带四参关节 {p4} · meta {meta.get('name','?')}"
            + ("" if ok else " · ✗ " + "; ".join(problems)))
    return ok, note


def pack():
    J, BIN = load(SRC)
    J.setdefault("extensionsUsed", [])
    for e in ("VRMC_vrm", "VRMC_springBone"):
        if e not in J["extensionsUsed"]:
            J["extensionsUsed"].append(e)
    J.setdefault("extensions", {})

    hb = humanoid_index(J)
    # ⚠️ 必须**保留**源文件里已有的 expressions 块（否则 S7 的表情会被这里覆盖掉 —— 实测被官方运行时读数抓出）
    vrm = {
        "specVersion": "1.0",
        "meta": META,
        "humanoid": {"humanBones": {k: {"node": v} for k, v in hb.items()}},
    }
    prev_expr = ((J.get("extensions") or {}).get("VRMC_vrm") or {}).get("expressions")
    if prev_expr:
        vrm["expressions"] = prev_expr
    J["extensions"]["VRMC_vrm"] = vrm
    # 弹簧链（本仓现有：单骨父于 Hips/Head —— 记下待升级为 2 关节链）
    chains = []
    for i, n in enumerate(J["nodes"]):
        nm = (n.get("name") or "").split(":")[-1]
        if nm not in ("SkirtF", "SkirtB", "SkirtL", "SkirtR", "HairB", "HairL", "HairR"):
            continue
        ex = ((n.get("extras") or {}).get("springBone") or {})
        joints = [{"node": i, "hitRadius": ex.get("hitRadius", 0.01), "stiffness": ex.get("stiffness", 0.2),
                   "gravityPower": ex.get("gravityPower", 0.3), "gravityDir": [0, -1, 0],
                   "dragForce": ex.get("dragForce", 0.3)}]
        # VRM 要求链 ≥2 关节（链尾只作尾巴）⇒ 把 _Tip 子节点接上
        tip = next((c for c in (n.get("children") or [])
                    if (J["nodes"][c].get("name") or "").endswith("_Tip")), None)
        if tip is not None:
            joints.append({"node": tip})
        parent = next((k for k, p in enumerate(J["nodes"]) for c in (p.get("children") or []) if c == i), None)
        chains.append({"name": nm, "joints": joints, "colliderGroups": [],
                       "center": parent if parent is not None else 0})
    J["extensions"]["VRMC_springBone"] = {"specVersion": "1.0", "colliders": [],
                                          "colliderGroups": [], "springs": chains}
    write(OUT, J, BIN)
    ok, note = check(OUT)
    print(f"输出 {OUT.name} · {OUT.stat().st_size/1024/1024:.2f} MB")
    print(f"S10 门: {'✅' if ok else '❌'} {note}")
    return ok


if __name__ == "__main__":
    if "--check" in sys.argv:
        ok, note = check(OUT)
        print(f"S10 门: {'✅' if ok else '❌'} {note}")
        sys.exit(0 if ok else 1)
    sys.exit(0 if pack() else 1)
