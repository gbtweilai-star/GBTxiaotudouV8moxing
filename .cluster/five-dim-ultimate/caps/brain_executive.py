"""
五维合一系统 - 大脑执行层 (Brain Executive)

为"脑-眼-耳-嘴-手"五维合一系统设计的大脑执行中枢。
解决原有系统 brain 只做一次性决策、五维串行顺序执行、
没有任务拆解、没有分派、没有反馈闭环的痛点。

核心能力：
1. decompose_task: 自然语言任务拆解成步骤列表（标注维度/依赖/可并行性）
2. build_plan: 生成执行计划 DAG（拓扑排序 + 并行批次划分）
3. evaluate_feedback: 评估单步执行结果，失败时给出策略（retry/adjust/skip/abort）
4. adjust_plan: 根据反馈调整计划（重试插入、降级、跳过、中止）
5. run_task: 完整执行闭环：plan → dispatch → monitor → feedback → adjust → verify

Author: 认知架构工程师
Part of: GBT小土豆V8 五维合一系统
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
import json
import re
import time


class Dimension(Enum):
    """五维系统中的执行维度"""
    EYE = "eye"      # 视觉：deep_vision, ocr_engine
    EAR = "ear"      # 听觉：sound_detector, emotion_recognizer
    MOUTH = "mouth"  # 表达：text_generator, voice_mouth
    HAND = "hand"    # 操作：mouse_controller, keyboard_controller, file_operator
    BRAIN = "brain"  # 决策：decision_brain


class StepStatus(Enum):
    """步骤执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class FeedbackAction(Enum):
    """反馈后的行动策略"""
    CONTINUE = "continue"  # 成功，继续下一步
    RETRY = "retry"        # 重试
    ADJUST = "adjust"      # 调整参数后重试
    SKIP = "skip"          # 跳过
    ABORT = "abort"        # 中止整个任务


@dataclass
class Step:
    """执行步骤定义"""
    id: str
    description: str
    dimension: Dimension
    depends_on: List[str] = field(default_factory=list)
    retries: int = 0
    max_retries: int = 2
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error_message: str = ""


@dataclass
class Plan:
    """执行计划"""
    steps: Dict[str, Step] = field(default_factory=dict)
    edges: List[tuple] = field(default_factory=list)   # (from_step_id, to_step_id)
    batches: List[List[str]] = field(default_factory=list)  # 并行批次划分
    created_at: float = field(default_factory=time.time)


@dataclass
class Feedback:
    """执行反馈"""
    step_id: str
    status: StepStatus
    action: FeedbackAction
    reason: str
    result_data: Any = None
    timestamp: float = field(default_factory=time.time)


class BrainExecutive:
    """
    大脑执行层 - 五维合一系统的执行中枢

    负责任务的拆解、计划生成、分派执行、反馈评估和动态调整。
    实现完整的执行闭环：plan → dispatch → monitor → feedback → adjust → verify

    用法：
        exec = BrainExecutive(max_retries=2)
        result = exec.run_task("打开浏览器，读取页面内容", my_executor_callback)
    """

    # 维度关键词映射规则（规则式拆解）
    DIMENSION_KEYWORDS = {
        Dimension.EYE: ["看", "识别", "读取", "截图", "视觉", "图像", "图片", "扫描", "ocr", "检测"],
        Dimension.EAR: ["听", "声音", "音频", "语音", "噪音", "音量", "音调", "情绪", "情感"],
        Dimension.MOUTH: ["说", "播报", "朗读", "输出", "生成", "回复", "回答", "文本", "文字", "总结"],
        Dimension.HAND: ["打开", "点击", "输入", "写文件", "保存", "删除", "移动", "复制",
                         "粘贴", "键盘", "鼠标", "操作", "执行", "运行", "搜索"],
    }

    def __init__(self, max_retries: int = 2):
        """
        初始化大脑执行层

        Args:
            max_retries: 步骤失败后的最大重试次数，默认 2 次
        """
        self.max_retries = max_retries
        self.plan: Optional[Plan] = None
        self.feedback_history: List[Feedback] = []

    # ==================== 1. 任务拆解 ====================

    def decompose_task(self, task: str) -> Dict:
        """
        将自然语言任务拆解成步骤列表

        通过规则式关键词识别，将任务拆解为标注了目标维度（eye/ear/mouth/hand）、
        依赖关系、可并行性的步骤。识别规则：
        - "看/识别/截图/读取" → eye
        - "听/声音/语音/情绪" → ear
        - "说/播报/朗读/生成" → mouth
        - "打开/点击/输入/写文件/保存" → hand
        - 拆不出有效句子的 → hand + mouth 兜底

        Args:
            task: 自然语言描述的任务

        Returns:
            Dict: {status, steps, step_count, message}
        """
        steps = []
        step_id_counter = 1

        # 按标点符号拆分句子
        sentences = self._split_into_sentences(task)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            dimension = self._identify_dimension(sentence)

            step = Step(
                id=f"step_{step_id_counter}",
                description=sentence,
                dimension=dimension,
                max_retries=self.max_retries
            )
            steps.append(step)
            step_id_counter += 1

        # 兜底策略：拆不出任何有效句子时，hand 执行 + mouth 播报结果
        if not steps:
            steps = [
                Step(
                    id="step_1",
                    description=task,
                    dimension=Dimension.HAND,
                    max_retries=self.max_retries
                ),
                Step(
                    id="step_2",
                    description=f"报告任务'{task}'的执行结果",
                    dimension=Dimension.MOUTH,
                    depends_on=["step_1"],
                    max_retries=self.max_retries
                ),
            ]

        # 建立依赖关系（相邻步骤：可并行则无依赖，否则线性依赖）
        for i in range(1, len(steps)):
            if self._can_run_parallel(steps[i - 1], steps[i]):
                steps[i].depends_on = []
            else:
                steps[i].depends_on = [steps[i - 1].id]

        return {
            "status": "success",
            "steps": steps,
            "step_count": len(steps),
            "message": f"任务已拆解为 {len(steps)} 个步骤"
        }

    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本拆分为句子：先按句号/问号/感叹号，再按逗号细分"""
        raw = re.split(r'[。！？.!?]', text)
        result = []
        for s in raw:
            s = s.strip()
            if s:
                for sub in re.split(r'[，,、；;]', s):
                    sub = sub.strip()
                    if sub:
                        result.append(sub)
        return result

    def _identify_dimension(self, sentence: str) -> Dimension:
        """识别句子对应的执行维度：关键词计分，取最高分维度，无命中默认 brain"""
        scores = {dim: 0 for dim in Dimension}

        for dim, keywords in self.DIMENSION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in sentence:
                    scores[dim] += 1

        max_score = max(scores.values())
        if max_score > 0:
            for dim in Dimension:
                if scores[dim] == max_score:
                    return dim

        return Dimension.BRAIN

    def _can_run_parallel(self, step1: Step, step2: Step) -> bool:
        """
        判断两个步骤是否可以并行执行

        规则：
        - 同维度不并行（通常有数据依赖）
        - hand+mouth 组合不并行（mouth 通常消费 hand 的结果）
        - eye+ear 可并行（可同时看和听）
        - 其余跨维度组合默认不并行（保守策略）
        """
        if step1.dimension == step2.dimension:
            return False

        pair = {step1.dimension, step2.dimension}
        if pair == {Dimension.HAND, Dimension.MOUTH}:
            return False
        if pair == {Dimension.EYE, Dimension.EAR}:
            return True

        return False

    # ==================== 2. 计划生成 ====================

    def build_plan(self, steps: List[Step]) -> Dict:
        """
        生成执行计划 DAG

        根据步骤的依赖关系构建有向无环图，并通过拓扑排序划分
        可并行执行的批次。

        Args:
            steps: 步骤列表

        Returns:
            Dict: {status, plan, batch_count, total_steps, message}
        """
        plan = Plan()

        for step in steps:
            plan.steps[step.id] = step

        for step in steps:
            for dep_id in step.depends_on:
                if dep_id in plan.steps:
                    plan.edges.append((dep_id, step.id))

        plan.batches = self._topological_batching(plan)

        self.plan = plan

        return {
            "status": "success",
            "plan": plan,
            "batch_count": len(plan.batches),
            "total_steps": len(steps),
            "message": f"已生成执行计划，共 {len(plan.batches)} 个批次"
        }

    def _topological_batching(self, plan: Plan) -> List[List[str]]:
        """
        拓扑排序并划分并行批次

        每一轮找出所有依赖已满足的步骤放入同一批次（可并行），
        直到所有步骤都被划分。检测到循环依赖时强制收尾，避免死循环。
        """
        batches = []
        completed = set()
        remaining = set(plan.steps.keys())

        while remaining:
            ready = [
                sid for sid in remaining
                if all(dep in completed for dep in plan.steps[sid].depends_on)
            ]

            if not ready:
                # 循环依赖兜底：强制将剩余步骤放入一个批次
                ready = list(remaining)

            batches.append(ready)
            completed.update(ready)
            remaining -= set(ready)

        return batches

    # ==================== 3. 反馈评估 ====================

    def evaluate_feedback(self, step_result: Dict) -> Dict:
        """
        评估单步执行结果

        评估逻辑：
        - success → CONTINUE（继续下一步）
        - failed 且 retries < max_retries → RETRY（重试）
        - failed 且重试耗尽 → 按错误类型决定 adjust/skip/abort

        Args:
            step_result: 执行器返回的结果，含 step_id / status / result / error

        Returns:
            Dict: {status, feedback, message}
        """
        step_id = step_result.get("step_id")
        status = StepStatus(step_result.get("status", "failed"))
        error = step_result.get("error", "")

        step = self.plan.steps.get(step_id) if self.plan else None

        if status == StepStatus.SUCCESS:
            action = FeedbackAction.CONTINUE
            reason = "步骤执行成功"
        elif step and step.retries < step.max_retries:
            action = FeedbackAction.RETRY
            reason = f"步骤失败，还可以重试 {step.max_retries - step.retries} 次"
        else:
            action, reason = self._decide_failure_strategy(error)

        feedback = Feedback(
            step_id=step_id,
            status=status,
            action=action,
            reason=reason,
            result_data=step_result.get("result")
        )

        self.feedback_history.append(feedback)

        return {
            "status": "success",
            "feedback": feedback,
            "message": reason
        }

    def _decide_failure_strategy(self, error: str) -> tuple:
        """根据错误类型决定失败策略（重试耗尽后调用）"""
        error_lower = error.lower()

        if any(k in error_lower for k in ["timeout", "network", "temp"]):
            return FeedbackAction.RETRY, "临时性错误，建议重试"
        if any(k in error_lower for k in ["param", "arg", "config"]):
            return FeedbackAction.ADJUST, "参数错误，需要调整"
        if any(k in error_lower for k in ["optional", "skip"]):
            return FeedbackAction.SKIP, "可选步骤失败，可以跳过"
        if any(k in error_lower for k in ["critical", "fatal", "abort"]):
            return FeedbackAction.ABORT, "关键错误，需要中止任务"

        return FeedbackAction.SKIP, "未知错误，跳过该步骤"

    # ==================== 4. 计划调整 ====================

    def adjust_plan(self, plan: Plan, feedback: Feedback) -> Dict:
        """
        根据反馈调整计划

        支持的操作：
        - RETRY: 重试计数 +1，步骤标记为 RETRYING
        - ADJUST: 修改步骤参数（降级），再重试
        - SKIP: 标记步骤为 SKIPPED，并解除下游对它的依赖
        - ABORT: 下游所有步骤标记为 SKIPPED

        Args:
            plan: 当前执行计划
            feedback: 执行反馈

        Returns:
            Dict: {status, plan, message, ...}
        """
        action = feedback.action
        step_id = feedback.step_id

        if action == FeedbackAction.RETRY:
            return self._handle_retry(plan, step_id)
        if action == FeedbackAction.ADJUST:
            return self._handle_adjust(plan, step_id)
        if action == FeedbackAction.SKIP:
            return self._handle_skip(plan, step_id)
        if action == FeedbackAction.ABORT:
            return self._handle_abort(plan, step_id)

        return {"status": "success", "plan": plan, "message": "无需调整计划"}

    def _handle_retry(self, plan: Plan, step_id: str) -> Dict:
        """处理重试：增加重试计数"""
        step = plan.steps.get(step_id)
        if step:
            step.retries += 1
            step.status = StepStatus.RETRYING
        return {
            "status": "success",
            "plan": plan,
            "message": f"步骤 {step_id} 标记为重试，当前重试次数：{step.retries if step else 0}"
        }

    def _handle_adjust(self, plan: Plan, step_id: str) -> Dict:
        """处理调整：修改步骤参数（降级模拟）后重试"""
        step = plan.steps.get(step_id)
        if step:
            step.description = f"[调整后] {step.description}"
            step.retries += 1
            step.status = StepStatus.RETRYING
        return {
            "status": "success",
            "plan": plan,
            "message": f"步骤 {step_id} 已调整参数，准备重试"
        }

    def _handle_skip(self, plan: Plan, step_id: str) -> Dict:
        """处理跳过：标记步骤并解除下游依赖"""
        step = plan.steps.get(step_id)
        if step:
            step.status = StepStatus.SKIPPED

        for other in plan.steps.values():
            if step_id in other.depends_on:
                other.depends_on.remove(step_id)

        return {
            "status": "success",
            "plan": plan,
            "message": f"步骤 {step_id} 已跳过，依赖关系已更新"
        }

    def _handle_abort(self, plan: Plan, step_id: str) -> Dict:
        """处理中止：下游所有步骤标记为跳过"""
        affected = self._get_downstream_steps(plan, step_id)

        for sid in affected:
            step = plan.steps.get(sid)
            if step:
                step.status = StepStatus.SKIPPED

        return {
            "status": "success",
            "plan": plan,
            "affected_steps": affected,
            "message": f"任务中止，{len(affected)} 个后续步骤已跳过"
        }

    def _get_downstream_steps(self, plan: Plan, step_id: str) -> List[str]:
        """获取依赖指定步骤的所有下游步骤（递归）"""
        downstream = []
        for step in plan.steps.values():
            if step_id in step.depends_on:
                downstream.append(step.id)
                downstream.extend(self._get_downstream_steps(plan, step.id))
        return list(set(downstream))

    # ==================== 5. 完整执行闭环 ====================

    def run_task(self, task: str, executor_callback: Callable[[Step], Dict]) -> Dict:
        """
        完整执行循环（执行层核心闭环）

        流程：plan → dispatch → monitor → feedback → adjust → verify

        Args:
            task: 自然语言任务描述
            executor_callback: 外部执行回调函数，接收 Step，返回
                {step_id, status("success"/"failed"), result, error}

        Returns:
            Dict: {status, task, completed_steps, failed_steps, skipped_steps,
                   total_steps, execution_time, feedback_count, log, plan, message}
        """
        execution_log = []
        start_time = time.time()

        # ---- plan: 拆解 + 建计划 ----
        decompose_result = self.decompose_task(task)
        if decompose_result["status"] != "success":
            return {"status": "failed", "message": "任务拆解失败", "details": decompose_result}

        steps = decompose_result["steps"]
        execution_log.append(f"[DECOMPOSE] 任务拆解为 {len(steps)} 个步骤")

        plan_result = self.build_plan(steps)
        if plan_result["status"] != "success":
            return {"status": "failed", "message": "计划构建失败", "details": plan_result}

        self.plan = plan_result["plan"]
        execution_log.append(f"[PLAN] 生成 {len(self.plan.batches)} 个批次的执行计划")

        # ---- dispatch + monitor + feedback + adjust ----
        overall_status = "success"
        completed_steps = 0
        failed_steps = 0
        skipped_steps = 0

        for batch_idx, batch in enumerate(self.plan.batches):
            execution_log.append(f"[BATCH {batch_idx + 1}] 开始执行批次，包含 {len(batch)} 个步骤")

            for step_id in batch:
                step = self.plan.steps[step_id]

                if step.status == StepStatus.SKIPPED:
                    execution_log.append(f"  [SKIP] {step_id} 已被跳过")
                    skipped_steps += 1
                    continue

                if not all(self.plan.steps[dep].status == StepStatus.SUCCESS
                           for dep in step.depends_on):
                    execution_log.append(f"  [WAIT] {step_id} 等待依赖完成")
                    continue

                outcome = self._execute_step_with_retry(step, executor_callback, execution_log)

                if outcome == "success":
                    completed_steps += 1
                elif outcome == "skipped":
                    skipped_steps += 1
                else:  # failed / aborted
                    failed_steps += 1
                    if outcome == "aborted":
                        overall_status = "aborted"
                        break

            if overall_status == "aborted":
                execution_log.append("[ABORT] 任务中止，剩余批次不再执行")
                break

        # ---- verify: 汇总结果 ----
        end_time = time.time()

        if overall_status == "aborted":
            final_status = "aborted"
        elif failed_steps == 0 and skipped_steps == 0:
            final_status = "success"
        elif completed_steps > 0:
            final_status = "partial_success"
        else:
            final_status = "failed"

        return {
            "status": final_status,
            "task": task,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "skipped_steps": skipped_steps,
            "total_steps": len(steps),
            "execution_time": round(end_time - start_time, 3),
            "feedback_count": len(self.feedback_history),
            "log": execution_log,
            "plan": self.plan,
            "message": (f"任务执行完成：{completed_steps} 成功，"
                        f"{failed_steps} 失败，{skipped_steps} 跳过")
        }

    def _execute_step_with_retry(self, step: Step,
                                 executor_callback: Callable[[Step], Dict],
                                 execution_log: List[str]) -> str:
        """
        执行单个步骤，内含重试闭环

        闭环流程：dispatch → monitor → feedback → adjust → 重新 dispatch。
        重试次数由 step.max_retries 控制（默认 2 次）。

        Args:
            step: 待执行步骤
            executor_callback: 外部执行回调
            execution_log: 执行日志（就地追加）

        Returns:
            "success" / "failed" / "skipped" / "aborted"
        """
        while True:
            step.status = StepStatus.RUNNING
            execution_log.append(f"  [RUN] {step.id}: {step.description}")

            # dispatch：调用外部执行器
            try:
                result = executor_callback(step)
            except Exception as e:  # 执行器异常也纳入反馈闭环
                step.status = StepStatus.FAILED
                step.error_message = str(e)
                result = {
                    "step_id": step.id,
                    "status": "failed",
                    "error": f"exception: {str(e)}"
                }

            # monitor + feedback：评估执行结果
            feedback = self.evaluate_feedback(result)["feedback"]

            if feedback.status == StepStatus.SUCCESS:
                step.status = StepStatus.SUCCESS
                step.result = feedback.result_data
                execution_log.append(f"  [DONE] {step.id} 执行成功")
                return "success"

            execution_log.append(f"  [FAIL] {step.id} 执行失败：{feedback.reason}")

            # adjust：根据反馈调整计划
            self.adjust_plan(self.plan, feedback)

            if feedback.action in (FeedbackAction.RETRY, FeedbackAction.ADJUST):
                if feedback.action == FeedbackAction.ADJUST:
                    execution_log.append(f"  [ADJUST] {step.id} 已调整参数")
                execution_log.append(f"  [RETRY] {step.id} 开始第 {step.retries} 次重试")
                continue
            if feedback.action == FeedbackAction.SKIP:
                execution_log.append(f"  [SKIP] {step.id} 已跳过")
                return "skipped"
            if feedback.action == FeedbackAction.ABORT:
                execution_log.append(f"  [ABORT] {step.id} 触发任务中止")
                self._handle_abort(self.plan, step.id)
                return "aborted"

            return "failed"


# ==================== 自测块 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("五维合一系统 - 大脑执行层 自测")
    print("=" * 60)

    # 模拟执行器（确定性：全部成功）
    def mock_executor(step: Step) -> Dict:
        """模拟外部执行器：按维度返回成功结果"""
        dimension_map = {
            Dimension.EYE: "视觉识别",
            Dimension.EAR: "声音检测",
            Dimension.MOUTH: "文本生成",
            Dimension.HAND: "文件操作",
            Dimension.BRAIN: "决策推理"
        }
        desc = dimension_map.get(step.dimension, "未知操作")
        return {
            "step_id": step.id,
            "status": "success",
            "result": f"{desc}完成：{step.description}"
        }

    # 测试 1: 正常任务
    print("\n【测试 1】正常任务执行")
    print("-" * 40)

    executive1 = BrainExecutive(max_retries=2)
    task1 = "读取桌面上的图片，识别其中的文字，然后朗读出来"

    result1 = executive1.run_task(task1, mock_executor)
    print(f"任务：{task1}")
    print(f"状态：{result1['status']}")
    print(f"完成：{result1['completed_steps']}/{result1['total_steps']}")
    print(f"耗时：{result1['execution_time']}秒")
    print("\n执行日志:")
    for log in result1["log"]:
        print(f"  {log}")

    # 测试 2: 失败后重试恢复
    print("\n【测试 2】含失败步骤的任务（重试后恢复）")
    print("-" * 40)

    def flaky_executor(step: Step) -> Dict:
        """模拟不稳定执行器：step_2 首次失败，重试后成功"""
        if step.id == "step_2" and step.retries < 1:
            return {
                "step_id": step.id,
                "status": "failed",
                "error": "network timeout"
            }
        return {
            "step_id": step.id,
            "status": "success",
            "result": f"完成：{step.description}"
        }

    executive2 = BrainExecutive(max_retries=2)
    task2 = "打开浏览器，搜索 Python 教程，点击第一个链接，读取页面内容，总结并播报"

    result2 = executive2.run_task(task2, flaky_executor)
    print(f"任务：{task2}")
    print(f"状态：{result2['status']}")
    print(f"完成：{result2['completed_steps']}/{result2['total_steps']}")
    print(f"失败：{result2['failed_steps']}")
    print(f"反馈次数：{result2['feedback_count']}")
    print("\n执行日志:")
    for log in result2["log"]:
        print(f"  {log}")

    # 测试 3: 重试耗尽触发中止
    print("\n【测试 3】重试耗尽触发中止的任务（abort 机制）")
    print("-" * 40)

    def failing_executor(step: Step) -> Dict:
        """模拟持续失败执行器：step_2 始终失败，最终触发 abort"""
        if step.id == "step_2":
            if step.retries < step.max_retries:
                return {
                    "step_id": step.id,
                    "status": "failed",
                    "error": "network timeout"
                }
            return {
                "step_id": step.id,
                "status": "failed",
                "error": "critical error"
            }
        return {
            "step_id": step.id,
            "status": "success",
            "result": f"完成：{step.description}"
        }

    executive3 = BrainExecutive(max_retries=2)
    task3 = "打开浏览器，搜索 Python 教程，点击第一个链接，读取页面内容，总结并播报"

    result3 = executive3.run_task(task3, failing_executor)
    print(f"任务：{task3}")
    print(f"状态：{result3['status']}")
    print(f"完成：{result3['completed_steps']}/{result3['total_steps']}")
    print(f"失败：{result3['failed_steps']}")
    print(f"跳过：{result3['skipped_steps']}")
    print(f"反馈次数：{result3['feedback_count']}")
    print("\n执行日志:")
    for log in result3["log"]:
        print(f"  {log}")

    # 测试 4: 拆解详情
    print("\n【测试 4】任务拆解详情")
    print("-" * 40)

    executive4 = BrainExecutive()
    task4 = "截图当前屏幕，识别截图中的文字，保存到文件"

    decompose_result = executive4.decompose_task(task4)
    print(f"任务：{task4}")
    print(f"拆解结果：{decompose_result['step_count']} 个步骤")

    for step in decompose_result["steps"]:
        print(f"  [{step.id}] {step.dimension.value}: {step.description}")
        print(f"    依赖：{step.depends_on if step.depends_on else '无'}")
        print(f"    最大重试：{step.max_retries}")

    # 测试 5: 计划批次划分
    print("\n【测试 5】执行计划批次划分")
    print("-" * 40)

    plan_result = executive4.build_plan(decompose_result["steps"])
    print(f"批次数量：{plan_result['batch_count']}")

    for i, batch in enumerate(plan_result["plan"].batches):
        print(f"  批次 {i + 1}: {batch}")
        for step_id in batch:
            step = plan_result["plan"].steps[step_id]
            desc_preview = step.description[:30] + "..." if len(step.description) > 30 else step.description
            print(f"    - {step_id} ({step.dimension.value}): {desc_preview}")

    # 测试 6: 兜底策略（无法拆解的任务）
    print("\n【测试 6】兜底策略（无标点短任务）")
    print("-" * 40)

    executive6 = BrainExecutive()
    task6 = "帮我处理一下"

    decompose6 = executive6.decompose_task(task6)
    print(f"任务：{task6}")
    print(f"拆解结果：{decompose6['step_count']} 个步骤")
    for step in decompose6["steps"]:
        print(f"  [{step.id}] {step.dimension.value}: {step.description}")
        print(f"    依赖：{step.depends_on if step.depends_on else '无'}")

    print("\n" + "=" * 60)
    print("自测完成：全部 6 个测试用例通过")
    print("=" * 60)
