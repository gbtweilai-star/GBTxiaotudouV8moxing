"""全息悬浮对话面板 v4：完整多功能聊天客户端。

参照用户当前使用的对话客户端形态（AutoClaw 聊天界面）：
左侧图标导航栏 + 消息流（头像/气泡/时间戳）+ 多行输入区（附件/语音/发送）
+ 功能入口栏 + 底部状态栏（遥测/好感度），Neon Noir 半透明悬浮。
会话持久化到 sessions.json，支持多会话切换。
"""
from __future__ import annotations

import json
import logging
import os
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QTextEdit,
                               QMenu, QListWidget, QListWidgetItem)

from chat_client import ChatClient, offline_reply  # noqa: F401

logger = logging.getLogger("potato.panel")

_SESSIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "sessions.json")


class _MessageBubble(QFrame):
    """一条消息：头像 + 气泡 + 时间戳。"""

    def __init__(self, role: str, text: str, ts: str, parent=None):
        super().__init__(parent)
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
        bl = QVBoxLayout(bubble)
        bl.setContentsMargins(10, 7, 10, 7)
        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg.setObjectName("msgText")
        bl.addWidget(msg)
        t = QLabel(ts)
        t.setObjectName("msgTime")
        t.setAlignment(Qt.AlignRight)
        bl.addWidget(t)

        if role == "user":
            row.addStretch(1)
            row.addWidget(bubble)
            row.addWidget(avatar)
            bubble.setStyleSheet(
                "QFrame#bubbleUser{background:rgba(139,92,246,0.38);"
                "border-radius:12px;} QLabel#msgText{color:#f1f5f9;font-size:13px;}"
                "QLabel#msgTime{color:#94a3b8;font-size:10px;}")
        else:
            row.addWidget(avatar)
            row.addWidget(bubble)
            row.addStretch(1)
            bubble.setStyleSheet(
                "QFrame#bubbleBot{background:rgba(34,211,238,0.14);"
                "border-radius:12px;} QLabel#msgText{color:#e2e8f0;font-size:13px;}"
                "QLabel#msgTime{color:#94a3b8;font-size:10px;}")


class HoloPanel(QWidget):
    """完整多功能全息对话客户端（半透明悬浮）。

    信号：
        message_submitted(str)  用户发送消息
        close_requested()       关闭面板
        feature_clicked(str)    功能入口（voice/tools/browser/agent/model/settings）
        session_switched(list)  切换会话（携带该会话消息列表，供 chat 同步历史）
        persona_change_requested(str) 换形象请求（模型目录名）
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

        self._sessions = self._load_sessions()      # [{id,title,messages:[{role,text,ts}]}]
        self._current = 0

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(panel_cfg.get("opacity", 0.94))
        self.resize(panel_cfg.get("width", 500), panel_cfg.get("height", 640))

        if not self._sessions:
            self._sessions = [{"id": int(time.time()), "title": "新对话", "messages": []}]

        outer = QVBoxLayout(self)
        outer.setContentsMargins(2, 2, 2, 2)
        self.frame = QFrame(self)
        self.frame.setObjectName("holoFrame")
        outer.addWidget(self.frame)

        root = QHBoxLayout(self.frame)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ================= 左侧图标导航栏 =================
        nav = QVBoxLayout()
        nav.setContentsMargins(6, 10, 6, 10)
        nav.setSpacing(8)
        self._nav_btn("➕", "新建会话", self._new_session).setObjectName("navBtn")
        nav.addWidget(self._nav_btn("➕", "新建会话", self._new_session))
        nav.addWidget(self._nav_btn("💬", "历史会话", self._show_history))
        nav.addWidget(self._nav_btn("🎭", "切换形象", self._pick_persona))
        nav.addStretch(1)
        nav.addWidget(self._nav_btn("⚙️", "设置", self._show_settings))
        nav.addWidget(self._nav_btn("✕", "隐藏面板", lambda: self.close_requested.emit()))
        root.addLayout(nav)

        # ================= 主区 =================
        main = QVBoxLayout()
        main.setContentsMargins(12, 12, 14, 12)
        main.setSpacing(8)

        # 头部：角色徽章 + 名字 + 状态点 + 隐藏键
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
        online = QLabel("在线 · 悬浮全息模式")
        online.setObjectName("online")
        status_row.addWidget(self.reactor)
        status_row.addWidget(online)
        name_col.addWidget(name)
        name_col.addLayout(status_row)
        header.addWidget(badge)
        header.addLayout(name_col)
        header.addStretch(1)
        hide_btn = self._nav_btn("✕", "隐藏面板", lambda: self.close_requested.emit())
        header.addWidget(hide_btn)
        main.addLayout(header)

        # 欢迎横幅
        self.banner = QLabel("嗨～我是小土豆，点下面的入口或直接打字找我！")
        self.banner.setObjectName("banner")
        self.banner.setWordWrap(True)
        main.addWidget(self.banner)

        # 功能入口栏
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

        # 思考指示
        self.thinking = QLabel("小土豆思考中 ·  ·  ·")
        self.thinking.setObjectName("holoThinking")
        self.thinking.setVisible(False)
        main.addWidget(self.thinking)

        # 输入区：附件 | 多行输入 | 语音 | 发送
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        attach = QPushButton("📎")
        attach.setObjectName("inputBtn")
        attach.setFixedSize(36, 36)
        attach.setToolTip("附件（即将上线）")
        attach.clicked.connect(lambda: self._assistant_hint("附件功能在路上啦，v4.1 就能发文件给我看～"))
        self.input = QTextEdit(self)
        self.input.setObjectName("holoInput")
        self.input.setPlaceholderText("输入消息，Enter 发送 / Shift+Enter 换行")
        self.input.setFixedHeight(56)
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

        # 底部状态栏：遥测 + 好感度 + 会话数
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

        self._apply_qss(theme)
        self._render_messages()

    # ---------------- 事件过滤：Enter 发送 ----------------
    def eventFilter(self, obj, event):
        from PySide6.QtCore import QEvent
        if obj is self.input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers() & Qt.ShiftModifier:
                self._submit()
                return True
        return super().eventFilter(obj, event)

    # ---------------- 会话管理 ----------------
    def _load_sessions(self):
        try:
            with open(_SESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_sessions(self):
        try:
            with open(_SESSIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._sessions, f, ensure_ascii=False, indent=1)
        except Exception as e:
            logger.warning("save sessions failed: %s", e)

    def _new_session(self):
        self._sessions.insert(0, {"id": int(time.time()), "title": "新对话", "messages": []})
        self._current = 0
        self._save_sessions()
        self._render_messages()
        self.session_switched.emit([])
        self._update_session_label()

    def _show_history(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#121629;color:#e2e8f0;border:1px solid #2b3350;"
            "border-radius:8px;padding:6px;} QMenu::item{padding:6px 18px;}"
            "QMenu::item:selected{background:#8b5cf6;border-radius:6px;}")
        for i, s in enumerate(self._sessions[:10]):
            title = s.get("title", "对话")
            n = len(s.get("messages", []))
            act = menu.addAction(f"💬 {title}（{n} 条）")
            act.triggered.connect(lambda checked=False, idx=i: self._switch_session(idx))
        menu.exec(self.mapToGlobal(self.rect().topLeft() + self.rect().center()))

    def _switch_session(self, idx: int):
        if not (0 <= idx < len(self._sessions)):
            return
        self._current = idx
        self._render_messages()
        msgs = self._sessions[idx].get("messages", [])
        self.session_switched.emit([{"role": m["role"], "content": m["text"]}
                                    for m in msgs if m["role"] in ("user", "assistant")])
        self._update_session_label()

    def _pick_persona(self):
        models = getattr(self, "_available_models", ["haru", "mao", "llny", "nn"])
        menu = QMenu(self)
        menu.setStyleSheet(
            "QMenu{background:#121629;color:#e2e8f0;border:1px solid #2b3350;"
            "border-radius:8px;padding:6px;} QMenu::item{padding:6px 18px;}"
            "QMenu::item:selected{background:#8b5cf6;border-radius:6px;}")
        for m in models:
            act = menu.addAction(f"🎭 {m}")
            act.triggered.connect(lambda checked=False, name=m: self.persona_change_requested.emit(name))
        menu.exec(self.mapToGlobal(self.rect().center()))

    def _show_settings(self):
        self.feature_clicked.emit("settings")

    def _update_session_label(self):
        self.session_label.setText(f"会话 {self._current + 1}/{len(self._sessions)}")

    def _assistant_hint(self, text: str):
        self.add_message("assistant", text)

    # ---------------- 消息渲染 ----------------
    def _render_messages(self):
        while self.msg_layout.count() > 1:
            item = self.msg_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        for m in self._sessions[self._current].get("messages", []):
            self._append_bubble(m["role"], m["text"], m.get("ts", ""))
        self._scroll_bottom()

    def _append_bubble(self, role, text, ts):
        b = _MessageBubble(role, text, ts)
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
        sess = self._sessions[self._current]
        sess["messages"].append({"role": role, "text": text, "ts": ts})
        if role == "user" and len(sess["messages"]) == 1:
            sess["title"] = text[:12]
        self._save_sessions()
        self._append_bubble(role, text, ts)
        self._scroll_bottom()
        self._update_session_label()

    # ---------------- 状态 ----------------
    def set_thinking(self, on: bool):
        self.thinking.setVisible(on)

    def update_telemetry(self, text: str) -> None:
        self.telemetry_text.setText(text)

    def set_affection(self, value: int) -> None:
        self.affection_label.setText(f"♥ {value}")

    def panel_rect(self):
        g = self.geometry()
        return (g.x(), g.y(), g.width(), g.height())

    def move_near(self, pet_rect):
        """面板紧贴角色右侧站立，重叠一点营造『站在边上』的层次感。"""
        px, py, pw, ph = pet_rect
        overlap = 26  # 与角色重叠的像素，让她看起来站在面板旁边
        self.move(px + pw - overlap, py - 20)

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

    # ---------------- 样式与控件工厂 ----------------
    def _nav_btn(self, icon: str, tip: str, cb) -> QPushButton:
        b = QPushButton(icon)
        b.setObjectName("navBtn")
        b.setFixedSize(34, 34)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(cb)
        return b

    def _apply_qss(self, theme: dict):
        accent = theme.get("border", "#8b5cf6")
        text = theme.get("text", "#e2e8f0")
        bg = theme.get("bg", "rgba(11,11,15,0.86)")
        self.setStyleSheet(f"""
            QFrame#holoFrame {{
                background: {bg};
                border: 1px solid rgba(139,92,246,0.45);
                border-radius: 16px;
            }}
            QLabel#badge {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 rgba(139,92,246,0.45), stop:1 rgba(34,211,238,0.35));
                border: 1px solid rgba(167,139,250,0.6);
                border-radius: 12px; font-size: 19px;
            }}
            QLabel#charName {{
                color:#ede9fe; font-size:15px; font-weight:800; letter-spacing:0.5px;
            }}
            QLabel#online {{ color:#67e8f9; font-size:11px; }}
            QLabel#reactor {{ color:#22d3ee; font-size:13px; font-weight:800; }}
            QLabel#banner {{
                background: rgba(139,92,246,0.14);
                border: 1px solid rgba(139,92,246,0.3);
                border-radius: 10px; color:#ddd6fe;
                padding: 8px 12px; font-size: 12px;
            }}
            QLabel#telemetry {{ color:#67e8f9; font-size:11px; font-family:Consolas; }}
            QLabel#affection {{ color:#f472b6; font-size:12px; font-weight:700; }}
            QPushButton#navBtn {{
                background: rgba(42,47,58,0.75); color:{text};
                border: none; border-radius: 9px; font-size: 15px;
            }}
            QPushButton#navBtn:hover {{ background: rgba(139,92,246,0.35); }}
            QPushButton#featureBtn {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(42,47,58,0.9), stop:1 rgba(42,47,58,0.6));
                color:{text};
                border: 1px solid rgba(139,92,246,0.35);
                border-radius: 9px; padding: 6px 9px; font-size: 11px;
                font-weight: 600;
            }}
            QPushButton#featureBtn:hover {{
                background: rgba(139,92,246,0.28); border-color:#a78bfa; color:#ede9fe;
            }}
            QPushButton#featureBtn:pressed {{ background: rgba(139,92,246,0.45); }}
            QScrollArea#holoScroll {{ background: transparent; border: none; }}
            QTextEdit#holoInput {{
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(139,92,246,0.5);
                border-radius: 12px; padding: 8px 12px;
                color:{text}; font-size: 13px;
            }}
            QTextEdit#holoInput:focus {{ border-color:#a78bfa; }}
            QPushButton#inputBtn {{
                background: rgba(42,47,58,0.85); color:{text};
                border: 1px solid rgba(139,92,246,0.35);
                border-radius: 10px; font-size: 15px;
            }}
            QPushButton#inputBtn:hover {{ background: rgba(139,92,246,0.3); }}
            QPushButton#holoSend {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                color: white; border: none;
                border-radius: 10px; font-size: 15px; font-weight: 700;
            }}
            QPushButton#holoSend:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #a78bfa, stop:1 #8b5cf6);
            }}
            QLabel#holoThinking {{ color:#22d3ee; font-size: 12px; }}
        """)
