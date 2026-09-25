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

from PySide6.QtCore import QEvent, QObject, QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QFrame, QTextEdit,
                               QTextBrowser, QMenu, QGridLayout, QSizePolicy)

import icons
import ui_theme as T
from chat_client import ChatClient, offline_reply  # noqa: F401
from eigenflux_drawer import EigenFluxDrawer

logger = logging.getLogger("potato.panel")

_SESSIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "sessions.json")

# Markdown 代码块提取（流式容错：未闭合的 ``` 也算一块）
_CODE_BLOCK_RE = re.compile(r"```[^\n]*\n(.*?)(?:```|$)", re.DOTALL)

# 会话默认标题（改标题的判定基准，见 _SessionStore.add）
_DEFAULT_TITLE = "新对话"


def _doc_css() -> str:
    """气泡内文档样式（暗色 Markdown 元素）。颜色全部取自 ui_theme token。"""
    return f"""
pre {{ background-color: {T.CODE_BG}; color: {T.ACCENT_CODE};
      font-family: Consolas, 'Cascadia Mono', monospace; font-size: 12px; }}
code {{ color: {T.WARN}; font-family: Consolas, monospace; }}
h1, h2, h3 {{ color: {T.TEXT_BRIGHT}; }}
a {{ color: {T.ACCENT_BRIGHT}; }}
table {{ color: {T.TEXT}; }}
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
        # 标题：首条 user 消息到达、且标题还是默认值时写入。
        # 旧条件是 len(messages) == 1（要求 user 消息必须是会话第一条），
        # 而桌宠旁白会先落一条 assistant → 实测唯一会话累积 300 条仍叫「新对话」，
        # 历史菜单里所有会话无法区分。
        if role == "user" and s.get("title", _DEFAULT_TITLE) == _DEFAULT_TITLE:
            first_line = (text.strip().splitlines() or [""])[0][:12].strip()
            s["title"] = first_line or _DEFAULT_TITLE
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
        self._fixed_h = 0
        self._fit_retry = False
        self.setFrameShape(QFrame.NoFrame)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        # 头像：单色描边图标（原来是 emoji，缺 emoji 字体时整块变豆腐）
        avatar = QLabel()
        avatar.setObjectName("avatar")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setPixmap(icons.pixmap(
            "user" if role == "user" else "pet", T.ACCENT_SOFT, 20))

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
            f"color:{T.TEXT};font-size:15px;selection-background-color:"
            f"{T.rgba(T.ACCENT, 0.45)};}}")
        self.doc.document().setDefaultStyleSheet(_doc_css())
        self.doc.setMarkdown(text)
        self.doc.setContextMenuPolicy(Qt.CustomContextMenu)
        self.doc.customContextMenuRequested.connect(self._show_menu)
        # 高度随内容自适应；超过面板可视高才内部滚动，且滚动条可见
        self.doc.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.doc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.doc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.doc.setMinimumHeight(24)
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
        # 构造时 viewport 还没拿到真实宽度，等布局落定后再量一次
        QTimer.singleShot(0, self._fit_height)

    def _max_height(self) -> int:
        """单条消息的高度上限：跟随面板可视高，避免气泡里再套一层滚动。"""
        scroll = getattr(self.window(), "scroll", None)
        available = scroll.viewport().height() if scroll is not None else 0
        if available > 160:
            return max(160, int(available * 0.92))
        return 520

    def _fit_height(self):
        """按真实可视宽度重算高度。

        旧实现用 `viewport().width() or 380` 在布局前测量，高度按 380px 宽算完
        就 setFixedHeight 冻死，实际宽度只有 256px → 文字重新折行后下半截被
        静默裁掉（实测 20 字裁 22px、240 字裁 200px、长 Markdown 裁 2089px）。
        """
        if self.doc is None:
            return
        try:
            width = self.doc.viewport().width()
        except RuntimeError:
            # 气泡已随会话切换被 deleteLater 销毁，延后触发的补量直接放弃
            return
        if width < 60:
            if not self._fit_retry:           # 布局未完成，只补量一次
                self._fit_retry = True
                QTimer.singleShot(0, self._fit_height)
            return
        self._fit_retry = False
        doc = self.doc.document()
        doc.setTextWidth(width)
        needed = int(doc.documentLayout().documentSize().height()) + 8
        height = max(24, min(needed, self._max_height()))
        if height != self._fixed_h:
            self._fixed_h = height
            self.doc.setFixedHeight(height)

    def resizeEvent(self, event):  # noqa: N802 — 宽度变化后重新折行
        super().resizeEvent(event)
        QTimer.singleShot(0, self._fit_height)

    def update_markdown(self, text: str):
        """流式刷新：重设 Markdown 并重算高度。"""
        self._raw = text
        self.doc.setMarkdown(text)
        QTimer.singleShot(0, self._fit_height)

    def _code_blocks(self):
        return [m.strip() for m in _CODE_BLOCK_RE.findall(self._raw) if m.strip()]

    def _show_menu(self, pos):
        menu = QMenu(self.doc)
        menu.setStyleSheet(_menu_qss())
        copy_icon = icons.icon("copy", T.ACCENT_SOFT, 16)
        act_copy = menu.addAction(copy_icon, "复制消息（Markdown 原文）")
        blocks = self._code_blocks()
        if blocks:
            if len(blocks) == 1:
                act_code = menu.addAction(copy_icon, "复制代码块")
            else:
                act_code = menu.addAction(copy_icon, f"复制全部代码（{len(blocks)} 块）")
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


def _menu_qss() -> str:
    """右键菜单样式：选中态跟随 theme.accent（原来是硬编码的 indigo 紫）。"""
    return (f"QMenu{{background:{T.MENU_BG};color:{T.TEXT};"
            f"border:1px solid {T.MENU_BORDER};"
            "border-radius:8px;padding:6px;} QMenu::item{padding:6px 18px;}"
            f"QMenu::item:selected{{background:{T.ACCENT};"
            f"color:{T.ON_ACCENT};border-radius:6px;}}")


class _ThinkingBar(QLabel):
    """思考/活动指示条：活动文案优先，动画只在空闲文案上补呼吸点。

    旧实现两个缺陷（都已实测）：
    - 构造时不隐藏自己 → 冷启动面板顶部常驻一行「小土豆思考中」，而
      `_timer.isActive()` 为 False（状态位从未初始化，看着像卡住/在后台干活）；
    - `_tick` 每 360ms 直接 `setText("小土豆思考中"+点)`，把 set_activity 写进去的
      真实进度文案覆盖掉 → 实测 set_activity 后 1.2 秒，可见文本已变成
      「小土豆思考中 · · ·」，所谓「逐字显示 AI 每一步在干嘛」最长活 360ms。
    """

    _IDLE_TEXT = "小土豆思考中"

    def __init__(self, parent=None):
        super().__init__(self._IDLE_TEXT, parent)
        self.setObjectName("holoThinking")
        self._n = 0
        self._activity = ""
        self._timer = QTimer(self)
        self._timer.setInterval(360)
        self._timer.timeout.connect(self._tick)
        self.setVisible(False)          # 空闲态：不显示、不误导

    def _render(self):
        if self._activity:
            self.setText(self._activity)
        else:
            self.setText(self._IDLE_TEXT + " ·" * self._n)

    def _tick(self):
        self._n = (self._n + 1) % 4
        self._render()

    def set_activity(self, text: str):
        """写真实进度文案；为空则退回「思考中 + 呼吸点」。"""
        self._activity = str(text or "")
        self._render()

    def start(self):
        self._timer.start()
        self.setVisible(True)

    def stop(self):
        self._timer.stop()
        self._activity = ""
        self._n = 0
        self._render()
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
    approval_resolved = Signal(int, str)
    social_refresh_requested = Signal()
    social_send_requested = Signal(str, str)

    # (图标名, 标签, 能力键)：图标见 icons.py（原来是 8 个 emoji 功能按钮）
    FEATURES = [
        ("voice", "语音", "voice"),
        ("tools", "工具", "tools"),
        ("browser", "联网", "browser"),
        ("plug", "万能插", "universal_plug"),
        ("tentacle", "触手", "tentacle"),
        ("social", "朋友圈", "eigenflux"),
        ("agent", "Agent", "agent"),
        ("model", "模型", "model"),
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
        self._chat_width = self.width()

        self._build_ui()
        self._apply_qss(theme)
        self._render_messages()
        # 冷启动状态位初始化：旧版没有这一步，面板一出现就挂着「小土豆思考中」
        self.set_thinking(False)

        # V8：面板可拖动（按住头部/空白处拖拽；避开按钮和输入区）
        self._drag_pos = None
        self.frame.setMouseTracking(True)
        self.frame.installEventFilter(self)


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

        # ---- 左侧图标导航栏（V8：无重复创建；图标为单色描边 SVG）----
        nav = QVBoxLayout()
        nav.setContentsMargins(6, 10, 6, 10)
        nav.setSpacing(8)
        nav.addWidget(self._nav_btn("new", "新建会话", self._new_session))
        nav.addWidget(self._nav_btn("history", "历史会话", self._show_history))
        nav.addWidget(self._nav_btn(
            "social", "AI 朋友圈", lambda: self.feature_clicked.emit("eigenflux")))
        nav.addWidget(self._nav_btn("persona", "切换形象", self._pick_persona))
        nav.addStretch(1)
        nav.addWidget(self._nav_btn("settings", "设置", self._show_settings))
        nav.addWidget(self._nav_btn("close", "隐藏面板",
                                    lambda: self.close_requested.emit()))
        root.addLayout(nav)

        # ---- 主区 ----
        main = QVBoxLayout()
        main.setContentsMargins(12, 12, 14, 12)
        main.setSpacing(8)

        header = QHBoxLayout()
        header.setSpacing(10)
        badge = QLabel()
        badge.setObjectName("badge")
        badge.setFixedSize(38, 38)
        badge.setAlignment(Qt.AlignCenter)
        badge.setPixmap(icons.pixmap("pet", T.ACCENT_SOFT, 26))
        name_col = QVBoxLayout()
        name_col.setSpacing(0)
        name = QLabel("GBT小土豆V8")
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
        header.addWidget(self._nav_btn("close", "隐藏面板",
                                       lambda: self.close_requested.emit()))
        main.addLayout(header)

        self.banner = QLabel("嗨～我是小土豆。代码块、表格、Markdown 我都能排好；"
                             "右键气泡可复制代码。Enter 发送，Shift+Enter 换行。")
        self.banner.setObjectName("banner")
        self.banner.setWordWrap(True)
        main.addWidget(self.banner)

        # 八个原生入口分两排，窄面板不挤压也不截断。
        feature_bar = QGridLayout()
        feature_bar.setSpacing(6)
        for index, (icon_name, label, key) in enumerate(self.FEATURES):
            b = QPushButton(label)
            b.setObjectName("featureBtn")
            b.setCursor(Qt.PointingHandCursor)
            icons.apply(b, icon_name, T.ACCENT_SOFT, 16)
            b.clicked.connect(lambda checked=False, k=key: self.feature_clicked.emit(k))
            feature_bar.addWidget(b, index // 4, index % 4)
        main.addLayout(feature_bar)

        # 消息流
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("holoScroll")
        self.msg_container = QWidget()
        self.msg_container.setObjectName("msgContainer")   # 透明底见 _apply_qss
        self.scroll.viewport().setAutoFillBackground(False)
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(0, 0, 0, 0)
        self.msg_layout.setSpacing(8)
        self.msg_layout.addStretch(1)
        self.scroll.setWidget(self.msg_container)
        main.addWidget(self.scroll, 1)

        # 思考指示（动态）
        self.thinking = _ThinkingBar(self)
        main.addWidget(self.thinking)

        # 审批卡片：Codex 请求主人裁决时显示（命令 / 文件 / 权限 / 提问）
        self._approval_req_id = None
        self.approval_card = QFrame(self)
        self.approval_card.setObjectName("approvalCard")
        self.approval_card.setVisible(False)
        approval_col = QVBoxLayout(self.approval_card)
        approval_col.setContentsMargins(12, 10, 12, 10)
        approval_col.setSpacing(6)
        self.approval_title = QLabel("需要你确认")
        self.approval_title.setObjectName("approvalTitle")
        self.approval_detail = QTextEdit(self)
        self.approval_detail.setObjectName("approvalDetail")
        self.approval_detail.setReadOnly(True)
        self.approval_detail.setFixedHeight(92)
        approval_col.addWidget(self.approval_title)
        approval_col.addWidget(self.approval_detail)
        approval_btns = QHBoxLayout()
        approval_btns.setSpacing(6)
        for label, decision in (
            ("允许一次", "accept"),
            ("本会话允许", "acceptForSession"),
            ("拒绝", "decline"),
            ("取消任务", "cancel"),
        ):
            b = QPushButton(label)
            b.setObjectName("approvalBtn")
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(
                lambda checked=False, d=decision: self._resolve_approval(d))
            approval_btns.addWidget(b)
        approval_col.addLayout(approval_btns)
        main.addWidget(self.approval_card)

        # 输入区
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        attach = QPushButton()
        attach.setObjectName("inputBtn")
        attach.setFixedSize(36, 36)
        attach.setToolTip("附件（即将上线）")
        icons.apply(attach, "attach", T.ACCENT_SOFT, 18)
        attach.clicked.connect(lambda: self.add_message(
            "assistant", "附件功能在路上啦，v6.1 就能发文件给我看～"))
        self.input = QTextEdit(self)
        self.input.setObjectName("holoInput")
        self.input.setPlaceholderText("输入消息（支持 Markdown / 代码），"
                                      "Enter 发送 / Shift+Enter 换行")
        self.input.setFixedHeight(72)
        self.input.installEventFilter(self)
        mic = QPushButton()
        mic.setObjectName("inputBtn")
        mic.setFixedSize(36, 36)
        mic.setToolTip("朗读开关（只听不说：还没有语音输入）")
        icons.apply(mic, "voice", T.ACCENT_SOFT, 18)
        mic.clicked.connect(lambda: self.feature_clicked.emit("voice"))
        stop = QPushButton()
        stop.setObjectName("inputBtn")
        stop.setFixedSize(36, 36)
        stop.setToolTip("中断当前任务")
        icons.apply(stop, "stop", T.ACCENT_SOFT, 18)
        stop.clicked.connect(lambda: self.feature_clicked.emit("stop"))
        send = QPushButton()
        send.setObjectName("holoSend")
        send.setFixedSize(36, 36)
        send.setToolTip("发送")
        icons.apply(send, "send", T.ON_ACCENT, 18)
        send.clicked.connect(self._submit)
        input_row.addWidget(attach)
        input_row.addWidget(self.input, 1)
        input_row.addWidget(mic)
        input_row.addWidget(stop)
        input_row.addWidget(send)
        main.addLayout(input_row)

        status = QHBoxLayout()
        self.mind_label = QLabel("心智 平稳")
        self.mind_label.setObjectName("mindState")
        self.telemetry_text = QLabel("")
        self.telemetry_text.setObjectName("telemetry")
        # 好感度：图标用描边爱心（原来直接拿心形字符当图标），数值单独一个 label
        self.affection_icon = QLabel()
        self.affection_icon.setPixmap(icons.pixmap("heart", T.AFFECTION, 13))
        self.affection_label = QLabel("0")
        self.affection_label.setObjectName("affection")
        self.session_label = QLabel("会话 1")
        self.session_label.setObjectName("telemetry")
        status.addWidget(self.mind_label)
        status.addWidget(self.telemetry_text, 1)
        status.addWidget(self.session_label)
        status.addWidget(self.affection_icon)
        status.addWidget(self.affection_label)
        main.addLayout(status)

        root.addLayout(main)

        # ---- AI 朋友圈侧抽屉：默认隐藏，展开时扩展面板而不是挤占会话区 ----
        self.social_drawer = EigenFluxDrawer(self)
        self.social_drawer.closed.connect(self.close_social)
        self.social_drawer.refresh_requested.connect(
            self.social_refresh_requested.emit)
        self.social_drawer.send_requested.connect(
            self.social_send_requested.emit)
        self.social_drawer.setVisible(False)
        root.addWidget(self.social_drawer)

    # ---------------- 事件过滤：Enter 发送 ----------------
    def eventFilter(self, obj, event):
        if obj is self.input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and \
                    not event.modifiers() & Qt.ShiftModifier:
                self._submit()
                return True
        # 面板头部拖拽：按下记录起点，移动拖动，松开清零
        if obj is self.frame:
            if event.type() == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                # 只允许头部区（y < 90）拖拽，避免挡住消息区/输入区的鼠标交互
                if event.position().y() < 90:
                    self._drag_pos = (event.globalPosition().toPoint()
                                      - self.frameGeometry().topLeft())
            elif event.type() == QEvent.MouseMove and self._drag_pos is not None:
                if event.buttons() & Qt.LeftButton:
                    self.move(event.globalPosition().toPoint() - self._drag_pos)
                    return True
            elif event.type() == QEvent.MouseButtonRelease:
                self._drag_pos = None
        return super().eventFilter(obj, event)

    # ---------------- 会话 ----------------
    def _new_session(self):
        self.store.new()
        self._render_messages()
        self.session_switched.emit([])
        self._update_session_label()

    def _show_history(self):
        menu = QMenu(self)
        menu.setStyleSheet(_menu_qss())
        chat_icon = icons.icon("history", T.ACCENT_SOFT, 16)
        for i, s in enumerate(self.store.sessions[:10]):
            title = s.get("title", "对话")
            n = len(s.get("messages", []))
            act = menu.addAction(chat_icon, f"{title}（{n} 条）")
            act.triggered.connect(lambda checked=False, idx=i: self._switch_session(idx))
        menu.exec(self.mapToGlobal(self.rect().topLeft() + self.rect().center()))

    def _switch_session(self, idx: int):
        if self.store.switch(idx):
            self._render_messages()
            self.session_switched.emit(self.store.history_for_chat(idx))
            self._update_session_label()

    def _pick_persona(self):
        # 兜底清单只在 main.py 没注入 _available_models 时生效；nn 因资源缺失
        # （贴图 nn.2048/texture_00.png 不存在）已被 main.list_available_models 过滤
        models = getattr(self, "_available_models", ["haru", "mao", "llny"])
        menu = QMenu(self)
        menu.setStyleSheet(_menu_qss())
        persona_icon = icons.icon("persona", T.ACCENT_SOFT, 16)
        for m in models:
            act = menu.addAction(persona_icon, m)
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
        self.msg_container.setUpdatesEnabled(False)   # 批量重建：避免每条都重排
        try:
            for m in self.store.session.get("messages", []):
                self._append_bubble(m["role"], m["text"], m.get("ts", ""))
        finally:
            self.msg_container.setUpdatesEnabled(True)
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

    def add_message(self, role: str, text: str, persist: bool = True):
        """追加一条消息。

        ``persist=False`` 用于桌宠旁白（behavior 的随机台词）：它属于界面气泡，
        不属于会话记录——旧版把每 60s 一次的自言自语全写进 sessions.json，
        实测单会话 300 条里 295 条是 assistant 台词，冷启动要重建它们，
        面板构造耗时 1137ms（空会话 25ms）。
        """
        ts = time.strftime("%H:%M")
        if persist:
            self.store.add(role, text, ts)
        self._append_bubble(role, text, ts)
        self._scroll_bottom()
        self._update_session_label()

    # ---------------- 流式显示（编程 AI 核心体验）----------------
    def set_activity(self, text: str):
        """V8：活动状态行——编程时逐字显示 AI 每一步在干嘛（如这个对话框）。

        文案交由 _ThinkingBar 托管：它以活动文案为主，只在没有活动文案时
        显示「小土豆思考中 + 呼吸点」，不再反过来覆盖真实进度。
        """
        self.thinking.set_activity(text)

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

    # ---------------- 审批（Codex 请求主人裁决）----------------
    def show_approval(self, request: dict) -> None:
        """显示审批卡片；请求由 Codex 通道发起，主人点击后原路回传。"""
        self._approval_req_id = request.get("id")
        summary = request.get("summary") or {}
        self.approval_title.setText(summary.get("title") or "需要你确认")
        detail = summary.get("detail") or ""
        cwd = summary.get("cwd")
        if cwd:
            detail = f"{detail}\n\n工作目录：{cwd}"
        self.approval_detail.setPlainText(detail)
        self.approval_card.setVisible(True)
        self._scroll_bottom()

    def _resolve_approval(self, decision: str) -> None:
        req_id = self._approval_req_id
        if req_id is None:
            return
        self._approval_req_id = None
        self.approval_card.setVisible(False)
        self.approval_resolved.emit(int(req_id), decision)

    # ---------------- 状态 ----------------
    def set_thinking(self, on: bool):
        self.thinking.start() if on else self.thinking.stop()

    def update_telemetry(self, text: str) -> None:
        self.telemetry_text.setText(text)

    def set_affection(self, value: int) -> None:
        self.affection_label.setText(str(value))

    def set_mind_state(self, pulse: dict) -> None:
        """接收心智脉冲，只更新状态呈现，不改变对话内容与能力行为。"""
        if not isinstance(pulse, dict):
            return
        mood = str(pulse.get("mood") or "平稳")
        presence = str(pulse.get("presence") or "在场")
        color = str(pulse.get("color") or T.ACCENT_BRIGHT)
        meta = pulse.get("metacognition") or {}
        owner = pulse.get("owner_model") or {}
        intention = pulse.get("intention") or {}
        tooltip_lines = [
            str((pulse.get("communication") or {}).get("reason") or ""),
            f"主人推断：{owner.get('state', 'unknown')}（置信度 {owner.get('confidence', '?')}）",
            f"当前需要：{owner.get('current_need', '')}",
            f"元认知：{meta.get('mode', 'inspect_then_act')}｜{meta.get('selected_option', '')}",
            f"意图：{intention.get('label', '')}",
        ]
        if meta.get("should_pause"):
            tooltip_lines.append("检测到低置信或高风险：先确认再推进")
        self.mind_label.setText(f"心智 {mood} · {presence}")
        self.mind_label.setToolTip("\n".join(line for line in tooltip_lines if line))
        self.mind_label.setStyleSheet(
            f"color:{color};font-size:12px;font-weight:700;font-family:Consolas;"
        )
        self.reactor.setStyleSheet(f"color:{color};")
        self.reactor.setText("◉" if bool(pulse.get("ok", True)) else "◇")

    # ---------------- AI 朋友圈侧栏 ----------------
    def open_social(self):
        if self.social_drawer.isVisible():
            return
        self.social_drawer.setVisible(True)
        self.resize(
            self._chat_width + self.social_drawer.width(),
            self.height(),
        )
        self._clamp_to_screen()
        self.social_refresh_requested.emit()

    def close_social(self):
        if not self.social_drawer.isVisible():
            return
        self.social_drawer.setVisible(False)
        self.resize(self._chat_width, self.height())
        self._clamp_to_screen()

    def toggle_social(self):
        if self.social_drawer.isVisible():
            self.close_social()
        else:
            self.open_social()

    def apply_social_snapshot(self, snapshot: dict) -> None:
        self.social_drawer.apply_snapshot(snapshot)

    def set_social_activity(self, text: str) -> None:
        self.social_drawer.set_activity(text)

    def set_social_error(self, text: str) -> None:
        self.social_drawer.set_activity(text)
        self.social_drawer.set_status(text, ok=False)

    def _clamp_to_screen(self):
        from PySide6.QtWidgets import QApplication
        center = self.frameGeometry().center()
        screen = QApplication.screenAt(center) or QApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()
        x = max(avail.left(), min(self.x(), avail.right() - self.width()))
        y = max(avail.top(), min(self.y(), avail.bottom() - self.height()))
        self.move(x, y)

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
    def _nav_btn(self, icon_name: str, tip: str, cb) -> QPushButton:
        b = QPushButton()
        b.setObjectName("navBtn")
        b.setFixedSize(36, 36)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        icons.apply(b, icon_name, T.ACCENT_SOFT, 18)
        b.clicked.connect(cb)
        return b

    def _apply_qss(self, theme: dict):
        """面板 QSS：颜色全部来自 ui_theme token（config.panel.theme 在此生效）。"""
        T.apply_theme(theme)
        a = T.ACCENT
        self.setStyleSheet(f"""
            QFrame#holoFrame {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {T.SURFACE_TOP}, stop:1 {T.SURFACE});
                border: 2px solid {T.rgba(T.ACCENT_EDGE, 0.75)};
                border-radius: 6px;
            }}
            QFrame#bubbleUser {{
                background: {T.rgba(a, 0.16)};
                border: 1px solid {T.rgba(a, 0.35)};
                border-radius: 8px;
            }}
            QFrame#bubbleBot {{
                background: rgba(8,32,54,0.72);
                border: 1px solid {T.rgba(a, 0.28)};
                border-radius: 8px;
            }}
            QLabel#msgTime {{ color:{T.TEXT_MUTED}; font-size:11px; font-family:Consolas; }}
            QLabel#badge {{
                background: {T.rgba(a, 0.14)};
                border: 1px solid {T.rgba(T.ACCENT_EDGE, 0.65)};
                border-radius: 6px;
            }}
            QLabel#charName {{
                color:{T.ACCENT_TITLE}; font-size:17px; font-weight:800;
                letter-spacing:1px; font-family:Consolas;
            }}
            QLabel#online {{ color:{T.rgba(a, 0.82)}; font-size:12px; font-family:Consolas; }}
            QLabel#reactor {{ color:{T.ACCENT_EDGE}; font-size:13px; font-weight:800; }}
            QLabel#banner {{
                background: {T.rgba(a, 0.08)};
                border: 1px solid {T.rgba(a, 0.25)};
                border-radius: 4px; color:{T.TEXT_DIM};
                padding: 8px 12px; font-size: 13px;
            }}
            QLabel#telemetry {{ color:{T.rgba(a, 0.82)}; font-size:12px; font-family:Consolas; }}
            QLabel#mindState {{ color:{T.ACCENT_BRIGHT}; font-size:12px; font-weight:700;
                                font-family:Consolas; }}
            QLabel#affection {{ color:{T.AFFECTION}; font-size:13px; font-weight:700; font-family:Consolas; }}
            QLabel#holoThinking {{ color:{T.ACCENT_EDGE}; font-size: 13px; font-family:Consolas; }}
            QFrame#approvalCard {{
                background: rgba(58,22,8,0.92);
                border: 1px solid {T.rgba(T.WARN, 0.75)};
                border-radius: 6px;
            }}
            QLabel#approvalTitle {{
                color:{T.WARN_TITLE}; font-size:13px; font-weight:800;
                font-family:Consolas; letter-spacing:1px;
            }}
            QTextEdit#approvalDetail {{
                background: rgba(12,10,4,0.75);
                border: 1px solid {T.rgba(T.WARN, 0.35)};
                border-radius: 4px; color:{T.WARN_TEXT};
                font-family:Consolas, monospace; font-size:12px; padding:6px;
            }}
            QPushButton#approvalBtn {{
                background: rgba(120,72,10,0.85); color:{T.WARN_BTN};
                border: 1px solid {T.rgba(T.WARN, 0.6)};
                border-radius: 5px; padding: 6px 10px;
                font-size:12px; font-weight:700; font-family:Consolas;
            }}
            QPushButton#approvalBtn:hover {{
                background: rgba(180,110,15,0.9); color:{T.WARN_BTN_HOVER};
                border-color:{T.WARN};
            }}
            QPushButton#approvalBtn:pressed {{ background: {T.rgba(T.WARN, 0.42)}; }}
            QPushButton#navBtn {{
                background: rgba(10,40,62,0.85); color:{T.ACCENT_SOFT};
                border: 1px solid {T.rgba(a, 0.35)};
                border-radius: 6px;
            }}
            QPushButton#navBtn:hover {{
                background: {T.rgba(a, 0.25)}; border-color:{T.ACCENT_EDGE};
                color:{T.TEXT_BRIGHT};
            }}
            QPushButton#featureBtn {{
                background: rgba(10,40,62,0.8);
                color:{T.ACCENT_SOFT};
                border: 1px solid {T.rgba(a, 0.4)};
                border-radius: 6px; padding: 6px 10px; font-size: 12px;
                font-weight: 600; font-family:Consolas;
            }}
            QPushButton#featureBtn:hover {{
                background: {T.rgba(a, 0.22)}; border-color:{T.ACCENT_EDGE};
                color:{T.TEXT_BRIGHT};
            }}
            QPushButton#featureBtn:pressed {{ background: {T.rgba(a, 0.38)}; }}
            QScrollArea#holoScroll {{ background: transparent; border: none; }}
            QWidget#msgContainer {{ background: transparent; }}
            /* 滚动条：长消息在气泡内滚动时必须有可见滚动条（原来是禁掉的），
               默认 Qt 样式是浅色轨道，与 HUD 主题冲突，这里统一成主色。 */
            QScrollBar:vertical {{
                background: rgba(10,40,62,0.55); width: 8px; margin: 0; border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {T.rgba(a, 0.55)}; border-radius: 4px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {T.rgba(a, 0.8)}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0; background: none; border: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QTextEdit#holoInput {{
                background: rgba(6,26,44,0.9);
                border: 1px solid {T.rgba(a, 0.55)};
                border-radius: 6px; padding: 10px 14px;
                color:{T.TEXT}; font-size: 15px;
                selection-background-color: {T.rgba(a, 0.45)};
            }}
            QTextEdit#holoInput:focus {{
                border-color:{T.ACCENT_EDGE}; background: rgba(8,32,54,0.95);
            }}
            QPushButton#inputBtn {{
                background: rgba(10,40,62,0.9); color:{T.ACCENT_SOFT};
                border: 1px solid {T.rgba(a, 0.4)};
                border-radius: 6px;
            }}
            QPushButton#inputBtn:hover {{ background: {T.rgba(a, 0.25)}; }}
            QPushButton#holoSend {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {T.ACCENT}, stop:1 {T.ACCENT_DEEP});
                color: {T.ON_ACCENT}; border: 1px solid {T.ACCENT_EDGE};
                border-radius: 6px; font-size: 15px; font-weight: 800;
            }}
            QPushButton#holoSend:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {T.ACCENT_BRIGHT}, stop:1 {T.ACCENT});
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
