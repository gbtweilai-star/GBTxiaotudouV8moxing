# HUD 错误显示改进方案（待风哥批准后动刀）

> 目标：把第三方的**模糊报错**（例：`初始化未返回 sessionInfo`）替换为**可执行的业务原因**
> （例：`积分不足，请充值`）。走《响应体优先律》：先拿业务码，再决定文案。

## 一、解析哪一层

| 项 | 决定 |
| --- | --- |
| 落点 | 前端 `holo_pet/app.js` 的星云初始化链路（`startXingyun()` 及其 catch/重试分支） |
| 数据源 | SDK 内部已发出 `POST /user/v1/ttsa_v2/session`，但**SDK 不暴露响应体** |
| 方案 A（推荐） | 在加载 SDK 前**包装 `window.fetch`**：仅当 URL 含 `ttsa_v2/session` 时，读取 `response.clone().json()` 副本，把 `error_code/error_reason` 暂存到 `xingyun.lastBusinessError`。**不改动原响应、不改变请求行为** |
| 方案 B（不推荐） | 由本地后端代理该请求、服务端解析后再下发。改面更大、涉及凭据转发，风险更高 |

选 A 的理由：**不碰 SDK、不碰凭据、不碰后端**；只在本地读一份副本；整段用 try/catch 包裹，失败即静默，绝不影响主链路。

## 二、怎么映射

先只覆盖**已知码**，未知码**如实透传原文**（宪章第十五条：只接受证据，不许编造解释）：

| error_code | 显示文案（HUD） | 建议动作 | 可等待? |
| --- | --- | --- | --- |
| 5 | 积分不足，请充值 | 充值 / 等额度重置 | 是 |
| 4 | 凭据签名错误 | 检查 App ID / Secret | 否 |
| 其他 | `原样透传 error_code + error_reason` | 按原文判断 | 按原文 |

映射表以前端常量维护，便于日后按官方错误码文档扩充（不做自动猜测）。

## 三、什么条件下显示

1. **触发**：星云初始化失败（catch 或重试耗尽）**且**本次会话窗口内捕获到业务错误码。
2. **位置**：面板 HUD（`#xingyun-hud-text`）与桌面 APP 的同一 HUD；同时写入任务时间线（`addTimeline`）留审计痕迹。
3. **优先级**：**业务码文案 > SDK 模糊文案**（前者是证据，后者只是症状）。
4. **兜底**：捕获不到业务码时保持现状，并在文案后追加「（未捕获业务码）」以示诚实。
5. **重试策略联动**：映射为"可等待类"（如积分不足）→ 重试上限由 3 次**降为 1 次**，避免无意义重试继续消耗配额；映射为网络类 → 保留 3 次。

## 四、怎么验证改对了

| 层 | 手段 |
| --- | --- |
| 静态 | `node --check holo_pet/app.js` |
| 真实复现 | **当前正好有真实错误可用**：积分不足状态下复测，HUD 应显示「积分不足，请充值」而非模糊文案 |
| 回归 | `holo_pet` 面板专项 20 项 + 全量 90 项，红项数不得上升 |
| 镜像先行 | 改动前先在镜像/副本页面验证通过，再落生产文件（宪章第六条） |

## 五、风险与边界

- 包装 `fetch` 属**全局副作用**：只读副本、不改响应、try/catch 兜底、仅对星云 URL 生效；
- 不触碰 SDK、凭据、后端；
- 若未来 SDK 自行暴露响应体，本层可整体退役（改为优先读取 SDK 提供值）。

---

## 七、风哥批复的五条附加条件（落地方案 · 2026-09-15）

### ① URL 白名单硬编码（不许模糊匹配）

```js
const HUD_HOOK_URL_MARKERS = ["/user/v1/ttsa_v2/session"];   // 纯字符串包含匹配
const hudHookTargets = (url) =>
  HUD_HOOK_URL_MARKERS.some((marker) => String(url).includes(marker));  // 不用正则
```

不含标记的请求：**原样放行，完全不碰**。

### ② 失败必须静默

```js
try { /* 读副本、解析、留痕 */ }
catch (err) { if (HUD_HOOK_DEBUG) console.warn("[hud-hook] swallow:", err && err.message); }
return originalResponse;   // 永远返回原始响应，不抛、不阻塞
```

### ③ SDK 兼容模式开关

```js
const HUD_HOOK_ENABLED = true;   // 配置项：HUD_RESPONSE_BODY_HOOK
// 关掉即整层退役：window.fetch 保持原函数引用，不留尾巴
```

### ④ 每次捕获必须留痕

捕获到业务码时，向任务时间线写一条结构化记录：

```
{ at, url, error_code, error_reason, sessionId }
```

（时间 / URL / 业务码 / 原因 / 本次会话 ID —— 供事后回溯证据）

### ⑤ 重试联动：数据驱动，不许 if-else 泥巴

```js
const HUD_RETRY_POLICY = {
  waitable: 1,   // 可等待类（积分不足 / 配额）→ 重试 1 次
  network: 3,    // 网络类 → 重试 3 次
  default: 3,
};
const HUD_CODE_CLASS = { 5: "waitable", 4: "network" };   // 业务码 → 类别
```

**可读**（策略集中在一张表）、**可测**（喂码断言返回次数）、**可关**（把开关设为 false 即回到 3 次）。

---

## 八、镜像验证记录（先镜像、后生产 · 宪章第六条）

镜像实现与测试位于 `.scratch/hud_mirror/`（**不触碰生产文件**）：

- `hud_hook.mirror.js` —— 包装 `window.fetch` 的只读 Hook（节点可注入）
- `hud_hook.test.mjs` —— 覆盖：白名单命中/不命中、解析失败静默、开关关闭退役、业务码映射、重试策略

测试通过后，才允许把等价实现落进 `holo_pet/app.js`。

## 六、本方案遵守的宪章条款

第一条（先取官方口径）、第十五条（只接受证据）、第十六条（不许改期望糊测试）、
第十七条（镜像先行）、第十九条（能回答为什么改 / 证据是什么 / 怎么验证）。
