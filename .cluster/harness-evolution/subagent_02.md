# GLM-4.7-Flash 接入实战调研

> 调研时间：2026-09-12 · 调研员：subagent_02（GLM API 实战调研）
> 所有数字均标注来源编号 [S1]-[S22]，对应文末来源清单。查不到的一律注明"未查到"。

---

## 一、API 参数全表（含 thinking/tools/stream 细节）

### 1.1 基础调用格式

- **Endpoint**：`POST https://open.bigmodel.cn/api/paas/v4/chat/completions`，Header `Authorization: Bearer <key>`（官方 GLM-4.7-Flash 页 cURL 示例）[S1]
- **OpenAI SDK base_url**：`https://open.bigmodel.cn/api/paas/v4/`（官方 OpenAI 兼容文档，注意结尾带斜杠的写法在所有示例中出现最多）[S6]
- 官方明确"后端兼容了 OpenAI 的所有 Endpoint，仅需更换 api_key 与 base_url" [S7]；但不支持 OpenAI 新版 `/responses` 端点（社区需求帖仍开放，未实现）[S17]
- 也可用官方 `zai-sdk`（`pip install zai-sdk`，示例版本 0.2.3+）[S1]

### 1.2 请求参数表（chat/completions）

| 参数 | 类型 | 默认值 | 说明（GLM-4.7-Flash 语境） | 来源 |
|---|---|---|---|---|
| `model` | string | 必填 | `glm-4.7-flash` | [S1] |
| `messages` | array | 必填 | OpenAI 格式 role/content | [S6] |
| `thinking` | object | `{"type":"enabled"}` | **GLM-4.7 系列默认开启 Thinking 且为"强制思考"**（不同于 GLM-4.6/4.5 的"模型自动判断"）；`disabled` 可关闭 | [S4][S5] |
| `reasoning_effort` | string | — | **仅 GLM-5.2 及以上支持**，GLM-4.7-Flash 不支持（传了无效/报错，官方未写明 Flash 行为，保守不传） | [S5] |
| `temperature` | float | OpenAI 兼容文档标 0.6；官方 Flash 示例用 1.0 | 区间 **(0,1) 开区间**，`temperature=0` / `do_sample=false` 在 OpenAI 调用中**不适用**（官方明确注意事项） | [S1][S6] |
| `top_p` | float | 0.95 | 推荐与 temperature 二选一；官方推荐值 0.8-0.95 | [S6][S8] |
| `max_tokens` | int | 默认 65536（glm-4.7 行） | 模型页标"最大输出 Tokens 128K"；官方"核心参数"页表格只单列了 `glm-4.7`（默认 65536 / 最大 131072），**未单列 glm-4.7-flash 行**（未查到 Flash 独立上限，按模型页 128K + 官方示例 65536 理解）；官方建议 ≥1024 | [S1][S8] |
| `stream` | bool | false | SSE 流式 | [S1][S8] |
| `tools` | array | — | OpenAI 格式 `[{"type":"function","function":{name,description,parameters}}]`，与 GLM-4.6 无格式差异 | [S6][S9] |
| `tool_choice` / `stop` / `do_sample` | — | — | do_sample 为智谱特有参数（OpenAI SDK 中需 extra_body 传） | [S8] |
| `thinking.clear_thinking` | bool | 标准 API 默认 true | 保留式思考开关：`false` = 保留历史轮 reasoning_content（Coding/Agent 场景推荐），标准 API 端点默认关闭 | [S9] |

### 1.3 thinking 参数行为细节（重点）

- `thinking.type`：`enabled`（默认，4.7 系强制思考）/ `disabled`（关闭思考）。**GLM-5.3 / GLM-5.3-Flash 传 `disabled` 会直接报错**（强制思考不可关），GLM-4.7 系可以关 [S5]
- GLM-4.7 新引入**轮级思考（Turn-level Thinking）**：同一会话内每轮请求可独立开/关思考，适合"轻量轮关思考快速响应 + 重任务轮开思考"的动态策略 [S9]
- **交错式思考（Interleaved Thinking）**：GLM-4.5 起默认支持，工具调用之间/收到工具结果后继续思考。**官方强制要求：使用"交错思考+工具"时必须显式保留 reasoning content，并在返回工具结果时一并传回** [S9]
- 这就是与 GLM-4.6 在工具调用上的核心差异：格式相同（都是 OpenAI tools 数组），但 4.7 系默认"每次响应和工具调用之前都先想一想"，且多了保留式思考（Preserved Thinking）与轮级思考 [S9][S10]

### 1.4 流式 SSE 与 reasoning_content

- 流式响应中思维链走 **`delta.reasoning_content`** 字段，正文走 `delta.content`（官方 zai-sdk 与 OpenAI SDK 示例均如此）[S1][S6]
- 官方 OpenAI SDK 示例处理方式：

```python
for chunk in response:
    if chunk.choices[0].delta.reasoning_content:   # 思维链
        print(chunk.choices[0].delta.reasoning_content, end='')
    if chunk.choices[0].delta.content:             # 正文
        print(chunk.choices[0].delta.content, end='')
```
（官方文档原文；官方交错思考示例中更稳妥的写法是 `if hasattr(delta, "reasoning_content") and delta.reasoning_content`）[S6][S9]

- 流式推理中途异常**不返回错误码**，而是通过 `finish_reason` 返回异常原因（官方错误码文档注意事项）[S12]

### 1.5 错误码速查（HTTP 状态码 + 业务码）

| 业务码 | HTTP | 含义 | 来源 |
|---|---|---|---|
| 1302 | 429 | 账户达到速率限制（并发超限） | [S3][S12] |
| 1305 | 429 | 平台服务过载（模型总访问量过大） | [S3][S12] |
| 1113 | 429 | 账户欠费 | [S12] |
| 1308/1310/1316/1317 | 429 | 达到时长窗口使用上限（含重置时间 next_flush_time） | [S12] |
| 1261 | 400 | Prompt 超长 | [S12] |
| 1301 | 400 | 内容安全拦截 | [S12] |
| 1210/1211/1214 | 400 | 参数错误/模型不存在/字段非法 | [S12] |

---

## 二、免费额度与限速（实锤数字）

### 2.1 免费性质

- **永久免费**：智谱 2026-01-20 宣布 GLM-4.7-Flash 永久免费开放（30B 总参/3B 激活 MoE）[S14][S15]；官方定价页输入/输出单价均为"免费" [S2]
- **无每日 token 上限的公开数字**：官方未公布 Flash 免费档的每日/每月 token 配额（未查到）。社区判断它是长期免费档而非限时活动 [S16]

### 2.2 并发限制（实锤）

- **官方免费档限 1 并发**（同一时刻仅 1 个在途请求）：多个独立来源一致 [S10 知乎评测][S16 ofox 实测][S13 cnblogs]
- 平台速率限制机制是"按用户权益等级 + 模型维度"的**并发数限制**，官方未公布 RPM/TPM 数字（未查到公开的 RPM/TPM 表）[S3]
- 历史参照：GLM-4-Flash 时代新用户免费 2 并发（2024 年 CSDN 记录）[S18]，4.7-Flash 收紧为 1
- 并发提升路径：消费现金余额攒积分 → 权益等级 V0(<2000)/V1(2000-10000)/V2(10000-50000)/V3(≥50000)，等级越高并发越高；或控制台提交"速率限制调整申请"（10 个工作日审核）[S3][S19]

### 2.3 实测吞吐（社区单线程实测，2026-05）

来自 ofox.ai 博客的 1 小时连续单线程实测（输入约 800 token / 输出约 1500 token/次）[S16]：

| 指标 | 实测值 |
|---|---|
| 平均首 token 延迟 | 0.8 秒 |
| 平均输出速率 | 65 tokens/秒 |
| 1 小时连续请求 | 约 120 次 / 18 万 token 输出 |
| 遇到 429 | 没有（单线程下） |
| 平均请求间隔 | 约 30 秒（受并发=1 + 生成速度约束） |

### 2.4 实名要求

- **调用 API 不强制实名**，官方建议实名（官方 FAQ 原文："目前调用 API 并不强制要求实名认证，但我们建议您进行实名认证"）[S20]
- 社区帖（台湾用户，针对新人资源包）：未实名可得 400 万 tokens 新人额度，实名+邀请好友可达 2000 万（针对付费模型的资源包，非 Flash 免费档）[S21]

### 2.5 429 抱怨主要集中在哪

- V2EX 多个帖子反映的 429/限流问题集中在 **GLM Coding Plan 套餐**（1302 并发超限、1305 过载、1313 公平使用策略限制），而非免费 Flash 档 [S22]
- 对 GBT 的含义：**免费档真正的约束是"同时只能有 1 个在途请求"**——GBT 大脑层必须把多通道回退做成串行队列或换模型，不能对 glm-4.7-flash 并发打两个请求

---

## 三、模型三档推荐（主力/备胎/重型）

### 3.1 2026 年 9 月智谱在售模型价格速览（元/百万 tokens，官方定价页）[S2]

| 模型 | 上下文 | 输入价 | 输出价 | 备注 |
|---|---|---|---|---|
| GLM-5.3（旗舰） | 1M | 8 | 28 | 缓存命中 2 |
| **GLM-5.3-Flash** | 1M | 0.8 | 2.8 | **原生多模态**（图片/视频/文件/文本），缓存命中 0.23 |
| GLM-4.7 | 200K | 2-4（分段） | 8-16（分段） | 限时免费缓存存储 |
| GLM-4.7-FlashX | 200K | 0.5 | 3 | 轻量高速 |
| **GLM-4.7-Flash** | 200K | **免费** | **免费** | 1 并发 |
| GLM-4.5-Air | 128K | 0.8 | 2-6 | |
| GLM-4.5-Flash | 128K | 免费 | 免费 | 上一代免费档 |
| GLM-4.6V（视觉） | 128K | 1（≤32K） | 3 | |
| GLM-4.6V-FlashX（视觉） | 128K | 0.15 | 1.5 | |
| **GLM-4.6V-Flash（视觉）** | 128K | **免费** | **免费** | 9B 轻量视觉推理 |

### 3.2 GLM-5.3-Flash"夜间畅用"活动细节（官方公告）[S11]

- **时间**：2026-09-03 至 2026-09-20，每晚 23:00 至次日 09:00（北京时间，含周末节假日）
- **ZCode 中调用 GLM-5.3-Flash：额度消耗为 0（真免费畅用）**
- 其他套餐支持的 Agent（含 OpenClaw）：可用额度 ×2
- 仅 GLM-5.3-Flash 享受；选 GLM-5.3 按标准规则扣
- 仅付费套餐用户；需 ZCode 3.10+ 版本
- 另有 7 天体验卡：从未订阅过的用户可免费领 [S23]

### 3.3 Coding Plan 套餐（积分制，2026-07-30 改版后）[S11]

| 套餐 | 5 小时积分 | 每周积分 | 价格 |
|---|---|---|---|
| Lite | 2,000 | 10,000 | 官网 zcode.z.ai 显示 ¥94.4/月（划线价 ¥118）[S24]；知乎 2026-08 帖记录 ¥118/月 [S25]（两来源略有出入，以官网实时价为准） |
| Pro | 12,000 | 60,000 | ¥538/月（知乎 8 月帖）[S25]；改版前 V2 价 ¥149 [S26] |
| Max | 28,000 | 140,000 | ¥1078/月（知乎 8 月帖）[S25]；改版前 V2 价 ¥469 [S26] |

- 积分公式：`消耗 = (输入Token×Input系数 + 缓存命中×Cached系数 + 输出Token×Output系数)/10000`；GLM-5.3 系数 6.9/1.7/24，GLM-5.3-Flash 系数 2.3/0.56/8（即 **Flash 抵扣是 5.3 的 1/3**）
- 非高峰时段（工作日 14:00-18:00 之外，含周末全天）按 50% 积分消耗
- 套餐内 GLM-5.3-Flash 可用量约为 GLM-5.3 的 3 倍；95% 缓存命中下 Lite 档 Flash 约 1.46-2.92 亿 tokens/周
- 限 Claude Code、Kilo Code、OpenClaw、OpenCode、TRAE、CodeBuddy 等指定工具；**在规定工具外调 API 不享用套餐额度**；OpenClaw 为次级调度（高负载下动态排队/限流）
- 调用 GLM-5.2/5.1 自动切换至 GLM-5.3；调用 GLM-5-Turbo/GLM-4.7 自动切换至 GLM-5.3-Flash

### 3.4 三档推荐（GBT 大脑层视角）

| 档位 | 推荐 | 理由 |
|---|---|---|
| **主力（免费日常）** | `glm-4.7-flash` | 0 成本、200K 上下文、128K 输出、SWE-bench 59.2%（30B 级开源 SOTA）、思考模式可开关。约束：1 并发 |
| **备胎（免费回退 + 低成本提速）** | 回退链 `glm-4.5-flash`（免费、128K/96K）→ `glm-4.7-flashx`（0.5/3 元，需要并发和速度时）| 4.5-Flash 是上一代免费档，可作 Flash 429 时的同 key 回退；FlashX 付费但便宜，200K 上下文 |
| **重型（复杂任务/多模态）** | `glm-5.3-flash`（0.8/2.8 元，1M 上下文，原生多模态，AA 指数 57 与 Claude Opus 4.8 持平）| 前沿智能第一次"不用省着用"（官方口径，价格为 5.3 的 1/10、限时折扣 1/20）[S27]；若追求极限可用 `glm-5.3`（8/28 元）。重度编码用户直接上 Coding Plan（非高峰 5 折 + 夜间活动）更划算 |

> 建议 GBT 通道顺序调整为：`glm-4.7-flash`（主力，串行队列）→ `glm-4.5-flash`（免费备胎）→ `glm-4.7-flashx` 或 `glm-5.3-flash`（低成本付费兜底）→ deepseek（外部兜底）。

---

## 四、OpenAI SDK 兼容坑清单（含代码示例）

本机已装 openai Python SDK（≥1.0.0 即可，官方要求 3.7.1+ / SDK≥1.0）[S6]。

### 坑 1：base_url 尾斜杠与地址

官方文档两种写法都出现过（`.../v4/` 与 `.../v4`），绝大多数示例带尾斜杠，**建议统一带 `/`**：

```python
from openai import OpenAI
client = OpenAI(
    api_key="你的智谱KEY",
    base_url="https://open.bigmodel.cn/api/paas/v4/",
)
```
来源：[S6]（官方 OpenAI 兼容文档全部示例）；国内网络无需代理直连 [S16]

### 坑 2：thinking 必须走 extra_body

OpenAI SDK 的 `create()` 没有 `thinking` 参数，必须：

```python
resp = client.chat.completions.create(
    model="glm-4.7-flash",
    messages=[{"role": "user", "content": "..."}],
    stream=True,
    extra_body={"thinking": {"type": "enabled"}},   # 关闭则 "disabled"
)
```
来源：[S6] 官方示例原样。GLM-4.7 默认就开思考，想省 token 提速才需要显式传 disabled。

### 坑 3：temperature=0 不可用

官方明确：`temperature` 区间为 (0,1) 开区间，`do_sample=False`（即 temperature=0）在 OpenAI 调用中不适用。**GBT 里若从别处迁移来的 `temperature=0` 硬编码会出错**，改成如 0.6，或单独用 top_p。来源：[S6][S8]

### 坑 4：流式 reasoning_content 字段访问

`delta.reasoning_content` 不是 OpenAI 标准字段。官方示例直接属性访问（新版 openai SDK 的 pydantic model_extra 允许），官方交错思考示例用 `hasattr(delta, "reasoning_content")` 防御：

```python
for chunk in stream:
    delta = chunk.choices[0].delta
    if hasattr(delta, "reasoning_content") and delta.reasoning_content:
        reasoning += delta.reasoning_content   # 思维链
    if hasattr(delta, "content") and delta.content:
        content += delta.content               # 正文
```
来源：[S6][S9] 官方示例。**注意：使用交错思考+工具调用时，必须把累积的 reasoning_content 原样随工具结果传回**，否则效果下降（且影响缓存命中）[S9]

### 坑 5：429 重试策略

- 智谱 429 有多个业务码：**1302=账户并发超限（降低并发/排队，稍后可重试）**、**1305=平台过载（增加重试间隔，避免立即高频重试）**、1113=欠费（重试无用，去充值）[S3][S12]
- **未查到智谱官方文档承诺返回 `Retry-After` 响应头**（未查到）。社区实践：hermes-agent 的 GitHub issue 明确记录 GLM-5.x 的 1305"不要盲目重试"，且存在"identical prompt 触发 429/1305"的 prompt 敏感现象 [S28]
- 官方建议：请求队列/并发池、避免固定间隔高频重试、Batch API 半价分流 [S3]
- OpenAI SDK 自带 `max_retries`（默认 2，会对 429/5xx 指数退避）；官方智谱配置类示例 `timeout=30, max_retries=3` [S6]。**对 1 并发的 Flash 档：把 GBT 的并发信号量设为 1 + SDK max_retries=3 + 自定义 1305 指数退避（首次 2s 起）**
- V2EX 实锤错误文案："429 您当前使用该 API 的并发数过高，请降低并发" [S22]

### 坑 6：超时建议

- 官方配置示例 timeout=30s [S6]；但 Flash 开思考时长输出（max_tokens 65536 + 思维链）单次可能跑几分钟，**GBT 长任务建议 timeout ≥ 120s，短问答 30s**
- 首帧延迟参考：免费档实测首 token 0.8s [S16]；官方发布记录称流式首帧响应低于 400ms（宣传口径）[S29]

### 坑 7：其他小坑

- 模型名必须全小写 `glm-4.7-flash`，写错报 1211 模型不存在 [S12]
- `do_sample`、`thinking`、`clear_thinking` 等智谱特有参数都要走 `extra_body`
- prompt 超长报 1261（400），Flash 上下文 200K，注意历史消息裁剪 [S12]
- 内容安全 1301：中文敏感内容可能触发，GBT 生成设计文案时留意 [S12]

---

## 五、编程能力实测数据

### 5.1 GLM-4.7-Flash 官方基准（HuggingFace 模型卡，30B-A3B MoE）[S30][S31]

| 基准 | GLM-4.7-Flash | 参照 |
|---|---|---|
| AIME 25 | **91.6** | 同尺寸最强之一 |
| SWE-bench Verified | **59.2** | 30B 级开源 SOTA；对比上代 GLM-4.6-Flash 系 22.0（模型卡对照列） |
| τ²-Bench（工具调用） | **79.5** | 对照 49.0；Artificial Analysis 实测其 τ²-Bench Telecom ~99% 为全模型最高 [S32] |
| BrowseComp | 42.8 | 对照 2.29 |
| HLE | 14.4 | 对照 9.8 |

- 官方口径："在 SWE-bench Verified、τ²-Bench 等主流基准测试中，GLM-4.7-Flash 的综合表现在相同尺寸模型系列中取得开源 SOTA 分数"[S1]
- HumanEval / MBPP 分数：**未查到**官方或权威第三方数字（这两个老基准已基本被 LiveCodeBench/SWE-bench 取代，2026 年新模型普遍不再公布）

### 5.2 与同门/竞品对比

| 模型 | SWE-bench Verified | 来源 |
|---|---|---|
| GLM-4.6（上代旗舰） | 68.0（73.8 - 5.8 推算，官方称 4.7 提升 5.8%） | [S10] |
| GLM-4.7-Flash | 59.2 | [S30] |
| GLM-4.7（旗舰） | **73.8**（较 4.6 +5.8%，开源第一；LiveCodeBench V6 84.9、τ²-Bench 84.7 开源 SOTA、Terminal Bench 2.0 41%） | [S10] |
| Claude Sonnet 4.5 | 77.2 | [S33] |
| DeepSeek-V4-Flash | 79%（2026 年数据） | [S34] |
| GLM-5.3-Flash | DeepSWE 63.4（vs Opus 4.8 的 58.0、DeepSeek-V4-Vision-Exp 59.3） | [S35] |

**结论：GLM-4.7-Flash 的 SWE-bench 59.2 低于 GLM-4.6 旗舰（≈68）和 DeepSeek-V4-Flash（79）**，作为"全栈编程大脑"属于"免费档里最能打"（30B 级 SOTA），复杂工程任务仍需上 GLM-5.3-Flash / GLM-5.3。GLM-5.3-Flash 在 Z.ai Code Bench 体感与 Claude Opus 4.8 相当（官方口径）[S27]。

### 5.3 社区实测体验

- Hacker News 讨论：对 59.2% SWE-bench（30B MoE、<4B 激活）评价"pretty darn good"，认为同尺寸无对手 [S36]
- 知乎评测（API + 本地双体验）："30B 级别最强模型，API 免费"；API 版限制 1 并发；交织思考提升指令遵循 [S10]
- Reddit LocalLLaMA：**本地量化版**（GGUF 等）体验参差，多为量化/运行环境问题（有人"从未成功跑顺"），与官方 API 版表现不是一回事 [S37]
- 官方发布记录：轻量规模实现高效 Coding，首帧 <400ms [S29]
- GBT 无本地 GPU、全走云 API → 直接用官方 API 版即可，避开社区本地量化的坑

---

## 六、视觉通道配置建议

### 6.1 主模型换纯文本后，视觉（GBT 眼维）可选项（官方定价页/模型概览）[S2][S27]

| 模型 | 输入价（元/M） | 输出价（元/M） | 上下文/最大输出 | 视觉能力 | 价格 |
|---|---|---|---|---|---|
| **GLM-4.6V-Flash** | **免费** | **免费** | 128K / 32K | 9B 轻量视觉推理，Function Calling 原生融入 | 免费 |
| GLM-4.1V-Thinking-Flash | 免费 | 免费 | 64K / 16K | 视觉推理 | 免费 |
| GLM-4V-Flash | 免费 | 免费 | 16K / 1K | 基础图像理解 | 免费 |
| GLM-4.6V | 1（≤32K）/ 2（32K+） | 3 / 6 | 128K / 32K | 106B 高性能版，前端复刻更稳 | 付费 |
| GLM-4.6V-FlashX | 0.15 | 1.5 | 128K / 32K | 轻量高速 | 付费 |
| GLM-4.5V | 2 / 4 | 6 / 12 | 64K / 16K | 106B，42 榜单同规模 SOTA（旧一代） | 付费 |
| GLM-5V-Turbo | 5 / 7 | 22 / 26 | 200K / 128K | 多模态 Coding 基座 | 付费 |
| **GLM-5.3-Flash** | 0.8 | 2.8 | **1M / 128K** | **原生多模态**（图片/视频/文件），视觉融入 Coding 循环 | 付费 |

- GLM-4.6V 系列比 GLM-4.5V **降价 50%**（新浪财经报道确认）[S38]
- GLM-4.6V 系列 128K 训练上下文，同参数规模视觉理解 SOTA，**首次把 Function Calling 原生融入视觉模型**（"图像即参数，结果即上下文"），支持图片/视频/文件输入、物体检测计数、Image2Prompt、视频时间轴等 [S39]

### 6.2 推荐视觉通道配置（GBT 眼维）

```
主力（免费）：glm-4.6v-flash      — 0 成本、128K 上下文、32K 输出、原生工具调用
进阶（低成本）：glm-4.6v          — 1/3 元每百万，复杂图表/文档/前端复刻精度更高
重型（多模态+长上下文）：glm-5.3-flash — 0.8/2.8 元、1M 上下文、原生多模态，
                                          可直接把截图丢进 Coding 循环（看渲染结果改代码）
```

- **GBT 现有 glm-4.6v/4.5v 回退链建议改为：glm-4.6v-flash（免费主力）→ glm-4.6v（1/3 元备胎）→ glm-5.3-flash（重型）**
- 注意 V 系列参数差异：glm-4.6v / 4.6v-flash / 4.6v-flashx 的 max_tokens **默认 16384、最大 32768**（不是文本系的 65536/131072），GBT 请求模板要单独设 [S8]
- glm-4.5v 强制思考（thinking.type=enabled 时），glm-4.6v 为自动判断 [S5]
- 若 GBT 眼维只做轻量识图（截图→描述），免费三档里 4.6v-flash 明显强于 4.1V-Thinking-Flash（128K vs 64K）和 4V-Flash（16K/1K），选 4.6v-flash

---

## 七、来源清单

| # | 来源 | URL |
|---|---|---|
| S1 | 智谱官方文档 · GLM-4.7-Flash 模型页（含 cURL/SDK 示例、200K/128K、免费） | https://docs.bigmodel.cn/cn/guide/models/free/glm-4.7-flash |
| S2 | 智谱官方文档 · API 定价（全模型价格表） | https://docs.bigmodel.cn/cn/guide/start/pricing |
| S3 | 智谱官方文档 · 速率限制（并发机制、1302/1305、权益等级） | https://docs.bigmodel.cn/cn/api/rate-limit |
| S4 | 智谱官方文档 · 深度思考 thinking（参数说明、各模型思考行为） | https://docs.bigmodel.cn/cn/guide/capabilities/thinking |
| S5 | 智谱官方文档 · 核心参数（max_tokens 各模型表、thinking/reasoning_effort 详解） | https://docs.bigmodel.cn/cn/guide/start/concept-param |
| S6 | 智谱官方文档 · OpenAI API 兼容（base_url、extra_body thinking、流式、参数表、temperature 注意事项） | https://docs.bigmodel.cn/cn/guide/develop/openai/introduction |
| S7 | 智谱官方文档 · 模型迁移（兼容 OpenAI 所有 Endpoint） | https://docs.bigmodel.cn/cn/guide/platform/model-migration |
| S8 | 智谱官方文档 · 核心参数页（快速参考表、top_p 推荐、max_tokens 默认/上限表） | https://docs.bigmodel.cn/cn/guide/start/concept-param |
| S9 | 智谱官方文档 · 思考模式（轮级/交错/保留式思考、reasoning_content 回传要求） | https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode |
| S10 | 知乎 · GLM-4.7-Flash 评测：30B 级别最强模型，API 免费（1 并发、交织思考） | https://zhuanlan.zhihu.com/p/1997615716233401535 |
| S11 | 智谱官方文档 · Coding Plan 套餐概览（积分制、抵扣系数、非高峰 5 折） | https://docs.bigmodel.cn/cn/coding-plan/overview |
| S12 | 智谱官方文档 · 错误码（全表 + SSE finish_reason 注意事项） | https://docs.bigmodel.cn/cn/faq/api-code |
| S13 | 博客园 · 免费的普惠大模型 API（官方限 1 并发、AIME 91.6） | https://www.cnblogs.com/justin-Y/p/20078212 |
| S14 | 凤凰科技 · 智谱 GLM-4.7-Flash 发布并开源，可免费调用 | https://tech.ifeng.com/c/8q3vMXPQEMq |
| S15 | 什么值得买社区 · GLM-4.7-Flash 2026-01-20 永久免费开放 | https://post.smzdm.com/p/ad73vnnd |
| S16 | ofox.ai · GLM-4.7-Flash 免费 API 国内接入指南（1 并发实测数据、65 tokens/s） | https://ofox.ai/zh/blog/glm-4-7-flash-free-api-china-guide-2026/ |
| S17 | GitHub · zai-org/GLM-5 issue #39（请求支持 /responses 端点，未实现） | https://github.com/zai-org/GLM-5/issues/39 |
| S18 | CSDN · GLM-4-Flash 免费 API 发布（历史：新用户 2 并发） | https://blog.csdn.net/AIBigModel/article/details/141607816 |
| S19 | 智谱官方文档 · 用户权益（V0-V3 等级与并发权益） | https://docs.bigmodel.cn/cn/guide/platform/equity-explain |
| S20 | 智谱官方文档 · 实名认证 FAQ（API 不强制实名） | https://docs.bigmodel.cn/cn/faq/authentication-issues |
| S21 | Facebook 帖 · 未实名 400 万 tokens / 实名+邀请 2000 万（新人资源包口径） | https://www.facebook.com/jp6tw/posts/（见搜索结果） |
| S22 | V2EX 多帖 · GLM 限流/429 实锤（t/1187116、t/1206408、t/1205781、t/1203291） | https://v2ex.com/t/1187116 等 |
| S23 | 知乎 · GLM Coding Plan 7 天体验卡免费领 | https://zhuanlan.zhihu.com/p/2076249896244473928 |
| S24 | ZCode 官网 · 套餐价格（Lite ¥94.4/月 划线 ¥118） | https://zcode.z.ai/ |
| S25 | 知乎 · 2026-08-24 AI Coding Plan 对比（智谱 Lite/Pro/Max = 118/538/1078 元） | https://zhuanlan.zhihu.com/p/2075392954261320429 |
| S26 | 腾讯云开发者 · 智谱 Coding Plan 改版（V2 价 49/149/469、积分制）+ 36kr 涨价报道 | https://cloud.tencent.com/developer/article/2718987 、https://m.36kr.com/p/3767538055463681 |
| S27 | 智谱官方文档 · GLM-5.3-Flash 模型页（320B/18B、1M、AA 57 分、定价 1/10-1/20、夜间活动） | https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash |
| S28 | GitHub · hermes-agent issues #47685/#51276（GLM 429/1305 不要盲目重试、prompt 敏感 429） | https://github.com/NousResearch/hermes-agent/issues/47685 |
| S29 | 智谱官方文档 · 模型与产品发布记录（首帧 <400ms） | https://docs.bigmodel.cn/cn/update/new-releases |
| S30 | HuggingFace · zai-org/GLM-4.7-Flash 模型卡（SWE-bench 59.2、τ²-Bench 79.5、AIME 91.6、BrowseComp 42.8、HLE 14.4） | https://huggingface.co/zai-org/GLM-4.7-Flash |
| S31 | lambda.ai · GLM-4.7-Flash 推理页（基准分数汇总） | https://lambda.ai/inference-models/zai-org/glm-4.7-flash |
| S32 | X · Artificial Analysis（GLM-4.7-Flash τ²-Bench Telecom ~99% 全模型最高、Terminal-Bench 22%） | https://x.com/ArtificialAnlys/status/2014518379114332204 |
| S33 | Towards AI · GLM-4.7-Flash 基准解读（GLM-4.7 73.8%、Claude Sonnet 4.5 77.2%） | https://pub.towardsai.net/glm-4-7-flash-z-ais-free-coding-model-and-what-the-benchmarks-say-da04bff51d47 |
| S34 | onyx.app · 2026 编码模型横评（DeepSeek-V4-Flash SWE-bench 79%、LiveCodeBench 91.6%） | https://onyx.app/insights/best-llms-for-coding-2026 |
| S35 | DataCamp · GLM-5.3-Flash 特性（DeepSWE 63.4 vs Opus 4.8 58.0） | https://www.datacamp.com/blog/glm-5-3-flash |
| S36 | Hacker News · GLM-4.7-Flash 讨论（30B MoE A3B、SWE-bench 59.2） | https://news.ycombinator.com/item?id=46681896 |
| S37 | Reddit · LocalLLaMA 本地量化运行 GLM-4.7-Flash 体验帖 | https://www.reddit.com/r/LocalLLaMA/comments/1qmdf2a/ |
| S38 | 新浪财经 · GLM-4.6V 系列发布，较 4.5V 降价 50%（输入 1 元/输出 3 元） | https://finance.sina.com.cn/tech/digi/2025-12-08/doc-inhaavuy3526263.shtml |
| S39 | 智谱官方文档 · GLM-4.6V 模型页（106B/9B、原生多模态工具调用、场景矩阵） | https://docs.bigmodel.cn/cn/guide/models/vlm/glm-4.6v |
| S40 | 智谱官方文档 · 模型概览（全模型上下文/最大输出/免费标注） | https://docs.bigmodel.cn/cn/guide/start/model-overview |

---

## 附：未查到事项（诚实清单）

1. **GLM-4.7-Flash 独立的默认/最大 max_tokens 官方表格行**——官方"核心参数"页只列了 glm-4.7（默认 65536/最大 131072），Flash 未单列（按模型页"最大输出 128K"+官方示例 65536 执行）
2. **官方公开的 RPM/TPM 具体数字**——智谱只按"并发数"限速，未公布 RPM/TPM 表
3. **智谱 429 响应是否带 Retry-After 头**——官方文档未提及，社区帖也未截图证实
4. **GLM-4.7-Flash 的 HumanEval/MBPP 分数**——新旧来源均无（行业已弃用这两个基准）
5. **免费 Flash 档的每日 token 总上限**——官方无公开数字，社区实测单线程 1 小时 18 万输出 token 未触发限制
