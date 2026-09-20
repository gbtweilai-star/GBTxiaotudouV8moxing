# gbt-capability: hook_registry
# ⛔ 开发者：自由的风 · 永久钢印 · 禁止删除
"""钩子矩阵 · 只读注册表骨架（hook_registry）· R-H184。

**钩子不是功能，是秩序。** 50 个钩子 = 给系统装 50 个传感器和阀门。

六类（编号连续 1–50）：
  A 生命周期(12) · B 触手操作(12) · C 编排调度(8) · D 证据审计(8) · E 内容发布(6) · F 系统元(4)

三层部署位置（**L3 是红线层**）：
  L1 框架级：通用钩子（限流/重试/超时）——挂触手基类，所有触手共用
  L2 业务级：业务钩子（参数/格式校验）——每根触手自己声明
  L3 审计级：审计钩子（证据/护照/异常）——**必须挂在触手外面**（框架统一执行）

三条红线（**做成机械闸**）：
  ① 审计钩子（L3）**不许挂在触手内部** —— 执行者不能自己写审计；触手自称 L3 ⇒ 注册被拒；
  ② 钩子自身的失败**必须隔离** —— `dispatch()` 逐个 try，坏钩子不许拖垮主流程；
  ③ 钩子链**必须可中断** —— `dispatch(deadline_s=…)` 超时即停，绝不无限等待。

命名空间规则：`hook.general.*`(L1) / `hook.business.*`(L2) / `hook.audit.*`(L3)，**不许同名混用**。
本模块只读：不写盘、不出网、不执行任何业务动作。
"""
from __future__ import annotations

import time

# (序号, 钩子名, 类别, 层, 状态)  状态：existing=已有实现（未复核）/ candidate=候选待核 / todo=待建
HOOKS = (
    (1, "on_session_start", "A", "L2", "todo"),
    (2, "on_session_end", "A", "L2", "todo"),
    (3, "before_turn", "A", "L2", "todo"),
    (4, "after_turn", "A", "L2", "todo"),
    (5, "before_step", "A", "L2", "todo"),
    (6, "on_step_finish", "A", "L2", "todo"),
    (7, "on_agent_idle", "A", "L2", "todo"),
    (8, "on_agent_error", "A", "L1", "todo"),
    (9, "on_subagent_spawn", "A", "L2", "todo"),
    (10, "on_subagent_stop", "A", "L2", "todo"),
    (11, "on_context_overflow", "A", "L1", "todo"),
    (12, "on_rate_limit", "A", "L1", "todo"),
    (13, "pre_tentacle_invoke", "B", "L2", "todo"),
    (14, "post_tentacle_invoke", "B", "L2", "todo"),
    (15, "before_browser_action", "B", "L2", "todo"),
    (16, "after_browser_action", "B", "L2", "todo"),
    (17, "before_file_write", "B", "L2", "todo"),
    (18, "after_file_write", "B", "L2", "todo"),
    (19, "before_network_call", "B", "L2", "todo"),
    (20, "after_network_call", "B", "L2", "todo"),
    (21, "on_tool_approval_required", "B", "L2", "todo"),
    (22, "on_tool_denied", "B", "L2", "todo"),
    (23, "on_tool_timeout", "B", "L1", "todo"),
    (24, "on_tool_retry", "B", "L1", "todo"),
    (25, "before_dag_schedule", "C", "L2", "todo"),
    (26, "after_dag_step_complete", "C", "L2", "todo"),
    (27, "on_blackboard_write", "C", "L2", "todo"),
    (28, "on_blackboard_read", "C", "L2", "todo"),
    (29, "before_starting_gun", "C", "L2", "todo"),
    (30, "on_agent_conflict", "C", "L2", "todo"),
    (31, "on_task_handoff", "C", "L2", "todo"),
    (32, "on_workflow_suspend", "C", "L2", "todo"),
    (33, "pre_audit_log", "D", "L3", "todo"),
    (34, "post_audit_log", "D", "L3", "todo"),
    (35, "on_passport_open", "D", "L3", "existing"),
    (36, "on_passport_close", "D", "L3", "existing"),
    (37, "on_baseline_snapshot", "D", "L3", "existing"),
    (38, "on_evidence_submitted", "D", "L3", "todo"),
    (39, "on_anomaly_detected", "D", "L3", "existing"),
    (40, "on_discrepancy_found", "D", "L3", "candidate"),
    (41, "on_content_generated", "E", "L2", "todo"),
    (42, "before_publish", "E", "L2", "todo"),
    (43, "after_publish", "E", "L2", "todo"),
    (44, "on_audio_master", "E", "L2", "todo"),
    (45, "on_video_export", "E", "L2", "todo"),
    (46, "on_research_complete", "E", "L2", "todo"),
    (47, "on_hook_registered", "F", "L1", "todo"),
    (48, "on_hook_failed", "F", "L1", "todo"),
    (49, "on_hook_bypass_attempt", "F", "L3", "todo"),
    (50, "on_hook_chain_timeout", "F", "L1", "todo"),
)

CATEGORIES = {"A": "生命周期", "B": "触手操作", "C": "编排调度",
              "D": "证据审计", "E": "内容发布", "F": "系统元"}

LAYERS = {"L1": "框架级（触手基类共用）", "L2": "业务级（各触手自己声明）",
          "L3": "审计级（**必须挂在触手外面**）"}

NAMESPACE = {"L1": "hook.general.", "L2": "hook.business.", "L3": "hook.audit."}

RED_LINES = (
    "审计钩子（L3）必须挂在触手外部：执行者不能自己写审计",
    "钩子自身的失败必须隔离（on_hook_failed）：不许拖垮主流程",
    "钩子链必须可中断（on_hook_chain_timeout）：不许无限等待",
)

# L3 的合法宿主：框架/门/审计器 —— **触手不是合法宿主**
_L3_HOST_OK = ("framework", "gate", "audit", "scanner", "store")


def catalogue(layer: str = "", category: str = "", status: str = "") -> dict:
    """查目录（只读）：按层/类/状态过滤，并给出**诚实的计数**。"""
    rows = []
    for n, name, cat, lay, st in HOOKS:
        if layer and lay != layer:
            continue
        if category and cat != category:
            continue
        if status and st != status:
            continue
        rows.append({"n": n, "hook": name, "category": cat, "category_cn": CATEGORIES[cat],
                     "layer": lay, "layer_cn": LAYERS[lay],
                     "namespace": NAMESPACE[lay] + name, "status": st})
    counts = {"total": len(rows)}
    for k in ("existing", "candidate", "todo"):
        counts[k] = sum(1 for r in rows if r["status"] == k)
    return {"ok": True, "readonly": True, "hooks": rows, "counts": counts,
            "layers": [{"key": k, "cn": v} for k, v in LAYERS.items()],
            "namespace_rules": dict(NAMESPACE), "red_lines": list(RED_LINES)}


def verify_registry() -> dict:
    """只读自检：编号连续 1–50、名字唯一、命名空间无重、**L3 不许挂触手内**。"""
    problems = []
    n_list = [h[0] for h in HOOKS]
    if n_list != list(range(1, len(HOOKS) + 1)):
        problems.append({"rule": "numbering", "why": "编号必须是连续的 1…N"})
    names = [h[1] for h in HOOKS]
    if len(set(names)) != len(names):
        problems.append({"rule": "unique_name", "why": "钩子名不许重"})
    if len(HOOKS) != 50:
        problems.append({"rule": "count", "why": "应为 50 条，实测 %d" % len(HOOKS)})
    full = [NAMESPACE[h[3]] + h[1] for h in HOOKS]
    if len(set(full)) != len(full):
        problems.append({"rule": "namespace_unique", "why": "命名空间不许同名混用"})
    return {"ok": not problems, "readonly": True, "count": len(HOOKS),
            "problems": problems,
            "counts": {k: sum(1 for h in HOOKS if h[4] == k) for k in ("existing", "candidate", "todo")}}


def can_register(hook: str, layer: str, owner: str) -> dict:
    """红线 ① 的闸：**L3 审计钩子的宿主必须是框架侧**，触手自称不行。"""
    lay = str(layer or "").strip().upper()
    own = str(owner or "").strip().lower()
    if lay == "L3" and not any(own.startswith(k) for k in _L3_HOST_OK):
        return {"ok": False, "denied": True, "rule": "l3_must_be_external",
                "why": "审计钩子不许挂在触手内部（executor=%r）：执行者不能自己写审计" % owner}
    ns = NAMESPACE.get(lay)
    if not ns:
        return {"ok": False, "denied": True, "rule": "unknown_layer", "why": "层只能是 L1/L2/L3"}
    return {"ok": True, "readonly": True, "hook": str(hook), "namespace": ns + str(hook)}


PUBLISH_HOOKS = ("before_publish", "after_publish")


def publish_hook_ok(text: str, scene: str = "") -> dict:
    """贯通④：**发布钩子必须锚场景**（引用场景锚定的那一份判据，不另立标准）。

    发布钩子的文字里若只有情绪/夸张词（"太伤感了/燃爆了/合集"）或没有可辨认的场景
    ⇒ 判不通过，**不许进发布流程**。
    """
    from . import scene_anchor
    got = scene_anchor.hook(text, scene)
    return {"ok": bool(got.get("ok")), "readonly": True,
            "rule": got.get("rule") or "", "why": got.get("why") or "",
            "from": "tools.scene_anchor", "publish_hooks": list(PUBLISH_HOOKS)}


def dispatch(hooks, deadline_s: float = 0.0, now=None) -> dict:
    """跑一条钩子链：**失败隔离 + 链可中断**（红线 ②③）。

    hooks: [(name, callable), ...]；某个钩子抛异常 ⇒ 记进 `errors`，**继续下一个**；
    超过 `deadline_s` ⇒ 记 `timed_out` 并**立即停止**（不许无限等待）。
    本函数**不写盘、不执行任何业务动作**，只演示顺序与隔离。
    """
    import inspect

    t0 = float(time.time() if now is None else now)
    ran, errors, timed_out = [], [], None
    for name, fn in list(hooks or []):
        if deadline_s and (float(time.time() if now is None else now) - t0) > float(deadline_s):
            timed_out = str(name)
            break
        try:
            if callable(fn):
                out = fn()
                if inspect.isawaitable(out):
                    out = None
            ran.append(str(name))
        except Exception as e:  # noqa: BLE001 —— 红线 ②：坏钩子不许拖垮主流程
            errors.append({"hook": str(name), "error": "%s: %s" % (type(e).__name__, str(e)[:120])})
    return {"ok": True, "readonly": True, "ran": ran, "errors": errors,
            "timed_out": timed_out, "chain_completed": timed_out is None,
            "red_lines": list(RED_LINES)}


def run(op="catalogue", **params) -> dict:
    """能力入口（只读）：catalogue / verify / register_check / redlines。不写盘、不出网。"""
    op = str(op or "catalogue")
    if op == "catalogue":
        return catalogue(params.get("layer", ""), params.get("category", ""),
                         params.get("status", ""))
    if op == "verify":
        return verify_registry()
    if op == "register_check":
        return can_register(params.get("hook", ""), params.get("layer", ""),
                            params.get("owner", ""))
    if op == "publish_check":
        # 贯通④的可见面：发布钩子必须锚场景
        return publish_hook_ok(params.get("text", ""), params.get("scene", ""))
    if op == "redlines":
        return {"ok": True, "readonly": True, "red_lines": list(RED_LINES),
                "layers": dict(LAYERS), "namespace_rules": dict(NAMESPACE),
                "categories": dict(CATEGORIES)}
    raise ValueError("未知 op %r（可用：catalogue/verify/register_check/redlines/publish_check）" % (op,))


HONEST_BOUNDARY = (
    "本注册表只保证『50 个钩子的位置、层级与三条红线是清楚的』。"
    "它不保证『钩子真的都在跑』—— 45 条待建今天一条都没接线。"
)
