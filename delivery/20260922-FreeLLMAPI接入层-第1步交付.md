# FreeLLMAPI 接入层 · 第 1 步交付（客户端）

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

- 日期：2026-09-22
- 交付物：`gbt_allinone/llm/freellmapi.py`（307 行，纯 stdlib，零新依赖）
- 上一步设计：`delivery/20260922-她·变压器·密钥AI·本体操控·官方独立接口-设计.md`

---

## 一、这步做完了什么

| 能力 | 函数 | 接口（读对方源码取证） | 实测 |
|---|---|---|---|
| 端口自动发现 | `discover_base_url()` | 读桌面版 `config.json` | ✔ 找到 `127.0.0.1:31415` |
| 探活 | `probe()` | `GET /api/ping`（`app.ts:226`，**明确无鉴权**） | ✔ `up:true` |
| 静态文档 | `docs_available()` | `GET /v1/openapi.json`（`app.ts:230-234`，无鉴权） | ✔ 30,027 B |
| 登录 | `login(email, pwd)` | `POST /api/auth/login` | ✔ 缺参被拒 |
| 供应商清单 | `providers(token)` | `GET /api/keys/providers`（`keys.ts:178`） | ✔ 无 token 报 401 |
| 已配密钥 | `list_keys(token)` | `GET /api/keys/`（`keys.ts:218`） | ✔ 401 |
| 加密钥 | `add_key(token, platform, key, label)` | `POST /api/keys/`（`keys.ts:481`） | ✔ 401 |
| 健康检查 | `health_check(token, key_id)` | `POST /api/health/check/:keyId`（`health.ts:61`） | 未测（需 token） |
| 统一 key | `unified_key(token)` | `GET /api/settings/api-key`（`settings.ts:229`） | ✔ 401（**返回值打码**） |
| 列模型 | `models(unified)` | `GET /v1/models` | ✔ 无 key 报 401 |
| 接入框架 | `framework_env(unified)` | **只算不写盘** | ✔ |
| 总表 | `status_report(token)` | 组合 | ✔ 无 token 时如实说"只探到服务在" |

---

## 二、实测中发现并改掉的三个错（都是我的）

### 错 1 · 端口写死 3001 —— **错的**
- 我照 README 默认值写死 `http://localhost:3001`。
- 实测：探活失败。查进程发现**桌面版早就在跑**（4 个进程，9/21 14:08 启动，
  日志 09/22 14:32 还在写健康检查），而它监听的是 **`127.0.0.1:31415`**。
- 真凭据：`%APPDATA%\FreeLLMAPI\config.json` = `{"port": 31415, "locale": "zh-CN"}`。
- 修法：改成**三级发现** —— 环境变量 → 桌面版 `config.json` → 默认 3001；
  且 `base_url()` 每次现算，端口换了能跟上。

### 错 2 · 差点用源码起服务，会**解不开你已有的 11 把 key**
- `~/freellmapi/server` 有 `start: node dist/index.js`，但 **`dist` 不存在**（没构建）。
  若从源码起，加密钥用的 `.encryption-key` 未必与
  `%APPDATA%\FreeLLMAPI\.encryption-key` 一致 ⇒ 11 把已配密钥可能全解不开。
- ⇒ 决定：**用你已装的桌面版起**（数据目录与密钥天然一致）。
  实测我 `Start-Process` 时它已有单实例锁，**没有拉起重复实例**（进程仍是 9/21 那 4 个）。

### 错 3 · 错误话术混了半截 JSON
- 原来把对方错误体截 300 字直接甩出来，实测尾巴是 `Authentication requ"` 这种断口。
- 修法：解析 `{"error":{"message":...}}` 抽干净话术。现在四个接口一致输出
  `HTTP 401 （需要 dashboard 登录：/api/* 走 requireAuth） Authentication required`。
- 另修：`list_keys` / `unified_key` 原来漏了 `status` 字段，现已补齐（四个接口口径一致）。

---

## 三、两条线（已实测确认，不是推理）

```
① 吃免费算力：/v1/*       只要统一 key，不需登录   ← requireAuth.ts:6-7 注释明写
   实测：/v1/models 无 key -> HTTP 401（要统一 key，但不要会话）✔
   实测：/v1/openapi.json 无 key -> HTTP 200 ✔

② 配密钥：/api/*          需要 dashboard 会话       ← app.ts:212 requireAuth
   实测：providers / keys / settings 无 token 一律 HTTP 401 ✔
```

**我绝不从 SQLite 掏 session token 绕过登录。** 要配置就登录一次，走官方 `/api/auth/login`。

---

## 四、诚实的边界

1. **带 token 的路径没实测**：`providers / list_keys / add_key / health_check / unified_key`
   目前只验证到"无 token 正确报 401"。要真跑通，需要**你的 dashboard 账号密码**
   （或你在窗口里现场输入）。**我没有、也不会去找你的密码。**
2. **`health_check` / `set_enabled` / `remove_key` 一次都没跑过** —— 未测就是未测。
3. **`setup-dsh` 这个命令在本机 v0.3.0 里不存在**：README 提到它，但
   `freellmapi --help` 只列到 `setup-generic`。属版本差，如实记下。
4. 作者三条限制照原样保留：**not production / 受各家服务条款约束 / 无前沿模型无 SLA**。

---

## 五、下一步（按依赖顺序）

1. ~~`freellmapi.py` 客户端~~ ← **本步完成**
2. `gbt_allinone/llm/official.py` —— 官方独立连接口（L1），与免费池 L2 分层
3. 密钥自动配置 AI：**盘**（providers）→ **认**（试探各家 /models 定归属）→ **配**（add_key + 必须过健康检查）
4. 密钥自动配置**窗口**（落在她的面板里）
5. 变压器（压缩 + 快速输出，带前后两个数）
6. 本体总线 `body_bus`
