# 官方 Codex 接入方案（待风哥确认后动刀）

> 立场：**方案先行，不动代码**。本文只回答四件事——路径、条件、内存占用、怎么与 gbt_allinone 对接。

## 一、现状（实测，非推测）

| 项 | 实测值 |
| --- | --- |
| 官方 Codex 安装路径 | `C:\Users\ADMIN\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe`（`codex --version` 可调用） |
| 现有桥接模块 | `gbt_allinone/codex_bridge.py`（`CLIENT_VERSION = "8.0.0"`） |
| 启动方式 | `[codex_path, "app-server", "--listen", "stdio://"]`，带 `CODEX_HOME`，`CREATE_NO_WINDOW`，stdio 管道 |
| 可执行体查找顺序 | `%LOCALAPPDATA%\OpenAI\Codex\bin` → `%APPDATA%\npm` → `%USERPROFILE%\.codex\bin`，匹配 `codex.exe` / `codex.cmd` / `codex` |
| **对接形态（关键）** | **旁路**：`holo_pet/panel_server.py` 直接 `import codex_bridge`；`caps_registry.py` / `api.py` 里**没有** codex 能力项 |
| 当前进程内存 | 3 个 codex 进程：**161.9 MB / 97.8 MB / 9.0 MB（合计 ≈269 MB）**；其中 7860 号 **CPU 累计 1087 秒（≈18 分钟）** |

## 二、路径（Path）

| 类别 | 路径 | 用途 |
| --- | --- | --- |
| 可执行体 | `%LOCALAPPDATA%\Programs\OpenAI\Codex\bin\codex.exe` | 官方安装（已存在） |
| 备选体 | `%APPDATA%\npm\node_modules\@openai\codex\...\codex.exe` | npm 全局安装形态 |
| 配置根 | `%USERPROFILE%\.codex\`（`config.toml`、`auth.json`、`sessions/`） | 模型/供应商/凭据/会话 |
| 运行时配置 | `CODEX_HOME` 环境变量 | 桥接层注入，隔离不同宿主 |
| 框架侧 | `gbt_allinone/codex_bridge.py` · `holo_pet/panel_server.py` · `gbt_allinone/store/`（审计与状态） | 现有对接面 |

**约定**：不硬编码绝对路径；一律走 `_EXE_CANDIDATES` 顺序 + 环境变量覆盖（`GBT_CODEX_PATH`）。

## 三、条件（Condition）

| # | 条件 | 现状 | 方案 |
| --- | --- | --- | --- |
| 1 | 可执行体存在且可调用 | ✅ 已满足 | 启动前探测，缺失时如实报 `needs_dependency` |
| 2 | 版本兼容（app-server 协议） | ✅ 0.154.0 | 启动握手校验，记录 `server_info.userAgent` |
| 3 | 凭据（`auth.json` / 登录态） | ✅ 已登录 | 只读探测；不复制、不落日志、不打印 |
| 4 | 运行配置（模型/供应商，如 `openai-compat` → `127.0.0.1:4446`） | ✅ 已配置 | 桥接不改用户配置；变更走主人授权 |
| 5 | 沙箱模式（`read-only` / `workspace-write` / 越权拒绝） | 配置为 `unelevated` | 桥接显式声明并在审计留痕 |
| 6 | 外网（模型通道） | ✅ 通过本地代理 | 外网失败时如实报，不静默降级 |
| 7 | 并发上限 | ❗**当前无限制**（实测 3 进程并存） | **方案要求：单实例复用 + 并发上限 1~2** |

## 四、内存占用（实测 + 方案约束）

```
实测（本机，2026-09-15）：codex 主进程 161.9 MB · 次进程 97.8 MB · 轻进程 9.0 MB ≈ 269 MB
其中主进程 CPU 累计 1087 秒 → 存在"长驻 + 空转"的浪费
```

**方案约束（写入宪章"宿主第一"口径）**：

1. **单实例共享**：复用一条 app-server（`get_shared_server()` 已有此设计），禁止每次对话重启；
2. **空闲回收**：空闲 > 10 分钟主动 `stop()`，释放 260+ MB；
3. **并发上限**：同时活跃 turn ≤ 1（队列化）；
4. **内存闸**：宿主可用内存低于阈值（如 < 20%）时拒绝新启动，只允许复用；
5. **可观测**：把 codex 进程数/内存/CPU 纳入 `sensory_state` 或独立探针，面板可见。

## 五、与 gbt_allinone 的对接方式（三档递进）

### 档位 A · 现状（旁路）

```
holo_pet/panel_server.py ── import ──▶ gbt_allinone/codex_bridge.py ── stdio ──▶ codex app-server
```
**问题**：不经过 `api.run_task()` → 无统一策略、无统一审计、无契约信封。

### 档位 B（推荐，本方案主张）· 注册为正式能力

```
任何调用方 ── run_task("codex_*") ──▶ api.py（策略/授权/审计/契约信封）──▶ codex_bridge ──▶ app-server
```

**新增能力项（走 caps_registry 注册）**：

| 能力 | 作用 | 风险级 |
| --- | --- | --- |
| `codex_status` | 只读状态（进程/版本/会话/内存） | 只读 |
| `codex_thread_new` | 新建线程 | 低 |
| `codex_turn_send` | 发送 turn（流式事件回传） | 中 |
| `codex_interrupt` | 中断当前 turn | 低 |
| `codex_tools` | 动态工具清单（`gbt_*`） | 只读 |

**统一治理**：这些能力必须经过 `policy.authorize`（写操作走 `process_execute` 作用域，与今日已注册的作用域对齐）+ 审计（`store.audit`）+ 统一契约信封（`{ok,kind,result,error}`）。

### 档位 C（可选，后续）· 双向工具面

把 `gbt_*` 动态工具（capability / mirror / preflight / nexus / tentacle / browser / mind / life）
通过 app-server 暴露给 Codex 侧，形成"框架↔Codex 双向可调用"，并对每次工具调用留审计痕迹。

## 六、风险与对策

| 风险 | 对策 |
| --- | --- |
| 空壳/假执行（外部 LLM 通病） | 按宪章第九章：代码必跑、产物必查、结果必证、响应体优先、双环境对照、证据链闭合 |
| 长驻空转吃宿主 | 第四节的 5 条内存约束（空闲回收 + 并发上限 + 内存闸） |
| 旁路绕开策略 | 档位 B：全部走 `api.run_task()`，禁止再直连 `codex_bridge` |
| 凭据泄露 | 只读探测，不复制 `auth.json`，不打印 token（宪章凭据纪律） |
| 版本漂移导致协议不兼容 | 启动握手校验 + 状态探针纳入体检 |

## 七、验证方式（落地后按此验收）

```
1) 能力注册：run_task("codex_status") 返回 {ok:true, result:{version, sessions, memory}}
2) 策略生效：未授权调用 codex_turn_send → denied（不是静默执行）
3) 审计留痕：store.audit 中出现 codex_* 事件（不含提示词全文与密钥）
4) 内存约束：空闲 10 分钟后进程数回落、内存下降；并发>1 被拒
5) 契约信封：成功/拒绝/异常三条分支均返回 {ok,kind,result,error}
6) 面板联动：holo_pet 侧改走 run_task 后，对话与时间线功能不降级
```

## 八、需要风哥拍板的三件事

1. **是否采用档位 B**（注册为正式能力、全部走统一入口）？
2. **内存约束取值**：空闲回收阈值（10 分钟？）、并发上限（1 还是 2）？
3. **是否同时做档位 C**（双向工具面），还是先 A→B 稳定后再谈？

---

> 本方案**只写不做**。你确认后，我按"镜像先验 → 生产落地 → 报账"执行，一步一验证。
