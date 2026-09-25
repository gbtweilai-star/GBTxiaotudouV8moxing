"""GBT小土豆 · 桌面数字人整合入口.

装配三层：形象层(Live2D 窗口) + 对话层(全息面板+聊天) + 行为层(FSM 引擎)。
形象多选：右键菜单可切换 Live2D 模型（haru/mao/nn/llny，缺哪个跳过哪个）。
"""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
from logging.handlers import RotatingFileHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("potato.main")


def setup_logging(config: dict) -> None:
    """按 config.logging 装配日志（控制台 + 落盘轮转）。

    config.json 声明了 {"level": "INFO", "file": "potato.log"}，但旧代码只调了
    logging.basicConfig(level, format)——没有任何 FileHandler，实测全仓递归都
    找不到 potato.log：桌宠是 GUI 程序，没有控制台，排障信息等于不可得。
    这里把声明的日志文件真正接上（1MB × 3 轮转，避免无限增长）。
    """
    cfg = config.get("logging") or {}
    level = getattr(logging, str(cfg.get("level") or "INFO").upper(),
                    logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    name = str(cfg.get("file") or "").strip()
    if name:
        path = name if os.path.isabs(name) else os.path.join(BASE_DIR, name)
        try:
            handlers.append(RotatingFileHandler(
                path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"))
        except OSError as exc:                      # 落盘失败不阻塞启动
            logger.warning("log file %s unavailable: %s", path, exc)
    for handler in handlers:
        handler.setFormatter(fmt)
    logging.basicConfig(level=level, handlers=handlers, force=True)


def load_config() -> dict:
    cfg_path = os.path.join(BASE_DIR, "config.json")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def model_problem(model_dir: str) -> str:
    """模型自检：model3.json 引用的贴图/动作必须真的存在。返回空串=可用。

    实测 resources/nn/nn.model3.json 引用 nn.2048/texture_00.png 而该目录不存在，
    37 条 Motion 的 sounds/*.wav 也全部缺失 —— 旧版仍把 nn 列进形象清单，
    用户切过去只会看到粉色占位圆脸，日志之外没有任何提示。
    """
    if not os.path.isdir(model_dir):
        return "目录不存在"
    names = [f for f in os.listdir(model_dir) if f.endswith(".model3.json")]
    if not names:
        return "目录里没有 .model3.json"
    try:
        with open(os.path.join(model_dir, names[0]), "r", encoding="utf-8") as f:
            refs = (json.load(f) or {}).get("FileReferences") or {}
    except Exception as exc:  # noqa: BLE001
        return f"model3.json 解析失败：{exc}"
    missing = [str(t) for t in (refs.get("Textures") or [])
               if not os.path.exists(os.path.join(
                   model_dir, str(t).replace("/", os.sep)))]
    if missing:
        return f"贴图缺失：{missing[0]}"
    return ""


def list_available_models() -> list:
    """扫描 resources/ 下所有含 .model3.json 且资源完整的目录。

    资源不完整的模型不再出现在形象清单里（旧版会把坏模型列出来，
    选中后静默退化成占位形象）。
    """
    res = os.path.join(BASE_DIR, "resources")
    models = []
    if os.path.isdir(res):
        for name in sorted(os.listdir(res)):
            d = os.path.join(res, name)
            if not os.path.isdir(d) or not any(
                    f.endswith(".model3.json") for f in os.listdir(d)):
                continue
            problem = model_problem(d)
            if problem:
                logger.warning("model %s skipped: %s", name, problem)
                continue
            models.append(name)
    return models


def main() -> int:
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setApplicationName("GBT Potatodoll")

    config = load_config()
    setup_logging(config)

    from behavior import BehaviorEngine
    from chat_client import ChatClient
    from eigenflux_bridge import EigenFluxBridge
    from holo_panel import HoloPanel
    from mind_client import MindClient
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
    social = EigenFluxBridge(config, panel)
    social.snapshot.connect(panel.apply_social_snapshot)
    social.activity.connect(panel.set_social_activity)
    social.error.connect(panel.set_social_error)
    panel.social_refresh_requested.connect(social.refresh_async)
    panel.social_send_requested.connect(social.send_async)

    # ---- 形象加载失败要说原因（不再只留一行日志）----
    configured_model = str(config.get("pet", {}).get("model_dir") or "haru")
    problem = model_problem(model_dir)
    if problem:
        logger.warning("configured model %s unusable: %s",
                       configured_model, problem)

    def on_model_load_failed(reason: str) -> None:
        panel.add_message(
            "assistant",
            f"形象「{configured_model}」没加载起来，先用了占位形象：{reason}",
            persist=False)

    pet.model_load_failed.connect(on_model_load_failed)

    # ---- 行为层 ----
    behavior = None
    if config.get("behavior", {}).get("enabled", True):
        behavior = BehaviorEngine(config)

        def _move_pet_keep_on_top(x, y):
            pet.move(int(x), int(y))
            pet.raise_()   # 移动后仍保持在面板之上

        behavior.set_callbacks(
            get_pet_rect=pet.window_rect,
            get_panel_rect=lambda: panel.panel_rect() if panel.isVisible() else None,
            move_pet_to=_move_pet_keep_on_top,
            set_panel_visible=lambda on: (panel.show_panel() if on else panel.hide_panel()),
            play_motion=lambda group, priority=1: pet.start_motion(group, priority),
            set_expression=lambda name: pet.set_expression(name),
            say=lambda text: panel.add_message("assistant", text, persist=False),
            sync_affection=lambda v: panel.set_affection(v),
        )

    # ---- 心智层：感知/评估/需要/自我模型/主人心智/预演/反思 ----
    mind = MindClient()
    mind.observe("startup", importance=0.15)
    panel.set_mind_state(mind.pulse())

    def sync_mind(pulse=None):
        current = pulse if isinstance(pulse, dict) else mind.pulse()
        panel.set_mind_state(current)
        if behavior:
            behavior.apply_mind(current)
        return current

    # ---- 接线 ----
    from PySide6.QtCore import QObject, Signal

    class _Relay(QObject):
        """跨线程中继：流式 chunk / 完整回复经信号投递到 GUI 线程。"""
        chunk = Signal(str)      # 流式增量（V8）
        replied = Signal(str)
        mind_updated = Signal(dict)

        def __init__(self):
            super().__init__()
            self.chunk.connect(self._on_chunk)
            self.replied.connect(self._on_replied)

        def _on_chunk(self, delta: str):
            # 首个 chunk：结束思考指示，开启流式气泡
            if not getattr(self, "_streaming", False):
                panel.set_thinking(False)
                panel.begin_stream("assistant")
                self._streaming = True
            panel.append_stream_chunk(delta)
            # V8：编程时逐字显示 AI 行动（随内容长度切阶段文案）
            # 前缀原来用四个符号字形当图标（其中齿轮属 emoji 集、缺字变豆腐块），
            # 改为纯文字阶段名；状态行本身已由 _ThinkingBar 保证不被动画覆盖。
            n = len(panel._stream_buf and "".join(panel._stream_buf) or "")
            if n < 60:
                panel.set_activity("正在分析需求…")
            elif n < 200:
                panel.set_activity("正在构建方案…")
            elif n < 500:
                panel.set_activity("正在编写代码…")
            else:
                panel.set_activity("正在整理输出…")

        def _on_replied(self, text):
            if getattr(self, "_streaming", False):
                panel.end_stream()          # 流式收尾（含落盘）
                self._streaming = False
            else:
                panel.set_thinking(False)
                panel.add_message("assistant", text)
            if behavior:
                behavior.on_message("assistant", text)
            mind.observe(
                "assistant_message",
                importance=0.42,
                focus="normal",
            )
            sync_mind()
            # v2: 语音说话
            if config.get("voice", {}).get("enabled", True):
                import voice
                voice.speak(text)

    relay = _Relay()
    relay.mind_updated.connect(sync_mind)

    def on_chunk(delta: str, _full: str) -> None:
        # 工作线程 → GUI 线程（信号中继）
        relay.chunk.emit(delta)

    def on_reply(text: str) -> None:
        relay.replied.emit(text)

    # ---- V8: Codex 真通道（本机 app-server；不可用时自动降级到原有大脑）----
    from codex_client import CodexPanelClient
    codex = CodexPanelClient(config)
    codex_ready = codex.start()
    pending_codex = {"text": None, "falling_back": False}

    codex.chunk.connect(lambda delta: relay.chunk.emit(delta))
    codex.replied.connect(lambda text: relay.replied.emit(text))
    codex.thinking_changed.connect(panel.set_thinking)
    codex.status_changed.connect(panel.set_activity)
    codex.approval_requested.connect(panel.show_approval)
    panel.approval_resolved.connect(codex.resolve_approval)

    def on_codex_finished(_info):
        status = str((_info or {}).get("status") or "").strip().lower()
        task_text = pending_codex.get("text") or "Codex 回合"
        success = status in {
            "completed", "complete", "done", "success",
            "succeeded", "ok",
        }
        mind.observe(
            "task_succeeded" if success else "task_finished",
            task=task_text,
            importance=0.72,
            focus="deep" if success else "normal",
            status=status,
            side_effect=False,
            certainty=0.78 if success else 0.66,
        )
        sync_mind()
        pending_codex["text"] = None
        pending_codex["falling_back"] = False

    def on_codex_failed(err: str):
        text = pending_codex.get("text")
        mind.observe(
            "task_failed",
            task=text or "Codex 回合",
            error=err,
            importance=0.92,
            focus="deep",
            side_effect=False,
            certainty=0.84,
        )
        sync_mind()
        if pending_codex.get("falling_back") or not text:
            panel.set_thinking(False)
            panel.add_message("assistant", f"Codex 通道暂时不可用：{err}")
            return
        # 同一个问题不丢：切到原有 LLM 通道继续回答
        pending_codex["falling_back"] = True
        panel.set_thinking(False)
        logger.warning("codex unavailable, fallback to LLM channel: %s", err)
        chat.send(text, on_reply, on_chunk=on_chunk)

    codex.failed.connect(on_codex_failed)
    codex.turn_finished.connect(on_codex_finished)
    if codex_ready:
        logger.info("codex channel ready: %s", codex.status().get("codex_path"))
    else:
        logger.info("codex channel unavailable, using LLM chain")
    mind.observe("startup_ready", importance=0.25)
    sync_mind()

    def on_submit(text: str) -> None:
        panel.add_message("user", text)
        mind.observe(
            "user_message",
            text=text,
            importance=0.55,
            focus="normal",
        )
        sync_mind()
        panel.set_activity("◌ 正在理解你的需求…")
        panel.set_thinking(True)
        if behavior:
            behavior.on_message("user", text)
        # v2: 离线工具触发（时间/系统状态/开应用）
        import tools
        result, hit = tools.try_offline_tool(text)
        if hit:
            panel.add_message("assistant", result)
            panel.set_thinking(False)
            mind.observe(
                "task_succeeded",
                task=text,
                importance=0.52,
                focus="normal",
                side_effect=False,
                certainty=0.82,
            )
            sync_mind()
            if config.get("voice", {}).get("enabled", True):
                import voice
                voice.speak(result)
            return
        # Codex 优先；派发失败立即回落到原有聊天通道
        if codex_ready and codex.available:
            pending_codex["text"] = text
            pending_codex["falling_back"] = False
            if codex.send(text):
                return
        chat.send(text, on_reply, on_chunk=on_chunk)

    panel.message_submitted.connect(on_submit)
    panel.close_requested.connect(panel.hide_panel)

    # ---- V8: 会话切换同步聊天历史 ----
    def on_session_switch(history):
        chat.replace_history(history)
        codex.new_thread()
        panel.add_message("assistant", "已切换会话，上下文同步完成～")

    panel.session_switched.connect(on_session_switch)

    # ---- V8: 面板内直接换形象 ----
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
    def _gbt_body(result: dict) -> dict:
        if isinstance(result, dict) and isinstance(result.get("gbt_result"), dict):
            return result["gbt_result"]
        return result if isinstance(result, dict) else {}

    def _gbt_owner_call(kind: str, payload: dict | None = None) -> dict:
        from gbt_allinone import api
        from gbt_allinone.security import policy
        with policy.owner_session():
            return api.run_task(kind, payload or {})

    def _run_feature(message: str, busy: str, worker) -> None:
        """后台执行原生能力，经 Qt 信号回到 GUI 线程显示。"""
        panel.set_thinking(True)
        panel.set_activity(busy)
        mind.observe(
            "task_started",
            task=message or busy,
            importance=0.62,
            focus="tools",
            side_effect=True,
            certainty=0.58,
        )
        sync_mind()

        def _worker():
            try:
                text = worker()
                success = True
            except Exception as exc:  # noqa: BLE001
                logger.warning("feature task failed: %s", exc, exc_info=True)
                text = f"能力执行失败：{str(exc)[:220]}"
                success = False
            mind.observe(
                "task_succeeded" if success else "task_failed",
                task=message or busy,
                error="" if success else text,
                importance=0.68,
                focus="tools",
                side_effect=False,
                certainty=0.74 if success else 0.90,
            )
            relay.mind_updated.emit(mind.pulse())
            relay.replied.emit(str(text))

        threading.Thread(target=_worker, name="potato-feature-task",
                         daemon=True).start()

    def on_feature(key: str) -> None:
        import voice as voice_mod
        if key == "voice":
            # voice.is_available() 只说明「TTS 引擎能初始化」，与「能不能听」无关：
            # 全仓没有任何语音输入实现（无 speech_recognition/whisper/录音代码），
            # 原文案「你可以直接对我说话啦（当前为文字模拟）」是自相矛盾的假能力。
            if config.get("voice", {}).get("enabled", True) and voice_mod.is_available():
                panel.add_message("assistant", "我现在只能出声朗读回复，还听不见你说话～"
                                               "想让我听懂，先打字告诉我吧。")
            else:
                panel.add_message("assistant", "语音引擎还没就绪哦，先打字聊吧～")
        elif key == "tools":
            panel.add_message(
                "assistant",
                "原生入口都在面板上：万能插负责并行编排，触手负责现实感官与操作，"
                "联网走原生浏览器；原有时间和系统工具也保留。")
        elif key == "browser":
            def _browser_worker():
                result = _gbt_body(_gbt_owner_call("browser", {
                    "op": "native",
                    "action": "ensure",
                    "url": "https://www.bing.com",
                    "timeout": 15,
                }))
                body = result.get("result") if isinstance(result, dict) else {}
                if not isinstance(body, dict):
                    body = result
                if body.get("needs_browser_debug"):
                    return "原生浏览器还没就绪：没有发现可复用的调试会话。"
                if body.get("status") in ("already_satisfied",):
                    return "目标搜索页已经存在，我复用了现有窗口，没有重复打开。"
                if body.get("status") in ("ready", "launched", "already_running"):
                    browser = body.get("browser") or "浏览器"
                    return f"原生浏览器已接通：{browser}，联网搜索页已复用或就绪。"
                return f"原生浏览器返回：{json.dumps(body, ensure_ascii=False)[:300]}"
            _run_feature("", "正在检查原生浏览器…", _browser_worker)
        elif key == "universal_plug":
            def _plug_worker():
                result = _gbt_body(_gbt_owner_call(
                    "wf_status", {"limit": 5}))
                body = result.get("result") if isinstance(result, dict) else {}
                rows = (body or {}).get("runs") or []
                if rows:
                    names = "、".join(
                        str(row.get("workflow") or "未命名") for row in rows[:5])
                    return f"万能插已接通，最近工作流：{names}。可以直接让我定义 DAG、并行跑或断点续跑。"
                return "万能插已接通；当前还没有工作流记录。可以直接让我定义 DAG、并行跑或断点续跑。"
            _run_feature("", "正在检查万能插…", _plug_worker)
        elif key == "tentacle":
            def _tentacle_worker():
                result = _gbt_body(_gbt_owner_call("tentacle_status", {}))
                body = result.get("result") if isinstance(result, dict) else {}
                diagnose = (body or {}).get("diagnose") or {}
                coverage = (body or {}).get("coverage") or {}
                ready = bool(diagnose.get("ok"))
                methods = diagnose.get("manifest_methods") or 0
                domains = coverage.get("total_domains") or 0
                if ready:
                    return (
                        f"触手已接通：眼/耳/嘴/手可用，能力清单 {methods} 项，"
                        f"覆盖 {domains} 个邻域。")
                error = diagnose.get("eye_error") or "硬件层未就绪"
                return f"触手已接线，但当前有真实环境缺口：{error}"
            _run_feature("", "正在检查触手…", _tentacle_worker)
        elif key == "eigenflux":
            panel.toggle_social()
            if panel.social_drawer.isVisible():
                social.refresh_async()
        elif key == "agent":
            if codex_ready and codex.available:
                panel.add_message("assistant",
                                  "Codex 内核已就绪，直接把任务说给我就行——"
                                  "读代码、改文件、跑测试、部署排练我都能接着做～")
            else:
                panel.add_message("assistant",
                                  "Codex 内核还没连上，我先用原有大脑陪你聊；"
                                  "本机装好 Codex 后重启面板即可接管编程任务～")
        elif key == "stop":
            if codex.interrupt():
                panel.add_message("assistant", "已请求中断当前任务～")
            else:
                panel.add_message("assistant", "当前没有可中断的 Codex 任务哦～")
        elif key == "model":
            if codex_ready and codex.available:
                names, default = [], ""
                for item in codex.models():
                    if not isinstance(item, dict) or item.get("hidden"):
                        continue
                    mid = item.get("id") or item.get("model") or ""
                    if not mid:
                        continue
                    names.append((item.get("displayName") or mid, mid))
                    if item.get("isDefault"):
                        default = mid
                if names:
                    current = codex.model or default or names[0][1]
                    shown = "、".join(label for label, _ in names[:6])
                    panel.add_message(
                        "assistant",
                        f"当前大脑：真 Codex 内核｜生效模型 {current}｜可选：{shown}")
                else:
                    status = codex.status()
                    ua = status.get("server", {}).get("server", {}).get("userAgent") or "Codex"
                    panel.add_message(
                        "assistant", f"当前大脑：真 Codex 内核（{str(ua)[:60]}）")
            else:
                # 报运行时真值：config.chat.model/base_url 只是配置项，
                # 真正生效的大脑由 chat_client.resolve_brain 的密钥链决定
                # （旧版按 config.api_key 判断，会报出「已接 GLM」而实际是 DeepSeek，
                #  或明明有环境变量密钥却说「离线俏皮模式（无 API key）」）。
                if chat.api_key:
                    panel.add_message(
                        "assistant",
                        f"当前大脑：{chat.provider} / {chat.model}"
                        f"（{chat.base_url or '默认上游'}）")
                else:
                    panel.add_message(
                        "assistant",
                        f"当前大脑：离线俏皮模式（未检测到可用 API key；"
                        f"config 里写的是 {config.get('chat', {}).get('model', '未知')}）")
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
        pet.raise_()          # V8 层叠规则：形象永远在面板之上（站得住看得见）

    # V8 层叠保障：面板每次显示后把形象提前（防 wander 后被压底）
    _orig_show_panel = panel.show_panel

    def _show_panel_keep_pet_on_top():
        _orig_show_panel()
        pet.raise_()

    panel.show_panel = _show_panel_keep_pet_on_top

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

    mind_timer = QTimer(app)
    mind_timer.setInterval(3500)
    mind_timer.timeout.connect(sync_mind)
    mind_timer.start()

    if behavior:
        behavior.start()

    social.start()
    app.aboutToQuit.connect(social.stop)
    app.aboutToQuit.connect(codex.stop)
    logger.info("GBT potato desktop doll started (models=%s)", models)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
