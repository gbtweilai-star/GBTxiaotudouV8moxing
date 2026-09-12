# 桌面数字人「GBT小土豆」· 补齐缺失全面推进 · 调度计划

> taskId: digital-human（复用既有工作区）· 2026-09-12 → 09-13 v2 升级
> v1：形象+面板+行为引擎已交付，残影 bug 已修复并经帧稳定性验证（delta 0.0%）

## cluster_bypass_reason

本任务曾派 3 个工程子代理（形象层/面板对话/行为引擎）全部 20 分钟超时零产出，
另派 1 个代码审查员 LLM 超时失败。为避免继续空耗，S2 后改由主线亲自完成全部
实现与审查，此决定已在交付报告中如实记录。

## v2 升级（对齐全网最热项目，2026-09-13 凌晨）

| # | 升级项 | 参照热项 | 实现 |
|---|--------|---------|------|
| 1 | 全息 HUD 遥测条：反应堆状态灯 + CPU/内存/电量/时钟 | HoloJarvis | holo_panel.py 顶部遥测区，ctypes 零依赖采集 |
| 2 | 工具调用（MCP 同概念）：天气/系统状态/时间/开应用 | Miku On Desktop / Desktop Pet | tools.py 工具注册表 + GLM function calling + 离线关键词触发 |
| 3 | 语音说话 | Project AIRI / Open-LLM-VTuber | voice.py：Windows SAPI 零依赖合成，线程化 + 限流，config 开关 |
| 4 | 好感度系统 | MeaPet | behavior.py 好感计数 + potato_state.json 持久化 + 面板显示 |

## 验证计划
重启 → 帧稳定性复检 → 遥测/工具/语音功能冒烟 → 同步 DELIVERY → v2 报告

## 已有资产（复用，不重跑）
- subagent_01.md 开源数字人项目调研（Open-LLM-VTuber 13.7k star 路线验证：Live2D 桌宠模式可行）
- subagent_02.md 形象层技术调研（推荐栈：PySide6 + live2d-py(Cubism 5) + QOpenGLWidget + Win32 ctypes）
- subagent_03.md 对话/行动链路调研（GLM-4.7-Flash 免费 API + 离线兜底策略）
- DELIVERY/桌面数字人可行性评估报告.html（三层全部可行）
- 硬件盘点实测：AMD RX 6500M 4GB（无 CUDA）/ Ryzen 5 5600H / 7.4GB RAM / 单屏 1536x864@125% DPI
- pip 可用版本已核实：PySide6 6.11.2、live2d-py 0.7.0.4（Python 3.13.12）

## 缺口（本轮补齐）
1. 依赖未安装：PySide6、live2d-py → 主线后台安装
2. 无 Live2D 模型文件 → 主线从 live2d-py 仓库下载 Hiyori 示例模型
3. 无形象层主程序（透明置顶 Live2D 窗口）→ subagent_04
4. 无半透明悬浮对话面板 → subagent_05
5. 无调皮行为引擎 → subagent_06
6. 无整合入口/配置/人设 → 主线（main.py、config.json、persona.md）
7. 代码风险审查 → subagent_07（第二轮）
8. 交付文档撰写 → subagent_08（第二轮，基于集成实测结果）

## 子任务表
| # | 子任务 | 负责 | 产出文件 | 角色 | 审查项 |
|---|---|---|---|---|---|
| 1 | pip 安装 PySide6+live2d-py | 主线 | 环境就绪 | - | import 冒烟 |
| 2 | 下载 Live2D 模型资源 | 主线 | potato_pet/resources/ | - | model3.json 可解析 |
| 3 | 形象层 Live2D 透明窗口 | subagent_04 | potato_pet/pet_window.py + win_utils.py | 工程实现 | live2d-py API 用法/透明置顶/DPI |
| 4 | 全息悬浮对话面板+聊天客户端 | subagent_05 | potato_pet/holo_panel.py + chat_client.py | 工程实现 | 无边框半透明/线程安全/降级链 |
| 5 | 调皮行为引擎（状态机） | subagent_06 | potato_pet/behavior.py | 工程实现 | 状态转移/权重调度/回调契约 |
| 6 | 整合入口+配置+人设 | 主线 | potato_pet/main.py + config.json + persona.md | - | offscreen 全链路冒烟 |
| 7 | 代码风险对抗审查 | subagent_07 | review.md | 对抗审查 | 崩溃风险/线程/编码/边界 |
| 8 | 交付报告撰写 | subagent_08 | 交付报告 md | 文档撰写 | 与实测一致、缺口如实 |
| 9 | 最终交付 | 主线 | DELIVERY/桌面数字人GBT小土豆/ + 报告 HTML | - | 可运行 + 桌面演示 |

## 依赖图
1,2 → (3 ∥ 4 ∥ 5) → 6 → 7,8 → 9

## 模块接口契约（三方共同遵守）
- pet_window.PetWindow(QWidget)：信号 clicked(str)/drag_pos_changed(int,int)/panel_toggle_requested()/quit_requested()；方法 start_motion(group,priority=1)/set_expression(name)/look_at_global(x,y)/window_rect()->QRect
- holo_panel.HoloPanel(QWidget)：信号 message_submitted(str)/close_requested()；方法 show_panel()/hide_panel()/toggle()/add_message(role,text)/set_thinking(bool)/panel_rect()->QRect/move_near(pet_rect)
- behavior.BehaviorEngine(QObject)：构造注入回调（get_pet_rect/get_panel_rect/move_pet_to/set_panel_visible/play_motion/set_expression/say）；方法 start()/stop()/on_pet_clicked(part)/on_message(role,text)/on_drag_end()
- chat_client.ChatClient：send(text, on_reply) 异步；离线俏皮应答 + GLM API 可选（读 config，无 key 自动离线）
- 统一：全 UTF-8；路径走 config；不 print 非 ASCII 到 GBK 控制台；不硬编码绝对路径
