"""形象层：透明、无边框、置顶的 Live2D 美少女窗口。

使用 PySide6 + live2d-py 渲染 Live2D 模型。模型加载在 QOpenGLWidget 的
initializeGL 中完成（offscreen/无 GL 上下文时 LoadModelJson 会崩溃，故延迟加载）。
模型缺失或加载失败时降级为 QPainter 绘制的可爱占位角色，保证程序不崩。
"""
from __future__ import annotations

import logging
import os

from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import (QColor, QPainter, QBrush, QPen, QPolygon,
                           QAction, QCursor)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget, QMenu, QVBoxLayout

import win_utils

logger = logging.getLogger("potato.pet_window")

# 尝试导入 live2d，失败则不阻塞（进入占位模式）
try:
    import live2d.v3 as live2d
    HAS_LIVE2D = True
except Exception as _e:  # pragma: no cover - import guard
    logger.warning("live2d import failed: %s", _e)
    live2d = None
    HAS_LIVE2D = False


class _PlaceholderBody(QWidget):
    """当 Live2D 模型缺失/加载失败时绘制的占位美少女（粉色圆脸 + 眼睛）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blink = 0.0

    def paintEvent(self, event):  # noqa: N802 (Qt naming)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # 身体（柔和粉色渐变近似）
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 190, 210))
        p.drawRoundedRect(int(w * 0.2), int(h * 0.55),
                          int(w * 0.6), int(h * 0.4), 28, 28)

        # 头
        p.setBrush(QColor(255, 224, 205))
        p.drawEllipse(int(w * 0.18), int(h * 0.05),
                      int(w * 0.64), int(h * 0.55))

        # 眼睛
        eye_y = int(h * 0.28)
        eye_r = max(3, int(w * 0.035))
        p.setBrush(QColor(60, 40, 70))
        p.drawEllipse(int(w * 0.34) - eye_r, eye_y - eye_r, eye_r * 2, eye_r * 2)
        p.drawEllipse(int(w * 0.66) - eye_r, eye_y - eye_r, eye_r * 2, eye_r * 2)

        # 嘴（微笑）
        p.setPen(QPen(QColor(180, 80, 110), max(2, int(w * 0.008))))
        p.setBrush(Qt.NoBrush)
        p.drawArc(int(w * 0.40), int(h * 0.34), int(w * 0.20), int(h * 0.08),
                  200 * 16, 140 * 16)
        p.end()


class PetWindow(QWidget):
    """透明置顶的 Live2D 桌宠窗口。

    信号：
        clicked(str part)              -- 点击角色某部件（Head/Body）
        drag_pos_changed(int x, int y) -- 拖拽过程中位置变化
        panel_toggle_requested()       -- 右键菜单请求切换对话面板
        quit_requested()               -- 右键菜单请求退出
    """

    clicked = Signal(str)
    drag_pos_changed = Signal(int, int)
    drag_finished = Signal()          # v3: 拖拽落定（行为引擎 on_drag_end 接线）
    panel_toggle_requested = Signal()
    quit_requested = Signal()

    def __init__(self, model_dir: str, config: dict, parent=None):
        super().__init__(parent)
        self.model_dir = model_dir
        self.config = config.get("pet", {})
        self._click_through = self.config.get("click_through_default", False)
        self._drag_offset = None
        self._model = None

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        w = self.config.get("width", 380)
        h = self.config.get("height", 560)
        self.resize(w, h)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.gl_widget = _Live2DCanvas(self.model_dir, self.config)
        self.gl_widget.clicked_part.connect(self._on_part_clicked)
        self.gl_widget.model_failed.connect(self._show_placeholder)
        self.gl_widget.model_ready.connect(self._on_model_ready)
        layout.addWidget(self.gl_widget)

        self._placeholder = None

        # 首次显示后应用 Win32 标志（需要有效 HWND）
        QTimer.singleShot(0, self._apply_flags)

    def _on_model_ready(self):
        logger.info("model ready, live2d mode active")
        if self._placeholder is not None:
            self._placeholder.hide()
            self.gl_widget.show()
            self.gl_widget.raise_()

    # ---- 占位降级 ----
    def _show_placeholder(self):
        if self._placeholder is not None:
            return
        self._placeholder = _PlaceholderBody(self)
        self.layout().addWidget(self._placeholder)
        self._placeholder.raise_()
        self.gl_widget.hide()
        logger.info("Live2D unavailable -> placeholder mode")

    # ---- 窗口标志 ----
    def _apply_flags(self):
        win_utils.apply_pet_window_flags(self, topmost=True,
                                         click_through=self._click_through)

    def set_click_through(self, enabled: bool):
        self._click_through = enabled
        hwnd = win_utils._get_hwnd(self)
        win_utils.set_click_through(hwnd, enabled)

    def toggle_click_through(self):
        self.set_click_through(not self._click_through)

    # ---- 位置 ----
    def window_rect(self):
        g = self.geometry()
        return (g.x(), g.y(), g.width(), g.height())

    # ---- 行为接口（供 behavior 引擎调用）----
    def start_motion(self, group: str, priority: int = 1):
        return self.gl_widget.start_motion(group, priority)

    def set_expression(self, name: str):
        return self.gl_widget.set_expression(name)

    def look_at_global(self, x: int, y: int):
        self.gl_widget.look_at(x, y)

    # ---- 鼠标交互 ----
    def _on_part_clicked(self, part: str):
        self.clicked.emit(part)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.button() == Qt.RightButton:
            self._show_context_menu(event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: N802
        if self._drag_offset is not None and event.buttons() & Qt.LeftButton:
            new_top_left = event.globalPosition().toPoint() - self._drag_offset
            self.move(new_top_left)
            self.drag_pos_changed.emit(new_top_left.x(), new_top_left.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802
        if self._drag_offset is not None:
            self.drag_finished.emit()  # v3: 拖拽落定通知行为引擎
        self._drag_offset = None
        super().mouseReleaseEvent(event)

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        act_panel = QAction("召唤/隐藏对话面板", self)
        act_panel.triggered.connect(self.panel_toggle_requested.emit)
        act_through = QAction(
            "关闭点击穿透" if self._click_through else "开启点击穿透（不挡桌面）",
            self)
        act_through.triggered.connect(self.toggle_click_through)
        menu.addAction(act_panel)
        menu.addAction(act_through)
        # 形象多选：注入可用模型子菜单
        models = getattr(self, "_available_models", None)
        switch = getattr(self, "_switch_model", None)
        if models and switch:
            menu.addSeparator()
            sub = menu.addMenu("切换形象")
            for name in models:
                act = QAction(name, self)
                act.triggered.connect(lambda checked=False, n=name: switch(n))
                sub.addAction(act)
        menu.addSeparator()
        act_quit = QAction("退出小土豆", self)
        act_quit.triggered.connect(self.quit_requested.emit)
        menu.addAction(act_quit)
        menu.exec(pos)


class _Live2DCanvas(QOpenGLWidget):
    """承载 live2d-py 渲染的 OpenGL 画布。"""

    clicked_part = Signal(str)
    model_ready = Signal()
    model_failed = Signal()

    def __init__(self, model_dir: str, config: dict, parent=None):
        super().__init__(parent)
        self.model_dir = model_dir
        self.config = config
        self.model = None
        self.model_loaded = False
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._last_mouse = None

        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def initializeGL(self):  # noqa: N802
        if not HAS_LIVE2D:
            logger.warning("live2d unavailable, skip GL model load")
            self.model_failed.emit()
            return
        try:
            live2d.init()
            live2d.glInit()
            model_json = os.path.join(self.model_dir, "Haru.model3.json")
            if not os.path.exists(model_json):
                # 尝试在目录内找任意 .model3.json
                cands = [f for f in os.listdir(self.model_dir)
                         if f.endswith(".model3.json")]
                if not cands:
                    logger.warning("no .model3.json in %s", self.model_dir)
                    self.model_failed.emit()
                    return
                model_json = os.path.join(self.model_dir, cands[0])
            self.model = live2d.LAppModel()
            self.model.LoadModelJson(model_json)
            self.model.Resize(self.width(), self.height())
            self.model.SetAutoBreathEnable(True)
            self.model.SetAutoBlinkEnable(True)
            self.model_loaded = True
            self._timer.start(16)  # ~60fps
            logger.info("Live2D model loaded: %s", model_json)
            self.model_ready.emit()
        except Exception as e:  # pragma: no cover
            logger.exception("Live2D model load failed: %s", e)
            self.model_loaded = False
            self.model = None
            self.model_failed.emit()

    def _on_tick(self):
        if self.model is None:
            return
        # 每帧重绘（paintGL 内部负责 clearBuffer + Update + Draw）
        self.update()

    def paintGL(self):  # noqa: N802
        if self.model is None:
            return
        try:
            # 先清屏：透明背景（0,0,0,0），否则上一帧残影叠加成鬼影
            live2d.clearBuffer(1.0, 1.0, 1.0, 0.0)
            self.model.Update()
            self.model.Draw()
        except Exception:
            pass

    def resizeGL(self, w, h):  # noqa: N802
        if self.model is not None:
            try:
                self.model.Resize(w, h)
            except Exception:
                pass

    def start_motion(self, group: str, priority: int = 1):
        if self.model is None:
            return False
        try:
            motions = self.model.GetMotions()
            if not motions:
                return False
            # group 可能在 motion 键里；支持直接组名或文件名前缀
            if group in motions:
                return self.model.StartRandomMotion(group, priority) is not None
            # 尝试按文件前缀模糊匹配组名
            for key in motions:
                if group.lower() in key.lower():
                    return self.model.StartRandomMotion(key, priority) is not None
            # 兜底：播放第一个动作组
            first_key = next(iter(motions))
            return self.model.StartRandomMotion(first_key, priority) is not None
        except Exception as e:
            logger.warning("start_motion(%s) failed: %s", group, e)
        return False

    def set_expression(self, name: str):
        if self.model is None:
            return False
        try:
            self.model.SetExpression(name)
            return True
        except Exception as e:
            logger.warning("set_expression(%s) failed: %s", name, e)
            return False

    def look_at(self, x: int, y: int):
        if self.model is None:
            return
        try:
            # 把全局坐标换算到画布局部，简单驱动眼睛参数（若存在）
            self.model.Drag(x % 100, y % 100)
        except Exception:
            pass

    def mousePressEvent(self, event):  # noqa: N802
        if self.model is not None and event.button() == Qt.LeftButton:
            try:
                part = self.model.HitPart(event.position().x(),
                                         event.position().y())
                name = part if part else "Body"
                self.clicked_part.emit(name)
            except Exception:
                self.clicked_part.emit("Body")
        super().mousePressEvent(event)
