#!/usr/bin/env python3
"""
五维合一系统 - 大脑执行层 × 同步引擎 深度打磨集成版
BrainExecutive(拆解/计划/反馈) + DimensionSyncEngine(并行调度) + 真实能力模块 + 真实语音
"""
import json
import os
import sys
import time
from typing import Dict

_BASE = os.path.dirname(os.path.abspath(__file__))
_CAPS = os.path.join(_BASE, 'caps')
if _CAPS not in sys.path:
    sys.path.insert(0, _CAPS)

from decision_brain import DecisionBrain
from deep_vision import DeepVision
from ocr_engine import OCREngine
from sound_detector import SoundDetector
from emotion_recognizer import EmotionRecognizer
from text_generator import TextGenerator
from voice_mouth import VoiceMouth
from mouse_controller import MouseController
from keyboard_controller import KeyboardController
from file_operator import FileOperator

from brain_executive import BrainExecutive, Dimension as BDim, Step
from dimension_sync import DimensionSyncEngine
from workplace_habits import WorkplaceHabits


class FiveDimDeepPolish:
    """大脑执行层 + 五维同步引擎 深度打磨系统"""

    def __init__(self, voice_enabled: bool = True):
        # 真实能力模块
        self.brain_mod = DecisionBrain()
        self.eye_vision = DeepVision()
        self.eye_ocr = OCREngine()
        self.ear_sound = SoundDetector()
        self.ear_emotion = EmotionRecognizer()
        self.mouth_text = TextGenerator()
        self.mouth_voice = VoiceMouth()
        self.hand_mouse = MouseController()
        self.hand_kb = KeyboardController()
        self.hand_file = FileOperator()
        self.voice_enabled = voice_enabled

        # 大脑执行层 + 同步引擎 + 做人习惯守卫
        self.executive = BrainExecutive(max_retries=2)
        self.sync = DimensionSyncEngine(brain_callback=self._brain_decide)
        self.habits = WorkplaceHabits()  # 认门牌/回读验证/交付点数/变体雷达

        # 各维度真实执行回调（注册进同步引擎）
        self.sync.register('eye', self._do_eye)
        self.sync.register('ear', self._do_ear)
        self.sync.register('mouth', self._do_mouth)
        self.sync.register('hand', self._do_hand)
        self.sync.register('brain', self._do_brain_step)

        # 执行统计
        self.exec_log = []
        self.sync.on_dimension_event(self._on_event)

    # ---------- 真实维度回调 ----------

    def _do_eye(self) -> Dict:
        v = self.eye_vision.analyze_image('screen_capture.png')
        o = self.eye_ocr.extract_text('screen_capture.png', lang='chi_sim')
        return {'scene': v.get('scene_type', 'unknown'),
                'ocr_blocks': o.get('text_blocks_count', 0)}

    def _do_ear(self) -> Dict:
        s = self.ear_sound.detect_events('audio_input.wav')
        e = self.ear_emotion.recognize_emotion('audio_input.wav')
        return {'events': s.get('events_detected', 0),
                'emotion': e.get('emotion', 'unknown')}

    def _do_mouth(self) -> Dict:
        t = self.mouth_text.generate(topic='五维同步播报', style='professional', length='short')
        return {'text_len': t.length}

    def _do_hand(self) -> Dict:
        self.hand_mouse.move_to(120, 240)
        self.hand_mouse.click('left')
        self.hand_kb.type_text('five-dim sync test')
        # 做人习惯：写文件前认门牌，写完回读验证
        target = os.path.join(_BASE, 'sync_output.txt')
        guard_ok, guard_msg = self.habits.guard_path(target)
        if guard_ok:
            w = self.hand_file.write_file(
                target,
                f'五维同步执行 @ {time.strftime("%H:%M:%S")}')
            rb = os.path.isfile(target) and os.path.getsize(target) > 0
            file_status = w.get('status', 'unknown') if rb else 'write_unverified'
        else:
            file_status = 'blocked_by_habits'
        return {'mouse': len(self.hand_mouse.get_history()),
                'keyboard': len(self.hand_kb.get_history()),
                'file': file_status,
                'habits_guard': 'pass' if guard_ok else guard_msg}

    def _do_brain_step(self) -> Dict:
        d = self.brain_mod.analyze({'task': '同步引擎脑步骤', 'complexity': 'low'})
        return {'action': d.action, 'confidence': d.confidence}

    def _brain_decide(self, perception: Dict) -> Dict:
        """同步引擎决策阶段回调：综合感知结果决策"""
        d = self.brain_mod.analyze({
            'task': '五维同步周期', 'complexity': 'medium',
            'perception': perception})
        return {'action': d.action, 'confidence': d.confidence}

    def _on_event(self, dim: str, status, result):
        self.exec_log.append(f"[{time.strftime('%H:%M:%S')}] {dim} -> {status.value}")

    # ---------- 集成测试 ----------

    def say(self, text: str, style: str = 'professional') -> Dict:
        if not self.voice_enabled:
            return {'status': 'skipped'}
        return self.mouth_voice.speak(text, style=style)

    def test_sync_cycle(self) -> Dict:
        """测试 1: 完整同步周期（感知并行→决策→行动→表达）"""
        print('\n' + '=' * 60)
        print('测试 1: 五维同步周期（真实模块 + 并行感知）')
        print('=' * 60)
        r = self.sync.execute_cycle(perception_phase=True)
        tl = r.get('timeline', {})
        phases = tl.get('phases', [])
        total = tl.get('total_duration', 0)
        print(f"  周期完成: {r.get('status')} | 总耗时 {total:.3f}s")
        for p in phases:
            tag = '并行' if p.get('parallel') else '串行'
            print(f"    {p.get('name')}: {p.get('duration', 0):.3f}s [{tag}]")
        # 感知并行验证
        perc = [p for p in phases if '感知' in str(p.get('name', ''))]
        speedup = None
        if perc:
            pd = perc[0].get('duration', 0)
            eye_d = self.sync._dimensions['eye'].last_duration or 0
            ear_d = self.sync._dimensions['ear'].last_duration or 0
            serial = eye_d + ear_d
            if pd > 0 and serial > 0:
                speedup = serial / pd
                print(f"  感知并行: {pd:.3f}s vs 串行 {serial:.3f}s → 加速比 {speedup:.2f}x")
        return {'ok': r.get('status') == 'success', 'speedup': speedup, 'total': total}

    def test_executive_dag(self, task: str) -> Dict:
        """测试 2: 大脑执行层拆解 → 同步引擎 DAG 并行执行"""
        print('\n' + '=' * 60)
        print(f'测试 2: 大脑执行层 × 同步引擎（任务: {task}）')
        print('=' * 60)
        # 1) 拆解
        dec = self.executive.decompose_task(task)
        steps = dec['steps']
        print(f"  拆解: {dec['step_count']} 步")
        for s in steps:
            print(f"    [{s.id}] {s.dimension.value}: {s.description[:24]}"
                  f" 依赖:{s.depends_on or '无'}")
        # 2) 转换为同步引擎 DAG 格式
        dag = [{'id': s.id,
                'dimension': s.dimension.value,
                'depends_on': list(s.depends_on)} for s in steps]
        # 3) DAG 并行执行
        r = self.sync.execute_steps(dag)
        tl = r.get('timeline', {})
        print(f"  执行: {r.get('executed_count')}/{r.get('total_steps')} | "
              f"状态 {r.get('status')} | 耗时 {tl.get('total_duration', 0):.3f}s")
        for p in tl.get('phases', []):
            tag = '并行' if p.get('parallel') else '串行'
            print(f"    {p.get('name')}: {p.get('duration', 0):.3f}s [{tag}]")
        return {'ok': r.get('status') == 'success' and r.get('executed_count') == len(steps),
                'steps': r.get('executed_count'), 'total': tl.get('total_duration', 0)}

    def test_feedback_loop(self) -> Dict:
        """测试 3: 反馈闭环（失败→重试→恢复）"""
        print('\n' + '=' * 60)
        print('测试 3: 大脑执行层反馈闭环（失败重试）')
        print('=' * 60)

        def flaky_executor(step: Step) -> Dict:
            # step_1 首次失败，重试成功 —— 验证 retry 闭环
            if step.id == 'step_1' and step.retries == 0:
                return {'step_id': step.id, 'status': 'failed', 'error': 'network timeout'}
            return {'step_id': step.id, 'status': 'success', 'result': 'ok'}

        r = self.executive.run_task('打开文件读取内容然后播报', flaky_executor)
        retried = any('重试' in l for l in r.get('log', []))
        print(f"  状态: {r.get('status')} | 完成 {r.get('completed_steps')}/"
              f"{r.get('total_steps')} | 反馈 {r.get('feedback_count')} 次")
        print(f"  重试机制触发: {'YES' if retried else 'NO'}")
        return {'ok': r.get('status') == 'success' and retried}

    def run_all(self) -> Dict:
        print('🧠 五维合一 · 大脑执行层 × 同步引擎 深度打磨')
        self.say('深度打磨开始。大脑执行层与五维同步引擎，联动测试。', 'professional')

        t1 = self.test_sync_cycle()
        t2 = self.test_executive_dag('截图识别文字，监听环境声音，整理后写文件并播报结果')
        t3 = self.test_feedback_loop()

        all_ok = t1['ok'] and t2['ok'] and t3['ok']
        print('\n' + '=' * 60)
        print('深度打磨总判定:', '✅ 全部通过' if all_ok else '⚠️ 部分未过')
        print(f"  同步周期:{'✅' if t1['ok'] else '❌'}"
              f"{'(加速比 %.2fx)' % t1['speedup'] if t1.get('speedup') else ''}"
              f"  执行层DAG:{'✅' if t2['ok'] else '❌'}({t2.get('steps')}步)"
              f"  反馈闭环:{'✅' if t3['ok'] else '❌'}")
        print('=' * 60)

        self.say('深度打磨完成。脑指挥，眼耳并行感知，手脚协同执行，五维同步如一。',
                 'warm')
        return {'all_ok': all_ok, 'sync': t1, 'dag': t2, 'feedback': t3,
                'events': len(self.exec_log)}


if __name__ == '__main__':
    system = FiveDimDeepPolish(voice_enabled=True)
    final = system.run_all()
    out = os.path.join(_BASE, 'deep_polish_result.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'all_ok': final['all_ok'],
                   'sync_speedup': final['sync'].get('speedup'),
                   'dag_steps': final['dag'].get('steps'),
                   'events_count': final['events']}, f, indent=2, ensure_ascii=False)
    print(f"\n📄 结果已保存: {out}")
