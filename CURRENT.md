# 现行清单（CURRENT）· 谁在用、谁退役、谁「看着旧但还活着」

> **这一份是全仓唯一的"新旧裁决书"。** 任何"这是旧的吗？能删吗？"的问题，**以本文件为准**。
> 为什么需要它：2026-09-23 我按「旧页面都要清理掉」去清点，**差点把正在供餐的面板服务删了** ——
> 因为 `holo_pet/` 这棵树**看起来**是旧生产树，实际它是活的。
> 根因不是"没注意"，是**没有一份能查的裁决书**，每个判断都得靠当场推理。
>
> 最后核对：2026-09-23（读数方式写在每条后面，**可复跑**）

---

## 一、现行（唯一准用）

| 树 / 文件 | 是什么 | 状态 |
|---|---|---|
| **`holo_pet_w3/`** | **一体式桌面壳（唯一现行）** | ✅ 现行。窗 A 对话 · 窗 1 上帝视角 · 窗 5 AI 朋友圈 · 窗 6 赏金台 · 窗 C 执行台 · 窗 D 代码台 · **窗 E 神经工作台** · **窗 F 触手视觉回传**（8 扇窗，`shell/windows.json` 为准）· 运行说明见 `holo_pet_w3/README.md` |
| **`holo_pet_w3/shell/*.cjs`** | **壳的六支验收器** | ✅ 现行。预检 **16/0/3** · 复演 7/0/1 · 真启动 **9/0** · 交互 7/0 · 取证 7 扇 FAIL 0 · 屏面暴露 0 命中。**命令一律走 `npm run <名>`**，别直接记路径（见该目录 README §3）。⚠️ 这三个数字是**读数**，改了器就会变（2026-09-23 第 43 轮预检 15→16、真启动 8→9）—— 别把上一行的数字抄到这一行 |
| `holo_pet_w3/skin-mission-control.css` | **专业皮肤层**（出处：`审美相关skill/design-systems/mission-control/`） | ✅ 现行。**必须在 `window.css` 之后引入**（靠加载顺序把壳的语义 token 接过去） |
| `holo_pet_w3/window.css` + `deck3d.css` | 壳品牌 token（白皮书冻结三色）+ 立体层 | ✅ 现行 |
| `gbt_allinone/` | 框架本体（161 能力位 · 22 模块族） | ✅ 现行 |
| `V22 GBT小土豆V8-{无限画布,可交互原型}.html`（仓根） | **最新一次 App 双交付** | ✅ 现行 |
| `plugins/gbt-master/` | 宿主插件（12/12 面板） | ✅ 现行 |
| `tools/codex-scripts/` | 全部机检器与生成器 | ✅ 现行 |
| `state/tree-registry.json` + `tools/codex-scripts/tree-registry.py` | **仓根树登记表 + 登记闸**（分类 / 实体与视图 / 已判过「留」的件） | ✅ 现行。`py -3.14 tools/codex-scripts/tree-registry.py --check` **绿**：43 棵树全登记 · 25 条视图全交代 · R8 12 件「已判过留」都在。**改盘先看这张表** |
| `tools/codex-scripts/probe-reparse-points.py` | **重解析点普查**（谁实体、谁是别人的视图） | ✅ 现行。25 条视图。**它存在的理由**：`vendor/pylibs` 与 `gbt_allinone/.pylibs` 逐字节相同，但后者是 junction ⇒ **「内容相同」推不出「有一份多余」** |
| `tools/codex-scripts/dup-source-inventory.py` | 重份盘面普查（文件数/字节/一层拆解，只读） | ✅ 现行。带 `--breakdown` / `--top` / `--json` |
| `tools/codex-scripts/vendor-node-trim.py` | vendor/node_modules 去重（进回收站） | ✅ 现行。2026-09-23 清 13 包 / **369.6 MB**；留 `three`（生成器真读）与 `.bin` |
| `tools/codex-scripts/exposure-scan.py` | **屏面暴露面扫描**（扫**真渲染出来的 innerText**，不扫源码） | ✅ 现行。7 扇窗 **0 命中**。带 `--selftest` 正负对照 |
| `tools/codex-scripts/pack-receipt.py` + `state/desktop-install-receipt.json` | **装机回执**（装机包真打出来之后，从包里**重新量**一遍） | ✅ 现行。`dist/win-unpacked/GBT小土豆V8.exe` 224.8 MB · 整包 306 文件 / 360.8 MB · **8 项机检 / 红 0** · 两条负规则（触手截图未进包 / 依赖目录未进包）零命中。**它不采信打包器 stdout** |
| `tools/codex-scripts/old-pages.py` | **旧页面判决器**（把 Owner 提过三次的「旧页面要清掉」固化成判决表 + 一道闸） | ✅ 现行。现读 **188 个页面 · 被超越 0 · 零引用 0** · `--check` 退出码 **0**。判决只有四种且**每种都要有依据**：清单点名 / 同族更高版 / 有引用 / 排除项（逐类写理由）。本轮真清出去：`V1 触手工作流-*` 两件入口壳（同族 V2 已在）；仓根那份研究记录**移到 `delivery/`**（记录不是草稿，不硬删） |
| **能力位 `audio_extract`**（`gbt_allinone/tools/audio_extract.py`） | **从视频里取声音**（Owner 2026-09-23：「学会这个能力固化为自己的原生能力接上」） | ✅ 现行。`probe`/`tracks` 只读；`extract` 出 **8 种格式**（mp3/aac/m4a/wav/flac/ogg/opus/wma，可切段/调音量/响度归一）。**零出网**（只用本机 ffmpeg 8.1.2）· **写面自收窄**到 `projects/`·`outputs/`·`.scratch/`（policy 无该 kind ⇒ 门内零作用域，故自钉，负对照见单测）· **产出即验证**（落盘后 ffprobe 回读产物）。判据 `gbt_allinone/tests/test_audio_extract.py` **25 项**。格式知识落成 `FORMATS` 表（容器≠编解码器 / 有损与无损两族），出处两篇文章记在模块头 |

## 二、退役（已清理 / 待清理）

| 树 / 文件 | 判据 | 处置 |
|---|---|---|
| `archive/V1..V21 …` | **被仓根 V22 超越**（同后缀更高版存在） | ✅ 2026-09-23 已进回收站（42 项） |
| `.shadow-repo/` | `build_shadow_repo.py` 生成 + `.gitignore` 已列 ⇒ 可重建 | ✅ 已进回收站（190 MB / 206 页）· 实测 2026-09-23 复读：**盘上确实没有** |
| `.openclaw/tmp` · `.scratch/_v22_stage` · `.scratch/_recovered` · `outputs/tentacle-studio/archive` | 临时/暂存/被超越 | ✅ 已进回收站 |

### 🔴 二·补：**这一行曾经写错，已在 2026-09-23 更正**（不改就等于邀请下一个人再删一次）

旧文写着：

> ~~`holo_pet/local-avatar-3d.js` · `_h1_verify.py` · `signal_ingest.py` · `research.json` · `xingyun_e2e.latest.js` · `holo_pet/__pycache__` · `holo_pet/desktop/`｜**零外部引用**（实测）｜✅ 2026-09-23 已进回收站（7 项）~~

**那句话在当时就是错的，后果已经发生过一次**：删掉之后面板 **12/12 → 11/12**、
`holo_pet/tests` **17 项转红**。原因是我只查了"谁 import 它"，
**漏了两种同样真实的引用形态**：① 靠**路径字符串**读它（不是 import）；② **目录条目被父级扫描**。

**实测复读（2026-09-23）**：那 7 项里 **6 项已经收回并在盘上** ——

| 项 | 现读 |
|---|---|
| `holo_pet/local-avatar-3d.js` | **在** 2,797 B |
| `holo_pet/_h1_verify.py` | **在** 1,099 B |
| `holo_pet/signal_ingest.py` | **在** 9,099 B |
| `holo_pet/research.json` | **在** 253 B |
| `holo_pet/xingyun_e2e.latest.js` | **在** 820,991 B |
| `holo_pet/__pycache__` | **在**（目录） |
| `holo_pet/desktop/` | 不在（只这一项真的没了） |

⇒ **这一格改为：全部禁止再动。** 判据不是"没人 import"，而是
`holo_pet/tests` 的 **157 项**正靠它们活着（实跑：`run-tests.py holo_pet/tests` → 157 passed / 0 failed）。
要动先用 §4.2 的三种形态全查一遍，**缺一种就不许删**。

**清理总账**：仓内 HTML **810 → 565 个**（56.5 → 15.9 MB）；回收站可还原。
2026-09-23 第 30 轮再清（**数字现场量，不是估的**）：HTML **633 → 625 个**（16.2 → 14.4 MB）；
连同缓存/临时档共 **181 项 / 134.7 MB** 进回收站（页 3 项 2.57 MB + `__pycache__` 169 项 95.33 MB
+ 临时扫描档 8 项 36.80 MB）。仓内（不含 `.git`）现 **4,623 MB**。

## 三、🔴 「看着旧但还活着」—— 这个区的东西**一律不许删**

### 三·补2（2026-09-23 第 39 轮）🔴 **`holo_pet_w3` 有两份，权威是工作区根那份**

`holo_pet_w3/README.md`（2026-09-18 那版）曾经写着：

> ~~「权威源：**镜像维度** `store/mirror_space/dimension/holo_pet_w3/`（唯一写入口）；
> 工作区根 `holo_pet_w3/` 是**落地副本**——只读，只许由落地动作整棵替换，**不许手改**。」~~

**实测（2026-09-23）：这句话是反的。**

| | 镜像维度 `gbt_allinone/store/mirror_space/dimension/holo_pet_w3/` | 工作区根 `holo_pet_w3/` |
|---|---|---|
| 落盘 | **2026-09-18 04:50**（7 天前的一次快照） | 持续在动 |
| 文件数 | **16** | **244** |
| `shell/windows.json` | 2,033 B | **9,768 B** |
| `window.js` | 19,205 B | **48,958 B** |

⇒ **权威 = 工作区根 `holo_pet_w3/`。**
⚠️ **谁照旧文档"从镜像重新落地"，会把工作树从 244 个文件整棵冲回 16 个** —— 十轮工作当场没了。
镜像空间是框架的**试验场**（AGENTS.md 定的），**不删**；它的定位是"某一天的快照"，
**不是现行源**。已把 `holo_pet_w3/README.md` 整份重写，并在开头把这条写死。

### 三·补（2026-09-23 第 30 轮）`deploy/` —— **看着最旧，其实是活的面板 #12**

这一条是**差点又犯一次同样的错**才写下来的。`deploy/` 三页标题全是 **V21**，
而仓根 `V22 …` 才是现行版 —— 按"看着旧"的字面，它是最该被清掉的那一堆。**但它是：**

| 证据 | 出处 |
|---|---|
| **它是 12 个面板里的第 12 个** | `plugins/gbt-master/lib/host.js:89` `{ id: 'deploy', file: 'deploy/index.html', … }` |
| **仓根 `index.html` 活着链过去** | `index.html:272` `<a class="card" data-i="08" href="deploy/index.html">` |
| **它是外网写入落点** | host.js 该条 note 原文：「重新部署＝外网写入 ⇒ **必须先问主人**」 |

⇒ **`deploy/index.html` 与 `deploy/canvas.html` 一律不许动。**
（同目录的 `deploy/gbt-prototype.html` 是**第三份**重复页、零引用 ⇒ 已进回收站，见下。）

**复验命令（清理后真跑过）**：
```powershell
cd plugins/gbt-master
node tools/verify-state-injection.mjs   # → 面板实况：在 12 / 12（无缺）
node tools/verify-catalog-latency.mjs   # → 目录路由 1211 ms · 面板 12 条
node tools/verify-all.mjs               # → 宿主插件三门全过
```
⚠️ **面板页的真 URL 是 `/gbt-master/fs/<路径>`（`host.js:165` `FS_BASE`），不是 `/deploy/index.html`。**
用错 URL 去量会得到 404 并误判"面板坏了" —— 第 30 轮我就这么误判过一次。

### 第 30 轮真清出去的三项（均可从回收站还原）

| 项 | 大小 | 判据 |
|---|---|---|
| `deploy/gbt-prototype.html` | 0.63 MB | 「可交互原型 V21」在本仓的**第三份**；`deploy/index.html` 才是面板 #12；仓根 V22 才是现行。**实测 0 引用** |
| `agent-gvmz-gbtv8/.openclaw/tmp/` | 1.93 MB | 框架自己两处写明：`scan_scope.py` 把 `.openclaw` 列进 `TOOLING_DIRS`；`gate_visibility.py` 把 `agent-gvmz-gbtv8` 列进 `DECLARED_NOT_WATCHED` |
| `.scratch/_overlay_old.html` | 0.01 MB | 名字自带 `_old`，同目录有 `_overlay_now.html` |

⚠️ **`agent-gvmz-gbtv8/DELIVERY/` 那 14 份带日期的交付报告保留** —— 那是记录，不是草稿。
Owner 说的是「别搞混」，不是「把历史删了」。

### `holo_pet/` 整棵树：**它是活的**

**证据（可复跑）**：

```powershell
Get-CimInstance Win32_Process -Filter "ProcessId=7440" | Select-Object CommandLine
# 实测输出：
#   "C:\Python310\python.exe" holo_pet\launch_panel.py --host 127.0.0.1 --port 8765 --no-browser
```

**它就是这个壳的面板服务**（端口 8765 · 12/12 面板靠它供餐）。
按"旧生产树"字面删它 ⇒ **面板当场全灭**。

### `holo_pet/` 里只有四件是**活读**的（其余是历史包袱，但没查干净前不许动）

| 文件 | 谁在读 |
|---|---|
| `panel_server.py` | 就是那个服务本体（`launch_panel.py` 从它 import `HoloBridge` / `create_server`） |
| `launch_panel.py` | 进程命令行里那个脚本 |
| `social.json` | `panel_server.py` 运行期读（`base / "social.json"`） |
| `ark_surface.json` | `panel_server.py` 运行期读（`_HERE / "ark_surface.json"`） |

**另外两块"看着能删、其实不能"**：
- `holo_pet/assets/`（**1.42 GB**）—— 数字人交付资产，**25 处外部引用**
- `holo_pet/node_modules/`（399 MB）—— 4 处外部引用（★ 我 vendor 的三份 three 来自**仓根 `vendor/`**，与它无关）

### 静态托管的口径（别改错）

`panel_server.py` 的 `_HERE` = `holo_pet/`，`_REPO_ROOT` = 仓根。它服务的
`index.html` / `capabilities.html` / `brain.html` **来自仓根**（`_REPO_ROOT_ALLOW` 白名单），
**不是** `holo_pet/index.html`。⇒ `holo_pet/index.html` + `styles.css` 是**旧上帝视角的壳**，
但**它被 5 处引用**，没查干净前别动。

## 四、机检护栏（让"又混了"不可能再发生）

### 4.1 🔴 一次真实事故（2026-09-23 · 必须留档）

我按「旧页面都要清理掉」清掉了 `holo_pet/{index.html, styles.css, app.js, deploy_check.py}`，
依据是"引用扫描显示没人用"。**结果面板从 12/12 掉到 11/12（缺「主控台 W1 · 数字人面板」）。**

**根因不是"没注意"，是扫描面漏了一整类文件**：

| | |
|---|---|
| 面板清单在哪 | `plugins/gbt-master/host.js:83` → `{ id: 'pet', file: 'holo_pet/index.html', … }` |
| 我扫的是什么 | `plugins/**/*.py` + `plugins/**/*.cjs` |
| **漏了什么** | **`plugins/**/*.js`** —— 而声明式消费者恰好住在 `.js` 里 |

**修复**：`index.html`/`app.js` 从 git `HEAD` 取回（`git checkout` 撞上并发会话的 `index.lock`，
改用 `git show` **绕开索引**）；`styles.css` 不在 HEAD 但**在 git 索引里**，用 `git show :path` 取回。
**面板已回到 12/12**。

**教训（比事故本身值钱）**：
> **扫描面的漏洞比判据的漏洞更致命。** 判据写错会误报；扫描面漏一类文件会**直接删错东西** ——
> 而"扫描通过"恰恰是因为**没扫到那个文件**。

### 4.2 「谁在用这个文件」有**三种形态**，缺一种就会误删

| # | 形态 | 护栏 | 已知边界 |
|---|---|---|---|
| ① | 进程正拿着 | `live_paths()` —— 父子**双向**匹配 | 只查命令行**字面**路径；查不到动态拼的 |
| ② | **清单/注册表点名** | **`manifest_paths()`** —— 扫 51 个声明文件 ⇒ **260 个受保护路径**（含**传递闭包**） | 只覆盖声明文件里出现的路径字面量 |
| ③ | 代码 import/引用 | 引用底账（`referenced_names()`） | 正则不含空格曾漏掉全部带空格的中文页名（已修） |

**传递闭包**：清单点名的页面**引用到的**本地件（`href`/`src`）一样是活的 ——
`holo_pet/styles.css` 与 `app.js` 就是这么被保护的。
（这个闭包我自己写错两次才通：首版把种子取成"引用方"而不是"被点名的文件"，
`.html` 过滤把 `host.js` 挡掉 ⇒ 闭包空转。）

### 4.3 ✅ 事故已完全收尾（2026-09-23 结）

| 文件 | 怎么回来的 |
|---|---|
| `holo_pet/index.html`（25.5 KB） | `git show HEAD:…` |
| `holo_pet/app.js`（145.0 KB） | `git show HEAD:…` |
| `holo_pet/styles.css`（62.9 KB） | 不在 HEAD、**在 git 索引里** ⇒ `git show :holo_pet/styles.css` |
| `holo_pet/deploy_check.py`（3.9 KB） | 回收站按名还原（`Shell.Application` + `InvokeVerb()`） |

**第四件为什么最后才回来**：回收站枚举在这台机器上**很慢**（1150 项），而首版脚本调了
`ExtendedProperty("System.Recycle.DeletedFrom")` —— 逐项取扩展属性 ⇒ **两次 120 s 超时**。
去掉属性枚举、只按 `Name` 匹配之后，**秒级完成**。
⚠️ **教训**：程序化还原不要碰扩展属性；先用 `Name` 定位，再 `InvokeVerb()`（默认动词即"还原"）。

**面板实况**：12/12（事故期间一度掉到 11/12）。

### 4.4 🔴 一次清理引发的连环事故（**完整留档 · 全部已收回**）

**这一节的每一环都是"判据看起来对、但漏了该管的那一类"。八次同形状，值得完整抄下来。**

| 轮 | 我做了什么 | 我为什么以为它对 | 真相 |
|---|---|---|---|
| 16 | 删 `holo_pet/` 里 7 个"零引用"文件 | 引用扫描报 0 命中 | 扫描面**漏了"测试文件 import 裸模块名"** ⇒ `signal_ingest.py` 其实有 14 条测试在用 |
| 17 | 删 `holo_pet/{index.html,styles.css,app.js}` | 扫的插件面是 `.py` + `.cjs`，**漏了 `.js`** | 面板清单住在 `plugins/gbt-master/lib/host.js` ⇒ 面板 12/12 掉到 **11/12** |
| 25 | 用 `git show HEAD:` / `:path` 还原 | 文件回来了、大小看着正常 | **还原的是 git 旧版**，工作树里那份带未提交改动的才是真的（27.6→25.5 / 68.0→62.9 / 147.3→145.0 KB） |
| 26 | 报"这 4 个文件救不回" | 回收站按名扫：0 命中 | **我的还原器要求 `$R` 是文件** ⇒ **33 个目录项被静默跳过**，含 `.shadow-repo` |
| 27 | 扫目录项 | —— | `.shadow-repo`（2470 文件）里**四个文件的真版本全在** ⇒ 还原 ⇒ `holo_pet/tests` **157 passed / 0 failed** |

**四条可复用的判据（都拿事故换的）**：

1. **"谁在用这个文件"有三种形态**：进程拿着 / **清单与注册表点名** / 代码 import。
   缺一种就会误删（§4.2 的两道护栏就是补这个）。
2. **"文件回来了" ≠ "文件是对的"** —— 必须**比对尺寸**。而尺寸**一开始就在我自己的清点记录里**。
3. **"扫过了没找到" ≠ "不存在"** —— 先问"我的扫描面漏了哪一类"。26 轮漏的是**整整一类**（目录）。
4. **"可重建"是真的，但重建出来的不是"你当时手里那份"。**
   `.shadow-repo` 我按"生成镜像、可重建"删的 —— 判据没错，可它**恰好是那批未提交改动的唯一副本**。

**讽刺的一点**：救回数据的，正是我当成"冗余重复"删掉的那个镜像。

### 4.5 回收站还原器（可复用）

`tools/codex-scripts/restore_from_recyclebin.py` —— **不走 COM**（`Shell.Application` 那条路两次 120 s 超时）：
直读 `C:\$Recycle.Bin\<SID>\` 的 `$I`/`$R` 对。两个必须记住的坑：
- **名长字段宽度随 Windows 版本不同**（4 B vs 8 B）—— 写死 4 B ⇒ 路径被切在半路（`…\GBT小土豆` 后面没了）；
- **目录项要一起扫** —— `$R` 可能是目录。

## 五、判据（可复用的三句话）

1. **「看着旧」不是判据** —— `holo_pet/` 看着最旧，它是活的；
2. **判据只能是「被超越」或「没人用」** —— 有更高版存在、或引用底账零命中；
3. **拿不准的一律留，并写进本文件** —— 留着的成本是一行字，删错的成本是交付物没了。

---

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
