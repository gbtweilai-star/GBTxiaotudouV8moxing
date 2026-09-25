# gbt-master · GBT小土豆V8 总面板（DSH 本地插件）

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
>
> **现役：`gbt-potato-master-v9` · 源稿 v1.8.1（进程须知：宿主半边在进程启动时装载，
> 🔴 重启前 `/gbt-master` 仍会自报 `v1.8.0` —— 那是「还没重启」，不是「改坏了」）· 面板登记表 12 条（在 12 / 12）**
> 换代口径见下面「第五节 · 换代码 = 换 specifier」；包名不是装饰，是**热换代的机关**。
> 🔴 **但换代清理有一条比"清理律"更高的前提**：**删旧代之前必须先重启 DSH**
> —— 加载器把 package metadata **按 specifier 缓存到进程重启**，删了会让还活着的进程整页插件加载失败
> （2026-09-22 实测红字错页）。现在 `node_modules` 里 `v6`（`plugins/gbt-master-compat-v6` 空转兼容壳）
> / `v8`（保留）/ `v9`（现役）**三代并存**，这是**故意的**，不是没清理干净。
> 品牌两格（single 槽）的 A/B 结论与自报诊断见「第 4.6 节」。

**口径（Owner 2026-09-22 定，v1.1.0 已按此纠正）：原面板保持原样，只往上加装能力。**

- 入口**只装在会话头那一行**（`conversation.session.header.utilities`，追加式）：`面板`（就地内嵌浮层打开面板窗，列出工作区全部可视化面板）与 `GBT小土豆 · 上帝视角`（同一浮层、预选 W3，装在该行最右）。
- **不另起中央面板、不占左栏图标位**（v1.0.x 曾做成一块独立「总面板」页 + 左栏图标 —— 那是**偏离**，已撤；旧版留档已按 Owner 要求**删除，不再保留**）。
- 品牌加装：左栏品牌行的标/名、新会话大标题上的品牌标、面板头 52px。
- 只走 DSH 公开扩展位（`conversation.session.header.utilities` / `conversation.hero.brand.mark` / `sidebar.brand.mark` / `sidebar.brand.name` / `webServer.register`），**不改 DSH 一行源码**，不发布任何 Cordis 服务。

## 面板登记表（现役 12 条 · 在 12 / 12）

| # | id | 面板 | 文件 | 说明 |
|---|---|---|---|---|
| 01 | `index` | 可视化面板总索引 | `index.html` | 台账**打开即现读** `/gbt-master`，不写死 |
| 02 | `caps` | 能力球 · 能力台 | `capabilities.html` | 158 项能力铺真 3D 球面 · `apiShim` |
| 03 | `w3` | 上帝视角 W3 | `holo_pet_w3/index.html` | 六页签驾驶舱（宿主内是静态壳+如实降级） |
| 04 | `h1` | 赏金台 · h1mcp | `holo_pet_w3/h1/index.html` | 本机只读 · `apiShim` · 凭据只报已配/未配 |
| 05 | `brain` | 大脑执行层 · 五维合一 | `brain.html` | AST 现算结构 · `apiShim` |
| 06 | `pet` | 主控台 W1 · 数字人面板 | `holo_pet/index.html` | `apiShim` · 3D 形象走 `raw/rig/model-rigged-anim.glb` |
| 07 | `avatar` | **数字人形象页（成品）** | `holo_pet/assets/digital-human/web/avatar.html` | `?model=bust` 换半身件；两件都在 12 MB 上限内 |
| 08 | `v22` | V22 可交互原型 | `V22 GBT小土豆V8-可交互原型.html` | 交付物 · 单文件 |
| 09 | `v22c` | V22 无限画布 | `V22 GBT小土豆V8-无限画布.html` | 自由画布 |
| 10 | `hitl` | HITL#1 审批屏 | `projects/_shared/templates/20260921-三方向-HITL1审批屏.html` | 链状态 + 逐镜待填 + 闸口表 |
| 11 | `form` | 分镜契约填写页 | `projects/_shared/templates/20260921-三方向-HITL1-分镜契约填写页.html` | 85 格契约表单 |
| 12 | `deploy` | 部署版入口 | `deploy/index.html` | 与根上 V22 同源 |

## 文件

| 文件 | 作用 |
|---|---|
| `package.json` | 包声明：`name=gbt-potato-master-v8`（**包名即 specifier**）；`main` = 宿主半边；`exports["./client"]` = 浏览器半边；`dsh.client.platform = web` |
| `lib/host.js` | 宿主半边：`/gbt-master` 目录 JSON（精确路由）+ `/gbt-master/heal.js` 自愈器（**每次现读磁盘上的 `lib/heal.js`**）+ `/gbt-master/api/*` 内嵌反代 + `/gbt-master/fs/*` 只读白名单静态路由（前缀） |
| `lib/client.js` | 浏览器半边：已构建 bundle（`window.__ModuleLoader__` 形态），会话头两个加装入口 + 浮层 + 三处品牌位 + 八个旧 id 的无副作用空壳 |
| `lib/heal.js` | **首页自愈器（在磁盘上，不随换代走）**：页面自带世代戳 vs 宿主现报世代，不一致就自己刷一次；带节流与上限 |
| `tools/cross-scan.py` | **穿透式交叉扫描**（四层：登记表 / 路由 / 运行时 / 数据层）—— 一键判「能力接上没有」 |
| `tools/verify-host.mjs` | 进程外真跑验宿主（反代 / 白名单 / 同源改写注入，含负对照） |
| `tools/verify-client-apply.mjs` | **无头验收浏览器半边**：把真 bundle 装进假装载器跑 `apply()`，断言 6 个插槽都注册上、品牌两格是同一层嵌套、防"挤在一起"的 CSS 都在 |

## 第 4.5 节 · 🔴 首页自愈：换代之后**真的不再需要人按 F5**（v1.7.0 定型）

**病史**：这一轮换代码换了 8 代（v1 → v8），每换一次，**已经开着的那张页面**整片入口与品牌位就消失。
中途做过一版"世代感知自愈"，**那一版是错的**，已删（本节目的是别让后来的人再走回去）：

| 错在哪 | 事实 |
|---|---|
| 把 `EXPECT_GEN`（宿主自己的包名）**写进注入文本** | 注入文本**跟着首页一起发下去**，页面一加载就固定成"当时那一代"的常量 |
| 拿页面的 `dataset.gbtGen` 跟那个常量比 | 对一张 v6 页面：自带的 GEN 是 v6、自己的戳也是 v6 ⇒ **自比恒等，自愈永不触发** |
| 于是 v6→v7 换代后 | Owner 那张页面卡在旧包（左栏还是官方品牌行），而注入侧日志一切正常 —— **报告层是绿的，事实是没救到** |
| 第二层病根 | 注入文本本身也在包里 ⇒ **改自愈逻辑又要换一代**（specifier 变了才重新 import）⇒"自愈"每次修都得求人按 F5 |

**现在的修法（两条一起断根，别再退回上表写法）**：

1. 注入进 HTML 的只剩**一行永不改变的标签**：
   `<script src="/gbt-master/heal.js" defer></script>`
   —— 判据与节流住在磁盘上的 `lib/heal.js`，由宿主**每次现读**发出去
   （实测：路由发出去的内容与磁盘文件**逐字节相同**）。
2. 判据改成 **"页面自己的戳" vs "宿主现报的 `plugin`"**：
   `dataset.gbtGen` 只由**当前这一代 bundle 的 `apply()`** 打上，宿主那栏是现读的
   ⇒ **任何旧页面都能认出自己旧了**（这正是旧写法做不到的那一步）。

⇒ 以后改自愈逻辑**只改 `lib/heal.js`**：不换代、不重装、不用求人按 F5。

**安全边界（写死，别放松）**：

| 边界 | 为什么 |
|---|---|
| 只在 `/gbt-master` **答 200** 时才动 | 插件被撤掉则整段失效，绝不惹事 |
| **最多自愈 3 次**、两次之间 ≥60 秒 | 物理上不可能变成刷新循环 |
| 世代对上**且入口在**才把计数清零 | 恢复正常后不残留计数 |
| `?gbt_noheal=1` 时不介入 | 留一个人为关闭的口子 |
| 全程 `try/catch`、不定义全局 | 不碰别人的东西 |
| **必须绑着 `webServer` 调**（`webServer.tapIndex(...)`） | 摘下来裸调会丢 `this`，注册表是服务实例上的字段 |

**唯一还需要人按一次 F5 的场合**：页面是**在本次换代之前**加载的，而且它带的是**旧版注入器**
（旧注入器只会自比 ⇒ 救不了自己）。**刷过这一次之后，以后换代它自己会刷。**

⚠️ 诚实口径：SPA 首页要 DSH 鉴权，**我这一侧取不到**（实测 401）。
所以"注入标签是否真的落到那页 HTML 上"，我这一侧不能直接看；能直接看的是
**路由那一半**（`/gbt-master/heal.js` 200 且与磁盘一致，已实测），**另一半由你刷新后的现象确认**。

## 第 4.6 节 · 🔴 左栏品牌两格（single 槽）为什么一直不生效 —— A/B 实测 + 自报诊断（v1.8.0 定形；v1.8.1 未动形态）

**病史**：v1.0.x 起就注册 `sidebar.brand.mark` / `sidebar.brand.name`，三代（v6 / v7 / v8）
都"以为注册上了"，**实测左栏始终是官方那条**（`deepseek HARNESS`）。中间的弯路与结论都记在这里，
**别再照旧稿推**：

| 曾经的判断 | 实测结果 |
|---|---|
| "v6 平铺两个 inject 是错的，官方用的是嵌套+生成器 ⇒ 改回官方写法就好" | **不成立**：v8 用的就是官方那套嵌套+生成器，**左栏两格仍然不生效** |
| "插槽检查器能看出是谁占着" | **不能**：本构建里 `registrant` 是**通用标签** —— 实测头部 4 条、浮层那条（确定是我们的 `gbt-panel-layer`）、品牌那条，**全是 `Ba`** |
| "single 槽被官方占了，deployment 顶不掉" | **能顶掉**：见下面的 A/B |

**A/B（2026-09-22，判据不靠猜）**：

1. 起一个**临时动态 Cordis 件**（`brand-1/pkg-1`，client 半边），用**普通函数**注入注册两格
   ⇒ 插槽检查器（只读）显示 `dyn/brand-1` **`active: true`**、官方那条转 **`active: false`**；
   **截图确认左栏变成 `GBT小土豆V8`**。
2. **停掉**该动态件 ⇒ 左栏**立刻退回**官方 `deepseek HARNESS`，插槽里又只剩官方那条。

⇒ 两条硬结论：**① single 槽可以被后注册者顶上（后注册的 active，先前的转 inactive）；
② 我们的静态包在这两个槽上从来没占上**（头部 `list` 槽 + `shell.overlay` 都进得去 ⇒ apply 确实跑了）。
v1.8.0 据此把形态改成**两格各自独立、普通函数**（唯一在实测里成功占位的形态）。

**自报诊断（查不出原因就别再猜）**：客户端每一步注册进 `try/catch`，结果两条路出去 ——
① 写进**页面标题** `[gbt] …`（截图肉眼可见）；② `POST /gbt-master/diag`，宿主存内存，
由 `/gbt-master` 的 **`clientDiag`** 字段读回（**免鉴权 HTTP，一条 GET 就能读，不用截图、不用桌面授权**）。
`clientDiag: null` = 那张页面还没按本代加载（要一次 F5）。

**验收器判据也跟着改了**：`tools/verify-client-apply.mjs` 原先断言"品牌两格必须是同一层嵌套的一组注册"
—— 那是在照**已被推翻**的假设判红，现改为：**两格都注册上 + 自报诊断挂钩在**（`/gbt-master/diag`）。

### 4.7 注入上下文的两处报告层假绿（2026-09-22 已修 + 已配闸）

这两处**不会让任何命令报错**，但会让**每一轮重启的模型读错事实**，所以单列：

| # | 病灶 | 后果 | 修法 |
|---|---|---|---|
| ① | `renderSnapshot` 里**写死**"左栏品牌行＝土豆 Logo + GBT小土豆V8" | 把"部署就绪"讲成"已生效"（同一份 payload 的 `clientDiag: null` 就是反证） | 按 `clientDiag` 分**三分支**：null → "尚未在任何页面生效（要一次 F5）"；`gen === gbt-potato-master-v9` → "已按本代加载（附诊断时间）"；gen 不符 → "与本代不符，那张页面是别的世代" |
| ② | `renderDhState` 读 `v.readings.joints/.vertices`，而状态源 `STATUS.json` 里是**平铺**的 `joints: 29 · verts: 16017 · textures_mb: 4.0` | 注入文本长期写着「关节 undefined · 顶点 undefined · 贴图 undefinedMB」——**看着像资产读数坏了**（假红），其实是读错了路径 | 两种形态都认（有 `readings` 就用它、否则用平铺字段），且**任何缺值写「（未写）」**，绝不注入 `undefined` |

**闸**：`node plugins/gbt-master/tools/verify-context-blocks.mjs`
（从 `lib/host.js` **现读抽函数体**，用真 `STATUS.json` 与三种 `clientDiag` 情形各跑一遍 →
断言"不许出现 `undefined`、数字必须与状态源一致、三分支说法必须互不相同"）。
第一版闸自己写死了参数名（`state, at`）抽 `renderSnapshot(payload, at)` 当场 `ReferenceError` —— **闸也要被测**。

⚠️ 两处修正都在**宿主半边**，而宿主半边是**进程启动时装载**的 ⇒ **下次 DSH 重启才生效**（不是热更新）。

### 4.8 🔴 改工作区源稿 ≠ 生效：装机副本会漂移（2026-09-22 现读实锤 + 已配闸）

DSH 按组合行的 `name:`（`gbt-potato-master-v9`）去 **profile 的 `node_modules`** 里解析包，
而那份是 `file:` 依赖装出来的**副本**（不是链接）。实测漂移：

| 文件 | 源稿 | profile 装机副本 | 差在哪 |
|---|---|---|---|
| `lib/host.js` | 30,378 B / 549 行 | 27,867 B / 516 行 | **少 33 行**：§4.7 的两处修正一行都没有 |
| `lib/heal.js` | 含 `setInterval` ×2 | **0 次** | 装机那份是**没有 60s 复查**的旧版 |
| `tools/verify-context-blocks.mjs` | 在 | **根本没有** | 新闸没装进去 |
| `README.md` / `tools/verify-client-apply.mjs` | — | 旧版 | 判据改动没同步 |

⇒ **光改工作区源稿、重启也不会生效**（重启加载的还是那份旧副本）。这类漂移不报错、不红页，
只会"看起来改了、其实没改" —— 与"技能根漂移"、"注入上下文假绿"同族，**根都是"源与在跑的那份不是一份"**。

**闸**：`node plugins/gbt-master/tools/verify-installed-copy.mjs`
（扫 `~/.dsh/profiles/*/node_modules/gbt-potato-master-*`，与 `plugins/gbt-master/**` 逐文件比 sha256）。

**一条命令跑完宿主插件的三道门**：`node plugins/gbt-master/tools/verify-all.mjs`
= ① 浏览器半边（bundle/插槽/品牌/诊断挂钩/CSS）· ② 注入上下文（不许 `undefined` · 数字同源 · 品牌三分支）·
③ 装机副本（源稿 vs DSH 真正加载的那份）。现读三门全过。

**⏳ 等重启后做的清理（本次只报不动，写在这是因为它是"换代纪律"的一部分）**：

1. profile `package.json` 里 `gbt-potato-master-v8` 指向的就是 v9 那个目录
   ⇒ `node_modules/gbt-potato-master-v8/package.json` 的 `name` 是 **v9**（specifier 与包名不符，
   闸会以 ⚠ 报出）。加载器按"解析出来的 manifest 包名"认浏览器模块，**这条等重启后清掉**。
2. 同理 `gbt-potato-master-v6`（`plugins/gbt-master-compat-v6` 空转壳）也只在**删旧代之前必须先重启**的
   纪律下保留；重启后若 `/gbt-master` 与品牌一切正常，可连同 v7/v8 的 specifier 一起收掉。
3. **顺序不能反**：先重启（让加载器忘掉旧 specifier 缓存）→ 再删依赖与目录。反了就是那次红页事故。

### 4.9 面板里的"写死读数"（2026-09-22 修 · 能力球那一个）

**病灶**：`capabilities.html` 把能力清单与五个图例数字**全写死在 HTML 里**：

| 写死的 | 当时的值 | 现读 |
|---|---|---|
| `const CAPS=[…]` | 183 条（registry 158 + ark 25） | 接口四条通道：registry **158** · app_routes 26 · app_pending 1 · **ark 25**（`total_all_channels 210`） |
| 提示语 | 「183 项能力 / 31 个域」 | 同上（数字本身没错，但它**不会跟着变**） |
| 图例 | 免卡 92 · 要授权 27 · 桩 28 · 禁用 11 · Ark 25 | 免卡 **106** · 要授权 **13** · 桩 28 · 禁用 11 · Ark 25 |

⇒ 面板自称"现读"却在**冻结**：注册表一变，球上就画着已经不在的条目、而新长出来的它没有。

**修法（三层，缺一层都不够）**：
1. 内嵌清单改名 `CAPS_SNAPSHOT`，**只当外观字典与离线兜底**（`domain_cn` / `handler` / `risk` / `stub` 这些只有注册表知道）；
2. `rebuild(list)` 把球面几何（nodes / domDir / LINKS）抽成一个函数，**快照与现读共用同一条铺法**；
3. 打开就 `fetch('/api/capabilities')` → **以现读为准重建**：
   - 注册表 `items` + **Ark `app.ark.skills` 两条通道都并**（第一版只并了 `items`，少画 25 个紫环、
     还错报"25 条已不在现读面"—— 接口原文写着「`total` 只数第一条，别拿它当全量」，**我漏读了**）；
   - 现读说 `enabled:false` 的一律判 `disabled`；`stub` 保留快照分类；其余按 `needs_confirmation` 分 free/guarded；
   - 只在快照里的 → **不画**并如实计数；取不到现读 → 保持快照并在提示语写「快照 · 取不到现读」。
4. 数字**全部由 `updateCounts()` 现算**（页面里再不许出现手抄的 183/31/92/27/28/25），
   并自报 `window.__gbtPanelCaps` 给验收器读。

**两道新闸**：

| 闸 | 干什么 | 现读 |
|---|---|---|
| `check-panel-syntax.py --all` | 把 12 个面板的**内联 JS** 抽出来逐段 `node --check`（跳过 `importmap` 那种 JSON） | 12/12 通过 |
| `verify-panel-live.py` | 真 Chrome 打开 `/gbt-master/fs/capabilities.html`，读页面自报，与 `/api/capabilities` 逐项对（count / 域数 / 禁用数 / Ark 数 / 有无报错） | **一致**：`source=live · count=183（注册表 158 + Ark 25）· domains=31 · hidden=0 · external=25` |

> 教训写死：**面板是手写单文件 HTML，没有编译期兜底**；改一行 JS 只会白屏，而白屏在 `/gbt-master`
> 目录里看不出来（`exists=true`、`size` 正常）。所以"改面板"必须配**语法闸 + 真浏览器验收**两条。

### 4.10 🔴 产物被手补、生成器不知道 —— 以及 12 个面板的"出身"清单（2026-09-22）

**同一课的第二遍**：§4.9 我把 `capabilities.html` 改好了，但它**是生成物** ——
生成器 `tools/codex-scripts/make_capability_console.py` 里的模板仍写着
`const CAPS=__CAPS__;` + 生成时算好的提示语/图例数字 ⇒ **下次一重新生成，我的手改就被冲掉，面板又变回冻结**。
（这个坑上一轮已经踩过一次：favicon 也是手补在产物上、一生成就丢，模板注释里留着那句教训。）

**修法**：把"现读重建"整段**挪进生成器模板**（`JS` 里），并给生成器加 `--check`：

| 命令 | 作用 | 现读 |
|---|---|---|
| `py -3.14 tools/codex-scripts/make_capability_console.py` | 现算快照 + 生成产物 | 85,203 字 |
| `py -3.14 tools/codex-scripts/make_capability_console.py --check` | **产物是不是这个模板生成的**（临时生成再逐字符比） | ✅ 一致 |

**12 个面板的出身（谁有生成器、谁没有）**：

| 面板 | 出身 | 有 `--check` 吗 |
|---|---|---|
| `capabilities.html` | `make_capability_console.py` | ✅ |
| `index.html` | `make_workspace_index.py` | ✅（2026-09-22 补） |
| `projects/_shared/templates/2026…HITL1审批屏.html` | `make_hitl1_screen.py` | ✅（同日补） |
| `projects/_shared/templates/2026…分镜契约填写页.html` | `make_storyboard_fill_page.py` | ✅（同日补） |
| `V22 …可交互原型.html` / `V22 …无限画布.html` | **手工演进**（祖先是 `build_v21.py`，**没有 build_v22**） | — |
| `brain.html` · `holo_pet/index.html` · `avatar.html` · `holo_pet_w3/**` · `deploy/index.html` | 手写 | — |

**四张生成页的现读状态（2026-09-22 补齐 `--check` 后逐个验过）**：

| 页 | 补 `--check` 时抓到的漂移 | 处置 |
|---|---|---|
| `index.html` | 盘上 23,349 字 vs 生成 17,768 字 —— **整段"台账现读"脚本（65 行）+ favicon + 3 张卡片 + 富文本描述都只在产物里** | 全部**挪进模板** → 重新生成 → `--check` ✅ |
| HITL 审批屏 | 差 **244 字**：一行 favicon **只补在产物上** | 挪进模板 → ✅ |
| HITL 填写页 | 同上（同样的 244 字） | 同上 ✅ |
| `capabilities.html` | （上一轮已处理）现读重建 + favicon | ✅ |

> ⚠️ **这四页是同一种病的四个病人**：产物被手补、模板不知道。区别只是补的东西大小不同
> （能力球是"现读重建"整段、总索引是"台账现读"整段、两页 HITL 只是一行 favicon）。
> 所以 §4.10 那条规则不是理论：**改产物必须同时改模板**，否则 `--check` 会一直红给你看。
>
> ⚠️ **生成顺序有依赖**：`index.html` 的卡片里写着各面板的**生成时字节数**（无 JS 时的兜底），
> 所以**任何面板重新生成之后，要最后再跑一次 `make_workspace_index.py`**，否则它的 `--check` 会红
> （页面本身打开时仍会从 `/gbt-master` 现读覆盖这些数字，但产物与模板对不上就是漂移）。

**页面现读一致性的两道真浏览器闸**：

| 闸 | 干什么 | 现读 |
|---|---|---|
| `plugins/gbt-master/tools/verify-panel-live.py` | 能力球：页面自报 vs `/api/capabilities`（count/域/禁用/Ark/报错） | ✅ 一致 |
| `plugins/gbt-master/tools/verify-index-panel.py` | 总索引：台账 vs `/gbt-master`（PANELS/RENDERS/MISSING/卡片逐条） | ✅ 一致（卡片 11 = 登记 12 减去本页自己） |

### 4.11 🔴 扫描器自己的报告层故障：把"慢"读成"坏"（2026-09-22 修）

`tools/cross-scan.py` 的运行时层原来**固定等 5 秒**就抓页面文字。于是数字人形象页
（3.96 MB GLB + three.js 解析，实测要约 15–20 秒才出读数）被抓成：

```
[avatar] http=200 ... 数字人 · — · 状态机 — · FPS 144 顶点 — · 三角形 — · 关…
```

**看着像页面坏了，其实只是还没加载完。** 修法三步（都是被自己的读数打回来的）：

| 版本 | 判据 | 结果 |
|---|---|---|
| v1 | 固定 5s | 误报「顶点 —」 |
| v2 | 加"文字连续两次不变"就早退 | **仍然误报** —— 慢加载页在加载期间文字长度可以长期不变 |
| v3 | 先认"页面**还欠着**的信号"（有 `#verts` 但没数字 / 有 `#live-src` 但还不是 LIVE / 有 `#hint` 但 `__gbtPanelCaps` 还没出）⇒ **欠着就不许早退**，上限 30s；并把 `settle=…ms` 打进读数 | ✅ avatar `settle=12500ms` 且给出真读数（顶点 16,017 · 关节 29 · idle · 弹簧偏角 3.1°）；index `settle=12500ms` 且 `PANELS 12`；其余页 8000ms 快路径 |

⚠️ 中间还踩一次：v2 里把 `window.__painted` 当就绪信号 —— 那是"**画过第一帧**"不是"**加载完**"，
数字人页一加载就满足 ⇒ 误报原样留着。**就绪信号必须是"内容级"的，不是"画布级"的。**

**最新一次全量扫描（真 Chrome，四层）**：登记表三份一致 12 条 · 路由 12/12 = 200 且字节对得上 ·
运行时 12 页 **err=0 / bad=0** · 数据层现读 26 条端点（只读真打 11 全通 + 会改状态 14 条静态对账 + SSE 通 +
POST body 到达上游）。落盘 `.scratch/_cross_scan_panels.json`（约 140 s）。

### 4.12 🔴 目录路由是 N+1 顺序等待：4.8 KB 的 JSON 要 8–10 秒（2026-09-22 修）

**怎么发现的**：几支验收器（`check-panel-syntax --all`、`verify-index-panel`）**偶发**报"取不到面板目录 / 超时"。
按项目规矩先怀疑门 —— 直接连测 6 次 `/gbt-master`：

```
#1 10.15s · #2 10.07s · #3 9.02s · #4 8.12s · #5 8.24s · #6 8.55s     （响应体都只有 4,794 B）
```

**不是负载，是稳定的慢。** 根因在宿主半边 `catalog()`：

| 事实 | 读数 |
|---|---|
| 它对 12 个面板**逐个 `await statOf()`**，每个 `statOf` 又是 `await fs.resolve()` + `await fs.stat()` | 24 次顺序往返 |
| 再加 `await fs.listDir(await fs.resolve(render/))` | 又 2 次顺序往返 |
| ⇒ 合计 | **26 次 `fs` 服务顺序 await** |

后果不止"慢"：总索引页的台账要等它、能力球的现读对齐要等它，**验收器的前置取数会偶发超时**。

**修法**：这些 stat **彼此独立** ⇒ 一次 `Promise.all` 并发取（renders 计数也并进去），
把 N 个来回压成一个来回。**A/B 实测（同一支门、同一打桩延迟 600 ms/次、同样 54 次调用）**：

| | 耗时 | 结论 |
|---|---|---|
| 改前（装机副本 = 现役运行的代码） | **15,716 ms** | 🔴 顺序（exit 1） |
| 改后（源稿） | **1,211 ms** | ✅ 并行（exit 0） |

**门**：`plugins/gbt-master/tools/verify-catalog-latency.mjs`
—— 把 `fs` 服务打桩成固定延迟，跑**真实的路由处理器**，断言 `elapsed < 4 × 延迟`
（顺序 ≈ 13×延迟，并行 ≈ 1×延迟，阈值离两头都远）。可指向任意 host.js 做改前/改后对照：

```powershell
node plugins\gbt-master\tools\verify-catalog-latency.mjs                                   # 测源稿
node plugins\gbt-master\tools\verify-catalog-latency.mjs <装机副本>\lib\host.js            # 测装机副本
```

⚠️ **生效时机**：宿主半边是**进程启动时装载**的 ⇒ 这次提速要**下次 DSH 重启**才落到正在跑的进程上；
装机副本已同步（`verify-installed-copy.mjs --fix`），重启后即时生效。

### 4.13 ✅ 品牌位问题结案 + 重启后验收单（2026-09-22）

**① 品牌位：页面自己报了"三处都成"**（这是等了两轮的那份证据）

`/gbt-master` 的 `clientDiag` 现读：

```json
{"at": "2026-09-22T17:29:34.695Z", "gen": "gbt-potato-master-v9",
 "diag": ["hero:ok", "sideMark:ok", "sideName:ok"]}
```

即：**某张 v9 页面在 17:29:34 加载后，三处品牌位全部注册成功** ——
`conversation.hero.brand.mark`（新会话大标题标）· `sidebar.brand.mark`（左栏标）· `sidebar.brand.name`（左栏名）。
独立的第二条证据：插槽检查器现读 `sidebar.brand.name` 只有**一个 occupant 且 `active: true`**
（`registrant` 仍是通用 `Ba`，所以单看它认不出是谁 —— 两条合起来才成立）。

⇒ 结案：**"两格各自独立、普通函数"这个形态是对的**（§4.6 的 A/B 判断得到页面自报的确认）。

**② 宿主代码改了必须动版本号（新增纪律）**

宿主半边在**进程启动时装载**，所以"现在跑的是哪一版"只能靠它自报。本版把 `version` 从 `1.8.0` 提到 **`1.8.1`**
（含 §4.7 两处报告层修正 + §4.12 目录路由并发）—— `/gbt-master` 的 `version` 字段就是那个信号。

**③ 一条命令看"重启到位没有"**：`plugins/gbt-master/tools/verify-after-restart.py`

| 项 | 判据 | 2026-09-22 现读 |
|---|---|---|
| ① 宿主机代码换代 | `/gbt-master` 的 `version`（源稿 1.8.1） | ⏳ 进程仍报 **1.8.0** ⇒ 还没重启 |
| ② 目录路由提速 | 同一请求耗时（旧 13 顺序 await ≈8–10 s） | ⏳ 本次 **7.84 s** ⇒ 旧实现仍在跑 |
| ③ 品牌位真的生效 | `clientDiag` 三项 ok（**页面自报**） | ✅ hero/sideMark/sideName 全 ok |
| ④ 注入上下文是新文案 | 装机副本装进假 ctx 实跑：三分支文案在、无 `undefined` | ✅ |
| ⑤ 旧 specifier 已清（可选） | profile 依赖里 v6/v8 是否还在 | ⏳ 还在 —— **必须先重启再清**（§4.8） |

⇒ 现在跑一次是 **exit 1**（三项 ⏳）；重启后再跑应是 **exit 0**。**这份单子就是"主人动手之后该看什么"。**

**顺带纠一处夸大**：面板清单里 `deploy` 那条原来写「与根上 V22 **同源**」——
现读是 **V21 代快照**（落盘 09-21 18:58，与根上 V22 有 **39 行差**），而且页内自称 V21
（76 处 V21 / 0 处 V22）—— "V22" 是**文件名上的称呼**，内容是手工演进的 V21 底座。已改成如实描述。

**规则（写给下一次改面板的人）**：
1. **改产物必须同时改模板**，否则 `--check` 会红 —— 这道红不是噪声，是"你手补的东西活不过下一次生成"。
2. 任何"写死的数字"都不许留在产物里（提示语 / 图例 / 快照条数）——**数字一律现算**。
3. 手写的面板没有生成器，改完**必须过语法闸 + 真浏览器验收**。
4. `deploy/` 是**外网写入**的落点：要同步 V22 先问主人（不在本轮范围内）。

## 第五节 · 换代码 = 换 specifier（不重启换代 · 实测路径）

**依据是 DSH 官方原文**（`@deepseek-ai/dsh-client-modules/README.md`）：

> 「Package metadata is cached per Loader specifier and owning-tree base URL **until restart**,
> while the resolved **manifest package name** identifies the browser module.」

⇒ 同一个 specifier 改源码**不会**重新 import（实测换入口文件、`disabled:true`→再启用，都无效）。
唯一不重启就换代的办法：**换包名 / 换组合行的 `name`**。本包因此走过八代：
`gbt-master` → `gbt-potato-master` → `-v2` → … → `-v7` → **`gbt-potato-master-v8`（现役）**。

换代四步（照做）：

```powershell
$DSH="$env:LOCALAPPDATA\npm-cache\_npx\1e7f6d9597241db0\node_modules\@deepseek-ai\dsh\lib\bin.js"

# ① 改工作区 package.json 的 name（新世代名），并同步 lib/client.js 里 bundle 的 id + STYLE_ID
#    旧 id 在 bundle 顶部用 __gbtStub('<旧id>') 留**无副作用空壳**，页面不会报"找不到模块"

# ② 装进 web profile（file: 让包落在 profile 树内；link: 名册不认）
node $DSH plugin --profile web add "file:C:/Users/ADMIN/Desktop/GBT小土豆V8/plugins/gbt-master"

# ③ 改组合行的 name → 新世代名（patchReload: live，存盘即热重组，秒级生效）
#    ~/.dsh/profiles/web/cordis.patch.yml → - insert: [{id: gbt-master, name: '<新世代名>', ...}]

# ④ 清掉上一世代（部署后清理律：没清 = 这次部署没完）
node $DSH plugin --profile web remove <上一世代名>
```

**生效条件：服务端热重组（③ 一存就生效）+ 浏览器 F5 一次**（客户端模块随页面引导载荷入册，
已开着的页面不会凭空多出一行；`dsh-client-hmr` 只管"已存在模块被重建"）。

## 怎么挂上去的（可复现）

```powershell
# ① 装进 web profile —— 必须用 file:，让包落在 profile 树内
#    （浏览器名册只扫树内包；用 link: 把真身指到树外，名册里就没有这一条，bundle 拿不到）
node "$env:LOCALAPPDATA\npm-cache\_npx\1e7f6d9597241db0\node_modules\@deepseek-ai\dsh\lib\bin.js" plugin --profile web add "file:C:/Users/ADMIN/Desktop/GBT小土豆V8/plugins/gbt-master"

# ② 组合行写进用户补丁层（该 profile 是 patchReload: live）
#    ~/.dsh/profiles/web/cordis.patch.yml
- insert:
    - id: gbt-master
      name: 'gbt-potato-master'
      config:
        # 工作区根显式声明：树内安装后 import.meta.url 落在 profile 里，推不出工作区
        workspace: 'C:/Users/ADMIN/Desktop/GBT小土豆V8'

# ③ 浏览器刷一次页面（F5）。服务端不需要重启。
```

## 生效：服务端零重启 · 浏览器刷一次 · 之后永久

实测（2026-09-22）：

- **补丁层是 `patchReload: live`**：改 `cordis.patch.yml` 会**热重组**——加行即装载、`disabled: true` 即卸载，秒级生效。
- **宿主半边换代码要换 specifier**：DSH 把每个 specifier 的**包元数据缓存到进程重启为止**。
  实测：换入口文件（`index.js` → `host.js`）无效、把行 disable→enable 也无效。
  ⇒ 唯一"不重启就换代"的办法是**换一个全新 specifier**（本包因此从 `gbt-master` 定为 `gbt-potato-master`）。
- **浏览器半边要刷一次页面**：客户端模块随页面引导载荷入册，已开着的页面不会凭空多出一个插件；
  `dsh-client-hmr` 只管"已存在模块被重建"，管不了"新模块首次入册"。
  ⇒ **服务端零重启 + 浏览器 F5 一次**；此后每次开机自动挂载，不用再管。

## 撤销（两条都行）

1. **只撤挂载**：把 `~/.dsh/profiles/web/cordis.patch.yml` 里 `- insert:` 那一段删掉 → 热重组即卸载，DSH 回原样；
2. **连包一起撤**：`dsh plugin --profile web remove gbt-potato-master`。

备份（首次改动前）：`~/.dsh/profiles/web/.gbt-backup/{package.json.bak, cordis.patch.yml.bak}`。

## 五个踩过的坑（别再踩）

1. **前缀路由不能带尾斜杠**。DSH 的匹配是 `pathname === prefix || pathname.startsWith(prefix + '/')` —— 注册 `/gbt-master/fs/` 永远匹配不上，请求全落到 SPA 兜底，**回 404 且响应体为空**（不是 401，别往权限上查）。
2. **`file:` vs `link:` 各有用处，别选错**：`file:` 把文件放进 profile 树内（浏览器名册才认），但 `import.meta.url` 会落在 `node_modules` 里 ⇒ 工作区根必须由组合行 `config.workspace` 显式声明；`link:` 让工作区成为真身，可包在树外 ⇒ 名册不认、拿不到 bundle。
3. **浏览器半边必须是已构建 bundle**（`window.__ModuleLoader__.load({ id, factory })`）：宿主提供构建产物，不跑构建步骤；只 `require` 平台基座里的模块（本插件只用到 `react`），数据走同源 `fetch('/gbt-master')`，不占 Host RPC。
4. **bundle 的正确探测形状是 combo URL**：`/plugins/??<id>/client.js&rev=<rev>`。直接探 `/plugins/<id>/client.js` 会 404，容易误判成"没供"。
5. **改名会留残留名册条目**：改名前的 id 仍留在本进程的浏览器名册里（对账只认当前存在的 entry 名），会一直留到重启。本包在 bundle 顶部给旧 id 注册了**空壳**（无副作用），让它也能解析，页面不会多报"找不到模块"；重启后随名册重算自然消失。

## 白名单口径

**默认拒绝**：非白名单扩展名、点开头文件、以及 `config/ store/ memory/ tools/ gbt_allinone/ vendor/ node_modules/` 一类目录一律 404；
单文件上限 12 MB。凭据文件不在可服务面内（负对照实测 404）。

## 品牌落点（v1.0.3 · 全部只走公开插槽）

| 位置 | 插槽 | 内容 |
|---|---|---|
| 左栏品牌行的**标** | `sidebar.brand.mark` | 土豆 Logo（部署方替换官方回退标的正式用法，写法照 `dsh-client-ui-brand-official`） |
| 左栏品牌行的**名** | `sidebar.brand.name` | `GBT小土豆V8`（三色渐变字） |
| 新会话大标题上的**品牌标** | `conversation.hero.brand.mark` | 大 Logo（宿主给 <56px 时抬到 56，带光晕） |
| 总面板头部 | 自有 UI | 52px Logo + 23px 渐变品牌名 + 副标 + 三色品牌渐变条 |
| 会话头右上角 | `conversation.session.header.utilities`（order=20，追加式） | 「GBT小土豆 · 上帝视角」入口，独立窗口拉起 W3 |

⚠️ **另踩一个坑（第 6 条）**：`file:` 安装下本包文件在 `node_modules` 里有**硬链接**，
用"原子替换式"写入（temp + rename / ReplaceFileW）会报 `EIO (Win32 1175)` —— 换成直接写入即可。
`git` 之外的工具编辑本包时请留意。

## 穿透式交叉扫描（2026-09-22 晚 · 本轮「把所有能力连接上」的取证工具）

**一键**：`C:\Python312\python.exe plugins/gbt-master/tools/cross-scan.py`（约 90 秒）
→ 落盘 `.scratch/_cross_scan_panels.json`（机读）+ `.scratch/_cross_scan_panels.out.txt`（人读）。

它穿透**四层**，每层只认真读数，不许猜：

| 层 | 查什么 | 断点判据 |
|---|---|---|
| ① 宿主层 | **三份登记表互相咬**：进程加载的那份 / 盘上源码 / profile 里已装的那份 | 三者 id 集合不等 = 登记表断点 |
| ② 路由层 | 每个面板 + 额外高价值页走真 HTTP（**路径按段百分号编码**，中文与空格文件名才不会误判） | 非 200 / 字节对不上（声明 `apiShim` 的页按「含注入」判，本来就该更大） |
| ③ 运行时层 | 真 Chrome 逐页渲染：控制台错 / ≥400 响应 / 请求失败 / 实际文本 / canvas 是否真出画面 | 有任何一条 = 带错 |
| ④ 数据层 | 端口 3080/8765/8788/8799/19681 + 面板 `/api/*` 逐个探（**区分「服务没起 503」与「端点不存在 404」**） | 探不到 = 数据通道断 |

### 本轮读数（2026-09-22 · 全部机检 · 最终一遍）

```
① 登记表：现役 12 ｜ 源码 12 ｜ 已装 12        → 三份一致，断点「无」
② 路由  ：12/12 全 200，字节全一致（apiShim 4 页按"含注入"判）
③ 运行时：12 页全 200 + 真内容，控制台错 0，失败请求 0   ← 首次全清
          pet    → 3D=ready（页面自报 body.dataset.localAvatar3d）
          avatar → 画面自证=True（window.__painted，采样 Δ亮度 217）
④ 数据层：26 条端点（现读 panel_server.APP_SURFACE）
          ＝ 只读真打 11 条（全通）＋ 会改状态静态对账 14 条（源码处理全在）
          /api/events 200 text/event-stream（SSE ✅）
          请求体转发钉子 ✅（直连与经宿主逐字一致：未知能力: <口令>）
          端口：3080 UP · 8765 UP · 8788 UP（pet 面板自己拉起的）· 8799/19681 DOWN
```

### ⚠️ 数据层的探测纪律（第一版在这里犯了错，写死当教训）

**26 条路由里有一批是"会改状态"的 POST**（开新线程 / 打断回合 / 受理蓝牙 / 受理对话 /
审批决定 / 星云与 EigenFlux 外发 …）。本扫描器第一版拿 `{}` **把 26 条全打了一遍** ——
实测后果：`/api/new-thread` 回 `{"ok": true}`（**真开了新线程**）、`/api/bluetooth` 回
`accepted: true`（**真受理了**）、`/api/interrupt` **真打断了回合**。

**改后的口径（照仓里《零副作用铁律》）**：

| 路由 | 怎么验 | 为什么 |
|---|---|---|
| `GET`（路由表自己声明只读） | **真打**（含经宿主这一跳，与直连对照） | 只读，打了没有后果 |
| `POST` / 其它（会改状态） | **静态对账**：路由表列了 ⇔ 源码里有 `parsed.path == "<route>"` 处理 | 不拿假 body 去戳真实动作 |
| 端到端只留**一条**安全动态钉子 | `/api/capability` + **未知 kind** ⇒ 只做合法性检查就拒，零副作用 | 且它的回话形状能分辨 body 到没到 |

### 本轮抓出并修掉的真缺陷（都是实测，不是推测）

| # | 缺陷 | 后果 | 修法 |
|---|---|---|---|
| 1 | 宿主 `sendJson` 把 `content-length` 报成 **JS 字符串字符数** | 中文一多，头小于身；严格客户端按头截断 ⇒ **目录 JSON 半截**（4671 字节被切到 3415，报 `Unterminated string`）。IWR/浏览器宽容，所以长期没暴露 | 改按 `Buffer.byteLength(body,'utf8')` 报头（v1.2.0）。**复验：头 4671 = 真字节 4671** |
| 2 | 登记表 9 条 vs 盘上 11 条 | 「赏金台 h1」「大脑执行层 brain」两个面板**在盘上、在总索引里，却点不到** | 补进登记表 + 换代上线（12 条） |
| 3 | 数字人成品页 `avatar.html` 不在登记表 | 数字人主线做出来的成品页在宿主内打不开 | 补进登记表（第 07 条） |
| 4 | `holo_pet/local-avatar-3d.js` 指向 `assets/digital-human/tripo-human.glb` | 那个文件**全树不存在** ⇒ 主控台 3D 形象 404、`localAvatar3d="failed"` | 改指 `raw/rig/model-rigged-anim.glb`（3.37 MB · 22 骨 · 带 idle/walk） |
| 5 | `index.html` 顶部台账人工写死（PANELS 10 / RENDERS 26 / PAYLOAD 1,726 KB） | 页面自称"与登记表同源"，数字却是上一版手抄的 —— **不诚实的自述比没有自述更坏** | 改为打开即同源现读 `/gbt-master`；取不到就显示「取不到」并写明原因 |
| 6 | 4 个面板页没声明 `rel="icon"` | 浏览器自动请求 `/favicon.ico` → 404 → 每页一条红字控制台错 | 补内联 `data:` icon（不依赖路径，CSP 的 `img-src data:` 也放行）。12 页 icon 全 True，控制台错全清 |
| 7 | **反代没转 `content-length`** | Node 对请求体改用 **chunked**；上游 `BaseHTTP/0.6`（HTTP/1.0）的 Python **不认 chunked** ⇒ **所有 POST 的 body 全丢**。后果：面板经宿主的每一个写动作都是**空转** —— 对话受理 / 审批决定 / 能力调用 / 社交发布 / 研究来源 / 设备总线 / Notion / EigenFlux / 星云 / 中断 / 开新线程。而直连 8765 全正常 ⇒ 极难从界面看出来 | 把 `content-length` 原样转下去（`transfer-encoding` 绝不转发）。**裸 socket 对照实测**：chunked → `400「缺少 kind」`；content-length → `200 accepted`。修后经宿主与直连**逐字一致** |

### 写盘机制（本轮踩了三次才吃透，写死）

**`file:` 安装 = 硬链接：工作区的包文件与 profile 里那份是同一个 inode（同一个文件）。**
（`fsutil hardlink list` 实证：两条路径、一个文件。）

⇒ **正确的改法次序**：先把源码全部改完 → **最后只跑一次** `dsh plugin … add`（只为登记新
specifier 名，内容根本不用同步）→ 换组合行 `name` → 移除上一世代。
**反例（我连踩三次）**：编辑一次就跑一次 `pnpm add` ⇒ pnpm 重新物化包、同一 inode 的
mtime 被改写 ⇒ 编辑器随后报「file changed since it was read」。**那不是文件被别人改了。**

### 扫描器自己的坑（写死，别重犯）

1. **路径不编码 = 把活面板误判成"路由断了"**。`V22 GBT小土豆V8-可交互原型.html` 带中文与空格，
   urllib 直接拒（`InvalidURL`）⇒ 第一版把这 4 个面板报成 `http=None`。按段 `urllib.parse.quote` 才对。
2. **探 SSE 必须带 `/gbt-master` 前缀**。漏了前缀就打到 DSH 自己的网关（`/api/events` → **401**），
   会被误报成"事件流断了"；真路由是 `/gbt-master/api/events` → **200 `text/event-stream`**。
3. **一律用 GET 探 = 把 POST 路由全误报 404**。必须按对方**声明的** method 探（现读 `APP_SURFACE`）。
4. **探针要读"页面自己声明的契约"**。画面自证我一开始查 `body.dataset.painted`（恒 null），
   而形象页声明的是 `window.__painted`／`__spread` ⇒ **改探针，不是改页面迁就探针**。

**教训一句话**：`None` / `null` 的读数**先怀疑探针**，再怀疑被测对象 —— 否则就是在给好的东西扣帽子。

## 连接审计与打磨（2026-09-22 早 · 首轮）

**一键排查**：`python plugins/gbt-master/tools/audit-panels.py` —— 用真浏览器把**当时登记表里的**面板逐个走 `/gbt-master/fs/*` 渲染一遍，
抓 HTTP 状态 / 控制台错 / 失败请求 / 是否真出内容，落盘 `.scratch/_panel_audit.json`。
（面板数已随登记表增长到 12；要四层穿透式全扫请用上一节的 `cross-scan.py`。）
**进程外验宿主**：`node plugins/gbt-master/tools/verify-host.mjs` —— 用真 `node:fs` + 真 8765 验反代、白名单放行、同源改写注入（含负对照）。

### 首轮审计结果（打磨前 · 当时 9 条）

9 个面板**全部 HTTP 200 + 真内容**；失败只在**数据侧**：
- `能力球`：6×401 —— 它的 `/api/recent-calls`、`/api/events` 打到了 **DSH 自己的网关**（同源）；
- `数字人面板`：12× —— 3D 依赖 `holo_pet/node_modules/three/**` 被白名单拒；`/api/capabilities`、`/api/social`、`/api/research`、`/api/observer`、`/api/tree`、`/api/studio` 全 401（同样打到 DSH）；
- `上帝视角 W3`：0 错，自己如实报「gbtW3 未注入」。

### 三处打磨（已验证）

1. **白名单放行面板自身依赖**：`EXEMPT = ['holo_pet/node_modules/three/']`（只放静态资源；`config/ store/ memory/ tools/ gbt_allinone/` 等仍默认拒绝，负对照 404）。
2. **内嵌反代 `/gbt-master/api/*` → 127.0.0.1:8765**（`node:http`）：服务在 → 原样透传；**服务没起 → 503 + 怎么起**（不假装有数据）。
3. **同源改写注入**：对声明 `apiShim` 的面板页注入一小段脚本，把页面里的 `/api/*`（fetch / XHR / EventSource）改写到内嵌反代 —— 于是面板的 `/api/*` **不再打到 DSH 网关**，也不再需要跳窗口。

⚠️ 宿主半边属**进程内代码**：DSH 按 specifier 缓存到重启，所以这三处在**下一次 `dsh web` 重启**后生效（已用进程外真跑验证过，不是等重启才发现）。

## 3D 形象与数据侧：已打通（2026-09-22 补）

**数字人面板现在真出 3D 形象**（真浏览器渲染读数：`body.dataset.localAvatar3d = "ready"` · canvas `844×702` · 状态「本地数字人在线」），右侧能力审计同时是**真数据**（共 158 项 · 可用 147 · 需确认 13 · 禁用 11，含 30 个域分布）。

为此补了两件（都不是代码，是缺的料）：
1. `cd holo_pet; npm install --no-audit --no-fund` → three 到位（`three.module.js` 589 KB）；
2. **从 git 索引恢复被清掉的 3D 模型**，头四字节 `glTF` 校验通过。
   （PowerShell 5.1 没有 `&&`，多条命令用 `;` 分隔；`cd holo_pet` 前要先在工作区目录。）

🔴 **路径已作废（2026-09-22 晚更正）**：当时恢复到的 `holo_pet/assets/digital-human/tripo-human.glb`
**现在已经不存在** —— 数字人主线把资产整理进了 `raw/` 分层，3D 形象一律走
`holo_pet/assets/digital-human/raw/rig/model-rigged-anim.glb`（3.37 MB · 22 骨 · idle 8.0s / walk 1.10s）。
`holo_pet/local-avatar-3d.js` 已按这个真身改过；**别再指 `tripo-human.glb`**（那就是断点 4）。

**复用工具**：`node plugins/gbt-master/tools/serve-digital-human.mjs`（起 8788：静态 + `/api` 反代到 8765）
配合 `python plugins/gbt-master/tools/shot-digital-human.py`（等模型就位后截图存证）。

⚠️ **本轮两个真缺陷（已修，都是实测踩出来的）**：
1. **反代错误分支会炸宿主进程**：上游已发出响应头后又报错时，再写 503 会抛 `ERR_HTTP_HEADERS_SENT`，
   且在错误处理里再抛一次 —— 已加 `headersSent / writableEnded` 护栏（只能断开，不能再写）。
2. **验证工具覆盖过真文件**：`verify-host.mjs` 原先往 `three/build/three.module.js` 写探针，
   npm 装完真文件存在后被覆盖成 34 字节桩 —— 已还原（重装 three），工具改为**独立探针文件名 + 存在即拒绝覆盖**。
   教训：**探针永远不要用真文件名**。

## 骨架存证工具其实一直在"假存证"（2026-09-22 晚 · 已修并配负控）

**怎么抓到的**：不是从工具报错抓到的（它从不报错），是从**一遍过期声明扫描**里，
看见 `tools/skeleton-viewer.html` 里还写着 `tripo-human.glb` —— 一个**全树不存在**的路径。
顺着往下挖，这个"骨架复核存证工具"其实是**三层假**：

| # | 缺陷 | 后果 | 修法 |
|---|---|---|---|
| 1 | viewer 里模型路径写死**已作废**的 `assets/digital-human/tripo-human.glb` | 每次都在**空场景**上截图，图上还印着「骨架复核 · 关节数 —」—— **图在，证据不在** | 默认改指真身 `raw/rig/model-rigged-anim.glb`，并支持 `?model=` 换件 |
| 2 | `shot-skeleton.py` 去开 `.scratch/_skeleton_viewer.html` 那份**早已不存在的副本** | 工具**根本跑不起来**（不是跑出坏结果，是压根没跑过） | 直接服务工具真身；**自己起一个 127.0.0.1 随机端口的只读静态服务**，不再依赖"外部先有个 8788" |
| 3 | 加载失败也只 `print` 一句就 **退出 0**，图与读数照旧落盘 | **静默失败**：坏读数被当成存证收下 | 关节数/顶点数非正 或 与期望不符 ⇒ **退出 1**；前置缺件单独 **退出 3**（"取不到"与"读数坏"分开） |
| 4 | 定心 + 缩放顺序写错（`position` 用 `-center` 而非 `-k·center`） | 偏移 `center·(k-1)` ⇒ 模型被推出画面右下角、半截在框外（旧图正是这样） | 改成 `position = -k·center`；网格落到脚下不再横穿身体 |
| 5 | 旧的 `render/骨架复核-*.png` 其实是 **10 关节老骨架**的图 | 顶着"骨架存证"的名字，会被读成**当前资产**的证据 | 用真身按 22 / 29 关节**同名重出**覆盖 |
| 6 | 实心网格把红色骨链**整条挡在身体里**，只剩几个青点 | 叫"骨架复核"却看不见骨架 | 默认半透明（`?ghost=0` 关）；弹簧档走 `?body=0` **只画骨架不画皮** |

**闸写粗了也会误判（本工具自己踩的）**：第一版对**每一张**都断言"弹簧骨 > 0"，
于是面板档三张全被自己判红 —— 那不是资产坏了，是**期望值没跟着"在测哪件资产"走**。
面板档 `model-rigged-anim.glb` 本来就**没有**弹簧链，7 根弹簧骨在 `model-springs-hair.glb` 里。
现期望值写在明处（`shots` 表里逐张带 `期22/期0`、`期29/期7`）。

**常驻负控**（工具自己的失败路径也要有闸，否则它会再退化成"没看出来"）：

```
py -3.14 plugins/gbt-master/tools/shot-skeleton.py            # 5 张存证，全正读数 ⇒ 退出 0
py -3.14 plugins/gbt-master/tools/shot-skeleton.py --negctl   # 指向不存在的模型 ⇒ 必须红字报出、不落 __shot
```

**第二条独立取证链**（这条是浏览器真加载 + three.js 真渲染，与 `audit-avatar-baseline.py`
那条 Python 解析 GLB 的路**互相独立**）：两边读数一致才算数 ——
**面板档 22 关节 / 16017 顶点 / 0 弹簧骨 ✅**、**弹簧档 29 关节 / 16017 顶点 / 7 弹簧骨 ✅**。

⚠️ **骨名口径（别引用错）**：HUD 上印的是 three.js **净化过**的骨名 —— `GLTFLoader` 的
`sanitizeNodeName` 会去掉 `[ ] . : /`，所以 GLB 里真名 `mixamorig:SkirtF` 显示成 `mixamorigSkirtF`。
已**直接读 GLB 的 JSON chunk** 核对：31 节点 / 7 命中 / 29 个名字带冒号。
**要原始骨名就看 GLB 或 `audit-avatar-baseline.py` 的输出，别抄 HUD。**

**这一族毛病的共同形状**（本会话已撞到第四次）：**"源"与"在用的那份"不是一份** ——
技能根漂移 → 注入上下文假绿 → 装机副本漂移 → **存证工具指向不存在的文件**。
所以抓法不是"看工具报不报错"，而是**把声明与真身逐一对账**：扫死路径、扫过期读数、扫退出码恒 0 的"验收器"。

## 语法闸对 importmap 是瞎的（2026-09-22 晚 · 同族第五处 · 已补 + 已配常驻负控）

**怎么抓到的**：把上一节的"对账"方法用到**门自己**身上 —— 先问一句"这道门能不能红？"。
`check-panel-syntax.py` 原来对 `type="importmap"` 走的是 `continue`（因为 `node --check` 查不了 JSON），
**跳过之后就再没验过**。而 importmap 在本项目是**载荷声明**（three.js 解析全靠它），坏了的表现是
**白屏** —— 正是这道门存在的理由（宿主目录里 `exists=true`、`size` 正常，看目录看不出来）。

| 夹具 | 旧行为 | 现在 |
|---|---|---|
| importmap JSON 坏（尾逗号） | ✅「通过」 | 🔴 importmap 0 不是合法 JSON |
| importmap `imports` 不是对象 | ✅「通过」 | 🔴 `imports` 不是对象（是 str） |
| importmap 顶层不是对象 | ✅「通过」 | 🔴 顶层不是对象（是 list） |
| 内联 JS 语法错 | 🔴 正确报错 | 🔴 不变 |
| 干净页（正对照） | ✅ | ✅ 不变 |

**现读有没有真面板中招**：**没有**。全量扫过 12 面板 + `avatar.html`，只有 `index.html` 与
`avatar.html` 带 importmap，**两份都合法** —— 所以这是**门上的盲区**，不是线上故障（已如实区分）。
汇总行也顺手改了：现在报「内联 script N 段 **+ importmap M 段**」，不然一个只有 importmap 的页面
会显示成"script 0 段 · 通过"，看起来像"没查也通过"。

**常驻负控**（写在门自己里面，夹具现造在临时目录，**不碰真面板**）：

```
py -3.14 plugins/gbt-master/tools/check-panel-syntax.py --all       # 12 个真面板 ⇒ 现读 exit 0
py -3.14 plugins/gbt-master/tools/check-panel-syntax.py --negctl    # 5 支夹具必须给出预设结论
```

## 门的自证清单（谁验过门？—— 本轮补齐）

一条纪律：**没被证明能红的门，不算门**。现读各门的"能红"证明方式：

| 门 | 怎么证明它能红 |
|---|---|
| `check-panel-syntax.py` | `--negctl`（5 支夹具：坏 importmap ×3 + JS 语法错 + 干净页正对照） |
| `shot-skeleton.py` | `--negctl`（指向不存在的模型 ⇒ 必须红字报出、不落 `__shot`） |
| `audit-dh-status.py` | `--negctl`（自造"幽灵引用"⇒ `--strict` 判红；`--no-receipt` 不盖真回执） |
| `design-inventory.py --check` | `--negctl`（在**自己的临时副本**上塞一条死路径 ⇒ 判红；真身 sha 判完不变） |
| `verify-installed-copy.mjs` | 天然红过：源稿一改就报不一致（本轮实测多次），`--fix` 后转绿 |
| `verify-catalog-latency.mjs` | 由真 A/B 造出：顺序 N+1 实测 15,716 ms、并行 1,211 ms，阈值 2,400 ms 卡在中间 |
| `audit-skill-roots.py` | 早前负控：改技能一个字节 ⇒ 退出 1 |

**另外三支工具的 `--negctl` 用法**（都在仓里可复跑）：

```
py -3.14 tools/codex-scripts/audit-dh-status.py --negctl
py -3.14 tools/codex-scripts/design-inventory.py --negctl
py -3.14 tools/codex-scripts/audit-dh-status.py --status <候选稿.json> --no-receipt   # 审候选稿、不留痕
```

⚠️ **两个自伤坑（写给别人别重犯）**：
① `design-inventory.py --negctl` 第一版把**锚点字符串原样写在脚本里** ⇒ 文件里就有两处 ⇒
`count != 1` 立刻把自己判红。锚点必须**拆开拼**（运行期等值、文件里不等值）。
② 一次性脚本里 `print("…⇒…")` 在 GBK 控制台上直接 `UnicodeEncodeError` **崩掉**（本轮又踩一次）——
写仓内脚本一律先 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`。
