"""
手牌系统
"""
import pygame
import math
from config import *

# 手牌尺寸
CARD_WIDTH = int(216 * UI_SCALE)
CARD_HEIGHT = int(324 * UI_SCALE)

# 手牌区域
PLAYER_CARD_X = WINDOW_WIDTH // 2
PLAYER_CARD_Y = int(WINDOW_HEIGHT * 0.90)
ENEMY_CARD_X = WINDOW_WIDTH // 2
ENEMY_CARD_Y = int(WINDOW_HEIGHT * 0.10)

# 手牌扇形参数
FAN_SPREAD_ANGLE = 25  # 扇形展开角度（度）
FAN_RADIUS = 500       # 扇形半径
HOVER_SPREAD_ANGLE = 35  # 悬停时展开角度
HOVER_SCALE = 1.4      # 悬停时缩放
HOVER_Y_OFFSET = -150   # 悬停时Y偏移

"""手牌类"""
class HandCard:
    def __init__(self, card_data, index, total_cards):
        self.card_data = card_data
        self.index = index
        self.total_cards = total_cards
        
        # 位置和旋转
        self.position = (0, 0)
        self.target_position = (0, 0)
        self.rotation = 0
        self.target_rotation = 0
        self.flip = False  # 是否翻转180度（敌人手牌）
        
        # 状态
        self.is_hovered = False
        self.is_selected = False
        self.is_dragging = False
        
        # 动画
        self.scale = 1.0
        self.target_scale = 1.0
        self.y_offset = 0
        self.target_y_offset = 0

        # 牌堆抽取动画
        self.animation_state = "idle"  # idle, drawing, arriving
        self.animation_progress = 0.0
        self.draw_from_pos = None  # 从哪个位置抽取
        
        # 加载图片
        self.load_image()

    """加载卡牌图片""" 
    def load_image(self):
        import os
        try:
            if os.path.exists(self.card_data.image_path):
                original = pygame.image.load(self.card_data.image_path)
                self.original_image = pygame.transform.smoothscale(
                    original, (CARD_WIDTH, CARD_HEIGHT)
                )
            else:
                self.original_image = self.create_placeholder()
        except:
            self.original_image = self.create_placeholder()
            
        self.original_image = self.original_image.convert_alpha()
        self.image = self.original_image.copy()
        
    def create_placeholder(self):
        """创建占位符"""
        surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        color = COLORS.get(self.card_data.rarity, (100, 100, 100))
        surface.fill(color)
        
        border_width = max(2, int(3 * UI_SCALE))
        pygame.draw.rect(surface, (255, 255, 255), 
                        (0, 0, CARD_WIDTH, CARD_HEIGHT), border_width)
        
        font = get_font(max(24, int(36 * UI_SCALE)))
        text = font.render(self.card_data.name[:4], True, (255, 255, 255))
        text_rect = text.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT // 2))
        surface.blit(text, text_rect)
        
        return surface
    
    """更新动画"""
    def update(self, dt):
        # 抽卡动画
        if self.animation_state == "drawing":
            self.animation_progress += dt * 2.0  # 动画速度
            
            if self.animation_progress >= 1.0:
                self.animation_state = "idle"
                self.animation_progress = 1.0
            
            # 缓动函数（ease-out）
            t = self.animation_progress
            ease_t = 1 - (1 - t) ** 3
            
            # 从卡堆位置移动到目标位置
            if self.draw_from_pos:
                fx, fy = self.draw_from_pos
                tx, ty = self.target_position
                
                self.position = (
                    fx + (tx - fx) * ease_t,
                    fy + (ty - fy) * ease_t
                )
                self.rotation = self.target_rotation * ease_t # 旋转到目标角度
                self.scale = 0.8 + 0.2 * ease_t # 缩放
        else:
            lerp_speed = min(1.0, dt * 10) # 平滑移动到目标位置
            px, py = self.position
            tx, ty = self.target_position
            self.position = (
                px + (tx - px) * lerp_speed,
                py + (ty - py) * lerp_speed
            )
            
            self.rotation += (self.target_rotation - self.rotation) * lerp_speed # 平滑旋转
            self.scale += (self.target_scale - self.scale) * lerp_speed # 平滑缩放
            self.y_offset += (self.target_y_offset - self.y_offset) * lerp_speed # Y轴偏移（悬停时上浮）
            
    def get_transformed_image(self):
        """获取变换后的图片"""
        # 缩放
        scaled_width = int(CARD_WIDTH * self.scale)
        scaled_height = int(CARD_HEIGHT * self.scale)
        scaled_image = pygame.transform.smoothscale(self.original_image, (scaled_width, scaled_height))
        # 旋转
        rotated_image = pygame.transform.rotate(scaled_image, self.rotation)
        
        return rotated_image
    
    def get_rect(self):
        """获取当前矩形（用于碰撞检测）"""
        image = self.get_transformed_image()
        rect = image.get_rect(center=(int(self.position[0]), 
                                     int(self.position[1] + self.y_offset)))
        return rect
    
    """绘制手牌"""
    def draw(self, screen):
        image = self.get_transformed_image()
        rect = image.get_rect(center=(int(self.position[0]), 
                                     int(self.position[1] + self.y_offset)))
        screen.blit(image, rect)
        
        # 高亮边框（悬停或选中时）
        if self.is_hovered or self.is_selected:
            border_color = (255, 255, 100) if self.is_selected else (255, 255, 255)
            border_width = max(3, int(4 * UI_SCALE))
            pygame.draw.rect(screen, border_color, rect, border_width, 
                           border_radius=max(5, int(8 * UI_SCALE)))

    def start_draw_animation(self, from_pos):
        """开始抽卡动画"""
        self.animation_state = "drawing"
        self.animation_progress = 0.0
        self.draw_from_pos = from_pos
        self.position = from_pos
        self.rotation = 0 if not self.flip else 180
        self.scale = 0.8


"""手牌管理器"""
class HandManager:
    def __init__(self, is_player=True):
        """is_player: True为玩家(下方正向), False为敌人(上方反向)"""
        self.is_player = is_player
        self.cards = []
        self.selected_card = None
        self.hovered_card = None
        
        # 手牌区域位置
        if is_player:
            self.center_x = PLAYER_CARD_X
            self.center_y = PLAYER_CARD_Y
            self.flip = False  # 不翻转
        else:
            self.center_x = ENEMY_CARD_X
            self.center_y = ENEMY_CARD_Y
            self.flip = True  # 翻转180度
    
    def add_card(self, card_data):
        """添加手牌"""
        hand_card = HandCard(card_data, len(self.cards), len(self.cards) + 1)
        self.cards.append(hand_card)
        self.update_card_positions()
        
    def remove_card(self, card):
        """移除手牌"""
        if card in self.cards:
            self.cards.remove(card)
            # 重新索引
            for i, c in enumerate(self.cards):
                c.index = i
                c.total_cards = len(self.cards)
            self.update_card_positions()
            
    def update_card_positions(self, force_spread=False):
        """更新所有手牌的目标位置"""
        count = len(self.cards)
        if count == 0:
            return
        
        # 根据是否有悬停卡牌决定展开角度
        spread_angle = HOVER_SPREAD_ANGLE if (self.hovered_card or force_spread) else FAN_SPREAD_ANGLE
        
        for i, card in enumerate(self.cards):
            if count == 1:
                angle = 0
            else:
                angle = -spread_angle / 2 + (i / (count - 1)) * spread_angle
            
            # 如果是敌人，翻转角度
            if self.flip:
                angle = -angle
            
            # 计算位置（扇形排列）
            rad = math.radians(angle)
            x = self.center_x + FAN_RADIUS * math.sin(rad)
            y = self.center_y - FAN_RADIUS * (1 - math.cos(rad))
            
            if self.flip:
                # 敌人手牌：上方，扇形向下
                y = self.center_y + FAN_RADIUS * (1 - math.cos(rad))
            
            card.target_position = (x, y)
            card.target_rotation = -angle if not self.flip else angle  # 卡牌旋转方向
            
            # 悬停效果
            if card == self.hovered_card:
                card.target_scale = HOVER_SCALE
                card.target_y_offset = HOVER_Y_OFFSET if not self.flip else -HOVER_Y_OFFSET
            else:
                card.target_scale = 1.0
                card.target_y_offset = 0
    
    """处理事件"""
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            self.update_hover(mouse_pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 点击选择/取消选择
            if self.hovered_card:
                if self.selected_card == self.hovered_card:
                    self.selected_card = None
                else:
                    self.selected_card = self.hovered_card
                    self.selected_card.is_selected = True
                return self.selected_card
        
        return None
    
    """更新悬停状态"""
    def update_hover(self, mouse_pos):
        old_hovered = self.hovered_card
        self.hovered_card = None
        
        # 从后往前检测（最上层的卡优先）
        for card in reversed(self.cards):
            if card.get_rect().collidepoint(mouse_pos):
                self.hovered_card = card
                break
        
        # 更新所有卡牌的悬停状态
        for card in self.cards:
            card.is_hovered = (card == self.hovered_card)
        
        # 如果悬停变化，更新位置
        if old_hovered != self.hovered_card:
            self.update_card_positions()
    
    def update(self, dt):
        """更新所有手牌"""
        for card in self.cards:
            card.update(dt)
    
    def draw(self, screen):
        """绘制所有手牌（从左到右，后面的覆盖前面的）"""
        for card in self.cards:
            card.draw(screen)
    
    def get_hovered_card_data(self):
        """获取当前悬停的卡牌数据（用于tooltip）"""
        if self.hovered_card:
            return self.hovered_card.card_data
        return None
    
    def add_card(self, card_data, animate=False):
        """
        添加手牌
        Args:
            card_data: CardData对象
            animate: 是否播放抽卡动画
        """
        hand_card = HandCard(card_data, len(self.cards), len(self.cards) + 1)
        self.cards.append(hand_card)
        self.update_card_positions()
        
        # 如果需要动画，从卡堆位置开始
        if animate:
            hand_card.start_draw_animation(self.deck_position)
        
        return hand_card
