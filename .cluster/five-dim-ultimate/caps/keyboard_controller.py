#!/usr/bin/env python3
"""
Keyboard Controller - 键盘控制能力
为五维合一系统提供精确的键盘操作
"""
import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class ActionType(Enum):
    """键盘操作类型"""
    TYPE_TEXT = "type_text"
    PRESS_KEY = "press_key"
    HOTKEY = "hotkey"
    HOLD_RELEASE = "hold_release"

@dataclass
class KeyboardAction:
    """键盘操作记录"""
    action_type: str
    content: str
    timestamp: float
    success: bool

class KeyboardController:
    """键盘控制能力
    
    提供文本输入、按键、组合键等键盘操作功能
    所有操作都会被记录到历史中，便于追踪和调试
    """
    
    def __init__(self):
        self.history: List[KeyboardAction] = []
        self._simulate_mode = True  # 骨架模式，模拟真实控制
        
    def type_text(self, text: str) -> Dict:
        """输入文本
        
        Args:
            text: 要输入的文本内容
            
        Returns:
            Dict: 包含操作状态和信息的字典
        """
        action = KeyboardAction(
            action_type=ActionType.TYPE_TEXT.value,
            content=text,
            timestamp=time.time(),
            success=True
        )
        self.history.append(action)
        
        return {
            "status": "success",
            "action": "type_text",
            "text_length": len(text),
            "message": f"已输入 {len(text)} 个字符"
        }
    
    def press_key(self, key: str) -> Dict:
        """按下并释放单个键
        
        Args:
            key: 按键名称（如 'a', 'enter', 'escape'）
            
        Returns:
            Dict: 包含操作状态和信息的字典
        """
        action = KeyboardAction(
            action_type=ActionType.PRESS_KEY.value,
            content=key,
            timestamp=time.time(),
            success=True
        )
        self.history.append(action)
        
        return {
            "status": "success",
            "action": "press_key",
            "key": key,
            "message": f"已按键：{key}"
        }
    
    def hotkey(self, *keys: str) -> Dict:
        """按下组合键
        
        Args:
            *keys: 组合键列表（如 'ctrl', 'c'）
            
        Returns:
            Dict: 包含操作状态和信息的字典
        """
        key_combo = "+".join(keys)
        action = KeyboardAction(
            action_type=ActionType.HOTKEY.value,
            content=key_combo,
            timestamp=time.time(),
            success=True
        )
        self.history.append(action)
        
        return {
            "status": "success",
            "action": "hotkey",
            "keys": list(keys),
            "combination": key_combo,
            "message": f"已执行组合键：{key_combo}"
        }
    
    def hold_release(self, key: str) -> Dict:
        """长按后释放单个键
        
        Args:
            key: 按键名称
            
        Returns:
            Dict: 包含操作状态和信息的字典
        """
        action = KeyboardAction(
            action_type=ActionType.HOLD_RELEASE.value,
            content=key,
            timestamp=time.time(),
            success=True
        )
        self.history.append(action)
        
        return {
            "status": "success",
            "action": "hold_release",
            "key": key,
            "message": f"已长按释放：{key}"
        }
    
    def get_history(self) -> List[Dict]:
        """获取操作历史
        
        Returns:
            List[Dict]: 操作历史列表
        """
        return [
            {
                "action_type": a.action_type,
                "content": a.content,
                "timestamp": a.timestamp,
                "success": a.success
            }
            for a in self.history
        ]
    
    def clear_history(self) -> Dict:
        """清空操作历史
        
        Returns:
            Dict: 操作状态
        """
        count = len(self.history)
        self.history.clear()
        return {
            "status": "success",
            "action": "clear_history",
            "cleared_count": count,
            "message": f"已清空 {count} 条历史记录"
        }

if __name__ == '__main__':
    print("=" * 50)
    print("Keyboard Controller 自测")
    print("=" * 50)
    
    controller = KeyboardController()
    
    # 测试输入文本
    result = controller.type_text("Hello, World!")
    print(f"\n[输入文本] {result}")
    
    # 测试单键
    result = controller.press_key("enter")
    print(f"[按键] {result}")
    
    # 测试组合键
    result = controller.hotkey("ctrl", "c")
    print(f"[组合键] {result}")
    
    # 测试长按释放
    result = controller.hold_release("shift")
    print(f"[长按释放] {result}")
    
    # 获取历史
    history = controller.get_history()
    print(f"\n[操作历史] 共 {len(history)} 条记录")
    for i, h in enumerate(history, 1):
        print(f"  {i}. {h['action_type']}: {h['content']}")
    
    print("\n" + "=" * 50)
    print("自测完成")
    print("=" * 50)
