"""
场景基类
"""
import pygame
from abc import ABC, abstractmethod
from ui.tooltip import get_tooltip # 导入全局 tooltip 获取函数

"""场景基类"""
class BaseScene(ABC):
    force_native_resolution = False

    def __init__(self, screen):
        self.screen = screen
        self.next_scene = None  # 下一个要跳转的场景
        self.is_active = True
        self.tooltip = get_tooltip()  # 添加全局 tooltip
    
    """处理事件"""
    @abstractmethod
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.update_tooltip(event.pos)
    
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

    """更新 tooltip"""
    def update_tooltip(self, mouse_pos):
        card_data = self.get_hovered_card(mouse_pos) # 默认实现：尝试获取悬停的卡牌
        
        if card_data:
            self.tooltip.show(card_data, mouse_pos)
        else:
            self.tooltip.hide()

    """获取鼠标悬停的卡牌"""
    def get_hovered_card(self, mouse_pos):
        return None

    """
    绘制场景并自动绘制 tooltip
    子类调用这个方法，或者在draw()最后手动调用self.tooltip.draw()
    """
    def draw_with_tooltip(self):
        self.draw()
        self.tooltip.draw(self.screen)