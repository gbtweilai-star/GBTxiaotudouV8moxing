# SKILL VETTING REPORT · 三块插件（视频/电影 · 音乐 · 挖漏洞）

> 按 `AGENTS.md`「Supply Chain / Skill Protection」流程产出：**查来源 → 读代码 → 评权限 → 出本报告 → 等主人确认**。
> **本报告不构成安装。** 未经主人明确同意，一个都没装、没下、没改环境。

日期：2026-09-21 · 审查方式：读上游 README / 源码仓库元数据（GitHub raw）

---

## 一、先说本地已经有什么（省得重复装）

| 块 | 本地已有 | 缺口 |
|---|---|---|
| **视频/电影** | 能力：`h3_video_gen`（H3mini 四原语 T2VA/I2VA/FL2VA/Ref2VA）· `libtv_skill` · `libtv_workflow`（节点式工作流五动作）· `a1art_skill` · **`drama`（剧本→分镜：景别·运镜·时长·情绪·角色位置）** · `film_intel` / `video_intel`<br>技能（110 个里 15 个）：`sora` · `fal-kling-o3` · `venice-video` · `remotion` · `fal-video-edit` · `fal-lip-sync` · `youtube-clipper` · `video-downloader` | **「发布」那一环没有专门技能**；**没有任何一条龙编排**（各环是散的） |
| **音乐** | 能力：`music_publishing`（三层只读归位）· `music_intel` · `voice` · `voice_orchestra`<br>技能：**`ai-music-album`** · `venice-audio-music` · `speech` · `venice-audio-speech` | **不成套**：没有作词／编曲／**混音母带**／发布准备的完整链 |
| **挖漏洞** | 能力五件套：`sec_scan`（OWASP+CWE）· `sec_surface`（攻击面）· `sec_chain`（利用链）· `sec_defenses`（蓝队验证）· `sec_llm`（黑客大脑，独立模型+独立密钥） | **技能侧为 0** —— 没有方法论、没有 payload 库、没有平台对接、没有验证闸 |

---

## 二、三个候选（逐项审查）

### ① AI视频/电影一条龙 · `ttalkkaklab/social-flow`

- **来源**：<https://github.com/ttalkkaklab/social-flow>
- **许可**：**Apache-2.0** ✓（含明确免责声明）
- **规模**：Claude Code 插件 · 18 skills + 内置 MCP server（46 工具；带发布凭据 72；带 portal key 96）· `server/dist` 已提交，装完即用
- **一条龙覆盖度**：**最高**。链路是
  `storyboard（只规划、不生成任何东西）→ 分平台视频与文本生产 → HITL 审批后发布`
  发布目标：**Threads · Instagram(Reels) · Facebook Pages · YouTube(Shorts + 长视频)**
- **分镜是真的**：`storyboard_read/apply/check` + `scenario_check`，分镜表按 sequence→scene→shot 四层读；
  有 `shot.eyeline`（视线）、`shot.depth`（景深）、`shot.render`（按目的选：静帧/3D角色/3D物件/数据图/生成视频），
  还有「胶片风格包」与**转场契约**（`dip` 优先）
- **剪辑是真的**：`skills/produce/references/cinematic-edit.md`；装配时把分镜转场编译进时间线，
  含边界帧校验与连续性播放片段；**「不许在视频上画东西」**——需要箭头的镜头改做 HTML 动效页
- **HITL 双闸** ✓：分镜审批（生产前）+ 发布审批（公开前）。**发布工具无自带复核闸，仅由发布技能的 HITL 门守**
- **成本透明** ✓：默认经济档 **$0.27–0.29/集**；每集上限 `max_cost_per_video` 默认 $1.00，**花钱前就拦**；
  价格表 `prices.tsv` 每行带**证据等级与出处**；未知价格**直接 exit 1 而不是猜**
- **本地可跑** ✓：图片与 TTS 有**端上引擎**（Z-Image / Supertonic 3），**零成本零密钥**；
  STT 用 Qwen3-ASR 本地；视频可走「确定性 HTML 动效页」零成本
- **安全契约** ✓：不落明文 token（文件 mode 600）· 账号经 `/me` 解析 · 不做事实扭曲（时效数字要两个独立来源）·
  不做跨平台复制粘贴 · 生成画面限「氛围镜头与自有角色」，禁真人/国徽/摆拍新闻画面
- **⚠️ 需注意**：
  - **文案风格闸是韩语专用** —— `check-style.py` 遇到非韩文**退出 4（SKIP）并明说"未检查"，绝不说"通过"**（这点很诚实）
  - 拍摄脚本与调研解析器**仅韩语**
  - 依赖：Node 20+ / ffmpeg / Chrome / python3（+ 可选 Blender 4.2+、supertonic、whisper.cpp）
  - 带「增长循环」（grow-threads/youtube/instagram）会在**一次 HITL 标准授权**下**自动发帖**；
    grow-threads **无日更上限**（换来的是每条出站文案要过 95 分对抗式复核）。**这是一条要主人自己决定的边界。**
  - 它是 Claude Code 插件；本环境是 DSH。README 明确支持 **Codex CLI / Grok CLI / Buzz**，
    但 **DSH 不在支持列表** ⇒ 要接得做适配（它的内核是 markdown 技能 + MCP server，可移植，但不是开箱）

### ② AI音乐整套 · `bitwize-music-studio/claude-ai-music-skills`

- **来源**：<https://github.com/bitwize-music-studio/claude-ai-music-skills>
- **许可**：**CC0（公有领域）** ✓✓ —— 三个里最干净的
- **规模**：**53 个技能 · 80+ MCP 工具（Python）· 72 个曲风目录 · 4,412 个测试**
- **整套覆盖度**：**最高**。链路是
  `概念开发（7 阶段）→ 调研（10 域并行子代理 + 核验）→ 作词（韵律/押韵/发音风险）→ Suno 提示词 → 导入分轨逐轨打磨 → 混音母带（-14 LUFS 流媒体标准）→ 发布准备（宣传视频 + 社媒文案）`
- **母带是真的**：`mastering-engineer` 技能知道**各平台响度目标与按曲风的 EQ 曲线**；
  QC 是 **7 项**（响度 · 削波 · 静音 · 相位 · 立体声宽度 · 频谱平衡 · 动态范围）
- **歌词闸是真的**：**13 项清单**（押韵 · 韵律 · 发音 · 视角一致 · 事实准确）
- **溯源是真的** ✓：纪实类专辑要求「每条主张都能追到一条已捕获、已核验的来源」，**核验通过 + 人工签核之后才允许生成歌词**
- **平台支持** ✓：**原生 Windows 全支持**，CI 在 `windows-latest` 上跑全套测试（含 MCP 启动与 MuseScore PDF 导出的 Windows 专线）
- **CI 安全** ✓：bandit + pip-audit 静态扫描，Dependabot 每周巡检
- **⚠️ 需注意**：
  - 生成在 **Suno** 上做（第三方），其余在终端做；插件本身不生成音频
  - 需要一个 **PostgreSQL**（宣传/推文内容管理用）
  - 多轨会话在 Pro 订阅下会撞速率上限（作者建议 Max）
  - 同样是 Claude Code 插件 ⇒ **DSH 需适配**

### ③ 专业挖漏洞 · `H-mmer/pentest-agents`

- **来源**：<https://github.com/h-mmer/pentest-agents>（安装包 `H-mmer/pentest-agents-suite`）
- **许可**：**⚠️ 未声明开源许可** —— README 只写「For authorized security testing only. Follow responsible disclosure.」
  **没有 LICENSE 字段 ⇒ 默认「保留所有权利」**。**这是本报告里唯一的硬性阻断项。**
- **规模**：~760 文件 / ~118k 行 · **50 agents · 26 命令 · 19 CLI 工具 · 11 技能 · 2 MCP servers**
- **覆盖度**：**最专业**。
  - **16 个众测平台**对接（HackerOne 全 API / Bugcrowd / Intigriti / Immunefi / YesWeHack + 11 桩）
  - 19 个漏洞类专家 agent（XSS/SQLi/CSRF/SSRF/SSTI/IDOR/认证/信息泄露/开放重定向/RCE/XXE/文件上传/CORS/子域接管/业务逻辑/竞态/提权/OAuth/**LLM-AI**）
  - **SAST 流水线 8 个 agent**（文件排序→入口映射→危险点映射→流追踪→缺口分析→对抗降级→狩猎→利用构建）
  - **Web3 审计** agent（Solidity grep 库 + Foundry PoC + DeFi 模式）
  - **A→B→C 利用链构建**（`/chain`，9 行能力表 + 4 条documented深链）
  - **方法论技能带真实报告蒸馏**：`hunt-rce` 1,135 行（1,218 份报告蒸馏）· `hunt-idor` 969 行（1,117 份）· `hunt-xss` 968 行 · `hunt-oauth` 770 行（365 份）· `hunt-llm-ai` 930 行（**OWASP LLM Top 10 v2025 + Agentic AI Top 10**）
  - **payload 库 2,605 行**、31 条狩猎规则、665 行「十大常见错误」
- **自带安全闸** ✓（这点做得好）：
  - **PreToolUse scope hook**：Bash 命令按 `scope.yaml` 精确+通配匹配，**越界目标在工具调用前就被拦**
  - **7-Question Gate**：每个发现必须过验证，第一个 NO 就 KILL
  - **CVSS 策略守卫**：H1 用 CVSS 3.1，其他平台用 4.0，机器强制
  - **never-submit 过滤**、`/report` 与 `/submit` 硬闸（无 `/validate` PASS 直接拒）
  - 断路器（连续 5 次 403/429 → 退避 60s）、端点级留痕、`file_path_guard` 拦幻觉路径
  - RAG 构建器的破坏性操作**一律要 `--execute`**，默认只打印计划
- **支持本工作区形态** ✓：`providers/openclaw/` 原生支持 OpenClaw（本工作区用的就是 `.openclaw-autoclaw`），
  另有 Codex / Gemini / Cursor / Windsurf / Copilot 六套预渲染包
- **⚠️ 风险（必须主人拍板）**：
  1. **许可未声明** —— 法律上不能直接拿来用/改/分发
  2. 这是**攻击性框架**：含 WAF 绕过阶梯、隐身浏览器（Camoufox 过 Cloudflare/Akamai）、2,605 行 payload
  3. 与本工作区红线的关系：本框架规定「**仅跑自有资产**」「**未授权目标不碰**」
     （`sec_scan` 的描述就是「扫描自有代码」）。这套框架**面向的是别人家的众测目标** —— 用途取向相反
  4. 它要对接众测平台并 **`/submit` 提交报告**，凭据是主人账号
- **同类备选**（若许可问题是阻断项）：
  - `backspace-shmackspace/deep-code-security` —— 多语言 **SAST**，tree-sitter 污点追踪 + **沙箱内验证利用** + MCP 接口 ⇒ **对「自有资产」取向最贴合**
  - `elementalsouls/Claude-BugHunter` —— 82 技能 / 15 命令 / **681 份公开报告模式**，覆盖 24 个漏洞类
  - `S3DFX-CYBER/Claude-Skills-Security` —— 生产级安全 **triage** 技能（偏防守/分诊）
  - `din4e/Skills4RedTeam` —— 红队技能集

---

## 三、还有两个可参考的目录（不是插件，是索引）

- `ella-wang-opus/awesome-video-skills` —— 视频向的开源 agent 技能索引
- `Ashokbtech87/Generative-Media-Skills` —— 多模态（图/视频/音频）生成技能，muapi.ai 驱动
- `OnyxMunk/AudioForge` —— agentic 音频工作流（HuggingFace Space）

---

## 四、审查结论与建议

| 块 | 建议 | 理由 |
|---|---|---|
| **AI视频/电影** | **可装（需适配 DSH）** | Apache-2.0 · 双 HITL 闸 · 成本透明且在花钱前拦 · 端上零成本通道 · 明确安全契约。**唯一要主人定的是「增长循环自动发帖」这条边界** |
| **AI音乐** | **可装（需适配 DSH）** | **CC0** · 80+ 工具 · 13+7 双闸 · 原生 Windows · CI 带 bandit/pip-audit。最干净的一个 |
| **挖漏洞** | **⛔ 先解决许可，再谈用途** | 许可未声明（默认保留所有权利）= 硬阻断；且它是**面向外部众测目标**的攻击框架，与本工作区「仅自有资产」红线取向相反。若要补强自有资产的安全能力，建议先看 `deep-code-security`（SAST/污点追踪/沙箱验证，取向相符） |

### 需要主人回答的三件事

1. **许可**：`pentest-agents` 没写 License。是（a）放弃它改用 `deep-code-security`，还是（b）您去确认上游授权？
2. **用途边界**：挖漏洞这块，是只做**自有资产**（与现有 `sec_*` 一致），还是要做**外部众测**？
   后者需要新的授权作用域，且与现行红线冲突 —— 必须您显式改红线，我不擅自扩。
3. **自动发布**：social-flow 的「增长循环」会在一次授权下自动发帖（Threads 无日更上限）。
   要不要开？开了要不要加日更上限？

### 落地方案（等您点头后我再动手）

三个候选都是 **Claude Code 插件形态**（markdown 技能 + MCP server），本环境是 **DSH**。所以不能直接装，可选两条路：
- **A. 蒸馏成 GBT 能力**（与现有 110 个技能同构）：把它们的**方法论与闸**抽成本地技能，不引外部 MCP —— 零供应链风险，但少了生成端
- **B. 接 MCP 到 GBT**：这条路**框架里已经铺好、而且已经带门**（现场实测）：

  | 能力 | 域 | 门 | 实测 |
  |---|---|---|---|
  | `mcp_tools` | tentacle | **免卡** | `scopes=()` risk=low —— 只列契约清单 |
  | `mcp_connect` | tentacle | **要 `process_execute`** | `scopes=('process_execute',)` **risk=high** |
  | `mcp_call` | tentacle | **要 `process_execute`** | `scopes=('process_execute',)` **risk=high** |

  三个的说明写得很直白：「触手契约层：连接任意 MCP 工具服务器（学会契约协议=接入整个 MCP 生态）」
  「按契约调用已连接服务器的任意工具」。
  ⇒ **要把 social-flow / bitwize-music / deep-code-security 的 MCP server 挂上来，
  不需要改 `security/policy.py`，也不需要新作用域 —— 授权只能主人在终端发 `process_execute` 即可。**
  这是三块里唯一「门已经就位」的通路。

我倾向 **先 A 后 B**：先把方法论吃进来（零风险、立即可用），真要用生成端时再走 B（那时才需要授权出网与密钥）。

---

## 五、主人的决定与执行结果（2026-09-21）

| 问题 | 主人选择 | 执行 |
|---|---|---|
| 挖漏洞 | **A. 改用 `deep-code-security`**（自有资产向） | 已审源码（见下），并已蒸馏 |
| 自动发布 | **A. 先不开**，只要「生产到成片 + 文案」那一半 | 蒸馏时**发布端与增长循环一概不含** |
| 落地方式 | **A. 先蒸馏方法论** | ✅ 已完成，3 个技能 |

### `deep-code-security` 源码审查补充（主人选定后新审的）

- **三阶段**：HUNTER（Semgrep/tree-sitter 源汇匹配 + 污点）→ AUDITOR（**沙箱里真跑 PoC**）→ ARCHITECT（修复指引）
- **置信度评分透明**：污点路径完整度 45% + 净化器缺失 25% + CWE 严重度 20% + 利用验证 **10%（仅加分，PoC 失败不扣分）**
- **沙箱策略是真硬**：`--network=none` · `--read-only` · tmpfs `noexec,nosuid` · `--cap-drop=ALL` ·
  `no-new-privileges` · 自定义 seccomp · `--pids-limit=64` · `--memory=512m` · 以 `nobody(65534)` 运行
- **MCP 服务跑在宿主机原生 stdio 进程里，不在容器内** —— 规避 Docker socket 挂载攻击面
- 文件访问走 `DCS_ALLOWED_PATHS` 白名单并解析符号链接；发现物来源由服务端会话校验（外部不能注入 finding）
- **🔴 14 项已知局限全部明写**，其中第 1 条最要紧：
  「**只做过程内污点追踪 ⇒ 预期检出率是真实世界注入类漏洞的 10–25%**；多数 Web 漏洞跨函数边界，v1 查不到」
- **⚠️ 许可**：上游 README **未声明 License** ⇒ 与 `pentest-agents` 同类问题。
  本报告的处置是：**只蒸馏判据（不搬其代码）**，并在技能元数据里写明
  `upstream_license: 见上游仓库（README 未声明许可 —— 使用前请主人确认）`。
  **若要真正使用它的代码，仍需主人先确认上游授权。**

### 蒸馏产出：3 个本地技能（110 → 113）

| 技能 | 行数 | 分类 | 蒸馏来源 | 含什么 |
|---|---|---|---|---|
| `video-pipeline` | 93 | video-generation | social-flow（Apache-2.0） | 分镜四层结构 · 镜头三契约（视线/景深/渲染路由）· 三条硬规则 · 预算前置闸 · 剪辑转场与边界帧校验 · 可转发物与信息句判据 · 双 HITL 闸 · 上游 5 项局限 |
| `music-production` | 77 | audio-music | claude-ai-music-skills（**CC0**） | 七阶段链路 · **先核验后作词**铁律 · 13 项歌词闸 · 7 项音频 QC · -14 LUFS 目标 · 4 项局限 |
| `code-security-review` | 119 | security | deep-code-security | 三阶段流水线 · **置信度评分公式与阈值** · 强制沙箱隔离 9 条 · 抑制文件规范 · **14 项已知局限逐条照抄** · 使用纪律（仅自有资产） |

**三个技能都不含**：外部 MCP 调用 · 出网请求 · 密钥需求 · 可执行代码。
只含**判据与闸**，所以零供应链风险。

**落点**：`审美相关skill/skills/<name>/SKILL.md`（与现有 110 个同构，随仓库版本管理）。
> 注：要让它们被**自动发现**，需复制到托管技能目录 `~/.openclaw-autoclaw/skills/`。
> 这一步会动到工作区之外的目录 —— **未做，等主人点头。**

### 仍未做（等主人）
1. **`deep-code-security` 的许可确认** —— 未确认前只用判据、不用其代码
2. **是否复制到托管目录**使其自动加载
3. **是否走 MCP 挂载**（真要生成端时）—— 路已铺好且带门：`mcp_connect`/`mcp_call` 各要 `process_execute`
