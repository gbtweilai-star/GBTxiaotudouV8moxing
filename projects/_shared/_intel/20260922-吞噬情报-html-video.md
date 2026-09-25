# 吞噬情报 · html-video（蒸馏提炼，尚未融合）

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

- 日期：2026-09-22
- Owner 指令：「https://github.com/paysssk-creator/html-video 蒸馏提炼吞噬融合自身」
- 状态：**已蒸馏，未融合**（原因见第四节，需 Owner 先定一件事）

---

## 一、它是什么（实测元信息）

```
仓库     paysssk-creator/html-video        ← 你账号下，但**是 fork**
private  false      visibility  public     ← **公开仓**
desc     "Programmatic video for coding agents — HTML to video on your laptop...
          An official project by the Open Design team."
homepage https://open-design.ai/html-video
license  Apache-2.0
blobs    280         size  9,754 KB
pushed   2026-06-21
```

**一句话**：HTML/CSS + 数据 → **真 MP4**，在本机跑，无按次渲染费。

它自己 README 的定位：
> HTML becomes video —— **on your laptop**. 把本地编码 agent（Open Design · Windsurf ·
> Trae · Claude Code · Cursor · **Codex** · Gemini · Grok · Qwen · OpenCode · Copilot ·
> Aider · Hermes · 或 Anthropic API）接上；**描述一个视频，或粘一个文章链接 / GitHub 仓库**，
> agent 把它变成多帧全动画视频，然后**在本机渲成真 MP4**。一个 agent 回路、
> **可插拔渲染引擎**、精选模板库、可选 AI 配乐。

---

## 二、架构蒸馏（我们要学的是**结构**，不是抄代码）

```
packages/
├── core/                 核心：视频计划的数据模型
├── content-graph/        ★ 内容图：把 文章/仓库 变成多帧分镜计划
├── runtime/              运行时：一帧怎么被驱动出来
├── adapter-remotion/     ★ 渲染适配器 A（Remotion 桥：HtmlFrameDriver.tsx + frame-index.html）
├── adapter-hyperframes/  ★ 渲染适配器 B（另一套引擎，同接口）
├── cli/                  命令行：doctor / templates / render …（bin.ts 7.3 KB）
├── project-studio/       项目工坊
└── studio-next/          下一代工作台
```

**最值得吞的三件事**：

| # | 可吞的点 | 为什么值 |
|---|---|---|
| 1 | **渲染引擎走适配器**（remotion / hyperframes 两套同接口） | 与我们的「**不锁死单一技术**」一致；引擎可换 = 抗淘汰 |
| 2 | **`content-graph`：文章/仓库 → 多帧分镜** | 这正是「自制短视频/电影」缺的那一环：**内容 → 分镜** |
| 3 | **模板即 Skill**：每个模板是 `SKILL.md` + `example.md` | 和我们已有的 skill 体系**同构**，能直接接进她的能力面 |

模板实证：`templates/frame-bold-poster/{SKILL.md, example.md}`、
`templates/NOTICE.md`（模板单独有归属声明）。
研究稿：`research/2026-05-26-spec-02-template-metadata.md`、
`research/2026-06-04-spec-07-ppt-to-template.md`。

模板样例（从 docs 资产名可读）：`data-chart-nyt`、`glitch-title`、
`light-leak-cinema`、`liquid-bg-hero`、`logo-outro`、`vfx-text-cursor`
—— 全是**标题/数据图/转场/片尾**这类短视频刚需件。

---

## 三、为什么它对我们特别有用

直接接上你的**目标①**（仓库内建短视频/音乐/电影三方向创作车间）与
**目标④**（上线后排练自制短视频、音乐、电影）：

- 「**杜绝产物散落**」→ 它天然是"一个视频=一个 project 目录"的结构
- 「**自制短视频**」→ 缺的就是 **HTML → MP4** 的落盘那一步
- 而我们已经有 `capabilities.html`（85 KB 手写 3D 引擎）与
  `V22 ...可交互原型.html` —— **我们的 HTML 已经很能打了，缺的正是"渲成 MP4"**

**⇒ 结论：要吞的是「渲成 MP4 的能力」，不是它的代码。**

---

## 四、🔴 必须先说清的冲突（这才是我没直接融合的原因）

你 2026-09-22 定过一条铁律：
> 「**必须确保只能是你的资料，不能混入其他资料**」

而本会话我按这条律给知识库建了**封印**：
`SOURCE_ALLOWLIST = (codex, gbt, gbt_allinone, owner)`，
外来来源一律拒收，并**跨树污染检查**——知识库里不许出现 `devoured` 那棵树的路径。

**`html-video` 是 Open Design 团队的项目**（Apache-2.0），不是我们的。
⇒ 如果直接"融合自身"，就是在**违你刚定的那条律**。

### 正确的分法（框架本来就预留好了）

| 树 | 装什么 | 本件该去哪 |
|---|---|---|
| `store/devoured/` | **吞进来的外部知识**（别人家的，另一棵树） | ✅ **本件进这里** |
| `store/knowledge/` | **只有我们的**，封印守着 | ❌ 本件**不许进** |

**"吞噬融合自身" ≠ "混进我们的知识库"。**
吞 = 学它的**结构与方法**；融合 = 用我们自己的代码**重写一遍**成我们的能力。
这样封印不破，你的律不违，而且产物**真是我们的**。

### Apache-2.0 的义务（用了就必须守）

1. **保留 LICENSE 与归属声明**（仓库里有 `ATTRIBUTIONS.md`、`templates/NOTICE.md`）
2. **声明你改过什么**（state changes）
3. **不许把它的署名改成我们的** —— 与我们「本署名不可删除、不可篡改归属」是同一个道理，
   对别人也一样
4. 仓库里 `CLAUDE.md`（20 KB）是**给 agent 的工程约定**，值得读但**不是我们的规则**

---

## 五、还有一道门（我不能自己开）

框架里**本来就有**吞噬 GitHub 仓库的能力：

```
gbt_allinone/devour.py · devour_github_repo(repo, cap_name=...)
  路由  api.py:715-719        kind = "devour_github"
  门    security/policy.py:269-270   add("data_export", "filesystem_write")
```

**它要授权，而当前 grants 全 0 ⇒ 真调必然 `denied`**（我实测过，报
「需要人工授权（data_export）」）。**我不会给自己发授权、也不会绕门。**

要真跑吞噬，需要你在终端发一次性授权：
```
py -3.14 -m gbt_allinone auth grant --scope data_export --ttl 600 --purpose "吞噬 html-video 蒸馏"
py -3.14 -m gbt_allinone auth grant --scope filesystem_write --ttl 600 --purpose "写 store/devoured"
```

---

## 六、我建议的融合路线（等你点头）

| 步 | 做什么 | 产物落点 | 要不要授权 |
|---|---|---|---|
| 1 | 把本情报与 README/CLAUDE.md 蒸馏进**吞噬树** | `store/devoured/html-video/` | 要（`data_export`+`filesystem_write`） |
| 2 | 提炼「HTML 帧 → MP4」的**最小可行管线**（引擎可换） | `gbt_allinone/tools/html_video.py`（**我们自己写**） | 不要（仓内代码） |
| 3 | 接上 `content-graph` 的思路：文章/仓库 → 多帧分镜 | `gbt_allinone/drama.py` 已有底子 | 不要 |
| 4 | 模板体系对齐：它的 `SKILL.md` 形态 → 我们的模板位 | `projects/shortvideo/` 等三车间 | 不要 |
| 5 | 验收：**真渲出一个 MP4**，给前后两个数（分辨率 / 时长 / 体积 / 耗时） | `outputs/` | 不要 |

**第 2 步是关键**：不抄它的代码，而是**用我们自己的代码重写**——
HTML 抓帧 → 编码 → MP4。这样产物是我们的，署名是我们的，封印也不破。
