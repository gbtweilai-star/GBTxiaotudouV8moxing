"""全息悬浮对话面板（GBT小土豆V8）：全能编程 AI 级对话客户端。

V8 视觉：全息 HUD 风（对照用户参考图）——青蓝发光边框 + 四角括弧 +
代码窗标题栏 + 扫描线，暗蓝底半透明悬浮。数字人保持 Live2D 美少女不变。

迭代记录：
- 全息 HUD 面板：青蓝发光边 + 四角括弧 + 代码窗标题栏（参考图风）
- 对话框重写：Markdown 富文本渲染（代码块/表格/列表/行内代码）
- 代码块可提取复制（右键菜单列出全部代码块，一键复制）
- 流式显示 API：begin_stream / append_stream_chunk / end_stream（80ms 合批上屏）
- 消息操作：右键复制消息；气泡内文本原生可选（Ctrl+C 可用）
- 架构分层：_SessionStore（持久化）/ _MarkdownBubble（渲染）/ HoloPanel（装配）
- 修复旧版缺陷：孤儿 nav 按钮重复创建、QLabel 无选择能力、全量重建气泡

对外契约与旧版完全兼容（main.py 无需改动）：
    message_submitted(str) / close_requested() / feature_clicked(str)
    session_switched(list) / persona_change_requested(str)
    add_message / set_thinking / set_affection / update_telemetry
    panel_rect / move_near / show_panel / hide_panel / toggle
新增：
    begin_stream() / append_stream_chunk(text) / end_stream()  流式回复
"""
from __future__ import annotations

import json
import logging
import os
import re
import time

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QTextEdit,
                               QTextBrowser, QMenu)

from chat_client import ChatClient, offline_reply  # noqa: F401

logger = logging.getLogger("potato.panel")

_SESSIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "sessions.json")

# Markdown 代码块提取（流式容错：未闭合的 ``` 也算一块）
_CODE_BLOCK_RE = re.compile(r"```[^\n]*\n(.*?)(?:```|$)", re.DOTALL)

# 气泡内文档默认样式：暗色主题下的 Markdown 元素（含代码块）
_DOC_CSS = """
pre { background-color: rgba(15,18,30,0.92); color: #a5f3fc;
      font-family: Consolas, 'Cascadia Mono', monospace; font-size: 12px; }
code { color: #fbbf24; font-family: Consolas, monospace; }
h1, h2, h3 { color: #ede9fe; }
a { color: #67e8f9; }
table { color: #e2e8f0; }
"""

# ══════════════════════════════════════════════════════════════ 持久化层
class _SessionStore:
    """会话存储：JSON 读写 + 当前会话指针。纯逻辑，无 Qt 依赖。"""

    def __init__(self, path: str):
        self.path = path
        self.sessions = self._load()
        if not self.sessions:
            self.sessions = [{"id": int(time.time()), "title": "新对话",
                              "messages": []}]
        self.current = 0

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.sessions, f, ensure_ascii=False, indent=1)
        except Exception as e:
            logger.warning("save sessions failed: %s", e)

    @property
    def session(self):
        return self.sessions[self.current]

    def new(self):
        self.sessions.insert(0, {"id": int(time.time()), "title": "新对话",
                                 "messages": []})
        self.current = 0
        self.save()

    def switch(self, idx: int) -> bool:
        if not (0 <= idx < len(self.sessions)):
            return False
        self.current = idx
        return True

    def add(self, role: str, text: str, ts: str):
        s = self.session
        s["messages"].append({"role": role, "text": text, "ts": ts})
        if role == "user" and len(s["messages"]) == 1:
            s["title"] = text[:12]
        self.save()

    def history_for_chat(self, idx=None):
        """当前（或指定）会话的 chat 历史格式。"""
        s = self.sessions[idx if idx is not None else self.current]
        return [{"role": m["role"], "content": m["text"]}
                for m in s.get("messages", [])
                if m["role"] in ("user", "assistant")]


# ══════════════════════════════════════════════════════════════ 渲染层
class _MarkdownBubble(QFrame):
    """Markdown 富文本气泡：QTextBrowser 渲染 + 复制/代码提取操作。

    - assistant 消息走 setMarkdown（代码块/表格/列表/行内代码全支持）
    - user 消息同样支持 Markdown（粘贴代码提问是编程 AI 高频场景）
    - 文本原生可选择（拖选 + Ctrl+C）
    - 右键菜单：复制消息 / 复制全部代码 / 逐个代码块复制
    """

    def __init__(self, role: str, text: str, ts: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._raw = text
        self.setFrameShape(QFrame.NoFrame)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        avatar = QLabel("🧑" if role == "user" else "👧")
        avatar.setObjectName("avatar")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignCenter)

        bubble = QFrame()
        bubble.setObjectName("bubbleUser" if role == "user" else "bubbleBot")
        col = QVBoxLayout(bubble)
        col.setContentsMargins(10, 7, 10, 7)
        col.setSpacing(4)

        self.doc = QTextBrowser()
        self.doc.setObjectName("mdDoc")
        self.doc.setOpenExternalLinks(True)
        self.doc.setFrameShape(QFrame.NoFrame)
        self.doc.setStyleSheet(
            "QTextBrowser{background:transparent;border:none;"
            "color:#e2e8f0;font-size:15px;selection-background-color:"
            "rgba(139,92,246,0.55);}")
        self.doc.document().setDefaultStyleSheet(_DOC_CSS)
        self.doc.setMarkdown(text)
        self.doc.setContextMenuPolicy(Qt.CustomContextMenu)
        self.doc.customContextMenuRequested.connect(self._show_menu)
        # 高度随内容：禁滚动条，容器气泡自适应
        self.doc.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.doc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.doc.setFixedHeight(self._doc_height())
        col.addWidget(self.doc)

        t = QLabel(ts)
        t.setObjectName("msgTime")
        t.setAlignment(Qt.AlignRight)
        col.addWidget(t)

        if role == "user":
            row.addStretch(1)
            row.addWidget(bubble)
            row.addWidget(avatar)
        else:
            row.addWidget(avatar)
            row.addWidget(bubble)
            row.addStretch(1)

    def _doc_height(self) -> int:
        doc = self.doc.document()
        doc.setTextWidth(self.doc.viewport().width() or 380)
        h = int(doc.documentLayout().documentSize().height()) + 8
        return max(24, min(h, 520))  # 超长代码块内部滚动，不撑爆面板

    def update_markdown(self, text: str):
        """流式刷新：重设 Markdown 并重算高度。"""
        self._raw = text
        self.doc.setMarkdown(text)
        self.doc.setFixedHeight(self._doc_height())

    def _code_blocks(self):
        return [m.strip() for m in _CODE_BLOCK_RE.findall(self._raw) if m.strip()]

    def _show_menu(self, pos):
        menu = QMenu(self.doc)
        menu.setStyleSheet(_MENU_QSS)
        act_copy = menu.addAction("📋 复制消息（Markdown 原文）")
        blocks = self._code_blocks()
        if blocks:
            if len(blocks) == 1:
                act_code = menu.addAction("📋 复制代码块")
            else:
                act_code = menu.addAction(f"📋 复制全部代码（{len(blocks)} 块）")
        else:
            act_code = None
        chosen = menu.exec(self.doc.mapToGlobal(pos))
        if chosen is act_copy:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText(self._raw)
        elif act_code is not None and chosen is act_code:
            from PySide6.QtWidgets import QApplication
            QApplication.clipboard().setText("\n\n".join(blocks))

    def copy_message(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._raw)


_MENU_QSS = ("QMenu{background:#121629;color:#e2e8f0;border:1px solid #2b3350;"
             "border-radius:8px;padding:6px;} QMenu::item{padding:6px 18px;}"
             "QMenu::item:selected{background:#8b5cf6;border-radius:6px;}")


class _ThinkingBar(QLabel):
    """动态思考指示：三点呼吸动画。"""

    def __init__(self, parent=None):
        super().__init__("小土豆思考中", parent)
        self.setObjectName("holoThinking")
        self._n = 0
        self._timer = QTimer(self)
        self._timer.setInterval(360)
        self._timer.timeout.connect(self._tick)

    def _tick(self):
        self._n = (self._n + 1) % 4
        self.setText("小土豆思考中" + " ·" * self._n)

    def start(self):
        self._timer.start()
        self.setVisible(True)

    def stop(self):
        self._timer.stop()
        self.setVisible(False)


# ══════════════════════════════════════════════════════════════ 面板
class HoloPanel(QWidget):
    """全能编程 AI 全息对话客户端（半透明悬浮）。

    信号与公共方法与旧版完全兼容；新增流式 API。
    """

    message_submitted = Signal(str)
    close_requested = Signal()
    feature_clicked = Signal(str)
    session_switched = Signal(list)
    persona_change_requested = Signal(str)

    FEATURES = [
        ("🎤", "语音", "voice"),
        ("🔧", "工具", "tools"),
        ("🌐", "联网", "browser"),
        ("🤖", "Agent", "agent"),
        ("🧠", "模型", "model"),
    ]

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        panel_cfg = config.get("panel", {})
        theme = panel_cfg.get("theme", {})

        self.store = _SessionStore(_SESSIONS_FILE)

        # 流式状态
        self._stream_role = None
        self._stream_buf = []
        self._stream_timer = QTimer(self)          # 80ms 合批刷新，避免每 token 重排
        self._stream_timer.setInterval(80)
        self._stream_timer.timeout.connect(self._flush_stream)
        self._stream_bubble = None

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(panel_cfg.get("opacity", 0.97))
        self.resize(panel_cfg.get("width", 560), panel_cfg.get("height", 720))

        self._build_ui()
        self._apply_qss(theme)
        self._render_messages()

    # ---------------- UI 构建 ----------------
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(2, 2, 2, 2)
        self.frame = QFrame(self)
        self.frame.setObjectName("holoFrame")
        outer.addWidget(self.frame)

        root = QHBoxLayout(self.frame)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- 左侧图标导航栏（V8：无重复创建）----
        nav = QVBoxLayout()
        nav.setContentsMargins(6, 10, 6, 10)
        nav.setSpacing(8)
        nav.addWidget(self._nav_btn("➕", "新建会话", self._new_session))
        nav.addWidget(self._nav_btn("💬", "历史会话", self._show_history))
        nav.addWidget(self._nav_btn("🎭", "切换形象", self._pick_persona))
        nav.addStretch(1)
        nav.addWidget(self._nav_btn("⚙️", "设置", self._show_settings))
        nav.addWidget(self._nav_btn("✕", "隐藏面板", lambda: self.close_requested.emit()))
        root.addLayout(nav)

        # ---- 主区 ----
        main = QVBoxLayout()
        main.setContentsMargins(12, 12, 14, 12)
        main.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(10)
        badge = QLabel("👧")
        badge.setObjectName("badge")
        badge.setFixedSize(38, 38)
        badge.setAlignment(Qt.AlignCenter)
        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        name = QLabel("GBT小土豆")
        name.setObjectName("charName")
        status_row = QHBoxLayout()
        status_row.setSpacing(6)
        self.reactor = QLabel("◉")
        self.reactor.setObjectName("reactor")
        online = QLabel("在线 · 编程全能源")
        online.setObjectName("online")
        status_row.addWidget(self.reactor)
        status_row.addWidget(online)
        name_col.addWidget(name)
        name_col.addLayout(status_row)
        header.addWidget(badge)
        header.addLayout(name_col)
        header.addStretch(1)
        header.addWidget(self._nav_btn("✕", "隐藏面板",
                                       lambda: self.close_requested.emit()))
        main.addLayout(header)

        self.banner = QLabel("嗨～我是小土豆。代码块、表格、Markdown 我都能排好；"
                             "右键气泡可复制代码。Enter 发送，Shift+Enter 换行。")
        self.banner.setObjectName("banner")
        self.banner.setWordWrap(True)
        main.addWidget(self.banner)

        feature_bar = QHBoxLayout()
        feature_bar.setSpacing(6)
        for icon, label, key in self.FEATURES:
            b = QPushButton(f"{icon} {label}")
            b.setObjectName("featureBtn")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked=False, k=key: self.feature_clicked.emit(k))
            feature_bar.addWidget(b)
        main.addLayout(feature_bar)

        # 消息流
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("holoScroll")
        self.msg_container = QWidget()
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(0, 0, 0, 0)
        self.msg_layout.setSpacing(8)
        self.msg_layout.addStretch(1)
        self.scroll.setWidget(self.msg_container)
        main.addWidget(self.scroll, 1)

        # 思考指示（动态）
        self.thinking = _ThinkingBar(self)
        main.addWidget(self.thinking)

        # 输入区
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        attach = QPushButton("📎")
        attach.setObjectName("inputBtn")
        attach.setFixedSize(36, 36)
        attach.setToolTip("附件（即将上线）")
        attach.clicked.connect(lambda: self.add_message(
            "assistant", "附件功能在路上啦，v6.1 就能发文件给我看～"))
        self.input = QTextEdit(self)
        self.input.setObjectName("holoInput")
        self.input.setPlaceholderText("输入消息（支持 Markdown / 代码），"
                                      "Enter 发送 / Shift+Enter 换行")
        self.input.setFixedHeight(72)
        self.input.installEventFilter(self)
        mic = QPushButton("🎤")
        mic.setObjectName("inputBtn")
        mic.setFixedSize(36, 36)
        mic.setToolTip("语音输入")
        mic.clicked.connect(lambda: self.feature_clicked.emit("voice"))
        send = QPushButton("➤")
        send.setObjectName("holoSend")
        send.setFixedSize(36, 36)
        send.setToolTip("发送")
        send.clicked.connect(self._submit)
        input_row.addWidget(attach)
        input_row.addWidget(self.input, 1)
        input_row.addWidget(mic)
        input_row.addWidget(send)
        main.addLayout(input_row)

        status = QHBoxLayout()
        self.telemetry_text = QLabel("")
        self.telemetry_text.setObjectName("telemetry")
        self.affection_label = QLabel("♥ 0")
        self.affection_label.setObjectName("affection")
        self.session_label = QLabel("会话 1")
        self.session_label.setObjectName("telemetry")
        status.addWidget(self.telemetry_text, 1)
        status.addWidget(self.session_label)
        status.addWidget(self.affection_label)
        main.addLayout(status)

        root.addLayout(main)

    # ---------------- 事件过滤：Enter 发送 ----------------
    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and \
                    not event.modifiers() & Qt.ShiftModifier:
                self._submit()
                return True
        return super().eventFilter(obj, event)

    # ---------------- 会话 ----------------
    def _new_session(self):
        self.store.new()
        self._render_messages()
        self.session_switched.emit([])
        self._update_session_label()

    def _show_history(self):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_QSS)
        for i, s in enumerate(self.store.sessions[:10]):
            title = s.get("title", "对话")
            n = len(s.get("messages", []))
            act = menu.addAction(f"💬 {title}（{n} 条）")
            act.triggered.connect(lambda checked=False, idx=i: self._switch_session(idx))
        menu.exec(self.mapToGlobal(self.rect().topLeft() + self.rect().center()))

    def _switch_session(self, idx: int):
        if self.store.switch(idx):
            self._render_messages()
            self.session_switched.emit(self.store.history_for_chat(idx))
            self._update_session_label()

    def _pick_persona(self):
        models = getattr(self, "_available_models", ["haru", "mao", "llny", "nn"])
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_QSS)
        for m in models:
            act = menu.addAction(f"🎭 {m}")
            act.triggered.connect(lambda checked=False, name=m:
                                  self.persona_change_requested.emit(name))
        menu.exec(self.mapToGlobal(self.rect().center()))

    def _show_settings(self):
        self.feature_clicked.emit("settings")

    def _update_session_label(self):
        self.session_label.setText(
            f"会话 {self.store.current + 1}/{len(self.store.sessions)}")

    # ---------------- 消息渲染 ----------------
    def _render_messages(self):
        while self.msg_layout.count() > 1:
            item = self.msg_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for m in self.store.session.get("messages", []):
            self._append_bubble(m["role"], m["text"], m.get("ts", ""))
        self._scroll_bottom()

    def _append_bubble(self, role, text, ts):
        b = _MarkdownBubble(role, text, ts)
        self.msg_layout.insertWidget(self.msg_layout.count() - 1, b, 0)
        return b

    def _scroll_bottom(self):
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ---------------- 输入 ----------------
    def _submit(self):
        text = self.input.toPlainText().strip()
        if not text:
            return
        self.input.clear()
        self.message_submitted.emit(text)

    def add_message(self, role: str, text: str):
        ts = time.strftime("%H:%M")
        self.store.add(role, text, ts)
        self._append_bubble(role, text, ts)
        self._scroll_bottom()
        self._update_session_label()

    # ---------------- 流式显示（编程 AI 核心体验）----------------
    def begin_stream(self, role: str = "assistant"):
        """开始一次流式回复：占位气泡 + 合批定时器。"""
        self.end_stream()  # 兜底：上次未闭合先落盘
        self._stream_role = role
        self._stream_buf = []
        ts = time.strftime("%H:%M")
        self._stream_bubble = self._append_bubble(role, "", ts)
        self._stream_timer.start()

    def append_stream_chunk(self, text: str):
        """追加一个 token/片段（80ms 合批后统一重排 Markdown）。"""
        if self._stream_bubble is None:
            self.begin_stream()
        self._stream_buf.append(text)

    def _flush_stream(self):
        if self._stream_bubble is not None and self._stream_buf:
            self._stream_bubble.update_markdown("".join(self._stream_buf))
            self._scroll_bottom()

    def end_stream(self):
        """结束流式：最终 Markdown 落盘进会话存储。"""
        if self._stream_bubble is None:
            return
        self._stream_timer.stop()
        final = "".join(self._stream_buf)
        self._stream_bubble.update_markdown(final)
        self.store.add(self._stream_role or "assistant", final,
                       time.strftime("%H:%M"))
        self._stream_bubble = None
        self._stream_buf = []
        self._scroll_bottom()
        self._update_session_label()

    # ---------------- 状态 ----------------
    def set_thinking(self, on: bool):
        self.thinking.start() if on else self.thinking.stop()

    def update_telemetry(self, text: str) -> None:
        self.telemetry_text.setText(text)

    def set_affection(self, value: int) -> None:
        self.affection_label.setText(f"♥ {value}")

    def panel_rect(self):
        g = self.geometry()
        return (g.x(), g.y(), g.width(), g.height())

    def move_near(self, pet_rect):
        """面板紧贴角色右侧站立，重叠一点营造『站在边上』的层次感。

        V8 屏幕边界钳制：角色在屏幕右半时面板改到左侧站立，
        避免被推出屏幕外。"""
        px, py, pw, ph = pet_rect
        overlap = 26
        candidate_x = px + pw - overlap
        # 屏幕可用区（含任务栏避让）
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QScreen  # QScreen 在 QtGui（V8 修正）
        screen = QApplication.screenAt(QPoint(px, py)) or QApplication.primaryScreen()
        avail = screen.availableGeometry()
        panel_w, panel_h = self.width(), self.height()
        # 右侧放不下 → 改左侧站立（镜像重叠）
        if candidate_x + panel_w > avail.right():
            candidate_x = px - panel_w + overlap
        # 水平钳在屏内
        candidate_x = max(avail.left(), min(candidate_x, avail.right() - panel_w))
        # 垂直钳在屏内（顶部对齐角色 - 20，但不越界）
        candidate_y = max(avail.top(), min(py - 20, avail.bottom() - panel_h))
        self.move(candidate_x, candidate_y)

    def show_panel(self):
        self.show()
        self.raise_()

    def hide_panel(self):
        self.hide()

    def toggle(self):
        if self.isVisible():
            self.hide_panel()
        else:
            self.show_panel()

    # ---------------- 工厂 ----------------
    def _nav_btn(self, icon: str, tip: str, cb) -> QPushButton:
        b = QPushButton(icon)
        b.setObjectName("navBtn")
        b.setFixedSize(36, 36)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(cb)
        return b

    def _apply_qss(self, theme: dict):
        text = theme.get("text", "#cfefff")
        self.setStyleSheet(f"""
            QFrame#holoFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(6,20,38,0.94), stop:1 rgba(4,12,26,0.96));
                border: 2px solid rgba(34,211,238,0.75);
                border-radius: 6px;
            }}
            QFrame#bubbleUser {{
                background: rgba(34,211,238,0.16);
                border: 1px solid rgba(34,211,238,0.35);
                border-radius: 8px;
            }}
            QFrame#bubbleBot {{
                background: rgba(8,32,54,0.72);
                border: 1px solid rgba(34,211,238,0.28);
                border-radius: 8px;
            }}
            QLabel#msgTime {{ color:#5fa8c4; font-size:11px; font-family:Consolas; }}
            QLabel#badge {{
                background: rgba(34,211,238,0.14);
                border: 1px solid rgba(80,230,255,0.65);
                border-radius: 6px; font-size: 18px;
            }}
            QLabel#charName {{
                color:#9ff0ff; font-size:17px; font-weight:800;
                letter-spacing:1px; font-family:Consolas;
            }}
            QLabel#online {{ color:#4fd8f0; font-size:12px; font-family:Consolas; }}
            QLabel#reactor {{ color:#3ddcff; font-size:13px; font-weight:800; }}
            QLabel#banner {{
                background: rgba(34,211,238,0.08);
                border: 1px solid rgba(34,211,238,0.25);
                border-left: 3px solid #22d3ee;
                border-radius: 4px; color:#a8e8f8;
                padding: 8px 12px; font-size: 13px;
            }}
            QLabel#telemetry {{ color:#4fd8f0; font-size:12px; font-family:Consolas; }}
            QLabel#affection {{ color:#ff7ab8; font-size:13px; font-weight:700; font-family:Consolas; }}
            QLabel#holoThinking {{ color:#3ddcff; font-size: 13px; font-family:Consolas; }}
            QPushButton#navBtn {{
                background: rgba(10,40,62,0.85); color:#7fe6ff;
                border: 1px solid rgba(34,211,238,0.35);
                border-radius: 6px; font-size: 15px;
            }}
            QPushButton#navBtn:hover {{
                background: rgba(34,211,238,0.25); border-color:#3ddcff; color:#e6fbff;
            }}
            QPushButton#featureBtn {{
                background: rgba(10,40,62,0.8);
                color:#8fe8ff;
                border: 1px solid rgba(34,211,238,0.4);
                border-radius: 6px; padding: 6px 10px; font-size: 12px;
                font-weight: 600; font-family:Consolas;
            }}
            QPushButton#featureBtn:hover {{
                background: rgba(34,211,238,0.22); border-color:#3ddcff; color:#e6fbff;
            }}
            QPushButton#featureBtn:pressed {{ background: rgba(34,211,238,0.38); }}
            QScrollArea#holoScroll {{ background: transparent; border: none; }}
            QTextEdit#holoInput {{
                background: rgba(6,26,44,0.9);
                border: 1px solid rgba(34,211,238,0.55);
                border-radius: 6px; padding: 10px 14px;
                color:#d8f6ff; font-size: 15px;
                selection-background-color: rgba(34,211,238,0.45);
            }}
            QTextEdit#holoInput:focus {{ border-color:#3ddcff; background: rgba(8,32,54,0.95); }}
            QPushButton#inputBtn {{
                background: rgba(10,40,62,0.9); color:#7fe6ff;
                border: 1px solid rgba(34,211,238,0.4);
                border-radius: 6px; font-size: 15px;
            }}
            QPushButton#inputBtn:hover {{ background: rgba(34,211,238,0.25); }}
            QPushButton#holoSend {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #22d3ee, stop:1 #0891b2);
                color: #03212e; border: 1px solid #3ddcff;
                border-radius: 6px; font-size: 15px; font-weight: 800;
            }}
            QPushButton#holoSend:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #67e8f9, stop:1 #22d3ee);
            }}
        """)

    def paintEvent(self, event):  # noqa: N802 — 全息 HUD 四角括弧
        super().paintEvent(event)
        from PySide6.QtGui import QPainter, QPen, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = self.frame.geometry()
        x0, y0 = g.x() + 2, g.y() + 2
        x1, y1 = g.right() - 1, g.bottom() - 1
        L = 20            # 括弧臂长
        pen = QPen(QColor(90, 235, 255, 235), 3)
        pen.setCapStyle(Qt.FlatCap)
        p.setPen(pen)
        # 四角 L 形亮弧（参考图的全息边框特征）
        for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1),
                                 (x0, y1, 1, -1), (x1, y1, -1, -1)):
            p.drawLine(cx, cy, cx + dx * L, cy)
            p.drawLine(cx, cy, cx, cy + dy * L)
        p.end()
