# DeepSeek/ECC Harness 深度研究与主模型进化方案

> 研究视角：Harness 进化架构师 —— 用 ECC/Harness 的方法论（上下文窗口优化、持久化、工作环、agent/skill 编排）升级 GBT 主模型的调用层，让即将接入的 GLM-4.7-Flash 主模型更聪明、更高效。
> 本方案基于本机真实资产：`brain/llm_client.py`（597 行，26KB）、已吞噬的 ECC Harness（68 agents / 286~292 skills / 121 rules / 19 harness 适配）、harness_fusion cap。

---

## 一、ECC Harness 精髓（它到底做了什么优化）

ECC（`affaan-m/ECC`，前身 `everything-claude-code`）自称 **"The agent harness performance optimization system"**，核心理念一句话：

> **"Optimize the context window. Persist everything else."**（优化上下文窗口，其余全部外置持久化）

它并不是一个"更好的提示词包"，而是一套**把 LLM 的上下文窗口当作稀缺预算来经营的操作系统**。其核心工作环是：

```text
plan → test → implement → review → verify → remember → improve
```

### 1.1 核心优化手段拆解

| ECC 手段 | 它解决什么问题 | 具体做法 |
|---|---|---|
| **Skills 按需加载** | 全量塞 system prompt 会烧干窗口 | 292 个 skill 只在任务需要时注入（"Loaded when the task needs them"），未用到的 skill 只占约 100 token 的注册表条目 |
| **Agents 上下文隔离** | 同一个被污染的上下文既写代码又审代码 | 规划/评审/实现分给独立 subagent，各自独立上下文 + 独立工具权限，评审用"fresh context"找盲点 |
| **Rules 选择性常驻** | "请用 TDD"这种指令模型会忘 | 常驻规则按语言/项目**选择性安装**，不是全装；`common/`（语言无关）才默认装 |
| **Hooks 上下文外执行** | 质量检查不能靠模型自觉 | 确定性检查（grep console.log 等）由 harness 事件触发脚本，**在模型上下文之外**运行，不占 token |
| **Instincts 置信度召回** | 会话学到的东西要能复用 | 从真实会话提取"本能"模式，带置信度分数，相关时才召回 |
| **Memory Vault 跨 harness 持久化** | 会话记忆 ≠ 存巨量 transcript | 会话蒸馏成摘要/本能/可复用 skill，`.ecc/memory/` 下存可检索 Markdown（`ecc.memory.v1` 格式），多 harness 共享交接 |
| **Token 预算显式管理** | 隐藏思考 token 是成本大头 | `MAX_THINKING_TOKENS` 从 31,999 压到 10,000（省 ~70% 隐藏成本），`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=50` 提前 compaction，subagent 用便宜模型（haiku） |
| **战略 compaction** | 自动 compaction 会在任务中途触发 | 在**逻辑断点**（研究完→实现前、里程碑完成→下一阶段）手动 `/compact`，而不是等到 95% 窗口爆掉 |

### 1.2 ECC 对标对象的本质差异

ECC 对标的是 **OpenAI Codex CLI / Claude Code 这类 coding agent harness**。它的洞察是：这些 harness 的"笨"往往不是模型弱，而是**上下文被低价值 token 淹没**——工具描述太多、MCP 全开、历史 transcript 无限堆叠、thinking token 无上限。ECC 用"分层 + 外置 + 按需 + 预算"四招把窗口还给真正有用的推理。

### 1.3 对 GBT 的可移植结论

GBT 的 `brain/llm_client.py` 目前是一个**纯通道回退层**（agnes→glm→deepseek 多通道 + 视觉缓存 + RPM 节流），但**没有上下文预算管理、没有 skill 按需注入、没有工作环、没有记忆蒸馏**。ECC 给我们的可移植内核是四件事：**① 上下文分级预算表 ② skill 注册表（~100 token）+ 按需注入（~1000 token）③ 工作环状态机外置到 harness ④ 会话→摘要的持久化闭环**。

---

## 二、业界 harness 上下文管理最佳实践（各家对比表）

| Harness / 框架 | 分层 system prompt | 工具描述压缩 | 记忆外置 | compaction 策略 | 关键数字 |
|---|---|---|---|---|---|
| **Claude Code**（Anthropic） | CLAUDE.md/子目录渐进加载 | MCP 工具描述按需，建议 <80 工具 / <10 MCP | `/save-session`/`/resume-session` 摘要持久化 | 自动 compaction 阈值可调 + 手动 `/compact`、`/clear` | `MAX_THINKING_TOKENS` 31,999→10,000 省 70%；subagent 用 haiku 省 80% |
| **Anthropic 官方上下文工程** | 上下文=有限资源，结构化笔记 | — | 结构化 note-taking（agent 写持久笔记） | 三种策略：compaction、structured note-taking、multi-agent | 明确"memory = 结构化笔记，不是存 transcript" |
| **OpenAI Codex CLI** | `AGENTS.md` 根→叶读取，近者覆盖，到 size 上限即停 | 工具按任务注入 | 会话外文件 + AGENTS.md | `/compact` + 断点压缩 | AGENTS.md 有 size 上限，超限跳过 |
| **Claude Skills / Agent Skills 标准** | 三层加载：元数据→正文→资源 | 注册表 ~100 token/skill，正文 ~1000 token 仅调用时加载 | — | progressive disclosure | 10 个 skill 注册表仅 ~600-800 token，全量注入要 15,000+ |
| **LangChain progressive disclosure** | 渐进披露 | 按需加载 | — | — | 核心是"按需而非前置加载" |
| **Alibaba SkillWeaver** | 跳过全库加载，路由到相关工具 | 工具路由 | — | — | 复杂场景 token 用降 99% |
| **Gemini 工具调用指南** | — | 有效工具集保持 **10-20 个以内** | — | — | 工具过多显著降低准确率 |

**统一结论（可落地到 GBT）**：
1. **注册表 + 按需正文**是行业标准答案——skill 的"名字+一句话描述"常驻（~100 token/条），完整 SKILL.md 只在命中时注入（~1000 token/条）。
2. **工具/能力数量有硬上限**——Gemini 建议 10-20，Claude Code 建议 <80，超过就降智。
3. **记忆 = 结构化笔记，不是 transcript**——Anthropic、ECC 两家独立得出同一结论。
4. **compaction 要战略化**——在逻辑断点做，不在任务中途做。
5. **thinking token 是隐藏成本大头**——必须显式设上限，简单任务直接关。

---

## 三、GLM-4.7-Flash 接入特性清单

> 来源：智谱官方文档 `docs.bigmodel.cn`（模型页 + 思考模式页 + 速率限制页）、HuggingFace `zai-org/GLM-4.7-Flash`、官方发布通稿。

### 3.1 基础规格

| 维度 | 值 | 备注 |
|---|---|---|
| 架构 | **30B 总参 / 3B 激活**，MoE + MLA | 30B-A3B，激活仅 3B 实现轻量推理 |
| 发布 | 2026-01-20 开源 | 免费 API 调用 |
| 上下文窗口 | **200K**（官方中文文档） | 英文社区/Cloudflare 记 128K~131,072，**以官方 200K 为准**；本地部署版（Unsloth）标 200K |
| 最大输出 | **128K** | |
| 输入/输出模态 | 纯文本 | 无视觉（视觉仍需 agnes-2.5-flash / glm-4.6v 通道） |
| 定位 | **Agentic Coding 强化** | SWE-bench Verified 59.2%，同尺寸开源 SOTA，官方称编程/长程规划/工具协同强 |
| 免费并发 | **1 并发**（免费档） | 社区实测曾为 3 并发后收紧；`awesome-free-llm-apis` 记 1 concurrent request |

### 3.2 思考模式（关键，直接影响调用层设计）

- **默认开启 Thinking**：GLM-4.7 系列默认开思考（不同于 GLM-4.6 的"混合 thinking 自动开启"）。关掉需显式 `"thinking": {"type": "disabled"}`。
- **轮级思考（Turn-level Thinking）**：GLM-4.7 **新引入**，同一会话内**每一轮可独立开关思考**——轻量轮次关思考求快，复杂轮次开思考求准。这是给 GBT 做"思考开关策略"的官方依据。
- **交错式思考（Interleaved thinking）**：GLM-4.5 起默认支持，工具调用之间、收到工具结果后都能继续思考。
- **保留式思考（Preserved thinking）**：`clear_thinking: False`，编码/Agent 场景推荐开启——保留先前 assistant 回合的 reasoning_content 能**提升缓存命中率、省 token**；但要求把完整未修改的 reasoning_content 原样传回 API。
- **强制约束**：用交错思考+工具时，**必须显式保留 reasoning content 并在返回工具结果时一并回传**，否则推理连续性断裂。

### 3.3 其他能力

- **Function Calling 强**（面向 Agentic Coding）、**结构化输出**（JSON）、**上下文缓存**、**MCP 支持**、流式输出。
- **速率限制错误码**：`1302`（用户级并发/频率超限）、`1305`（平台过载）。官方建议"请求队列/并发池 + 避免固定间隔高频重试 + 异步/批处理 API"。

### 3.4 对 GBT 的接入要点

1. GLM-4.7-Flash 走智谱 `https://open.bigmodel.cn/api/paas/v4/chat/completions`，`model="glm-4.7-flash"`，OpenAI 兼容（`zai-sdk` / 原生 openai SDK 均可）。
2. **纯文本**——现有 `_supports_images()` 对 glm 通道应标记 `False`，图片剥离降级逻辑（现有 1210/400/image 剥离）直接复用。
3. **1 并发是硬约束**——GBT 现有 `_throttle()` 只做 RPM 节流，需补"并发信号量=1"的排队。
4. **thinking 参数**用 `extra_body`/`thinking` 字段透传，`_strip_think()` 已能剥推理标签，但 GLM 是 `reasoning_content` 独立字段而非 `<think>` 标签，需按通道适配剥离逻辑。
5. **回退链**：现有 glm 通道默认 `glm-5.2`，应把主模型默认切到 `glm-4.7-flash`（200K 窗口 + 编码强化 + 免费），glm-5.2 降为可选。

---

## 四、GBT 主模型进化方案（六项）

> 落地坐标全部指向 `brain/llm_client.py`（597 行）。现状以该文件实际代码为准。

---

### 4.1 上下文预算管理（ECC 式分层）

**现状**：`llm_chat(prompt, system, max_tokens, ...)` 里 `system` 是调用方一次性塞进来的字符串，`prompt` 是用户内容，**没有任何 token 预算概念**；`max_tokens` 只限输出不限输入。调用方（brain_ring 等）想塞多少 system 就塞多少，长期会话 transcript 堆叠无上限。

**设计**：引入 ECC 式四层预算表，把"人设 / 工具描述 / 会话记忆"分级外置。针对 GLM-4.7-Flash 的 **200K 窗口**，预算分配表如下：

| 层级 | 内容 | 预算 | 常驻? | 外置位置 |
|---|---|---|---|---|
| L0 人设/硬规则 | 你是谁、安全底线、语言契约 | ≤ 2K | ✅ 每轮 | 内存常量（精简版） |
| L1 工具/能力注册表 | 技能名 + 一句话描述（每条 ~100 token） | ≤ 4K（约 40 条命中） | ✅ 每轮 | 按任务路由后注入 |
| L2 会话工作记忆 | 当前任务目标、关键结论、待办 | ≤ 8K | ✅ 每轮 | 从持久化摘要加载 |
| L3 历史 transcript | 原始对话全文 | 不常驻 | ❌ | 磁盘 JSONL，按需检索 |

**落地（`brain/llm_client.py`）**：

1. 新增模块级常量与函数：
```python
# 预算常量（token 估算用字符/4 粗算）
_CTX_BUDGET = {"persona": 2048, "skills": 4096, "workmem": 8192, "reserve": 4096}
_CTX_WINDOW = 200_000          # glm-4.7-flash 官方窗口
_CTX_HARD_CAP = 180_000        # 留 20K 给输出，防爆窗

def _estimate_tokens(text: str) -> int:
    """粗算 token：中文约 1 字 1 token，英文约 4 字符 1 token。精确可用 tiktoken，此处求快。"""
    # 混合粗估：中文字符按 1，其余按 len/4
    cjk = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    return cjk + (len(text) - cjk) // 4

def _assemble_system(persona: str, skill_registry: str, workmem: str) -> str:
    """ECC 式分层拼装：persona 常驻 + 命中 skill 注册表 + 会话工作记忆。"""
    parts = [persona[: _CTX_BUDGET["persona"]]]
    if skill_registry:
        parts.append("[可用能力]\n" + skill_registry[: _CTX_BUDGET["skills"]])
    if workmem:
        parts.append("[工作记忆]\n" + workmem[: _CTX_BUDGET["workmem"]])
    return "\n\n".join(parts)
```

2. 改 `llm_chat()` 签名，新增可选参数 `skill_registry=""`、`workmem=""`，在拼 `system` 时调用 `_assemble_system()`，并在请求前做一次**预算超限保护**：
```python
# 在 _chat/_responses 发出前：
_total_in = _estimate_tokens(system) + _estimate_tokens(prompt)
if _total_in > _CTX_HARD_CAP:
    # 裁剪：优先砍历史 prompt 尾部（旧消息最不重要），再砍 workmem
    ...
```

3. `_chat()` 与 `_responses()` 的 `system` 字段统一走 `_assemble_system()`，避免调用方绕过预算。

---

### 4.2 Skill 按需注入（注册表 + 词法粗筛 + 可选 embedding）

**现状**：GBT 有 539 caps + 286 吞噬 skills，但 `llm_client.py` **完全不知道 skill 的存在**——调用方要么全塞，要么不塞，没有中间态。

**设计**：ECC 的"注册表常驻 + 正文按需"。分两阶段：

- **Phase 1（词法粗筛，零依赖，立即上）**：维护一个 skill 索引文件（`skills_index.json`，skill 名 + 一句话描述 + 关键词 tag）。任务来了，用**关键词/子串匹配**对任务文本做粗筛，命中 top-K（K=8~12）个 skill，只把它们的"名字+一句话描述"注入注册表。完整 SKILL.md 正文由上层决定是否二次加载。
- **Phase 2（embedding 精排，可选）**：若词法召回质量不足，引入 embedding 向量（GBT 已有智谱 embedding 通道可复用），做余弦相似度 top-K 召回。**先不引入**，词法够用。

**落地**：

1. 新增模块：
```python
_SKILL_INDEX: list[dict] = []   # [{"name":..., "desc":..., "tags":[...], "path":...}]
_SKILL_TOP_K = 10

def load_skill_index(idx_file: str = None) -> None:
    """加载 skill 索引（由上层扫描 caps/skills 目录生成，llm_client 只消费）。"""
    import json as _j
    _p = idx_file or Path(__file__).parent / "skills_index.json"
    if _p.exists():
        _SKILL_INDEX[:] = _j.loads(_p.read_text(encoding="utf-8"))

def route_skills(task_text: str) -> str:
    """词法粗筛：任务文本 vs 每个 skill 的 name+desc+tags，命中返回注册表文本。"""
    if not _SKILL_INDEX:
        return ""
    scored = []
    _t = task_text.lower()
    for s in _SKILL_INDEX:
        hay = (s.get("name","") + " " + s.get("desc","") + " " + " ".join(s.get("tags",[]))).lower()
        score = sum(1 for w in _t.split() if w in hay)   # 简单词法命中
        if score:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    picked = scored[:_SKILL_TOP_K]
    return "\n".join(f"- {s['name']}: {s['desc']}" for _, s in picked)
```

2. 在 `llm_chat()` 调用前由上层执行 `route_skills(task_text)`，结果作为 `skill_registry` 传入（接 4.1 的 `_assemble_system`）。

3. **token 收益量化**：286 个 skill 全量注入约 286×1000 ≈ 286K token（直接爆窗）；注册表模式只需 10×100 ≈ 1K token，**省 99.6%**。

---

### 4.3 工作环接入（ECC plan→test→implement→review→verify→remember→improve）

**现状**：GBT 已有 brain_ring（运转环），但它是**调用层外的调度逻辑**，`llm_client.py` 只暴露 `llm_chat` / `llm_chat_stream` / `vision_chat` 三个原子接口，环状态、证据链、fresh-context 评审都靠上层手搓。

**设计**：把 ECC 工作环的**状态机 + 证据链**下沉到调用层可感知的轻量协议，但**不重写 brain_ring**——只给它提供"环友好的调用原语"：

1. **阶段标记（phase tag）**：每次调用可带 `phase`（plan/test/implement/review/verify/remember/improve），`llm_client` 据此切换 `system` 人设片段与 thinking 开关（见 4.4）。
2. **fresh-context 评审**：`review` 阶段用**独立精简上下文**（只带任务目标 + 代码 diff + 工作记忆，不带历史 transcript），复现 ECC"新上下文找盲点"。
3. **evidence 落盘**：每个阶段结束时把产物（plan 文本、测试结果、review 结论）写进记忆文件（见 4.6），供下一环读取。

**落地**：

1. `llm_chat()` 新增 `phase: str = ""` 参数：
```python
_PHASE_PERSONA = {
    "plan":     "你是规划者：只输出方案拆解，不写实现代码。",
    "implement":"你是实现者：按计划写最小可用实现。",
    "review":   "你是评审者：用全新视角找 bug、盲点、回归风险，不修改代码。",
    "verify":   "你是验证者：核对产出是否满足验收标准。",
    "remember": "你是记忆整理者：蒸馏本次会话为结构化摘要。",
}
# 拼 system 时：若 phase 有值，把 _PHASE_PERSONA[phase] 前置进 persona
```

2. `review` 阶段通过 `workmem` 只传"目标 + diff + 关键约束"，实现 fresh-context（复用 4.1 的 `_assemble_system`，只是不传 skill_registry 和长 prompt 历史）。

3. **与 brain_ring 的接口**：brain_ring 在每环调用 `llm_chat(..., phase="plan")` → `... phase="implement"` ...，`llm_client` 内部自动切换人设与 thinking，brain_ring 无需改流程，只加一个参数。

---

### 4.4 思考模式策略（GLM-4.7 混合思考开关）

**现状**：`_strip_think()` 剥离 `<think>...</think>` 标签（针对 agnes/glm 旧格式），但**没有主动控制 thinking 开关**——模型默认开不开、怎么关，完全没管。

**设计**：利用 GLM-4.7 官方"轮级思考"能力，做**任务分级开关**：

| 任务类型 | thinking | 依据 |
|---|---|---|
| 简单对话 / 事实查询 / 改措辞 | `disabled` | 官方：轻量轮次关思考求快 |
| 代码生成 / 复杂规划 / 多约束推理 / 调试 | `enabled` | 官方：重任务开思考提升正确率 |
| 工具调用（执行轮） | `disabled` | 官方：快速执行轮降低推理开销 |
| 工具结果综合（决策轮） | `enabled` | 官方：综合工具结果做决策再开深度思考 |
| Agent/Coding 长任务 | `enabled` + `clear_thinking: False` | 官方：保留式思考提升缓存命中、省 token |

**落地**：

1. 新增思考策略函数：
```python
def _thinking_policy(phase: str = "", complex_hint: bool = False) -> dict:
    """GLM-4.7 轮级思考开关。返回 thinking 参数 dict（仅 glm-4.7 通道生效）。"""
    if phase in ("plan", "implement", "review", "verify") or complex_hint:
        return {"type": "enabled", "clear_thinking": False}   # 编码/推理：保留式思考
    if phase in ("remember", "improve"):
        return {"type": "disabled"}                            # 整理轮：求快
    # 默认普通对话：关思考（GLM-4.7 默认开，需显式关）
    return {"type": "disabled"}
```

2. 改 `_chat()`：当 `_p["model"]` 以 `glm-4.7` 开头（或 provider 为 zhipu 且模型在 thinking 支持列表）时，把 `_thinking_policy()` 结果塞进请求体：
```python
_body = {"model": model, "messages": msgs, "max_tokens": max_tokens}
if model.startswith("glm-4.7") or model.startswith("glm-5"):
    _body["thinking"] = _thinking_policy(phase, complex_hint)
```

3. **改 `_strip_think()` 适配 GLM**：GLM-4.7 的推理在 `reasoning_content` 独立字段（流式是 `delta.reasoning_content`），不是 `<think>` 标签。需在 `_chat()` 解析处增加：优先取 `message.content`，**丢弃 `message.reasoning_content`**（或单独存到 `_CH_STATS` 供调试），避免推理痕迹混进最终回复。

4. **保留式思考的回传约束**：若 `clear_thinking: False`，多轮调用必须把上一轮完整 `reasoning_content` 原样回传（放进 assistant message 的 `reasoning_content` 字段）。`llm_client` 需维护一个**按会话/调用方维度的 reasoning 缓存**：
```python
_REASONING_CACHE: dict = {}   # {session_id: reasoning_content}
# 每次 _chat 发出时：若 clear_thinking 且缓存有值，把 reasoning_content 附到最后的 assistant message
# 每次收到响应时：更新缓存
```

---

### 4.5 多通道回退链升级（agnes→glm-4.7-flash→deepseek）

**现状**：`_provider()` 依据环境变量选主通道；`llm_chat()` 内做 responses→chat 双端点回退 + 末尾硬编码 DeepSeek 兜底；视觉走独立 `VISION_CHANNELS`（agnes→glm-4.6v→glm-4.5v）。

**设计**：新回退顺序与分工（接入 GLM-4.7-Flash 后）：

| 优先级 | 通道 | 用途 | 触发条件 |
|---|---|---|---|
| 1 | **glm-4.7-flash**（智谱免费） | **主文本模型**：编码/推理/Agentic Coding | 默认 |
| 2 | agnes-2.5-flash | 备用文本 + **主视觉**（唯一稳定看图） | glm 429/超时/1302 时回退 |
| 3 | deepseek-v4-pro（推理脑，`_ACTIVE_BRAIN_PROVIDER`） | 深度推理独立通道 | 独立脑任务，不参与普通回退 |
| 4 | kimi/nvidia/tokenhub/charger | 可选扩展 | 显式配置 |

关键调整：
1. **glm-4.7-flash 升主**：`_provider()` 里 glm 通道默认模型从 `glm-5.2` 改 `glm-4.7-flash`；`has_responses=False`（纯 chat/completions）。
2. **并发=1 信号量**：免费档 1 并发，现有 `_throttle()` 只节流 RPM，需加全局信号量 + 排队：
```python
import threading
_GLM_SEM = threading.Semaphore(1)   # glm-4.7-flash 免费档 1 并发
# 在 llm_chat 走 glm 通道时：
with _GLM_SEM:
    _r = _chat(...)
```
3. **错误码 1302/1305 识别**：现有代码只认 `"429"/"Too Many"/"限流"`，需补智谱专属错误码 `1302`（用户限流）、`1305`（平台过载）→ 前者 `time.sleep(15)` 重试，后者换通道回退 agnes。
4. **视觉与文本彻底解耦**：`_supports_images("glm-4.7-flash")` 必须返回 `False`，图片请求自动路由到 `vision_chat()`（现有 VISION_CHANNELS 不动），文本请求走 glm-4.7-flash，避免图片污染文本主通道。

**落地**：改 `_provider()` 中 glm 分支的默认 model；改 `_supports_images()` 加 `glm-4.7-flash` 黑名单；改 `llm_chat()` 的异常分支识别 1302/1305；加 `_GLM_SEM`。

---

### 4.6 记忆持久化（"Persist everything else" 落地）

**现状**：GBT 已有 JSONL/记忆文件体系（`memory/YYYY-MM-DD.md` 日日志、`MEMORY.md` 长期、视觉缓存 `~/.gbt/visual_memory/native_vision_cache.json` 磁盘持久化），但 `llm_client.py` 只做视觉缓存持久化，**文本会话记忆蒸馏完全没接**。

**设计**：把 ECC"会话→摘要→可复用 skill/本能"的三级蒸馏，接到 GBT 现有记忆体系上：

1. **会话摘要（每会话落盘）**：`remember` 阶段（4.3）触发一次轻量蒸馏调用，把当前会话提炼为结构化摘要，写 `memory/session/`（新增目录），键 = 会话 ID。
2. **工作记忆（跨会话加载）**：新会话开始时，加载最近 N 条会话摘要的前 8K token 作为 `workmem`（4.1 L2），不加载原始 transcript。
3. **本能/可复用结论（长期）**：多次出现的高价值结论，由上层人工确认后提升进 `MEMORY.md`（保护文件，不自动写，符合 GBT 现有权限规则）。
4. **JSONL transcript 外置**：原始对话全文写 `memory/transcript/{session_id}.jsonl`，上下文窗口内**永不常驻**，只有显式检索才读回。

**落地**（新增，不侵入现有 `llm_chat` 主流程，作为可选副作用）：

```python
def persist_session(session_id: str, summary: str, transcript: list = None) -> None:
    """ECC 式会话持久化：摘要常驻可加载，transcript 外置 JSONL 可检索。"""
    _sdir = Path.home() / ".gbt" / "memory" / "session"
    _tdir = Path.home() / ".gbt" / "memory" / "transcript"
    _sdir.mkdir(parents=True, exist_ok=True); _tdir.mkdir(parents=True, exist_ok=True)
    (_sdir / f"{session_id}.md").write_text(summary, encoding="utf-8")
    if transcript:
        with (_tdir / f"{session_id}.jsonl").open("a", encoding="utf-8") as f:
            for m in transcript:
                f.write(json.dumps(m, ensure_ascii=False) + "\n")

def load_workmem(limit_tokens: int = 8192) -> str:
    """加载最近会话摘要作为工作记忆（受预算约束）。"""
    _sdir = Path.home() / ".gbt" / "memory" / "session"
    if not _sdir.exists():
        return ""
    parts = []
    for p in sorted(_sdir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
        parts.append(p.read_text(encoding="utf-8"))
        if _estimate_tokens("\n".join(parts)) >= limit_tokens:
            break
    return "\n\n".join(parts)[:limit_tokens * 4]   # 粗裁剪
```

**与现有记忆体系的关系**：`persist_session` 只写 `~/.gbt/memory/` 下的**新子目录**，不触碰 `MEMORY.md`/`USER.md` 等保护文件（提升进保护文件需显式授权，符合 GBT 权限红线）。日日志 `memory/YYYY-MM-DD.md` 继续由上层写，`llm_client` 不越权。

---

## 五、风险与依赖

| 风险 | 影响 | 缓解 |
|---|---|---|
| **免费档 1 并发**是硬约束，脑循环/多线程并发调用会撞 1302 | 主通道频繁降级 | `_GLM_SEM` 信号量 + 队列串行化；高并发任务显式降级 agnes/deepseek |
| **200K 窗口的"伪 128K"**：社区/Cloudflare 记 128K，官方记 200K，实际可用可能更小 | 预算表超配导致爆窗 | 预算表按保守 **128K 硬上限**设计，输出留 20K，输入不超 108K |
| **保留式思考的 reasoning_content 回传约束**：回传错误会降效并伤缓存 | 多轮推理质量下降 | `_REASONING_CACHE` 严格原样回传，不做重排/修改；单次调用不启用 clear_thinking |
| **`_strip_think()` 不匹配 GLM 的 `reasoning_content` 字段** | 推理痕迹混入回复 | 4.4 落地第 3 条：解析层显式丢弃 reasoning_content |
| **skill 索引文件不存在/过期** | 路由失效，回退空注册表 | `route_skills()` 找不到索引返回 `""`（安全降级为不注入），索引由上层扫描任务定期刷新 |
| **词法粗筛召回差**（同义词/跨语言） | 该注入的 skill 漏注入 | Phase 2 引入 embedding 精排（复用智谱 embedding 通道） |
| **工作环接入与 brain_ring 耦合** | 重复状态机 | 只给 `llm_chat` 加 `phase` 参数，状态机仍在 brain_ring，调用层不越权 |
| **GLM-4.7-Flash 是纯文本** | 误把图片请求打到文本通道 | `_supports_images` 黑名单 + 图片剥离降级逻辑复用 |
| **免费 API 政策变动**（并发/限额调整） | 主通道不可用 | 多通道回退链已存在，glm 挂掉自动降 agnes→deepseek |

---

## 六、来源清单

**ECC Harness**
1. ECC 官方仓库 README（核心工作环、Token Optimization、Key Concepts、Memory Vault）：https://github.com/affaan-m/ECC
2. ECC Token Optimization Guide：https://github.com/affaan-m/ecc/blob/main/docs/token-optimization.md
3. ECC harness-optimizer agent（eval 驱动 / pass@k）：https://github.com/affaan-m/ecc/blob/main/agents/harness-optimizer.md
4. ECC 2.0.0 发布讨论：https://github.com/affaan-m/ECC/discussions/2213
5. 第三方解读（ECC 结构/星级）：https://www.augmentcode.com/learn/everything-claude-code-github-stars 、 https://www.datacamp.com/tutorial/everything-claude-code

**业界 harness 上下文最佳实践**
6. Anthropic《Effective context engineering for AI agents》(2025-09-29)：https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
7. Claude Code Compaction 官方文档：https://platform.claude.com/docs/en/build-with-claude/compaction
8. Claude Code 成本管理（prompt caching / token 优化）：https://code.claude.com/docs/en/costs
9. LangChain 按需 skill 加载（progressive disclosure）：https://docs.langchain.com/oss/python/langchain/multi-agent/skills-sql-assistant
10. Agent Skills 三层加载（~100 token 注册表 / ~1000 token 正文）：https://ai.plainenglish.io/how-claude-skills-actually-work-and-how-to-build-the-same-architecture-in-your-product-75f2c8e249fc
11. Alibaba SkillWeaver（跳过全库加载，token 降 99%）：https://venturebeat.com/orchestration/new-alibaba-ai-framework-skips-loading-every-tool-cutting-agent-token-use-99
12. Gemini 工具调用指南（有效工具集 10-20 个）：https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/tools/function-calling
13. Codex AGENTS.md / 上下文管理：https://iceberglakehouse.com/posts/2026-03-context-openai-codex/ 、 https://getunblocked.com/blog/codex-context-window/

**GLM-4.7-Flash**
14. 智谱官方模型页（30B/3B、200K、128K 输出、Agentic Coding）：https://docs.bigmodel.cn/cn/guide/models/free/glm-4.7-flash
15. 智谱官方思考模式文档（轮级/交错/保留式思考、thinking.type、clear_thinking）：https://docs.bigmodel.cn/cn/guide/capabilities/thinking-mode
16. 智谱官方速率限制文档（并发限制、错误码 1302/1305）：https://docs.bigmodel.cn/cn/api/rate-limit
17. HuggingFace 官方模型卡（30B-A3B MoE）：https://huggingface.co/zai-org/GLM-4.7-Flash
18. GLM-4.7-Flash SWE-bench Verified 59.2%：https://www.threads.com/@testingcatalog/post/DTsklM2DSdF/ 、 https://news.ycombinator.com/item?id=46681896
19. 免费 API 并发（1 concurrent request）：https://github.com/mnfst/awesome-free-llm-apis
20. 发布通稿（2026-01-20 开源、免费调用）：https://finance.sina.com.cn/tech/2026-01-20/doc-inhhxehz7308958.shtml

---

*本方案由 Harness 进化架构师 subagent 产出，落地坐标以 `brain/llm_client.py` 实际 597 行代码为准；所有"改哪个函数、加什么逻辑"均已标注到具体函数级。*
