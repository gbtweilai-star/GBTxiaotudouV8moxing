# 远端独有产物 · 抢救留档（2026-09-22）

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

## 为什么会有这个目录

推送干净分块时列远端 refs，发现一个分支 `prod-hardening-no-cap-changes`，
它有 **3 个文件在 main 里没有、本机也一个都没有**。

按「不破坏既有产物」+「先看再动手」，我**没有删那个分支**，
而是先把 3 个文件从远端**逐字节**取回落在这里留档。

## 来源（可复核）

| 项 | 值 |
|---|---|
| 仓库 | `paysssk-creator/GBT-V8`（私有） |
| 分支 | `prod-hardening-no-cap-changes` |
| 分支 tip | `f40e03add293e52cb66151b681d1a94efbdd7246` |
| 相对 main | `diverged` · ahead 3 · behind 9 |
| 取法 | `git show <branch>:<path>`（走 git 协议，**不走 API**） |

## 三个文件

| 文件 | 大小 | 远端 blob sha | 本地 sha256 |
|---|---:|---|---|
| `CAPABILITIES.md` | 8,850 B | `10a28b613a29779ac0245f746e3a1ba80a0dada3` | `a4282b4bacdb079a6b664d4458295a0815b9b5eeb0cae01530aa9c7d10a695bc` |
| `preflight_check.py` | 2,808 B | `90110807b1fd40094cbd5911fa4711aa3c65f8d2` | `887372f1b78adab22c09bc4c5b8cf412d3bcc09eebefe1680b5c12c545614e86` |
| `readiness.py` | 4,892 B | `abc87074bde98259fb1beba8473c3a32f2e13cb8` | `56023fec56016631cb77c74f00e3ed7cec3d05184c94030ae737624f1ce71425` |

远端原路径：
- `gbt_allinone/CAPABILITIES.md`
- `gbt_allinone/deploy/preflight_check.py`
- `gbt_allinone/readiness.py`

## 内容是什么（读过，不是猜的）

- **`readiness.py`** —— 依赖就绪自检。开头写着「立场（Owner 定调）：这是纯 AI 框架 + 全 AI
  能力体系。本模块**绝不删除、绝不禁用**任何能力」，对 vision / voice / browser / sec_llm /
  llm_chat 五个能力逐个探测外部后端与密钥，缺了就**如实报 `needs_dependency`**，
  而不是在生产里静默失败。**与我们「反假执行」的纪律完全一致。**
- **`preflight_check.py`** —— 进生产预检三件：① BOM 扫描（可选 `--fix`）② `compileall`
  全量编译校验 ③ 调 `readiness.check()`。退出码 0/1/2 语义明确。
- **`CAPABILITIES.md`** —— 自称「框架能力的**权威索引**」，按域组织，对应
  `caps_registry.py` 真实注册项，经 `api.py` 路由。署名行齐全。

## 判定：这是**我们自己的东西**，不是外人塞进来的

证据：
1. 三个文件都带我们的署名「开发者：自由的风 · 本署名不可删除、不可篡改归属」。
2. 通篇引用我们的内部件：`caps_registry.py`、`api.py`、`run_task`、`store/audit.jsonl`、`SOUL`。
3. 全部 11 个远端分支**都含我们的 `AGENTS.md`** ⇒ 都是我们框架的分叉。
4. 仓库**协作者只有 `paysssk-creator` 一个**（admin），没有第二个人有写权限。
5. 提交署名串是「金欧锦Disrupt traditional paradigms」，该提交**未关联任何 GitHub 账号**
   （API 的 `author.login` 为空）；本机 git 身份**改过**
   （现 local/global `user.name=paysssk-creator`，local `user.email=lopaycn@gmail.com`）。
   ⇒ 极可能只是**你以前用过的另一个署名**。

**所以我不断言"这是外人"。** 只列事实，判断权在你。

## 本机对照

- 本机 `gbt_allinone/` 有 `preflight.py`（38,633 B，另一个更大的模块），
  **没有 `readiness.py`** ⇒ 这 3 个文件是**尚未并入本机的独有产物**。
- 因此**绝不能删那个分支**，否则就真丢了。

## 要不要并入本机

**我没有自动并入**——往 `gbt_allinone/` 加文件属于改框架，得你点头。
你说并，我就按原路径放回去并跑一次 `preflight_check.py` 验收；
你说不并，这份留档就放着，随时可取。

## 怎么自己复核

```powershell
cd C:\Users\ADMIN\Desktop\GBT小土豆V8
# 远端再取一次对比
git -C .shadow-repo show probe/prod-hardening-no-cap-changes:gbt_allinone/readiness.py > $env:TEMP\r.py
(Get-FileHash $env:TEMP\r.py -Algorithm SHA256).Hash.ToLower()
# 应等于 56023fec56016631cb77c74f00e3ed7cec3d05184c94030ae737624f1ce71425
```
