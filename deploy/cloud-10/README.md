# 10 云插件拼接网 · GBT小土豆V8

> 开发者：自由的风 · 守护者：公主土豆 · 本署名不可删除、不可篡改归属

主人 2026-09-25 令：**不部署在本地，直接部署在云插件上，以模块化部署，再进行 10 插件拼接运行。**
这一目录就是把这句话落成可核对件的地方。

---

## 一、10 位是谁（每位绑其余 9 位）

| 号 | 模块 id | 主人给的名字 | 职责 | 云侧落点 |
|---|---|---|---|---|
| 01 | `gbt-c01-llm-gateway` | dsh-llm-qwen-local | 模型接入与推理路由 | Workers AI / 自建端点 |
| 02 | `gbt-c02-context-compact` | dsh-force-compact | 上下文压缩与预算 | KV / 内存 |
| 03 | `gbt-c03-uncensored-lane` | dsh-llm-qwen-abliterated | 无审查通道（自托管权重） | 容器 / 自建端点 |
| 04 | `gbt-c04-tool-web` | dsh-tool-web | 联网检索与抓取 | ai-search / fetch |
| 05 | `gbt-c05-tool-file` | dsh-tool-file | 文件读写（对象存储） | R2（`mesh10/` 前缀） |
| 06 | `gbt-c06-tool-shell` | dsh-tool-shell | 命令执行（隔离容器） | Containers |
| 07 | `gbt-c07-memory-vector` | dsh-memory-vector | 向量记忆与检索 | Vectorize / 内存降级 |
| 08 | `gbt-c08-memory-local` | dsh-memory-local | 键值持久化 | KV（`mesh10/` 前缀） |
| 09 | `gbt-c09-policy-guard` | dsh-policy-guard | 权限与安全策略门 | 自带（15 条作用域） |
| 10 | `gbt-c10-observability` | dsh-observability | 可观测与审计落账 | Logs / R2 追加账 |

主人给的那 10 个 npm 名 **现读 2 存在（`dsh-llm-qwen-local` / `dsh-observability`）、8 返回 HTTP 404**
（`dsh-force-compact` · `dsh-llm-qwen-abliterated` · `dsh-tool-web` · `dsh-tool-file` · `dsh-tool-shell` ·
`dsh-memory-vector` · `dsh-memory-local` · `dsh-policy-guard`）。
所以这一套是**按那 10 条职责自建的云侧模块**，不冒充那 8 个不存在的包。

---

## 二、两种形态（只有第一种叫"共享 CPU"）

| | 形态 A（本目录默认） | 形态 B（`modules/` 下生成） |
|---|---|---|
| 怎么装 | 10 个模块编进**同一个 Worker** | 10 个独立 Worker，每位 9 条服务绑定 |
| isolate | 同一个 ⇒ **CPU/内存真共用** | 各一个 ⇒ 各算各的 |
| 互通 | 进程内直调 | Cloudflare 原生服务绑定 |
| 边数 | 90 条（10×9） | 90 条（同表生成） |

> **插件是接线，不是算力。** 90 条边是接线读数：它不增加一个核、不增加一字节显存。
> 主人要的"全部云插件共享 CPU"只有形态 A 成立；形态 B 是真互通，但 CPU 不共享 —— 不许念成共享。

---

## 三、件与真源

```
deploy/cloud-10/
  mesh.json              ← 单一真源：10 模块 · 每位每个 op 过哪道门 · 形态口径
  wrangler.toml          ← 形态 A 部署配置（用主人账号里**已有**的 KV/R2，不新建资源）
  src/modules.js         ← 10 位模块本体（手写）
  src/worker.js          ← 路由 / 门 / 边读数 / 全互通实跑（手写）
  src/mesh.generated.js  ← 生成物：运行时读的接线表
  modules/<id>/          ← 生成物：形态 B 的单模块 Worker + 9 条服务绑定
  tools/run-mesh-local.mjs ← 本机形状验收（70 项判据，不是本机部署）
  tools/check-endpoint-gate.mjs ← 本机**端点闸行为**验收（57 项，含 12 条负控，离线 0.3 s）
```

**部署前必跑的一道闸**（离线 · 不联网 · 不改远端）：`tools/codex-scripts/cloud-config-wiring.py`
把「这份 `wrangler.toml` 声明的名字」与「代码真正读的 `env.*`」**逐名对账** ——
`deploy/` 是生产落点，配置与代码对不上的代价不是报错，是**部署后静默 `undefined`**。

```powershell
python tools/codex-scripts/cloud-config-wiring.py        # A 读未声明 · B 声明未读 · C 形态B · D 容器面
```

它首跑就抓到两个真缺口：`SANDBOX`（06 号命令面的容器绑定）与 `AE`（10 号观测面的 Analytics Engine 绑定）——
**代码在读，而配置里连名字都没出现过** ⇒ 后来人要接这个能力，查不到绑定该叫什么名。

改接线只改 `mesh.json`，然后：

```powershell
python tools/codex-scripts/cloud-mesh.py gen     # 生成件
python tools/codex-scripts/cloud-mesh.py check    # 对账：表改了件没改 ⇒ 点名
python tools/codex-scripts/cloud-mesh.py edges    # 90 条边现算读数
python tools/codex-scripts/cloud-mesh.py selftest # 54 项控制（含负控）
python tools/codex-scripts/cloud-mesh.py readiness# 云侧只读现读：身份/资源/占位符
node deploy/cloud-10/tools/run-mesh-local.mjs     # 本机形状验收 70 项
node deploy/cloud-10/tools/check-endpoint-gate.mjs # 本机端点闸行为 57 项（离线 · 不出一字节网）

# 上面这条为什么单独有：worker.js 里 2026-09-25 那 4 批改动（令牌闸 / `/v1/models`
# 作用面读数 / `normalizeMessages` 拍平块数组 / 错误分档）当时还没部署，云端一次都没跑过，
# 所以先在本机把**代码行为**验掉。这条闸现在仍然留着当**回归门**（改了 worker.js 就跑它）。
#
# ✅ 2026-09-25 22:00 现读更正（第 37 轮）：**云端早就部署了**，而且令牌闸是开着的 ——
#    `GET /v1/models` 自报 auth_scope={chat:bearer, models:public, tokens_configured:1,
#    compare:sha256+timingSafeEqual}（这些字段正是那 4 批加的）；不带 Authorization 打
#    `/v1/chat/completions` 现读 401。`cloud-mesh.py live --url <真地址>` 真跑 **17/17 全过**。
#    证据留档 output/cloud-live/2026-09-25-live-17of17.json。**下面那句"未部署"已作废。**
# 口径（仍然成立）：本机验的是**代码行为**，与云端真读数是两件事，两个都要有。

# 真跑验收（对一个**已经跑起来**的实例量 16 条判据；不部署、不改远端）
wrangler dev -c deploy/cloud-10/wrangler.toml --port 8787 --local   # 本机 workerd 冒烟
python tools/codex-scripts/cloud-mesh.py live --url http://127.0.0.1:8787
# deploy 之后把 --url 换成真地址，跑的**是同一套判据**

# 连模型面一起量（01/03 真打端点，+4 条判据 ⇒ 共 20 条）
python tools/codex-scripts/mock-vllm-endpoint.py serve --port 8111 --model-id gbt-potato-v8
wrangler dev -c deploy/cloud-10/wrangler.toml --port 8790 --local `
  --var LLM_ENDPOINT:http://127.0.0.1:8111/v1 `
  --var UNCENSORED_ENDPOINT:http://127.0.0.1:8111/v1 `
  --var OWNER_TOKEN:<本机冒烟用的一次性口令>
# ⚠️ 01/03 两条 op 挂的是 external_llm 这道门：**先请主人在终端放行**，再量
python tools/codex-scripts/cloud-mesh.py live --url http://127.0.0.1:8790 --expect-llm
```

---

## 三之三、模型面：01/03 是**真调用**，不是占位（2026-09-25 已跑通）

| 项 | 读数（真 workerd + 真 HTTP 端点） |
|---|---|
| 01 号打到 `<base>/chat/completions` | `http=200` · `model=gbt-potato-v8` · **7 ms** · 回包 **81 字**进了读数 |
| 权重口径 | 自托管端点 ⇒ `weights_ours=true`；Workers AI ⇒ `weights_ours=false`（**不许混着念**） |
| 密钥 | 只进 `Authorization` 头；读数里**逐字搜不到**（有负控） |
| 端点地址口径 | 回环地址照原样报；**非回环只报前几位**（`https://gpu.***:8443`，有负控） |
| AI 绑定在但没配模型 id | **拒**并说明「不替主人挑模型」（有负控） |
| 端点 500 / 回包不是 JSON / 超时 | 三种**分开报**（`http` + `error`），不合并成一句「失败」 |
| 01/03 两条 op | 挂 `external_llm` 门 ⇒ 云上没授权时读数明写「**被门挡住：缺 …**」（仍算红，不念成通过） |

> **这一段的边界**：本机跑的是**假端点**（`mock-vllm-endpoint.py`）。
> 它证明的是**管道**（URL 口径 · 请求头 · 载荷 · 回包解析 · 失败分型），
> **不是**「模型真的能答」。真答案要等我们自己的权重与算力到位（§五 的 03 号）。

---

## 三之四、身份红线（主人三条红线之一：身份不变）

**机制**（不是口号）：调用方**没带** system 提示词时，01 号注入本机身份；
**带了就一律尊重、绝不覆盖**（这一条有负控钉着）。文案改一处就换：`env.GBT_IDENTITY`。

| 判据 | 读数 |
|---|---|
| 身份文案可读 | `GET /rpc/gbt-c01-llm-gateway/identity` ⇒ 文案 + 来源（默认 / `env.GBT_IDENTITY`） |
| 没带 system ⇒ 注入 | `identity_injected: true`，且 `messages[0].role === "system"` |
| 注入不顶掉用户的话 | `messages` 变成 `[system, user]`，用户原文仍在 |
| 调用方自带 system ⇒ 不覆盖 | `identity_injected: false`，首条仍是调用方那句 |
| 换文案只改一处 | `GBT_IDENTITY` 一改即生效 |

---

## 三之五、07 号向量记忆：D1 落点**真写了**，并且**活得过重启**

之前 07 号宣称「Vectorize 没授权 ⇒ 落 isolate/D1」，**但代码里只有内存那条**。现在 D1 真落了。

```powershell
# 本地验收专用配置（带一个"假 id"的 D1；拿它 deploy 会失败 —— 这正是保险）
wrangler dev -c deploy/cloud-10/wrangler.dev.toml --port 8791 --local
python tools/codex-scripts/cloud-mesh.py live --url http://127.0.0.1:8791 --expect-d1   # 19/19
```

**持久性量不了一次调用**（要重启），两步做法：

| 步 | 命令 | 读数 |
|---|---|---|
| 1 | 写入并当场查 | `sink=d1` · 命中首位就是刚写那条 · `count=N` |
| 2 | **杀掉 dev 再起一次**，再查 | `sink=d1` · `count=N` 仍在 ⇒ **活过重启** |
| 负控 | 用**不带 D1** 的 `wrangler.toml` 起，同法两步 | 重启后命中 **0 条** ⇒ 内存落点确实活不过重启 |

第三条（负控）才是这条判据有分辨力的证据：**同样两步，一个活一个死**。

> ⚠️ **D1 全表扫**：检索在模块内算内积，O(n)。表大了要换 Vectorize。
> ⚠️ **不许碰主人的库**：主人账号现读那 4 个 D1 都是别的用途（orders / caps / wallet），
> 所以 `wrangler.toml` 里 D1 **故意留空**；`cloud-mesh.py check` 有一条护栏盯着
> 「部署配置里不许出现 D1 绑定」。要真上云，得主人点头新建一个。

---

## 三之二、装前实测（2026-09-25 已跑）

| 检查 | 读数 |
|---|---|
| `wrangler deploy --dry-run` | 打包成功 **38.07 KiB / gzip 9.67 KiB** · 6 个绑定全部解析（KV×2 · R2×2 · AI · 三个变量） |
| `wrangler dev --local` + `cloud-mesh.py live` | **16/16**（本机 workerd 真跑，非 Node 模拟） |

🔴 **真跑抓到一条本机验收抓不到的真 bug**：Worker 的默认导出**每次请求都会重新执行** ——
原来「每次请求 new 一个 mesh」会让计数的边、发的授权、落账**出了这次请求就全没了**
（`edges_after` 读数 `0/90`，Node 侧因为一直复用同一个 mesh 所以是绿的）。
修法：账提到**模块级**（同一 isolate 内跨请求活着）。

**边界（不许念过头）**：isolate 是**尽力而为**的 —— 会被回收、会同时存在多个副本。
⇒ 计数与日志当"热读数"可以；**要算数的授权必须落 KV/DO/secret**，
否则 A 副本发的授权 B 副本看不见。

---

## 四、门在这里怎么站

- 每个 op 该过哪条作用域写在 `mesh.json` 的 `op_gates` 里（**单一真源**，代码里不藏第二套 if）。
- 门名只有 `none` 或 15 条作用域之一，别的值一律判红。
- 发授权只有一条路：`POST /admin/grant` + 主人令牌；**没有主人令牌的实例根本没有这个口子**。
- 门是分层的：门先挡（403 + `missing_scopes`），门开了模块才说话 —— 两层分开量。
  例：`exec` 过了 `process_execute` 这道门，若容器没绑，模块仍如实回 `unsupported_in_worker`（**授权 ≠ 凭空有能力**）。
- 读写作用域分开：拿到 `filesystem_write` 不等于能 `list`（那是 `filesystem_read`）。

---

## 五、落地状态（2026-09-25 现读）

- wrangler **4.111.0 已装**；OAuth **已登录**（账号 `82dd****` · 作用域 28 条）。
- 账号里**已有**资源：KV 4 个（BRAIN_KV / gbt-canary-kv / gbt-monitor-kv / VBOX_STATE）·
  R2 1 个（gbt-bigfiles）· D1 4 个（gbt-orders-a/b · gbt-caps · gbt-wallet）。
- `wrangler.toml` 生效占位符 **0 个** ⇒ **现在可部署**。
- 未做：真 `wrangler deploy`（这一步会在主人账号里建 Worker，是真改远端，要主人点头）。
- 部署后仍要另量的真读数：身份漂移 · 拒答率 · 遥测 · 装机验收 —— 本机形状验收不顶替。

### 部署后会如实报的 5 处已知缺口（不假装有）

1. **01 号**：Workers AI 的权重不是我们的，平台侧内容策略仍在 ⇒ 能干活，但不是"无限制"。
2. **03 号**：没有自托管权重端点 ⇒ 读数=未读到；托管模型不许冒充无审查。
3. **06 号**：容器没建 ⇒ `exec` 如实拒。
4. **07 号**：令牌作用域表里没有 `vectorize:write` ⇒ 落 isolate 内存，`sink` 如实报。
5. **10 号**：没有 `analytics_engine:write` ⇒ 落 R2/KV 追加账，`sink` 如实报。

### 不碰主人原有数据

本网所有 KV 键与 R2 对象都走 `mesh10/` 前缀（`src/modules.js` 的 `NS_PREFIX`），
读数里 `logical_key`（人写的）与 `stored_key`（真落点）分开报。
本机验收里专门有两条负控：**主人的原有键/对象逐字节没动** · **列自己的列不出主人的**。

---

## 五之二、🔴 已部署 · 闭环已跑通（2026-09-25 主人令「部署好并跑通闭环」）

| 项 | 读数 |
|---|---|
| 地址 | **https://gbt-potato-cloud-10.lopaycn.workers.dev** |
| 版本 | 第 3 次部署 · 50.00 KiB / gzip 13.36 KiB · 绑定 9 个（KV×2 · R2×2 · AI · 变量×4） |
| 真云验收 | **30/30**（基础 16 + 模型面 6 + 存储面 8） |
| 闭环（模型） | `ok=true` · `via=workers-ai` · `model=@cf/openai/gpt-oss-120b` · **2416 ms** · `identity_injected=true` |
| 模型原话 | 「我是一款由自由的风开发的中文对话AI——**GBT小土豆V8**……」 |
| 授权 | 只发 4 条（`external_llm` · `filesystem_read` · `filesystem_write` · `network_read`），写在 `wrangler.toml` 的 `GRANTED_SCOPES` ⇒ **删一行即撤**；`owner_control` 等**故意不发**，门对 `process_execute` 仍 403 |

**复制即用**（`--expect-llm --expect-storage` 会真调模型、真读写存储）：

```powershell
python tools/codex-scripts/cloud-mesh.py live --url https://gbt-potato-cloud-10.lopaycn.workers.dev --expect-llm --expect-storage
```

```powershell
curl.exe -H "User-Agent: gbt-mesh-acceptance/1.0" -H "content-type: application/json" -d "{\"prompt\":\"用一句话说你是谁\"}" https://gbt-potato-cloud-10.lopaycn.workers.dev/rpc/gbt-c01-llm-gateway/complete
```

> ⚠️ **别用默认的 `Python-urllib` UA 去调**：平台侧会 403（实测），看着像部署失败，其实 Worker 好好的。
> 验收工具已改成**如实自报**的 UA（不是伪装浏览器）。

### 真云上现形的三条「本机量不出」（都已处理并写进读数）

1. **平台挡默认 UA** ⇒ 16 条判据全红假象；
2. **多副本**：跨请求的计数不保证（`full-ping` 与随后的 `/edges` 可能落在不同 isolate）⇒
   判据改成**同一次请求内取证**；**要算数的东西必须落 KV/DO**（授权持久化就是为这个）；
3. **回包形状不能硬猜**：`choices[0].message.content` vs `response` vs `result` ——
   现在逐个试并**自报匹配到哪条**（`content_path`），一条都不中就带回**回包的键名**。

---

## 六、本机形状验收量了什么（64/64 通过）

① 十位全在（10/10）· ② 声明 90 条边 / 每位绑 9 位 / 无自环 / 双向对称 / 实跑 90 发全中 ·
③ 门：授权前 403、授权后 200、宽度不外溢、读写作用域分开、令牌不对拒、野作用域拒、
门开了没接线仍拒 · ④ 没接线就报"未读到" · ⑤ 九位模块各自真跑一遍（扇出/压缩/向量召回/
读写 KV/落账/门表 15 条）· ⑥ 形态 B 单模块件能加载、未挂绑定如实报 0 ·
⑦ 模型面（真打端点 / 密钥只进头 / 上传形状 / 失败分型）· ⑧ 身份红线（注入 + 不覆盖）·
控制面与数据面分前缀。

> 本机跑 ≠ 云端跑。这里量的是**形状**（在不在、通不通、门开不开）；
> 真云读数见 §五之二（**已部署 · 30/30**）。
