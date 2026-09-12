"""调皮行为引擎（v2：含好感度系统）：分层有限状态机 + 随机加权微动作调度。

让 GBT小土豆活起来：待机呼吸眨眼、随机小动作、被点击反应、
对话中反应、爬到对话面板上玩耍、长时间不理她打盹。
"""
from __future__ import annotations

import logging
import random
import time

from PySide6.QtCore import QObject, QTimer

import json
import os

logger = logging.getLogger("potato.behavior")

# 顶层状态
IDLE = "idle"
WANDER = "wander"
INTERACT = "interact"
TALK = "talk"
PLAY = "play"
SLEEP = "sleep"

# 俏皮台词
_LINES_CLICK_HEAD = ["诶嘿，摸头会长不高的啦~", "哼哼，谁允许你摸我头的？", "呜……被偷袭了！"]
_LINES_CLICK_BODY = ["哇！干什么啦！", "痒死了啦，别戳~", "抓到你了！"]
_LINES_PLAY = ["我在你对话框上面跳个舞~", "趴在这里看你打字，嘿嘿~", "上面视野真好，我要住这了！", "呼~爬上来啦！"]
_LINES_BORED = ["你已经好久没理我啦，理理我嘛~", "无聊死了，陪我玩会儿~", "我数到三，再不理我我就打盹了哦！"]
_LINES_WAKE = ["哼哼，睡醒啦！", "充能完毕，满血复活！"]

_MOOD_TO_EXPRESSION = {
    "happy": "F01",
    "shy": "F02",
    "sad": "F03",
    "bored": "F04",
    "surprised": "F05",
}


class BehaviorEngine(QObject):
    """行为状态机。回调通过 set_callbacks 注入。"""

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config.get("behavior", {})
        self._cb = {}
        self.state = IDLE
        self._last_activity = time.time()
        self._last_play = 0.0
        # v2: 好感度（MeaPet 同款概念），持久化到 potato_state.json
        self._state_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "potato_state.json")
        self.affection = self._load_affection()
        self._drag_timer = QTimer(self)
        self._drag_timer.setInterval(300)
        self._drag_timer.timeout.connect(self._maybe_drag_end)

        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(self.config.get("idle_interval_ms", 4000))
        self._idle_timer.timeout.connect(self._on_idle_tick)

        self._wander_timer = QTimer(self)
        self._wander_timer.setInterval(self.config.get("wander_interval_ms", 45000))
        self._wander_timer.timeout.connect(self._maybe_wander)

        self._play_timer = QTimer(self)
        self._play_timer.setInterval(self.config.get("play_interval_ms", 60000))
        self._play_timer.timeout.connect(self._maybe_play)

        self._sleep_check = QTimer(self)
        self._sleep_check.setInterval(15000)
        self._sleep_check.timeout.connect(self._check_sleep)

    # ---- 回调注入 ----
    def set_callbacks(self, **kwargs):
        self._cb = kwargs
        # 启动时同步一次好感度显示
        if "sync_affection" in kwargs:
            try:
                kwargs["sync_affection"](self.affection)
            except Exception:
                pass

    def _call(self, name, *args):
        fn = self._cb.get(name)
        if fn is not None:
            try:
                return fn(*args)
            except Exception as e:
                logger.warning("callback %s failed: %s", name, e)
        return None

    # ---- 生命周期 ----
    def start(self):
        self._idle_timer.start()
        self._wander_timer.start()
        self._play_timer.start()
        self._sleep_check.start()
        self._set_state(IDLE)
        logger.info("behavior engine started")

    def stop(self):
        for t in (self._idle_timer, self._wander_timer, self._play_timer,
                  self._sleep_check, self._drag_timer):
            t.stop()
        logger.info("behavior engine stopped")

    def note_activity(self):
        """任何用户互动都调用，刷新活动时间、唤醒。"""
        was_sleeping = self.state == SLEEP
        self._last_activity = time.time()
        if was_sleeping:
            self._say(random.choice(_LINES_WAKE))
            self._set_expression("happy")
            self._set_state(IDLE)

    # ---- 好感度 ----
    AFFECTION_MAX = 100

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
        self.affection = max(0, min(self.AFFECTION_MAX, self.affection + delta))
        if self.affection != old:
            self._save_affection()
            self._call("sync_affection", self.affection)
            logger.info("affection: %s -> %s", old, self.affection)

    # ---- 事件入口（由主程序接线）----
    def on_pet_clicked(self, part: str):
        self.note_activity()
        self.add_affection(1)  # 摸摸头 +1 好感
        self._set_state(INTERACT)
        self._play_motion("TapBody", 3)
        line = (random.choice(_LINES_CLICK_HEAD) if part and "head" in part.lower()
                else random.choice(_LINES_CLICK_BODY))
        self._say(line)
        expr = "shy" if (part and "head" in part.lower()) else "surprised"
        self._set_expression(expr)
        # 短暂交互后回到待机
        QTimer.singleShot(2200, lambda: self._set_state(IDLE))

    def on_message(self, role: str, text: str):
        self.note_activity()
        if role == "user":
            self.add_affection(1)  # 每次对话 +1
        self._set_state(TALK)
        if role == "user":
            self._set_expression("happy")
        else:
            self._set_expression("happy")
        # 对话态维持若干秒后回到待机
        QTimer.singleShot(4000, lambda: self._set_state(IDLE))

    def on_drag_end(self):
        self.note_activity()
        self._set_state(IDLE)

    def _maybe_drag_end(self):
        self._drag_timer.stop()

    # ---- 定时器回调 ----
    def _on_idle_tick(self):
        if self.state == IDLE:
            # 随机加权：小动作 or 主动撒娇
            idle_since = time.time() - self._last_activity
            bored_p = min(0.7, idle_since / (self.config.get("affection_decay_minutes", 3) * 60) * 0.35)
            if random.random() < bored_p:
                self._say(random.choice(_LINES_BORED))
                self._set_expression("bored")
            else:
                self._play_motion("Idle", 2)

    def _maybe_wander(self):
        if self.state not in (IDLE,) or random.random() > self.config.get("wander_probability", 0.35):
            return
        self._wander()

    def _wander(self):
        self._set_state(WANDER)
        rect = self._call("get_pet_rect")
        if not rect:
            self._set_state(IDLE)
            return
        x, y, w, h = rect
        # 在屏幕内小范围走动（限制在安全屏幕范围内）
        import random as r
        screen = self._screen_bounds()
        dx = r.randint(-120, 120)
        dy = r.randint(-60, 60)
        nx = max(screen[0] + 10, min(x + dx, screen[2] - w - 10))
        ny = max(screen[1] + 10, min(y + dy, screen[3] - h - 10))
        self._call("move_pet_to", nx, ny)
        self._play_motion("Idle", 2)
        QTimer.singleShot(3000, lambda: self._set_state(IDLE))

    def _screen_bounds(self):
        """获取主屏可用区域（任务栏除外），失败时用安全默认值。"""
        try:
            from PySide6.QtGui import QGuiApplication
            geo = QGuiApplication.primaryScreen().availableGeometry()
            return (geo.x(), geo.y(), geo.x() + geo.width(), geo.y() + geo.height())
        except Exception:
            return (0, 0, 1536, 824)

    def _maybe_play(self):
        # 面板显示时，一定概率爬上去玩
        panel_rect = self._call("get_panel_rect")
        if panel_rect and self.state in (IDLE, TALK) and \
                random.random() < self.config.get("play_probability", 0.30):
            self._play_on_panel(panel_rect)

    def _play_on_panel(self, panel_rect):
        self._set_state(PLAY)
        px, py, pw, ph = panel_rect
        # 爬到面板上沿中间（限制在屏幕内）
        target_x = px + int(pw / 2) - 100
        target_y = py - 160
        screen = self._screen_bounds()
        target_x = max(screen[0] + 10, min(target_x, screen[2] - 380 - 10))
        target_y = max(screen[1] + 10, target_y)
        self._call("move_pet_to", target_x, target_y)
        self._play_motion("Idle", 4)
        self._set_expression("happy")
        self._say(random.choice(_LINES_PLAY))
        self._last_play = time.time()
        # 玩几秒回到原位附近
        QTimer.singleShot(5000, self._end_play)

    def _end_play(self):
        self._set_state(IDLE)
        self._set_expression("happy")

    def _check_sleep(self):
        idle_min = (time.time() - self._last_activity) / 60.0
        threshold = self.config.get("sleep_after_minutes", 10)
        if idle_min >= threshold and self.state != SLEEP:
            self._set_state(SLEEP)
            self._set_expression("bored")
            self._play_motion("Idle", 1)

    # ---- 状态切换 ----
    def _set_state(self, state):
        if state == self.state:
            return
        old = self.state
        self.state = state
        logger.info("behavior state: %s -> %s", old, state)

    # ---- 助手 ----
    def _play_motion(self, group, priority=1):
        return self._call("play_motion", group, priority)

    def _set_expression(self, expr):
        name = _MOOD_TO_EXPRESSION.get(expr, expr)
        return self._call("set_expression", name)

    def _say(self, text):
        return self._call("say", text)
