# 五维合一系统·最终完整版 执行计划

## 任务边界
用户已确认五维合一 = 脑-眼-耳-嘴-手。前序轮次已完成：
- 基础系统 five_dimension_system.py（五维框架）
- 增强版 five_dimension_enhanced.py + 3 个增强能力（decision_brain / mouse_controller / text_generator）

本轮目标（下一步）：
1. 视觉维增强：deep_vision（深度视觉分析）+ ocr_engine（文字识别）
2. 听觉维增强：sound_detector（声音事件检测）+ emotion_recognizer（语音情感识别）
3. 执行维增强：keyboard_controller（键盘控制）+ file_operator（文件操作）
4. 集成最终完整版系统（增强率 60% → 100%）
5. 生成最终交付报告

## 子任务分解（并行轴：按维度切分）

| # | 子任务 | 执行者 | 产出文件 | 角色视角 | 审查项 |
|---|--------|--------|----------|----------|--------|
| 1 | 视觉维增强（2 个能力模块） | subagent 视觉维增强 Worker | caps/deep_vision.py, caps/ocr_engine.py, subagent_01.md | 计算机视觉工程师 | 代码可运行、接口完整、风格与现有模块一致 |
| 2 | 听觉维增强（2 个能力模块） | subagent 听觉维增强 Worker | caps/sound_detector.py, caps/emotion_recognizer.py, subagent_02.md | 音频算法工程师 | 同上 |
| 3 | 执行维增强（2 个能力模块） | subagent 执行维增强 Worker | caps/keyboard_controller.py, caps/file_operator.py, subagent_03.md | 桌面自动化工程师 | 同上 + 无危险操作 |
| 4 | 系统集成（依赖 1-3） | 主线 | five_dimension_ultimate.py | 系统架构师 | 五维全部接入、可运行 |
| 5 | 代码交叉审查（依赖 1-4） | subagent 审查 Worker | review.md | 对抗性代码审查 | 逻辑缺陷、风格偏差、遗漏 |
| 6 | 最终报告与交付（依赖 5） | 主线 | DELIVERY/ 报告 + 完整代码包 | 交付负责人 | 文件齐全、可打开 |

## 依赖图
- 任务 1、2、3 并行（第一轮）
- 任务 4 依赖 1-3 完成
- 任务 5 依赖 4
- 任务 6 依赖 5

## 统一代码约定（传给每个 Worker）
- 纯 Python 标准库，框架/骨架级实现（与现有 caps 风格一致）
- 类 + dataclass + 类型注解 + 中文 docstring + __main__ 自测
- 统一返回 Dict 结构，含 status 字段
