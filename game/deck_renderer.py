"""卡堆渲染器"""
import pygame
from config import *

class DeckRenderer:
    """卡堆渲染器"""
    
    def __init__(self, x, y, is_player=True):
        self.position = (x, y)
        self.is_player = is_player
        
        # 卡牌尺寸
        self.card_width = int(144 * UI_SCALE)
        self.card_height = int(216 * UI_SCALE)
        
        self.card_count = 0 # 卡堆剩余数量
        
        self.create_card_back() # 创建卡背图片
        
    def create_card_back(self):
        """创建卡背"""
        self.card_back = pygame.Surface((self.card_width, self.card_height))
        
        # 渐变背景
        for y in range(self.card_height):
            ratio = y / self.card_height
            color = (
                int(30 + ratio * 50),
                int(30 + ratio * 80),
                int(80 + ratio * 100)
            )
            pygame.draw.line(self.card_back, color, 
                           (0, y), (self.card_width, y))
        
        # 边框
        border_color = (100, 150, 200)
        border_width = max(3, int(4 * UI_SCALE))
        pygame.draw.rect(self.card_back, border_color,
                        (0, 0, self.card_width, self.card_height),
                        border_width, border_radius=max(8, int(12 * UI_SCALE)))
        
        # 装饰图案（中央菱形）
        center_x = self.card_width // 2
        center_y = self.card_height // 2
        size = int(40 * UI_SCALE)
        
        diamond_points = [
            (center_x, center_y - size),
            (center_x + size, center_y),
            (center_x, center_y + size),
            (center_x - size, center_y)
        ]
        pygame.draw.polygon(self.card_back, (150, 200, 255), diamond_points)
        pygame.draw.polygon(self.card_back, (100, 150, 200), diamond_points, 3)
        
    def set_count(self, count):
        """设置剩余卡牌数"""
        self.card_count = count
        
    def draw(self, screen):
        """绘制卡堆"""
        if self.card_count <= 0:
            return
        
        x, y = self.position
        
        # 绘制堆叠效果（多张卡片重叠）
        stack_depth = min(5, self.card_count)
        offset = max(1, int(2 * UI_SCALE))
        
        for i in range(stack_depth):
            # 每张卡稍微偏移
            draw_x = x + i * offset
            draw_y = y - i * offset
            
            # 阴影
            shadow_surface = pygame.Surface((self.card_width, self.card_height), 
                                          pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 100))
            screen.blit(shadow_surface, (draw_x + 3, draw_y + 3))
            
            # 卡背
            screen.blit(self.card_back, (draw_x, draw_y))
        
        # 显示剩余数量
        font = get_font(max(16, int(24 * UI_SCALE)))
        count_text = font.render(f"{self.card_count}", True, (255, 255, 255))
        
        # 数量背景圆形
        text_rect = count_text.get_rect()
        badge_radius = max(20, int(30 * UI_SCALE))
        badge_center = (
            x + self.card_width + badge_radius,
            y + self.card_height // 2
        )
        
        pygame.draw.circle(screen, (50, 50, 50), badge_center, badge_radius)
        pygame.draw.circle(screen, (200, 200, 200), badge_center, badge_radius, 2)
        
        count_text_rect = count_text.get_rect(center=badge_center)
        screen.blit(count_text, count_text_rect)
        
        # 标签
        label_font = get_font(max(12, int(16 * UI_SCALE)))
        label = "牌堆" if self.is_player else "敌方牌堆"
        label_text = label_font.render(label, True, (200, 200, 200))
        label_rect = label_text.get_rect(centerx=x + self.card_width // 2,
                                         top=y + self.card_height + 5)
        screen.blit(label_text, label_rect)