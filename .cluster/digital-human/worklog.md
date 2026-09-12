# 桌面数字人「GBT小土豆」v1 · 收口工作档案

> 2026-09-12/13 · taskId: digital-human · 本档案记录本轮补齐与全面推进的完整过程

## 一、排查结论（用户问：还有没有缺失）

**有缺失，且是关键缺失**：此前只有调研（subagent_01/02/03.md）和评估报告（DELIVERY/桌面数字人可行性评估报告.html），**没有一行可运行的数字人代码**。

具体缺口清单：
1. 渲染依赖未安装（PySide6、live2d-py）
2. 无 Live2D 美少女模型文件
3. 无形象层主程序（透明置顶 Live2D 窗口）
4. 无半透明全息悬浮对话面板
5. 无调皮行为引擎（爬面板玩耍、点击反应、走动、打盹）
6. 无整合入口、配置、人设

## 二、本轮补齐（全部完成）

| 缺口 | 补齐产物 | 状态 |
|---|---|---|
| 依赖 | PySide6 6.11.2 + live2d-py 0.7.0.4 + numpy + pyopengl 已安装 | ✅ pip 冒烟通过 |
| 模型 | Haru 官方示例模型完整下载（moc3 + 2 张 2048 纹理 + 8 表情 + 27 动作 + 物理 + pose） | ✅ 文件完整 |
| 形象层 | potato_pet/pet_window.py + win_utils.py（形象层工程师 subagent） | ✅ 已交付 |
| 面板+聊天 | potato_pet/holo_panel.py + chat_client.py（面板与对话工程师 subagent） | ✅ 已交付 |
| 行为引擎 | potato_pet/behavior.py（行为引擎工程师 subagent） | ✅ 已交付 |
| 整合 | potato_pet/main.py + config.json + persona.md + README + 启动小土豆.bat（主线） | ✅ 已交付 |

## 三、集成实测记录

- live2d-py 0.7.0.4 API 实测：`LoadModelJson`（非 LoadModel）、`SetAutoBlinkEnable`/`SetAutoBreathEnable`/`StartMotion`/`StartRandomMotion`/`SetExpression`/`HitTest`/`HitPart`/`Drag` 全部存在 ✅
- **关键坑（审查必查）**：offscreen 无 GL 上下文时 `LoadModelJson` 会段错误崩溃（exit 0xC0000005）——模型加载必须延迟到 QOpenGLWidget.initializeGL() 内执行，且 C++ 层日志显示 glad 初始化失败时渲染器创建会崩
- Haru 模型动作组：`Idle` / `TapBody`（model3.json FileReferences.Motions）——行为引擎的 motion group 名要与这两个对齐，不能瞎编组名
- Haru HitAreas：`Head` / `Body` 两个点击区
- 表情 8 组：F01~F08

## 四、待办（审查轮 + 交付轮）

1. subagent_07 对抗审查四个核心模块（崩溃风险/线程/编码/接口契约一致性）
2. 修复审查发现的问题
3. 真机 GUI 冒烟（用户双击 启动小土豆.bat）
4. subagent_08 交付报告 + DELIVERY 收口
5. 未来增强项（不阻塞 v1）：GLM API key 接入实测、TTS 语音、ASR、OpenClaw 网关联动干活
