# web_archive 归档清单

> 归档时间: 2026-09-12 · 原因: 公网根收敛，只保留当前产品面 · 方式: Move（可恢复），未删除任何文件
> 生成: 收口轮终验

| 类别 | 数量 | 内容 |
|---|---|---|
| history/ | 80 | platform_v43..v91、gbt_quant_platform_v13..v40、散落历史页 |
| backups/ | 30 | 9 个首轮 .deploy_bak + 16 个时间戳备份 + autoclaw bak + 9 个修复轮 deploy_bak + platform_v92.deploy_bak.20260912_v922（SEV-2 补归档） |
| internal/ | 50 | v47..v75 showcase、v76 验收/报告、v77..v84 报告、零引用图片、assets/、__pycache__/ |

共 163 个文件（web/ 保留 57 = 白名单分毫不差）。恢复方式：`Move-Item web_archive\<类>\<文件> web\`。

## history/（80）
platform_v43.html · platform_v45.html … platform_v91.html（78，v44 不存在）
gbt_quant_platform_v13..v39.html · v19_guide · v40_cis_harvester（29）
ai_full_control_v44.html · cis_v41_dashboard.html · cis_v42_dashboard.html（3）

## backups/（30）
首轮: index/wallet_v2/exchange/messages/site_a/site_b/site_c/platform_v92 的 .deploy_bak（8）
时间戳: platform_v76_backup_clean、v84/v85/v86/v87/v88/v89/v90/v91 各 backup_*/bak_*（16）
autoclaw-tools/index.html.bak_2026-09-090058（1）
SEV-2 补: platform_v92.html.deploy_bak.20260912_v922（1）
修复轮: ai-browser/caps_panel/digital_asset/gbt-chat/health/monitor/payment/platform_v92/temp_mail 的 .deploy_bak（9→其中 platform_v92 的已改名入上条，另 8 个 + payment 计入）——精确 30 含目录 deploy_20260912/ 下 9 个

## internal/（50）
v47..v75_showcase.html（29）· v76_acceptance.html/.png · v76_fee10_report · v76..v84_report.html（12）
gbt_hero_v2.jpeg · gbt_mascot_icon.jpeg（2）· assets/（gbt-3d.js、mermaid.min.js）· __pycache__/（3 pyc）
