# 对话与行动链路调研报告

> 调研员：subagent_03（AI 应用链路）· 调研时间：2026-09-12
> 范围：对话层（会聊）+ 行动层（会干活）技术选型。形象层另有人负责。
> 本机实测事实：Windows SAPI TTS 已出声；**本机 GPU 为 AMD Radeon RX 6500M（4GB）+ AMD 核显，无 NVIDIA CUDA**（WMI 查询确认），直接影响 TTS/ASR 本地方案选型。

---

## 一、结论先行（推荐组合）

| 层 | 推荐方案 | 理由一句话 |
|---|---|---|
| **大脑模型** | 智谱 **GLM-4.7-Flash**（免费 API，OpenAI 兼容）为主，**GLM-5.3-Flash**（新一代，低价/活动免费）为升级项 | 国产最全免费模型家族，OpenAI 兼容格式 + function calling，注册即用零成本 |
| **语音输入 ASR** | **FunASR paraformer-zh**（本地离线，中文最强）+ 交互用**按住说话**起步，唤醒词后补 openWakeWord | 中文识别明显优于 Whisper（Whisper 中文 CER 约 20%），CPU 可实时，带标点/VAD |
| **TTS** | 梯度：**SAPI（已有）→ edge-tts（免费，音质大幅提升）→ GLM-TTS / 豆包 TTS（付费情感）**；GPT-SoVITS 本机不可行（无 N 卡） | edge-tts 目前仍免费可用但有 403 风险，需保留 SAPI 兜底 |
| **对话记忆** | **JSONL 会话日志 + 人设/persona 文件 + 摘要式长期记忆**（仿 OpenClaw 四层记忆堆栈），SQLite 存结构化事实（提醒/偏好），向量库暂不上 | 单机单用户规模下，向量检索收益低、复杂度高 |
| **行动层** | GLM function calling（OpenAI tools 格式）+ 本地工具集（白名单+危险操作确认） | GLM tools 支持成熟，本地工具简单可控 |
| **OpenClaw 集成** | 数字人轻客户端直连 GLM 闲聊；"干活"任务经 **OpenClaw 网关（WebSocket RPC，端口 18789）** 或 CLI 转发 | 网关有完整 RPC 协议 + OpenAI 兼容 HTTP 端点（默认关闭需开启）+ cron 持久化 |

**总成本：0 元起步**（GLM 免费 API + FunASR 本地 + edge-tts/SAPI + JSONL），全链路可跑通后再按需付费升级音色。

---

## 二、逐项调研明细

### 2.1 GLM API 接入（大脑）

**免费额度现状（2026 年）**：
- glm-4-flash 是智谱第一个免费 API（128K 上下文，2024 年推出），但**已不是最优选择**——智谱免费家族已迭代到第 7 个免费模型：
  - **GLM-4.5-Flash**：官方文档明确"完全免费开放使用"，支持 128K 上下文、推理、代码生成、多工具协同（docs.bigmodel.cn/cn/guide/models/free/glm-4.5-flash）
  - **GLM-4.7-Flash**（2026-01-20 发布并开源）：30B 总参数/3B 激活的混合思考模型，BigModel.cn 上**免费调用**，性能超 gpt-oss-20b（zhipuai.cn/zh/news/148）
  - **GLM-5.3-Flash**（2026-08-26 发布并开源）：320B-A18B 原生多模态、1M 上下文，国际端 $0.15/$0.50 每百万 tokens；国区 Coding Plan 套餐内可用，另有"夜间畅用活动"（2026-09-03 起，docs.bigmodel.cn/cn/coding-plan/notice/event-glm-5.3-flash）免费时段使用
- ⚠️ 注意官方迁移公告：调用历史模型 GLM-5-Turbo、GLM-4.7 会**自动切换至 GLM-5.3-Flash**（docs.bigmodel.cn/cn/coding-plan/overview），代码里模型名要写活、可配置

**API 格式**：OpenAI 兼容。端点 `https://open.bigmodel.cn/api/paas/v4/chat/completions`，标准 messages/tools/stream 字段，OpenAI SDK 换 base_url 即可用。

**Function calling / tools**：官方支持（docs.bigmodel.cn/cn/guide/capabilities/function-calling），GLM-4.5 起工具调用稳定性较好，GLM-5.x/4.7 系列多步工具编排更强（社区实测 GLM-4.5/4.6 function calling 有完全指南，Novita 等第三方也有评测）。

**Streaming**：支持 SSE 流式输出。

**并发限制**：按"在途请求并发数"限流（docs.bigmodel.cn/cn/guide/models/text/glm-4 用户并发权益）；免费档新用户约 **2 个并发**、老用户并发不变（智谱官方口径，baai 报道）。对单用户桌宠（一问一答 + 偶发工具调用）完全够用。

**备选对比**：

| 模型 | 价格（每百万 tokens） | 备注 |
|---|---|---|
| GLM-4.7-Flash | **免费** | 推荐主力 |
| GLM-5.3-Flash | 国区套餐内 / 国际 $0.15 输入、$0.50 输出 | 多模态+1M 上下文，升级项 |
| GLM-4.6 | 国际 $0.6 输入 / $2.2 输出（缓存命中 $0.11） | 旗舰级，按量付费 |
| DeepSeek V4-Flash | 缓存命中输入 0.02 元（空闲）/ 0.04 元（高峰）；未命中 1 元（空闲）/ 2 元（高峰） | 2026-08-13 调价后引入峰谷定价 |
| DeepSeek V4 Pro | 高峰输出 **27 元**（原 6 元，涨幅 350%） | 涨价潮后性价比下降明显（新浪/钜亨等多家报道） |

结论：**DeepSeek 2026 年 8 月大幅涨价后，智谱免费 Flash 系列对个人桌宠的性价比优势进一步拉大**。若某天需要更强推理，再按量买 GLM-4.6/5.3。另有 GLM Coding Plan 订阅（国区 Lite/Pro/Max = 49/149/469 元/月，2026 年 2 月调价后 Lite 80 prompts/5h），如果她要重度写代码管项目可考虑，日常对话不需要。

### 2.2 语音输入 ASR

**本地离线方案对比**：

| 方案 | 中文质量 | 速度 | 大小 | 特点 |
|---|---|---|---|---|
| **FunASR paraformer-zh** | ★★★★★（工业级，6 万小时中文语料训练，CER 远优于 Whisper） | 非自回归架构，GPU 上 120x 实时，**CPU 也可实时** | ~1GB 级 | 带 VAD+标点+时间戳，支持热词，长音频整段转写；FunASR 官方还提供 **OpenAI 兼容服务**部署（funasr.com/models.html、github.com/modelscope/FunASR） |
| FunASR SenseVoiceSmall | ★★★★☆（CER 略低于 paraformer，多语言） | 极快（比 Whisper-small 快约 15 倍） | 小 | 额外带**情感识别+音频事件检测**（可做"她听出你情绪"的彩蛋）；中文为主场景官方建议 SenseVoice（最快）或 paraformer-zh（最稳+热词） |
| faster-whisper large-v3 | ★★☆☆☆（中文 CER ~20%，funasr 官方对比数据） | GPU 快；CPU int8 可近实时（large-v3 1.55B 参数约 3GB，CPU 建议用 small/medium int8） | tiny~large 全档 | 多语言强（中英混说可用），中文纯场景不如 FunASR |

**云端**：
- **智谱 GLM-ASR-2512**：0.06 元/分钟（约 16 元/百万 tokens ≈ 0.0002 元/秒，docs.bigmodel.cn/cn/guide/models/sound-and-video/glm-asr），便宜且和 GLM 同平台同 key；另有开源 1.5B GLM-ASR-Nano-2512 可本地部署。桌面闲聊一分钟说不了几句话，成本可忽略，但**本地 FunASR 已够用且零延迟零成本**，云端只做备用。
- 剪映 API：无官方开放 API，逆向接口不稳定，不推荐。

**交互方式：按住说话 vs 唤醒词**：
- **按住说话（PTT）**：v1 强烈推荐——零误触、零功耗、实现只需一个热键+录音，无需唤醒引擎
- **唤醒词**（v2 常驻监听时再加）：
  - **openWakeWord**（dscripka/openWakeWord）：完全开源免费，openwakeword.com 支持自定义唤醒词训练（20+ 语言），社区评价可靠性一般但免费（Reddit r/speechtech）
  - **Porcupine**（Picovoice）：精度高、CPU <5%、轻量，但商业产品——个人开发者需申请免费许可证（个人用途免费），自定义唤醒词要走其平台（picovoice.ai、CSDN 对比文）
  - Snowboy 已死，排除
- 建议：先 PTT 跑通全链路 → 后期用 openWakeWord 训练"小土豆"自定义唤醒词（中文唤醒词训练质量需实测，列为未知项）；若误唤醒率高再换 Porcupine 个人免费 license

**结论**：FunASR paraformer-zh（或 SenseVoiceSmall 想要情绪检测时）本地部署 + 按住说话。无 N 卡不是障碍（FunASR CPU 实时可行）。

### 2.3 TTS 升级路线

| 梯度 | 方案 | 成本 | 音质 | 状态/风险 |
|---|---|---|---|---|
| T0（已达成） | Windows SAPI（System.Speech） | 0，离线 | ★★☆ 机械感明显 | ✅ 本机已实测出声，作为**永久兜底** |
| T1（第一步升级） | **edge-tts**（微软 Edge 在线 TTS 非官方接口） | 0（云端） | ★★★★ zh-CN-XiaoxiaoNeural 等神经网络音色远好于 SAPI | ⚠️ **目前仍可免费用**，但属非官方：存在 403 风险（Sec-MS-GEC 令牌/时间同步问题、部分地区限流；GitHub issue #458、掘金/微软 Q&A 均有记录）。修法：系统时间同步、升级 edge-tts 版本、必要时代理。必须实现"SAPI 自动兜底" |
| T2（付费情感） | **GLM-TTS**（智谱，2025-12 开源+API）/ **火山豆包 TTS** / 讯飞超拟人 | GLM-TTS：API 按量（有免费体验额度，社区 zai-tts 项目可包成 OpenAI Speech 格式）；豆包大模型合成 **4.5 元/万字符**（45 元/年 10 万字符起，docs.volcengine 1359370）；讯飞一句话复刻类似 | ★★★★★ 情感/语调智能预测，多情感音色 | 正式商用级；豆包实测码率/延迟优于讯飞（知乎对比） |
| T3（专属音色克隆） | **GPT-SoVITS**（开源） | 0 软件费，但**硬件是硬门槛**：官方要求 NVIDIA CUDA 显卡 6GB+ 显存（训练），推理最低 4GB（CSDN/知乎/官方 README）；有 gsv-tts-lite 等低显存引擎宣称毫秒级响应 | ★★★★★ 5 秒样本零样本克隆，1 分钟数据微调 | ❌ **本机无 N 卡（AMD RX 6500M 4GB），DirectML 路线不成熟，本机不可行**。替代路径：① GLM-TTS 音色复刻 API（3 秒样本克隆，docs.bigmodel.cn 音色复刻接口）② 豆包声音复刻（秒级录音）③ 阿里云函数计算部署 GPT-SoVITS（官方教程，免 GPU 运维）④ 未来换 N 卡（≥6GB）再本地跑 |

**推荐梯度**：上线即 SAPI（已通）→ 一周内接 edge-tts（音质跃升、仍免费、留 SAPI 兜底）→ 用出感情后上 GLM-TTS 音色复刻给"她"定制专属音色（3 秒样本，成本极低）→ GPT-SoVITS 仅在未来有 N 卡或云 GPU 时考虑。

### 2.4 对话记忆

**参考系**：OpenClaw 自身记忆系统 = Markdown 文件为唯一真实载体（MEMORY.md 长期精华 + 每日日志 + 会话 JSONL，四层堆栈：会话 JSONL → 每日 → 长期 → 载入，知乎/OpenClaw 全书第六章）。数字人直接**复用同构设计**，好处是与 OpenClaw 生态天然互通。

**推荐架构（轻量三层）**：
1. **会话层**：`sessions/YYYY-MM-DD.jsonl` 逐轮追加（append-only，永不损坏，天然适合流式写入；崩溃恢复友好）。每行一条 `{ts, role, content, tool_calls?, emotion?}`
2. **人设层**：`persona.md`（静态人设：性格、口癖、称呼、边界）+ `facts.md`（用户事实卡：名字、偏好、重要日期）——每次请求拼进 system prompt
3. **长期层**：`MEMORY.md` 由"每日收尾摘要任务"（可挂 OpenClaw cron 每晚跑）从当日 JSONL 提炼要点合并；上下文窗口只带 最近 N 轮原文 + MEMORY.md + persona，超出部分靠摘要

**JSONL vs SQLite**：对话原文用 JSONL（人类可读、git 可管、无锁竞争）；**提醒/定时/结构化事实用 SQLite**（OpenClaw cron 本身就持久化在共享 SQLite 里，同类场景天然一致）。两者不冲突，按数据形态分工。

**向量记忆**：v1 不上。单用户闲聊数据量小（每天几百 KB 文本），关键词检索+摘要已覆盖 90% "她还记得我"体验；等语料到 MB 级再考虑本地 embedding（GLM embedding API 或 bge-small CPU 即可），届时也不需要专门向量库（sqlite-vec 就够）。

### 2.5 行动层 Function Calling

**GLM tools 定义格式**：OpenAI 兼容——请求体 `tools: [{type:"function", function:{name, description, parameters(JSON Schema)}}]`，模型返回 `tool_calls`，回传 `role:"tool"` 消息。GLM-4.5+ / 4.7-Flash / 5.3-Flash 均支持（docs.bigmodel.cn function-calling 指南）。

**本地工具清单设计（见第三章）**：开软件、查天气（wttr.in `?format=j1` JSON，免 key，github.com/chubin/wttr.in）、定提醒（转 OpenClaw cron）、整理文件、网页搜索等。

**沙箱与安全**：
- 白名单制：可打开的软件列表、可操作的目录列表硬编码于本地配置，模型只能引用白名单内的名字
- **危险操作确认**：删除/移动/覆盖文件、任何 shell 命令 → 弹确认框（她口头复述将执行的操作，用户点确认/说"确认"）
- 破坏性命令黑名单（rm/del/format/mv 系统目录/注册表等）直接拒绝，连确认都不给
- 所有工具调用写审计日志（JSONL 记录 who/what/when/result）
- subprocess 一律 `shell=False`、参数列表传递；超时上限（如 30s）

### 2.6 OpenClaw 集成（详见第四章）

OpenClaw 网关 = WebSocket 服务器（默认端口 **18789**），完整 RPC 协议覆盖 status/channels/models/chat/agent/sessions/nodes/approvals（docs.openclaw.ai/gateway/protocol、/gateway/external-apps）。另有 **OpenAI 兼容 HTTP 端点 `/v1/chat/completions`（默认关闭，需在 gateway.http.endpoints 开启）**。Cron 在网关进程内运行、持久化到共享 SQLite、重启不丢（docs.openclaw.ai/zh-CN/automation/cron-jobs）。

---

## 三、行动层工具清单设计（v1）

| 工具名 | 功能 | 实现 | 安全级别 |
|---|---|---|---|
| `open_app` | 打开软件/网站 | `os.startfile()` / `start <uri>`，白名单映射表（如 "浏览器"→chrome.exe，"B站"→URL） | 🟢 低危：白名单内直接执行 |
| `get_weather` | 查天气 | `curl wttr.in/<城市>?format=j1`（免 API key，JSON），解析 current_condition + 3 日预报 | 🟢 低危：只读 |
| `set_reminder` | 定时提醒 | 调 OpenClaw `openclaw cron add --at "20分钟后" --message "提醒内容"`（at 一次性任务）或 gateway RPC；持久化由 OpenClaw SQLite 保证 | 🟢 低危：只增不删 |
| `list_reminders` / `cancel_reminder` | 提醒管理 | `openclaw cron list/remove` | 🟡 中危：删除需确认 |
| `web_search` | 联网搜索 | 走 OpenClaw 网关的搜索能力（或直接调智谱 web_search 工具） | 🟢 低危：只读 |
| `organize_files` | 整理文件（按类型/日期归类下载目录等） | Python pathlib 移动；**只允许白名单目录**（Downloads/Desktop 等）；先输出计划清单 → 用户确认 → 执行；进回收站而非永久删除 | 🔴 高危：两步确认（计划预览 + 明确批准），dry-run 默认开启 |
| `run_openclaw_task` | 复杂任务委托（写代码/管项目/跑脚本） | 封装转发到 OpenClaw（见第四章），由 OpenClaw 的执行环境+审批机制兜底 | 🟡 由 OpenClaw 审批流管控 |
| `remember_fact` | 记住用户事实 | 写入 facts.md（追加式） | 🟢 低危 |
| `screen_capture`（可选 v2） | 看屏幕 | 截图→GLM-4.6V/5.3-Flash 多模态理解 | 🟡 只读但涉隐私，默认关 |

**统一执行框架**：每个工具 = `schema`（给 GLM 的 JSON Schema）+ `handler`（本地函数）+ `policy`（安全级别/白名单/确认要求）。工具注册表单文件管理，新增工具零侵入。

---

## 四、OpenClaw 集成方案

**定位**：数字人（形象层+对话层）是"皮套/前台"，OpenClaw 是"干活的身体"。

**推荐架构（双通道）**：

```
用户 ⇄ 桌宠UI（形象层）
         │
         ├─ 闲聊通道：桌宠 → GLM-4.7-Flash API（直连，低延迟，本地记忆+本地小工具）
         │
         └─ 干活通道：桌宠 → OpenClaw 网关 → 主智能体（跑代码/管项目/cron/消息）
                      · WebSocket RPC (ws://localhost:18789)  ← 主推荐
                      · 或 HTTP /v1/chat/completions（需 gateway.http.endpoints 开启）
                      · 或 CLI：openclaw agent --message "..."（最简单，功能全）
```

**三条接入路径对比**：

| 路径 | 协议 | 适用 | 备注 |
|---|---|---|---|
| **A. WebSocket RPC**（推荐） | ws://localhost:18789 + RPC 方法（chat/agent/sessions/approvals...） | 需要长连接、实时事件（任务完成回调、审批请求推给桌宠播报） | 官方外部应用集成标准路径（docs.openclaw.ai/gateway/external-apps） |
| B. OpenAI 兼容 HTTP | POST /v1/chat/completions | 桌宠代码只想用 OpenAI SDK 复用 | **默认关闭**，需改 gateway 配置开启（gateway.http.endpoints）；promptfoo 等工具即这样接入 |
| C. CLI 子进程 | `openclaw agent --message` / `openclaw cron add` | 快速原型、一次性任务 | 零配置，桌宠用 subprocess 调 CLI 即可跑通 v1 |

**落地节奏**：v1 用 C（CLI 转发，一天跑通"她替你管项目"演示）→ v2 换 A（WebSocket，获得任务状态推送+审批交互，她能在屏幕上播报"代码跑完了/需要你批准这个命令"）。

**审批联动**：OpenClaw 的危险命令审批（approvals）事件经 WebSocket 推到桌宠 → 她口头播报 + 桌宠弹确认框 → 结果回传网关。这条闭环是"安全+拟人"兼得的关键。

**记忆互通**：数字人记忆文件（JSONL/MEMORY.md 同构）放在工作区，OpenClaw 主智能体可直接读，实现"她和你聊过的事，干活时也知道"。

---

## 五、风险与未知项

**风险**：
1. **edge-tts 非官方接口**：随时可能被微软封禁（ToS 边缘、403 已有先例）。缓解：SAPI 自动兜底 + 监控失败率自动降级 + 不把它当唯一方案
2. **智谱免费政策变动**：免费模型历史上有自动切换（4.7→5.3-Flash 已发生）、活动制免费（夜间畅用）等先例。缓解：模型名做成配置项，主备双模型（4.5-Flash / 4.7-Flash / 5.3-Flash 三选一热切换）
3. **GLM 免费档并发=2**：多路同时请求（对话+后台摘要+cron 任务撞车）可能 429。缓解：本地请求队列串行化 + 指数退避重试
4. **DeepSeek 涨价潮**（2026-08 峰谷定价、V4 Pro 高峰输出 27 元/M）：若选 DeepSeek 做主力需按峰谷控制调用时段，性价比已不如智谱免费档
5. **工具执行安全**：文件整理等高危操作必须两步确认，防止模型幻觉参数误删文件

**未知项（需实测/后续确认）**：
1. GLM-5.3-Flash 在 bigmodel.cn 国区是否**长期免费**（目前证据：开源 + Coding Plan 内含 + 夜间活动免费；4.5/4.7-Flash 有明确"完全免费"文档背书）→ 上线前到 bigmodel.cn/pricing 核对当月政策
2. openWakeWord 自定义**中文唤醒词**（如"小土豆"）的唤醒率/误唤醒率——需用本人声音样本实测，官方平台支持 20+ 语言训练但中文质量无权威评测
3. FunASR paraformer-zh 在本机 **CPU（无独显加速）上的实际实时率**——官方称 CPU 可实时，但需实测 RTF 是否 <1（若不行降级到 Fun-ASR-Nano 或 SenseVoiceSmall，更小更快）
4. OpenClaw 网关 OpenAI 兼容端点开启后的**流式/工具调用支持完整度**（官方标注"small surface"，可能不含 tools 参数完整语义，v2 集成前需验证）
5. GLM-TTS **音色复刻 API 的免费额度与商用条款**（3 秒克隆能力已确认存在，计费细节未查到公开页）
6. 桌宠→网关 WebSocket 的**鉴权方式**（token 在网关配置中的生成位置），集成时查 gateway 配置文档

---

### 附：主要来源
- 智谱免费模型：docs.bigmodel.cn（glm-4.5-flash、glm-4-flash-250414、function-calling、pricing、coding-plan/overview、glm-asr、glm-tts、音色复刻 API）
- GLM-4.7-Flash 免费上线：zhipuai.cn/zh/news/148、finance.sina.com.cn（2026-01-20）
- GLM-5.3-Flash：z.ai/blog/glm-5.3-flash、oschina.net/news/502144、llm-stats.com、docs.z.ai/guides/overview/pricing
- DeepSeek 定价：api-docs.deepseek.com/zh-cn/quick_start/pricing、新浪科技/钜亨/Yahoo 奇摩（2026-08 涨价报道）
- FunASR：funasr.com/models.html、github.com/modelscope/FunASR、huggingface.co/funasr/paraformer-zh、funasr.com/blog/which-funasr-model.html
- faster-whisper：github.com/SYSTRAN/faster-whisper、CSDN 模型选型指南
- 唤醒词：github.com/dscripka/openWakeWord、openwakeword.com、picovoice.ai、百度云语音唤醒方案对比
- edge-tts：pypi.org/project/edge-tts、github.com/rany2/edge-tts/issues/458、掘金 403 修复文、learn.microsoft.com Q&A
- GPT-SoVITS：github.com/RVC-Boss/GPT-SoVITS（README 硬件要求）、localaimaster.com（4GB 推理）、pypi gsv-tts-lite、阿里云 FC 部署教程
- 豆包/讯飞 TTS：volcengine.com/docs/6561/1359370（计费）、volcengine.com/product/tts、xfyun.cn 超拟人/一句话复刻、知乎实测对比
- OpenClaw：docs.openclaw.ai（gateway/protocol、gateway/external-apps、gateway/openai-http-api、zh-CN/automation/cron-jobs、zh-CN/tools/subagents）、meta-intelligence.tech（18789 端口）
- wttr.in：github.com/chubin/wttr.in
