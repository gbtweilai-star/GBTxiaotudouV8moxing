# gbt-capability-bar · GBT小土豆V8 能力栏（DSH 本地插件 · A 腿）

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
>
> **现役：`gbt-potato-capability-bar-v1` · 宿主 v1.0.0** —— 包名即 specifier（换代机关，见第五节）。
> 本 README 取代 2026-09-22 的「设计稿 v0.1」（那份的三条"未验项"已全部落地：插槽写法照
> `plugins/gbt-master` 的活样板，bundle 形态、`dsh.client.inject`、插槽 id 全部实测可用）。
>
> 页面本体（B 腿）在 `holo_pet_w3/capability-bar/index.html`（自包含 · 零外链 · 零远端取数）。
> 本插件**只负责把它嵌进官方 APP**：左栏脚部一格 + `shell.overlay` 浮层 iframe（零开窗）。

## 一 · 主人令与口径（2026-10-08）

| 原话 | 落法 |
|---|---|
| 「记得能力栏精细设计一下」 | 页面五条精细设计（一屏可读 / 三态一色 / 数据新鲜度 / 零打扰 / 可点到处）逐条在 `docs/能力栏-精细设计.md` |
| 「使用官方的 APP 来改造」 | 不另起界面：**加装**在 DSH 官方 APP 里 —— 左栏脚部一格 + 浮层内嵌；**不占品牌位、不动 gbt-master 的任何一格** |
| 「只要能力全部不丢失就行」 | 页面把 **240 位一位一格**全画出来（三边零未绑），一个不落；"不丢失"的证据 = 绑定台账三边计数守恒 |
| 「不破坏环境，我们加装其他的而已」 | 宿主半边**只读**（无写盘原语）；插件只注册两个插槽；不改 DSH 一行源码（只走 `webServer.register` 与公开插槽） |

## 二 · 与 gbt-master（`plugins/gbt-master`）的关系 —— 加法，不加锁

| 面 | gbt-master | 本件 | 会不会打架 |
|---|---|---|---|
| 左栏脚部 | `sidebar.footer.action`：`gbt-panels`(40) / `gbt-godview`(41) | 同槽 `gbt-capbar`(**42**) | **不会**：list 槽多占用，本件 order 排在它俩之后 |
| 浮层 | `shell.overlay`：`gbt-panel-layer`(40) | 同槽 `gbt-capbar-layer`(**41**) | **不会**：id 不同、两层各自开关 |
| 品牌位 | `sidebar.brand.mark/.name` + `conversation.hero.brand.mark` | **一格不碰** | — |
| 首页注入 | `webServer.tapIndex`（自愈器 `heal.js`） | **不调 tapIndex** | **不会**：两家都注会变双份刷新源；本件只在**自己的页**里注入数据脚本 |
| 自报诊断 | `POST /gbt-master/diag` | `POST /gbt-capability-bar/diag` | 各存各的内存，互不覆盖 |
| 页面自愈戳 | `documentElement.dataset.gbtGen`（判据！） | **只写 `data-gbt-capbar`** | **🔴 关键**：写 `gbtGen` 会让对方的自愈器把整页判成"旧世代"而反复刷新 |
| 静态白名单 | `/gbt-master/fs/*` 放行整套工作区面板 | `/gbt-capability-bar/fs/*` 只放行 **6 条**（见第四节） | 各走各的前缀 |

## 三 · 文件

| 文件 | 作用 |
|---|---|
| `package.json` | 包声明：`name=gbt-potato-capability-bar-v1`（包名即 specifier）；`main`=宿主半边；`exports["./client"]`=浏览器半边；`dsh.client.platform=web` |
| `lib/host.js` | 宿主半边：目录 JSON / **现读数据件 `live.js`** / 页面包装注入 / 只读白名单静态路由 / 自报诊断。**只读**：无写盘原语、不碰 `~/.dsh`（判据 C9/C11 机检） |
| `lib/client.js` | 浏览器半边（已构建 bundle：`window.__ModuleLoader__.load`）· 只 `require("react")` · 两个插槽 + 浮层组件 |
| `tools/verify-host.mjs` | **进程外真跑**宿主（假 ctx 起真 apply，逐条路由打真请求；白名单含负对照） |
| `tools/verify-client-apply.mjs` | **无头验收**浏览器半边（真 bundle 装进假装载器跑 apply + 渲染一层浮层读 iframe） |
| `README.md` | 本文件 |

## 四 · 只读白名单（默认拒绝，面比 gbt-master 窄得多）

放行只有 **1 个前缀 + 5 个精确文件**：

```
holo_pet_w3/capability-bar/**                 ← 本页自身（index.html / run-evidence.js）
holo_pet_w3/energy/index.html                 ← 详页：能量与绑定（240 条逐条）
holo_pet_w3/energy/energy-data.js
holo_pet_w3/capabilities/index.html           ← 详页：能力统计（326 项逐条）
holo_pet_w3/capabilities/capabilities-data.js
assets/brand/logo-potato-64.png               ← 品牌标
```

别的一律 404（含 `state/`、`memory/`、`gbt_allinone/`、`plugins/`、点开头文件、非白名单扩展名）。
**负对照实测 9 条越界路径全 404**（含 `%2e%2e` 编码穿越、`../` 上级目录、`win.ini`、`.env`）。

## 五 · 挂载（照 gbt-master 的实测路径；**本节改动一律「未执行」**）

```powershell
# ① 装进 web profile —— 必须用 file:（浏览器名册只扫树内包）
node "$env:LOCALAPPDATA\npm-cache\_npx\1e7f6d9597241db0\node_modules\@deepseek-ai\dsh\lib\bin.js" `
  plugin --profile web add "file:C:/Users/ADMIN/Desktop/GBT小土豆V8/plugins/gbt-capability-bar"

# ② 组合行写进用户补丁层（该 profile 是 patchReload: live，存盘即热重组）
#    ~/.dsh/profiles/web/cordis.patch.yml 第 63-68 行是 gbt-master 的 - insert: 项
#    ⇒ 在**同一个 list 末尾**（第 68 行之后）增一项：
#    - id: gbt-capability-bar
#      name: 'gbt-potato-capability-bar-v1'
#      config:
#        workspace: 'C:/Users/ADMIN/Desktop/GBT小土豆V8'

# ③ 浏览器 F5 一次（客户端模块随页面引导载荷入册；已开着的页面不会凭空多出一格）
```

**怎么判"接上没有"**（不用截图、一条 GET）：

```powershell
curl.exe -s http://127.0.0.1:3080/gbt-capability-bar     # 或浏览器直开同路径
```

- `ok:true` + `counts.caps:240` ⇒ 宿主半边在；
- `clientDiag:null` ⇒ **还没在任何页面生效**（要一次 F5）；
- `clientDiag.diag:["footBar:ok","overlay:ok"]` ⇒ 浏览器半边两格都注册上了。

**换代 = 换 specifier**（DSH 把包元数据按 specifier 缓存到进程重启）：改宿主代码要换
`package.json` 的 `name`（如 `-v2`）并同步组合行 `name`；旧 id 在 `lib/client.js` 顶部按
gbt-master 的办法留**无副作用空壳**，重启后自然消失。

## 六 · 撤销（两条都行）

1. **只撤挂载**：把 `cordis.patch.yml` 里 `- id: gbt-capability-bar` 那一段删掉 → 热重组即卸载，官方 APP 回原样；
2. **连包一起撤**：`node <dsh bin> plugin --profile web remove gbt-potato-capability-bar-v1`
   （⚠️ 照 gbt-master §4.8 的教训：**删旧代之前先重启 DSH**，否则缓存还指着已删的包 ⇒ 整页红字）。

## 七 · 判据（三条，全部可复跑）

```powershell
py -3.14 tools/codex-scripts/capability-bar-check.py refresh   # 重生成运行证据快照（近 24h 有界窗口）
py -3.14 tools/codex-scripts/capability-bar-check.py --check   # 判据 11 条 + 负对照 8 条（退出码 0/1）
node plugins/gbt-capability-bar/tools/verify-host.mjs          # 宿主进程外真跑 13 条（含白名单负对照）
node plugins/gbt-capability-bar/tools/verify-client-apply.mjs  # 浏览器半边无头验收 13 条（含 3 条负对照）
```

现读（2026-10-08 本轮）：

```
判据 PASS 11 · FAIL 0 ｜ 负对照 PASS 8 · FAIL 0 ｜ 端到端(--live) PASS
宿主进程外真跑：PASS 13 · FAIL 0
浏览器半边无头验收：PASS 13 · FAIL 0
```

## 八 · 已知观察（**只记录，一件未动**）

1. **gbt-master 的自愈器 `mounted()` 可能恒假**：`plugins/gbt-master/lib/heal.js` 里
   `mounted()` 判的是 `.gbtm-gv`，而该 class 在其 `lib/client.js` 里**只出现在 CSS 段**
   （grep 计数：3 处，全在样式字符串；v9 已把带该 class 的会话头按钮删掉）。
   ⇒ 若非我漏看，`stamp() === gen && mounted()` 永远不会为真，页面可能被刷到 3 次上限。
   **本件不动它**（那是 gbt-master 的件），只在本 README 与 `docs/能力栏-精细设计.md` 留档。
2. `plugins/gbt-capability-bar/README.md` 的**旧版**（2026-09-22 设计稿 v0.1）已被本文件取代；
   `lib/client.js` 的旧草案（自称"不许被当成能加载的插件"）同样已被真实实现取代。
