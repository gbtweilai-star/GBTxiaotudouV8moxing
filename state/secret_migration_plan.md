# 明文令牌迁移清单（主人 2026-10-04 点名「2」：列哪把该迁到哪）

> 背景：体检发现 **HKCU\Environment 里明文存着多把令牌**。本文件只给**去向与命令**，
> **不含任何令牌值**（打印一律只留前 4 字符掩码）。执行需要主人在终端发一次票（铸钥/落盘要 `filesystem_write`）。
> 口径：凭据进 **DPAPI 保险箱**（`store/secrets/<profile>.dpapi`，读写都过 `deepseek_key`），
> 环境变量只留**引用名**（`env:<名>` / `vault:<profile>`），不存值。

## 零、已就位（本端口已做，主人无需操心）

- **四档保险箱 profile 已登记**：`deepseek_key._PROFILES` 新增 `potato / custom / imap / gateway`
  （文件 `*_api.dpapi`、取值变量指向对应 `GBT_*`、形状 = 非空白 8–256 字符）。
  实测：假值通过、含空格值被拒 ⇒ 形状不松不紧。**没有这步，下面命令会报「未知保险箱 profile」。**
- **未执行任何写操作**（落箱 / 删环境变量都要主人的票或会话标记）。

## 一、谁在读（改错地方会断链，这列是实测 grep 结果）

| 环境变量 | 本仓读者 | 有没有人读 |
|---|---|---|
| `GBT_POTATO_API_KEY` | `llm/key_gateway.py` · `llm/cloud_llm.py` · `tools/console_pages.py` · `tools/gods_eye.py` | ✅ 4 处 |
| `GBT_LLM_API_KEY` | `llm/freellmapi.py` · `llm/cloud_llm.py` · `llm/key_gateway.py` · `security/abl_gateway.py` | ✅ 4 处 |
| `GBT_GATEWAY_TOKEN` | `tools/capability_gateway.py` | ✅ 1 处 |
| `GBT_IMAP_PASS` | `tools/codex-scripts/mail-bind.py` · `verify-brain-objective.py` | ✅ 2 处 |
| `GBT_JWT_TOKEN` | —— | ❌ 零读者 |
| `GBT_ADMIN_TOKEN` | —— | ❌ 零读者 |
| `GBT_SMTP_PASS` | —— | ❌ 零读者 |
| `GBT_FORWARDEMAIL_TOKEN` | —— | ❌ 零读者 |

非密钥类（**不用迁**，留着即可）：`GBT_POTATO_BASE_URL` · `GBT_POTATO_MODEL` · `GBT_SMTP_HOST/PORT/USER/FROM` · `GBT_IMAP_USER` · `GBT_LLM_PROVIDER`。

## 二、迁移表（每把去哪、怎么落）

| # | 令牌 | 去向（保险箱 profile） | 迁完谁读得到 | 迁移命令（主人终端，发一次票后） |
|---|---|---|---|---|
| 1 | `GBT_POTATO_API_KEY` | `store/secrets/potato_api.dpapi` + 道表 `potato` 的 `vault="potato"` | key_gateway 现算链（`key_for` → `dpapi:potato`） | 见 §三-A |
| 2 | `GBT_LLM_API_KEY` | `store/secrets/custom_api.dpapi` + 道表 `custom` 的 `vault="custom"` | 同上（custom 道） | 见 §三-A（profile 换 `custom`） |
| 3 | `GBT_GATEWAY_TOKEN` | `automation_keys` 槽位（`browser` 或新建 `gateway` 槽）→ `vault:gateway`（文件 `gateway_api.dpapi`） | `capability_gateway.py` 改读门内引用 | 见 §三-B |
| 4 | `GBT_IMAP_PASS` | `store/secrets/imap_api.dpapi`，两个脚本改读 `deepseek_key.load_key("imap")` | mail-bind / verify-brain-objective | 见 §三-C |
| 5-8 | `GBT_JWT_TOKEN` / `GBT_ADMIN_TOKEN` / `GBT_SMTP_PASS` / `GBT_FORWARDEMAIL_TOKEN` | **无读者 ⇒ 不进箱**：先**轮换**（在各自平台作废旧值）再**从环境移除** | —— | 见 §三-D |

## 三、命令（全部在**主人自己的** PowerShell；本端口不代跑写操作）

### A. 模型钥进 DPAPI 箱（第 1、2 把）
```powershell
$env:GBT_OWNER_SESSION=1     # 本会话标记（不落盘）—— 或先 auth grant --scope filesystem_write --ttl 600
py -3.14 -c "import os,sys; sys.path.insert(0, r'C:\Users\ADMIN\Desktop\GBT小土豆V8'); from gbt_allinone import deepseek_key as d; print(d.store_key(os.environ['GBT_POTATO_API_KEY'], 'potato'))"
# 同一形状换 profile：'custom'（值取 GBT_LLM_API_KEY）
# 迁完把这两把从用户环境移除（值已在 DPAPI）：
#   [Environment]::SetEnvironmentVariable('GBT_POTATO_API_KEY',$null,'User')
#   [Environment]::SetEnvironmentVariable('GBT_LLM_API_KEY',$null,'User')
```
> 道表要同步：`llm/key_gateway.py` 的 `dict(name="potato", vault="")` → `vault="potato"`（custom 同理）。
> 这一步是**代码小改**（一字段），改完 `key_for()` 会优先走 DPAPI，环境变量可退出。

### B. 网关令牌进槽位（第 3 把）
```powershell
$env:GBT_OWNER_SESSION=1
py -3.14 -m gbt_allinone run automation_keys '{"op":"set","slot":"gateway","ref":"vault:gateway"}'
# 再把 capability_gateway.py 的取值改为门内引用（一函数），值进 store/secrets/gateway.dpapi
```

### C. 邮件口令进箱（第 4 把）
```powershell
py -3.14 -c "import os,sys; sys.path.insert(0, r'C:\Users\ADMIN\Desktop\GBT小土豆V8'); from gbt_allinone import deepseek_key as d; print(d.store_key(os.environ['GBT_IMAP_PASS'], 'imap'))"
# 两个脚本把 os.environ['GBT_IMAP_PASS'] 改为 deepseek_key.load_key('imap')（两行）
```

### D. 无读者的四把：轮换 + 移除（第 5–8 把）
```powershell
# ① 先到各自平台作废旧值（JWT/管理令牌/SMTP 授权码/转发令牌）
# ② 从用户环境移除（这是删环境变量，属可逆动作：值仍在这份清单的历史里，可重设）
foreach ($n in 'GBT_JWT_TOKEN','GBT_ADMIN_TOKEN','GBT_SMTP_PASS','GBT_FORWARDEMAIL_TOKEN') {
  [Environment]::SetEnvironmentVariable($n, $null, 'User')
}
```

## 四、回滚

- A/C：值仍在原环境变量里（迁完才移除）⇒ 回滚 = 把道表 `vault` 字段改回 `""`、脚本读法改回 `os.environ[...]`。
- B：`automation_keys op=unset slot=gateway`。
- D：四把的旧值若没作废，可原样重设；**作废后不可逆**（这是它的目的）。

## 五、顺序建议（防断链）

1. 先做 **D**（零读者，无风险）→ 2. 再做 **A/B/C**（有读者：**先落箱、再改读法、最后移除环境变量**，三步之间各跑一次 `llm_status` / 对应脚本确认）。

> 本清单由 zcode 端口 2026-10-04 产出；**未执行任何写操作**（写操作要主人票）。执行完请把结果回一行，我更新台账。
