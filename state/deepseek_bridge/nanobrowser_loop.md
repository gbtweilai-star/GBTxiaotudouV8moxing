# Nanobrowser × chat.deepseek.com × GBT 能力桥 · 接线手册

> 2026-10-04 主人令：用开源 Nanobrowser 当驱动外壳，接 chat.deepseek.com（免费原生网页）
> 与 GBT小土豆V8 全部能力（经触手双向绑定 + run_task 唯一门），实现稳定输出。
> 分工一句话：**Nanobrowser=浏览器上的手（开页/粘贴/点复制），DeepSeek=决策嘴（免费），
> 桥 watch=执行手（run_task 唯一门），剪贴板=两者之间的传送带。**

## 一、三层架构

```
┌─ Nanobrowser 扩展（_upstream/nanobrowser/dist，MV3 v0.2.0）─────┐
│  · 它自己的 agent 脑 = GBT 本地模型链（OpenAI 型 provider →      │
│    http://127.0.0.1:31417/v1，agnes_proxy，免鉴权本地端点）      │
│  · 稳定 DOM 动作：开页面 / 填输入框 / 点「复制」按钮 / 粘贴发送   │
└──────────────────────┬───────────────────────────────────────────┘
                       │ 剪贴板（DeepSeek 自带「复制」按钮 → 确定性）
┌──────────────────────▼───────────────────────────────────────────┐
│ deepseek_bridge.py watch --execute（仓根 deepseek_watch.cmd）     │
│  · 解析 ```gbt 指令块 → run_task 唯一门（授权/审计全在门里）       │
│  · 反馈块自动上剪贴板 → Nanobrowser 粘回 DeepSeek 对话 → 闭环      │
└──────────────────────────────────────────────────────────────────┘
```

稳定性的关键：**不解析页面文本、不注入页面脚本**。取 DeepSeek 的回复靠它自带的
「复制」按钮（点击=确定性动作），送回靠输入框粘贴——每一步都是 Nanobrowser 最擅长的
DOM 操作，页面改版也基本不受影响。

## 二、装载 Nanobrowser（一次性，需主人点三下）

1. Chrome/Edge 地址栏开 `chrome://extensions`（或 `edge://extensions`）；
2. 右上开「开发者模式」→ 点「加载已解压的扩展程序」；
3. 选本仓目录：`C:\Users\ADMIN\Desktop\GBT小土豆V8\_upstream\nanobrowser\dist`。

（源已按 Apache-2.0 克隆于 `_upstream/nanobrowser`，pnpm install+build 已在本机完成，产物即 dist/。）

## 三、把 Nanobrowser 的脑接到 GBT 模型链

扩展图标 → 设置（Options）→ Provider：

| 项 | 值 | 说明 |
|---|---|---|
| Provider 类型 | **OpenAI** | 自定义 baseUrl 的 OpenAI 兼容型 |
| Base URL | `http://127.0.0.1:31417/v1` | 本机 agnes_proxy（密钥链自动路由，本地免鉴权） |
| API Key | 留空 | 本地端点不验钥（Nanobrowser 允许本地模型空钥） |
| 模型 | `agnes-2.5-flash`（或 `agnes-2.5-pro-alpha`） | 思考型会把 max_tokens 烧在 reasoning 上——若回复空壳就换模型 |

纪律：**凭据只走环境变量/密钥服务**。本端点本地免鉴权，不落任何钥值；若日后换成要票的
端点（如 :31716 统一密钥闸），钥值只进 Nanobrowser 的 chrome.storage（不进仓、不进文档）。

## 四、每日循环（执行前先起桥）

1. 双击仓根 **`deepseek_watch.cmd`**（= watch --execute；急停：新建
   `state\deepseek_bridge\PAUSE` 文件即停，删除即恢复）。
2. 点 Nanobrowser 图标开侧栏，给它任务，模板：

   > 打开 https://chat.deepseek.com/ 。在输入框发送以下内容（我已放到剪贴板，直接粘贴），
   > 等 DeepSeek 回答完（确保状态不再是"正在输入"），点它这条回答下方的**复制按钮**，
   > 等 3 秒，再把剪贴板内容原样粘贴进输入框发送。重复上述"发送→等→点复制→等→粘贴发送"
   > 循环，直到 DeepSeek 的回复里出现「任务完成」为止。全程不需要你理解内容，只做搬运。

3. 首次必做：把 `state\deepseek_bridge\tool_manifest.md` 全文先粘给 DeepSeek
   （能力位增减后重新 `py -3.14 tools\codex-scripts\deepseek_bridge.py manifest` 再粘一次）。

## 五、红线（与本桥判据一致，逐条可审计）

- 执行一律过 run_task 唯一门；缺作用域/缺票的回执**原样**回喂，DeepSeek 停下来向主人要票；
- 每轮最多 8 个指令块；rounds.jsonl 全程留痕（`state/deepseek_bridge/rounds.jsonl`）；
- Nanobrowser 只做**搬运**不做决策——决策在 DeepSeek（主人看着），执行在 GBT 门内；
- 涉险名（keylogger 等）由 policy 硬拒；急停闸 PAUSE 一票否决。

## 六、已实测的证据（2026-10-04）

- 桥判据 14/14（封闭）；壳套件 82/82；守卫负对照含 3 条新例全过；
- **真门实弹**：`ledger_note R-H643` 由 gbt 指令块真落盘（`gbt_allinone/docs/待落刀登记.md` 末行）；
  `audit_query` 缺 `audit_read` 票被门拒且回执带 `how_to_grant` 原样回喂；
- **剪贴板全环**：Set-Clipboard → watch 自动执行 health（1 ok）→ 反馈块自动上剪贴板（现读验证）；
- 剪贴板读取口三修：① 句柄竞态 AV→整口兜底；② GlobalSize 谎报 0→阶梯定界读；
  ③ **ctypes 未声明 restype，64 位 GlobalLock 指针被截断**（真根因）→ 全量 restype/argtypes 声明。
