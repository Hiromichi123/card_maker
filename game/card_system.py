import os
import random
import pygame
from config import *

class Card:
    """卡牌类"""
    def __init__(self, image_path, rarity, position, index):
        self.image_path = image_path
        self.rarity = rarity
        self.target_position = position
        self.index = index
        
        # 动画相关
        self.current_position = (position[0], -CARD_HEIGHT)
        self.scale = 0.0
        self.alpha = 0
        self.rotation = 0
        self.animation_progress = 0
        self.flip_progress = 0
        
        # 缓存渲染的图片
        self.cached_surfaces = {}
        
        # 加载图片
        self.load_image()
        
    def load_image(self):
        """加载卡牌图片"""
        try:
            if os.path.exists(self.image_path):
                original = pygame.image.load(self.image_path)
                self.image = pygame.transform.smoothscale(original, (CARD_WIDTH, CARD_HEIGHT))
            else:
                self.image = self.create_placeholder()
        except:
            self.image = self.create_placeholder()
        
        self.image = self.image.convert_alpha()
        self.back_image = self.create_card_back().convert_alpha()
        self.glow_surface = self.create_glow_surface()
        
    def create_placeholder(self):
        """创建占位符图片"""
        surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        color = COLORS.get(self.rarity, (100, 100, 100))
        surface.fill(color)
        
        pygame.draw.rect(surface, (255, 255, 255), 
                        (0, 0, CARD_WIDTH, CARD_HEIGHT), max(3, int(3 * UI_SCALE)))
        
        # 使用中文字体
        font_size = max(24, int(48 * UI_SCALE))
        font = get_font(font_size)  # 修改这里
        text = font.render(self.rarity, True, (255, 255, 255))
        text_rect = text.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT // 2))
        surface.blit(text, text_rect)
        
        font_small_size = max(12, int(20 * UI_SCALE))
        font_small = get_font(font_small_size)  # 修改这里
        filename = os.path.basename(self.image_path)
        text_small = font_small.render(filename, True, (255, 255, 255))
        text_rect_small = text_small.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT - int(20 * UI_SCALE)))
        surface.blit(text_small, text_rect_small)
        
        return surface
    
    def create_card_back(self):
        """创建卡背"""
        surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        surface.fill((50, 50, 80))
        
        border_width = max(5, int(5 * UI_SCALE))
        border_margin = max(10, int(10 * UI_SCALE))
        pygame.draw.rect(surface, (100, 100, 150), 
                        (border_margin, border_margin, 
                         CARD_WIDTH - border_margin * 2, 
                         CARD_HEIGHT - border_margin * 2), border_width)
        
        font_size = max(18, int(36 * UI_SCALE))
        font = get_font(font_size)  # 修改这里
        text = font.render("?", True, (200, 200, 200))
        text_rect = text.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT // 2))
        surface.blit(text, text_rect)
        
        return surface
    
    def create_glow_surface(self):
        """预创建发光效果surface"""
        glow_margin = max(10, int(10 * UI_SCALE))
        surface = pygame.Surface((CARD_WIDTH + glow_margin * 2, 
                                 CARD_HEIGHT + glow_margin * 2), 
                                pygame.SRCALPHA)
        color = COLORS.get(self.rarity, (255, 255, 255))
        border_width = max(5, int(5 * UI_SCALE))
        pygame.draw.rect(surface, (*color, 100), 
                        (0, 0, CARD_WIDTH + glow_margin * 2, 
                         CARD_HEIGHT + glow_margin * 2), border_width)
        return surface
    
    def update(self, dt, start_time):
        """更新卡牌动画"""
        delay = self.index * STAGGER_DELAY
        elapsed = start_time - delay
        
        if elapsed < 0:
            return
        
        if self.animation_progress < 1.0:
            self.animation_progress = min(1.0, elapsed / ANIMATION_DURATION)
            t = self.ease_out_bounce(self.animation_progress)
            
            start_y = -CARD_HEIGHT
            self.current_position = (
                self.target_position[0],
                start_y + (self.target_position[1] - start_y) * t
            )
            
            self.scale = t
            self.alpha = int(255 * t)
        
        elif self.flip_progress < 1.0:
            self.flip_progress = min(1.0, (elapsed - ANIMATION_DURATION) / CARD_FLIP_DURATION)
            self.rotation = self.flip_progress * 180
    
    def ease_out_bounce(self, t):
        """缓动函数"""
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - pow(-2 * t + 2, 2) / 2
    
    def draw(self, screen):
        """绘制卡牌"""
        if self.scale <= 0:
            return
        
        if self.rotation < 90:
            img = self.back_image
            scale_x = 1 - (self.rotation / 90)
        else:
            img = self.image
            scale_x = (self.rotation - 90) / 90
        
        width = int(CARD_WIDTH * self.scale * abs(scale_x))
        height = int(CARD_HEIGHT * self.scale)
        
        if width <= 0 or height <= 0:
            return
        
        cache_key = (width, height, self.rotation < 90)
        if cache_key not in self.cached_surfaces:
            self.cached_surfaces[cache_key] = pygame.transform.smoothscale(img, (width, height))
        
        scaled_img = self.cached_surfaces[cache_key].copy()
        scaled_img.set_alpha(self.alpha)
        
        pos = (
            int(self.current_position[0] + (CARD_WIDTH - width) // 2),
            int(self.current_position[1])
        )
        
        screen.blit(scaled_img, pos)
        
        if self.flip_progress > 0.5:
            self.draw_rarity_glow(screen)
    
    def draw_rarity_glow(self, screen):
        """绘制稀有度光效"""
        glow_alpha = int(100 * (self.flip_progress - 0.5) * 2)
        glow_copy = self.glow_surface.copy()
        glow_copy.set_alpha(glow_alpha)
        
        glow_margin = max(10, int(10 * UI_SCALE))
        screen.blit(glow_copy, 
                   (self.current_position[0] - glow_margin, 
                    self.current_position[1] - glow_margin))

"""卡牌系统"""
class CardSystem:
    def __init__(self):
        self.cards = []
        self.animation_start_time = 0
        self.is_animating = False
    
    """抽取卡牌"""
    def draw_cards(self):
        self.cards = []
        drawn_cards = []
        
        card_pool = self.get_card_pool()
        
        for i in range(TOTAL_CARDS):
            rarity, card_path = self.draw_single_card(card_pool)
            row = i // CARDS_PER_ROW
            col = i % CARDS_PER_ROW
            
            total_width = CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_SPACING
            start_x = (WINDOW_WIDTH - total_width) // 2
            start_y = int(WINDOW_HEIGHT * 0.15) + row * (CARD_HEIGHT + CARD_SPACING)
            
            position = (start_x + col * (CARD_WIDTH + CARD_SPACING), start_y)
            
            card = Card(card_path, rarity, position, i)
            drawn_cards.append(card)
        
        self.cards = drawn_cards
        self.animation_start_time = 0
        self.is_animating = True
        
    """获取卡池"""  
    def get_card_pool(self):
        pool = {rarity: [] for rarity in CARD_PROBABILITIES.keys()}
        
        for rarity in pool.keys():
            rarity_path = os.path.join(CARD_BASE_PATH, rarity)
            if os.path.exists(rarity_path):
                files = [f for f in os.listdir(rarity_path) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                pool[rarity] = [os.path.join(rarity_path, f) for f in files]
            
            if not pool[rarity]:
                pool[rarity] = [f"{rarity}_placeholder_{i}.png" for i in range(5)]
        
        return pool
    
    def draw_single_card(self, card_pool):
        """抽取单张卡牌"""
        rand = random.randint(1, 100)
        cumulative = 0
        
        for rarity, probability in CARD_PROBABILITIES.items():
            cumulative += probability
            if rand <= cumulative:
                if card_pool[rarity]:
                    card_path = random.choice(card_pool[rarity])
                    return rarity, card_path
        
        return "D", random.choice(card_pool["D"])
    
    def update(self, dt):
        """更新卡牌动画"""
        if self.is_animating:
            self.animation_start_time += dt
            
            for card in self.cards:
                card.update(dt, self.animation_start_time)
            
            if self.animation_start_time > ANIMATION_DURATION + CARD_FLIP_DURATION + TOTAL_CARDS * STAGGER_DELAY:
                self.is_animating = False
    
    def draw(self, screen):
        """绘制所有卡牌"""
        for card in self.cards:
            card.draw(screen)