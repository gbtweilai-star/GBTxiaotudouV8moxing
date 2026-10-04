# pm_live — Polymarket 真金执行层

把平台 v77–v79「UI 桥接 + 模拟放行」的 Polymarket 环节替换为**真金链路**的独立后端模块:
真实 L2 钱包私钥签名 + Polymarket CLOB API 凭证下单, Polygon 链上 USDC.e 充值/提现。
UI(platform_v*.html)后续通过本地 API(127.0.0.1:8096)接线, 本模块不依赖浏览器。

## 模块

| 文件 | 职责 |
|---|---|
| `config.py` | .env 读取 / 准入判断 / 链上常量(USDC.e、CTF Exchange、Polygon RPC) |
| `gamma.py` | 公开行情: 关键词找市场、取 clobTokenIds/conditionId/negRisk、盘口校价 |
| `clob.py` | py-clob-client 封装: 本地 EIP-712 签名(不发网)、post_order、cancel、余额 |
| `chain.py` | 链上真金: approve / CTF deposit / NegRiskAdapter deposit / withdraw(JSON-RPC 裸交易) |
| `engine.py` | 编排 + 干跑优先 + 双闸放行 + 审计(~/.gbt/pm_live_audit.jsonl, 可 PM_AUDIT_FILE 覆盖) |
| `api.py` | FastAPI :8096, 供平台 UI 接线 |
| `cli.py` | 命令行入口 |
| `.env` | 凭证(自建, 参照 .env.example; 不提交 git) |

## 真金三层防线

1. **默认干跑**: PM_DRY_RUN=1(默认) → 所有命令只本地签名、打印摘要、落审计, 不广播。
2. **显式放行**: 干跑关掉(PM_DRY_RUN=0)后, CLOB 下单仍需 `--live` / API live=true; 链上充值/提现仍需 `--yes`。
3. **广播前自检**: `doctor` 验证凭证/地址/连通性 + 链上合约代码存在 + USDC.e symbol/decimals; 下单前自动用真实盘口校价(偏离 >5% 拦截)。

审计默认写 `~/.gbt/pm_live_audit.jsonl`(项目 gatekeeper 白名单区), 用 `PM_AUDIT_FILE` 可改路径。

## 启用步骤(真金)

```powershell
cd C:\Users\ADMIN\Desktop\GBT小土豆
# 1) 凭证(绝不在聊天贴私钥):
#    polymarket.com 个人页 Settings -> API Keys 生成(用你的 L2 钱包签名), 把三项 + L2 私钥填入 pm_live\.env
C:\Python312\python.exe -m pip install py-clob-client eth-account fastapi uvicorn pydantic

# 2) 自检(无凭证也先跑, 验证行情/交易主机连通)
C:\Python312\python.exe -m pm_live.cli doctor

# 3) 熟悉市场与盘口(全真实数据)
C:\Python312\python.exe -m pm_live.cli search "bitcoin up"
C:\Python312\python.exe -m pm_live.cli book <token_id>

# 4) 干跑下单(本地签名, 看订单指纹/签名, 不上链)
C:\Python312\python.exe -m pm_live.cli order "bitcoin up" BUY 5 0.55

# 5) 真金(确认钱包有 USDC.e → 小额开始):
#    a. 关干跑: 编辑 pm_live\.env 设 PM_DRY_RUN=0
#    b. 链上充值 100 USDC.e(自动 approve + deposit)
C:\Python312\python.exe -m pm_live.cli deposit 100 --yes
#    c. 查 CLOB 到账
C:\Python312\python.exe -m pm_live.cli balance
#    d. 真实下单
C:\Python312\python.exe -m pm_live.cli order <token_id> BUY 10 0.55 --live
#    e. 撤单 / 提现
C:\Python312\python.exe -m pm_live.cli cancel <order_id>
C:\Python312\python.exe -m pm_live.cli withdraw 20 --yes
```

## UI 接线(platform_v7X.html 待无并发时改)

v79 面板 `pmBridgeDeposit()` / `pmToggleAI()` 的模拟体, 替换为 fetch 本模块(或直接放 AI 引擎 SETTLE 步):
```js
// 下单: 返回 {ok, data:{status:'DRY-RUN'|'LIVE-SUBMITTED', ...}}
fetch('http://127.0.0.1:8096/api/pm/order', {method:'POST', headers:{'Content-Type':'application/json'},
  body: JSON.stringify({q: tokenId, side:'BUY', size: usdcQty, price: price, live: true})})
// 面板只读: /api/pm/balance · /api/pm/search?q= · /api/pm/book?token_id=
// 状态灯:  /api/pm/health -> {mode:'LIVE'|'DRY-RUN', creds, l2}
```
服务端启动(可加入 start_gbt_services.ps1 端口监听防重):
```powershell
Start-Process C:\Python312\python.exe -ArgumentList '-m','pm_live.api','--port','8096' -WorkingDirectory 'C:\Users\ADMIN\Desktop\GBT小土豆' -WindowStyle Hidden
```

## 审计

`~/.gbt/pm_live_audit.jsonl` 记录每次动作(ts/action/params/ok/note), 私钥与签名永不入档;
干跑与真金均留痕, 订单指纹(hash_struct)/交易哈希可链上追溯。

## 合规与风险(必读)

- Polymarket 对部分地区(含美国)用户受限; 是否可交易由你自行确认合规。
- 真金前务必小额验证: 先充值 10–20 USDC.e → 下一张最小单 → 撤单/结算流程跑通再放大。
- CTF Exchange / NegRiskAdapter 地址以 `doctor` 链上自检为准; 新市场若 adapter 未知, 先人工核对条件 ID。
- 本模块不参与 BestChange 兑换/收款钱包等其它平台环节。
