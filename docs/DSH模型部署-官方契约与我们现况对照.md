# DSH 模型部署 · 官方契约与我们现况的逐条对照

> 取证日期 **2026-09-25** · 取证方式：**读盘上安装的官方包**（版本与本机宿主逐字对齐），
> 不读网上博客、不看二手教程。
> 一手件（全是本机现读，非引用）：
> - `@deepseek-ai/dsh-base@0.1.5-rc.3` — `README.zh.md` / `cordis.patch.yml`（19,515 B）
> - `@deepseek-ai/dsh-llm-pi-ai@0.1.5-rc.3` — `README.zh.md`（22,703 B）**← 我们挂 provider 用的就是它**
> - `@deepseek-ai/dsh-llm@0.1.5-rc.3` — `README.zh.md`（14,663 B）← 服务层权威
> - `@deepseek-ai/dsh-llm-retry` / `dsh-host-plugin-inventory` / `dsh-client-ui-settings-models`
> - 落点：`~/.dsh/profiles/node_modules/@deepseek-ai/`（**240 个包**）
> 本机 `dsh --version` = **0.1.5-rc.3**（与 npm latest 一致，没落后）

---

## 一、「我们这种方式」的准确定义（先钉死，否则谈不上"最完美"）

组合树有四层，**从上到下覆盖，每层只覆盖它点到的东西**：

```
~/.dsh/profiles/web/cordis.yml        空的入口列表（真的就一行 `[]`）
        ↑ 由三类补丁依次组合：
   ① package.json 的 dsh.profile.bundles   →  @deepseek-ai/dsh-base
                                             @deepseek-ai/dsh-web-app
   ② cordis.patch.yml                      →  我们自己的行（含 llm-pi-ai 的 gbt-potato / gbt-free）
   ③ --patch 覆盖层                        →  临时覆盖
```

原话（`cordis.yml` 全文）：

> dsh profile root — an empty entry list. The tree is composed as patches:
> each bundle in package.json's dsh.profile.bundles, then cordis.patch.yml, then any
> `--patch` overlays. **Edit cordis.patch.yml, not this file.**

`profiles/web/package.json` 现读：

```jsonc
"dsh": { "profile": { "bundles": ["@deepseek-ai/dsh-base", "@deepseek-ai/dsh-web-app"],
                      "patchReload": "live" } },
"dependencies": {
  "gbt-potato-master-v6": "file:.../gbt-master-compat-v6",
  "gbt-potato-master-v8": "file:.../gbt-master",
  "gbt-potato-master-v9": "file:.../gbt-master"     // ← 本地插件以 file: 依赖挂上来
}
```

**⚠️ 官方对本地插件的立场（`dsh-base/README.zh.md`）**：本地插件是 `file:` 依赖、按**包名**解析到行；
官方另有 `dsh plugin --profile <name> add <pkg>` 这条正规通道。
**我们三个 `gbt-potato-master-v*` 全指向同一个目录**（v8/v9 同路径）—— 换包名即换代，
这是仓里已知的"页面入口消失"病根的三层对策之一（见 `memory/2026-09-22.md`）。

---

## 二、官方契约（逐条摘录，每条都标出处）

### 2.1 `apiKeyEnv` 是**凭据引用**，不是环境变量名

> `apiKeyEnv` 是按请求经 **harness 凭据 seam** 解析的凭据引用，**因此配置文件绝不包含密钥**；
> 解析为空的引用会让请求以 `MISSING_CREDENTIAL` 失败。省略它会让路由保持
> **已配置但无密钥（configured-but-keyless）** 状态。

⇒ 我们的 `~/.dsh/.credentials.yaml` 里存 `GBT_POTATO_API_KEY` **正是走这条 seam**，
所以它不该"再配一遍环境变量"——§四·3 解释为什么这条对我们特别重要。

### 2.2 🔴 改路由**不必重启**：settings 分节与组合分节**按提供方合并**

> profile 通过可选 settings seam **每次操作重新读取**：base 与用户的 `llm-pi-ai:` 设置分节
> **按提供方合并**，因此用户可以新增路由、覆盖组合路由的一个字段或把路由指向另一个代理，
> **全部在下一个请求生效、无需重启**。

⇒ **这是"最完美部署技术"的核心一句。** 我们目前把路由**写死在 `cordis.patch.yml`**，
改一次要重启宿主 —— 比官方姿势差一档。

**两条实测约束**（同一节，逐字）：
- > **设置可以新增或覆盖路由，不能移除组合路由** —— 用户层覆盖组合 base，因此删除
  > `cordis.yml` 提供的提供方属于组合变更。
- > **分层合并对字典键没有删除** —— base 声明的 `reasoningEfforts` 等级、`modelOverrides`
  > 条目或 `compat` 字段可以被用户层覆盖，但**不能被移除**。

### 2.3 手工声明路由的三条硬性要求

> pi-ai 不提供的路由需要 **`api`、`baseURL` 与非空 `models` 列表**；无法服务的 profile
> 会在写入处被拒绝，并点名路由与模型。

且路由键必须落在**记录文法**内：

> 落在记录文法之外——**小写连字符标识符**——的手工声明路由键**无法登录**，因为对它的记录写入
> 会以 `LlmError('UNSTORABLE_PROVIDER_ID')` 拒绝。

⇒ 我们的 `gbt-potato` / `gbt-free` 都符合 ✅；`gbt-potato` 三要素齐 ✅。

### 2.4 🔴 自托管端点（vLLM）的两条专属开关

> 对于**自托管 Chat Completions 端点**，`thinkingTokenBudgetField` 选择推理预算参数，
> **`vllmPriority` 在服务端启用优先级调度时设置整数调度优先级**。模板参数接受 `$var: thinking.budget`。

⇒ 这**正是 `dsh-llm-qwen-local` 那条路的官方对应能力**。
⇒ 我们如果真上自建 vLLM，这两个字段是**官方点名要配**的，我们现在一个都没配。

### 2.5 🔴 无密钥本地服务器的**必需条件**（最容易踩）

> **未认证路由取决于其协议** —— 不点名凭据的路由解析为已配置但无密钥，但 **pi-ai 的
> OpenAI 兼容实现仍要求 API 密钥或 `Authorization` 标头**，因此**无密钥本地服务器需要由
> `apiKeyEnv` 引用或 `headers` 中的 `Authorization` 条目提供的占位凭据**。

⇒ **本机 vLLM / Ollama / LM Studio 这类不需要真密钥的服务，也必须塞一个占位凭据。**
不塞 = 直接失败。（我们 `gbt-free` 指向本机 `127.0.0.1:31415`，`apiKeyEnv: FREELLMAPI_API_KEY`
**未配** ⇒ 按契约应是 `MISSING_CREDENTIAL`，与我实测的"连不上"一致。）

### 2.6 失败携带**稳定 code**（我们白掏了一次 502）

> 失败携带稳定 code：无法使用的凭据以 `INVALID_CREDENTIAL` 失败并点名路由与引用，
> `apiKeyEnv` 引用解析为空的路由以 `MISSING_CREDENTIAL` 失败，未配置模型以 `UNKNOWN_MODEL` 失败，
> 终止性提供方失败则区分 **`QUOTA`** 与暂时性 **`RATE_LIMIT`**。

**但同一份文档也写明**：

> **提供方 HTTP 状态不可用** —— pi-ai 错误事件不跨提供方暴露稳定 HTTP 状态。

⇒ 所以 **`QUOTA` 这个 code 本该直接告诉我们"配额用尽"**，不需要我 curl 掏 502 响应体才知道。
⇒ 我们昨天掏 502 那次，**等于绕过了官方给的诊断通道**。这条要写进排查纪律。

### 2.7 重试策略

> 每个 profile 都可以设置 `retryPolicy`；省略时使用 **normal mode、最多重试五次**。
> …由 `dsh-llm-retry` 执行。
> **重试策略由提供方自有，而非 SDK 重试** —— pi-ai SDK 重试保持禁用，
> 因此持久 agent 步骤与 `llm/retry` 事件拥有每个可见尝试。

⇒ "断断续续"的观感里，有一部分**可能只是官方在按 5 次重试兜底** ——
表面看是"一会儿通一会儿不通"，实际是重试在救。**这条值得单独查**（未验）。

### 2.8 🔴🔴 **输入模态声明 = 能不能看图的开关**（本文件最重要的一条）

服务层权威（`dsh-llm/README.zh.md`）：

> **图片投影遵循捕获的路由** —— **只有支持图片的模型**会把持久 `ImageBlock` 引用转换为
> 路由专用请求版本；**纯文本模型接收稳定占位符**。
>
> 请求会对照其精确模型的能力——上下文窗口、输出默认值、推理强度、**输入模态**与
> `systemPromptUpdate` 模式——校验，填入任何适配器配置的默认值。

适配器层补充（`dsh-llm-pi-ai`）：

> **模态声明不受校验** —— 声明 `image` 而其网关不支持的模型会在**提示词准入后**被提供方拒绝。
> **持久图片仍留在历史中**，同一误声明模型可能**再次失败**；切换到纯文本模型仍然可行，
> 因为共享 LLM 运行时会针对该请求**把图片引用投影为稳定文本**。
>
> **system 或 assistant 历史中的图片**（包括首条系统消息中的图片）在两条转换路径上
> 都会以 **`UNSUPPORTED_CONTENT`** 失败。

⇒ 三个可操作结论：
1. **没声明 `image` 的模型 = 纯文本模型 = 图片被换成占位符，模型根本看不到，且不报错**（静默失效）。
2. **误声明 `image` 有粘性代价**：图片留在历史里，会**反复失败** —— 所以只能给**实测过**的模型声明。
3. **只有 user 消息里的图片能走**；system / assistant 历史里的图片必失败。

---

## 三、我们现况 vs 官方契约（逐条审计）

| # | 官方契约 | 我们现读 | 判定 |
|---|---|---|---|
| 1 | 组合树 = bundles → `cordis.patch.yml` → `--patch` | ✅ 结构与之一致（`cordis.yml` 仍是 `[]`） | ✅ 对 |
| 2 | 本地插件走 `file:` 依赖或 `dsh plugin add` | ✅ 三个 `gbt-potato-master-v*` 是 `file:` | ⚠️ **v8/v9 同路径**（换名换代的老对策） |
| 3 | `apiKeyEnv` 经 harness 凭据 seam | ✅ `GBT_POTATO_API_KEY` 在 `.credentials.yaml` 里 | ✅ 对 |
| 4 | **改路由走 settings，下一个请求生效、无需重启** | 🔴 **全写死在 `cordis.patch.yml`** | 🔴 **差一档** |
| 5 | 手工声明路由键须小写连字符 | ✅ `gbt-potato` / `gbt-free` 都合规 | ✅ 对 |
| 6 | 手工声明要 `api` + `baseURL` + 非空 `models` | ✅ 两条都齐 | ✅ 对 |
| 7 | **自托管端点配 `vllmPriority` / `thinkingTokenBudgetField`** | 🔴 **一个没配**（`dsh-llm-qwen-local` 还没装） | 🔴 **缺** |
| 8 | **无密钥本地服务器要占位凭据** | 🔴 `gbt-free` 的 `FREELLMAPI_API_KEY` **未配** | 🔴 **缺（且已实测连不上）** |
| 9 | 失败带稳定 code（`QUOTA` / `MISSING_CREDENTIAL` …） | 🔴 昨天是自己 curl 掏 502 才看到配额 | 🔴 **没走官方通道** |
| 10 | `retryPolicy` 默认 normal × 5 | ⚠️ 没显式配（走默认） | ⚠️ 未验 |
| 11 | **支持图片的模型要声明输入模态** | 🔴 **73 个模型条目的 `input` 全是 `[]`，`image` 声明 0 个** | 🔴🔴 **见下** |

### 路由与模型现读（实测缩进解析，不是猜）

```
[unified]   baseURL=http://127.0.0.1:31415（FreeLLMAPI · 实测死的）  defaultInput=[text]  3 模型
            agnes-3.0-flash · agnes-2.5-flash · nemotron-3-ultra-550b
[cerebras]  baseURL=https://apihub.agnes-ai.com（活）                defaultInput=[text]  2 模型
            gemma-4-31b · gpt-oss-120b
[opencode]  baseURL=https://apihub.agnes-ai.com（活）                defaultInput=[text]  68 模型
            claude-* ×14 · qwen3.5/3.6-plus · deepseek-v4-* · gemini-* · glm-* …
[组合层]     gbt-potato → gbt-potato-cloud-10.lopaycn.workers.dev/v1（活，但 502 配额）
             gbt-free   → http://127.0.0.1:31415/v1（死）
```

**合计 5 条路由**（settings 3 + 组合 2，按官方契约**按提供方合并**）。

---

## 四、「不能看图」的完整因果链（三条独立断路，全部实测）

**第 1 条 · 模态没声明（根因，最隐蔽）**
73 个模型 `input: []` + 三条路由 `defaultInput: [text]` ⇒ 图片被投影成**稳定占位符**，
模型看不到，**且不报错**。

**第 2 条 · 能看图的模型挂在死路由上（实测映射）**
`agnes-2.5-flash` / `agnes-3.0-flash` 我**实测过**真能看图（答对了"红底白正方形"和
"蓝底三个黄圆"，连数量都对），但它们**只出现在 `unified` 路由下**，
而 `unified` 的 baseURL 是本机 FreeLLMAPI（`127.0.0.1:31415`）——**实测连接被拒**。
活着的两条路由（`cerebras` / `opencode`，直连 agnes 网关）的模型表里**没有它们**。

**第 3 条 · 组合层那条腿自己也在修（已修完）**
`gbt-potato` 是**纯文本**上游（Worker 自认 `weights_ours: false` → `@cf/openai/gpt-oss-120b`），
且 `worker.js:282` 把 messages 原样透传、**没有任何图片分支** ⇒ 结构性不可能看图。
**她自己的原生视觉**（`gbt_allinone.vision` → `cloud_recognize`）已于本日接通
（见 `memory/2026-09-25.md`「把她自己的原生视觉接入」一节）。

---

## 五、最完美部署技术：落地清单（按官方契约排序）

> ⚠️ 下面每一条都**待主人拍板**；本文件只出方案与依据，**未改任何宿主配置**。

### 5.1 立刻可做（零重启、零风险、直接修「不能看图」）

**往活着的那条路由加一个模型条目，并声明模态。** 官方契约说 settings **下一个请求生效**。

```yaml
# ~/.dsh/settings.yaml → llm-pi-ai → providers → opencode → models 列表里**新增**：
      - id: agnes-2.5-flash
        name: Agnes 2.5 Flash（实测能看图）
        contextWindow: 131072
        maxTokens: 32768
        input: [text, image]        # ← 官方开关：支持图片的模型必须声明
```

依据：**我已实测**该模型读图正确（红底白方块 → "红底白正方形"；蓝底三黄圆 → "蓝底三个黄圆"）。
`opencode` 的 `baseURL` 已是 `https://apihub.agnes-ai.com`（**就是实测通过的那个网关**）。

⚠️ 契约提醒：**只有 user 消息里的图片能走**；system/assistant 历史里的图片必 `UNSUPPORTED_CONTENT`。
⚠️ **只给实测过的模型声明** —— 误声明会让图片粘在历史里反复失败。

### 5.2 把路由配置迁到 settings（官方姿势，换来"改路由不用重启"）

组合层保留**必须随组合走的**（与插件包同生命周期的），把**可调的**（baseURL / displayName /
模型表 / retryPolicy）放进 `settings.yaml` 的 `llm-pi-ai:` 分节。
契约允许"新增或覆盖"，**不允许移除组合行** —— 所以要撤一条组合路由只能改 `cordis.patch.yml`。

### 5.3 补官方点名的自托管两件套（真上 vLLM 时）

```yaml
      - id: <自建路由名>
        api: openai-completions
        baseURL: http://<GPU 机器>:8000/v1
        apiKeyEnv: <占位凭据>          # ← §2.5：无密钥本地服务器**也必须**塞占位凭据
        # vllmPriority: 0               # §2.4：服务端启用优先级调度时才设
        # thinkingTokenBudgetField: ... # §2.4：推理预算参数
```

### 5.4 排查纪律（写进本仓，替换掉"自己 curl 掏 HTTP 体"）

1. 先看**稳定 code**（`QUOTA` / `MISSING_CREDENTIAL` / `RATE_LIMIT` / `UNKNOWN_MODEL`）——
   它们是官方给的诊断通道。
2. 只有拿不到 code 时，才退到掏 HTTP 体（官方明说**不跨提供方暴露 HTTP 状态**）。
3. `llm/retry` 事件里有**每一次可见尝试** —— "断断续续"先数重试次数，再怀疑路由。

### 5.5 与「本地 27B」那件事的关系（不重复取证）

`memory/在办清单.md §一百零二·一` 已有取证（**三处对不上，一处硬门槛**）：
本机 **RAM 7.39 GB · GPU RX 6500M 4 GB · 无 CUDA**，27B 即使 4-bit 也要 ~14 GB ⇒
**是容量问题，不是配置问题**。
上面 5.3 是"**真拿到 GPU 机器之后**"的官方接线清单 —— 在那之前不必装 `dsh-llm-qwen-local`。

---

## 六、待主人

1. **要不要按 5.1 加那条模型条目**（立刻能看图，无需重启）；
2. 要不要按 5.2 把可调路由迁进 settings（换来"改路由不用重启"）；
3. `FREELLMAPI_API_KEY` 补不补（§2.5 说无密钥本地服务**必须**有占位凭据）；
4. §2.7 那条"5 次重试会不会就是我们感觉到的断断续续"——要不要我去数一遍 `llm/retry` 事件。

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
