"""
面板组件
"""
import pygame
from config import UI_SCALE

class Panel:
    """面板类 - 用于组织UI元素"""
    
    def __init__(self, x, y, width, height, 
                 color=(40, 40, 60), 
                 alpha=200,
                 border_color=(100, 100, 120),
                 border_width=3):
        """
        Args:
            x, y: 面板位置
            width, height: 面板尺寸
            color: 背景颜色
            alpha: 透明度
            border_color: 边框颜色
            border_width: 边框宽度
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.alpha = alpha
        self.border_color = border_color
        self.border_width = max(1, int(border_width * UI_SCALE))
        
        # 创建surface
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
    def draw(self, screen):
        """绘制面板"""
        # 填充背景
        self.surface.fill((*self.color, self.alpha))
        
        # 绘制边框
        border_radius = max(15, int(15 * UI_SCALE))
        pygame.draw.rect(self.surface, self.border_color, 
                        (0, 0, self.rect.width, self.rect.height),
                        self.border_width, border_radius=border_radius)
        
        screen.blit(self.surface, self.rect)