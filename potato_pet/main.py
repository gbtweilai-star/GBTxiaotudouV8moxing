"""GBT小土豆 · 桌面数字人整合入口.

装配三层：形象层(Live2D 窗口) + 对话层(全息面板+聊天) + 行为层(FSM 引擎)。
形象多选：右键菜单可切换 Live2D 模型（haru/mao/nn/llny，缺哪个跳过哪个）。
"""
from __future__ import annotations

import json
import logging
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("potato.main")


def load_config() -> dict:
    cfg_path = os.path.join(BASE_DIR, "config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_available_models() -> list:
    """扫描 resources/ 下所有含 .model3.json 的目录，作为形象多选清单。"""
    res = os.path.join(BASE_DIR, "resources")
    models = []
    if os.path.isdir(res):
        for name in sorted(os.listdir(res)):
            d = os.path.join(res, name)
            if os.path.isdir(d):
                for f in os.listdir(d):
                    if f.endswith(".model3.json"):
                        models.append(name)
                        break
    return models


def main() -> int:
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setApplicationName("GBT Potatodoll")

    config = load_config()

    from behavior import BehaviorEngine
    from chat_client import ChatClient
    from holo_panel import HoloPanel
    from pet_window import PetWindow

    # ---- 形象层 ----
    model_dir = os.path.join(BASE_DIR, "resources",
                             config["pet"].get("model_dir", "haru"))
    pet = PetWindow(model_dir=model_dir, config=config)

    # ---- 语音（v2）----
    import voice
    voice.init(enabled=config.get("voice", {}).get("enabled", True))

    # ---- 对话层 ----
    chat = ChatClient(config)
    panel = HoloPanel(config)

    # ---- 行为层 ----
    behavior = None
    if config.get("behavior", {}).get("enabled", True):
        behavior = BehaviorEngine(config)
        behavior.set_callbacks(
            get_pet_rect=pet.window_rect,
            get_panel_rect=lambda: panel.panel_rect() if panel.isVisible() else None,
            move_pet_to=lambda x, y: pet.move(int(x), int(y)),
            set_panel_visible=lambda on: (panel.show_panel() if on else panel.hide_panel()),
            play_motion=lambda group, priority=1: pet.start_motion(group, priority),
            set_expression=lambda name: pet.set_expression(name),
            say=lambda text: panel.add_message("assistant", text),
            sync_affection=lambda v: panel.set_affection(v),
        )

    # ---- 接线 ----
    from PySide6.QtCore import QObject, Signal

    class _Relay(QObject):
        """跨线程中继：工作线程的聊天回复经信号投递到 GUI 线程。"""
        replied = Signal(str)

        def __init__(self):
            super().__init__()
            self.replied.connect(self._on_replied)

        def _on_replied(self, text):
            panel.add_message("assistant", text)
            panel.set_thinking(False)
            if behavior:
                behavior.on_message("assistant", text)
            # v2: 语音说话
            if config.get("voice", {}).get("enabled", True):
                import voice
                voice.speak(text)

    relay = _Relay()

    def on_reply(text: str) -> None:
        # 可能从工作线程调用，用信号切回 GUI 线程
        relay.replied.emit(text)

    def on_submit(text: str) -> None:
        panel.add_message("user", text)
        panel.set_thinking(True)
        if behavior:
            behavior.on_message("user", text)
        # v2: 离线工具触发（时间/系统状态/开应用）
        import tools
        result, hit = tools.try_offline_tool(text)
        if hit:
            panel.add_message("assistant", result)
            panel.set_thinking(False)
            if config.get("voice", {}).get("enabled", True):
                import voice
                voice.speak(result)
            return
        chat.send(text, on_reply)

    panel.message_submitted.connect(on_submit)
    panel.close_requested.connect(panel.hide_panel)

    # ---- v4: 会话切换同步聊天历史 ----
    def on_session_switch(history):
        chat.replace_history(history)
        panel.add_message("assistant", "已切换会话，上下文同步完成～")

    panel.session_switched.connect(on_session_switch)

    # ---- v4: 面板内直接换形象 ----
    import win_utils  # noqa: F401
    models = list_available_models()

    def on_persona(name: str):
        if name not in models:
            return
        cfg_path = os.path.join(BASE_DIR, "config.json")
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        cfg["pet"]["model_dir"] = name
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        panel.add_message("assistant", f"换到 {name} 形象，重启后生效～（右键退出再启动即可）")

    panel.persona_change_requested.connect(on_persona)
    panel._available_models = models

    # ---- v3: 功能入口接线 ----
    def on_feature(key: str) -> None:
        import voice as voice_mod
        if key == "voice":
            if config.get("voice", {}).get("enabled", True) and voice_mod.is_available():
                panel.add_message("assistant", "语音模式准备中，你可以直接对我说话啦（当前为文字模拟）～")
            else:
                panel.add_message("assistant", "语音引擎还没就绪哦，先打字聊吧～")
        elif key == "tools":
            panel.add_message("assistant", "我会的活儿：报时间、查系统状态、打开应用。试试说「现在几点了」？")
        elif key == "browser":
            import webbrowser
            webbrowser.open("https://www.bing.com")
            panel.add_message("assistant", "已为你打开联网搜索窗口～")
        elif key == "agent":
            panel.add_message("assistant", "委托任务功能路上啦，v4 接入 OpenClaw 网关后我就能替你干活了～")
        elif key == "model":
            model = config.get("chat", {}).get("model", "离线模式")
            api = "已接 GLM" if config.get("chat", {}).get("api_key") else "离线俏皮模式（无 API key）"
            panel.add_message("assistant", f"当前大脑：{model}（{api}）")
        elif key == "settings":
            panel.add_message("assistant", "右键我可以切换形象（haru/mao/llny/nn）和开关面板哦～")

    panel.feature_clicked.connect(on_feature)

    pet.panel_toggle_requested.connect(panel.toggle)
    pet.quit_requested.connect(app.quit)
    if behavior:
        pet.clicked.connect(behavior.on_pet_clicked)
        pet.drag_pos_changed.connect(lambda *_: behavior.note_activity())
        pet.drag_finished.connect(behavior.on_drag_end)  # v3: 拖拽落定

    # ---- 形象多选：把可用模型注入右键菜单 ----
    models = list_available_models()
    if len(models) > 1:
        from PySide6.QtGui import QAction
        menu_holder = {}

        def switch_model(name: str):
            cfg_path = os.path.join(BASE_DIR, "config.json")
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["pet"]["model_dir"] = name
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            # 重启自身以加载新形象
            python = sys.executable
            os.execv(python, [python, os.path.abspath(__file__)] + sys.argv[1:])

        pet._switch_model = switch_model
        pet._available_models = models

    # 面板初始位置：摆在小土豆附近
    pet.show()
    if config["panel"].get("auto_show_on_start", True):
        panel.move_near(pet.window_rect())
        panel.show_panel()

    # ---- v2: 全息遥测条（HoloJarvis 风格，每 5 秒刷新）----
    import tools as tools_mod
    from PySide6.QtCore import QTimer

    def refresh_telemetry():
        try:
            panel.update_telemetry(tools_mod.get_system_status())
        except Exception as e:
            logger.warning("telemetry refresh failed: %s", e)

    telemetry_timer = QTimer(app)
    telemetry_timer.setInterval(5000)
    telemetry_timer.timeout.connect(refresh_telemetry)
    refresh_telemetry()
    telemetry_timer.start()

    if behavior:
        behavior.start()

    logger.info("GBT potato desktop doll started (models=%s)", models)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
