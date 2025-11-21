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
        self.current_position = (position[0], -CARD_HEIGHT)  # 从屏幕上方开始
        self.scale = 0.0
        self.alpha = 0
        self.rotation = 0
        self.animation_progress = 0
        self.flip_progress = 0
        
        # 加载图片
        self.load_image()
        
    def load_image(self):
        """加载卡牌图片"""
        try:
            if os.path.exists(self.image_path):
                self.image = pygame.image.load(self.image_path)
                self.image = pygame.transform.scale(self.image, (CARD_WIDTH, CARD_HEIGHT))
            else:
                # 如果图片不存在，创建一个带颜色的矩形作为占位符
                self.image = self.create_placeholder()
        except:
            self.image = self.create_placeholder()
            
        self.back_image = self.create_card_back()
        
    def create_placeholder(self):
        """创建占位符图片"""
        surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        color = COLORS.get(self.rarity, (100, 100, 100))
        surface.fill(color)
        
        # 添加边框
        pygame.draw.rect(surface, (255, 255, 255), 
                        (0, 0, CARD_WIDTH, CARD_HEIGHT), 3)
        
        # 添加稀有度文字
        font = pygame.font.Font(None, 48)
        text = font.render(self.rarity, True, (255, 255, 255))
        text_rect = text.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT // 2))
        surface.blit(text, text_rect)
        
        # 添加文件名
        font_small = pygame.font.Font(None, 20)
        filename = os.path.basename(self.image_path)
        text_small = font_small.render(filename, True, (255, 255, 255))
        text_rect_small = text_small.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT - 20))
        surface.blit(text_small, text_rect_small)
        
        return surface
    
    def create_card_back(self):
        """创建卡背"""
        surface = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        surface.fill((50, 50, 80))
        pygame.draw.rect(surface, (100, 100, 150), 
                        (10, 10, CARD_WIDTH - 20, CARD_HEIGHT - 20), 5)
        
        font = pygame.font.Font(None, 36)
        text = font.render("?", True, (200, 200, 200))
        text_rect = text.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT // 2))
        surface.blit(text, text_rect)
        
        return surface
    
    def update(self, dt, start_time):
        """更新卡牌动画"""
        # 计算延迟后的动画时间
        delay = self.index * STAGGER_DELAY
        elapsed = start_time - delay
        
        if elapsed < 0:
            return
        
        # 下落动画
        if self.animation_progress < 1.0:
            self.animation_progress = min(1.0, elapsed / ANIMATION_DURATION)
            # 使用缓动函数
            t = self.ease_out_bounce(self.animation_progress)
            
            # 位置插值
            start_y = -CARD_HEIGHT
            self.current_position = (
                self.target_position[0],
                start_y + (self.target_position[1] - start_y) * t
            )
            
            # 缩放和透明度
            self.scale = t
            self.alpha = int(255 * t)
        
        # 翻转动画（在下落完成后）
        elif self.flip_progress < 1.0:
            self.flip_progress = min(1.0, (elapsed - ANIMATION_DURATION) / CARD_FLIP_DURATION)
            self.rotation = self.flip_progress * 180
    
    def ease_out_bounce(self, t):
        """缓动函数 - 弹跳效果"""
        if t < 0.5:
            return 2 * t * t
        else:
            return 1 - pow(-2 * t + 2, 2) / 2
    
    def draw(self, screen):
        """绘制卡牌"""
        if self.scale <= 0:
            return
        
        # 选择显示正面还是背面
        if self.rotation < 90:
            # 显示卡背
            img = self.back_image
            scale_x = 1 - (self.rotation / 90)
        else:
            # 显示卡面
            img = self.image
            scale_x = (self.rotation - 90) / 90
        
        # 缩放
        width = int(CARD_WIDTH * self.scale * abs(scale_x))
        height = int(CARD_HEIGHT * self.scale)
        
        if width > 0 and height > 0:
            scaled_img = pygame.transform.scale(img, (width, height))
            
            # 设置透明度
            scaled_img.set_alpha(self.alpha)
            
            # 居中绘制
            pos = (
                int(self.current_position[0] + (CARD_WIDTH - width) // 2),
                int(self.current_position[1])
            )
            
            screen.blit(scaled_img, pos)
            
            # 绘制稀有度光效
            if self.flip_progress > 0.5:
                self.draw_rarity_glow(screen)
    
    def draw_rarity_glow(self, screen):
        """绘制稀有度光效"""
        color = COLORS.get(self.rarity, (255, 255, 255))
        glow_alpha = int(100 * (self.flip_progress - 0.5) * 2)
        
        glow_surface = pygame.Surface((CARD_WIDTH + 20, CARD_HEIGHT + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (*color, glow_alpha), 
                        (0, 0, CARD_WIDTH + 20, CARD_HEIGHT + 20), 5)
        
        screen.blit(glow_surface, 
                   (self.current_position[0] - 10, self.current_position[1] - 10))


class CardSystem:
    """卡牌系统"""
    def __init__(self):
        self.cards = []
        self.animation_start_time = 0
        self.is_animating = False
        
    def draw_cards(self):
        """抽取卡牌"""
        self.cards = []
        drawn_cards = []
        
        # 获取所有可用的卡牌文件
        card_pool = self.get_card_pool()
        
        # 抽取10张卡
        for i in range(TOTAL_CARDS):
            rarity, card_path = self.draw_single_card(card_pool)
            row = i // CARDS_PER_ROW
            col = i % CARDS_PER_ROW
            
            # 计算卡牌位置（居中显示）
            total_width = CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_SPACING
            start_x = (WINDOW_WIDTH - total_width) // 2
            start_y = 100 + row * (CARD_HEIGHT + CARD_SPACING)
            
            position = (start_x + col * (CARD_WIDTH + CARD_SPACING), start_y)
            
            card = Card(card_path, rarity, position, i)
            drawn_cards.append(card)
        
        self.cards = drawn_cards
        self.animation_start_time = 0
        self.is_animating = True
        
    def get_card_pool(self):
        """获取卡池"""
        pool = {rarity: [] for rarity in CARD_PROBABILITIES.keys()}
        
        for rarity in pool.keys():
            rarity_path = os.path.join(CARD_BASE_PATH, rarity)
            if os.path.exists(rarity_path):
                files = [f for f in os.listdir(rarity_path) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                pool[rarity] = [os.path.join(rarity_path, f) for f in files]
            
            # 如果没有找到图片，添加占位符
            if not pool[rarity]:
                pool[rarity] = [f"{rarity}_placeholder_{i}.png" for i in range(5)]
        
        return pool
    
    def draw_single_card(self, card_pool):
        """抽取单张卡牌"""
        # 根据概率选择稀有度
        rand = random.randint(1, 100)
        cumulative = 0
        
        for rarity, probability in CARD_PROBABILITIES.items():
            cumulative += probability
            if rand <= cumulative:
                if card_pool[rarity]:
                    card_path = random.choice(card_pool[rarity])
                    return rarity, card_path
        
        # 默认返回D级
        return "D", random.choice(card_pool["D"])
    
    def update(self, dt):
        """更新卡牌动画"""
        if self.is_animating:
            self.animation_start_time += dt
            
            for card in self.cards:
                card.update(dt, self.animation_start_time)
            
            # 检查动画是否完成
            if self.animation_start_time > ANIMATION_DURATION + CARD_FLIP_DURATION + TOTAL_CARDS * STAGGER_DELAY:
                self.is_animating = False
    
    def draw(self, screen):
        """绘制所有卡牌"""
        for card in self.cards:
            card.draw(screen)