# 公众门面上线前审校报告（gbt-public-showcase · 复核 05）

- **审校时间**：2026-09-12 09:27 GMT+7
- **审校对象**：本轮刚上线的公众门面改动（index v6 / terms 新建 / exchange 补丁 / site_a/b/c 补丁 / wallet_v2+messages 补丁）
- **方法**：只读排查。本地源码（`web/` 目录）逐行扫描 + 公网 `https://wallet-api.gbtxiaotudou.com/ui/*` 实拉 200 校验 + 本地/线上字节级 diff + deploy_bak 补丁逐行比对。未修改任何源文件。
- **审校基线**：本地 `web/` 为本轮新版（时间戳 2026-09-12 09:23-09:26），线上与本地内容一致（每文件 +367B 为 Cloudflare 自动注入的 beacon 脚本，非页面源码，详见问题 P4）。

---

## 一、逐项 PASS/FAIL 表

| # | 审校项 | 结果 | 证据 |
|---|--------|------|------|
| ① | 红线词（index/terms/exchange） | **PASS** | 本地+线上逐页词边界扫描（排除 base64 数据串与 index 子串）：bestchange/bisq/p2p/dex（\b 词边界）/兑换商/去中心化/订单簿/场外 均 0 命中。另核 site_a/b/c、wallet_v2、messages 线上版亦全部 0 命中 |
| ② | 费率口径三值齐全、无 3% 残留 | **PASS** | **index**：1.5% L207/L227/L242/L244，10% L207/L227/L244，5% L207/L227；**terms**：L54(1.5%)/L55(10%)/L56(5%) 费率卡；**exchange**：L206(币→币1.5%)/L207(法币→币10%)/L208(量化收益5%)+L272/L409。三页 3% 残留均为 0 |
| ③ | 免责与合规 | **PASS** | **index**：不构成任何要约 L326；年满 18 周岁 L215/L302/L326；所在地区适用法律法规 L302/L326。**terms**：不构成任何要约 L72；年满 18 周岁 L70；所在地区适用法律法规 L71。**terms 风险提示**：L64「量化收益不保证，存在市场风险与本金损失风险；历史表现不代表未来」+ L65「不提供任何保本、保收益承诺」。exchange 免责 L234 hero-foot 三连（18+/所在地区/不构成要约/本金损失）齐备 |
| ④ | 死链（本地 href + 公网 200） | **PASS** | 公网 10 目标全 200：index(21927B)/terms(5263B)/exchange(67204B)/site_a(338621B)/site_b(199934B)/site_c(483623B)/wallet_v2(25527B)/messages(34724B)/favicon.svg(255B)/gbt_hero_facade.jpeg(65233B)。index 18 个 href：13 个 `/ui/*` 本地文件全部存在（`/ui/` 为部署路径前缀，映射 `web/` 根），4 个页内锚点 + 1 个 `#flow`；terms 5 个 href 全部有效。hero 图 CSS 相对引用 `gbt_hero_facade.jpeg`（L48）在 `/ui/` 下解析 200 |
| ⑤ | index v6 结构 | **PASS**（1 处死锚见 P1） | 6 入口全齐：exchange L201(CTA)+L237(大卡)+L321(页脚)、wallet_v2 L247+L320、messages L254+L322、site_a L286、site_b L287、site_c L288。hero 图 L48 `url('gbt_hero_facade.jpeg')` 存在且线上 200。`<script>` 0 个、on* 内联事件 0 个、外部资源依赖 0（纯静态达成，线上 beacon 为 CDN 注入非源码，见 P4） |
| ⑥ | 移动端 | **PASS** | @media 覆盖 900px(L146) 与 640px(L158) 双断点 + prefers-reduced-motion(L171)。≤640px：L164 `.cta-row{flex-direction:column;align-items:stretch}` + L165 `.btn-main,.btn-sub{width:100%;justify-content:center}` → CTA 满宽。hero-art 为 `position:absolute;inset:0;background:…center/cover`（L48），小屏随容器自适应裁切，hero-veil 左侧 90% 渐变（L49）保证文字区可读性；640px 时 hero 取消 min-height 改 56px 双边距（L160）防止小屏溢出。900px 下 prod-grid/dir 单列化、stats 2×2、f-row 重排（L147-155），布局完整 |
| ⑦ | 违规话术（8 页） | **PASS**（1 处词面命中为合规反声明，见 P5） | 逐页扫描低风险/低门槛/秒到账/高收益/低利率/无成本/保本/保收益/稳赚/躺赚/暴富/100%安全：仅 terms.html L65「平台**不**提供任何**保本、保收益**承诺」否定句命中——语境为风险披露的合规反声明，非营销承诺，判定正当。其余 7 页 0 命中。messages 的"10%"命中实为 CSS 渐变坐标 `at 80% -10%`（L27），非费率表述，已排除 |
| ⑧ | HTML 标签平衡 | **PASS** | **index**：div 75/75、section 3/3、a 17/17、header 1/1、footer 1/1、nav 1/1、span 27/27、p 11/11 全平衡。**terms**：div 10/10、a 4/4、span 6/6、p 4/4、ul 2/2、li 6/6 全平衡 |

### 补丁落实核验（对照改动清单）

| 改动项 | 落实情况 |
|--------|----------|
| index.html 全新 v6 | ✅ Hero+信任条(L204-217)+数字带(L222-229)+非对称三入口(L236-261, 1大2小)+五步流程(L270-276)+方向预览(L285-289)+合规章(L294-309)+页脚(L312-328)，结构完整 |
| terms.html 新建 | ✅ 五章结构（服务说明/费率口径/风险提示/合规要求/到账与结算）+ 底部 tabbar 导航，公网 200 |
| exchange.html 补丁 | ✅ deploy_bak diff 仅 +1 行 favicon（L6）；量化收益 5% tag（L208）已在旧版存在且新版保留；免责 L234 齐备；title/description 品牌口径「GBT小土豆量化收益平台」正确 |
| site_a/b/c 补丁 | ✅ deploy_bak diff 各 4 行：terms 死链 `href="terms"` → `href="/ui/terms.html"`（旧版裸 "terms" 在 /ui/ 下会 404，已修复）×3 处 + 新增「进入平台 →」CTA 指向 /ui/index.html ×1 处 |
| wallet_v2 补 favicon | ✅ deploy_bak diff 仅 +1 行 `<link rel="icon" href="/ui/favicon.svg">`（L6） |
| messages 补 favicon + meta description | ✅ deploy_bak diff：+favicon L6 + description L8 |

---

## 二、发现的问题（按严重度）

### P1 · 中 — index.html 导航死锚 `#fees`
- **位置**：L187 `<a href="#fees">费率</a>`
- **问题**：页面定义的 id 仅 `directions`/`flow`/`products`，无 `fees`。点击后无滚动目标（浏览器滚回顶部）。
- **影响面**：仅桌面端（≤900px 时 .top-links 已 display:none）。
- **建议**：给数字带 `.stats` 区块加 `id="fees"`（该区 L227 正好展示「1.5% / 10% / 5% 全程明示」），或将导航项改指 `#products`。

### P2 · 低 — exchange.html「平台条款」无落地链接
- **位置**：L234 hero-foot「连接钱包即代表您已阅读并同意平台条款」
- **问题**：全页 0 处 terms.html 链接，用户在 exchange 页无法直达条款全文（需绕行 index/site 页）。
- **建议**：hero-foot「平台条款」四字加 `<a href="/ui/terms.html">`。本轮改动清单未含此项，属轻微遗漏而非回归。

### P3 · 低 — site_a/b/c favicon 为空占位
- **位置**：三页均为 `<link rel="icon" href="data:,">`
- **问题**：8 页中 5 页已用 `/ui/favicon.svg`，site 三页标签页无图标，品牌一致性轻微打折。本轮改动清单未包含 site 页 favicon，非回归，建议下轮统一。

### P4 · 提示 — 线上全站被 Cloudflare 自动注入 beacon 脚本
- **证据**：8 个文件线上均比本地恰多 367B，diff 确认为 `static.cloudflareinsights.com/beacon.min.js`（Cloudflare Web Analytics 自动注入，位于 `</body>` 前）。
- **定性**：非页面源码，index v6「纯静态无脚本」以源码为准成立。但若对第三方 RUM 脚本（访客数据采集）有合规顾虑，可在 Cloudflare 控制台关闭自动注入——由 Owner 决策，不影响本次上线。

### P5 · 提示 — terms.html L65 词面命中「保本/保收益」
- 语境为「平台**不**提供任何保本、保收益承诺；请勿相信任何以本平台名义作出的收益保证」，属风险披露的合规反声明（正是监管要求应写的内容），非违规营销话术，判定正当使用、无需修改。

---

## 三、上线判定

**GO** —— 合规红线（禁词/费率口径/免责/18+/死链）全部 PASS，补丁与清单逐项吻合、线上与源码一致；唯一功能性缺陷为 `#fees` 死锚（P1，中低严重度、不影响合规与资金链路），建议热修但不构成上线阻断。
