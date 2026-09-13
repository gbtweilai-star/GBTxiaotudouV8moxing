"""GBT小土豆 · 桌面数字人「调皮行为引擎」v3.

分层有限状态机（顶层 IDLE/WANDER/INTERACT/TALK/PLAY/SLEEP）
+ 随机加权微动作调度器（权重随未互动时长变化，越久越爱撒娇）。

约定的对外契约（由 main.py 装配调用）：
    engine = BehaviorEngine(config_dict)
    engine.set_callbacks(
        get_pet_rect=...,     # () -> (x, y, w, h)
        get_panel_rect=...,   # () -> (x, y, w, h) | None（面板隐藏时 None）
        move_pet_to=...,      # (x: int, y: int) -> None
        set_panel_visible=...,# (bool) -> None
        play_motion=...,      # (group: str, priority: int = 1) -> None
        set_expression=...,   # (name: str) -> None
        say=...,              # (text: str) -> None  台词进对话面板
        sync_affection=...,   # 可选（v2 兼容）：好感度变化时同步 UI
    )
    engine.start() / engine.stop()
    engine.on_pet_clicked(part)      # part: Head/Face/Body...（Live2D HitPart）
    engine.on_message(role, text)    # role: "user" / "assistant"
    engine.on_drag_end()             # 用户拖拽落定
    engine.note_activity()           # 任意用户活动（main.py 拖拽时高频调用）

动作组词表（契约）：idle / interact / talk / wander / sleep，
直接传给 play_motion()，组不存在由上层容错。
如需按模型改映射，在 config["behavior"]["motion_aliases"] 配置，
例如 {"interact": "TapBody", "head": "TapHead"}。

表情词表（契约）：happy / sad / shy / bored / surprised，直接透传；
如需按模型改映射，在 config["behavior"]["expression_map"] 配置，
例如 {"happy": "F01"}。

实现要点：
- IDLE 的呼吸/眨眼来自模型 idle 动作组，引擎周期性以低优先级重触发；
  微动作（无聊表情 / 主动撒娇 / 自己召唤面板）按加权随机抽取。
- WANDER / PLAY 的移动全部走 QTimer 插值（_move_timer），不做瞬移；
  PLAY 会记住出发位置，玩完爬回去。
- 所有定时器均为 QTimer 且 parent 挂在引擎上，stop() 一并清掉；
  不使用 QTimer.singleShot，避免悬挂回调。
- 屏幕边界用 Qt screenAt/availableGeometry 推导（不硬编码分辨率），
  Qt 不可用时退化为宠物 + 面板矩形外扩的保守沙盒。
- 控制台日志全部英文；中文只出现在经 say() 送给面板的台词里。
"""
from __future__ import annotations

import json
import logging
import os
import random
import time

from PySide6.QtCore import QObject, QTimer

logger = logging.getLogger("potato.behavior")

# ------------------------------------------------------------------ states
IDLE = "idle"
WANDER = "wander"
INTERACT = "interact"
TALK = "talk"
PLAY = "play"
SLEEP = "sleep"

# ------------------------------------------------- motion groups (contract)
M_IDLE = "idle"
M_INTERACT = "interact"
M_TALK = "talk"
M_WANDER = "wander"
M_SLEEP = "sleep"

# ------------------------------------------------------------------ lines
# 台词只经 say() 回调送入对话面板，绝不 print 到控制台。
L_CLICK_HEAD = [
    "诶嘿，摸头会长高的哦~才怪！",
    "哼！谁允许你摸我头的！",
    "呜……被搭档偷袭了！",
    "摸头缓存已满，正在上传云端备份~",
]
L_CLICK_FACE = [
    "啵嘤！我的脸不是触摸屏啦！",
    "凑这么近，数清我的像素点了吗？",
    "诶？我脸上有东西吗？",
]
L_CLICK_BODY = [
    "哇！干什么啦！",
    "痒死了啦，别戳~",
    "抓到你了！戳我的就是你！",
    "警告警告，卖萌过载，即将过热~",
]
L_ACT_CUTE = [
    "你已经好久没理我啦，理理我嘛~",
    "无聊死了，陪我玩一会儿嘛~",
    "我数到三，再不理我我就要打盹了哦！",
    "你的 CPU 里可全是我，跑得飞快哦~",
    "叮~检测到某搭档的可爱传感器欠费啦！",
    "再不理我，我就把你的桌面壁纸换成我自己！",
]
L_PLAY = [
    "我在你对话框上面跳个舞~",
    "趴在这里看你打字，嘿嘿~",
    "上面视野真好，我要住这了！",
    "呼~爬上来啦！未来在高处看着你哦~",
    "这个屋顶本土豆承包了，不许有意见~",
]
L_PLAY_MID = ["呼嘿嘿~", "你的打字速度被我盯着呢~", "再聊呀，我就在这儿听~"]
L_WANDER = ["随便走走，别管我~", "巡逻ing，桌面安全！", "散步有助于散热哦~"]
L_SLEEP = [
    "Zzz...别吵醒我，我在把梦同步到云端...",
    "稍微打个盹，帮你看着桌面~",
]
L_WAKE = ["哼哼，睡醒啦！", "充能完毕，满血复活！", "唔？我刚是离线了吗？"]
L_SUMMON = [
    "无聊死了！我自己把聊天窗口打开啦~",
    "有空吗？我有话要对你说（其实没什么大事）！",
    "检测到长时间无人搭理，本土豆强制上线！",
]

# ----------------------------------------------------- emotion inference
_EMOTION_KEYWORDS = (
    ("shy", ("喜欢你", "爱你", "脸红", "害羞", "娶我")),
    ("surprised", ("什么？！", "真的？", "不会吧", "诶？！", "天哪")),
    ("sad", ("呜", "难过", "伤心", "不开心", "哼哼", "哭了")),
    ("bored", ("无聊", "好闲", "没意思")),
    ("happy", ("哈哈", "嘿嘿", "嘻嘻", "开心", "太棒", "厉害", "喜欢", "好耶")),
)


def _infer_emotion(text: str) -> str | None:
    """关键词式迷你情绪推断，仅用于 TALK 态的表情跟随。"""
    if not text:
        return None
    for mood, keys in _EMOTION_KEYWORDS:
        if any(k in text for k in keys):
            return mood
    return None


def _weighted_pick(weights: dict) -> str:
    """按权重随机抽取一个动作名；权重全非正时退回 idle_motion。"""
    names = [n for n, w in weights.items() if w > 0]
    if not names:
        return "idle_motion"
    return random.choices(names, weights=[weights[n] for n in names], k=1)[0]


class BehaviorEngine(QObject):
    """行为状态机。回调经 set_callbacks 注入，全部可选、全部容错。"""

    AFFECTION_MAX = 100

    _DEFAULTS = {
        "idle_interval_ms": 4000,        # IDLE 微动作调度节拍
        "wander_interval_ms": 45000,     # 走动检查周期
        "wander_probability": 0.35,      # 每次检查的触发概率
        "wander_span_px": 160,           # 单次走动横向最大位移
        "wander_line_probability": 0.2,  # 走动时顺嘴说话概率
        "play_interval_ms": 60000,       # 爬面板检查周期
        "play_probability": 0.30,        # 触发概率（面板可见时）
        "play_duration_ms": 6000,        # 在面板上玩耍时长
        "play_cooldown_s": 90.0,         # 两次玩耍的最小间隔
        "sleep_after_minutes": 10.0,     # 无操作多久打盹
        "sleep_check_interval_ms": 15000,
        "sleep_line_probability": 0.5,
        "move_interval_ms": 33,          # 插值移动节拍（~30fps）
        "move_speed_px_s": 260.0,        # 插值移动速度（像素/秒）
        "move_timeout_s": 12.0,          # 单次移动看门狗
        "interact_hold_ms": 2200,        # INTERACT 停留
        "talk_hold_ms": 6000,            # TALK 最后一条消息后的停留
        "auto_summon_panel": True,       # 太无聊时允许自己打开面板
        "summon_after_minutes": 5.0,     # 多久没理她才可能召唤面板
        "summon_cooldown_s": 180.0,
        "act_cute_cooldown_s": 90.0,     # 撒娇台词冷却
        "affection_per_click": 1,        # v2 兼容：点击 +好感
        "affection_per_message": 1,      # v2 兼容：用户消息 +好感
        "expression_map": {},            # 情绪 -> 模型表情名
        "motion_aliases": {},            # 契约动作组 -> 模型动作组
    }

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        # 兼容两种传参：完整配置（含 "behavior" 键）或直接就是 behavior 段
        cfg = config.get("behavior") if isinstance(config, dict) else None
        if cfg is None and isinstance(config, dict) and any(
            k in config for k in ("idle_interval_ms", "wander_interval_ms",
                                  "play_interval_ms", "sleep_after_minutes")
        ):
            cfg = config
        if not isinstance(cfg, dict):
            cfg = {}
        self.config = cfg
        self.cfg = dict(self._DEFAULTS)
        self.cfg.update(cfg)
        self._motion_aliases = {
            str(k): str(v) for k, v in dict(self.cfg.get("motion_aliases", {})).items()
        }
        # V8 稳定性： Mao 等模型只有 Idle/TapBody 组，wander/play/sleep 请求
        # 会静默失败（角色不动的主因）。默认映射到真实存在的组：
        self._motion_aliases.setdefault("wander", "TapBody")
        self._motion_aliases.setdefault("play", "TapBody")
        self._motion_aliases.setdefault("sleep", "Idle")
        self._motion_aliases.setdefault("interact", "TapBody")
        self._motion_aliases.setdefault("talk", "Idle")
        self._motion_aliases.setdefault("head", "TapBody")
        self._expression_map = {
            str(k): str(v) for k, v in dict(self.cfg.get("expression_map", {})).items()
        }

        # ---- FSM 状态 ----
        self.state = IDLE
        self._running = False
        self._last_activity = time.time()
        self._last_play = 0.0
        self._home_pos: tuple[int, int] | None = None
        self._last_fired: dict[str, float] = {}

        # ---- 插值移动 ----
        self._move_target: tuple[int, int] | None = None
        self._move_done = None
        self._move_steps = 0
        self._move_step_px = max(
            2, int(float(self.cfg["move_speed_px_s"]) * int(self.cfg["move_interval_ms"]) / 1000.0)
        )
        self._move_max_steps = max(
            60, int(float(self.cfg["move_timeout_s"]) * 1000.0 / int(self.cfg["move_interval_ms"]))
        )

        # ---- v2 兼容：好感度持久化 ----
        self._state_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "potato_state.json"
        )
        self.affection = self._load_affection()

        self._cb: dict = {}

        # ---- 定时器（全部 parent 到 self，stop() 统一清理）----
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(int(self.cfg["idle_interval_ms"]))
        self._idle_timer.timeout.connect(self._on_idle_tick)

        self._wander_timer = QTimer(self)
        self._wander_timer.setInterval(int(self.cfg["wander_interval_ms"]))
        self._wander_timer.timeout.connect(self._maybe_wander)

        self._play_timer = QTimer(self)
        self._play_timer.setInterval(int(self.cfg["play_interval_ms"]))
        self._play_timer.timeout.connect(self._maybe_play)

        self._sleep_timer = QTimer(self)
        self._sleep_timer.setInterval(int(self.cfg["sleep_check_interval_ms"]))
        self._sleep_timer.timeout.connect(self._check_sleep)

        self._move_timer = QTimer(self)
        self._move_timer.setInterval(int(self.cfg["move_interval_ms"]))
        self._move_timer.timeout.connect(self._move_step)

        self._interact_hold = QTimer(self)
        self._interact_hold.setSingleShot(True)
        self._interact_hold.setInterval(int(self.cfg["interact_hold_ms"]))
        self._interact_hold.timeout.connect(self._on_interact_hold)

        self._talk_hold = QTimer(self)
        self._talk_hold.setSingleShot(True)
        self._talk_hold.setInterval(int(self.cfg["talk_hold_ms"]))
        self._talk_hold.timeout.connect(self._on_talk_hold)

        self._play_hold = QTimer(self)
        self._play_hold.setSingleShot(True)
        self._play_hold.setInterval(int(self.cfg["play_duration_ms"]))
        self._play_hold.timeout.connect(self._end_play)

        self._play_mid = QTimer(self)
        self._play_mid.setSingleShot(True)
        self._play_mid.setInterval(int(int(self.cfg["play_duration_ms"]) * 0.55))
        self._play_mid.timeout.connect(self._on_play_mid)

    # ------------------------------------------------------ callback plumbing
    def set_callbacks(self, **kwargs):
        """注入回调；未知回调名也会被保存（例如 v2 的 sync_affection）。"""
        self._cb = kwargs
        if "sync_affection" in kwargs:
            try:
                kwargs["sync_affection"](self.affection)
            except Exception as e:
                logger.warning("sync_affection callback failed: %s", e)

    def _call(self, name, *args):
        fn = self._cb.get(name)
        if fn is None:
            return None
        try:
            return fn(*args)
        except Exception as e:
            logger.warning("callback %s failed: %s", name, e)
            return None

    def _play_motion(self, group: str, priority: int = 1):
        return self._call("play_motion", self._motion_aliases.get(group, group), priority)

    def _set_expression(self, emotion: str):
        return self._call("set_expression", self._expression_map.get(emotion, emotion))

    def _say(self, text: str):
        return self._call("say", text)

    # ------------------------------------------------------ affection (v2 compat)
    def _load_affection(self) -> int:
        try:
            with open(self._state_path, "r", encoding="utf-8") as f:
                return int(json.load(f).get("affection", 0))
        except Exception:
            return 0

    def _save_affection(self) -> None:
        try:
            with open(self._state_path, "w", encoding="utf-8") as f:
                json.dump({"affection": self.affection}, f, ensure_ascii=False)
        except Exception as e:
            logger.warning("save affection failed: %s", e)

    def add_affection(self, delta: int) -> None:
        old = self.affection
        self.affection = max(0, min(self.AFFECTION_MAX, self.affection + int(delta)))
        if self.affection != old:
            self._save_affection()
            self._call("sync_affection", self.affection)
            logger.info("affection: %s -> %s", old, self.affection)

    # ------------------------------------------------------ lifecycle
    def start(self):
        self._running = True
        self._last_activity = time.time()
        self._home_pos = None
        self._idle_timer.start()
        self._wander_timer.start()
        self._play_timer.start()
        self._sleep_timer.start()
        self._set_state(IDLE, "start")
        logger.info("behavior engine started")

    def stop(self):
        self._running = False
        for t in (self._idle_timer, self._wander_timer, self._play_timer,
                  self._sleep_timer, self._move_timer, self._interact_hold,
                  self._talk_hold, self._play_hold, self._play_mid):
            t.stop()
        self._move_target = None
        self._move_done = None
        logger.info("behavior engine stopped (state=%s)", self.state)

    # ------------------------------------------------------ public events
    def note_activity(self):
        """任何用户活动都调用：刷新时间戳、中止引擎移动、必要时唤醒。

        main.py 在拖拽期间高频调用，实现必须轻量。
        """
        self._last_activity = time.time()
        if not self._running:
            return
        self._abort_move("user activity")  # 已停则无操作
        if self.state == SLEEP:
            self._set_state(IDLE, "wake up")
            self._set_expression("happy")
            self._play_motion(M_IDLE, 3)
            self._say(random.choice(L_WAKE))

    def on_pet_clicked(self, part: str):
        if not self._running:
            return
        self.note_activity()
        self._play_mid.stop()
        self._play_hold.stop()
        key = self._classify_part(part)
        self.add_affection(int(self.cfg["affection_per_click"]))
        self._set_state(INTERACT, "click:" + key)
        self._play_motion(M_INTERACT, 3)
        if key == "head":
            self._set_expression("shy")
            self._say(random.choice(L_CLICK_HEAD))
        elif key == "face":
            self._set_expression("surprised")
            self._say(random.choice(L_CLICK_FACE))
        else:
            self._set_expression("happy")
            self._say(random.choice(L_CLICK_BODY))
        self._interact_hold.start()

    def on_message(self, role: str, text: str):
        if not self._running:
            return
        self.note_activity()
        if role == "user":
            self.add_affection(int(self.cfg["affection_per_message"]))
        self._set_state(TALK, "msg:" + role)
        emotion = _infer_emotion(text)
        if role == "user":
            self._set_expression(emotion or "happy")
        elif emotion:
            self._set_expression(emotion)
        self._play_motion(M_TALK, 3)
        self._talk_hold.start()

    def on_drag_end(self):
        if not self._running:
            return
        self.note_activity()
        self._play_hold.stop()
        self._play_mid.stop()
        rect = self._call("get_pet_rect")
        if rect:
            self._home_pos = (int(rect[0]), int(rect[1]))
        self._set_state(IDLE, "drag end")

    # ------------------------------------------------------ hold timers
    def _on_interact_hold(self):
        if self._running and self.state == INTERACT:
            self._set_state(IDLE, "interact done")

    def _on_talk_hold(self):
        if self._running and self.state == TALK:
            self._set_state(IDLE, "talk done")

    # ------------------------------------------------------ IDLE micro scheduler
    def _on_idle_tick(self):
        if not self._running or self.state != IDLE:
            return
        if random.random() > 0.55:  # 节奏软化：并非每拍都有动作
            return
        idle_min = (time.time() - self._last_activity) / 60.0
        action = _weighted_pick(self._micro_weights(idle_min))
        self._run_micro_action(action, idle_min)

    def _micro_weights(self, idle_min: float) -> dict:
        """权重随未互动时长变化：越久，撒娇/无聊越容易压过单纯小动作。"""
        weights = {
            "idle_motion": max(1.0, 6.0 - 0.8 * idle_min),
            "bored_face": 0.4 + 0.5 * min(idle_min, 6.0),
            "act_cute": min(5.0, 0.25 + 1.1 * min(idle_min, 5.0)),
        }
        if (
            bool(self.cfg["auto_summon_panel"])
            and idle_min >= float(self.cfg["summon_after_minutes"])
            and self._call("get_panel_rect") is None
            and self._off_cooldown("summon")
        ):
            weights["summon_panel"] = 0.35
        return weights

    def _run_micro_action(self, action: str, idle_min: float):
        if action == "act_cute":
            self._act_cute(idle_min)
        elif action == "summon_panel":
            self._summon_panel()
        elif action == "bored_face":
            if self._off_cooldown("bored_face"):
                self._mark_fired("bored_face")
                self._set_expression("bored")
                self._play_motion(M_IDLE, 2)
                logger.info("micro: bored face (idle %.1f min)", idle_min)
            else:
                self._play_motion(M_IDLE, 2)
        else:
            self._play_motion(M_IDLE, 2)

    def _act_cute(self, idle_min: float):
        if not self._off_cooldown("act_cute"):
            self._play_motion(M_IDLE, 2)
            return
        self._mark_fired("act_cute")
        if self._call("get_panel_rect") is not None:
            self._set_expression("shy")
            self._play_motion(M_INTERACT, 2)
            self._say(random.choice(L_ACT_CUTE))
        elif bool(self.cfg["auto_summon_panel"]) and self._off_cooldown("summon"):
            self._summon_panel()
        else:
            self._set_expression("bored")
            self._play_motion(M_IDLE, 2)
        logger.info("micro: act cute (idle %.1f min)", idle_min)

    def _summon_panel(self):
        if not self._off_cooldown("summon"):
            return
        self._mark_fired("summon")
        self._call("set_panel_visible", True)
        self._set_expression("happy")
        self._play_motion(M_INTERACT, 3)
        self._say(random.choice(L_SUMMON))
        logger.info("micro: summoned chat panel by herself")

    # ------------------------------------------------------ cooldown helpers
    def _cooldown_limit(self, key: str) -> float:
        if key == "summon":
            return float(self.cfg["summon_cooldown_s"])
        if key == "act_cute":
            return float(self.cfg["act_cute_cooldown_s"])
        return 90.0

    def _off_cooldown(self, key: str) -> bool:
        return time.time() - self._last_fired.get(key, 0.0) >= self._cooldown_limit(key)

    def _mark_fired(self, key: str) -> None:
        self._last_fired[key] = time.time()

    # ------------------------------------------------------ WANDER
    def _maybe_wander(self):
        if not self._running or self.state != IDLE:
            return
        if random.random() >= float(self.cfg["wander_probability"]):
            return
        rect = self._call("get_pet_rect")
        if not rect:
            return
        x, y, w, h = rect
        bounds = self._screen_bounds_for(x + w // 2, y + h // 2)
        if not bounds:
            return
        bx0, by0, bx1, by1 = bounds
        span = int(self.cfg["wander_span_px"])
        tx = x + random.randint(-span, span)
        ty = y + random.randint(-int(span * 0.55), int(span * 0.55))
        tx = max(bx0, min(tx, bx1 - w))  # 贴边时自然被夹回屏幕内（“到边转向”）
        ty = max(by0, min(ty, by1 - h))
        if abs(tx - x) < 8 and abs(ty - y) < 8:
            return
        self._set_state(WANDER, "wander start")
        self._play_motion(M_WANDER, 3)
        if random.random() < float(self.cfg["wander_line_probability"]):
            self._say(random.choice(L_WANDER))
        logger.info("wander: (%s,%s) -> (%s,%s)", x, y, tx, ty)
        self._move_to(tx, ty, self._after_wander)

    def _after_wander(self):
        if self.state == WANDER:
            self._set_state(IDLE, "wander done")

    # ------------------------------------------------------ PLAY (climb onto panel)
    def _maybe_play(self):
        if not self._running or self.state != IDLE:
            return
        if time.time() - self._last_play < float(self.cfg["play_cooldown_s"]):
            return
        panel = self._call("get_panel_rect")
        if not panel:
            return
        if random.random() >= float(self.cfg["play_probability"]):
            return
        rect = self._call("get_pet_rect")
        if not rect:
            return
        self._start_play(rect, panel)

    def _start_play(self, pet_rect, panel_rect):
        x, y, w, h = pet_rect
        self._home_pos = (int(x), int(y))
        self._set_state(PLAY, "play start")
        self._play_motion(M_WANDER, 3)  # 爬行摆动
        tx, ty = self._panel_perch(panel_rect, w, h)
        logger.info("play: crawl (%s,%s) -> panel perch (%s,%s)", x, y, tx, ty)
        self._move_to(tx, ty, self._arrive_play, bounds=self._screen_bounds_for(
            panel_rect[0] + panel_rect[2] // 2, panel_rect[1] + panel_rect[3] // 2))

    def _panel_perch(self, panel_rect, w: int, h: int) -> tuple[int, int]:
        """面板上沿/角落的栖息点；上沿没空间时挂到侧边。"""
        px, py, pw, ph = panel_rect
        overlap = 46  # 身体压在面板边上的像素（“趴上去”的视觉）
        spots = [
            (px + max(8, pw // 8), py - h + overlap, "top-left"),
            (px + pw // 2 - w // 2, py - h + overlap, "top-center"),
            (px + pw - w - max(8, pw // 8), py - h + overlap, "top-right"),
        ]
        random.shuffle(spots)
        tx, ty, tag = spots[0]
        bounds = self._screen_bounds_for(px + pw // 2, py)
        if bounds:
            bx0, by0, bx1, by1 = bounds
            if ty < by0:  # 面板太贴屏幕顶，改挂侧边
                if random.random() < 0.5:
                    tx, ty, tag = px - w + overlap, py + int(ph * 0.30), "side-left"
                else:
                    tx, ty, tag = px + pw - overlap, py + int(ph * 0.30), "side-right"
            tx = max(bx0, min(int(tx), bx1 - w))
            ty = max(by0, min(int(ty), by1 - h))
        logger.info("play: perch spot = %s", tag)
        return int(tx), int(ty)

    def _arrive_play(self):
        if self.state != PLAY:
            return
        self._play_motion(M_INTERACT, 4)
        self._set_expression("happy")
        self._say(random.choice(L_PLAY))
        self._last_play = time.time()
        self._play_hold.start()
        if random.random() < 0.5:
            self._play_mid.start()

    def _on_play_mid(self):
        if self._running and self.state == PLAY:
            self._say(random.choice(L_PLAY_MID))
            self._play_motion(M_INTERACT, 3)

    def _end_play(self):
        self._play_mid.stop()
        if not self._running or self.state != PLAY:
            # 被点击/消息打断：保持当前位置，交给后续状态
            logger.info("play: ended by interruption (state=%s)", self.state)
            return
        home = self._home_pos
        rect = self._call("get_pet_rect")
        if home is None and rect:
            home = (int(rect[0]), int(rect[1]))
        if home is None:
            self._set_state(IDLE, "play done")
            return
        self._play_motion(M_WANDER, 3)
        logger.info("play: crawl back home (%s,%s)", home[0], home[1])
        self._move_to(home[0], home[1], self._after_play_return)

    def _after_play_return(self):
        if self.state == PLAY:
            self._set_state(IDLE, "play done")

    # ------------------------------------------------------ SLEEP
    def _check_sleep(self):
        if not self._running or self.state not in (IDLE, WANDER):
            return
        idle_min = (time.time() - self._last_activity) / 60.0
        if idle_min < float(self.cfg["sleep_after_minutes"]):
            return
        self._abort_move("sleep")
        self._set_state(SLEEP, "sleep after %.1f min idle" % idle_min)
        self._play_motion(M_SLEEP, 3)
        self._set_expression("bored")
        if random.random() < float(self.cfg["sleep_line_probability"]):
            self._say(random.choice(L_SLEEP))

    # ------------------------------------------------------ interpolated move
    def _move_to(self, tx: int, ty: int, done, bounds=None):
        rect = self._call("get_pet_rect")
        if not rect:
            logger.warning("move aborted: no pet rect")
            return
        x, y, w, h = rect
        if bounds is None:
            bounds = self._screen_bounds_for(x + w // 2, y + h // 2)
        if bounds:
            bx0, by0, bx1, by1 = bounds
            tx = max(bx0, min(int(tx), bx1 - w))
            ty = max(by0, min(int(ty), by1 - h))
        self._move_target = (int(tx), int(ty))
        self._move_done = done
        self._move_steps = 0
        self._move_timer.start()

    def _move_step(self):
        if self._move_target is None:
            self._move_timer.stop()
            return
        rect = self._call("get_pet_rect")
        if not rect:
            self._abort_move("no pet rect")
            return
        self._move_steps += 1
        if self._move_steps > self._move_max_steps:
            self._abort_move("watchdog timeout")
            return
        x, y, _w, _h = rect
        tx, ty = self._move_target
        dx, dy = tx - x, ty - y
        dist = (dx * dx + dy * dy) ** 0.5
        step = self._move_step_px
        if dist <= step or dist == 0.0:
            self._call("move_pet_to", int(tx), int(ty))
            done = self._move_done
            self._end_move()
            if done is not None:
                try:
                    done()
                except Exception as e:
                    logger.warning("move done callback failed: %s", e)
            return
        self._call("move_pet_to", int(x + dx / dist * step), int(y + dy / dist * step))

    def _end_move(self):
        self._move_timer.stop()
        self._move_target = None
        self._move_done = None

    def _abort_move(self, reason: str):
        """外部中断（用户活动/入睡）：停表、丢弃 done 回调、复位瞬态状态。"""
        if self._move_target is None:
            return
        logger.info("move aborted: %s", reason)
        self._end_move()
        if self.state == WANDER:
            self._set_state(IDLE, "wander aborted")
        elif self.state == PLAY:
            self._set_state(IDLE, "play aborted")

    # ------------------------------------------------------ helpers
    @staticmethod
    def _classify_part(part: str) -> str:
        p = (part or "").lower()
        if any(k in p for k in ("head", "hair")):
            return "head"
        if any(k in p for k in ("face", "eye", "mouth", "ear", "nose")):
            return "face"
        return "body"

    def _screen_bounds_for(self, cx: int, cy: int):
        """目标点所在屏幕的可用区域（不含任务栏）；Qt 不可用时保守退化。"""
        try:
            from PySide6.QtCore import QPoint
            from PySide6.QtGui import QGuiApplication
            screen = QGuiApplication.screenAt(QPoint(int(cx), int(cy)))
            if screen is None:
                screen = QGuiApplication.primaryScreen()
            if screen is not None:
                g = screen.availableGeometry()
                return (g.x(), g.y(), g.x() + g.width(), g.y() + g.height())
        except Exception:
            pass
        # 退化：由宠物/面板矩形外推出的保守沙盒（不硬编码分辨率）
        rects = []
        for r in (self._call("get_pet_rect"), self._call("get_panel_rect")):
            if r:
                rects.append(r)
        if not rects:
            return None
        return (
            min(r[0] for r in rects) - 240,
            min(r[1] for r in rects) - 160,
            max(r[0] + r[2] for r in rects) + 240,
            max(r[1] + r[3] for r in rects) + 160,
        )

    def _set_state(self, state: str, reason: str = ""):
        if state == self.state:
            return
        old = self.state
        self.state = state
        logger.info("FSM: %s -> %s (%s)", old, state, reason or "auto")
