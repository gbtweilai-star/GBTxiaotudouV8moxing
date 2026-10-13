# GBT小土豆V8 × CLIProxyAPI · 统一模型分化路由（说明与口径）

> 主人令 2026-10-04：「借助这玩意把我们自己的大模型以及现有的全部重新使用她做分化和连接」。
> 上游项目：`router-for-me/CLIProxyAPI`（GitHub 54k★）—— 把各家 CLI 账户与自定义 OpenAI 兼容上游
> 统一成 **OpenAI / Gemini / Claude / Codex 兼容的本地端点**。
> 已取至 `_upstream/CLIProxyAPI`（Apache 许可自带），**本机已构建** `CLIProxyAPI.exe`（94MB，Go 1.26.5）。

## 一、它在我们这儿扮演什么

```
触手 / 唯一门 / 统一密钥链
        │  （只认一个 base-url：http://127.0.0.1:8317/v1）
        ▼
  CLIProxyAPI（回环 · 不外露）
        ├── 车道 gbt-potato       ← 自家大模型（云端 Worker 的 OpenAI 兼容面）
        ├── 车道 gbt-free-pool    ← 本机免费池（127.0.0.1:31415，没跑就 disabled）
        ├── 车道 <codex|claude|gemini|grok|kimi|muse|devin>  ← 各 CLI 账户（OAuth 登录后自动出现）
        └── 车道 <任意 OpenAI 兼容上游>（OpenRouter 等，按同一形状加）
```
- **分化**：一条腿 = 一条车道（`name` 独立、`prefix` 可选做点名路由、各自冷却/重试/权重）。
- **连接**：我们这一侧只要认 `127.0.0.1:8317/v1`，就能用全部车道。

## 二、怎么起（本机）

```bash
py -3.14 tools/codex-scripts/cliproxy.py up        # 写配置 + 重启 + 探活 + 列车道
py -3.14 tools/codex-scripts/cliproxy.py status    # 看车道
py -3.14 tools/codex-scripts/cliproxy.py probe     # 真发一轮（默认第一条车道）
py -3.14 tools/codex-scripts/cliproxy.py down      # 停
```
密钥**只从环境变量来**：`GBT_POTATO_BASE_URL`（已在环境里）· `GBT_POTATO_API_KEY` · `GBT_FREE_POOL_KEY`
· `GBT_CLIPROXY_KEY`（本地客户端钥匙，不给就本机随机生成）。生成物只落
`%APPDATA%\gbt-cliproxy\`（`config.yaml` / `client-key.txt` / `cliproxy.log`），**仓库里只有本模板**。

## 三、配置口径（两个实测坑，别再踩）

1. **`openai-compatibility` 的层级是顶层 `api-keys:`**（与 `access:` 平级）。
   写成 `upstream.api-keys.*` ⇒ 服务日志报 `0 OpenAI-compat`、车道恒空（它对未知字段**静默忽略**，
   不看日志发现不了）。
2. **自定义上游必须显式列 `models`**（路由器不替你猜模型名）。

## 四、往车道里加东西

- **加自己的 OpenAI 兼容上游**：照 `config.gbt.example.yaml` 再抄一段。
- **加 CLI 账户**（Codex / Claude / Gemini / Antigravity / Grok / Kimi / Muse / Devin）：
  跑一次登录，凭证落 `_upstream/CLIProxyAPI/auths/`，重启即多出对应车道：
  ```bash
  cd _upstream/CLIProxyAPI
  ./CLIProxyAPI.exe -codex-login      # 或 -claude-login / -antigravity-login / -devin-login …
  ```
  （登录是主人的事：会弹浏览器/设备码，AI 不代跑。）

## 五、现状（2026-10-04 实测，如实）

| 环节 | 读数 |
|---|---|
| 构建 | ✅ `CLIProxyAPI.exe` 94MB（go1.26.5） |
| 服务 | ✅ 回环 8317，`/v1/models` HTTP 200 |
| 自家车道 | ✅ 注册成功（日志 `1 OpenAI-compat`）· 车道列表含 `gbt-potato-v8` |
| 真发一轮 | ⛔ **HTTP 401**：云端 Worker 要 `GW_AUTH`（本机只有 `GBT_ENDPOINT_TOKEN`；`GW_AUTH` 是 Cloudflare 只写密钥，读不回来）⇒ **待主人侧补** |
| 免费池车道 | `disabled: true`（31415 没在跑，不编「活着」） |
| CLI 车道 | 未加（需主人跑一次 OAuth 登录） |

## 六、与框架的关系（下一步，未做不吹）

- 目前是**独立可跑的本地服务 + 本仓工具**（`tools/codex-scripts/cliproxy.py`），框架侧还**没有**把它登记成
  `key_gateway` 的一条链 —— 那一步（把 8317 作为统一密钥链的一条候选、并把各车道名映射成模型别名）
  等主人定「哪些车道要进链」后再动，避免先把没凭证的车道挂进链里空转。
