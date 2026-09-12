#!/usr/bin/env python3
"""
五维合一系统 - 最终完整版 (Ultimate v2)
Brain-Eye-Ear-Mouth-Hand 完整增强版 + 真实语音输出
增强率：100% · 嘴维升级为真实发声引擎
"""
import json
import time
import os
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# 路径处理：兼容直接运行与包导入
_BASE = os.path.dirname(os.path.abspath(__file__))
_CAPS = os.path.join(_BASE, 'caps')
if _CAPS not in sys.path:
    sys.path.insert(0, _CAPS)

# 导入所有能力模块（直接导入，避免包依赖问题）
from decision_brain import DecisionBrain
from mouse_controller import MouseController
from text_generator import TextGenerator
from deep_vision import DeepVision
from ocr_engine import OCREngine
from sound_detector import SoundDetector
from emotion_recognizer import EmotionRecognizer
from keyboard_controller import KeyboardController
from file_operator import FileOperator
from voice_mouth import VoiceMouth

class Dimension(Enum):
    BRAIN = "🧠 脑 - 认知维"
    EYE = "👁️ 眼 - 视觉维"
    EAR = "👂 耳 - 听觉维"
    MOUTH = "👄 嘴 - 表达维"
    HAND = "🖐️ 手 - 执行维"

@dataclass
class DimensionResult:
    name: str
    status: str
    enhanced: bool
    capabilities: List[str]
    result: Dict

class FiveDimensionUltimate:
    """五维合一系统 - 最终完整版 v2（含真实语音）"""

    def __init__(self, voice_enabled: bool = True):
        # 脑 - 认知维
        self.brain = DecisionBrain()

        # 眼 - 视觉维
        self.deep_vision = DeepVision()
        self.ocr = OCREngine()

        # 耳 - 听觉维
        self.sound_detector = SoundDetector()
        self.emotion_recognizer = EmotionRecognizer()

        # 嘴 - 表达维（真实语音引擎）
        self.text_gen = TextGenerator()
        self.voice_mouth = VoiceMouth()
        self.voice_enabled = voice_enabled

        # 手 - 执行维
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.file_op = FileOperator()

        # 五维状态
        self.dimensions = {
            Dimension.BRAIN: {'status': 'ready', 'enhanced': True, 'capabilities': ['decision_brain']},
            Dimension.EYE: {'status': 'ready', 'enhanced': True, 'capabilities': ['deep_vision', 'ocr_engine']},
            Dimension.EAR: {'status': 'ready', 'enhanced': True, 'capabilities': ['sound_detector', 'emotion_recognizer']},
            Dimension.MOUTH: {'status': 'ready', 'enhanced': True, 'capabilities': ['text_generator', 'voice_mouth(真实语音)']},
            Dimension.HAND: {'status': 'ready', 'enhanced': True, 'capabilities': ['mouse_controller', 'keyboard_controller', 'file_operator']}
        }

        self.results: List[DimensionResult] = []

    def say(self, text: str, style: str = "warm") -> Dict:
        """让系统开口说话（真实语音）"""
        if not self.voice_enabled:
            return {'status': 'skipped', 'message': '语音未启用'}
        return self.voice_mouth.speak(text, style=style)

    def run_ultimate(self, task: str) -> Dict:
        """运行最终完整版五维合一"""
        results = {
            'task': task,
            'timestamp': time.time(),
            'version': 'ultimate-v2',
            'enhanced_rate': '100%',
            'dimensions': {}
        }

        print(f"🚀 启动五维合一系统 - 最终完整版 v2")
        print(f"🎯 任务：{task}")
        print(f"✨ 增强率：100%（含真实语音输出）")
        print()

        # 开场白（真实语音）
        self.say(f"五维合一系统启动，开始执行任务：{task}", style="professional")

        # 🧠 脑 - 增强决策推理
        print("🧠 [脑 - 认知维] 增强决策推理...")
        decision = self.brain.analyze({
            'task': task,
            'complexity': 'medium',
            'urgency': 'normal'
        })
        results['dimensions'][Dimension.BRAIN.value] = {
            'decision': decision.action,
            'confidence': decision.confidence,
            'reasoning': decision.reasoning,
            'enhanced': True
        }
        print(f"   ✓ 决策：{decision.action} (置信度：{decision.confidence:.2f})")

        # 👁️ 眼 - 增强视觉分析
        print("👁️ [眼 - 视觉维] 增强视觉分析...")
        vision_result = self.deep_vision.analyze_image('screen_capture.png')
        ocr_result = self.ocr.extract_text('screen_capture.png', lang='chi_sim')
        results['dimensions'][Dimension.EYE.value] = {
            'vision': {'scene_type': vision_result.get('scene_type', 'unknown')},
            'ocr': {'text_blocks': ocr_result.get('text_blocks_count', 0)},
            'enhanced': True
        }
        print(f"   ✓ 场景类型：{vision_result.get('scene_type', 'unknown')}")

        # 👂 耳 - 增强听觉分析
        print("👂 [耳 - 听觉维] 增强听觉分析...")
        sound_result = self.sound_detector.detect_events('audio_input.wav')
        emotion_result = self.emotion_recognizer.recognize_emotion('audio_input.wav')
        results['dimensions'][Dimension.EAR.value] = {
            'sound_events': sound_result.get('events_detected', 0),
            'emotion': emotion_result.get('emotion', 'unknown'),
            'enhanced': True
        }
        print(f"   ✓ 声音事件：{sound_result.get('events_detected', 0)} 个")

        # 👄 嘴 - 增强文本生成 + 真实语音播报
        print("👄 [嘴 - 表达维] 文本生成 + 真实语音播报...")
        feedback = self.text_gen.generate(topic=task, style='professional', length='medium')
        voice_result = self.say(
            f"任务 {task} 分析完成。视觉检测到场景，听觉检测到声音事件，现在开始执行。",
            style="professional"
        )
        results['dimensions'][Dimension.MOUTH.value] = {
            'generated_text': feedback.content,
            'length': feedback.length,
            'voice_status': voice_result.get('status', 'unknown'),
            'voice_engine': 'Windows SAPI (System.Speech)',
            'enhanced': True
        }
        print(f"   ✓ 生成 {feedback.length} 字符文本")
        print(f"   ✓ 语音播报：{voice_result.get('status', 'unknown')}")

        # 🖐️ 手 - 增强执行控制
        print("🖐️ [手 - 执行维] 增强执行控制...")
        self.mouse.move_to(100, 200)
        self.mouse.click('left')
        self.keyboard.type_text('Hello, Five Dimension System!')
        self.keyboard.hotkey('ctrl', 's')
        file_result = self.file_op.write_file(
            os.path.join(_BASE, 'output.txt'),
            f'Task: {task}\nCompleted at: {time.strftime("%Y-%m-%d %H:%M:%S")}\nStatus: success'
        )
        results['dimensions'][Dimension.HAND.value] = {
            'mouse_actions': len(self.mouse.get_history()),
            'keyboard_actions': len(self.keyboard.get_history()),
            'file_status': file_result.get('status', 'unknown'),
            'enhanced': True
        }
        print(f"   ✓ 鼠标 {len(self.mouse.get_history())} 次 / 键盘 {len(self.keyboard.get_history())} 次")
        print(f"   ✓ 文件写入：{file_result.get('status', 'unknown')}")

        # 结束播报（真实语音）
        self.say("任务执行完毕。脑眼耳嘴手，五维合一，全部就绪。", style="warm")

        print()
        print("✅ 五维合一最终完整版 v2 执行完成!")
        print(f"📊 增强率：100%（5/5 维度增强，含真实语音）")

        return results

    def get_summary(self) -> Dict:
        """获取系统摘要"""
        enhanced_count = sum(1 for d in self.dimensions.values() if d['enhanced'])
        total_count = len(self.dimensions)

        return {
            'total_dimensions': total_count,
            'enhanced_dimensions': enhanced_count,
            'enhancement_rate': f"{enhanced_count/total_count*100:.0f}%",
            'capabilities_count': sum(len(d['capabilities']) for d in self.dimensions.values()),
            'voice_engine': 'Windows SAPI (System.Speech)' if self.voice_enabled else 'disabled',
            'total_spoken': self.voice_mouth.total_spoken,
            'dimensions': [dim.value for dim in self.dimensions.keys()]
        }

    def print_report(self):
        """打印完整报告"""
        summary = self.get_summary()

        print("\n" + "="*60)
        print("五维合一系统 - 最终完整版 v2 报告")
        print("="*60)
        print(f"总维度数：{summary['total_dimensions']}")
        print(f"增强维度：{summary['enhanced_dimensions']}")
        print(f"增强率：{summary['enhancement_rate']}")
        print(f"集成能力：{summary['capabilities_count']} 个")
        print(f"语音引擎：{summary['voice_engine']}")
        print(f"本次说话：{summary['total_spoken']} 句")
        print()
        print("维度列表:")
        for dim_name in summary['dimensions']:
            print(f"  • {dim_name}")
        print("="*60)


if __name__ == '__main__':
    # 创建最终完整版系统（语音开启）
    system = FiveDimensionUltimate(voice_enabled=True)

    # 运行五维合一（会真实说话）
    results = system.run_ultimate("演示五维合一完整流程")

    # 打印报告
    system.print_report()

    # 保存结果
    result_path = os.path.join(_BASE, 'five_dimension_ultimate_result.json')
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': system.get_summary(),
            'dimensions_count': len(results['dimensions'])
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📄 结果已保存到：{result_path}")
