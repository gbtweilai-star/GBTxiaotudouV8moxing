# Lobe UI Design System

> Category: AI / AIGC Chat Applications
> LobeHub 的开源组件库，面向 AIGC Web 应用（**此句改写自其 README 自述，非原文照搬**；原话见 §1）。Ant Design v6 基座、CSS-in-JS 令牌、对话优先的表面。
> **来源**：[`lobehub/lobe-ui`](https://github.com/lobehub/lobe-ui) · MIT · `@lobehub/ui` **v5.48.2** · 本件为**蒸馏件**，只抽机制、不搬文本。

## 0. 诚实分栏（先说清我读了什么，没读什么）

**读到的（一手，可复核）**：
- `package.json`（v5.48.2 · `license: MIT` · ESM only · `engines.node >= 22` · 全部依赖与 peerDependencies）
- `README.md`（用法、Provider 嵌套规则、i18n 用法、NextJS `transpilePackages` 要求）
- `src/` 目录树（组件清单，见 §3）

**没读到的（**不许当"它就是这样"**）**：
- ❌ **配色 / 圆角 / 间距 / 字体栈的具体数值** —— 我试了 `src/theme/token/index.ts`、`src/styles/token.ts` 两条路径**都是 404**。
  ⇒ 本件**一个色号都不给**。要抄它的视觉，请自行读 `src/styles/`（我只确认了该目录存在）。
- ❌ 任何 `.tsx` 实现、Storybook、`docs/`
- ❌ 它自述的"设计理念"原文（README 里没有这一节）

## 1. Visual Theme & Atmosphere（从依赖与组件清单**推断**，非原文）

AIGC 应用的**对话优先**界面：长时间阅读、流式输出、代码与多模态内容混排。
从它的依赖选择能读出四条取向（**推断，非文档自述**）：

1. **不自己造底座** —— 承认 Ant Design v6 为基座（peerDependency），自己只做 AIGC 特有的那一层；
2. **样式即 token** —— 用 `antd-style` 做 CSS-in-JS，而不是散落的 CSS 文件；
3. **动效是基础设施** —— `motion`（Framer Motion 后继）是 peer 依赖，且**必须由 `ConfigProvider` 注入**；
4. **为"流"而生** —— `streamdown` + `@shikijs/stream`（流式 markdown/代码高亮）、`virtua`（虚拟滚动）。

### Use Cases（它自己声明的适用面）
- AIGC Web 应用（对话、生成、助手）—— README 原话就是 "an open-source UI component library for building _AIGC_ web apps"
- 需要**长对话 + 流式渲染 + 代码块 + 多模态**的产品
- **不适用**：营销落地页、静态官网（它没有那类骨架）

### Prior Art
Ant Design（基座）· LobeChat（它的主消费方）· 同类：Vercel AI SDK 的 UI 层、shadcn 的 AI 组件。

## 2. Color

🔴 **未取到**（两条令牌路径均 404）。**不给推测色号** —— 猜出来的色号会被下游当事实用，那是本仓最贵的错。
已知的只有**机制**：
- `src/color/` 存在 ⇒ 有一层配色工具（依赖里有 `chroma-js` + `polished`，即**程序化配色**：从一个主色派生整套色阶）
- `src/brand/` 存在 ⇒ 品牌层独立于组件层
- `ThemeProvider` 与 `ThemeSwitch` 成对 ⇒ 明暗双模式是一等公民（且主题由 Provider 注入，非全局 CSS）

## 3. 组件清单（`src/` 目录树现读，可用于选型）

**AIGC 特有（值得直接学）**：
`EditorSlashMenu`（编辑器斜杠菜单）· `Snippet` · `CodeDiff` · `CodeEditor` · `EditableText` ·
`FluentEmoji` + `EmojiPicker` · `FileTypeIcon` · `CopyButton` / `DownloadButton` ·
`DraggablePanel` / `DraggableSideNav`（可拖拽/可缩放面板）· `ScrollShadow` · `Toc` · `Video`

**通用件（与 AntD 重叠但有自己的取法）**：
`ActionIcon` / `ActionIconGroup`（图标动作 + 分组，带 Tooltip）· `Block` / `Flex` /
`Avatar` · `Tag` · `Segmented` · `SearchBar` · `SortableList` · `SliderWithInput` ·
`ColorSwatches` · `Skeleton` · `Empty` · `Toast` · `Tooltip` · `ContextMenu` · `Drawer` ·
`SideNav` · `Burger` · `Freeze` · `FontLoader` · `ThemeSwitch` · `Form` / `FormModal`

**分组子入口**（package.json exports 现读）：
`/chat` · `/dashboard` · `/mobile` · `/mdx` · `/awesome` · `/base-ui` · `/brand` · `/color` · `/icons`

## 4. 三条**对我们直接有用**的机制（本轮就可落地）

| # | 机制 | 为什么对我们有用 |
|---|---|---|
| 1 | **`remark-cjk-friendly`**（依赖里真有它） | 我们的界面**全是中文**。中文没有词间空格，断行规则与拉丁文不同 —— 它专门解决**中文排版断行**。我们的面板正文（62em 行长）正需要这一条。 |
| 2 | **`virtua` 虚拟滚动** | 我们的审计流/能力位列表动辄上千条（`交流视野` 现读 1378 条），全量渲染会卡。虚拟列表是正解。 |
| 3 | **`ActionIcon` 图标动作** | 本仓面板的动作目前是**文字按钮**（"刷新/折叠/自检"）。图标+Tooltip 更省空间，也更容易排成组。 |

## 5. 一处**明确分歧**（如实并列，不假装一致）

它把 **FluentEmoji 当一等视觉资产**（有 `FluentEmoji` 组件、`EmojiPicker`、甚至 emoji 作为 package 依赖）。
而本仓 `gbt-aesthetic` §3.1 **P0-3 明令禁止 emoji 当 UI 图标**（理由是"一眼 AI 味"）。

**两条都留着，不折叠**：对话产品的表情反馈是产品语言（它是聊天应用，emoji 是内容不是图标）；
而我们的面板是**仪器**，仪器上放 emoji 就是错。**同一套规则不该跨场景硬套** —— 这比强行统一更有用。

## 6. 未验账（本件没验过什么）

| # | 没验什么 | 为什么 |
|---|---|---|
| 1 | **色值 / 圆角 / 间距 / 字体** | 两条令牌路径 404；**没猜** |
| 2 | 任何组件的**实际观感** | 没装、没跑、没截图（它需要 antd v6 + React 19 + motion 的工程） |
| 3 | 它的**无障碍与键盘路径** | 没读实现 |
| 4 | 与 AntD v6 的**破坏性变更** | 只知 peer 是 `antd ^6.1.1`，未核 API 差异 |
| 5 | 许可细节 | 只确认 `license: MIT`（package.json 现读）；未逐文件核头部声明 |
| 6 | **本件**喂不了**未来的 derive 脚本** | `_schema/AGENTS.md` 第 166-169 行交代：DESIGN.md 是 derive 脚本取 **A1 值（色阶 / 字阶）**的来源。而本件**一个色号、一个字阶都没有**（令牌路径 404，见 §0/§2）⇒ **它不可被机器取值**。这是**已知缺口**，不是隐瞒 —— 列在这里，免得将来有人跑脚本时以为漏了 |

## 7. 归属

[MIT](https://github.com/lobehub/lobe-ui/blob/master/LICENSE) © LobeHub。本件是**机制蒸馏**，不含其源码或文本片段。

**可复核**（本件自己的验收器，只读）：

```powershell
python .scratch\_verify_lobe_ui.py
```

它查九条：格式合**库内 150 个兄弟件现算出来的约定**（`# ` 标题 150/150 · `> Category:` 150/150 · `## N.` 147/150）、
MIT 归属、诚实分栏、未验账、署名、**自称不给色号就真没给**、无 ≥12 词未标注长句搬运；
另报两项**不参与红绿**的：derive 可用性（见未验账第 6 条）与 6–11 词灰色带（**只列给人看，不自动定罪**）。

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
