# 桌宠形象层技术调研报告

> 调研对象：住在 Windows 桌面的美少女 AI 桌宠「形象层」技术栈
> 调研范围：Live2D 渲染、VTube Studio API、VRM 路线、开源桌宠先例、Windows 窗口魔法、行为引擎
> 调研日期：2026-09-12

---

## 结论先行（推荐技术栈组合）

**推荐组合：PySide6（或 PyQt6）+ live2d-py（C 扩展，Cubism 5 内核）+ QOpenGLWidget 自绘 + ctypes 调用 Win32 DWM 层。**

一句话回答三个关键判断：

1. **PyQt + live2d-py 能否撑起"会呼吸会眨眼会撒娇会走动的美少女"？——能，而且这是目前最轻、最契合的一条路。** live2d-py 是 Python C Extension，底层是官方 Cubism Native SDK 5_r4，直接暴露 `SetAutoBreath`（呼吸）、`SetAutoBlink`（眨眼）、物理摆动（`UpdatePhysics`）、`StartRandomMotion`（随机动作/撒娇）、精确点击检测（`HitTest`/`HitPart`）等 API。渲染通过 OpenGL，官方明确支持 PyQt5 / PySide2 / PySide6，有 `main_pyqt6_canvas.py`、`main_pyside6.py` 等现成样例。模型走 Cubism 3.0+（`.moc3`/`.model3.json`），支持物理/表情/动作/口型同步。GPU 加速，60fps 无压力。

2. **全息面板：PyQt/QML 的 translucency + DWM Acrylic 能不能做出电影级悬空 HUD？——能，但要用 Win32 API 而不是纯 Qt 属性。** Qt 的 `WA_TranslucentBackground` + `FramelessWindowHint` 能做出"只有内容、没有背景"的悬空效果；再叠加 Windows 10/11 的 DWM Acrylic/Mica（通过 ctypes 调 `DwmSetWindowAttribute`，或直接用 `PyQt-Fluent-Widgets`/`QFluentWidgets` 内置的 mica/acrylic 支持），就能得到毛玻璃半透明模糊。全息 HUD 的关键是"透明+边缘辉光+轻微模糊"，这套组合完全够用。

3. **有没有比 PyQt 更合适的轻量方案？——对"美少女 Live2D 桌宠"这个具体需求，没有。** Electron 内存 80–250MB 起步（Open-LLM-VTuber 就是 Electron 前端，重）；Tauri 比 Electron 轻但 Rust 门槛高；Godot 4 做桌宠可行但 Live2D 生态是弱项（要自己接 Cubism）；纯 GLFW/Pygame 能渲染但缺 UI 能力。PyQt/PySide 内存几十 MB 级，且 Python 与"对话层/行动层"天然同栈，是最优解。

### 推荐技术栈明细

| 层次 | 选型 | 理由 |
|------|------|------|
| 窗口/UI 骨架 | PySide6（LGPL，商用友好） | 比 PyQt 授权干净，API 同源，live2d-py 官方支持 |
| Live2D 渲染 | live2d-py（`live2d.v3`） | C 扩展 + 官方 Cubism Core 5_r4，性能≈原生 |
| OpenGL 载体 | QOpenGLWidget | 内嵌进 PySide6 窗口，可叠加 QWidget 做 UI |
| 透明/置顶/点击穿透 | Win32 API（ctypes）：`WS_EX_LAYERED` + `WS_EX_TRANSPARENT` + `SetWindowPos(HWND_TOPMOST)` | 原生能力，绕过 Qt 在 macOS 上的限制 |
| 半透明模糊面板 | `DwmSetWindowAttribute`（Acrylic/Mica）+ Qt `WA_TranslucentBackground` | Win10/11 原生毛玻璃，PyQt-Fluent-Widgets 有封装 |
| 行为编排 | 分层 FSM（状态机）+ 随机加权调度器 | 见「行为编排方案」 |

---

## 逐项调研明细

### 1. live2d-py（重点，强烈推荐）

**项目**：https://github.com/EasyLive2D/live2d-py | PyPI: https://pypi.org/project/live2d-py/

**核心结论：这是本项目形象层的最优渲染方案。**

- **版本支持**：
  - `live2d.v3`：**Cubism 3.0 及以后全部版本**（含 Cubism 4、Cubism 5），通过 Python C Extension 封装，底层是官方 Cubism Core（当前 **CsmSDK 5_r4**）。
  - `live2d.v2` / `live2d.v2cpp`：Cubism 2.1 及更早（旧模型），纯 Python / C++ 移植。
  - 关键：**Cubism 5 模型完全支持**（README 明确 CsmSDK 5_r4），所以现在从官网/第三方下载的任何新模型都能用。

- **功能清单（官方 README 原文）**：
  - Model Loading（Cubism 2.1 和 3.0+）
  - Eye tracking（眼睛追踪，看向鼠标/目标）
  - Click interaction（点击交互）
  - Motion playback callback（动作回调）
  - Lip-sync synchronization（口型同步）
  - Parameter control for model parts（参数控制）
  - Opacity control for parts（部件透明度）
  - **Precise part-level click detection（部件级精确点击检测）**——这是桌宠"点哪撒娇"的关键

- **呼吸/眨眼/物理**：从源码 `lapp_model.py` 确认存在以下高层 API：
  - `SetAutoBreathEnable(bool)` — 自动呼吸
  - `SetAutoBlinkEnable(bool)` — 自动眨眼
  - `StartMotion(group, no, priority)` / `StartRandomMotion(group)` — 播放动作/随机动作（撒娇、调皮等）
  - `SetExpression(expressionId)` / `SetRandomExpression()` — 表情切换
  - `Drag(x, y)` — 拖拽跟随
  - `HitTest(hitAreaName, x, y)` / `HitPart(x, y)` — 点击区域判定
  - 底层 `UpdatePhysics` / `UpdatePose` / `UpdateBreath` / `UpdateBlink` 在 `Model.Update(dt)` 里统一驱动（物理摆动头发裙子由 Cubism 模型自带的 physics 配置实现，渲染器自动计算）

- **Qt 集成**：官方 README 明说"理论上兼容所有能用 OpenGL 渲染的 UI 库"，列出的 PyQt5 / PySide2 / PySide6 均有样例：
  - `examples/main_pyqt5_canvas_opacity.py`
  - `examples/main_pyqt5_multi_win.py`
  - `examples/main_pyqt6_canvas.py`
  - `examples/main_pyside6.py`
  - `examples/main_pyside6_moderngl_qt.py`（还支持 ModernGL）

- **性能**：`live2d.v3` 是 C 扩展直接调官方 Cubism Native Core + OpenGL，性能接近原生 C++ 实现，**60fps 轻松**。仓库还展示了一屏渲染 4 个模型的 demo（`main_glfw_four_model.py`）。相比之下，走 Web 引擎（如 pixi-live2d-display + Electron）会有 JS 桥接和 Chromium 开销。内存占用主要是 Python 解释器 + Qt + OpenGL 纹理，**远低于 Electron 方案**（PyQt 常驻约 30–80MB，Electron 轻量应用 80–250MB）。

- **许可证**：MIT License（Copyright 2024 Arkueid）。**但注意**：仓库本身不含 Live2D Cubism Core 和 Framework（受 Live2D 许可限制），从源码编译时需自行从官网下载。PyPI 的预编译 wheel 已内置，直接 `pip install live2d-py` 即可用。**商用注意**：Live2D Cubism SDK 的发布许可（Publication License）对中小规模企业/个人免费，但中大型企业（年销售额超 1000 万日元）需签署授权协议。

- **免费模型资源授权**：
  - Live2D 官方示例模型（**Hiyori / Haru / Haru receptionist / Niziiro Mao** 等）：受《Live2D Free Material License Agreement》和《Terms of Use for Live2D Cubism Sample Data》约束。**个人/小规模开发、学习测试可免费使用**；中大型企业商用需额外授权。https://www.live2d.com/en/learn/sample/
  - Open-LLM-VTuber 项目里有专门的 `LICENSE-Live2D.md` 说明同样的约束（它内置了 Live2D 示例模型，非 MIT 覆盖）。

### 2. VTube Studio API（备选，不推荐作为主方案）

**项目**：https://github.com/DenchiSoft/VTubeStudio | API 文档在仓库 README / Wiki

**结论：可行但架构重、耦合深，适合"借用 VTS 当渲染器"的场景，不适合自建轻量桌宠。**

- **API 能力（WebSocket，默认 `ws://localhost:8001`）**：
  - 控制模型：`ModelLoadRequest`（加载/卸载模型）、`MoveModelRequest`（位置/旋转/缩放，可每帧发送实现完全接管移动）、`HotkeyTriggerRequest`（触发动画/表情/换模型/移动）、`ExpressionActivationRequest`（激活表情）、`InjectParameterDataRequest`（注入任意 Live2D 参数值，含 `mode: set/add`）
  - 读取状态：`CurrentModelRequest`（当前模型及位置）、`StatisticsRequest`（含 framerate）、`InputParameterListRequest` / `Live2DParameterListRequest`（参数列表）
  - **物理控制**：`GetCurrentModelPhysicsRequest` / `SetCurrentModelPhysicsRequest`（可动态改物理强度、风力、每组 multiplier）——这意味着"头发裙子物理摆动"在 VTS 里是现成的，还能通过 API 实时调节
  - 事件订阅：模型加载、点击、追踪丢失/恢复等
  - 认证：首次需 `AuthenticationTokenRequest` 弹窗授权，之后用 token 复用

- **画面捕获（Spout2）**：VTube Studio 支持 **Spout2**（仅 Windows），激活后在 Camera 设置里开启，能把模型渲染画面通过 GPU 共享纹理发给其它程序（OBS 插件 `obs-spout2-plugin` 是标准用法）。Python 侧有 `SpoutGL`（PyPI）和 `pyspout`（Off-World-Live）可接收纹理，再在自建 PyQt 窗口里显示。**这是"VTS 渲染 + 自建窗口"的可行通路**。

- **为什么不做主方案**：
  - VTS 是独立游戏/应用（Steam），桌宠必须依赖它常驻运行，无法打包成独立轻量应用。
  - 通过 Spout 收画面 = 两个进程 + GPU 纹理中转，多一层开销和延迟；点击交互要自己用 API 的点击事件反向映射坐标，链路长。
  - 本质是"外包渲染"，丧失了对窗口/内存的精细控制，违背"轻量常驻"目标。
  - **价值**：如果用户已经有自己的 Live2D 模型、VTS 配置、或者想用 iPhone 面捕，VTS API + Spout 是快速验证"会动的美少女"的捷径；以及 VTS 的 API 文档是理解 Live2D 参数/物理/表情体系的最佳参考资料。

### 3. VRM 路线（three.js + @pixiv/three-vrm + pywebview）

**结论：3D 美少女的备选方案，视觉上限高，但性能/内存/开发成本都高于 Live2D，不推荐作为首选。**

- **技术**：`@pixiv/three-vrm`（v3.x，支持 WebGPURenderer + MToon 材质）是渲染 VRM 模型的事实标准。pywebview 支持透明无边框窗口（https://pywebview.flowrl.com/examples/transparent），可以包一个 WebView 跑 three.js 渲染 VRM。
- **免费 VRM 模型资源**：
  - VRoid Hub（https://hub.vroid.com/）有海量免费 VRM 模型，但**每个模型的授权由作者单独设定**（允许/禁止商用、是否可二次分发、是否需署名），下载前必须逐模型核对 license 字段。
  - VRoid Studio 自己制作导出的模型：官方明确**任何个人或企业可商用出售**（https://vroid.com/en/studio/guidelines），这是最干净的来源。
- **对比 Live2D 的劣势**：
  - VRM 是 3D 网格 + 骨骼 + MToon 材质，渲染重（需要 WebGL/WebGPU + WebView），内存和 CPU 占用显著高于 2D Live2D。
  - pywebview 底层（Windows 用 Edge WebView2 / 或 Chromium）本质又回到了"内嵌浏览器"，常驻内存 ≈ Electron 级别，与"轻量"矛盾。
  - "半透明全息"3D 面板实现比 2D 复杂。
- **适用场景**：用户明确想要 3D 风格角色（而非 2D Live2D 纸片人）时采用；或后期作为"3D 形态切换"的扩展形态。

### 4. 已有开源桌宠项目（重要先例，强烈建议借鉴）

GitHub 搜索 `desktop-pet live2d` 按 star 排序，关键项目：

- **Open-LLM-VTuber**（13.7k stars，最成熟先例）：https://github.com/Open-LLM-VTuber/Open-LLM-VTuber
  - 架构：Python 后端（LLM/ASR/TTS/Agent 模块化）+ **Electron 前端**渲染 Live2D。
  - **桌面宠物模式**明确实现了本项目全部窗口需求：透明背景、全局置顶、鼠标点击穿透、可拖拽到屏幕任意位置、窗口模式/宠物模式自由切换、上下文共享。
  - 内置 Live2D 示例模型（带 LICENSE-Live2D.md 授权说明）。
  - **可借鉴**：窗口模式的实现思路、情感→表情映射、点击/拖拽交互；**教训**：Electron 前端导致体积大、内存高（这恰是我们改用 live2d-py 要规避的）。
- **DD-MASTERT/AI-Girlfriend-Desktop-Pet**（233 stars）：Python 实现，Live2D 2.0/3.0 模型 + GPT-SoVITS/edge-tts 语音 + 国产大模型 API。纯 Python 路线，与推荐栈同源，值得看它怎么组织 Live2D + TTS + LLM。
- **kirbystudy/chatgpt-desktopPet**（90 stars）：Electron + Live2D + GPT，最早的桌宠 + LLM 组合之一。
- **ai-zen/live2d-copilot**（TypeScript + Electron + Steam）：AI 桌宠，Live2D 100% 完成度，含 Workshop（模型工坊）。
- **qiyueblues-design/zhuomianling**（TypeScript，桌面精灵）："Open-source customizable Live2D desktop pet framework"，可定制框架。
- **cyanfish-x/dsh-live2d-pets**（TypeScript）：DeepSeek Harness 的 Live2D 桌宠插件，内置"宽松许可预设模型"——说明有人专门解决了模型授权问题。
- **x380kkm/Live2DPet**（JS + VOICEVOX TTS）：AI Live2D 桌宠。
- **DasterProkio/awesome-ai-companion**（667 stars）：AI 伴侣/桌宠项目大全（人机恋开源项目合集），是找更多先例的入口。

**共同规律**：成熟桌宠几乎都选 Live2D（而非 VRM），交互模式（透明+置顶+穿透+拖拽）高度趋同；分歧点主要在"渲染层用 Electron 还是原生"，而我们选 live2d-py 走原生。

### 5. Windows 窗口魔法（形象层的地基）

- **透明无边框窗口**：Qt 侧 `Qt.FramelessWindowHint` + `Qt.WA_TranslucentBackground`（顶层 QWidget 设置该属性后背景透明，只有内容可见）。这是桌宠"悬空"的基础。
- **置顶**：`SetWindowPos(hwnd, HWND_TOPMOST, ...)` 通过 ctypes 调 user32.dll；或 Qt 的 `WindowStaysOnTopHint`（但 ctypes 更可控，且能配 SWP_NOMOVE/NOSIZE 避免抖动）。
- **点击穿透（不挡操作）**：`WS_EX_LAYERED` + `WS_EX_TRANSPARENT` 扩展样式，通过 `GetWindowLong`/`SetWindowLong` 设置。**注意**：`WS_EX_TRANSPARENT` 是"整窗穿透"，所以桌宠的标准做法是——默认让角色区域可点（接收点击、触发反应），只有在"待机不打扰"模式才开穿透；更精细的"只穿透透明像素、角色身体可点"需要用 region 裁剪或逐像素命中（live2d-py 的 `HitTest` 能判断点击是否落在角色上，配合动态切换穿透标志即可实现"点空白穿过、点角色有反应"）。
  - 参考：Electron 的 `setIgnoreMouseEvents` 也是整窗穿透（electron issue #23042 印证了这套模式的普遍性）。
- **DWM Acrylic / Mica 半透明模糊**：Windows 10 的 Acrylic（`SetWindowCompositionAttribute`）、Windows 11 的 Mica/Acrylic backdrop（`DwmSetWindowAttribute` + `DWMWA_SYSTEMBACKDROP_TYPE` / `DWMWA_USE_IMMERSIVE_DARK_MODE`），都可通过 ctypes 在 PyQt 窗口上调用。**现成封装**：`PyQt-Fluent-Widgets` / `QFluentWidgets` 的 `FluentWindow` 组件在 Win11 默认开 Mica，`setMicaEffectEnabled(True)` 一行搞定（https://qfluentwidgets.com/pages/components/fluentwindow/）；纯毛玻璃可用 `QtWin.ExtendFrameIntoClientArea` 或第三方 `QTWin11`。
- **多显示器支持**：Qt 的 `QScreen` API 枚举所有屏幕 + `QGuiApplication.screens()`，窗口移动用绝对坐标，天然支持多屏。桌宠"走动"时把逻辑坐标映射到 `QScreen.availableGeometry()` 即可，Win32 层无需额外处理。唯一注意：DPI 缩放（`Qt.AA_EnableHighDpiScaling`）要在 `QApplication` 创建前开启，避免高分屏坐标错位。
- **内存/常驻**：Qt + Python 解释器空载约 30–80MB，Live2D 纹理视模型分辨率追加（典型 512–1024 纹理，几十 MB 内）。相比 Electron 的 80–250MB（HN/Medium 实测 Qt/QML 内存约为 Electron 的 1/3，来源 https://pkoretic.medium.com/quick-look-electron-vs-qt-qml-app-memory-usage-e8769008534f），符合"轻量常驻"目标。

### 6. 行为引擎（闲逛/撒娇/调皮的动画编排）

- **结论：用「分层有限状态机（FSM）+ 随机加权调度器」，不要上行为树（BT）。**

- **FSM vs BT 的取舍**：
  - 桌宠行为是**强模式化、状态明确**的（待机 / 呼吸眨眼 / 走动 / 撒娇 / 被点击 / 对话中 / 睡眠），状态间转换清晰，FSM 直观、易调试、开销小。
  - 行为树适合"复杂决策、目标规划、条件组合多的 AI"（游戏敌人 AI、机器人），桌宠不需要这种复杂度；引入 BT 反而增加认知负担和运行开销。
  - 共识（Unity 论坛、Opsive、gamedev 社区、arXiv 2405.16137）：**FSM 擅长"当前处于什么模式 + 模式切换"，BT 擅长"决策树式规划"**。桌宠场景选 FSM。

- **推荐组织方式**：
  - **顶层状态**：`IDLE`（待机，呼吸+眨眼+随机小动作）→ `WANDER`（走动/闲逛）→ `INTERACT`（被点击/拖拽的即时反应）→ `TALK`（对话中，口型同步+情绪表情）→ `SLEEP`（长时间无操作）。
  - **随机加权调度器**：在 IDLE 态内，用带权重的随机抽签决定下一个微动作（眨眼频率、呼吸节奏、小动作如"歪头/挥手/眨眼卖萌"），权重可随时间/情绪/用户互动历史调整（例如越久没互动越容易"主动撒娇"吸引注意）。
  - **Live2D motion 列表组织**：利用 live2d-py 的 `GetMotions()` 拿到 `{group: [{File, Sound}...]}` 结构，按语义分组——`idle` 组（小动作）、`interact` 组（点击反应）、`talk` 组（说话姿态）、`emoji` 组（情绪动作）。`StartRandomMotion(group)` 直接在组内随机播放，天然契合随机调度。表情用 `SetExpression` 由上层"情绪"驱动，口型用参数注入由 TTS 音频驱动。
  - **"走动"**：Live2D 本体是 2D 立绘，不会真的迈步走；"在桌面上走动"= **窗口本身在屏幕上移动**（SetWindowPos 逐帧移动窗口坐标 + 模型内部播放"走路"摆动 motion + 可选 `Drag`/`Rotate` 制造移动惯性）。这是所有 2D 桌宠的通用做法。

---

## 全息面板实现方案

目标：电影里那种"悬空、半透明、带轻微辉光和模糊"的 HUD 对话面板。

**分层实现**：

1. **面板窗口**：独立于角色窗口的第二个 PySide6 窗口（或同一窗口内嵌 QWidget），`FramelessWindowHint` + `WA_TranslucentBackground`，背景完全透明。

2. **半透明模糊底**：调用 Win32 `DwmSetWindowAttribute`（Windows 11 用 `DWMWA_SYSTEMBACKDROP_TYPE = 4` 即 Mica，或 Acrylic=3；Windows 10 用 `SetWindowCompositionAttribute` + `ACCENT_ENABLE_ACRYLICBLURBEHIND`）。效果 = 面板背后桌面内容被实时模糊 + 叠加半透明色。用 `PyQt-Fluent-Widgets` 的 `AcrylicWindow`/`FluentWindow` 可少写 ctypes 代码。

3. **辉光/描边/扫描线（电影感的关键）**：
   - 角色与面板的**发光描边**：Qt 的 `QGraphicsDropShadowEffect`（模糊半径调大、颜色取主题色，如青色/紫色）。
   - **扫描线/网格底纹**：用 `QLinearGradient` + 半透明网格贴图叠加，营造 HUD 科技感。
   - **文字发光**：`QLabel` 加 `QGraphicsDropShadowEffect` 或用 QSS 的 `outline` + 发光阴影。
   - **淡入淡出**：`QPropertyAnimation` 做 opacity 动画（面板弹出/收起、角色反应时闪烁）。

4. **性能注意**：`QGraphicsDropShadowEffect` 和 DWM 模糊都有 GPU 成本，但对话面板只在对话时显示、尺寸有限，60fps 不受影响；角色窗口本身不加模糊（保持透明），只有面板加，避免常驻开销。

**结论**：PyQt/QML 的 translucency + DWM Acrylic 完全能做出接近电影级的悬空 HUD 感，难点不在技术而在视觉设计（配色、辉光、动效节奏）。

---

## 行为编排方案

（详见上文第 6 条，此处为落地建议汇总）

- **引擎**：分层 FSM（顶层 5–6 个状态）+ 每个状态内随机加权微动作调度器。
- **Live2D motion 分组约定**（模型制作/导入时统一）：
  - `idle`：待机小动作（眨眼、歪头、捋头发）
  - `wander`：走动/闲逛时的身体摆动
  - `interact`：点击、拖拽的反应（惊讶、开心、害羞）
  - `talk`：说话姿态
  - `sleep`：打盹/入睡
- **情绪驱动**：对话层的情绪信号（开心/生气/害羞/无聊）→ 映射到 `SetExpression` + 选择对应 motion 组。
- **口型同步**：TTS 音频 → live2d-py 的 lipsync 参数注入。
- **走动**：窗口坐标插值移动 + `wander` motion + 到达边界转向（用 `QScreen.availableGeometry()` 判界）。

---

## 风险与未知项

1. **Live2D 授权（最大合规风险）**：
   - Cubism SDK 发布许可：个人/中小规模免费，**中大型企业（年销售额 ≥1000 万日元）商用需签协议**。项目若未来商业化需评估。
   - 官方示例模型（Hiyori/Haru）中大型企业商用受限；长期需自备模型或使用明确宽松授权的第三方模型（如 dsh-live2d-pets 内置的"宽松许可预设"、雅萌工作室等）。
   - live2d-py 的 PyPI wheel 内置了 Cubism Core，虽 MIT 开源但 Core 部分仍需遵守 Live2D 许可——**商用发布前必须逐条核对**。

2. **点击穿透的粒度**：`WS_EX_TRANSPARENT` 是整窗级穿透，无法原生做到"只穿透透明像素、角色身体可点"。方案是动态切换穿透标志 + live2d-py `HitTest` 判定，但"逐像素穿透"仍需验证是否满足"角色不规则轮廓可点"的体验（可能需要 region 裁剪或额外命中蒙版）。

3. **DWM Acrylic 的系统差异**：Acrylic 在 Windows 10/11 表现不同，Mica 是 Win11 专属；老系统（Win10 早期版本、无 GPU 时）模糊可能退化。需做版本降级兜底（模糊失效→纯半透明色块）。

4. **live2d-py 的成熟度**：项目较新、社区规模小（相比 Web 版 pixi-live2d-display 生态），文档以中文为主，Wiki 开放编辑。深度定制（如自定义 shader、高级拖拽物理）可能需要读源码或回退到直接调 Cubism Native SDK。**建议立项时先跑通官方 PySide6 样例验证兼容性。**

5. **60fps 与常驻内存的实测**：live2d-py 官方未给出权威 benchmark 数字（只有"一屏 4 模型"的 demo），60fps 是理论推断（C 扩展 + 官方 Core）。**需在目标机器上实测**：模型分辨率、眨眼/物理更新频率、多显示器 DPI 下的实际帧率与内存占用。

6. **音画同步**：TTS 流式播放与 Live2D 口型同步的延迟控制（live2d-py 提供 lipsync 接口，但流式音频的"前瞻口型"需要自己缓冲对齐），是体验打磨的隐藏难点。

7. **"走动"的真实感**：2D Live2D 只能靠"窗口移动 + 摆动 motion"模拟走路，无法像 3D 那样有真实步态。若用户对"走路"有较高真实感要求，可能需要 VRM 3D 路线兜底。

8. **未充分验证项**：
   - pyvts/coovts（Python VTS 客户端库）的成熟度——备选方案 VTS 路线若要落地需评估。
   - `SpoutGL`/`pyspout` 的 Python 接收端在 PySide6 窗口内的集成复杂度（VTS 备选路线的关键环节）。
   - Open-LLM-VTuber v2.0 正在重写，其 Electron 前端是否会迁移到更轻的方案值得持续关注（可能给出新的参考实现）。
