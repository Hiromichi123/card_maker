"""
场景基类
"""
import pygame
from abc import ABC, abstractmethod

"""场景基类"""
class BaseScene(ABC):
    def __init__(self, screen):
        self.screen = screen
        self.next_scene = None  # 下一个要跳转的场景
        self.is_active = True
    
    """处理事件"""
    @abstractmethod
    def handle_event(self, event):
        pass
    
    """通用更新"""
    @abstractmethod
    def update(self, dt):
        pass
    
    """绘制场景"""
    @abstractmethod
    def draw(self):
        pass
    
    """进入场景时调用"""
    def enter(self):
        self.is_active = True
        
    """退出场景时调用"""
    def exit(self):
        self.is_active = False
    
    """切换到其他场景"""
    def switch_to(self, scene_name):
        self.next_scene = scene_name