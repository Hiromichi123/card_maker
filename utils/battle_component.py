""""战斗组件类，包括卡牌槽位和血量条等"""
import pygame
from config import *

"""卡牌槽位类"""
class CardSlot:
    def __init__(self, x, y, width, height, slot_type="battle"):
        self.rect = pygame.Rect(x, y, width, height)
        self.slot_type = slot_type
        self.card = None  # 当前槽位的卡牌
        self.is_hovered = False
        self.is_highlighted = False  # 是否可放置提示
        from utils.card_database import get_card_database
        self.card_database = get_card_database()
        
    def set_card(self, card):
        """放置卡牌"""
        self.card = card
        
    def remove_card(self):
        """移除卡牌"""
        card = self.card
        self.card = None
        return card
        
    def has_card(self):
        """是否有卡牌"""
        return self.card is not None
        
    def draw(self, screen):
        """绘制槽位"""
        # 槽位背景
        if self.card:
            # 有卡牌时不显示槽位框
            pass
        else:
            # 空槽位
            alpha = 150 if self.is_highlighted else 80
            slot_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            
            # 根据槽位类型选择颜色
            if self.slot_type == "battle":
                color = (100, 150, 200, alpha)
                border_color = (150, 200, 255, 200)
            elif self.slot_type == "waiting":
                color = (150, 150, 100, alpha)
                border_color = (200, 200, 150, 200)
            else:  # discard
                color = (150, 100, 100, alpha)
                border_color = (200, 150, 150, 200)
            
            slot_surface.fill(color)
            
            # 边框
            border_width = max(2, int(3 * UI_SCALE))
            if self.is_hovered:
                border_width = max(3, int(4 * UI_SCALE))
                border_color = (255, 255, 255, 255)
            
            pygame.draw.rect(slot_surface, border_color, 
                           (0, 0, self.rect.width, self.rect.height), 
                           border_width, border_radius=max(5, int(8 * UI_SCALE)))
            
            screen.blit(slot_surface, self.rect)
            
            # 空槽位提示（小圆点或图标）
            if not self.card and self.slot_type == "battle":
                center = self.rect.center
                radius = max(3, int(5 * UI_SCALE))
                pygame.draw.circle(screen, (200, 200, 200, 100), center, radius)

"""血量条类"""
class HealthBar:
    def __init__(self, x, y, width, height, max_hp, current_hp, is_player=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.is_player = is_player
        self.animated_hp = current_hp # 动画当前血量（用于平滑过渡）
        
    def set_hp(self, hp):
        """设置血量"""
        self.current_hp = max(0, min(hp, self.max_hp))
        
    def update(self, dt):
        """更新血量动画"""
        # 平滑过渡到目标血量
        diff = self.current_hp - self.animated_hp
        self.animated_hp += diff * min(1.0, dt * 5)
        
    def draw(self, screen):
        """绘制血量条"""
        # 背景
        bg_color = (50, 50, 50)
        pygame.draw.rect(screen, bg_color, self.rect, 
                        border_radius=max(5, int(10 * UI_SCALE)))
        
        # 血量条
        hp_ratio = self.animated_hp / self.max_hp
        hp_width = int(self.rect.width * hp_ratio)
        
        if hp_width > 0:
            hp_rect = pygame.Rect(self.rect.x, self.rect.y, hp_width, self.rect.height)
            
            # 根据血量百分比选择颜色
            if hp_ratio > 0.6:
                hp_color = (100, 255, 100) if self.is_player else (255, 100, 100)
            elif hp_ratio > 0.3:
                hp_color = (255, 200, 100)
            else:
                hp_color = (255, 100, 100) if self.is_player else (100, 255, 100)
            
            pygame.draw.rect(screen, hp_color, hp_rect, 
                           border_radius=max(5, int(10 * UI_SCALE)))
        
        # 边框
        border_color = (100, 100, 100)
        border_width = max(2, int(3 * UI_SCALE))
        pygame.draw.rect(screen, border_color, self.rect, border_width,
                        border_radius=max(5, int(10 * UI_SCALE)))
        
        # 血量数字
        font = get_font(max(16, int(24 * UI_SCALE)))
        hp_text = f"{int(self.current_hp)}/{self.max_hp}"
        text_surface = font.render(hp_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
