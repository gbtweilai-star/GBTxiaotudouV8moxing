# 用户端功能盘点 · 落实清单（只读排查）

> 盘点员：用户端功能盘点员（subagent 08）
> 范围：`web/` 下 index.html / wallet_v2.html / exchange.html / messages.html / terms.html（主）+ payment.html / digital_asset.html（辅助）
> 方法：逐页提取 onclick/fetch/XHR/表单 action，对照真实后端路由清单 + 本地端口探活 + 真实 POST/GET 实测
> 结论：**大量「设而不实」**。静态页基本落实；钱包/兑换/消息/支付 4 页存在明显的演示桩、死接口、纯摆设。

---

## 〇、后端真实路由实测基线（探活结果）

| 端口 | 服务文件 | 状态 | 说明 |
|---|---|---|---|
| 8097 | gbt_wallet/api.py（钱包主服务，`/ui` 挂载前端） | ✅ 运行中 | 五页同源部署入口 |
| 8094 | crypto_exchange_gateway.py（兑换网关） | ✅ 运行中 | 兑换页真接口所在 |
| 8081 | payment_gateway.py（支付网关） | ✅ 运行中 | payment.html 接口所在 |
| 18900 | gbt_cap_bridge.py（cap 桥） | ✅ 运行中 | digital_asset.html 接口所在 |
| 8093 | wallet_service.py（旧钱包） | ✅ 运行中 | 旧版 wallet.html 用，非五页 |
| 8888 | api_gateway.py | ❌ 未运行 | — |

### 8097 钱包路由实测
- ✅ 正常：`health` `monitor` `invoices` `balances` `receipts` `receipts/summary` `receipts/export` `orders` `settlements` `events` `social/support` `social/dm` `social/channel` `social/unread` `eigenflux/net`
- ❌ `/api/gbtwallet/invoice`（POST）→ **500**：钱包未初始化（`~/.gbt/gbt_wallet/` 无 keystore.json，`monitor` 返回 `"initialized":false`），`next_receive_address→_mnemonic` 抛 `SystemExit("钱包未初始化")`
- ✅ `/api/gbtwallet/scan`（POST）→ 200 "无待收发票, 跳过扫描"
- ❌ `/api/gbtwallet/settlements/summary`（GET）→ **404**：`api.py` 第 257-259 行 `settle_summary()` **缺少 `@app.get` 装饰器**（后端 bug）

### 8094 兑换网关路由实测
`auth/connect` `stats` `exchange/fiat-to-usdt` `address/generate` `addresses` `invoice/create` `invoices` `exchange/history` **全部真实可用**（已实测 POST 成功返回）。

### 8081 支付网关路由实测
`health` `payment/list` `payment/create` `payment/{id}` 存在；**无 `/api/payment/status`**。

### 18900 cap 桥路由实测
`/api/cap/wallet_bridge/connect` `/bridge` `/token_swap/swap` `/crypto_pay/create_invoice` **全部真实可用**（已实测成功）。

---

## 一、逐页盘点

### 1. index.html（门户）—— 已落实 ✅
- 纯静态，无任何 fetch/JS 交互。
- 所有链接有效：`wallet_v2` `exchange` `messages` `terms` `site_a/b/c` 均存在。
- 注：`og:url` 指向 `https://wallet-api.gbtxiaotudou.com/ui/index.html`（生产域名，与本地 8097 不同，属上线配置，非缺陷）。

### 2. wallet_v2.html（钱包，核心页）—— 收款链路「设而不实」⚠️❌
| 功能 | 状态 | 证据（行号+锚点） | 落实建议 |
|---|---|---|---|
| 服务状态加载 | ✅ 真接口 | L373-375 `fetch("/api/gbtwallet/monitor")` | 无需改 |
| **收款地址生成（核心）** | ❌ **演示桩/纯摆设** | L393-411 `recvBtn` 只调 `rid()`(L360)/`ridAddr()`(L361) 生成**随机 TR… 地址**，**从不调用** `/api/gbtwallet/invoice` | 改调 `POST /api/gbtwallet/invoice`，展示返回的 `invoice.address` |
| 收款单号 | ❌ 假数据 | L396 `rid("INV-")` = 前缀+demoDate+随机数 | 用发票返回的 `invoice_id` |
| 二维码 | ✅ 真生成（但编码假地址） | `qr_local.js` 是完整 QR 编码器（GF(256)+Reed-Solomon+矩阵，L405-406 `QRLocal.renderToCanvas`）；L440 `<script src="qr_local.js">` | 编码真实发票地址即可 |
| 我的订单历史 | ⚠️ 本地假数组 | L392 `var hist=[]`；L409 `hist.unshift(...)`；从未调 `/api/gbtwallet/orders` | 接 `GET /api/gbtwallet/orders` |
| 累计订单/已结算/单据数 | ✅ 真（来自 monitor） | L378-382 | 无需改 |
| 币种下拉 | ⚠️ 与后端白名单部分吻合 | L300 `USDT/USDC`；后端 config.py 白名单 `USDC.E/USDC/USDT/WETH` | 未调用，不阻塞 |
| 演示声明 | ❌ 明示是假 | L328 `当前为演示数据，仅供界面预览`；L354 `demoDate:"2026-09-11"` | 落实后删除 |

**核心结论**：钱包页只有「状态概览」是真接口，**「生成收款地址 → 二维码 → 订单历史」整条收款主链路全部是写死的演示桩**，与后端已就绪的 `invoice/orders` 端点脱节。

### 3. exchange.html（兑换）—— 全部接口指向 8094，同源部署下全成死接口 ❌
| 功能 | 状态 | 证据（行号+锚点） | 落实建议 |
|---|---|---|---|
| API 基址 | ❌ 错位 | L420 `var API = (file: ? "http://127.0.0.1:8094" : "")`。页面经 8097 `/ui` 部署时 `API=""` → 请求发到 8097 | 改指向 8094 或网关反向代理 |
| 钱包连接 | ⚠️ 假 SDK + 假地址 | L443-444 无 `window.tronLink/ethereum`（实测 0 引用），注释"模拟连接（生产环境接真实钱包 SDK）"；随机生成 T… 地址 | 接真实 TronLink/MetaMask 或至少删掉假连接 |
| 法币→USDT 兑换 | ⚠️ 后端真但部署后死接口 | L510 `fetch("/api/exchange/fiat-to-usdt")`；8094 实测成功，但 8097 下 404 → 落 L529-541 演示分支 | 修正 API 基址 |
| 演示汇率 | ❌ 过期假数据 | L531 `{USD:6.48, CNY:1, EUR:7.02, THB:0.19}`，与网关 L40 真实 `{USD:7.2,CNY:1.0,EUR:8.5,THB:0.021}` 不符 | 删除演示分支，信任后端 |
| **结算收款地址 xSettle** | ❌ **纯摆设** | L316 输入框存在，但 JS **0 处读取** `$("xSettle")` | 下单 body 增加 `settle_address` 并落库 |
| 生成收款地址 | ⚠️ 后端真但部署后死 | L548 `fetch("/api/address/generate")` | 同 API 基址 |
| 创建发票 | ⚠️ 后端真但部署后死 | L584 `fetch("/api/invoice/create")` → 演示 `inv_demo_`(L596) | 同 API 基址 |
| 订单历史/统计/地址/发票列表 | ⚠️ 后端真但部署后死 | L494/L568/L602/L616 | 同 API 基址 |
| **使用说明 helpModal** | ❌ **纯摆设** | L402 模态框存在，但**无任何按钮/入口** `classList.add('on')`（实测 0 触发点） | 补一个打开按钮或删除 |

### 4. messages.html（消息中心）—— 仅客服 AI 真，其余全是假 ❌
| 功能 | 状态 | 证据（行号+锚点） | 落实建议 |
|---|---|---|---|
| AI 客服 | ✅ 真接口 | L284-285 `fetch("/api/gbtwallet/social/support")`；已实测返回真实 AI 回复（Agnes） | 无需改 |
| **会话/群组/频道列表** | ❌ 写死 mock | L176-187 `dms/groups/channels` 三个硬编码数组（Alice/Bob/GRP-quant/VIP/公告） | 接 `GET /social/dm` + `/social/channel` |
| 历史消息 | ❌ 写死 | L222-235 `loadMessages()` 全是硬编码演示文案，从不 fetch | 接 `GET /social/dm?a=&b=` |
| 群组/私信发送 | ❌ 假回显 | L291-295 `setTimeout` 假回显（"收到 👍"），未调 `/social/send`（后端存在） | 接 `POST /social/send` |
| **搜索框** | ❌ **纯摆设** | L133 `<div class="search">` 只有图标+文字，**无 `<input>`、无事件** | 补输入框或删除 |
| **附件按钮 attachBtn** | ❌ 演示桩 | L328-331 点附件反而注入假红包 `addTipMsg(5,"USDT","请你喝咖啡")` | 接真实附件/转账，或改文案 |
| 红包「领取」 | ❌ 假 | L265-267 点击仅替换按钮文字，无后端 | 接红包/转账接口 |
| emoji 面板 | ✅ 真（本地数组） | L168-172, L299-322 | 无需改 |

### 5. terms.html（条款）—— 已落实 ✅
纯静态法务文案，无 JS，链接有效。无缺陷。

### 6. payment.html（辅助·支付）—— 死接口 + 参数错配 + 乱码 ❌
| 功能 | 状态 | 证据（行号+锚点） | 落实建议 |
|---|---|---|---|
| 创建订单 | ❌ 参数错配 | L272-275 `fetch('/api/payment/create', JSON body)`；8081 网关签名是 **query 参数** `create_payment(amount:float,currency:str)` → 422；8097 下更直接 404 | 对齐网关参数/响应契约 |
| **查询支付状态** | ❌ **死接口** | L342 `fetch('/api/payment/status?id=')`；网关只有 `/api/payment/{id}`，无 `/status` → 404 | 改 `GET /api/payment/{id}` |
| 订单列表 | ⚠️ 契约不符→总是假数据 | L359 `/api/payment/list`；网关返回 `{data,total}`（无 `ok` 字段），页面 `if(data.ok)`(L361) 恒假 → 落 L363 `getDemoOrders()`(L387-393) | 对齐响应契约 |
| 支付方式 card/bank/alipay | ⚠️ 纯 UI 选中态 | L187-201 按钮仅切换 `.active`，无任何差异化逻辑 | 明确未接通或隐藏 |
| 收款地址 | ❌ 写死假地址 | L218/L288 硬编码 `TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t` | 用真实派生地址 |
| **去钱包按钮 goToWallet** | ❌ 死链 | L355 `window.location.href='/wallet/'`；8097 挂载是 `/ui/`，`/wallet/` 404 | 改 `/ui/wallet_v2.html` |
| **文案乱码** | ❌ 双编码乱码 | L319 `宸茶繃鏈?`、L334 `宸插鍒?`、L346 `鏀粯鎴愬姛`、L370/381/416-425 等大量乱码字符串 | 修复为正确中文 |

### 7. digital_asset.html（辅助·数字资产）—— 接口真但报价/QR 是演示桩 ⚠️
| 功能 | 状态 | 证据（行号+锚点） | 落实建议 |
|---|---|---|---|
| 连接钱包/跨链桥/兑换/开票 | ✅ 真接口 | L260 `API_BASE='http://127.0.0.1:18900'`；L293/L319/L362/L383 分别调 wallet_bridge/bridge/token_swap/crypto_pay，已实测全通 | 无需改 |
| **swap 报价** | ❌ 演示桩 | L348-354 硬编码价 `{ETH:3500,BTC:67000...}` + `Math.random()` 算 Gas；token_swap 有 `do_quote` 未用 | 接 `token_swap/quote` |
| **二维码** | ❌ 假渲染 | L394 把 `qr_data`（=地址字符串）字符映射成 `█`/空格块，非真 QR | 接 qr_local.js 或后端真 QR 图 |
| 顶部导航 | ⚠️ 死链（相对本服务） | L93-95 `/v9_ultimate` `/payment` `/wallet` 属旧平台 `_routes.json` 路由，非 8097 `/ui` | 改 `/ui/...` |

---

## 二、落实清单总表

| 页面 | 功能 | 当前状态 | 证据(行号) | 落实建议 |
|---|---|---|---|---|
| index | 门户+链接 | 已落实 | 全静态 | — |
| wallet_v2 | 状态概览 | 已落实 | L373-375 | — |
| wallet_v2 | **生成收款地址** | **演示桩** | L393-411(ridAddr L361) | 接 `POST /api/gbtwallet/invoice` |
| wallet_v2 | 二维码 | 真生成(编码假地址) | qr_local.js / L406 | 编码真实发票地址 |
| wallet_v2 | 订单历史 | 假数组 | L392/L409 | 接 `GET /api/gbtwallet/orders` |
| exchange | 钱包连接 | 演示桩 | L443-444(无 SDK) | 接真实 SDK |
| exchange | 法币兑换 | 后端真·部署后死接口 | L510/L531 | 修正 API 基址(8094) |
| exchange | **结算地址 xSettle** | **纯摆设** | L316(0 读取) | 下单携带 settle_address |
| exchange | 生成地址/开票/历史 | 后端真·部署后死接口 | L548/L584/L602/L616 | 修正 API 基址 |
| exchange | **helpModal** | **纯摆设** | L402(无打开入口) | 补入口或删除 |
| messages | AI 客服 | 已落实 | L284-285 | — |
| messages | 会话/群组/频道列表 | 写死 mock | L176-187 | 接 `/social/dm` `/social/channel` |
| messages | 历史消息 | 写死 | L222-235 | 接 `/social/dm` |
| messages | 群组/私信发送 | 假回显 | L291-295 | 接 `POST /social/send` |
| messages | **搜索框** | **纯摆设** | L133(无 input) | 补输入或删除 |
| messages | **附件按钮** | **演示桩** | L328-331(注入假红包) | 接真实附件 |
| terms | 条款 | 已落实 | 全静态 | — |
| payment | 创建订单 | 参数错配 | L272-275(JSON vs query) | 对齐 8081 契约 |
| payment | **查询状态** | **死接口** | L342(`/payment/status` 不存在) | 改 `/payment/{id}` |
| payment | 订单列表 | 恒落假数据 | L359-363/L387-393 | 对齐 `ok` 契约 |
| payment | **goToWallet** | **死链** | L355(`/wallet/`) | 改 `/ui/wallet_v2.html` |
| payment | 收款地址 | 写死假地址 | L218/L288 | 用真实派生地址 |
| payment | 中文文案 | 乱码 | L319/L334/L346/L370/381/416-425 | 修复编码 |
| digital_asset | 连接/桥/兑换/开票 | 已落实 | L293/L319/L362/L383 | — |
| digital_asset | swap 报价 | 演示桩 | L348-354 | 接 `token_swap/quote` |
| digital_asset | 二维码 | 假渲染 | L394 | 接真 QR |

---

## 三、后端侧缺陷（与页面无关，但需同步修）

1. **`settlements/summary` 缺路由装饰器**（api.py L257-259）：`settle_summary()` 函数体存在，但未挂 `@app.get("/api/gbtwallet/settlements/summary")` → 404。
2. **钱包未初始化**：`~/.gbt/gbt_wallet/` 只有 `ledger.jsonl` 和 `social_messages.json`，**无 keystore.json**，导致 `POST /api/gbtwallet/invoice` 500、`scan` 空转。收款/开票链路要落实，须先 `init` 钱包（生成助记词密钥库）。
3. **payment_gateway.py 契约**：`create_payment` 用 query 参数而非 Pydantic body，且无 `/status` 别名端点，与 payment.html 前端契约不一致。

---

## 四、优先级建议（供主控决策）

- **P0（核心链路假）**：wallet_v2 的「收款地址生成」是随机假地址，这是用户点「所有设定好要落实」最核心的一环 → 接 `/api/gbtwallet/invoice`（前提：先初始化钱包密钥库）。
- **P1（同源部署致全线死接口）**：exchange.html 的 API 基址在 8097 `/ui` 部署下全部失效 → 改指 8094 或做网关反代。
- **P1（死接口/死链）**：payment 的 `/api/payment/status`、`/wallet/` 死链、`settlements/summary` 404。
- **P2（纯摆设）**：messages 搜索框、exchange 的 xSettle 与 helpModal、payment 的乱码。
- **P2（演示桩）**：messages 会话列表/发送、digital_asset 报价与 QR、exchange 演示汇率。

> 本报告为只读排查结论，未修改任何被盘工件。所有行号以盘点时工作区文件为准。
