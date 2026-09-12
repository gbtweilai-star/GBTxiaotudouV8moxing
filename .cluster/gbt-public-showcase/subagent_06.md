# Subagent 06 · 旗舰页面病历单 — platform_v92.html

> 排查对象：`C:\Users\ADMIN\Desktop\GBT小土豆\web\platform_v92.html`（459,879 字节 / 5750 行）
> 性质：只读排查，未修改任何文件。所有行号、锚点均对应当前文件原样。
> 用途：供主线直接做字符串替换补丁。**所有"原文字符串"均为文件内精确子串。**

---

## 〇、结论速览

1. **可见区 UI emoji（含 HTML 实体形式）约 120 处**。真正需要"必除"的界面骨架 emoji 集中在：头部状态徽章（●×4+JS 同步）、Swap 按钮（⇄）、Agent 名（🎯💰🔫）、定时器图标（⚡📊🔔📈🤖）、告警铃铛（🔔×2 JS）、保险产品（🛡️×3）、信号灯（🟢🟡🔴）、验证状态（✅⏳✓）、评分星（★×14）。**🔫 L1031 无论保留策略如何一律必除**。
2. **品牌口径共 4 处硬伤**：title（L8）、logo-sub `Control Center v48`（L573，版本号还停留在 v48 与 v92 不符）、侧栏 `CIS v42 Online`（L648）、桌面通知标题（L4444）。页面整体为英文口径（42 面板标题均为英文），按任务定义全站英文属于"内部口径"，但一次性汉化 42 面板风险大，病历中仅列出门面级锚点。
3. **head 缺 favicon 与 meta description**，插入锚点已给出（L7 之后）。
4. **费率/红线保护项 30 处**，其中 3 行（L961、L1662、L1952）同时含 ⚠️emoji 和费率文案——补丁时只许动 emoji 字符本身。
5. **CSS 现状**：box-shadow 16、backdrop-filter 4（全为模态浮层）、infinite 动画仅 1（wlShine 流光）、gradient-text 类 0（但 L477 有 background-clip:text 渐变数字）、linear-gradient 57、radial-gradient 1、@keyframes 4、text-shadow 0。工具页基调克制，无大面积光污染。

---

## 一、可见区 UI emoji 全量清单

区域划分说明：
- **A 区** = HTML 骨架（L561–2197）
- **B 区** = HTML 骨架（L2274–4262，位于第 1、2 个 `<script>` 之间的静态 HTML）
- **C 区** = JS 运行时注入的界面骨架文本（L4404–5689 内若干）
- **D 区** = JS 日志/toast 内容型（建议保留或仅统一风格，非骨架）

### A 区（L561–2197）

| # | 行 | 字符 | 出现次数 | 精确上下文（原文锚点，含前后文） | 区域 | 建议 |
|---|-----|------|---------|----------------------------------|------|------|
| A1 | 664 | ● | 1 | `<span class="pill pill-green">● CIS Online</span>` | 头部状态徽章 | 换 CSS 圆点（span.status-dot 已有现成样式）或纯文字 |
| A2 | 665 | ● | 1 | `<span class="pill pill-cyan">● Wallet Online</span>` | 头部状态徽章 | 同上 |
| A3 | 666 | ● | 1 | `style="background:rgba(179,136,255,0.15);color:var(--purple)">● 3 Agents</span>` | 头部状态徽章 | 同上 |
| A4 | 668 | ● | 1 | `rgba(255,182,72,.3)">● 连接中</div>`（id="feed-state"，JS setFeed 会覆写） | 头部状态徽章 | 同上，且必须与 C 区 setFeed 三处同步改 |
| A5 | 816 | ⇄ | 1 | `<button class="swap-btn" onclick="swapTokens()">⇄</button>` | DEX Swap 换向按钮 | 换 SVG 双向箭头线性图标 |
| A6 | 961 | ⚠️ | 1 | `color:#ff8a80">⚠&#65039; Collections to these addresses incur a <strong>10% platform fee</strong> on settlement.</div>` | 财库地址警示条 | ⚠️ 换 SVG 三角警示；**严禁动句中 10% 字样** |
| A7 | 995 | 🎯 | 1 | `<div class="agent-name">🎯 BTC Trend Hunter</div>` | Agent 卡片名 | 删 emoji 或换 SVG 趋势图标 |
| A8 | 1013 | 💰 | 1 | `<div class="agent-name">💰 ETH Arbitrage Bot</div>` | Agent 卡片名 | 删或换 SVG |
| A9 | 1031 | 🔫 | 1 | `<div class="agent-name">🔫 Altcoin Sniper</div>` | Agent 卡片名 | **必除**（暴力意象，品牌风险最高优先级） |
| A10 | 1056 | → | 1 | `<span class="log-m ok">ETH Arb Bot: Detected 0.18% spread Binance→OKX</span>` | 运行日志（静态示例） | 内容型，可保留（与 JS 日志风格一致） |
| A11 | 1076 | ⚡ | 1 | `<div class="timer-icon timer-icon-running">⚡</div>` | Task Scheduler 图标 | 换 SVG 线性图标（Signal Scanner） |
| A12 | 1085 | 📊 | 1 | `<div class="timer-icon timer-icon-running">📊</div>` | Task Scheduler 图标 | 换 SVG（Portfolio Rebalance） |
| A13 | 1094 | 🔔 | 1 | `<div class="timer-icon timer-icon-running">🔔</div>` | Task Scheduler 图标 | 换 SVG（Price Alerts） |
| A14 | 1103 | 📈 | 1 | `<div class="timer-icon timer-icon-idle">📈</div>` | Task Scheduler 图标（idle 态） | 换 SVG（Performance Report） |
| A15 | 1112 | 🤖 | 1 | `<div class="timer-icon timer-icon-running">🤖</div>` | Task Scheduler 图标 | 换 SVG（Agent Health Check） |
| A16 | 1202 | ● | 1 | `<div class="metric-value green">● Connected</div>` | WebSocket 状态值 | 换 CSS 圆点 |
| A17 | 1254 | → | 1 | `<div style="color:#00e676">BUY · 100 USDT → 0.0013 BTC</div>` | 成交记录方向符 | 数据型，可保留 |
| A18 | 1578 | ● | 1 | `<div class="metric-value green">● Active</div>` | 状态值 | 换 CSS 圆点 |
| A19 | 1584,1585,1589,1590,1594,1595,1599 | → | 7 | `<div style="font-size:11px;color:#5a6a7a">Binance → OKX</div>`、`$78,234 → $78,562` 等 | 套利路径方向 | 数据型，可保留（金融惯例） |
| A20 | 1632,1633 | → | 2 | `5 min ago · Binance → OKX`、`12 min ago · OKX → Bybit` | 套利轨迹 | 同上 |
| A21 | 1662 | ⚠️ | 1 | `color:#ff8a80">⚠&#65039; Platform policy: all fiat conversions (USD/EUR/GBP) and payouts are charged a <strong>10% fee</strong>. Crypto-to-crypto applies a <strong>1.5% platform fee</strong> (plus route fee).</div>` | 汇率计算器警示 | ⚠️ 换 SVG；**10%、1.5% 严禁动** |
| A22 | 1952 | ⚠️ | 1 | `color:#ff8a80">⚠&#65039; Payout policy: proceeds from sales are credited after a <strong>10% platform collection fee</strong>.</div>` | 卖币警示 | 同 A6 |
| A23 | 2051 | ⚠ | 1 | `<span style="color:#ffd740;font-weight:700">⚠</span> Scam rate industry-wide ~0.02% on escrow platforms — still stay vigilant` | P2P 防诈提示 | ⚠ 换 SVG |

### B 区（L2274–4262，两个 script 之间的静态 HTML）

| # | 行 | 字符 | 次数 | 精确上下文 | 区域 | 建议 |
|---|-----|------|-----|-----------|------|------|
| B1 | 2395 | ✓ | 1 | `color:var(--green)">✓ Recommended · Target Sharpe: 1.85</div>` | 投组方法推荐标记 | ✓ 换 SVG 勾或去符号留文字 |
| B2 | 2768,2771,2774,2777 | ✓ | 4 | `<span style="color:#00e676">✓ Bullish</span>`（EMA/MACD/RSI/Bollinger 四行） | 技术指标状态 | 同上 |
| B3 | 2783 | ⚠ | 1 | `<span style="color:#ff5252">⚠ Overbought</span>` | 技术指标状态 | 换 SVG |
| B4 | 2838 | 🟢 | 1 | `margin-bottom:4px">🟢 Bullish Signal</div>` | 信号卡标题 | 换 CSS 色点（已有色彩编码，emoji 冗余） |
| B5 | 2842 | 🟡 | 1 | `margin-bottom:4px">🟡 Watch Zone</div>` | 信号卡标题 | 同上 |
| B6 | 2846 | 🔴 | 1 | `margin-bottom:4px">🔴 Risk Alert</div>` | 信号卡标题 | 同上 |
| B7 | 3768 | ↑ | 1 | `<span style="color:#00e676;font-weight:600">↑ Rising</span>` | 7d 趋势 | 数据型，可保留 |
| B8 | 3790,3795,3805 | ↑ | 3 | `<div style="font-size:10px;color:#00e676">↑ Bullish</div>` / `↑ Very Bullish` | 币种趋势标签 | 数据型，可保留 |
| B9 | 3800 | → | 1 | `<div style="font-size:10px;color:#ffd740">→ Neutral</div>` | 币种趋势标签 | 数据型，可保留 |
| B10 | 4085–4089 | → + ✓/⏳/🔄 | 5+5 | `<span>ETH → Polygon</span>…<span style="color:#00e676;font-size:11px">✓ Completed</span>`、`⏳ Pending`、`🔄 Processing` | OTC 近期转账 | → 保留；✓⏳🔄 换统一状态徽章 |
| B11 | 4111 | 🛡️ | 1 | `<div><strong>🛡️ Smart Contract Guard</strong>` | 保险产品名 | 换 SVG 盾牌（🛡+VS16 两字符，注意） |
| B12 | 4118 | 🛡️ | 1 | `<div><strong>🛡️ Liquidity Pool Protection</strong>` | 保险产品名 | 同上 |
| B13 | 4125 | 🛡️ | 1 | `<div><strong>🛡️ Bridge Risk Cover</strong>` | 保险产品名 | 同上 |
| B14 | 4135,4136,4138,4139 | ✅ | 4 | `<span style="color:#00e676;font-size:11px">✅ Verified</span>` | 保险商验证 | 换 SVG 勾 |
| B15 | 4137,4176 | ⏳ | 2 | `<span style="color:#ffd740;font-size:11px">⏳ Pending</span>` | 验证/对冲状态 | 换 SVG 时钟 |
| B16 | 4140 | ⚠️ | 1 | `<span style="color:#5a6a7a;font-size:11px">⚠️ Limited</span>` | 保险商状态 | 换 SVG |
| B17 | 4162,4169,4183 | ✓ | 3 | `<span style="color:#00e676;font-size:11px">✓ Active</span>` | 对冲策略状态 | 换 SVG 勾 |

### C 区（JS 运行时注入的界面骨架——补丁时与 A 区同步）

| # | 行 | 字符 | 次数 | 精确锚点 | 说明 | 建议 |
|---|-----|------|-----|---------|------|------|
| C1 | 4404 | 🔔 | 1 | `var b=document.createElement('button');b.id='alert-bell';b.textContent='🔔 告警 0';` | 告警铃铛初始文案 | 换 SVG 铃铛 + 文字"告警 0" |
| C2 | 4424 | 🔔 | 1 | `if(bell){bell.textContent='🔔 告警 '+ALERT_HUB.ring.length;}` | 铃铛计数刷新 | 与 C1 同步 |
| C3 | 4482 | ● | 1 | `if(st==='online'){el.textContent='● 行情在线';` | feed 状态在线 | 换 CSS 圆点方案时同步 |
| C4 | 4483 | ● | 1 | `else if(st==='down'){el.textContent='● 行情断连';` | feed 断连 | 同上 |
| C5 | 4484 | ● | 1 | `else{el.textContent='● 连接中';` | feed 连接中（与 A4 初始值呼应） | 同上 |
| C6 | 5214 | ● | 1 | `bar.innerHTML='<span class="pm-sel-t">● '+m.title+'</span>'` | Polymarket 已选市场条 | 同上 |
| C7 | 5664 | ✔ | 1 | `wlLog('✔ 授权签署 '+wlState.authId+' · 地址 '+wlState.address.slice(0,10)+'…','#00e676');` | 授权日志 | 日志内容型，可保留 |
| C8 | 5689 | ⚠ | 1 | `wlLog('⚠ 资金冻结: '+wlState.freezeReason+' · AI 收割已停摆 · 充值/桥接/出入金暂停','#ff5252');` | 冻结告警日志（红线文案） | 字符可换，**冻结文案本身绝不能动** |

### D 区（JS 日志/toast 内容型——建议保留，不做骨架处理）

- L4658 `toast('Executing arbitrage: '+sym+' '+from+'→'+to+'…` — 方向符
- L4861 `o.from+' → '+o.to` — AI 订单行方向
- L4865 `Settle → ` — 结算方向
- L4883 `rate locked @ '+order.rate+' ('+order.from+'→'+order.to+')'`
- L4889 `settling '+order.netTxt+' '+order.to+' → '+aiAddrFor(...)`
- L4929 `order submitted · '+o.from+' '+o.amtTxt+' → '+o.to+' via '`
- L5338 `USDC.e → Polymarket`、L5342 `pmLog('✓ 链上充值已广播…`、L5345 `pmLog('✗ 真金充值失败…`、L5349 `pmLog('⚠ pm_live 为 DRY-RUN…`
- L4482–4484 同行内其余为状态色逻辑

### HTML 实体形式符号（渲染后等同可见符号，与 emoji 同类处理）

| 字符 | 实体 | 次数 | 行号 | 用途 | 建议 |
|------|------|-----|------|------|------|
| ★ | `&#9733;` | 14 | 1911(×5), 1919(×4+1☆), 1927(×5) | 交易对手评分 | 可保留（评级语义）或换 SVG 星 |
| ➔ | `&#10132;` | 13 | 1706, 1740, 1744, 1748, 1752, 1756, 1760, 1970, 1994, 1998, 2002, 2006, 2010 | 主按钮"Execute/Post Offer ➔" | 换 SVG 箭头或删除 |
| → | `&#8594;` | 10 | 867(×2), 895, 1847(×4), 1858(×3) | 卡片副标题/流程说明 | 可保留 |
| ● | `&#9679;` | 8 | 907, 1835, 1855, 1856, 1857, 1858, 1859, 1860 | 状态点/要点列表 | 骨架，换 CSS 圆点 |
| ✓ | `&#10003;` | 7 | 853, 1714, 2046, 2047, 2048, 2049, 2050 | 链条节点/安全要点 | 换 SVG 勾 |
| ⚠ | `&#9888;` | 3 | 890, 5509, 5538 | 安全线/冻结按钮/冻结横幅 | 换 SVG（5509/5538 是红线 UI，只换符号） |
| ↦ | `&#8614;` | 2 | 841, 867 | 桥节点图标 | 换 SVG |
| ▲ | `&#9650;` | 2 | 849, 903 | 链条/收割节点图标 | 换 SVG |
| ◆ | `&#9670;` | 1 | 837 | Treasury 节点图标 | 换 SVG |
| □ | `&#9633;` | 1 | 845 | PM wallet 节点图标 | 换 SVG |
| ⚑ | `&#9873;` | 1 | 888 | 地址pill旗标 | 换 SVG |
| ⧉ | `&#10697;` | 1 | 888 | 复制图标 | 换 SVG |
| ▶ | `&#9654;` | 1 | 917 | 市场卡图标 | 换 SVG |
| ☰ | `&#9776;` | 1 | 922 | 账本卡图标 | 换 SVG |
| ⇄ | `&#8644;` | 1 | 1674 | BestChange 换向大图标（22px） | 换 SVG 双向箭头 |
| ⚡ | `&#9889;` | 1 | 1718 | 汇率卡图标 | 换 SVG |
| ✕ | `&#10005;` | 3 | 5440, 5521, 5523 | 模态关闭按钮 | 换 SVG 叉 |
| ☆ | `&#9734;` | 1 | 1919 | 半星评分 | 随 ★ 处理 |

---

## 二、品牌口径问题（品牌口径：GBT小土豆量化收益平台）

| # | 行 | 原文精确锚点 | 问题 | 建议 |
|---|-----|-------------|------|------|
| 1 | 8 | `<title>GBT AI Control Center v92 · AI Automation</title>` | 英文内部口径 + 版本号 v92 露出 | 改 `<title>GBT小土豆量化收益平台</title>` |
| 2 | 571 | `<div class="logo-text"><span>GBT</span> AI</div>` | "GBT AI" 英文口径（GBT 字样本身是品牌，可留） | 最小改法：`<span>GBT</span> 小土豆`；logo-icon 的 "G"（L570）可保留 |
| 3 | 573 | `<div class="logo-sub">Control Center v48</div>` | "Control Center" + **过期版本号 v48**（实际 v92，口径不一致） | 改 `量化收益平台` 或删除版本号 |
| 4 | 648 | `<div class="status-row"><div class="status-dot"></div><span>CIS v42 Online</span></div>` | v42 版本号露出且又是一个版本 | 改 `CIS 引擎在线` |
| 5 | 659 | `<p id="h-sub">Real-time monitoring · AI Automation · Smart decisions</p>` | 页面头部英文副标题 | 改中文，如 `实时监控 · AI 自动化 · 智能决策` |
| 6 | 691 | `<div class="card-subtitle">Quant harvesting system</div>`（所在行首为 `<div class="card-header"><div><div class="card-title">CIS Engine</div>`） | 英文内部口径（收割系统） | 可改 `量化收割系统`（注意：仅文案，不涉逻辑） |
| 7 | 4444 | `new Notification('GBT AI Control Center',{body:msg});` | 桌面通知标题仍是英文旧口径 | 改 `'GBT小土豆量化收益平台'` |
| 8 | 1164 | `<div class="chat-header-info"><h3>GBT AI Assistant</h3><p>Quant trading advisor · Real-time analysis</p></div>` | AI 助手英文口径（产品名，低优先级） | 可保留或改 `GBT AI 助手` |
| 9 | 4338 | `const titles={overview:'Dashboard',trading:'CIS Trading',…}` | 42 面板英文标题映射（约 45 个键值对，单行超长） | 门面级可只改首屏 Dashboard；全量汉化建议另行任务，避免单行大改引发回滚困难 |
| 10 | 1172 | `<div class="msg msg-ai">Hello! I am GBT AI assistant specializing in quant trading and market analysis. How can I help you today?</div>` | AI 初始问候英文 | 可保留（AI 人设文本属内容型）或改中文 |

**版本号散布（注释口径，不渲染，无品牌风险但列作参考）**：v92（L6,8,10,119,4264,4279,4295,4322,4775,4814,4815,4832,4947,5004）、v48（L412,573,1063）、v42（L648）、v91/v90（L5）、v81（L452,499,834,5435）、v80（L5002,5074,5435,5543）、v79（L4811）。渲染面上只有 L8/L573/L648 三处版本号露出。

---

## 三、head 缺失项与插入锚点

当前 head（L3–L8）结构：
```
<head>
<meta charset="UTF-8">
<!-- v91: ... -->
<!-- v92 加固: ... -->
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GBT AI Control Center v92 · AI Automation</title>
```

缺失：favicon（全文件 0 处）、meta description（0 处）、og:*（0 处）、theme-color（0 处）、apple-touch-icon（0 处）。

**插入锚点**：在 L7 `<meta name="viewport" content="width=device-width, initial-scale=1.0">` 之后、L8 `<title>` 之前插入：

```html
<link rel="icon" type="image/svg+xml" href="/ui/favicon.svg">
<meta name="description" content="GBT小土豆量化收益平台 · AI 量化交易 · 多链资产管理 · 自动化收益">
```

（若追求最小 diff，也可插在 `</title>` 行之后；二选一，不要两处都插。）

---

## 四、红线与费率保护项（主线补丁时**绝不能碰**）

### 费率数字与计算逻辑

| 行 | 精确锚点（关键片段） | 内容 |
|-----|---------------------|------|
| 4815 | `var GBT_FEES={fiat:0.10,crypto:0.015,profit:0.05};` | **费率唯一口径定义**：法币 10% / 币币 1.5% / 收益 5% |
| 4764 | `var PLATFORM_FEE=0.10;` | 平台费变量 |
| 4775 | `var fee=(fiatFx?GBT_FEES.fiat:(GBT_FEES.crypto+(BC_FEES[plat]||0.005)));` | 币币费计算（含 1.5%+通道费） |
| 4947 | 同上（第二处相同表达式） | AI 单费计算 |
| 4783 | `var feeTag=fiatFx?'Platform Fee 10% (Fiat)':'Fee '+feePct+' ('+plat+')';` | 费率标签 |
| 4785 | `document.getElementById('bc-fee').textContent=(fiatFx?'10% Fiat Platform Fee':'Fee '+feePct)+' \u2014 $'+…` | 费率 UI 渲染 |
| 4950, 4965, 4975 | `feePct:(fiatFx?'10%':'fee '+(fee*100).toFixed(1)+'%')` ×3 | 订单费率字段 |
| 4985 | `toast('Offer live on GBT order book @ $'…' — 10% collection fee applies','success');` | 10% 收取费 toast |
| 4986 | `aiLog('Offer posted on GBT order book @ $'…' (10% collection fee)');` | 同上日志 |
| 5120 | `if(fl) fl.textContent='10% fee = $'+feeAmt.toFixed(2);` | 10% 费行 |
| 5276 | `pmLog('CIS exit · '+reason+' · P&L $'…(feeAmt>0?' (10% fee $'+feeAmt.toFixed(2)+')':'')…` | CIS 退出 10% 费 |
| 5319 | `pmLog('CIS scalper ACTIVATED · 10% fee on settlement · '…` | CIS 激活 10% |
| 5393 | `hv.textContent='10% fee · '+(tot>=0?'+':'')+'$'+tot.toFixed(2);` | 账本 10% 行 |

### 费率警示文案（⚠️ emoji 与费率同行的三处——只许动符号！）

| 行 | 精确锚点 |
|-----|---------|
| 961 | `⚠&#65039; Collections to these addresses incur a <strong>10% platform fee</strong> on settlement.` |
| 1662 | `⚠&#65039; Platform policy: all fiat conversions (USD/EUR/GBP) and payouts are charged a <strong>10% fee</strong>. Crypto-to-crypto applies a <strong>1.5% platform fee</strong> (plus route fee).` |
| 1952 | `⚠&#65039; Payout policy: proceeds from sales are credited after a <strong>10% platform collection fee</strong>.` |
| 880 | `id="pm-fee-line">10% fee = $0.10</div>` |
| 854 | `id="pm-chain-hv" style="font-size:11px">10% fee · $0.00</div>` |
| 922 | `every scalp exit recorded &#183; P&amp;L shown net of 10% fee` |
| 1859 | `<strong style="color:#f0f4fc">10% platform fee</strong> — fiat conversions &amp; payouts (policy)` |
| 6 | 注释 `币币技术费统一 1.5%`（口径注释，勿动） |

### 授权协议条款区（整段冻结，含 ⚠/✕ 符号行只换符号不换文案）

| 行 | 内容 |
|-----|------|
| 5476 | `平台受托在已绑定外部钱包授权额度内执行充值/桥接/预测市场买入卖出与结算，费率 10% 于结算时计提。` |
| 5481 | 冻结排查条款摘要 |
| 5490 | 《资金托管、冻结与追回授权协议》入口 |
| 5509 | `&#9888; 冻结资金（排查）` 按钮 |
| 5521–5529 | 协议模态：关闭 ✕、条款 1–5（冻结排查权/无期限追回/10% 平台费/风险披露） |
| 5537–5538 | 冻结横幅（backdrop-filter 行）与 `&#9888; 资金保障状态` |
| 5659 | `授权无效: 三项权限与条款必须全部勾选` |
| 5665 | `权限 ①交易执行 ②异常冻结排查 ③争议追回(无期限) · 条款 '+WL_TERMS_VER` |
| 5689 | 冻结停摆告警（C8 同行） |

### 风控红线数值

| 行 | 精确锚点 |
|-----|---------|
| 1530 | `<div style="font-family:monospace;font-size:18px;font-weight:700;color:#ff5252">-5%</div>`（Daily Loss Limit） |
| 1546 | `>1.5x</div>`（Stop Loss Level ATR 倍数） |
| 4371 | `_dd>=10?'#ff6b6b':(_dd>=5?'#ffb648':'#3ddc97')`（回撤阈值染色逻辑） |
| 5255 | `else if(drift>=0.10) reason='momentum stall / reverse…'` |
| 5284 | `if(stake>=5&&px>0.05&&px<0.95){`（CIS 扫参数） |
| 683 | `id="sl-alert">--</div>`（Stop Level 槽位） |
| 3484 | `安全线 70%</span><span>警戒线 85%` |

### 真实链上数据（勿动）

- L984 `TTML7MEQZh8iwqXZcrnrcRXF4ZL62Ln2B2`（TRON Treasury 地址）
- L842/L867 `0xad07&#8230;388`（Polygon 桥地址）
- L976 `data-settle-addr="ETH">结算地址未配置 · 由管理端注入(localStorage gbt_settle_addr)`（v92 安全机制占位）
- L888 `<code id="pm-addr-code">（结算地址未配置）</code>`

---

## 五、CSS 现状基线（box-shadow / backdrop-filter / infinite / gradient）

| 项目 | 数量 | 主要挂载点 | 评估 |
|------|-----|-----------|------|
| box-shadow | **16** | CSS 15 处 + JS 行内 1 处（L5708 chip）。挂载：L44 `.status-dot` 6px 微光、L117 wcard hover、L422 agent-card hover、L458 pm-node.live 微光、L481 pmFlash 关键帧扩散、L496–498 pm-market-tile hover/sel、L500 **wl-shell 双层大阴影+青色 glow（最重的一处）**、L503 wl-step-ic、L506 wl-dot currentColor、L513 wl-qr-holder、L554 wl-field focus、L5708 告警 chip | 工具页可接受；若收口优先处理 L500 的 60px 彩色 glow |
| backdrop-filter | **4** | L104 `.modal-ov` blur(4px)、L5436 wl-overlay blur(6px)、L5520 wl-terms-modal blur(4px)、L5537 wl-freeze-bar blur(4px) | 全部在模态/浮层，合理保留 |
| infinite 动画 | **1** | L504 `#wl-overlay .wl-step-ic.on::after{…animation:wlShine 2.2s linear infinite}`（授权步骤流光） | 单点、低频，可保留；已受 L122 prefers-reduced-motion 保护 |
| gradient-text 类 | **0** | 无 `.gradient-text` 类 | — |
| background-clip:text（渐变文字） | **2**（同行） | L477 `.pm-bignet`（净入金大数字 #00e676→#7dffb0 渐变） | 唯一渐变文字，若品牌收口可改纯色 |
| linear-gradient | **57** | CSS 27 + 行内 30。集中区：logo/按钮主色（L33,76,515）、卡片背景板（L217,225,229,232,245,414）、pm 链条（L453,456,470,471）、wl 授权壳（L500,503,504）、行情卡/进度条（L2120–2136,2485–2495 等） | 多为低透明度背景板，专业工具页可接受 |
| radial-gradient | **1** | L454 pm-chain-strip 顶部 10% 光晕 | 轻微，可留 |
| @keyframes | 4 | fadeIn(L57)、slideIn(L111)、pmFlash(L481)、wlShine(L505) | 全部 ≤1.4s 短动画 |
| text-shadow | 0 | — | 无 |

---

## 六、风险与注意事项

1. **⚠️/🛡️ 是双字符**（U+26A0/U+1F6E1 + VS16 U+FE0F，文件里写作 `⚠&#65039;` 或 `⚠️`）。字符串替换必须整体匹配，否则残留 VS16 空字符。
2. **A4 与 C3/C4/C5 是同一 UI 的初始值与运行时覆写**，只改 HTML 不改 JS 会在状态刷新后"复活"旧样式；alert-bell（C1/C2）同理。
3. **L961/L1662/L1952 三行 emoji 与费率共存**——建议的补丁方式是只把 `⚠&#65039; ` 子串替换为 SVG/空，绝不能整行重写。
4. **版本号口径混乱**（v92/v91/v90/v81/v80/v79/v48/v42 并存），渲染面只有 L8/L573/L648 三处；L6/L5/L4264 等注释里的版本号不动。
5. **L903 疑似实体编码错乱**：`cis&#24635;&#25142;&#26415;` 解码为 "cis总戶术"，疑似想写 "cis总战术"（&#25142; 应为 &#25112;）。顺带记录，主线可修可不修。
6. **L4338 titles 是单行超长对象**（约 45 个键值对），整行替换回滚成本高；若汉化建议拆成多次小替换（每个 `'Dashboard'` 类键值单独替换）。
7. 品牌名 "GBT" 本身大量出现在**业务文案**中（L941,956,961,1164,1172,1707,1736,2241,4793,4985,4986…），多数是资金池/执行口径说明，属于产品语义而非版本口径，**不要在 emoji/品牌补丁中顺手批量替换**，避免误伤费率与协议语境。
8. 文件为 UTF-8 无 BOM、LF/LF 混合需注意：行尾均为文件原样（本病历未验证 CRLF/LF 差异，主线打补丁前建议按字节精确匹配原文锚点）。
9. genAI()（L4661–4669）AI 回复文本不含 emoji，无需处理；AI Chat 内容型 emoji 本文件实际不存在（此前担心的场景未出现）。

---

> 病历完毕。锚点均为文件内逐字精确子串，可直接用于字符串替换补丁。
> 生成：Subagent 06 · 旗舰页面病历员 · 2026-09-12
