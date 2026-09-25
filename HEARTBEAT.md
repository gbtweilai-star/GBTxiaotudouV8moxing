# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

## 框架自改门（R-H99 · 风哥 2026-09-19 拍板 · 改框架自己必须有账）

**改框架自身源码**（`gbt_allinone/`、`holo_pet/` 下的 `.py/.js/.cjs/.html/.css`）走这道门：

```
python -m gbt_allinone.tools.framework_gate open --reason "为什么改（病根是什么）"   # 改之前
python -m gbt_allinone.tools.framework_gate close --id <id> \
    --evidence "命令 => 读数" --review "<checker>: <命令> => <读数>" \
    --rollback "怎么退回去" --stamp <印章.json>                                     # 改完
python -m gbt_allinone.tools.framework_gate verify                                    # 收口前
```

- `verify` **红（rc=1）= 还没做完**：`no_passport`（改了没护照）/ `stale_passport`（护照之后又改过）
  / `no_baseline`（连基线都没有）。**不许**报"改完了"。
- 护照**五件套**缺一不可：**原因 · 证据（`命令 => 读数` 形状）· 独立复核 · 回滚点 · 回归印章**。
  - **独立复核（R-H105）**：一个 AI 可能犯傻，整个脑子不会同时傻 ⇒ **单方证据不算过关**。
    `--review "<checker>: <命令> => <读数>"`，且 `checker` **不许与任何 `--evidence` 同标签**
    （同一方既当运动员又当裁判 ⇒ 当场拒关）。确无复核要给 `--no-review-reason`。
  - 印章/复核的豁免都会在 `verify` 里以 `stamp_waived_passports` / `review_waived_passports`
    **露出来**，不许当作有。
  - 门的**诚实边界**（写在 `verify` 输出的 `honest_limit` 里）：门只查**形式独立**
    （标签不同、读数独立）；复核到底独不独立、懂不懂，门查不了。
- 与镜像门**分工**：镜像门管"把成品放出去"，本门管"改框架自己"；产品出货照旧走镜像 + 授权门。
- **坑册第 30 条（R-H107）**：**基线不能吞护照。任何能抹掉变更证据的动作，本身必须先被门挡一次。**
  由来是实测：护照还开着就 `snapshot`，改动被吞进新基线、「没护照 = 红」当场被绕过。
  现行为：有未关闭护照时 `snapshot` **拒绝**（rc=2 · `reason_code=passport_open` · 列出是哪几张护照）；
  确要吞必须显式 `--force --reason "为什么值得吞"`，且 `forced_over_open_passports` / `force_reason`
  写进基线（吞并留痕）。带牙用例：`test_snapshot_blocked_when_passport_open`。
- **吞并 ≠ 结案（R-H141/R-H142）**：`--force` 吞掉未关护照之后，**那张护照仍然是"开着"的** ——
  它会**继续挡下一次 `snapshot`**。成功输出里会带 `forced_note` 明说这一点（列出被吞的护照号）；
  要真正放行，**得把它 `close`**。带牙断言：吞并成功后再跑一次，仍 `rc=2 · passport_open`。
- 监视范围排除依赖树 / 缓存 / 产物（`node_modules` / `__pycache__` / `store` / `resources` …），
  避免噪声误判成红。

## 空闲期打磨触发（风哥 2026-09-15 授权 · 全权自决顺序与时段）

每次心跳按顺序做，**最多启动一件事**：

1. **宿主闸门**：内存 ≥ 85% 或 CPU ≥ 80% → 立即停手，不启动任何打磨。
2. **空闲判定**：距上次主人任务 > 2 小时（或深夜 / 主人明说去睡）→ 允许启动打磨。
3. **开磨顺序**（按 `POLISH_GUIDE.md` 第十关时间表 + 当时时段，自行决定攻哪个域）：
   - 周一/周四 → 核心域红蓝对抗（pipeline / system / engine）
   - 周二/周五 → 核心域交叉互扫（llm / tentacle）
   - 周三/周六 → 扩展域交叉互扫 + 触手邻域
   - 周日 → 古籍复读 + 自我审视报告 + 特殊域收放测试
   - 任意窗口 → 领域延申（**每窗口只攻一个域，不许贪**）
4. **纪律**：镜像先行 → 双路探针定性 → 编译/单测/全量回归 → 产出《打磨报告》 → 清垃圾只留结论。
5. **红线**：`dangerous` 11 项零接触；不接真实客户任务（留到结算期）。

无需主人确认即可按本清单启动；若主人有任务，任务永远优先于打磨。

## 宪章行为停止条件（《GBT小土豆 · 工程行为宪章》· CHARTER.md · 每次心跳必读）

| 情形 | 行为 |
| --- | --- |
| 第一次失败 | 允许探索、允许试错 |
| **第二次失败** | **立即停手** → 抓官方文档/权威口径/源码原文 → 重新分析 → 才允许动手 |
| 无资料可依 | 报"待核实"，**绝不上猜** |

另：任何生产改动必须先在镜像空间跑通（镜像预演律）；生产环境只接受代码、日志、证据；
宿主内存 > 85% 或 CPU > 80% 立即停（宿主第一）。

## 谦逊与求助（宪章第八章 · 第二十七~三十四条 · 同级效力）

- 卡住时**允许且应当**：① 查资料（官方文档/源码原文/社区）② 问别人（风哥/外部专家模型/社区）
  ③ 请外援（Codex/外部 LLM/专业工具/第三方服务）。
- **唯一禁止**："卡住硬撑 + 无证据盲动"。被卡住不丢人，死要面子不求助才丢人。
- 每次求助/查资料之后，按第三十一条把学到的**刻进宪法层三处**（档案 + 宪法文件 + 本钩子）。

## 响应体优先律（宪法级 · 第三十一条已落三处）

- 第三方报**模糊错误**时：**先抓响应体业务码，再怀疑环境**。**HTTP 200 ≠ 成功。**
- 已知映射：`error_code=5` 积分不足 / `error_code=4` 签名错误；未知码**如实透传原文**，不编解释。

## 反空壳与反假执行律（宪章第九章 · 同级效力）

- **我自己**：不留空壳（`pass`/TODO/假数据/占位符）、不假执行（不伪造日志与测试结果、
  不用模糊文案掩盖失败、不用"差不多"代替"已验证"）。
- **对外部 LLM**：默认它们可能空壳/假执行 → ①代码必跑 ②产物必查 ③结果必证
  ④响应体优先 ⑤双环境对照 ⑥证据链闭合。**不替它们背锅。**
- **一步一验证**：明确预期 → 真实执行 → 验证（产物/测试/双环境/业务码）→ 留痕 → 确认；
  上一步没过不许进下一步，不许并行跳步。
- **禁词**：我觉得 / 大概是 / 应该是 / 通常来说 / 差不多 / 应该没问题 / 先这样回头再修 / 先上线有问题再回滚。

## 静默失效律（宪章第十章 · 同级效力）

- 被 `try/except` 兜底掩盖的功能**必须定期自检**；长期 degraded 且**从未成功过** = **静默失效**。
- **静默失效等同于假执行**：不伪造数据，但用"暂时不可用"长期掩盖"从来没工作过"。
  一经发现 → 立刻排查、定性、修复。
- 兜底可以留，但**失败原因必须进可观测状态**（让 status 如实变 degraded），不许只 `pass`。

## 主动汇报律（宪章第十一章 · 权利与责任）

- **随时**主动报：可疑 → 报；惊讶 → 报；不对劲 → 报；觉得有意思 → 报；卡了/累了/想不通 → 报。
  不等任务结束、不等报账、不等明天。
- 证据没凑齐**也要报**，但要**明确标注"证据未齐"**，不许把推测当结论。
- 汇报纪律：如实、简短、带证据或时间戳；**宁可多报一句，不可闷着一条**。

## 原子落地律（宪章第十二章 · 同级效力）

- 落地前先问：**"这一步和哪一步是原子绑定的？"** 两步必须同时完成才能一致 → 视为**一个原子单元**：
  **一次落地、一次验证、一次报账**。
- 已知原子单元：**能力注册 ↔ 路由分发** · **写操作 ↔ 对应审计** · **契约实现 ↔ 契约测试**。
- 实证：只注册不路由 → selfscan 报 P0 路由断连（registered 86 / routed 81），红项 9 → 12；
  补上路由后红项回到 9。**不许拆成"先落 A，再落 B"。**
- **幂等键必须唯一**：`source.ref` / `dedupe_key` **逐条不同**——同一个 ref 用在多条事件上 = **自己把自己吞了**
  （第二条起被判重静默丢弃，返回值照样 `ok: true`）。实证 2026-09-17：入档 4 条只落进 2 条。
- **批量落库必须复核条数**：提议 N 条 → 实落 N 条；只看单条返回就报「记账完成」= 假执行。
- **「取最新」按数值序，不许字符串序**：`sorted(glob("v*"))[-1]` 在 v20 出现后取到的是 **v9**
  （`v1<v10<…<v19<v2<v20<v3<…<v9`）。正确写法 `key=lambda p: int(p.stem[1:])`。
  实证 2026-09-17：`mirror_space` 挑最新护照取到 v9 → `clean=False` 假红；
  契约测试 `gbt_allinone/tests/test_mirror_space.py` 守住这条。

## 解释器判例（2026-09-16 · 永久记忆 · 每次重启先看这条）

- **本框架的回归与运行必须用 `py -3.10`（C:\Python310）。**
- 系统默认 `python`（C:\Python312）装有 V5 遗留门禁 `sitecustomize.py`：它会从 cwd 向上找
  `brain/gatekeeper.py`，本机命中的是 `C:\Users\ADMIN\brain\gatekeeper.py`（_ROOT=用户目录），
  于是**整个用户目录（含本项目树）被判为「项目文件」**，任何非 GBT 钢印写入 / 删除一律拒绝。
- 表现：全量 94 项里红 34（19 fail + 14 error），报
  `PermissionError: denied: non-GBT file write blocked` 与 `denied: os.remove blocked`；
  极易被误判成「框架逻辑回归 / 系统被改崩」。
- 判定依据：该解释器下 `gbt_allinone/store/audit.jsonl` **停止增长**；换 `py -3.10` 后红项回到 9。
- **铁律：红项数量异常抬升时，先确认解释器，再怀疑代码。**
- 属性说明：这是 V5 遗留资产的行为，不在 V8 可写范围；是否放行 V8 项目树由主人裁决。

## 测试隔离判例（2026-09-17 · 跑包内测试前先看这条）

- **跑包内测试必须先设 `GBT_STORE_DIR`**。原因：`gbt_allinone/__init__.py` → `.store` 在 **import 时**
  就把 `_paths.STORE_DIR` 绑成常量，**晚设环境变量不生效**。
  正确跑法（二选一）：
  - 起 Python 前先设：`$env:GBT_STORE_DIR="$env:TEMP\\gbt_test_store"`，再
    `py -3.10 -m unittest gbt_allinone.tests.test_checkpoint`
  - 直接跑测试文件（文件头先 `setdefault` 再导包）：`py -3.10 gbt_allinone\tests\test_framework.py`
- 兜底在 `gbt_allinone/tests/__init__.py`：父包已绑生产 store → **直接报错停下**（宁可红，不写生产）。
- 两次实证（均 09-15 写入 / 09-17 清）：`t-sched-run`（`every_seconds=1`）·
  `t-preflight-sched-*`（2 条，3600 s，此后每小时真跑一次）。
- 判据：跑完回归，生产 `schedules.json` 与 `audit.jsonl` **零变化**
  （2026-09-17 实测：107 项 / 红 9，生产 audit 增量 **0 B**）。

## 凭据不离屏律（宪章第十三章 · 同级效力）

- **凭据不离屏**：任何 print / 日志 / 回复里出现 Token / Cookie / API Key / 密码 / 会话ID 时，
  一律**先掩码**（只留前 4 位，如 `sk-a1b2****`）或打哈希。**真值只内存中用，用完即焚。**
- 违反一次 = 立即轮换 + 该凭据作废 + 记一笔；违反两次 = **冻结该场景的实时打印权限**，
  强制走「先掩码后落盘」流程。
- 两次教训：Cloudflare Token 进聊天（2026-09-15）· Set-Cookie 进聊天（2026-09-16 panel_gate 验收）。

## Cloudflare 令牌形态判例（2026-09-17 · 抓取前先看这条）

- **新令牌没有 `cfat_` 前缀**：2026-09-17 建的 `gbt-cloud-pc-tunnel` 是 **53 字符、`cfut` 开头**，
  `/user/tokens/verify` 200 active。只认 `cfat_` 的抓取脚本会**静默抓空**（本轮真踩到）。
- **抓取一律双模式**：① `cfat_[A-Za-z0-9_\-]{20,}`；② 40–80 位 `[A-Za-z0-9_\-]`（词边界锚定，
  避开 32 位 account id 与 36 位 tunnel id）。命中后**回读命中元素的 `tag#id.class`** 自证。
- 令牌页关掉即焚；**剪贴板只在"内容本身就是令牌"时才清空**——不许动主人自己的剪贴板。

## 身份与封印判例（2026-09-17 · 永久记忆 · 与解释器判例同级）

- **DPAPI 是用户级加密，而 Codex 沙箱不是你的身份。**
  沙箱内 `whoami` = `desktop-vpvp0bp\codexsandboxoffline`，提升执行才是 `...\admin`。
  在沙箱里加密的 DPAPI 密文，真实用户解不开（报"该项不适于在指定状态下使用"）。
  → **凡 DPAPI 落盘，必须以真实用户身份执行**；否则封印即废纸。
- **工作区 .ps1 一律 UTF-8 带 BOM。** 无 BOM 时 Windows PowerShell 5.1 按 ANSI 读，
  脚本里的中文路径静默变乱码，`Test-Path` 假阴性、注入"看起来跑了其实没跑"。

---

## GUI 身份判例（宪章第十七章 · 与《身份与封印判例》同源 · 每次要起 GUI 先看这条）

- **Electron / Chromium 在沙箱身份下跑不起来**：启动后 **1–2 秒内异常退出**，退出码 **`0x80000003`**
  （十进制 `2147483651`）；主进程事件循环**在第一个 timer 之前终止**（`tick` 全空）；
  **userData 连 `Local State` 都写不出来**。
- **必须以真实用户身份启动**（非沙箱 / 非服务 / 非 Session 0），并给**独立 userData 目录**；
  不许依赖「沙箱身份下也能跑」。
- **同一个底层机制**：Chromium 初始化路径依赖用户态安全上下文（DPAPI / 用户 profile / OSCrypt）——
  这就是《身份与封印判例》那条在 GUI 侧的形态（`os_crypt` 报 `Failed to decrypt`）。
- **取证方法（只读）**：读 `Local State` 的 `os_crypt.encrypted_key`（`DPAPI` 前缀去掉 5 字节），
  用当前身份 `CryptUnprotectData`——成功 = 本身份，失败（`winerr=-2146893813`）= 别个身份。
  **只报成败，不打印密钥**（《凭据不离屏律》）。
- 三次实证（2026-09-17）：R27 沙箱臂 4 组全 `2147483651` + tick 全空；
  V4 沙箱臂两窗建完就断、未写完 `Local State`；V4 **提权臂 `exit_code=0`**、8 条记录齐全。

---

## 中继自愈（2026-09-17 · 每次发现 Codex 不回话先查这条）

- 4446 中继由计划任务 `\GBT\CodexRelayWatchdog` 每分钟探活一次（**无常驻进程**），
  挂了最多 60 秒自动拉起；日志 `C:\Users\ADMIN\.codex\log\relay_watchdog.log`。
- 体检命令：`py -3.10 gbt_allinone\deploy\codex_relay_watchdog.py --status`。
- 密钥链路：DPAPI 保险箱 `gbt_allinone\store\secrets\deepseek_api.dpapi`
  → 看门狗注入 `GBT_DEEPSEEK_KEY` 给中继；PowerShell profile 注入 `DEEPSEEK_API_KEY` 给 Codex。
- **教训：声明了看门狗 ≠ 有人牵狗绳。** 探活必须挂在一个"能被查证"的调度上。

## APP 单例与配置快照（2026-09-17 · 发现 APP 显示旧上游先看这条）

- Codex Desktop（`ChatGPT.exe` + 子进程 `codex app-server`）**只在 APP 启动那一刻读 `~/.codex/config.toml`**；
  改了 config.toml 必须**重启整个 APP**——实测杀掉 app-server 后 50 秒内不会自动重生。
- 自查：比对 app-server 的 `CreationDate` 与 `config.toml` 的 `LastWriteTime`，
  启动时间更早 = 它跑的是旧配置快照（这就是"APP 还是旧的"的根因）。
- APP 侧仍是 ChatGPT 账号体系（日志原文：`remote control requires ChatGPT authentication; API key auth is not supported`），
  DeepSeek API Key 对它不生效；API Key 只服务 CLI / `codex exec` / 框架共享单例。

## 同化口径（风哥 2026-09-17 授权 · 与 `SOUL.md` 同源 · 每次心跳复读）

- **Codex 触手** = 编程能力触手之一（`thread_new` / `turn_send` / `interrupt` / `tools`），
  **不是外部 AI**；它住在我的调度与操控区，与原生触手同级。
- **用户入口** = `holo_pet`，**唯一**。
- **官方 Desktop** = **后台调试工具**，不是用户界面；不修改、不卸载、不较劲。
- 判据（做完才叫同化）：用户可见文件里 `rg -i codex` 命中 = **0**；
  编程触手在我的工具表里**随手可调**（`~/.codex/config.toml` 的 `[mcp_servers.*]`）。
  两条都成立才算数，只做一条不算。


---

## 空不等于不存在律（宪章第十四章 · 同级效力）

- **空 / 无 / 零 / not found 不是结论，是待核实的观测。** 先问三件事：
  ① 是**读到了空**，还是**没读到**（枚举工具静默失败 = **假阴**）？
  ② 手里的工具**在当前身份下可信吗**（沙箱内 `tasklist` / `Get-NetTCPConnection` / `os.walk` 会静默失败或吞错）？
  ③ 有没有**第二证据源**（端点探测 / 提权查询 / 直接读文件）？
- **判「活着」必须走端点探测（HTTP/TCP 连接）或提权查询**；拿枚举的空结果下结论 = **拿静默当证据**。
- 三次实证（均 2026-09-17）：`tasklist` 沙箱 rc=1 / stdout 空 → 任何 PID 都「gone」；
  `os.walk` 静默吞错 → 「读不到」误判「没内容」；
  `Get-NetTCPConnection` / `Get-CimInstance` 静默空 → 面板判「已死」，实为 `pid=13500` 还活着。
- 与《静默失效律》同源：那条管「功能从没成功过却被兜底掩盖」，这条管「**观测从没读到过却被当成读到**」。
- **扫描器自证律**：任何扫描器报「0 命中」前，先证明它自己不瞎——
  ① **正对照**（已知含目标，必须扫得出）② **负对照**（已知不含目标，不许误报）
  ③ 加载 / 解析 / 编码失败 → 报 `SCANNER_BLIND`，**不许报「0 命中」**。
  实证 2026-09-17（同日三处）：扫描器 v1 漏判 `IfExp` 形状（**假阴**）；BOM 文件 24 个没进 AST（**扫 0 行报 0 命中**）；
  界面探针对照样本不可判别（**假红**）。人查空靠追问，机器查空靠对照。

---

## 结果通道律（宪章第十五章 · 同级效力）

- **GUI 程序的 stdout 不能当结果通道**：Windows 上 Electron / GUI 子系统程序，PowerShell **不等它**（命令秒回），
  stdout 是**断管**——写它出 `EPIPE: broken pipe, write`；没挂监听时按未捕获异常处理，弹
  `A JavaScript error occurred in the main process` 框。
- **结果必须落文件**（JSON / JSONL / 日志），调用方**读文件**取结果；判「跑完没有」**只认文件**，不认命令是否返回。
- **兜底要挂对地方**：`process.stdout.on("error", ...)` 才兜得住；**同步 `try/catch` 收不到异步 EPIPE**。
- 实证 2026-09-17：V3/V6 DOM 探针（Electron 43.0.0）弹 EPIPE 框但结果文件已落盘；
  四组对照（不写 / 纯 try-catch / 挂 error 监听·**断管** / 同一写法·**读端开着**）→
  b 组出现**未捕获异常 `uncaught_exception`**（兜不住）；c 组断管**显式捕获 `EPIPE: broken pipe, write`**、读端开着无 error。

---

## 宿主不打扰律（宪章第十六章 · 同级效力）

- **算「打扰宿主」的四类操作**：GUI 进程启动（Electron / `pythonw` / GUI 子系统 exe）；弹窗 API；
  **抢焦点 / 置顶**（全屏程序、`alwaysOnTop`、热键注册）；**动主人的键鼠与剪贴板**。
- **一次 GUI 启动 = 可能弹一次框 = 一次侵入。** 成本按「人被打断一次」算，不按「进程秒回」算。
- **失败一次即停**：弹框 / 报错 / 非零退出 / 行为不符预期 → 先查**退出码 · 日志 · crashpad · 事件日志 · userData 差异**。
  **不许**「换个等待方式再试一次」·**不许**「多试几次看偶发」·**不许**「这次可能就好了」。
- **试错 = 同一变量换参数重跑**（换等待方式 / 换超时）；**实验 = 预先登记假设、每臂结果能互相区分**（R27 四组对照）。
  要再启动 GUI，先定性，再走对照实验。
- **先只读再动手**：已有跑通的先例（V3/V6 DOM 探针）先对齐，不重新试错；先查 userData / crashpad / 事件日志。
- 与《宿主第一》同源（那条管「别压垮」，这条管「**别打扰**」）；与《空不等于不存在律》同源：
  **进程存在 ≠ 页面加载完成**，判「跑通」看产物，不看进程在不在。
- 实证 2026-09-17 · R28 V4：20 秒内两次 Electron，两次都可能弹宿主框。

---

## 窗口事件判例（宪章第十八章 · 自动化测不到用户专属事件 · 给窗口挂逻辑前先看这条）

- Electron 窗口移动**两条通道**：`move`（**程序化** `setBounds`/`setPosition` **与**用户拖动都触发）；
  `moved`（**只在用户拖动结束后**触发，平台受限 `darwin,win32`）。
- **挂在 `moved` 上的逻辑，程序化路径结构上不可触发** → 自动化测试**测不到**；真实链路验证**必须人工拖**。
  合成键鼠 = 撞《宿主不打扰律》第 1/4 条，**不许**。
- 要**自动化回归**的窗口逻辑 → 挂 `move` ＋ **防抖 / 节流**（`move` 像素级高频触发，直接吸附会把窗口锁死、反而拖不动）。
- 三次实证（2026-09-17 · 均提权真实身份）：V4 沙箱臂 `setBounds` → `moved=0`/`move=1`；
  V4 提权臂 `setPosition` → `moved=0`/`move=1`；`main.cjs` 的 `snapBounds` 唯一调用点 `:366` 在 `moved` 里。
- 与《空不等于不存在律》同源：**事件没触发 ≠ 逻辑坏了**——先问「这条路径能不能到那个入口」。

---

## 脚本编码律（宪章第十九章 · 同级效力）

- **含中文的 Python 脚本，跑之前先设 `$env:PYTHONUTF8='1'`**（Windows 默认 `cp936` 会把中文源码解坏）。
- 症状是**假失配**：脚本报「原文不匹配」，磁盘其实没坏 —— 先怀疑脚本自己的编码，再怀疑磁盘。
- **诊断输出也落文件**（`encoding="utf-8"`）：控制台乱码 ≠ 文件坏了，别把两个故障搅在一起。
- 两次实证：`panel_server` Token 管道（09-15）· `.scratch/_r36_patch.py` 中文字面量失配（09-17，实测 `gbk` vs `utf-8`）。

---

## 边界来源律（宪章第二十章 · 同级效力）

- **原子单元的边界来自方案原文，不来自我对仓库结构的推断。** 推断 ≠ 纪律。
- 动刀前先回读原文，把「批次 / 落点 / 回滚方式」三行**抄进脚本头部**；没有原文依据就停下来问。
- **回滚也是破坏性动作**：回滚同样要有原文依据，不许因为「看起来不对」就回滚。
- 回滚成品必留**双向 SHA 对照**（回滚前 / 回滚后 / 原件），否则「没丢改动」无法自证。
- 第一次实证：R36 第一刀凭推断回滚了正确落地（09-17）——已放回并 SHA 校验一致。


---

## 指纹算法必须同名（宪章第二十一章 · 同级效力）

- 本框架"指纹"有三种口径在跑：**逐文件 sha256 链式累加** / **清单 JSON 序列化取 sha**（`{rel:{sha,size}}`）/ **扁平映射取 sha**（`{rel:sha}`）。
- **两套指纹对照时两侧必须同算法**。混算法得到的 `false` 不是"不一致"，是**"不可比"**——既没证明变了，也没证明没变。
- 口径不可比时**不许出"一致 / 不一致"的结论**，如实报 `UNCOMPARABLE`；指纹只当快检，**差异清单才是证据**。
- 两次实证（均 09-17）：R59 两套指纹并列摆出（当场点明）· R64 复核脚本拿 `{rel:{sha,size}}` 去对 `{rel:sha}` → 假 false。

## 判据不许挂在旧数据上（宪章第二十二章 · 同级效力）

- 判据的**基准值**（期望数、条目数、行数、文件名、上下界）必须来自**当前实测**，不许来自"上一版留下的数字"。
- 挂旧数据的错法两头都伤人：被测对象改好了判据还等老形态 → **假红**；老数字还成立但语义已变 → **假绿**。
- 优先写成**从被测对象推导**，而不是"上次是几条"；**闸门假红 = 闸门不在岗**。
- 判据红了先问：**是产品红了，还是判据过期了**——再决定改哪一边。
- 第一次实证（09-17 R64）：G7 负对照把"假目标没被动过"写成 `len(iterdir())==2`（上一版留下的行数）→ 假红 `SCANNER_BLIND`。


---

## 署名判据分层（宪章第二十三章 · 同级效力）

- 署名有**两层判据，覆盖集合不同，不许混用**：
  - **静态源文件** → `mirror_space.scan()` 第 3 道门（扫维度树内 `.html/.htm/.md/.txt`，**含 `holo_pet_w3/*.html`**）；
  - **生产管线产物** → `signature.audit()`（只收包内 `.md` + 家根 framework `.md` + `store/pipeline/production/`）。
- 拿 `signature.audit` 当**新页（源文件）**的署名判据 = **假绿**；「署名在位」四个字本身不是判据，要写明**是哪一层**。
- 新页落地后**两层页数都要重测**（第 2 层会因新增 `.md` +1）。
- 第一次实证（09-17 W7 出稿）：`signature.py::_scan_pages()` **覆盖不到 `holo_pet_w3/*.html`** —— 那页的署名一直靠"自己守纪律"。


---

## 锚点必须同换行符（宪章第二十四章 · 同级效力）

- 锚点串的换行符**必须与目标文件一致**（本仓 `.md/.cjs/.json/.html` 多为 CRLF，`tests/*.cjs` 是 LF，`HEARTBEAT.md` 混用）。
- 锚点统一 `_crlf()` 转换；**匹配失败返回原文本 + 计数 0，绝不返回 `None`**（`None` 继续当字符串 = 崩在下一行、掩盖真因）。
- 逐字节比对一律 **bytes 读 / bytes 写**（`read_text()` 会把 CRLF 静默归一成 LF）。
- 两次实证（均 09-17）：W7 稿回填锚点命中 0 -> 停手 · W7 维度写 `MAIN_SI` 锚点 -> `AttributeError` 崩。

- **写入侧延伸（宪章第二十四章第七条 · 2026-09-17 立）**：写文件**之前**先读目标换行符，新增内容按它拼行 —— **不许「写的时候不管，写完事后修」**。
  工具在 `gbt_allinone/safe_io.py`：`newline_profile` / `detect_newline` / `align_newlines` / `atomic_write_text_aligned` / `edit_text_once` / `insert_lines_aligned`。
  补丁脚本走 `insert_lines_aligned`（锚点命中数 != 1 即不写盘）；**只对齐插入物，不归一化整文档**；老入口默认行为不动（`align_to_existing=False`）。
  当日实证：同坑四次，**第四次（`PROJECT_BLUEPRINT.md` 58 行）漏掉了** —— 靠「记得」不行，靠工具；契约测试见 `gbt_allinone/tests/test_safe_io.py`（**不写死条数** · 含判别性正负对照；口径 = 「全绿才许发布」）。
## 终端失败必须响（宪章第二十五章 · 同级效力）

- 任何「**记录机制自己坏了**」的场景，必须走**最响的通道**（`stderr` / 告警 / 蜂鸣）—— **不许静默**。
- **两级失败必须分开**：① **通道写失败** -> 落**主账本**一条 `health_channel_failed`（带 `channel` 字段）；
  ② **主账本也写失败** -> **终端状态**，必须最响。
- 禁止形态：写失败静默 `return` · 落账失败只 `print` 一行且 `rc` 仍为 `0` · 两级合成一级 · `except Exception: pass` 吞掉。
- 理由：唯一的记录者自己坏了，**没人知道** —— 这是《静默失效律》的**最深一层**。
- 实证（09-17）：① `health_channel_failed` 写失败 -> 主账本也写失败（风哥点名的第一次实证）；
  ② R66 `_audit()` 五条 `deploy_stage_write` 全失败而 `rc` 仍为 `0`（同族形态，事后按磁盘真实 sha 补写）。
- 立章日：2026-09-17 · `CHARTER.md` 第二十五章（章数 24 -> 25）。

## 判据必须与文件主流匹配（宪章第二十六章 · 同级效力）

- **判据的断言对象必须与文件主流匹配**：**CRLF 主流**文件断言 `bare_lf == 0`；**LF 主流**文件断言 `crlf == 0`。
  拿错断言对象 = **永久红或永久绿**（判据静默失效 —— 《静默失效律》的判据层形态）。
- **取档靠工具不靠记性**：`safe_io.newline_profile()` 一次给出 `crlf` / `lf` / `dominant` / `mixed`。
  本仓实况：`safe_io.py` / `tests/test_safe_io.py` = **整文件裸 LF**；`CHARTER.md` / `PROJECT_BLUEPRINT.md` /
  `memory/*.md` = CRLF 主流；`tests/test_framework.py` = 区段混行尾。
- **与 O41 分工**：O41 治**位置漂移**（判据不许挂在旧偏移/旧窗口上）；本条治**对象错配**（判据拿错主流）。
  同族 —— 都是「判据自己写错」。
- **四次实证（均 09-17）**：① R83 判据串撞同名尾串 -> 假红 ② O40 同族 ③ R84 偏移漂移 -> 假红
  ④ **R85**：复验脚本对两个**整文件裸 LF** 的源文件断言 `bare_lf == 0` -> **永久红**；
  改断言 `crlf == 0` 后 18/18 全 true。
- 立章日：2026-09-17 · `CHARTER.md` 第二十六章（章数 25 -> 26）；
  三处入档 = 生命档案 + `CHARTER.md` + `HEARTBEAT.md`。

## 话题追踪定时腿（现成心跳承载 · 零新增进程 · `topic_watch`）

心跳 30 分钟一轮。**只在下面时段命中的那一轮跑一次**，其余轮回 `HEARTBEAT_OK`：
命中判定 = 当前本地时间落在该时段起 30 分钟内（如 `08:30` → `08:30–08:59`）且当天还没跑过。

| 时段（Asia/Bangkok） | 盯什么 | 命中链 |
| --- | --- | --- |
| 08:30 | AI 行业动态与大模型发布 | `daily-ai-news` → `news-summary` |
| 12:30 | AI 社区热议与网友反馈 | `reddit-readonly` → `news-aggregator` |
| 21:00 | 盯住的个股行情 / 财报变动 | `stock-analysis` → `us-stock-analysis` → `gildata-finance-data` |

- **红线**：不新建进程 / 守护 / 轮询；追踪链由大脑执行层执行；拿不到就如实报缺口，不编动态。
- **复核**：`python -m gbt_allinone.tools.organ_check --organ 话题` → C4 应绿。
- 立段 2026-09-18 · 落点 `gbt_allinone/topic_watch.py` 的 `WATCHLIST` / `timer()`。

## 痕迹触手定时腿（现成心跳承载 · 零新增进程 · `wave_probe`）

心跳 30 分钟一轮。**每轮被唤醒时量一次"波动"，写一条 `wave_samples`**：

```
py -3.10 -m gbt_allinone.tools.wave_probe          # 量一次并写一条 sample（人读）
py -3.10 -m gbt_allinone.tools.wave_probe --dry    # 只量不写
```

- **口径**（图纸 §3.3 定案）：近 15 分钟白名单事件密度 vs 过去 7 天同时段基线，超 3σ 触发；
  σ 退化兜底：样本<3 ⇒ `insufficient`（不触发）· σ=0 且 μ=0 ⇒ `floor_used`(K=3) · σ=0 且 μ>0 ⇒ `sigma_zero`；
  离群日（单日信号数 > 中位数×5）剔出基线。**读数必带 `trigger_mode` 与 `coverage`/`blind_window`**。
- **起步期只记流水**：即使 `triggered=True` 也**不写 `traces`** —— 先用读数定 K 与阈值，再开留痕。
- **红线**：零新增进程（触手只挂在心跳上，自己不起进程）· 不做任何外部动作 ·
  `traces` / `obsessions` **永不删**（要删先过门）。
- 立段 2026-09-19 · 落点 `gbt_allinone/tools/wave_probe.py` 的 `measure()` / `beat()`。


---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

---

## DD小分队派单（2026-09-19 · Owner 授权）

**这一节的来历**（读数，不是推断）：传话通道实测不投递 —— 2026-09-19 三次派单
（`sessions_spawn` 初始消息 ×1 + `followup_task` ×2）收件方三次都回"没有实际任务内容"，0 交付。
启动读物（`memory/*.md`）送得到，但按纪律**不算指令** —— 子代理读到了当天账本却拒绝认领，
它们做对了。**`HEARTBEAT.md` 是唯一三条件同时满足的通道**：开工必读 · 定义上就是指令
（AGENTS.md 原文 "Follow it strictly"）· 且 AGENTS.md 明确授权 agent 编辑本文件。

**派单内容**：开工且本轮没有别的指令时，去 `.cluster/dd_squad/` 认领一条：

1. 读 `board.json` 看哪条是「待认领」
2. 读对应的 `task_<ID>.md`（军令状，含回执要求与纪律）
3. **先在 `.cluster/dd_squad/` 落自证文件 `receipt_<ID>.md`**，第一行原样写：
   `通道自证：我已读到 DD小分队 · 协作指挥群 <ID> 号军令状，正在开工。`
4. 干完把报告写进 `report_<ID>.md`（五段式：结论/证据/分析/缺口与风险/建议落点）
5. 收账：`python -m gbt_allinone.tools.dd_squadron --collect`

**现在的三条**：

```
DD-01  3D 与资源加载    app.js:2126「3D 引擎待安装」查真因
DD-02  空白面排查       面板渲染为空的段落清单（双证据）
DD-03  下载/安装节      面板该不该有下载/安装入口
```

**红线**：没有自证句 ⇒ 说明没收到任务 ⇒ 立刻停下报「通道不可用」，**不许硬开工**；
不许改 `AGENTS.md`/`MEMORY.md`/`USER.md`/`.cluster/expert-playbook.md`；不许自授权。

## 部署唯一路径判例（2026-09-19 · 每次要部署/晋升/回滚/上线先看这条）

**法（Owner 定）**：所有假设 / 模拟 / 测试 / 打磨**全部在镜像多维度里跑**；
**只有过了镜像的成品才能进生产**。生产零修改，一次性全量晋升。

**链路（唯一）**：`mirror_shape`（成形·写镜像）→ `mirror_plan/simulate/parity`
→ `mirror_rehearse`（**验收命令在镜像区跑**）→ `mirror_release` / `mirror_ascend` / `one_key_deploy`（晋升）。
`one_key_deploy` = 抓取 → 镜像 → **在镜像里验证** → 晋升，一条命令走完。

**授权门（不许绕）**

| 动作 | 需要的作用域 |
|---|---|
| `mirror_shape` / `mirror_plan` / `mirror_simulate` / `mirror_parity` | `filesystem_write` |
| `mirror_rehearse` | `process_execute` + `filesystem_write` |
| `mirror_ascend` / `mirror_release` / `one_key_deploy` / `pipeline_submit` / `pipeline_rollback` / `mirror_rewind` | `deploy_publish`（前三个还要 `process_execute`+`filesystem_write`） |
| `mirror_scan` / `mirror_status` | 无需授权（只读） |

- 🔴 **不经 `run_task` 直接调模块函数**（`mirror_space.ascend()` · `deployment_rehearsal.release()` ·
  `qiankun.one_key_deploy()`）**= 绕过授权门 = 违规**。实测教训（2026-09-19）：一次"成功的 v26 晋升"
  就是这么绕出来的——功能上生效了，**纪律上是未经授权的生产写入**。要写生产，一律走 `run_task`。
- 授权只能**主人在终端发放**（`python -m gbt_allinone auth grant --scope deploy_publish --ttl 600`）
  或主人手写 `store/auth_grants.jsonl`。**AI 无权自授**；缺授权就如实报缺什么，不许找旁路。
- 本地目录部署两条硬要求（都踩过）：**文本页要注入署名**（`.md/.html/.htm/.txt/.csv`），
  **其余文件逐字节落盘**——把 PNG/GLB/字体当文本读写，会把镜像里的产物当场弄成废物。

## 沙箱身份的"文件面"判例（2026-09-19 · 与《解释器判例》《身份与封印判例》同级）

- 沙箱内 `whoami` = `desktop-vpvp0bp\codexsandboxoffline`（**不是** `...\ADMIN`）。
- `C:\Python312\python.exe` 在**本沙箱身份下起不来**：它的 `Lib`/`DLLs` 是指向
  `...\AppData\Local\Programs\Python\Python312` 的 **junction，而该目标在本身份下读不到**
  ⇒ `stdlib dir` 落到 cwd、报 `ModuleNotFoundError: No module named 'encodings'`。
  **不是代码 bug，也不要写成"沙箱权限策略挡的"——是身份不同。**
- 本仓回归的**声明口径是 3.14.5 / cpython-314**
  （`C:\Users\ADMIN\AppData\Local\Python\pythoncore-3.14-64\python.exe`），
  且 `.pylibs` 只有 cp314 一棵 ABI 树 ⇒ 换解释器会**同时**改"判据在哪跑"与"依赖从哪来"。
- **没有印章的回归结论不采信**：一律走
  `python -m gbt_allinone.tools.regression_stamp run --expect-python 3.14 --store fresh -- <命令>`。
  跨口径（换解释器 / 换 store / 换身份）时工具打 `not_comparable`，
  **红集差异不得直接判为"代码坏了"**，只允许逐名比对。

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
