# -*- coding: utf-8 -*-
"""轴系标定 v2：**换探针** —— 不再量"骨末端位移"（末端在自转轴上，天生量不准），
而是量**世界旋转轴**：绕局部某轴转 +deg 后，算 R1·R0⁻¹ 的轴角，轴指向哪个世界方向就是哪个轴上转。

这样「转身/扭头/转腰」这类**绕竖轴的自转**终于量得出来（v1 里它们全是 0）。
判据：每条记录的旋转角必须≈输入角（否则说明该轴没驱动到骨），轴向量长度归一。
用法（Blender）：-b -P calibrate_axes2.py -- <glb> [角度]
"""
import math
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
glb = argv[0]
DEG = float(argv[1]) if len(argv) > 1 else 15.0

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
arm.data.pose_position = "POSE"

BONES = [
    "mixamorig:Hips", "mixamorig:Spine", "mixamorig:Spine2",
    "mixamorig:Neck", "mixamorig:Head",
    "mixamorig:LeftArm", "mixamorig:RightArm",
    "mixamorig:LeftForeArm", "mixamorig:RightForeArm",
    "mixamorig:LeftHand", "mixamorig:RightHand",
    "mixamorig:LeftHandIndex1", "mixamorig:LeftHandThumb1",
    "mixamorig:LeftUpLeg", "mixamorig:RightUpLeg",
    "mixamorig:LeftLeg", "mixamorig:LeftFoot", "mixamorig:LeftToeBase",
]
AX = [("X", 0), ("Y", 1), ("Z", 2)]
NAMES = "XYZ"


def clear():
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()


rows, bad = [], []
for name in BONES:
    pb = arm.pose.bones.get(name)
    if not pb:
        bad.append(name + "(不存在)")
        continue
    clear()
    R0 = pb.matrix.to_3x3()
    cells = []
    for an, idx in AX:
        clear()
        pb.rotation_mode = "XYZ"
        r = [0.0, 0.0, 0.0]
        r[idx] = math.radians(DEG)
        pb.rotation_euler = tuple(r)
        bpy.context.view_layer.update()
        D = pb.matrix.to_3x3() @ R0.inverted()
        q = D.to_quaternion()
        ang = math.degrees(q.angle)
        ax = q.axis
        if ang < 1e-3:
            cells.append("%s=0(没驱动)" % an)
            continue
        j = max(range(3), key=lambda i: abs(ax[i]))
        cells.append("%s→%s%s(%.0f°)" % (an, NAMES[j], "+" if ax[j] > 0 else "-", ang))
        if abs(ang - DEG) > 1.0:
            bad.append("%s.%s 转角偏离 %.1f°" % (name, an, ang - DEG))
    rows.append("%-34s %s" % (name, " · ".join(cells)))

clear()
print("=== 轴系标定 v2（旋转轴探针 · 每轴 +%.0f°）===" % DEG)
for r in rows:
    print("CAL2 " + r)
print("CAL2_红 " + str(bad))
