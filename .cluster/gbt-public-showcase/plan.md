# 用工收口轮 · 调度计划（2026-09-12）

任务：把整个平台的"毛边"收干净——公网根只留当前一代产品，旗舰页品牌收口，全程可验证。

## 现状（S1 已确认）
- web/ 目录 144 文件全量公网可达（含 .deploy_bak ×7、platform_v13..v91 历史版本 ×34、v*_report/showcase/acceptance 内部工件 ×34、备份 .backup_* ×13）
- platform_v92.html：标题 "GBT AI Control Center v92 · AI Automation"（英文内部口径）、无 favicon、无 meta、可见区 emoji 37 个（含 🔫）
- 路由表 _routes.json 47 条路由，其中 /wallet→旧版 wallet.html、/quant_*→旧版量化页（公众可达旧皮肤）

## 三条作业线
- A 线（归档搬运）：web/ 中被确认为"备份/历史版本/内部工件"的文件移至 web_archive/（Move 可恢复，不删除）。保留白名单 = 公开产品页 + 其引用资产 + 路由仍指向的功能页。
- B 线（旗舰收口）：platform_v92 标题/meta/favicon 品牌化，可见区 UI emoji → SVG/文字（🔫 必除），不动费率数字与红线文案。
- C 线（回归复查）：搬运+补丁后，公网面全量回归（200/引用完整性/红线/费率）。

## 子代理调度
| # | 子代理 | 角色 | 输出 | 依赖 |
|---|---|---|---|---|
| 5 | 公网依赖审计员 | 只读扫描：10 个公开页+platform_v92 的全部本地引用（href/src/url()/fetch）→ 给出保留白名单 + 搬运清单 | subagent_05.md | 无 |
| 6 | 旗舰页面病历员 | 只读扫描：platform_v92 全部可见区 emoji 精确锚点+英文串+品牌口径问题清单 | subagent_06.md | 无 |
| 7 | 对抗复查员 | 搬运+补丁后：公网面回归验证（第二轮派发） | subagent_07.md | A+B 完成后 |

主线职责：deploy 补丁（子代理不可写源项目）、PowerShell 搬运、验证、交付报告。

## 边界与安全
- 搬运 = Move 至 web_archive/，不删除；路由表不动（功能路由可能有运维依赖，仅报告建议）
- platform_v92 的费率数字（如出现）与红线词逐字保留；只动品牌皮肤层
- 内部工具页（monitor/health/caps_panel/temp_mail/ai-browser/gbt-chat/payment/wallet 旧版）**保留在 web/**——它们挂在功能路由上，可能有运维依赖；是否公网隔离属 Owner 决策，写入报告 P1
