# gbt-capability: tripo
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""tripo 能力 — AI 生成 3D 数字人 + 自动绑骨 + 100+ 动作（Tripo3D API）。

用户要求的"随便什么动作都可以完成"的实现路径：
  1. 文本/图片 → AI 生成 3D 美少女模型（text-to-model / image-to-model）
  2. 自动绑骨 rig（biped 人形骨骼，约 30 秒）
  3. 动画重定向 retarget（100+ 预设：idle/walk/run/jump/climb/slash/shoot…）
  4. 下载绑骨+动画 GLB → 桌宠渲染层直接播放任意动作

API（developers.tripo3d.ai 实测文档）：
  Base URL: https://openapi.tripo3d.ai/v3（国内站 developers.tripo3d.com）
  认证: Authorization: Bearer {TRIPO_API_KEY}
  端点: POST /generation/text-to-model → task_id → GET /tasks/{task_id} 轮询
        POST /animations/rig-check（免费预检）→ POST /animations/rig（25 积分）
        POST /animations/retarget（10 积分/个，批量最多 5）
  状态: queued → running → success/failed/cancelled

需要 TRIPO_API_KEY（Tripo 控制台创建）。未配置时如实报告。
"""
from __future__ import annotations

import os
import time
import urllib.request

BASE = os.environ.get("TRIPO_BASE_URL", "https://openapi.tripo3d.ai/v3")


def _key():
    return os.environ.get("TRIPO_API_KEY", "").strip()


def _headers():
    return {"Authorization": f"Bearer {_key()}",
            "Content-Type": "application/json"}


def _post(path, body):
    req = urllib.request.Request(
        BASE + path, data=__import__("json").dumps(body).encode("utf-8"),
        headers=_headers(), method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return __import__("json").loads(resp.read().decode("utf-8"))


def _get(path):
    req = urllib.request.Request(BASE + path, headers=_headers())
    with urllib.request.urlopen(req, timeout=60) as resp:
        return __import__("json").loads(resp.read().decode("utf-8"))


def balance():
    """查积分余额（验证密钥有效性）。"""
    if not _key():
        return {"ok": False, "status": "needs_dependency",
                "missing": "TRIPO_API_KEY",
                "hint": "Tripo 控制台 platform.tripo3d.ai 创建 API Key，"
                        "setx TRIPO_API_KEY <key> 后重试"}
    try:
        r = _get("/account/balance")
        return {"ok": True, "balance": r.get("data", {})}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def text_to_model(prompt, out_format="glb"):
    """文本生成 3D 模型（美少女数字人等），返回 task_id。"""
    if not _key():
        return {"ok": False, "status": "needs_dependency", "missing": "TRIPO_API_KEY"}
    r = _post("/generation/text-to-model", {"prompt": prompt, "format": out_format})
    return {"ok": r.get("code") == 0, "task_id": r.get("data", {}).get("task_id"),
            "raw": r}


def image_to_model(image_path, out_format="glb"):
    """图片生成 3D 模型（先上传文件再引用 task_id）。"""
    if not _key():
        return {"ok": False, "status": "needs_dependency", "missing": "TRIPO_API_KEY"}
    # 1. 上传文件
    boundary = "----gbttripo"
    with open(image_path, "rb") as f:
        img_data = f.read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            f"filename=\"{os.path.basename(image_path)}\"\r\n"
            f"Content-Type: image/png\r\n\r\n").encode() + img_data + \
        f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + "/files", data=body,
        headers={"Authorization": f"Bearer {_key()}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        up = __import__("json").loads(resp.read().decode("utf-8"))
    image_token = up.get("data", {}).get("image_token")
    if not image_token:
        return {"ok": False, "error": "上传失败", "raw": up}
    # 2. 图生 3D
    r = _post("/generation/image-to-model", {"file": {"image_token": image_token}})
    return {"ok": r.get("code") == 0, "task_id": r.get("data", {}).get("task_id"),
            "raw": r}


def task_status(task_id):
    """查任务状态（queued/running/success/failed）。"""
    if not _key():
        return {"ok": False, "status": "needs_dependency", "missing": "TRIPO_API_KEY"}
    r = _get(f"/tasks/{task_id}")
    d = r.get("data", {})
    return {"ok": r.get("code") == 0, "status": d.get("status"),
            "progress": d.get("progress"), "output": d.get("output", {})}


def rig_check(task_id):
    """绑骨前检查（免费）：确认模型可绑骨 + 推荐绑骨类型。"""
    if not _key():
        return {"ok": False, "status": "needs_dependency", "missing": "TRIPO_API_KEY"}
    r = _post("/animations/rig-check", {"original_model_task_id": task_id})
    d = r.get("data", {})
    return {"ok": r.get("code") == 0, "rig_type": d.get("rig_type"),
            "eligible": d.get("eligible", False)}


def rig(task_id, rig_type="biped", out_format="glb"):
    """自动绑骨（25 积分，约 30 秒）：给模型加人形骨骼+权重。"""
    if not _key():
        return {"ok": False, "status": "needs_dependency", "missing": "TRIPO_API_KEY"}
    r = _post("/animations/rig", {"original_model_task_id": task_id,
                                  "rig_type": rig_type,
                                  "out_format": out_format})
    return {"ok": r.get("code") == 0, "task_id": r.get("data", {}).get("task_id")}


def animate(rig_task_id, animation="idle", out_format="glb", in_place=True):
    """动画重定向（10 积分/个）：给绑骨模型套预设动作。

    animation: idle/walk/run/dive/climb/jump/slash/shoot/hurt/fall/turn…
    可传 list 批量（最多 5 个）。
    """
    if not _key():
        return {"ok": False, "status": "needs_dependency", "missing": "TRIPO_API_KEY"}
    body = {"original_model_task_id": rig_task_id,
            "bake_animation": True, "animate_in_place": in_place}
    if isinstance(animation, list):
        body["animations"] = animation[:5]
    else:
        body["animation"] = animation
    r = _post("/animations/retarget", body)
    return {"ok": r.get("code") == 0, "task_id": r.get("data", {}).get("task_id")}


def wait_task(task_id, max_wait_s=300, poll_s=5):
    """轮询任务到完成（success/failed），返回最终输出。"""
    t0 = time.time()
    while time.time() - t0 < max_wait_s:
        st = task_status(task_id)
        if st.get("status") in ("success", "failed", "cancelled"):
            return st
        time.sleep(poll_s)
    return {"ok": False, "error": f"超时 {max_wait_s}s", "last": st if 'st' in dir() else {}}


def full_pipeline(prompt="二次元美少女桌宠数字人，全身，Q版比例，青蓝色全息服装，素模，T-pose",
                  animations=None):
    """一条龙：文生模型 → 绑骨 → 动画 → 返回 GLB 下载地址。"""
    if not _key():
        return {"ok": False, "status": "needs_dependency", "missing": "TRIPO_API_KEY",
                "hint": "platform.tripo3d.ai 注册（送免费积分）→ 创建 Key → setx TRIPO_API_KEY"}
    # 1. 生成
    g = text_to_model(prompt)
    if not g.get("ok"):
        return g
    st = wait_task(g["task_id"], max_wait_s=600)
    if st.get("status") != "success":
        return {"ok": False, "error": "生成失败", "detail": st}
    model_task_id = g["task_id"]
    # 2. 绑骨
    rc = rig_check(model_task_id)
    rg = rig(model_task_id, rig_type=rc.get("rig_type") or "biped")
    if not rg.get("ok"):
        return rg
    rst = wait_task(rg["task_id"], max_wait_s=300)
    if rst.get("status") != "success":
        return {"ok": False, "error": "绑骨失败", "detail": rst}
    # 3. 动画
    outputs = []
    if animations:
        an = animate(rg["task_id"], animations)
        if an.get("ok"):
            ast_ = wait_task(an["task_id"], max_wait_s=300)
            outputs = ast_.get("output", {})
    return {"ok": True, "model_task": model_task_id, "rig_task": rg["task_id"],
            "output": rst.get("output", {}), "animations": outputs}


def status():
    """tripo 状态：配置/余额/能力清单。"""
    if not _key():
        return {"ok": True, "configured": False,
                "capability": "文生3D→绑骨→100+动作（配置 TRIPO_API_KEY 后可用）",
                "hint": "platform.tripo3d.ai 注册（送免费积分）→ 创建 Key → setx TRIPO_API_KEY"}
    bal = balance()
    return {"ok": True, "configured": True, "balance": bal.get("balance"),
            "ops": ["text_to_model", "image_to_model", "rig_check", "rig",
                    "animate", "wait_task", "full_pipeline"]}


def run(op="status", **params):
    """tripo 统一入口：status/text_to_model/image_to_model/rig_check/rig/
    animate/wait_task/full_pipeline。"""
    if op == "status":
        if not _key():
            return {"ok": True, "configured": False,
                    "hint": "配置 TRIPO_API_KEY 后可：文生3D→绑骨→100+动作"}
        return balance()
    if op == "balance":
        return balance()
    if op == "text_to_model":
        return text_to_model(params.get("prompt", ""), params.get("out_format", "glb"))
    if op == "image_to_model":
        return image_to_model(params.get("image_path", ""))
    if op == "task_status":
        return task_status(params.get("task_id", ""))
    if op == "rig_check":
        return rig_check(params.get("task_id", ""))
    if op == "rig":
        return rig(params.get("task_id", ""), params.get("rig_type", "biped"))
    if op == "animate":
        return animate(params.get("task_id", ""), params.get("animation", "idle"))
    if op == "wait_task":
        return wait_task(params.get("task_id", ""), int(params.get("max_wait_s", 300)))
    if op == "full_pipeline":
        return full_pipeline(params.get("prompt", ""), params.get("animations"))
    raise ValueError(f"未知 op: {op}（可用: status/balance/text_to_model/image_to_model/"
                     f"task_status/rig_check/rig/animate/wait_task/full_pipeline）")
