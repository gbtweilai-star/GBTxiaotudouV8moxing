# Harness 进化任务计划

## 任务背景
用户注册 GLM key 期间，要求深度研究 DeepSeek Harness（实为已吞噬的 ECC Harness）指南，给主用大模型搞进化。

## 本机资产盘点（已完成）
- brain/llm_client.py（26KB）：主模型层，七通道回退（agnes→glm→deepseek→kimi/nvidia/tokenhub/charger），视觉缓存+节流+通道统计
- devoured_ecc cap：ECC Harness 吞噬产物（68 agents + 286 skills + 121 rules + 19 harness 适配）
- harness_fusion cap：ECC × 万能插融合内核（指令总线/单操控/多单元协同/同步校验）
- brain/deepseek_bridge.py：空文件（0B，占位）
- auth_config.json：能力授权配置

## 子任务分发

### 1. Harness 进化架构师（subagent_01）
- 输出：.cluster/harness-evolution/subagent_01.md
- 职责：研究 ECC Harness 原始设计 + 业界 harness 最佳实践 + GLM-4.7-Flash 特性 → 设计六项进化方案（上下文预算/技能按需注入/工作环/思考模式/回退链/记忆持久化）
- 审查项：方案必须具体到"改哪个函数"，不许空谈

### 2. GLM 接入实战调研员（subagent_02）
- 输出：.cluster/harness-evolution/subagent_02.md
- 职责：GLM-4.7-Flash API 参数/免费额度限速/模型三档推荐/SDK 兼容坑/编程实测/视觉通道
- 审查项：所有数字标注来源，查不到明说

## 依赖图
1 和 2 并行 → 主线汇总 → 落地进化补丁 → 交付报告

## 主线剩余工作
- 等 2 个 Agent 返回
- 汇总设计 → 直接落地 llm_client.py 进化补丁（等 key 到位后实测）
- 交付进化报告到 DELIVERY/
