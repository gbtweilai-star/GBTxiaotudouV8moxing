# vision_print · 触手记忆库

> 本库是触手 `vision_print`（视觉打印）的**独立永久记忆**。互通往返见页尾。

## 这本库记什么
- 这根触手吞进来的东西（吞天吸收 → 记 `记忆.md`）
- 它的能力面与判据
- 它踩过的坑与修法（教训只追加，不改历史）

## 能力位一句话
**视觉打印（主人令 2026-10-13「看到的东西都可以原样以代码打印并渲染成看到的样子」）**：
五段链 **①see 取帧 → ②print 打成代码 → ③render 真渲染 → ④diff 与所见帧比 → ⑤judge 成档**。
码由**她/调用方**给（本件不编码）；要模型看图回码走 `op=ask_model`。

## 为什么要有它（现读三面证明这条链**从未在册**）

| 面 | 现读 | 缺什么 |
|---|---|---|
| 她的「看」 | tentacle 视觉 12 法 + `vision` / `vlx_flow` / `vision_grounding` | 只出**读数与指纹**，不吐代码 |
| 她的「渲」 | `ui_render`（**8 组件白名单** · 零脚本零外链） | 是**报告页**渲染器，按设计就还原不了任意界面 |
| 框架自述 | `zimage_rewash` desc：「**无图像理解能力位**：vision 是屏幕视觉、云链 ask() 是纯文本」 | 「看图→出码」这格是空的 |
| 反向那一半 | `render_page.py`（真 Chromium 渲成 PNG 给自己看） | 那是「码→像」，不是「像→码」 |

⇒ 「有没有丢」的答案：**没丢，是从来没长出来**；本件把它补上。

## 尺子：为什么档位咬的是"局部敏感"那两个数（本条最重要）

首版只用 **整图 aHash 距离 + 4×4 块变化率 + 平均亮度差** 判档。自测当场抓到**假绿**：

```
只见帧 A × 码 A（改一处文字颜色 #00E5FF→#FF6B6B）
  ⇒ aHash 距离 = 0 · 块变化率 = 0.0 · 平均亮度差 = 0.0   ⇒ 判成「同款」
```

**那不是"像"，那是尺子看不见**：整图缩到 16×16 后，一行字的颜色在均值里被抹平；
平均值又被整页面积摊薄。⇒ 补两个**局部敏感**的现算数：
`变化像素占比`（逐像素容差 8 之外的比例）与 `最大块平均差`（4×4 里最差那块的平均像素差）。
补齐后同一对图 ⇒ **接近**（变化像素占比 0.00397 · 最大块平均差 13.83）。

档位表（`tools/vision_print.py::_BANDS`，**可复核可改**，字段序 =
名字 · aHash 距离上限 · 块变化率上限 · 变化像素占比上限 · 最大块平均差上限）：

| 档 | aHash≤ | 块变化率≤ | 变化像素占比≤ | 最大块平均差≤ |
|---|---|---|---|---|
| 同款 | 4 | 0.125 | 0.002 | 6.0 |
| 接近 | 10 | 0.375 | 0.02 | 20.0 |

## 落地读数（2026-10-13 · 五处齐）

| 处 | 读数 |
|---|---|
| 注册表 | 在册（`domain=vision` · `handler=vision_print`） |
| 分派 | 唯一门真跑 `cap vision_print` ⇒ `status: ok` · 默认 `op=status`（零作用域） |
| 作用域 | `security/policy.py` 逐 op 定档：status/where 零 · see/diff → `privacy_read` · print/loop → `process_execute`+`filesystem_write`（loop 另加 `privacy_read`）· ask_model → `privacy_read`+`external_llm`；**未知 op fail-closed** |
| 触手 | 总纲 `### 视觉(13)` 收入 `vision_print`；分派分支真 import `vision_bus` + `vision_cap` ⇒ **触手承载**（代码证据） |
| 三控自测 | 正控 **同款**（全 0）· 中间控 **接近** · 负控 **不像**（aHash 距离 45 / 变化像素占比 1.0）· 原生眼控 **不像** |

## 关联
- 本体自研库：[[GBT本体记忆]]
- 心跳：`run_task('obsidian_vault', {'op':'remember','tentacle':'vision_print','text':'…'})`
- 对位件：`gbt_allinone/tools/vision_print.py` · 纪律同族 `tools/codex-scripts/render_page.py`
- 尺子出处：`gbt_allinone/tentacle/vision_bus.py`（aHash / 网格块 / 区域差）
- 眼出处：`gbt_allinone/tentacle/omni_core.py::_screen_capture`（dxcam→mss→pyautogui）

---
互通往返：本页链回 [[GBT本体记忆]]；本体库 [[触手总索引]] 链回本库。
