# subagent_07 · 对抗复查报告（gbt-public-showcase）

- 复查员：对抗复查员（只读，未修改源项目任何文件；源项目仅读，写入均在 V8 工作区临时目录）
- 日期：2026-09-12（GMT+7）
- 对象：`C:\Users\ADMIN\Desktop\GBT小土豆`（web/ 收敛 + platform_v92.html 旗舰收口两轮作业）
- 方法：Python 3.12 只读遍历 + curl.exe 公网探测 + node --check 语法验证

---

## 逐项 PASS/FAIL 总表

| # | 检查项 | 判定 |
|---|--------|------|
| ① | 搬运完整性（57/153） | **FAIL**（web/=58，deploy_bak 未搬走） |
| ② | 公网面回归（18 页 + 3 资产全 200） | **PASS** |
| ③ | 归档面隔离（5 项全 404） | **FAIL**（deploy_bak 公网 200） |
| ④ | 11+7 公开页本地引用完整性 | **FAIL**（payment.html 3 死链；其余 17 页 OK） |
| ⑤ | 旗舰页补丁质量 | **FAIL**（可见区 emoji 残留 28；品牌/favicon/meta/费率/🔫 全部到位） |
| ⑥ | platform_v92 JS 语法完整 | **FAIL（SEV-1）**（块1 语法破坏，全页交互逻辑不执行，线上即坏版） |
| ⑦ | 全站红线词抽查 | **多页命中（如实报告）**（详见下表；兑换商/订单簿/场外全站 0） |

---

## ① 搬运完整性 — FAIL

- `web/` 递归实测 **58** 文件（预期 57）。根级 38 + `autoclaw-tools/` 子树 20。
- 多出文件：**`web\platform_v92.html.deploy_bak`**（459,879 字节，MD5 `76f5025fc152d80cd77c7d1f0231ce83`）。
- 佐证：`web_archive\backups\platform_v92.html.deploy_bak` 亦存在但内容**不同**（452,143 字节，MD5 `6564a2dc…`）——即归档的是早先版本，web/ 里这份更新过的备份没搬。
- `web_archive/` 递归实测 **153** ✓（history 80 / backups 25 / internal 48）。
- 抽查 8 个已搬文件（platform_v91.html、v84_report.html、gbt_hero_v2.jpeg、site_c.html.deploy_bak、gbt_quant_platform_v40_cis_harvester.html、exchange.html.deploy_bak、index.html.bak_2026-09-090058、platform_v84.backup_2026-09-082306.html）：全部"web/ 不存在 ✓、web_archive/ 存在 ✓"。
- 除此之外，按 basename 全量比对 153 个归档文件，只有 deploy_bak 这一个仍留在 web/。
- MANIFEST 类：源项目根有 `.project.manifest`（v5.1，生成于 2026-08-23），早于本次搬运且不含 web_archive 记录；按任务口径不计 FAIL，如实备案。

## ② 公网面回归 — PASS

`https://wallet-api.gbtxiaotudou.com/ui/` 下 21 项全部 **200**：

- 18 页面：index / wallet_v2 / exchange / messages / terms / site_a / site_b / site_c / platform_v92 / payment / digital_asset / wallet / monitor / health / caps_panel / gbt-chat / ai-browser / temp_mail（.html）
- 3 资产：favicon.svg / qr_local.js / gbt_hero_facade.jpeg

## ③ 归档面隔离 — FAIL

| 路径 | 状态 |
|------|------|
| /ui/platform_v91.html | 404 ✓ |
| **/ui/platform_v92.html.deploy_bak** | **200 ✗** |
| /ui/v84_report.html | 404 ✓ |
| /ui/gbt_hero_v2.jpeg | 404 ✓ |
| /ui/gbt_quant_platform_v40_cis_harvester.html | 404 ✓ |

deploy_bak 公网可达且**承载旧品牌口径**：其 `<title>GBT AI Control Center v92 · AI Automation</title>`、无 favicon、无 meta description——正是本轮收口要清除的旧口径，现原样暴露在公网。

## ④ 公开页本地引用完整性 — FAIL（1/18 页）

- 逐页抽取 href/src 的本地 .html/.js/.jpeg/.svg/.png 并对 web/ 解析：17 页全部 OK（含 gbt-invoice-qr.png 运行时豁免）。
- **payment.html：3 个死链**
  - `href="/docs/pricing.html"` → 本地无、线上 404
  - `href="/wallet/"` → 线上 404
  - `href="/"` → 线上 404（根路径本身 404，返回首页死链）
  - 位置：页内 nav（GBK 解码为"费率/钱包/返回"三项）。属站内绝对路径，非本轮搬运造成的断链（web/ 内本无 /docs/），但公开页存在 3 个点击即 404 的链接。

## ⑤ 旗舰页补丁质量 — FAIL（子项多数 PASS，emoji 未清零）

通过项：
- title：`GBT小土豆量化收益平台 · AI 量化控制台`，**v92 字样已消失** ✓
- favicon：`<link rel="icon" type="image/svg+xml" href="/ui/favicon.svg">` ✓
- meta description：`GBT小土豆量化收益平台 · AI 量化交易 · 多链资产管理 · 自动化收益` ✓
- logo-sub：`量化收益平台`；h-sub：`实时监控 · AI 自动化 · 智能决策` ✓
- 桌面通知品牌：`new Notification('GBT小土豆量化收益平台',{body:msg})` ✓
- **🔫 零残留**：全文件计数 0 ✓；VS16(U+FE0F) 全文件 0（费率行剥 VS16 已执行）✓
- 费率保护项全部在位：
  - `GBT_FEES={fiat:0.10,crypto:0.015,profit:0.05}`（定义 1 处 + 引用 6 处）✓
  - `10% platform fee` ×2、`1.5% platform fee` ×1 ✓
  - TRON 地址 `TTML7MEQZh8iwqXZcrnrcRXF4ZL62Ln2B2` ×1 ✓
  - 协议条款"费率 10% 于结算时计提" ×1 ✓

未通过项：
- **可见区（剔除 `<style>` 后）emoji 计数 = 28，非 0**：
  - ✓ U+2713 ×16（15 处可见 HTML："✓ Bullish"×5、"✓ Recommended · Target Sharpe: 1.85" 等 + 1 处 script）
  - ⚠ U+26A0 ×8（6 处可见 HTML + 2 处 script；其中 5 处在费率/政策提示行，按"费率行仅剥 VS16"口径可视为豁免，扣后仍有 ⚠ Overbought、⚠ Limited 2 处非豁免）
  - ⏳ U+23F3 ×2（可见 HTML："⏳ Pending"×2）
  - ✗ U+2717 ×1（script）、✔ U+2714 ×1（script）
  - 扣除费率行豁免 ⚠×5 后仍余 23 个。均为装饰性 dingbat/符号（非 🔫 类武器或敏感 emoji），严重度低，但按"清零"验收口径不达标。
  - 另：● U+25CF ×10 为信号灯替换产物（普通几何符号，非 emoji），符合"信号灯全换"预期，不计入。

## ⑥ platform_v92.html JS 语法完整 — FAIL（SEV-1，最高优先级）

- 4 个 `<script>` 块，逐块 `node --check`：
  - 块0（4,754 ch）OK
  - **块1（28,533 ch / 475 行）FAIL**：`SyntaxError: Unexpected end of input`；`new Function()` 报 `Missing catch or finally after try`
  - 块2（40,191 ch）OK
  - 块3（11,592 ch）OK
- **根因定位**：块1 第 7 行 `try{`（端点覆盖逻辑）永远等不到 catch。第 17–23 行插入的"v92 加固增强块"（escAi 转义函数 + 导航键盘可达 + 结算地址运行时渲染 + 聊天演示标注）被塞进了这个 try 的内部，原 try 结构的闭合/catch 被撕裂未补。括号深度追踪：最终深度 +1，未闭合的正是 line 7 的 `try{`。
- **对照证据**：
  - `web_archive/history/platform_v91.html`（3 块）全部 node --check OK → 破坏由 v92 轮次引入，非历史遗留。
  - `web/platform_v92.html.deploy_bak` 块1 同样 FAIL（28,546 ch）→ 加固块插入时（收口前轮次）即已破坏，本轮品牌收口在坏版上继续做文案，未发现也未修复。
  - **线上 = 本地逐字节一致**（live 455,630 == local 455,630，无首处分歧）→ 公网当前运行的就是坏版。
- **影响面**：块1 是全页主初始化块——时钟、模拟行情刷新、导航 `show()`、`toast()`、`refreshOverview/refreshTrading/refreshWallet`、通知中心、`escAi` 加固函数本身、DOMContentLoaded 全部逻辑。整块不解析 = 页面静态可见但**所有交互全部失灵**，且后续块2/块3 虽语法完好、运行时也因块1 抛错而无法保证执行顺序（块1 在前，抛 SyntaxError 后同脚本标签内代码不执行；块2/3 是独立标签可执行，但依赖块1 定义的函数/变量会 ReferenceError）。

## ⑦ 全站红线词抽查 — 多页命中（供 Owner 决策）

方法：18 页（11 公开页 + platform_v92 + 其余 6 页）词边界匹配，排除 base64 数据串。

全站 0 命中：**兑换商 / 订单簿 / 场外 / bestchange(公开页) / bisq(公开页)**。

命中明细：

| 页面 | 词 | 计数 | 位置性质 |
|------|-----|------|----------|
| wallet.html | DEX | 5 | **可见区**："DEX 连接中"、"DEX聚合器 · Uniswap/1inch/EnsExchange"、"自动兑换 (DEX Aggregator)"、页脚 "GBT WALLET v2.0 · DECENTRALIZED DEX AGGREGATOR" |
| payment / digital_asset / monitor / health / gbt-chat / ai-browser / temp_mail（各页） | 去中心化 | 各 3 | head 区 SEO 文案（meta description / og:description / twitter:description："GBT小土豆 - 去中心化量化交易平台"、"去中心化、零KYC、AI驱动"）；页面可见区不显示，但源码/搜索引擎可抓取 |
| caps_panel.html | p2p | 8 | 可见按钮标签：`do_p2p_ad_create` / `do_p2p_buy`（crossmint_integration 能力操作按钮） |
| caps_panel.html | 去中心化 | 4 | 3 处 head meta + 1 处可见："去中心化 P2P 推理网络上的自主 Agent(2M+ nodes…)" |
| **platform_v92.html**（内部工具页，公开可达） | bestchange | 9 | 可见 6（导航"BestChange"、"BESTCHANGE AGGREGATOR — DEEP INTEGRATION"注释、两处卡片标题）+ script 3 |
| 同上 | bisq | 37 | 可见 21（导航、p-bisq 面板、bisq-tab-content 等）+ script 16 |
| 同上 | p2p | 54 | 可见 35（导航"No-KYC P2P"、"NO-KYC P2P EXCHANGE — BISQ DEEP INTEGRATION"、"P2P Markets" 等）+ script 19 |
| 同上 | DEX | 7 | 可见 4（导航"DEX Swap"/"DEX Hub"、卡片"DEX Aggregator"、动态行"DEX Swap"）+ style 1 + script 2 |

- platform_v92 的 bisq/p2p 按任务口径属内部操作台业务语义豁免，但该页公网可达，命中数如上，是否清除由 Owner 决策。
- 8 页 head 区"去中心化"meta 属统一模板残留，一次批量替换可清。

---

## 问题按严重度

**SEV-1（阻断级，必须修复后才能上线口径）**
1. platform_v92.html 块1 JS 语法破坏（`try{` line7 缺 catch）→ 全页交互失灵，且当前公网就是坏版。修复方式：在加固增强块前补 `}catch(e){}` 闭合原 try，或重构该区域（escAi 等定义移出 try 体）。修复后必须重跑 node --check + 浏览器实测。

**SEV-2（高危）**
2. `web/platform_v92.html.deploy_bak` 未搬走：白名单 57→58 破坏 + 公网 200 暴露旧品牌口径（"GBT AI Control Center v92 · AI Automation"）。搬走并复测 404。

**SEV-3（中危，内容口径）**
3. wallet.html 可见区 DEX×5；7 页 head meta"去中心化"×3/页；caps_panel 可见 p2p 按钮×8 + "去中心化 P2P 推理网络"×1；platform_v92 可见区 BestChange/bisq/p2p/DEX 导航与卡片标签（内部工具页豁免语义，但公开可达，Owner 决策）。

**SEV-4（低危）**
4. payment.html 3 个站内死链（/docs/pricing.html、/wallet/、/）。
5. platform_v92 可见区 emoji 残留 28 个（✓⚠⏳✗✔；扣费率行豁免后 23）——装饰符号，非武器/敏感 emoji。

---

## 总判定

**NO-GO** —— 旗舰页 platform_v92 主脚本块语法破坏导致全页交互瘫痪且已在线上（SEV-1），叠加 deploy_bak 旧口径公网暴露（SEV-2），两项修复并复验前不得视为收口完成。
