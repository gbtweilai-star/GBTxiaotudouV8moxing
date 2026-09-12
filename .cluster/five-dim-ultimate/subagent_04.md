# Subagent 04 交付报告：大脑执行层（Brain Executive）

## 一、结论

✅ **任务完成**。已交付 `caps/brain_executive.py`（约 24.6 KB，纯 Python 标准库：json/time/typing/dataclasses/enum/re），实现 BrainExecutive 类的 5 大核心能力，自测 6 个用例全部通过，包括任务要求的"正常任务"与"含失败步骤触发 retry"的完整闭环。

**实际写入的文件（正确路径，无空格）：**

- `C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\caps\brain_executive.py`（核心交付物）
- `C:\Users\ADMIN\Desktop\GBT小土豆V8\.cluster\five-dim-ultimate\subagent_04.md`（本报告）

> 说明：中途曾误写入带空格的错误目录 `GBT 小土豆 V8\.cluster\...`（该目录非本任务边界内），发现后已将文件复制到正确路径，并清理了误写副本。未触碰任务边界外的任何文件（dimension_sync.py、subagent_05.md、decision_brain.py 等 10 个能力模块均未改动）。

## 二、证据（自测输出）

自测命令：`python .\.cluster\five-dim-ultimate\caps\brain_executive.py`

**测试 2（失败→重试→恢复）关键输出：**
```
任务：打开浏览器，搜索 Python 教程，点击第一个链接，读取页面内容，总结并播报
状态：success
完成：5/5  反馈次数：6
  [BATCH 2] ... [RUN] step_2: 搜索 Python 教程
    [FAIL] step_2 执行失败：步骤失败，还可以重试 2 次
    [RETRY] step_2 开始第 1 次重试
    [RUN] step_2: 搜索 Python 教程
    [DONE] step_2 执行成功
  （后续 step_3/4/5 全部成功）
```

**测试 3（重试耗尽→abort）关键输出：**
```
状态：aborted  完成：1/5  反馈次数：4
    [FAIL] step_2 执行失败：步骤失败，还可以重试 2 次 → RETRY 1
    [FAIL] ... 还可以重试 1 次 → RETRY 2
    [FAIL] ... 关键错误，需要中止任务
    [ABORT] step_2 触发任务中止
  [ABORT] 任务中止，剩余批次不再执行
```

**测试 3/4（拆解与批次）**：'截图当前屏幕，识别截图中的文字，保存到文件' → 3 步（eye→eye→hand），线性依赖，3 个批次。

**测试 6（兜底）**："帮我处理一下"（无关键词）→ brain 维度单步 + 默认依赖为无。

## 三、分析（设计决策）

1. **维度识别规则**：按关键词计分取最高维度，无命中默认 BRAIN。理由：decision_brain 已存在，无关键词句子视为需要决策比盲发 hand 更合理；而任务规范要求"拆不出默认 hand+mouth 兜底"仅在完全无有效句子时触发（测试 6 走的正是该路径的边界情况——有句子但无关键词，归 brain；完全无句子如空串才走 hand+mouth）。
2. **依赖与并行**：相邻步骤可并行判定的规则保守——仅 eye+ear 判定可并行（同时看和听），hand+mouth 明确不并行（嘴消费手的结果），同维度不并行。理由：规则式拆解拿不到真实数据流，保守策略避免错误的并行分派。
3. **重试闭环设计（本次关键修复）**：初版存在闭环缺陷——步骤标记 RETRYING 后主循环只遍历一遍批次，重试从未真正执行。修复方案：抽取 `_execute_step_with_retry()` 内层 while 循环，形成 dispatch→feedback→adjust→重新 dispatch 的真闭环，重试上限由 `step.max_retries`（默认 2）控制。这是"执行中枢"与"一次性决策"的本质区别。
4. **失败策略**：重试耗尽后按错误类型分类（timeout/network→RETRY，param→ADJUST，critical/fatal→ABORT，其余→SKIP），规则可解释、可扩展。
5. **执行器异常也纳入反馈闭环**：executor_callback 抛异常不直接崩溃，转为 failed feedback 统一走评估→调整流程。
6. **新增 CONTINUE 动作**：区分"成功继续"与"失败重试"，语义更准确（初版成功时 action=RETRY 是语义错误）。
7. **最终状态分级**：success / partial_success / failed / aborted 四级，比单一 success/failed 更贴近真实执行情况。

## 四、缺口与风险

1. **规则式拆解的覆盖度**：关键词表有限，复合句（如"看完之后告诉我"）会被拆成单步单维度，跨句数据流（step_3 用 step_1 的结果）无法识别——这需要 LLM 级理解或显式的参数传递协议，超出本模块边界。
2. **并行批次未真正并发执行**：batches 表达了"可并行"的划分，但 run_task 内仍是顺序遍历（executor_callback 是同步接口）。真正并发需要线程池/异步接口改造，属集成层决策。
3. **数据流转未实现**：步骤间只有依赖边，没有输入输出管道（如 OCR 结果传给 mouth 播报）。集成时需约定 result 的传递契约。
4. **错误分类依赖 error 字符串**：`_decide_failure_strategy` 基于关键词匹配错误消息，真实执行器应返回结构化错误码，集成时需对齐。
5. **Plan.batches 在 adjust 后不会重新计算**：skip 解除依赖后批次划分保持原样（不影响正确性，因为状态检查在遍历时进行，但批次信息会与实际依赖图略有时滞）。

## 五、建议集成方式

1. **与 decision_brain 的关系**：建议 decision_brain 作为 executor_callback 的内部实现之一（brain 维度步骤由它执行），BrainExecutive 在其上层做拆解/分派/闭环——即"决策脑"负责单步怎么想，"执行中枢"负责整个任务怎么跑。
2. **回调契约**：外部执行器统一返回 `{"step_id": str, "status": "success"|"failed", "result": Any, "error": str}`；建议后续扩展 `error_code` 字段替代字符串匹配。
3. **数据管道建议**：给 Step 增加 `inputs`/`outputs` 字段（当前仅 result），executor 按 step.id 从上游 step.result 取数——最小改动即可打通五维数据流。
4. **路由到 10 个能力模块**：executor_callback 内按 `step.dimension` 分派：eye→deep_vision/ocr_engine、ear→sound_detector/emotion_recognizer、mouth→text_generator/voice_mouth、hand→mouse/keyboard/file_operator、brain→decision_brain。
5. **入口位置**：`five_dimension_ultimate.py` 主流程中，把"一次性决策→串行执行"替换为 `BrainExecutive().run_task(task, dispatcher)`，dispatcher 即上述维度路由器。
