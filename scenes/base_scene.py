"""
场景基类
所有UI界面都继承此类
"""
import pygame
from abc import ABC, abstractmethod

class BaseScene(ABC):
    """场景基类"""
    
    def __init__(self, screen):
        self.screen = screen
        self.next_scene = None  # 下一个要跳转的场景
        self.is_active = True
        
    @abstractmethod
    def handle_event(self, event):
        """
        处理事件
        Args:
            event: pygame事件
        """
        pass
    
    @abstractmethod
    def update(self, dt):
        """
        更新逻辑
        Args:
            dt: 时间增量（秒）
        """
        pass
    
    @abstractmethod
    def draw(self):
        """绘制场景"""
        pass
    
    def enter(self):
        """进入场景时调用"""
        self.is_active = True
        
    def exit(self):
        """退出场景时调用"""
        self.is_active = False
        
    def switch_to(self, scene_name):
        """
        切换到其他场景
        Args:
            scene_name: 场景名称
        """
        self.next_scene = scene_name