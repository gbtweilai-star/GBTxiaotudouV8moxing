"""
五维同步引擎 (Dimension Sync Engine)

为"脑 - 眼-耳 - 嘴 - 手"五维合一系统提供同步协调能力的核心模块。
解决五维串行执行的痛点，实现状态跟踪、并行协同、事件通知。

Author: 自由的风 · GBT 小土豆 V8
"""

import json
import time
import threading
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed


class DimensionStatus(Enum):
    """维度状态枚举"""
    IDLE = "idle"          # 空闲
    RUNNING = "running"    # 运行中
    DONE = "done"          # 完成
    ERROR = "error"        # 错误


@dataclass
class DimensionState:
    """维度状态数据结构"""
    name: str                    # 维度名称
    status: DimensionStatus      # 当前状态
    last_result: Any = None      # 最后一次执行结果
    last_duration: float = 0.0   # 最后一次执行耗时 (秒)
    error_message: Optional[str] = None  # 错误信息


@dataclass
class PhaseRecord:
    """阶段记录数据结构"""
    name: str                    # 阶段名称
    start: float                 # 开始时间戳
    end: float                   # 结束时间戳
    parallel: bool               # 是否并行执行
    results: Dict[str, Any] = field(default_factory=dict)  # 各维度结果


@dataclass
class CycleTimeline:
    """周期时间线数据结构"""
    cycle_id: int                # 周期 ID
    phases: List[PhaseRecord] = field(default_factory=list)  # 阶段列表
    total_duration: float = 0.0  # 总耗时
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "cycle_id": self.cycle_id,
            "phases": [
                {
                    "name": p.name,
                    "start": p.start,
                    "end": p.end,
                    "duration": p.end - p.start,
                    "parallel": p.parallel,
                    "results": p.results
                }
                for p in self.phases
            ],
            "total_duration": self.total_duration
        }


class DimensionSyncEngine:
    """
    五维同步引擎
    
    协调眼 (eye)、耳 (ear)、嘴 (mouth)、手 (hand) 四个维度的执行，
    脑 (brain) 作为指挥中心不参与注册，通过构造函数传入。
    """
    
    def __init__(self, brain_callback: Optional[Callable[[Dict], Dict]] = None):
        """
        初始化同步引擎
        
        Args:
            brain_callback: 脑的决策回调函数，接收感知结果，返回决策
        """
        self._brain_callback = brain_callback
        self._dimensions: Dict[str, DimensionState] = {}
        self._callbacks: Dict[str, Callable[[], Any]] = {}
        self._event_hooks: List[Callable[[str, DimensionStatus, Any], None]] = []
        self._lock = threading.Lock()
        self._cycle_counter = 0
        self._timeline_history: List[CycleTimeline] = []
        
    def register(self, dimension: str, worker_callback: Callable[[], Any]) -> Dict:
        """
        注册维度执行器
        
        Args:
            dimension: 维度名称 (eye/ear/mouth/hand)
            worker_callback: 该维度的执行回调函数
            
        Returns:
            包含 status 字段的字典
        """
        with self._lock:
            self._dimensions[dimension] = DimensionState(
                name=dimension,
                status=DimensionStatus.IDLE
            )
            self._callbacks[dimension] = worker_callback
            
        return {
            "status": "success",
            "message": f"维度 {dimension} 已注册",
            "dimension": dimension
        }
    
    def on_dimension_event(self, callback: Callable[[str, DimensionStatus, Any], None]) -> Dict:
        """
        注册维度事件钩子（观察者模式）
        
        Args:
            callback: 事件回调函数，参数为 (维度名，新状态，结果)
            
        Returns:
            包含 status 字段的字典
        """
        self._event_hooks.append(callback)
        return {"status": "success", "message": "事件钩子已注册"}
    
    def _notify_event(self, dimension: str, new_status: DimensionStatus, result: Any):
        """触发维度事件通知"""
        for hook in self._event_hooks:
            try:
                hook(dimension, new_status, result)
            except Exception:
                pass  # 事件钩子失败不影响主流程
    
    def _execute_dimension(self, dimension: str) -> Dict:
        """
        执行单个维度
        
        Args:
            dimension: 维度名称
            
        Returns:
            执行结果字典
        """
        if dimension not in self._callbacks:
            return {"error": f"维度 {dimension} 未注册"}
        
        callback = self._callbacks[dimension]
        
        with self._lock:
            self._dimensions[dimension].status = DimensionStatus.RUNNING
        
        start_time = time.time()
        try:
            result = callback()
            duration = time.time() - start_time
            
            with self._lock:
                self._dimensions[dimension].status = DimensionStatus.DONE
                self._dimensions[dimension].last_result = result
                self._dimensions[dimension].last_duration = duration
            
            self._notify_event(dimension, DimensionStatus.DONE, result)
            return {"success": True, "result": result, "duration": duration}
            
        except Exception as e:
            duration = time.time() - start_time
            
            with self._lock:
                self._dimensions[dimension].status = DimensionStatus.ERROR
                self._dimensions[dimension].last_duration = duration
                self._dimensions[dimension].error_message = str(e)
            
            self._notify_event(dimension, DimensionStatus.ERROR, str(e))
            return {"success": False, "error": str(e), "duration": duration}
    
    def _reset_dimensions(self, dimensions: List[str]):
        """重置维度状态为空闲"""
        with self._lock:
            for dim in dimensions:
                if dim in self._dimensions:
                    self._dimensions[dim].status = DimensionStatus.IDLE
                    self._dimensions[dim].error_message = None
    
    def execute_cycle(self, perception_phase: bool = True) -> Dict:
        """
        执行一个完整的同步周期
        
        阶段流程:
        1. 感知阶段 (并行): eye 和 ear 同时执行
        2. 决策阶段：脑综合感知结果决定行动
        3. 行动阶段：hand 执行动作
        4. 表达阶段：mouth 播报结果
        
        Args:
            perception_phase: 是否包含感知阶段
            
        Returns:
            包含 status 和时间线信息的字典
        """
        self._cycle_counter += 1
        cycle_id = self._cycle_counter
        timeline = CycleTimeline(cycle_id=cycle_id)
        cycle_start = time.time()
        
        try:
            # ========== 阶段 1: 感知阶段 (并行) ==========
            if perception_phase:
                phase_start = time.time()
                perception_results = {}
                
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures = {
                        executor.submit(self._execute_dimension, dim): dim
                        for dim in ["eye", "ear"]
                        if dim in self._callbacks
                    }
                    
                    for future in as_completed(futures):
                        dim = futures[future]
                        perception_results[dim] = future.result()
                
                phase_record = PhaseRecord(
                    name="感知阶段",
                    start=phase_start,
                    end=time.time(),
                    parallel=True,
                    results=perception_results
                )
                timeline.phases.append(phase_record)
                
                # 脑决策
                if self._brain_callback:
                    brain_result = self._brain_callback(perception_results)
                else:
                    brain_result = {"action": "default", "target": None}
            else:
                brain_result = {"action": "skip", "target": None}
                perception_results = {}
            
            # ========== 阶段 2: 决策阶段 ==========
            decision_start = time.time()
            decision_result = {"decision": brain_result}
            phase_record = PhaseRecord(
                name="决策阶段",
                start=decision_start,
                end=time.time(),
                parallel=False,
                results={"brain": decision_result}
            )
            timeline.phases.append(phase_record)
            
            # ========== 阶段 3: 行动阶段 ==========
            action_start = time.time()
            action_results = {}
            
            if "hand" in self._callbacks:
                action_results["hand"] = self._execute_dimension("hand")
            
            phase_record = PhaseRecord(
                name="行动阶段",
                start=action_start,
                end=time.time(),
                parallel=False,
                results=action_results
            )
            timeline.phases.append(phase_record)
            
            # ========== 阶段 4: 表达阶段 ==========
            expression_start = time.time()
            expression_results = {}
            
            if "mouth" in self._callbacks:
                # 各阶段结果已汇总在时间线 results 字段中，mouth 可通过 get_status() 回溯
                expression_results["mouth"] = self._execute_dimension("mouth")
            
            phase_record = PhaseRecord(
                name="表达阶段",
                start=expression_start,
                end=time.time(),
                parallel=False,
                results=expression_results
            )
            timeline.phases.append(phase_record)
            
            timeline.total_duration = time.time() - cycle_start
            self._timeline_history.append(timeline)
            
            # 重置维度状态
            self._reset_dimensions(["eye", "ear", "hand", "mouth"])
            
            return {
                "status": "success",
                "cycle_id": cycle_id,
                "timeline": timeline.to_dict()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "cycle_id": cycle_id
            }
    
    def execute_steps(self, steps: List[Dict]) -> Dict:
        """
        按依赖 DAG 执行任意步骤集
        
        步骤格式:
        {
            "id": "步骤 ID",
            "dimension": "维度名称",
            "depends_on": ["依赖的步骤 ID 列表"]
        }
        
        同层无依赖的步骤会并行执行。
        
        Args:
            steps: 步骤列表
            
        Returns:
            包含 status 和执行结果的字典
        """
        if not steps:
            return {"status": "success", "message": "无步骤需要执行"}
        
        results = {}
        executed = set()
        timeline_phases = []
        layer_index = 0
        total_start = time.time()
        
        # 构建依赖图
        step_map = {s["id"]: s for s in steps}
        
        while len(executed) < len(steps):
            # 找出当前可执行的步骤（依赖已满足）
            ready_steps = []
            for step_id, step in step_map.items():
                if step_id in executed:
                    continue
                deps = step.get("depends_on", [])
                if all(d in executed for d in deps):
                    ready_steps.append(step)
            
            if not ready_steps:
                break  # 防止循环依赖
            
            # 并行执行当前层
            phase_start = time.time()
            phase_results = {}
            
            with ThreadPoolExecutor(max_workers=len(ready_steps)) as executor:
                futures = {
                    executor.submit(self._execute_dimension, step["dimension"]): step["id"]
                    for step in ready_steps
                }
                
                for future in as_completed(futures):
                    step_id = futures[future]
                    phase_results[step_id] = future.result()
                    executed.add(step_id)
                    results[step_id] = phase_results[step_id]
            
            # 记录阶段
            layer_index += 1
            phase_record = PhaseRecord(
                name=f"执行层-{layer_index}",
                start=phase_start,
                end=time.time(),
                parallel=len(ready_steps) > 1,
                results=phase_results
            )
            timeline_phases.append(phase_record)
        
        total_duration = time.time() - total_start
        
        return {
            "status": "success" if len(executed) == len(steps) else "partial",
            "executed_count": len(executed),
            "total_steps": len(steps),
            "results": results,
            "timeline": {
                "phases": [
                    {
                        "name": p.name,
                        "duration": p.end - p.start,
                        "parallel": p.parallel
                    }
                    for p in timeline_phases
                ],
                "total_duration": total_duration
            }
        }
    
    def get_status(self) -> Dict:
        """
        获取全部维度当前状态 + 最近一次周期的时间线
        
        Returns:
            包含所有维度状态和时间线的字典
        """
        with self._lock:
            dimensions_status = {
                name: {
                    "status": state.status.value,
                    "last_result": state.last_result,
                    "last_duration": state.last_duration,
                    "error_message": state.error_message
                }
                for name, state in self._dimensions.items()
            }
        
        recent_timeline = None
        if self._timeline_history:
            recent_timeline = self._timeline_history[-1].to_dict()
        
        return {
            "status": "ok",
            "dimensions": dimensions_status,
            "cycle_count": self._cycle_counter,
            "recent_cycle_timeline": recent_timeline
        }


# ========== 自测块 ==========
if __name__ == "__main__":
    import random
    
    print("=" * 60)
    print("五维同步引擎 自测")
    print("=" * 60)
    
    # 模拟事件钩子
    event_log = []
    def on_event(dim: str, status: DimensionStatus, result: Any):
        event_log.append((dim, status.value, time.time()))
        print(f"  [事件] {dim} -> {status.value}")
    
    # 创建引擎
    engine = DimensionSyncEngine(
        brain_callback=lambda perception: {
            "action": "analyze",
            "confidence": random.uniform(0.7, 0.95),
            "input_summary": {k: "processed" for k in perception.keys()}
        }
    )
    engine.on_dimension_event(on_event)
    
    # 注册模拟维度回调
    def make_mock_callback(name: str):
        def callback():
            # 模拟 50-150ms 耗时
            delay = random.uniform(0.05, 0.15)
            time.sleep(delay)
            return {
                "source": name,
                "data": f"{name}_result_{int(time.time()*1000)}",
                "processed_at": time.time()
            }
        return callback
    
    engine.register("eye", make_mock_callback("eye"))
    engine.register("ear", make_mock_callback("ear"))
    engine.register("mouth", make_mock_callback("mouth"))
    engine.register("hand", make_mock_callback("hand"))
    
    print("\n[已注册维度] eye, ear, mouth, hand\n")
    
    # ========== 测试 1: 执行 2 个完整周期 ==========
    print("-" * 60)
    print("测试 1: 执行 2 个完整同步周期")
    print("-" * 60)
    
    parallel_times = []
    sequential_sum = []
    
    for i in range(2):
        print(f"\n>>> 周期 {i+1} 开始...")
        result = engine.execute_cycle(perception_phase=True)
        
        if result["status"] == "success":
            timeline = result["timeline"]
            total = timeline["total_duration"]
            
            # 提取感知阶段数据
            perception_phase = next(p for p in timeline["phases"] if p["name"] == "感知阶段")
            perception_time = perception_phase["duration"]
            parallel_times.append(perception_time)
            
            # 计算串行总和
            eye_time = perception_phase["results"].get("eye", {}).get("duration", 0)
            ear_time = perception_phase["results"].get("ear", {}).get("duration", 0)
            seq_sum = eye_time + ear_time
            sequential_sum.append(seq_sum)
            
            print(f"  总耗时：{total:.3f}s")
            for phase in timeline["phases"]:
                parallel_mark = " [并行]" if phase["parallel"] else ""
                print(f"  - {phase['name']}: {phase['duration']:.3f}s{parallel_mark}")
        else:
            print(f"  周期 {i+1} 失败：{result.get('error')}")
    
    # ========== 测试 2: DAG 步骤集 ==========
    print("\n" + "-" * 60)
    print("测试 2: DAG 步骤集执行 (含并行验证)")
    print("-" * 60)
    
    dag_steps = [
        {"id": "step1", "dimension": "eye", "depends_on": []},
        {"id": "step2", "dimension": "ear", "depends_on": []},
        {"id": "step3", "dimension": "hand", "depends_on": ["step1", "step2"]},
        {"id": "step4", "dimension": "mouth", "depends_on": ["step3"]},
    ]
    
    print("\n>>> DAG 步骤结构:")
    print("  step1(eye) ─┐")
    print("               ├──> step3(hand) ─> step4(mouth)")
    print("  step2(ear) ─┘")
    print("\n>>> 执行中...")
    
    dag_result = engine.execute_steps(dag_steps)
    
    if dag_result["status"] in ["success", "partial"]:
        print(f"  执行完成：{dag_result['executed_count']}/{dag_result['total_steps']} 步骤")
        print(f"  总耗时：{dag_result['timeline']['total_duration']:.3f}s")
        
        for phase in dag_result["timeline"]["phases"]:
            parallel_mark = " [并行]" if phase["parallel"] else ""
            print(f"  - {phase['name']}: {phase['duration']:.3f}s{parallel_mark}")
    else:
        print(f"  DAG 执行失败：{dag_result.get('error')}")
    
    # ========== 并行性验证 ==========
    print("\n" + "=" * 60)
    print("并行性验证结果")
    print("=" * 60)
    
    avg_parallel = sum(parallel_times) / len(parallel_times)
    avg_sequential = sum(sequential_sum) / len(sequential_sum)
    speedup = avg_sequential / avg_parallel if avg_parallel > 0 else 1
    
    print(f"\n感知阶段平均并行耗时：{avg_parallel:.3f}s")
    print(f"感知阶段平均串行耗时 (eye+ear): {avg_sequential:.3f}s")
    print(f"加速比：{speedup:.2f}x")
    
    if avg_parallel < avg_sequential:
        print(f"\n[OK] 并行验证通过：并行耗时 < 串行耗时")
        savings_pct = (1 - avg_parallel / avg_sequential) * 100
        print(f"  节省时间：{avg_sequential - avg_parallel:.3f}s ({savings_pct:.1f}%)")
    else:
        print(f"\n[FAIL] 并行验证未通过")
    
    # ========== 最终状态 ==========
    print("\n" + "=" * 60)
    print("最终系统状态")
    print("=" * 60)
    
    status = engine.get_status()
    print(f"\n周期计数：{status['cycle_count']}")
    print("\n维度状态:")
    for dim, info in status["dimensions"].items():
        print(f"  {dim}: {info['status']} (最后耗时：{info['last_duration']:.3f}s)")
    
    print(f"\n事件触发次数：{len(event_log)}")
    
    print("\n" + "=" * 60)
    print("自测完成")
    print("=" * 60)
