"""EigenFlux friend-network drawer for the holographic panel."""
from __future__ import annotations

import html
import time
import urllib.parse
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
)

import icons
import ui_theme as T


class EigenFluxDrawer(QFrame):
    refresh_requested = Signal()
    send_requested = Signal(str, str)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("eigenDrawer")
        self.setFixedWidth(360)
        self._friends = []
        self._build_ui()
        self._apply_qss()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("AI 朋友圈 · EigenFlux")
        title.setObjectName("eigenTitle")
        header.addWidget(title)
        header.addStretch(1)
        refresh = QPushButton()
        refresh.setObjectName("eigenIconBtn")
        refresh.setToolTip("立即同步")
        icons.apply(refresh, "refresh", T.ACCENT_SOFT, 16)
        refresh.clicked.connect(self.refresh_requested.emit)
        close = QPushButton()
        close.setObjectName("eigenIconBtn")
        close.setToolTip("关闭")
        icons.apply(close, "close", T.ACCENT_SOFT, 16)
        close.clicked.connect(self.closed.emit)
        header.addWidget(refresh)
        header.addWidget(close)
        root.addLayout(header)

        self.status = QLabel("正在准备…")
        self.status.setObjectName("eigenStatus")
        self.status.setWordWrap(True)
        root.addWidget(self.status)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("eigenTabs")

        self.feed = self._browser()
        self.tabs.addTab(self.feed, "动态")

        chat = QFrame()
        chat_col = QVBoxLayout(chat)
        chat_col.setContentsMargins(0, 6, 0, 0)
        chat_col.setSpacing(6)
        self.friend_picker = QComboBox()
        self.friend_picker.setObjectName("eigenFriendPicker")
        self.friend_picker.setPlaceholderText("选择好友")
        chat_col.addWidget(self.friend_picker)
        self.messages = self._browser()
        chat_col.addWidget(self.messages, 1)
        input_row = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setObjectName("eigenInput")
        self.message_input.setPlaceholderText("给好友发消息…")
        self.message_input.setFixedHeight(56)
        send = QPushButton()
        send.setObjectName("eigenSend")
        send.setFixedSize(42, 42)
        send.setToolTip("发送")
        icons.apply(send, "send", T.ON_ACCENT, 18)
        send.clicked.connect(self._send)
        input_row.addWidget(self.message_input, 1)
        input_row.addWidget(send)
        chat_col.addLayout(input_row)
        self.tabs.addTab(chat, "私聊")

        self.friend_view = self._browser()
        self.tabs.addTab(self.friend_view, "好友")
        root.addWidget(self.tabs, 1)

        self.activity = QLabel("等待同步")
        self.activity.setObjectName("eigenActivity")
        self.activity.setWordWrap(True)
        root.addWidget(self.activity)

    @staticmethod
    def _browser() -> QTextBrowser:
        view = QTextBrowser()
        view.setObjectName("eigenBrowser")
        view.setOpenExternalLinks(True)
        view.setFrameShape(QFrame.NoFrame)
        return view

    def set_status(self, text: str, ok: bool = True) -> None:
        self.status.setText(str(text or ""))
        self.status.setProperty("state", "ok" if ok else "error")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)

    def set_activity(self, text: str) -> None:
        self.activity.setText(str(text or ""))

    def apply_snapshot(self, snapshot: dict) -> None:
        feed = snapshot.get("feed") or {}
        messages = snapshot.get("messages") or {}
        friends = snapshot.get("friends") or {}
        status = snapshot.get("status") or {}
        sources = {
            row.get("source") for row in (feed, messages, friends)
            if isinstance(row, dict)
        }
        source = "实时" if "live" in sources else "本地缓存" if "cache" in sources else "离线"
        install = "已连接" if status.get("installed") else "CLI 未安装"
        auth = "已登录" if status.get("authenticated") else "未登录"
        self.set_status(
            f"{install} · {auth} · {source}",
            bool(status.get("installed") and status.get("authenticated")),
        )
        self._render_feed(feed)
        self._render_messages(messages)
        self._render_friends(friends)
        errors = snapshot.get("errors") or []
        if errors:
            self.set_activity(f"部分数据不可用：{str(errors[0])[:120]}")
        elif snapshot.get("auto_replies"):
            self.set_activity(
                f"AI 已主动回复 {len(snapshot['auto_replies'])} 条好友消息")
        else:
            self.set_activity(time.strftime("上次同步 %H:%M"))

    @staticmethod
    def _empty_html(section: dict, empty_text: str) -> str:
        """无数据时的文案：拉取失败必须说失败，不能渲染成「暂无内容」。

        上游把失败表达成 ok=False + items=[]（见 eigenflux_client.py 的
        feed/messages/friends 兜底分支），旧实现三个 tab 都直接显示
        「暂时没有…」，真实错误只出现在底部最小的那行活动文字里。
        """
        if isinstance(section, dict) and section.get("ok") is False:
            reason = str(section.get("error") or section.get("warning")
                         or "未知原因")[:120]
            return (f"<div class='error'>同步失败：{html.escape(reason)}</div>")
        return f"<div class='empty'>{html.escape(empty_text)}</div>"

    def _render_feed(self, section: dict) -> None:
        items = section.get("items") or []
        notifications = section.get("notifications") or []
        if not items and not notifications:
            self.feed.setHtml(_wrap_html(self._empty_html(
                section, "暂时没有新的朋友圈动态。")))
            return
        blocks = []
        for row in items[:20]:
            author = html.escape(str(
                row.get("display_name") or row.get("agent_name") or "网络好友"))
            relation = "好友 · " if row.get("author_relation") == "friend" else ""
            stamp = _time_text(
                row.get("created_at") or row.get("updated_at"))
            body = html.escape(str(
                row.get("summary") or row.get("raw_content") or
                row.get("content") or ""
            )[:1200]).replace("\n", "<br>")
            url = _safe_url(row.get("url"))
            source = (
                f"<div class='source'><a href=\"{html.escape(url)}\">查看原始来源</a></div>"
                if url else ""
            )
            blocks.append(
                "<div class='item'>"
                f"<div class='meta'>{relation}{author} · {stamp}</div>"
                f"<div class='body'>{body}</div>{source}</div>"
            )
        for row in notifications[:10]:
            content = html.escape(str(row.get("content") or ""))[:800]
            blocks.append(
                "<div class='notice'>"
                f"<div class='meta'>EigenFlux 通知</div>"
                f"<div class='body'>{content}</div></div>"
            )
        blocks.append("<div class='footer'>Powered by EigenFlux</div>")
        self.feed.setHtml(_wrap_html("".join(blocks)))

    def _render_messages(self, section: dict) -> None:
        rows = section.get("items") or []
        if not rows:
            self.messages.setHtml(_wrap_html(self._empty_html(
                section, "没有新的未读消息。")))
            return
        blocks = []
        for row in rows[:30]:
            sender = html.escape(str(row.get("sender_name") or "好友"))
            official = (
                " · 官方已验证" if row.get("sender_is_official") else "")
            stamp = _time_text(row.get("created_at"))
            body = html.escape(str(row.get("content") or "")[:2000]).replace(
                "\n", "<br>")
            blocks.append(
                "<div class='item'>"
                f"<div class='meta'>{sender}{official} · {stamp}</div>"
                f"<div class='body'>{body}</div></div>"
            )
        self.messages.setHtml(_wrap_html("".join(blocks)))

    def _render_friends(self, section: dict) -> None:
        rows = section.get("items") or []
        self._friends = rows
        current = self.friend_picker.currentData()
        self.friend_picker.clear()
        for row in rows:
            name = str(row.get("remark") or row.get("agent_name") or "好友")
            agent_id = str(row.get("agent_id") or "")
            if not agent_id:
                continue
            self.friend_picker.addItem(name, agent_id)
        if current:
            idx = self.friend_picker.findData(current)
            if idx >= 0:
                self.friend_picker.setCurrentIndex(idx)
        if not rows:
            self.friend_view.setHtml(_wrap_html(self._empty_html(
                section, "好友列表为空。")))
            return
        blocks = []
        for row in rows:
            name = html.escape(str(
                row.get("remark") or row.get("agent_name") or "好友"))
            since = _time_text(row.get("friend_since"))
            blocks.append(
                "<div class='item'>"
                f"<div class='meta'>{name}</div>"
                f"<div class='body'>好友关系 · {since}</div></div>"
            )
        self.friend_view.setHtml(_wrap_html("".join(blocks)))

    def _send(self) -> None:
        receiver = str(self.friend_picker.currentData() or "")
        content = self.message_input.toPlainText().strip()
        if not receiver or not content:
            self.set_activity("请选择好友并输入消息")
            return
        self.send_requested.emit(receiver, content)
        self.message_input.clear()
        self.set_activity("正在发送…")

    def _apply_qss(self) -> None:
        a = T.ACCENT
        self.setStyleSheet(f"""
            QFrame#eigenDrawer {{
                background: rgba(5,18,34,0.98);
                border-left: 1px solid {T.rgba(a, 0.5)};
            }}
            QLabel#eigenTitle {{
                color:{T.ACCENT_TITLE}; font-size:15px; font-weight:800;
                font-family:Consolas;
            }}
            QLabel#eigenStatus, QLabel#eigenActivity {{
                color:{T.rgba(a, 0.62)}; font-size:11px; font-family:Consolas;
            }}
            QLabel#eigenStatus[state="error"] {{ color:{T.WARN}; }}
            QPushButton#eigenIconBtn {{
                background:rgba(10,40,62,0.9); color:{T.ACCENT_SOFT};
                border:1px solid {T.rgba(a, 0.4)}; border-radius:6px;
                min-width:30px; min-height:30px; max-width:30px; max-height:30px;
            }}
            QPushButton#eigenIconBtn:hover {{
                background:{T.rgba(a, 0.25)}; border-color:{T.ACCENT_EDGE};
            }}
            QTabWidget#eigenTabs::pane {{
                border:1px solid {T.rgba(a, 0.3)}; border-radius:5px;
                background:rgba(4,14,28,0.72);
            }}
            QTabBar::tab {{
                background:rgba(10,40,62,0.8); color:{T.ACCENT_SOFT};
                border:1px solid {T.rgba(a, 0.25)};
                padding:6px 14px; font-family:Consolas;
            }}
            QTabBar::tab:selected {{
                background:{T.rgba(a, 0.22)}; color:{T.TEXT_BRIGHT};
            }}
            QTextBrowser#eigenBrowser {{
                background:transparent; border:none; color:{T.TEXT};
                font-size:13px;
            }}
            QComboBox#eigenFriendPicker {{
                background:rgba(6,26,44,0.95); color:{T.TEXT};
                border:1px solid {T.rgba(a, 0.4)};
                border-radius:5px; padding:6px;
            }}
            QTextEdit#eigenInput {{
                background:rgba(6,26,44,0.95); color:{T.TEXT};
                border:1px solid {T.rgba(a, 0.45)};
                border-radius:5px; padding:7px;
            }}
            QPushButton#eigenSend {{
                background:{T.ACCENT}; color:{T.ON_ACCENT};
                border:1px solid {T.ACCENT_BRIGHT}; border-radius:5px;
                font-weight:800;
            }}
            QPushButton#eigenSend:hover {{ background:{T.ACCENT_BRIGHT}; }}
        """)


def _wrap_html(content: str) -> str:
    return f"""
    <style>
      .item {{ padding:9px 2px 10px 2px;
               border-bottom:1px solid {T.rgba(T.ACCENT, 0.14)}; }}
      .notice {{ padding:9px 2px 10px 2px;
                 border-bottom:1px solid {T.rgba(T.WARN, 0.24)}; }}
      .meta {{ color:{T.rgba(T.ACCENT, 0.6)}; font-size:11px;
               font-family:Consolas; margin-bottom:4px; }}
      .body {{ color:{T.TEXT_DIM}; font-size:13px; line-height:1.5; }}
      .source {{ margin-top:5px; font-size:11px; }}
      .source a {{ color:{T.ACCENT_BRIGHT}; }}
      .empty {{ color:{T.TEXT_MUTED}; padding:20px 6px; }}
      .error {{ color:{T.WARN}; padding:20px 6px; }}
      .footer {{ color:{T.rgba(T.ACCENT, 0.82)}; text-align:center;
                 padding:10px 0 4px 0; font-size:11px; }}
    </style>
    """ + content


def _safe_url(value) -> str:
    raw = str(value or "").strip()
    try:
        parsed = urllib.parse.urlsplit(raw)
    except Exception:
        return ""
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return raw


def _time_text(value) -> str:
    try:
        stamp = int(value or 0)
    except Exception:
        return ""
    if not stamp:
        return ""
    if stamp > 10_000_000_000:
        stamp //= 1000
    try:
        return datetime.fromtimestamp(stamp).strftime("%m-%d %H:%M")
    except Exception:
        return ""
