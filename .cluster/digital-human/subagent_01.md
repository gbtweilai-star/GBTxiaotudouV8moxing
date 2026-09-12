# 开源数字人项目调研报告

> 调研角色：数字人技术调研员 · 面向「住在 Windows 桌面的全栈编程 AI 美少女」项目
> 调研日期：2026-09-12 · 本机环境：Windows 11 + Python 3.12
> 数据说明：star 数与更新时间经 GitHub API 于 2026-09-12 核实；许可证均查阅仓库 LICENSE 原文。

---

## 结论先行

**1. 哪条路线能真正实现"在桌面上随意走动、调皮撒娇"？——Live2D（以及 VRM）骨骼动画路线，而不是写实视频流数字人。**

- 写实数字人（DUIX / EchoMimic / HeyGem / LivePortrait 这类）本质是**视频帧生成管线**：矩形视频、持续 GPU/CPU 推理、动作受限于预录素材，且在真人数据上训练，做不出"二次元美少女"的可爱感。把它做成常驻桌面的透明小窗口在技术上可行（透明渲染是存在的），但算力常驻占用高（风扇狂转）、形象风格不匹配、Windows 桌面端没有现成 SDK。
- Live2D/VRM 是**骨骼+网格变形实时渲染**，GPU 占用接近于零，天然支持透明背景、全局置顶、鼠标穿透、点击拖拽物理反馈——这正是"桌宠"的成熟技术栈。

**2. 推荐项目：Open-LLM-VTuber（13.7k star，后端 MIT）**

它是目前唯一一个把"桌宠模式"完整做进产品逻辑的开源项目，与用户三层架构几乎一一对应：

| 用户需求 | Open-LLM-VTuber 对应能力 |
|---|---|
| 形象层（会动） | Live2D 模型 + 口型同步 + 情绪表情映射 + 点击/拖拽触摸反馈 + **桌宠模式（透明背景、全局置顶、鼠标穿透）** |
| 对话层（会聊） | 内置 ASR/TTS/LLM 全链路（Ollama、OpenAI 兼容 API、sherpa-onnx、GPT-SoVITS 等），支持语音打断、AI 主动说话、内心 OS |
| 行动层（会干活） | Python 后端 + Agent 接口 + **MCP 支持**（仓库内含 mcp_servers.json），可自由扩展工具调用 |

来源：https://github.com/Open-LLM-VTuber/Open-LLM-VTuber （README.CN.md 原文核实：支持 Windows/macOS/Linux、网页版+桌面客户端、"透明背景的桌宠模式……点击或拖拽与 AI 伙伴互动"）

**3. 备选与补充**
- 想要 **3D 形象**：走 VRM + three.js（`@pixiv/three-vrm`）自研，或参考 VMagicMirror（Windows 上成熟的 VRM 桌面应用，源码开放）；Warudo 闭源不推荐作为基座。
- 写实数字人项目（Duix-Avatar/HeyGem、EchoMimicV2、LivePortrait）的正确用法是当**离线视频内容生成器**（比如让"她"给你生成一段自我介绍视频），而不是常驻角色。

**4. 一个关键的待确认项**：用户本机是否有 NVIDIA 独立显卡。Open-LLM-VTuber + Live2D 路线**无 GPU 也能跑**（LLM 走云 API、Live2D 渲染不需要 GPU）；而所有写实数字人路线都强依赖 NVIDIA GPU（Duix-Avatar 官方推荐 RTX 4070 + 32GB 内存）。

---

## 逐项目评估表

### ① DUIX 家族（硅基智能 / duixcom）——注意：含三个不同定位的项目

先澄清：任务中提到的 "Duix.Huawei" 仓库经搜索**未找到**（GitHub 无此仓库）。硅基智能（GuijiAI → duixcom）现行开源体系是三件套：**Duix-Mobile**（移动端实时交互 SDK）、**Duix-Avatar**（原 HeyGem，离线视频合成）、**Duix-Reface**（实时换脸）。另有 GuijiAI/duix.ai 汇总仓库（阿里云开发者文章称其提供 Windows/macOS SDK，约 5.3k star）。

#### 1a. Duix-Mobile（移动端实时交互数字人 SDK）

| 维度 | 评估 |
|---|---|
| 开源许可证 | ⚠️ **DUIX.COM Community License**（已查 LICENSE 原文，非 OSI 开源协议）：MAU 超过 1000 需向 duix.com 申请商业许可；再分发需展示 "Powered by Duix.com"。**个人自用无碍，商用有门槛**。来源：https://github.com/duixcom/Duix-Mobile/blob/main/LICENSE |
| 形象风格 | 写实真人（官方提供 Leo/Oliver/Sofia/Lily 四个真人形象包；自定义形象需提供 15 秒~2 分钟真人视频，发邮件定制） |
| 实时性 | ✅ 真实时：端侧渲染、延迟 <120ms（骁龙 8 Gen 2 实测）、流式音频+打断。来源：README |
| 硬件要求 | ✅ 极低：4 核 CPU + 4GB 内存即可流畅运行，不需要 GPU。来源：https://juejin.cn/post/7529427029008810030 |
| Windows 桌面集成 | ❌ **致命伤：只有 iOS/Android SDK（C++），无 Windows 桌面端**。渲染透明支持是给移动 App 嵌入用的（DUIXRenderer/DUIXTextureView）。来源：https://github.com/duixcom/Duix-Mobile |
| Python 接口 | ❌ 无（C++ 原生 SDK，Android/iOS Demo） |
| 社区活跃度 | 8,230 star，2026-09-11 仍在更新，1.2k fork，活跃 |

#### 1b. Duix-Avatar（原 HeyGem，Windows 离线视频合成）

| 维度 | 评估 |
|---|---|
| 开源许可证 | ⚠️ 同为 DUIX.COM Community License。README 写"全球免费商用（10 万用户以上企业或年收入超 1000 万美元需签商业协议）"，但 LICENSE 原文条款是 **MAU>1000 即需申请商业许可**——两者不一致，保守以 LICENSE 为准：个人自用安全，商用需读细条款。来源：https://github.com/duixcom/Duix-Avatar/blob/main/LICENSE |
| 形象风格 | 写实真人（10 秒视频克隆形象+声音，8 语言口型） |
| 实时性 | ❌ **非实时**。README 第 7 节原文："Duix.Avatar's digital human realizes digital human cloning and **non-real-time video synthesis**. If you want a digital human to support interaction, you can visit duix.com"（想实时交互得去买他家云服务）。来源：https://github.com/duixcom/Duix-Avatar |
| 硬件要求 | 🔴 重：需 Docker + 3 个容器镜像（约 70GB 下载）、C 盘 100GB+、D 盘 30GB+、推荐 i5-13400F + 32GB 内存 + RTX 4070、必须有 NVIDIA 显卡。50 系显卡有专门适配方案。 |
| Windows 桌面集成 | ❌ 它是个 Electron 视频制作工具（提交任务→等合成→出 MP4），不是常驻角色。有本地 HTTP API（8383 端口视频合成、18180 端口语音合成），Python 可以调。 |
| Python 接口 | ⚠️ 间接：通过本地 REST API（`http://127.0.0.1:8383/easy/submit` 等）调用，服务本体是 Docker/Node |
| 社区活跃度 | 15,093 star，2.5k fork，2026-09-11 更新，issue 区很活跃（421 open） |

### ② LivePortrait（快手 KlingAIResearch）

| 维度 | 评估 |
|---|---|
| 开源许可证 | ✅ **MIT**（已查 LICENSE 原文），但有一个坑：内置 InsightFace 人脸检测模型**仅限非商用**，商用需自行替换检测模型。来源：https://github.com/KlingAIResearch/LivePortrait/blob/main/LICENSE |
| 形象风格 | 写实真人（照片驱动，也支持猫狗 Animals 模式）；**驱动方式是"视频驱动"不是"音频驱动"**——需要一段驱动视频（表情+头动），不是拿 TTS 音频直接驱动 |
| 实时性 | ⚠️ 分两档：原版官方定位是**离线推理**（inference.py / Gradio app）；社区版 **FasterLivePortrait**（warmshao，MIT，1,184 star）用 TensorRT 做到 RTX 3090 上 30+ FPS 实时，并提供 `python api.py` 服务化接口。来源：https://github.com/warmshao/FasterLivePortrait |
| 硬件要求 | 中等：NVIDIA GPU 实测 GTX 970 4GB 显存即可跑（Reddit 用户实测报告）；官方文档推荐 RTX 3070 8GB 起。有 Windows 一键整合包（cleardusk/LivePortrait-Windows）。Animals 模式仅在 Linux/Windows + NVIDIA GPU 上测试过。 |
| Windows 桌面集成 | ❌ 无桌面窗口形态，输出是视频文件/Gradio 界面；要做桌宠需要自己把推理流嵌进透明窗口，且视频驱动方式与"对话口型"需求错位（还得额外接音频驱动模型） |
| Python 接口 | ✅ 纯 Python 项目（PyTorch），inference.py 可直接 import |
| 社区活跃度 | 19,035 star（本报告所有项目中最高），2026-09-11 更新，已成为主流视频平台的肖像动画方案 |

### ③ EchoMimic / EchoMimicV2（蚂蚁集团 antgroup）

| 维度 | 评估 |
|---|---|
| 开源许可证 | ✅ Apache-2.0（已查 LICENSE 原文，可商用）。来源：https://github.com/antgroup/echomimic_v2 |
| 形象风格 | 写实真人（V2 主打半身动画：参考图+音频+手部姿势序列→高质量动画视频） |
| 实时性 | ❌ **纯离线、且慢**：官方 README 数据——A100 上 120 帧原本要约 7 分钟，优化后约 50 秒（提速 9 倍）。消费级显卡更慢。没有任何实时模式。来源：https://github.com/antgroup/echomimic_v2 |
| 硬件要求 | 🔴 高显存：社区反馈"only works on high-VRAM systems"（Reddit r/StableDiffusion）；扩散模型管线，16GB 显存级起步才舒适 |
| Windows 桌面集成 | ❌ 完全不沾边：学术研究代码，输出视频文件 |
| Python 接口 | ✅ 纯 Python（PyTorch + Diffusers 生态） |
| 社区活跃度 | 4,652 star，2026-09-10 更新（CVPR 2025 论文配套代码，学术驱动） |

### ④ HeyGem（已并入 Duix-Avatar）

| 维度 | 评估 |
|---|---|
| 项目现状 | ⚠️ **HeyGem 是 Duix-Avatar 的曾用名**。duixcom/Duix-Avatar 的 Releases 页原文："The original project name 'HeyGem'..."。原 GuijiAI/HeyGem.ai 仓库已不可搜索到（GitHub 搜索 0 结果），现存 nbttboy/HeyGem.ai、suifeng9203/HeyGem.ai、botoai/HeyGem.ai 等均为镜像/搬运。来源：https://github.com/duixcom/Duix-Avatar/releases |
| 评估结论 | **与 1b Duix-Avatar 完全同源，评估表见 1b**。补充两点：(1) 网传"最低 1080Ti 可跑"来自知乎体验文（https://zhuanlan.zhihu.com/p/29274862393），但官方推荐配置仍是 RTX 4070/32GB 内存；(2) CSDN 有文章指出第三方"批量版 WebUI 二次开发构建"版本未声明授权协议、模型权重来源不明，**用 HeyGem 务必认准 duixcom/Duix-Avatar 官方仓库**（https://blog.csdn.net/weixin_42598278/article/details/157668273） |
| 形象/实时性/许可证/硬件 | 同 Duix-Avatar：写实真人 / 非实时视频合成 / DUIX Community License / Docker+NVIDIA GPU |

### ⑤ OpenAvatarLive / OpenAvatarUI → 实际对应 OpenAvatarChat（阿里通义 HumanAIGC）

| 维度 | 评估 |
|---|---|
| 项目现状澄清 | ⚠️ 搜索中**未找到**名为 "OpenAvatarLive" 或 "OpenAvatarUI" 的现存仓库（GitHub 精确搜索 0 结果）。最接近的实体是 **HumanAIGC-Engineering/OpenAvatarChat**（前端仓库曾名 OpenAvatarChat-WebUI，架构重构前后端分离）。本表按 OpenAvatarChat 评估。来源：https://github.com/HumanAIGC-Engineering/OpenAvatarChat |
| 开源许可证 | 未在本次调研中核实 LICENSE 原文（仓库为阿里通义 HumanAIGC 团队出品，需使用前确认；其同门 lite-avatar 为 MIT 系开源） |
| 形象风格 | 写实真人为主（LiteAvatar、LAM 版本；另有 SoulX-FlashHead 扩散模型实时说话头） |
| 实时性 | ✅ 真实时：模块化 ASR+LLM+TTS 全双工对话，支持手动打断/双工打断；底层 **lite-avatar 模型可在纯 CPU 上 30fps 实时**（HumanAIGC/lite-avatar，473 star："can run in 30fps on only CPU devices without GPU acceleration"）。来源：https://github.com/HumanAIGC/lite-avatar |
| 硬件要求 | 分档：LiteAvatar 版纯 CPU 可跑；扩散模型版（SoulX-FlashHead）需要 GPU |
| Windows 桌面集成 | ⚠️ **是 Web 应用形态**（浏览器对话界面，类似视频通话 UI）。改造成桌面透明置顶窗口需要自己包一层 Electron/PyWebView，属于"可改造但要动手"，项目本身没有桌宠概念 |
| Python 接口 | ✅ Python 后端（模块化设计，可换 ASR/LLM/TTS 组件） |
| 社区活跃度 | 3,754 star，622 fork，2026-09-11 更新，迭代快（架构重构、新数字人接入频繁） |

### ⑥ 其他调研中发现的重要项目

#### ⑥-1. Open-LLM-VTuber（★ 本次调研最强推荐）

| 维度 | 评估 |
|---|---|
| 开源许可证 | ✅ 后端 **MIT**（已查 LICENSE 原文，版权 2025 Yi-Ting Chiu；Live2D 样本模型有单独条款不随 MIT）。⚠️ 前端 Open-LLM-VTuber-Web（Electron）是**自定义许可证：非商业用途免费**（含个人项目、教育），商用需购买授权——个人桌面伴侣场景完全免费。来源：后端 https://github.com/Open-LLM-VTuber/Open-LLM-VTuber/blob/main/LICENSE ；前端 https://github.com/Open-LLM-VTuber/Open-LLM-VTuber-Web/blob/main/LICENSE |
| 形象风格 | 二次元（Live2D 为主；支持导入自定义 Live2D 模型+自定义人设 Prompt+音色克隆）。README.CN.md 明确写着支持"虚拟女友/男友/萌宠"定位 |
| 实时性 | ✅ 真实时全双工：语音打断（无需耳机）、AI 主动说话、TTS 情绪驱动 Live2D 表情、口型同步 |
| 硬件要求 | ✅ 全档位：N 卡/非 N 卡/CPU 都支持，LLM/ASR/TTS 可全部走云 API（2GB 内存 VPS 实测可跑，YouTube 博主验证）；Live2D 渲染本身不吃 GPU |
| Windows 桌面集成 | ✅✅ **完美命中**：官方桌面客户端原生支持**窗口模式 ↔ 桌宠模式自由切换**；桌宠模式 = 透明背景 + 全局置顶 + 鼠标穿透（v1.2.0 加了点击穿透开关）+ 可拖拽到屏幕任意位置 + 点击/拖拽触摸反馈 + 视觉感知（摄像头/屏幕录制/截图）。Windows 直接下载 exe。来源：https://github.com/Open-LLM-VTuber/Open-LLM-VTuber 及 https://open-llm-vtuber.github.io/en/docs/intro/ |
| Python 接口 | ✅✅ Python 后端本体（run_server.py，uv 管理），配置文件切换模块，Agent 接口可继承扩展，支持 MCP（仓库根目录 mcp_servers.json）——**行动层（会干活）可以从这里接代码执行/文件操作等工具** |
| 社区活跃度 | 13,709 star，1.6k fork，2026-09-11 更新；注意 v2.0 全面重写中（v1 只修 bug 不加新功能） |
| 相关生态 | 同作者推荐 LLM-Live2D-Desktop-Assitant（支持电脑控制、语音唤醒、唱歌）：https://github.com/ylxmf2005/LLM-Live2D-Desktop-Assitant |

#### ⑥-2. LiveTalking（lipku）——写实实时数字人的最佳 Python 底座（如果坚持写实路线）

9,479 star，Apache-2.0（已查 LICENSE 原文）。实时交互流式数字人：支持 ernerf/musetalk/wav2lip/Ultralight-Digital-Human 多模型、声音克隆、打断重说、**WebRTC/RTMP/虚拟摄像头输出**、动作编排（不说话时播放自定义视频）。社区实测 RTX 3060 跑 musetalk 可到 60 帧（https://zhuanlan.zhihu.com/p/2058649512651109624）。纯 Python。**输出是视频流（浏览器/虚拟摄像头），做桌面窗口需自己嵌 WebView**。来源：https://github.com/lipku/livetalking

#### ⑥-3. DH_live（kleinlee）——最快 2D 视频数字人

2,146 star，MIT。自称"目前最快的 2D 视频数字人方案，没有之一"；DH_live_mini 不依赖任何 GPU、可在手机实时运行；实测显存占用不到 2GB。含网页推理案例。适合低配机器做写实实时数字人。来源：https://github.com/kleinlee/DH_live 、https://blog.csdn.net/qq_34717531/article/details/141065146

#### ⑥-4. AIAvatar（shibing624）

192 star，Apache-2.0（已查 LICENSE 原文）。wav2lip 实时交互数字人，Python，支持打断/Webrtc/动作编排，GPU 部署。体量小，可作参考实现。来源：https://github.com/shibing624/AIAvatar

#### ⑥-5. VMagicMirror / Warudo（VRM 桌面 3D 路线参考）

- **VMagicMirror**（malaybaku）：Windows 桌面 VRM 角色应用（键盘映射动作、无摄像头也能动），**源码在 GitHub 开放**，License 页面写明可个人+商用（https://malaybaku.github.io/VMagicMirror/en/license/）。它是成品应用不是 SDK，但可作为 VRM 桌面交互的设计参考。来源：https://github.com/malaybaku/VMagicMirror
- **Warudo**：3D VTuber 软件，Steam 发行，**闭源**（个人免费/Pro 付费），只作能力对照，不作基座。来源：https://warudo.app/ 、https://store.steampowered.com/app/2079120/Warudo/

---

## 路线对比（写实数字人 vs Live2D/VRM 动画 vs 混合）

| 对比项 | 路线 A：写实视频流数字人 | 路线 B：Live2D/VRM 骨骼动画 | 路线 C：混合 |
|---|---|---|---|
| 代表项目 | Duix-Mobile / LiveTalking / DH_live / lite-avatar / OpenAvatarChat | **Open-LLM-VTuber** / VMagicMirror / three.js+VRM | B 为主 + A 做离线视频彩蛋 |
| "住在桌面、随意活动" | ⚠️ 勉强可行：透明视频窗口技术上存在（DUIX 渲染器支持透明；LiveTalking 有虚拟摄像头），但 Windows 没有现成桌面 SDK，全要自研窗口层 | ✅ 原生支持：透明背景+置顶+穿透+拖拽+点击物理反馈是桌宠标准配置，Open-LLM-VTuber 开箱即用 | ✅ |
| "调皮撒娇"（动作/表情丰富度） | ❌ 弱：动作=预录视频片段回放（Duix-Mobile 的"动作区间播放"），表情受训练数据限制 | ✅ 强：Live2D 表情系统+物理引擎（头发/衣服/饰品摆动）+程序化动画，"活"感完胜 | ✅ |
| "美少女"形象匹配度 | ❌ 低：模型全部在真人数据上训练，二次元风格效果差；真人形象还涉及肖像权 | ✅ 高：Live2D 美少女模型生态极其成熟（海量免费+付费模型） | ✅ |
| 常驻算力占用 | 🔴 高：即使 CPU 实时方案（lite-avatar）也是持续 30fps 神经网络推理，风扇常转 | 🟢 极低：骨骼插值渲染，几乎不吃 GPU | 🟢 低（写实模块按需启动） |
| 无 NVIDIA GPU 可行性 | ❌ Duix-Avatar/EchoMimic/LivePortrait 全灭；DH_live/lite-avatar 例外可 CPU | ✅ 完全可行（LLM 走 API） | ✅ |
| 口型同步 | ✅ 音频驱动，写实口型好 | ✅ Live2D 口型同步（音素映射） | ✅ |
| Python 生态整合 | ⚠️ 分散：LiveTalking/DH_live 纯 Python 可用；DUIX 无 Python/Windows | ✅ Open-LLM-VTuber 就是 Python 后端 | ✅ |
| 许可证友好度 | DUIX 系=社区许可（MAU 限制）；LiveTalking=Apache；DH_live=MIT | ✅ 后端 MIT / 前端非商业免费 | ⚠️ 混合需各自审查 |
| 工程量（到可用桌宠） | 🔴 大：自研窗口层+推理管线+对话链路 | 🟢 小：Open-LLM-VTuber 下载 exe + 改配置即用，改造点集中在人设/工具层 | 🟡 中 |

**明确结论：**

1. **写实视频流数字人能否做成小窗口在桌面拖动？** 技术上能（透明渲染、虚拟摄像头、WebView 嵌流都有先例），但代价是：常驻视频推理的算力开销、Windows 端无现成 SDK 的自研成本、写实形象与"美少女/未来小孩"气质的根本错配。**这是一条"能走但没必要"的路。**
2. **真正能落地"桌面上活动"的是 Live2D 路线**，且 Open-LLM-VTuber 已把 90% 的路铺完（桌宠模式、语音链路、情绪表情、MCP 工具接口）。项目要做的改造集中在：人设 Prompt、专属 Live2D 模型选型/定制、行动层工具（编程/文件操作）接入。
3. 若用户强烈想要 3D，再评估 VRM 路线（three.js 自研，工程量大于 Live2D）；写实数字人降级为"视频内容生成器"（例如她自我介绍/生日祝福视频用 Duix-Avatar 离线生成）。

---

## 风险与未知项

1. **本机 GPU 未知（阻塞项）**：用户未说明是否有 NVIDIA 独立显卡及显存大小。Live2D 路线不依赖 GPU（LLM/ASR/TTS 可全部云 API 化），但若未来要跑本地 LLM 或写实视频模块，GPU 是硬门槛。建议下一步先跑 `nvidia-smi` 确认。
2. **Open-LLM-VTuber 双许可结构**：后端 MIT 可自由改造；**前端 Electron 客户端是自定义非商业许可证**——个人使用免费，若日后想商用（比如分发给她人收费）需要购买前端授权或自研前端替换。当前"自住桌面"场景无风险。
3. **Open-LLM-VTuber v2.0 重写中**：官方公告 v1 不再接受新功能（只修 bug），v2.0 是全面重写、API 可能变化。建议锁定 v1 稳定版使用，关注 v2 进展再决定是否迁移。
4. **Live2D 模型版权**：项目自带的 Live2D 官方样本模型有单独使用条款（Live2D Inc.，商用需额外授权）；若想换模型，nizima 等平台商用模型需购买。自用无碍。
5. **DUIX 系许可证的两面性**：README 宣传"全球免费商用（10 万用户/1000 万美元营收门槛）"与 LICENSE 原文"MAU>1000 需申请商业许可"**不一致**，以 LICENSE 文本为准应保守看待；个人自用不受影响。
6. **"OpenAvatarLive/OpenAvatarUI" 名称未找到现存仓库**：任务指定的这个项目名在 GitHub 无精确匹配，已用最接近的 OpenAvatarChat（阿里通义系）替代评估；若用户手中资料另有出处（如私有 fork 或已改名项目），需补充确认。
7. **LivePortrait 商用暗坑**：MIT 代码 + InsightFace 非商用检测模型的组合，商用需替换检测模型（社区有现成替换方案，但要动手）。
8. **口型质量的主观性**：DUIX 宣传"100% 口型匹配"来自其商业版 API，开源本地版 README 自述口型效果为 "Usable effect"（可用级），商业版才是 "Stunning"——对开源版效果要有合理预期。
9. **Windows 透明窗口技术细节**：若走自研路线（VRM/three.js 或写实流嵌入），Electron/PyQt 的透明+置顶+穿透组合在 Windows 11 上有已知坑（如穿透与拖拽冲突、DPI 缩放），Open-LLM-VTuber 前端已踩过这些坑，这也是推荐直接复用它的理由之一。

---

## 附：核心来源索引

- Duix-Mobile：https://github.com/duixcom/Duix-Mobile （README/LICENSE 已核）
- Duix-Avatar（原 HeyGem）：https://github.com/duixcom/Duix-Avatar （README/LICENSE/Releases 已核）
- LivePortrait：https://github.com/KlingAIResearch/LivePortrait （LICENSE 已核）；实时版 https://github.com/warmshao/FasterLivePortrait
- EchoMimicV2：https://github.com/antgroup/echomimic_v2 （LICENSE 已核）
- OpenAvatarChat：https://github.com/HumanAIGC-Engineering/OpenAvatarChat ；lite-avatar：https://github.com/HumanAIGC/lite-avatar
- Open-LLM-VTuber：https://github.com/Open-LLM-VTuber/Open-LLM-VTuber （README.CN/LICENSE 已核）；文档 https://open-llm-vtuber.github.io/en/docs/intro/
- LiveTalking：https://github.com/lipku/livetalking （LICENSE 已核）
- DH_live：https://github.com/kleinlee/DH_live
- VMagicMirror：https://malaybaku.github.io/VMagicMirror/en/
- Warudo：https://warudo.app/

> 调研员：subagent_01（数字人开源项目调研）· 2026-09-12
