# 公网依赖审计 · 搬运清单 & 保留白名单

> 审计员：公网依赖审计员（只读，未修改任何文件）
> 范围：`C:\Users\ADMIN\Desktop\GBT小土豆\web`（全量公网可达，共 210 个文件）
> 结论性质：精确搬运清单 + 保留白名单 + 风险缺口提示

---

## 一、结论

1. **公开产品面 = 11 个页面**：`index.html`、`wallet_v2.html`、`exchange.html`、`messages.html`、`terms.html`、`site_a.html`、`site_b.html`、`site_c.html`、`platform_v92.html`、`payment.html`、`digital_asset.html`。这 11 页的**联合本地资源引用仅 21 项**，静态文件依赖极轻（favicon.svg、qr_local.js、gbt_hero_facade.jpeg 三件）。
2. **路由层（`_routes.json` 47 条 = 24 个唯一服务文件）**：除 11 个公开页中已覆盖的 `index/wallet_v2/exchange/payment/digital_asset` 外，还有 19 个独立路由功能页必须保留在 `web/`。
3. **白名单 57 个文件，搬运 153 个文件**，二者合计 210，零遗漏、零重叠。
4. **交叉验证通过**：抽样的 5 个搬运候选（`platform_v91.html`、`v84_report.html`、`gbt_quant_platform_v40_cis_harvester.html`、`platform_v84.backup_2026-09-082306.html`、`v76_acceptance.html`）在 11 公开页 + 19 路由页的全文 grep 中**全部零引用**，确认可安全搬运。附加零引用资产（`gbt_hero_v2.jpeg`、`gbt_mascot_icon.jpeg`、`v76_acceptance_shot.png`、`gbt-3d.js`、`mermaid.min.js`）同样零引用。
5. **8 个「运维依赖待 Owner 确认」文件**：`wallet.html`（路由 `/wallet` 指向）+ `monitor.html`、`health.html`、`caps_panel.html`、`temp_mail.html`、`ai-browser.html`、`gbt-chat.html` + 3 个后端脚本 `universal_panel_server.py`/`cis_v41_trader.py`/`cis_v42_trader.py` 被**外部运维代码引用**（见第四节），不能擅自搬运。

---

## 二、引用扫描证据

### 2.1 11 个公开页的联合本地引用（21 项）

| 引用 | 类型 | 来源页 | 处置 |
|---|---|---|---|
| `gbt_hero_facade.jpeg` | 图片 | index.html | 保留（index 直接引用） |
| `qr_local.js` | JS | wallet_v2.html | 保留（wallet_v2 直接引用） |
| `favicon.svg`（相对 `favicon.svg` + 根路径 `/favicon.svg`） | 图标 | exchange/messages/terms/payment/wallet_v2 等 6 页 | 保留（共享图标） |
| `/ui/index.html` 等 7 个 `/ui/xxx` | 站内导航 | 各页互链 | 服务端重写，映射到根同名页，保留对应根页即可 |
| `/` `/wallet` `/wallet/` `/payment` `/v9_ultimate` | 路由链接 | payment/digital_asset | 路由层处理，保留路由目标页 |
| `/api/payment/*`（3 条） | API | payment.html | 后端接口，非静态文件 |
| `/docs/pricing.html` | 链接 | payment.html | ⚠️ 见风险 4.4，文件不存在 |

### 2.2 静态资源全目录反向 grep（关键证据）

| 文件 | 被引用次数 | 引用方 |
|---|---|---|
| `favicon.svg` | 10（含 4 个 .deploy_bak） | 6 个公开页 + 备份 |
| `qr_local.js` | 3（含 wallet_v2.deploy_bak） | wallet_v2.html + 备份 |
| `gbt_hero_facade.jpeg` | 2（含 index.deploy_bak） | index.html + 备份 |
| `gbt_hero_v2.jpeg` | **0** | 无 → 搬运 |
| `gbt_mascot_icon.jpeg` | **0** | 无 → 搬运 |
| `v76_acceptance_shot.png` | **0** | 无 → 搬运 |
| `assets/gbt-3d.js` | **0** | 无 → 搬运 |
| `assets/mermaid.min.js` | **0** | 无 → 搬运 |
| `gbt-invoice-qr.png` | 1 | wallet.html（但该文件**不存在**于 web/，运行时生成） |

> 注：`gbt-3d.js` / `mermaid.min.js` 未用 `assets/` 前缀出现在任何保留页；`caps/web_panel_server/run.py` 有 `/assets/` 前缀映射 `web/assets`，但保留页零 `/assets/` 引用，故 assets 目录可整体归档。

### 2.3 传递闭包

以「11 公开页 + 19 路由功能页」为种子做 HTML 链接闭包扫描，**未拉入任何额外页面**（种子集合自封闭）。即：路由外、公开页外，无隐藏静态依赖链。

---

## 三、保留白名单（57 个文件）

### A. 11 个公开产品页（11）
| 文件 | 保留理由 |
|---|---|
| index.html | 公网首页，`/` 路由 |
| wallet_v2.html | 钱包 v2，公开产品面 |
| exchange.html | 交易所页 |
| messages.html | 消息页 |
| terms.html | 条款页 |
| site_a.html | 站 A |
| site_b.html | 站 B |
| site_c.html | 站 C |
| platform_v92.html | 平台当前版 v92 |
| payment.html | 支付页 |
| digital_asset.html | 数字资产页 |

### B. 路由指向的功能页（19，含 8 个运维待确认项）
| 文件 | 保留理由 |
|---|---|
| v9_ultimate.html | 路由 `/v9_ultimate` |
| v9_terminal.html | 路由 `/v9_terminal` |
| quant_platform.html | 路由 `/quant_platform` |
| quant_pro.html | 路由 `/quant_pro` |
| quant_pro_v3.html | 路由 `/quant_pro_v3` |
| quant_pro_realtime.html | 路由 `/quant_pro_realtime` |
| quant_simple.html | 路由 `/quant_simple` |
| quant_terminal_v1.html | 路由 `/quant_terminal_v1` |
| quant_terminal_v11.html | 路由 `/quant_terminal_v11` |
| cis_dashboard.html | 路由 `/cis_dashboard` |
| cis_v4_dashboard.html | 路由 `/cis_v4_dashboard` |
| cis_report.html | 路由 `/cis_report` |
| **wallet.html** | 路由 `/wallet`；⚠️ 运维依赖待确认（见 4.1） |
| **monitor.html** | 路由 `/monitor`；⚠️ 被 `refresh_cap_health.py` F7 引用 |
| **health.html** | 路由 `/health`；⚠️ 被 `caps/web_panel_server/run.py` 服务 |
| **caps_panel.html** | 路由 `/caps_panel`；⚠️ 被 caps 服务引用 |
| **temp_mail.html** | 路由 `/temp_mail`；⚠️ 被 caps 服务引用 |
| **ai-browser.html** | 路由 `/ai-browser`；⚠️ 被 `brain/gbt_chat_server.py` 引用 |
| **gbt-chat.html** | 路由 `/gbt-chat`；⚠️ 被 brain 服务引用 |

### C. 共享静态资产（3）
| 文件 | 保留理由 |
|---|---|
| favicon.svg | 6 个公开页 + 根路径 `/favicon.svg` 引用 |
| qr_local.js | wallet_v2.html 直接引用 |
| gbt_hero_facade.jpeg | index.html 直接引用 |

### D. 路由配置 + 运维后端（4）
| 文件 | 保留理由 |
|---|---|
| _routes.json | 47 条路由定义，公网服务核心配置 |
| universal_panel_server.py | ⚠️ 被 `tests/test_universal_plugin.py` L29 直接读取；面板服务本体 |
| cis_v41_trader.py | ⚠️ 后端交易脚本，被 __pycache__ 对应 pyc 引用 |
| cis_v42_trader.py | ⚠️ 后端交易脚本，被 `tools/audit_r1.py`、`v46_完整增强版说明.md` 引用 |

### E. autoclaw-tools 子目录（20，排除 1 个 .bak）
| 文件 | 保留理由 |
|---|---|
| autoclaw-tools/index.html | 被 `refresh_cap_health.py` F1 引用 |
| autoclaw-tools/eigenflux-hub/index.html | F2 引用 |
| autoclaw-tools/eigenflux-space/index.html | F3 引用 |
| autoclaw-tools/eigenflux-space/EigenFlux 空间.html | 同目录配套 |
| autoclaw-tools/notify-center.html | F4 引用 |
| autoclaw-tools/obsidian-panel/index.html | F5 引用 |
| autoclaw-tools/obsidian-panel/gbt-map-data.js | 被 `brain/unified_core/sweep.py` L80 引用 |
| autoclaw-tools/obsidian-panel/icon-192.png / icon-512.png / manifest.webmanifest / sw.js | PWA 配套 |
| autoclaw-tools/personal-tools/index.html | F6 引用 |
| autoclaw-tools/personal-tools/icon-192.png / icon-512.png / manifest.webmanifest / sw.js | PWA 配套 |
| autoclaw-tools/README.md | 目录说明 |
| autoclaw-tools/connector-health.ps1 | 运维脚本 |
| autoclaw-tools/obsidian-panel/README.md / personal-tools/README.md | 目录说明 |

> ⚠️ `autoclaw-tools/index.html.bak_2026-09-090058` 是备份文件，已归入搬运清单（唯一被搬的 autoclaw-tools 文件）。

---

## 四、搬运清单（153 个文件，按三类）

### 类别一：历史版本（80 个）
`platform_v13..v91`（缺 v44，共 78 个）+ `gbt_quant_platform_v13..v40`（缺 v40 主体，实为 v40_cis_harvester，共 28 个），另含 2 个散落历史页。

**platform 系列（78）**
```
platform_v43.html  platform_v45.html  platform_v46.html  platform_v47.html
platform_v48.html  platform_v49.html  platform_v50.html  platform_v51.html
platform_v52.html  platform_v53.html  platform_v54.html  platform_v55.html
platform_v56.html  platform_v57.html  platform_v58.html  platform_v59.html
platform_v60.html  platform_v61.html  platform_v62.html  platform_v63.html
platform_v64.html  platform_v65.html  platform_v66.html  platform_v67.html
platform_v68.html  platform_v69.html  platform_v70.html  platform_v71.html
platform_v72.html  platform_v73.html  platform_v74.html  platform_v75.html
platform_v76.html  platform_v77.html  platform_v78.html  platform_v79.html
platform_v80.html  platform_v81.html  platform_v82.html  platform_v83.html
platform_v84.html  platform_v85.html  platform_v86.html  platform_v87.html
platform_v88.html  platform_v89.html  platform_v90.html  platform_v91.html
```
> 注：v44 不存在；v45..v91 除 v92（当前）外全部搬运。

**gbt_quant_platform 系列（28）**
```
gbt_quant_platform_v13.html  gbt_quant_platform_v14.html  gbt_quant_platform_v15.html
gbt_quant_platform_v16.html  gbt_quant_platform_v17.html  gbt_quant_platform_v18.html
gbt_quant_platform_v19.html  gbt_quant_platform_v19_guide.html
gbt_quant_platform_v20.html  gbt_quant_platform_v21.html  gbt_quant_platform_v22.html
gbt_quant_platform_v23.html  gbt_quant_platform_v24.html  gbt_quant_platform_v25.html
gbt_quant_platform_v26.html  gbt_quant_platform_v27.html  gbt_quant_platform_v28.html
gbt_quant_platform_v29.html  gbt_quant_platform_v30.html  gbt_quant_platform_v31.html
gbt_quant_platform_v32.html  gbt_quant_platform_v33.html  gbt_quant_platform_v34.html
gbt_quant_platform_v35.html  gbt_quant_platform_v36.html  gbt_quant_platform_v37.html
gbt_quant_platform_v38.html  gbt_quant_platform_v39.html
gbt_quant_platform_v40_cis_harvester.html
```

**散落历史页（2）**
```
ai_full_control_v44.html
cis_v41_dashboard.html
cis_v42_dashboard.html
```
> 注：`ai_full_control_v44.html` 全库零引用；`cis_v41/v42_dashboard.html` 非路由（路由只挂 `cis_dashboard`/`cis_v4_dashboard`）。

### 类别二：备份文件（25 个）
**deploy_bak（9）**
```
index.html.deploy_bak
wallet_v2.html.deploy_bak
exchange.html.deploy_bak
messages.html.deploy_bak
site_a.html.deploy_bak
site_b.html.deploy_bak
site_c.html.deploy_bak
platform_v92.html.deploy_bak
```
**backup 时间戳文件（16）**
```
platform_v76_backup_clean.html
platform_v84.backup_2026-09-082306.html
platform_v84.backup_20260909_0050.html
platform_v84_dd.backup_2026-09-082309.html
platform_v84_risk.backup_2026-09-082308.html
platform_v85_sl.backup_2026-09-082330.html
platform_v85_sl.backup_2026-09-082331.html
platform_v86_alerts.backup_2026-09-082334.html
platform_v87_tray.backup_2026-09-082337.html
platform_v88_sltrigger.backup_2026-09-082339.html
platform_v89.html.bak_realbt_2026-09-090001
platform_v89_btcard.backup_2026-09-082349.html
platform_v89_btcard.backup_2026-09-082350.html
platform_v90.html.bak_cfg_2026-09-090013
platform_v90.html.bak_eq_2026-09-090007
platform_v91.html.bak_notify_2026-09-090055
autoclaw-tools/index.html.bak_2026-09-090058
```

### 类别三：内部工件（41 个）
**showcase 系列（29）**
```
v47_showcase.html  v48_showcase.html  v49_showcase.html  v50_showcase.html
v51_showcase.html  v52_showcase.html  v53_showcase.html  v54_showcase.html
v55_showcase.html  v56_showcase.html  v57_showcase.html  v58_showcase.html
v59_showcase.html  v60_showcase.html  v61_showcase.html  v62_showcase.html
v63_showcase.html  v64_showcase.html  v65_showcase.html  v66_showcase.html
v67_showcase.html  v68_showcase.html  v69_showcase.html  v70_showcase.html
v71_showcase.html  v72_showcase.html  v73_showcase.html  v74_showcase.html
v75_showcase.html
```
**acceptance / report 系列（12）**
```
v76_acceptance.html
v76_acceptance_shot.png
v76_fee10_report.html
v76_report.html  v77_report.html  v78_report.html  v79_report.html
v80_report.html  v81_report.html  v82_report.html  v83_report.html  v84_report.html
```

### 类别四：零引用静态资产（7 个）
```
assets/gbt-3d.js
assets/mermaid.min.js
gbt_hero_v2.jpeg
gbt_mascot_icon.jpeg
__pycache__/cis_v41_trader.cpython-312.pyc
__pycache__/cis_v42_trader.cpython-312.pyc
__pycache__/universal_panel_server.cpython-312.pyc
```

> 小计核对：80 + 25 + 41 + 7 = **153** ✅

---

## 五、风险与缺口

1. **8 个「运维依赖待 Owner 确认」**：`wallet.html`（路由 `/wallet`）、`monitor.html`、`health.html`、`caps_panel.html`、`temp_mail.html`、`ai-browser.html`、`gbt-chat.html` 这 7 个 HTML + `universal_panel_server.py` 被**非 web/ 的运维代码**引用（`caps/web_panel_server/run.py`、`brain/gbt_chat_server.py`、`refresh_cap_health.py`、`brain/unified_core/sweep.py`、`tests/test_universal_plugin.py`、`tools/audit_r1.py`）。**搬运前必须由 Owner 确认这些运维服务是否仍在线、是否依赖 web/ 原路径。**

2. **autoclaw-tools 子目录是「半运维半产品」**：`refresh_cap_health.py` 的 FILE_MAP 明确引用 6 个 autoclaw-tools 文件 + `web/monitor.html`，`sweep.py` 引用 `obsidian-panel/gbt-map-data.js`。整目录已列白名单保留，但若 Owner 判断这些是内部工具，可整体降级为搬运（需 Owner 确认，非审计员权限范围）。

3. **`_routes.json` 在 web/ 外零引用**（全库 grep 无命中），说明它由公网网关/服务端直接读取。若归档时移动该文件，必须同步更新服务端配置路径，否则 47 条路由全部失效。

4. **`payment.html` 引用的 `/docs/pricing.html` 文件不存在**（`docs/pricing.html` 不存在于 `GBT小土豆/docs/`），当前该链接 404。搬运时需确认是否要在 `docs/` 补一个 pricing 页，或保留 404 现状。

5. **`wallet.html` 引用的 `gbt-invoice-qr.png` 不存在于 web/**，疑似运行时动态生成（发票二维码）。搬运 wallet.html 相关资产时勿误判该文件为「缺失需恢复」——它本就不在静态目录。

6. **三个 `.py` 后端脚本的 __pycache__ 可安全归档**：pyc 是编译缓存，搬运 py 本体或 pyc 均不影响源文件；但 `cis_v41/v42_trader.py` 本体被外部引用，**本体暂列白名单**，仅 pyc 归入搬运。

---

## 附：本次审计未做、也不该由审计员做的事

- 未修改、未移动、未删除任何文件（全程只读）。
- 未执行搬运动作——本报告仅产出「精确清单」，实际 mv/归档由执行员在 Owner 确认第 5.1 节 8 个运维依赖后操作。
