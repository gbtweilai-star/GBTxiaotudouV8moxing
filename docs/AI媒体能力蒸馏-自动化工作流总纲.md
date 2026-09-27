# AI 媒体能力蒸馏 · 自动化工作流总纲

> 2026-09-26 · 数据源：JuneYaooo/awesome-ai-media-cn 全清单（约 90 个工具）+ TapNow 四板斧对标
> 结论：**不逐个装 90 个工具，按七大产线段蒸馏成 12 个编制岗位，装 8 个、抄 6 个思路、跳过重叠的。**

---

## 一、总图：七大产线段 × 岗位排布

```
策划 → 素材 → 生成 → 后期 → 审核 → 分发 → 变现
```

| 产线段 | 蒸馏出的岗位 | 采纳方式 | 具体工具 |
|---|---|---|---|
| **策划** | 竞品情报员 | **ADOPT** | MediaCrawler（小红书/抖音/快手/B站爬虫）+ BiliNote（视频→笔记） |
| **素材** | 无水印搬运工 | **ADOPT** | Douyin_TikTok_Download_API（自托管去水印下载） |
| **生成·短视频** | 一键成片师 | **ADOPT** | MoneyPrinterTurbo（脚本/配音/字幕/剪辑全自动）——短视频线主力 |
| **生成·解说** | 解说员 | 备选 | NarratoAI（AI 解说+剪辑） |
| **生成·长片/短剧** | 短剧工厂 | **ADOPT** | PlotCraft（**角色一致性+唇形同步**——直接补我们的一致性缺口）+ huobao-drama（一句话短剧） |
| **生成·视频模型** | 云端渲染农场 | **CLOUD** | Wan2.1 / HunyuanVideo-1.5（消费级可跑）→ **派 Colab**（本机 7.39GB 跑不动，云内存扩容） |
| **后期·拆条** | 病毒剪辑手 | **ADOPT** | CutDeck（Rust 管线长拆短）或 hotclip（竖屏爆款）——**TapNow「病毒式短片」的开源等价物** |
| **后期·字幕** | 字幕大师 | **ADOPT** | VideoLingo（Netflix 级）+ faster-whisper |
| **后期·硬字幕/水印** | 清道夫 | 备用 | video-subtitle-remover |
| **审核** | （框架双闸已有） | 自研在岗 | social_life.redact + content_review |
| **分发** | 多平台发布官 | **ADOPT** | social-auto-upload / matrix（Playwright 多平台）——**发布段自动化的最后一块拼图** |
| **变现** | 数字人主播 | **ADOPT** | aigcpanel（虚拟主播/数字分身）——直播带货位 |
| **编程视频** | Remotion | 已在用 | （注意商业许可条款） |

## 二、TapNow 四板斧 → 我们的免费实现（不装它，超它）

| TapNow 功能 | 开源等价 | 我们的落地 |
|---|---|---|
| AI 缩略图（URL→高 CTR 图） | yt-dlp + ffmpeg 抽帧 + LLM 文案 + pollinations 生成 | 给《末班义庄》每集自动出 3 版缩略图带 CTR 预估 |
| 病毒式短片（3 小时→30 秒爆款） | **CutDeck/hotclip + faster-whisper + LLM 找钩子** | 电影正片→短剧拆条自动线；直播回放→高光 |
| URL 变内容（30 秒） | 同上链路 + ai-mixed-cut（「解构-重构」爆款再创作） | 竞品爆款→我们的再创作管线 |
| 节点画布工作流 | remotion 工作流可视化 | 电影产线的节点化调度（二期） |

## 三、EMULATE 借鉴（不装，抄架构思路）

- **video-clipforge 的 9 阶段 DAG 管线**：任务拆成有向无环图、逐节点验收——套用到电影产线调度；
- **OpenMontage 的 Agent 全流程**：调研→脚本→素材→剪辑→成片，agent 驱动——与我们「牛马派单」同构，参考其任务格式；
- **AIGC-Claw 的 Web/微信/飞书多入口**：任务入口多元化——牛马的任务可以从微信直接下。

## 四、SKIP（重叠，不装）

ShortGPT（被 MoneyPrinterTurbo 覆盖）· RedditVideoMakerBot（无 Reddit 线）· BibiGPT 系（BiliNote 更聚焦）· 各类重复的搬运器（选 social-auto-upload 一个）。

## 五、内存约束下的安装策略（本机 7.39GB · 可用 0.42GB 的现实）

1. **本机只装轻量 CLI**：faster-whisper（cpp 版）、CutDeck、social-auto-upload、MediaCrawler——每个 <500MB 运行占用；
2. **重型模型全部上云**：Wan2.1/HunyuanVideo/文生视频推理 → **Colab GPU**（已列编制）；批量生图 → 牛马沙箱；
3. **页面文件已 37GB 够用**；物理内存 7.39GB 是硬顶——**真正的扩容是云内存 + 加内存条**（8G→16G 硬件升级，主人决策）；
4. 本会话 ZCode 自占 1.75GB——重活跑之前我会先交还。

## 六、安装排期（一天建产线）

| 批次 | 安装 | 解锁 |
|---|---|---|
| 第 1 批（今天） | MoneyPrinterTurbo + CutDeck + faster-whisper | 短视频一键成片 + 拆条 + 字幕 —— 短视频线全自动化 |
| 第 2 批 | social-auto-upload + MediaCrawler | 分发自动化 + 竞品情报 —— 发布段闭环 |
| 第 3 批 | PlotCraft + aigcpanel | 短剧角色一致性 + 数字人主播 —— 电影/带货线 |
| 云端 | Colab 装 Wan2.1/HunyuanVideo | 云渲染农场 —— 内存扩容的真正答案 |

**蒸馏完成度：清单 90 工具 → 8 装 + 6 借鉴 + 跳过重叠 ≈ 能力全收录，零冗余部署。**

---

## 七、零遗漏补全表（主人令：一个类别都不许漏 · 2026-09-26 补）

| 清单类别 | 蒸馏结论 | 归属 |
|---|---|---|
| 一键视频生成（29 个） | MoneyPrinterTurbo 为主力，NarratoAI 备选，OpenMontage/AIGC-Claw 抄 Agent 架构，CaroCut（Remotion 多 Agent）与我们的 remotion 产线合流 | 第 1 批装主力，架构入 EMULATE |
| AI 文生视频模型（9 个） | Wan2.1/HunyuanVideo-1.5（消费级可跑）→ **Colab 云端**；FramePack（低显存长视频）→ 备选；Open-Sora/CogVideo 观望 | 云渲染农场 |
| 自媒体运营/分发（18 个） | **social-auto-upload + matrix** 已选；补充 **Postiz**（自托管社媒管理台，开源）作分发中枢 UI；AIWriteX（公众号）→ 公众号线开启时启用；RedBox（小红书工作台）→ 小红书线开启时启用 | 第 2 批扩 |
| 社媒爬虫/竞品（9 个） | **MediaCrawler** 已选（覆盖小红书/抖音/快手/B站/微博五合一）；**Douyin_TikTok_Download_API**（自托管无水印下载）+ **parse-video**（Golang 轻量去水印）→ 素材段补充；**TikHub SDK**（部分可用·付费 API）→ 跳过（有免费替代） | 第 2 批 |
| 字幕与本地化（15 个） | **VideoLingo + faster-whisper** 已选；补 **KrillinAI**（翻译配音一体）→ 海外版（YouTube/TikTok 英字）启用；**video-subtitle-remover** → 素材洗稿用 | 第 2 批 |
| AI 短剧生成（10 个） | **PlotCraft**（角色一致性+唇形同步）已选；补 **LocalMiniDrama**（本地数据不出机——隐私线符合框架纪律）→ 备选；huobao-drama（一句话短剧）→ 快速原型用 | 第 3 批 |
| AI 视频分析与笔记（4 个） | **BiliNote** → 给编剧室自动出竞品笔记（B站僵尸片拆解） | 第 2 批 |
| AI 数字人（1 个） | **aigcpanel**（虚拟主播/数字分身）→ 直播带货位 | 第 3 批 |
| 编程式视频制作 | **Remotion 已在用**（注意商业许可条款——开源项目发布可用，商用许可需确认） | 在岗 |
| 视频编辑库 | **ffmpeg-python**（我们直接用 ffmpeg 原生）+ MoviePy（PIL 做旧管线的视频版备用） | 在岗 |

**蒸馏终局：11 大类 · 90+ 工具 · 每一类都有归属（装 10 / 借鉴 8 / 云端 3 / 在岗 3 / 明确跳过若干）——零遗漏。**

---

## 八、语音能力升级：克隆配音选型（主人令：要能克隆配音的多功能语音）

需求：小土豆/秋师父/**主人的声音**都能克隆定型，跨集一致；支持多角色多情绪。

| 候选 | 星级 | 克隆方式 | 中文质量 | 本机可行性 |
|---|---|---|---|---|
| **GPT-SoVITS** | ⭐45k+ | 少样本（1 分钟参考音频） | 顶级（中文先天优化） | 推理可 CPU/4GB 显存；训练需 GPU → **训练派 Colab** |
| **CosyVoice2**（阿里） | 热门 | 零样本（3-10 秒参考） | 顶级 · 流式 | 同上 |
| **F5-TTS** | 热门 | 零样本 | 优 | 轻量 |
| **OpenVoice** | ⭐34k | 即时克隆（音色） | 中 | 轻 |
| edge-tts（在用） | — | 不支持克隆 | 好（预设音色） | 零依赖 ✔ |

**接入方案（voice_orchestra 新增「克隆引擎」档）**：
1. 第一步：**F5-TTS 或 CosyVoice2 本地推理**（零样本：录 10 秒参考音 → 定型小土豆/秋师父声线）；
2. 训练级定制：GPT-SoVITS 微调 → **Colab GPU 训练**（内存压强派单制：本机不训）；
3. 接线：`voice_orchestra` 注册克隆引擎档位 → 电影配音统一走克隆声线（跨集一致，配合连续性铁律）；
4. 主人自己的声音克隆（用于旁白/出镜配音）：参考音频 10 秒即成，**声纹属生物凭据——参考音频只存 DPAPI 保险箱，不进 git**。
