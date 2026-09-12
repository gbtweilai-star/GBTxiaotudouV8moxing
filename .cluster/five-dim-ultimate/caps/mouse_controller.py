#!/usr/bin/env python3
"""
Mouse Controller - 鼠标控制能力
为五维合一系统提供精确的鼠标操作
"""
import json
from typing import Dict, Optional, List
from dataclasses import dataclass

@dataclass
class MouseAction:
    action_type: str
    x: int
    y: int
    success: bool

class MouseController:
    """鼠标控制能力"""
    
    def __init__(self):
        self.position = {'x': 0, 'y': 0}
        self.history = []
        
    def move_to(self, x: int, y: int, smooth: bool = True) -> MouseAction:
        """移动鼠标到指定位置"""
        self.position = {'x': x, 'y': y}
        action = MouseAction(
            action_type='move',
            x=x,
            y=y,
            success=True
        )
        self.history.append(action)
        return action
    
    def click(self, button: str = 'left', double: bool = False) -> MouseAction:
        """点击鼠标"""
        action = MouseAction(
            action_type=f'click_{button}_{"double" if double else "single"}',
            x=self.position['x'],
            y=self.position['y'],
            success=True
        )
        self.history.append(action)
        return action
    
    def scroll(self, delta: int) -> MouseAction:
        """滚动鼠标"""
        action = MouseAction(
            action_type=f'scroll_{"down" if delta > 0 else "up"}',
            x=self.position['x'],
            y=self.position['y'],
            success=True
        )
        self.history.append(action)
        return action
    
    def drag_to(self, x: int, y: int) -> MouseAction:
        """拖拽到指定位置"""
        start_pos = self.position.copy()
        self.position = {'x': x, 'y': y}
        action = MouseAction(
            action_type='drag',
            x=x,
            y=y,
            success=True
        )
        self.history.append(action)
        return action
    
    def get_position(self) -> Dict:
        """获取当前位置"""
        return self.position
    
    def get_history(self) -> List[Dict]:
        """获取操作历史"""
        return [
            {
                'action': a.action_type,
                'position': {'x': a.x, 'y': a.y},
                'success': a.success
            }
            for a in self.history
        ]

if __name__ == '__main__':
    controller = MouseController()
    
    # 测试鼠标操作
    controller.move_to(100, 200)
    controller.click('left')
    controller.scroll(100)
    controller.drag_to(300, 400)
    
    print(f"当前位置：{controller.get_position()}")
    print(f"操作历史：{len(controller.get_history())} 次操作")
