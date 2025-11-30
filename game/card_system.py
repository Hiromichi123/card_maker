"""卡牌系统"""
import os
import random
import pygame
from config import *
from utils.card_database import get_card_database, CardData

# 常驻卡池概率
CARD_PROBABILITIES = {
    "SSS": 0.5,
    "SS+": 0.8,
    "SS": 0.7,
    "S+": 1.2,
    "S": 1.3,
    "A+": 3.0,
    "A": 5.5,
    "B+": 7.0,
    "B": 10.0,
    "C+": 12.0,
    "C": 18.0,
    "D": 40.0
}

# 抽卡参数
CARD_WIDTH = 360  #原720
CARD_HEIGHT = 540 #原1080
CARD_SPACING = 40
CARDS_PER_ROW = 5
TOTAL_CARDS = 10
# 动画设置
ANIMATION_DURATION = 0.5  # 秒
CARD_FLIP_DURATION = 0.3  # 秒
STAGGER_DELAY = 0.1       # 每张卡片之间的延迟

"""卡牌类"""
class Card:
    def __init__(self, image_path, rarity, position, index):
        self.image_path = image_path
        self.rarity = rarity
        self.target_position = position
        self.index = index
        
        # 加载图片
        try:
            self.image = pygame.image.load(self.image_path).convert_alpha()
        except Exception as e:
            self.image = pygame.Surface((200, 280))
            self.image.fill((100, 100, 150))
        
        # 获取卡牌详细数据
        self.card_database = get_card_database()
        self.card_data = self.card_database.get_card_by_path(image_path)
        
        # 如果数据库中没有，创建默认数据
        if not self.card_data:
            print(f"[card_system] 数据库中未找到卡牌数据: {self.image_path}")
            self.card_data = CardData(
                card_id=f"unknown_{index}",
                name="未知卡牌",
                rarity=rarity,
                atk=0,
                hp=0,
                cd=0,
                image_path=image_path
            )
        
        # 方便访问的属性
        self.rarity = self.card_data.rarity
        self.level = self.card_data.level
        
        # 动画相关
        self.current_position = (position[0], -CARD_HEIGHT)
        self.scale = 0.0
        self.alpha = 0
        self.rotation = 0
        self.animation_progress = 0
        self.flip_progress = 0
        
        # 鼠标悬停
        self.is_hovered = False
        
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
        
        # 使用稀有度颜色
        color = COLORS.get(self.card_data.rarity, (100, 100, 100))
        surface.fill(color)
        
        pygame.draw.rect(surface, (255, 255, 255), 
                        (0, 0, CARD_WIDTH, CARD_HEIGHT), max(3, int(3 * UI_SCALE)))
        
        # 使用数据库中的名称
        font_size = max(16, int(24 * UI_SCALE))
        font = get_font(font_size)
        
        # 名称（可能需要换行）
        name_lines = self._wrap_name(self.card_data.name, font, CARD_WIDTH - 20)
        y_offset = CARD_HEIGHT // 4
        for line in name_lines:
            name_text = font.render(line, True, (255, 255, 255))
            name_rect = name_text.get_rect(center=(CARD_WIDTH // 2, y_offset))
            surface.blit(name_text, name_rect)
            y_offset += int(30 * UI_SCALE)
        
        # ATK/HP
        font_small = get_font(max(12, int(16 * UI_SCALE)))
        stats_text = font_small.render(f"ATK:{self.card_data.atk} HP:{self.card_data.hp} CD:{self.card_data.cd}", 
                                       True, (255, 255, 255))
        stats_rect = stats_text.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT * 3 // 4))
        surface.blit(stats_text, stats_rect)
        
        # 稀有度标记
        rarity_text = font_small.render(f"[{self.card_data.rarity}]", True, (255, 255, 255))
        rarity_rect = rarity_text.get_rect(center=(CARD_WIDTH // 2, int(CARD_HEIGHT * 0.9)))
        surface.blit(rarity_text, rarity_rect)
        
        return surface
    
    def _wrap_name(self, name, font, max_width):
        """名称换行"""
        name_no_space = name.replace(' ', '') # 移除空格
        # 如果名称较短，直接返回
        test = font.render(name_no_space, True, (255, 255, 255))
        if test.get_width() <= max_width:
            return [name_no_space]
        
        # 否则分两行
        mid = len(name_no_space) // 2
        return [name_no_space[:mid], name_no_space[mid:]]
    
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
        
        font = get_font(int(45 * UI_SCALE))
        text = font.render("？？？", True, (200, 200, 200))
        text_rect = text.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT // 2))
        surface.blit(text, text_rect)
        
        return surface
    
    def create_glow_surface(self):
        """预创建发光效果surface"""
        glow_margin = max(10, int(10 * UI_SCALE))
        surface = pygame.Surface((CARD_WIDTH + glow_margin * 2, 
                                 CARD_HEIGHT + glow_margin * 2), 
                                pygame.SRCALPHA)
        color = COLORS.get(self.card_data.rarity, (255, 255, 255))
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
    
    def update_hover(self, mouse_pos):
        """更新悬停状态"""
        # 只有翻转完成后才检测悬停
        if self.flip_progress >= 1.0:
            # 检查鼠标是否在卡牌矩形内
            card_rect = pygame.Rect(
                self.current_position[0],
                self.current_position[1],
                CARD_WIDTH,
                CARD_HEIGHT
            )
            
            self.is_hovered = card_rect.collidepoint(mouse_pos)
            
            # 如果悬停，持续调用 show（tooltip 内部会处理延迟）
            if self.is_hovered:
                from ui.tooltip import get_tooltip
                tooltip = get_tooltip()
                tooltip.show(self.card_data, mouse_pos)
            else:
                # 离开时隐藏
                from ui.tooltip import get_tooltip
                tooltip = get_tooltip()
                if tooltip.card_data == self.card_data:
                    tooltip.hide()


class CardSystem:
    """卡牌系统"""
    def __init__(self):
        self.cards = []
        self.animation_start_time = 0
        self.is_animating = False
        
    def draw_one_card(self, prob=CARD_PROBABILITIES):
        """单抽"""
        card_pool = self.get_card_pool(prob=prob)
        level_dir, card_path = self.draw_single_card(card_pool, prob=prob)
        position = ((WINDOW_WIDTH - CARD_WIDTH) // 2, 
                    (WINDOW_HEIGHT - CARD_HEIGHT) // 2)
        card = Card(card_path, level_dir, position, 0)
        self.cards = [card]
        self.animation_start_time = 0
        self.is_animating = True
        return card

    def draw_ten_cards(self, prob=CARD_PROBABILITIES):
        """十连抽"""
        self.cards = []
        drawn_cards = []
        
        card_pool = self.get_card_pool(prob=prob)
        
        for i in range(TOTAL_CARDS):
            level_dir, card_path = self.draw_single_card(card_pool, prob=prob)
            row = i // CARDS_PER_ROW
            col = i % CARDS_PER_ROW
            
            total_width = CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_SPACING
            start_x = (WINDOW_WIDTH - total_width) // 2
            start_y = int(WINDOW_HEIGHT * 0.15) + row * (CARD_HEIGHT + CARD_SPACING)
            
            position = (start_x + col * (CARD_WIDTH + CARD_SPACING), start_y)
            
            card = Card(card_path, level_dir, position, i)
            drawn_cards.append(card)
        
        self.cards = drawn_cards
        self.animation_start_time = 0
        self.is_animating = True
        return drawn_cards
    
    def get_card_pool(self, prob=CARD_PROBABILITIES):
        """获取卡池，默认常驻卡池"""
        pool = {level_dir: [] for level_dir in prob.keys()}
        
        for level_dir in pool.keys():
            level_path = os.path.join("assets/outputs", level_dir) # 不能使用配置中的绝对路径
            if os.path.exists(level_path):
                files = [f for f in os.listdir(level_path) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                pool[level_dir] = [os.path.join(level_path, f) for f in files]
            
            # 如果没有找到图片，添加占位符
            if not pool[level_dir]:
                pool[level_dir] = [f"{level_dir}_placeholder_{i}.png" for i in range(5)]
        
        return pool
    
    def draw_single_card(self, card_pool, prob=CARD_PROBABILITIES):
        """抽取单张卡牌"""
        rand = random.randint(1, 100)
        cumulative = 0
        
        for level_dir, probability in prob.items():
            cumulative += probability
            if rand <= cumulative:
                if card_pool[level_dir]:
                    card_path = random.choice(card_pool[level_dir])
                    return level_dir, card_path

        # 如果概率计算未命中，降级到可用卡池的随机卡牌
        available_levels = [level for level, cards in card_pool.items() if cards]
        if available_levels:
            fallback_level = random.choice(available_levels)
            fallback_card = random.choice(card_pool[fallback_level])
            return fallback_level, fallback_card

        # 理论上不会发生，如果卡池为空则抛出异常以便定位问题
        raise ValueError("card_pool is empty; unable to draw card")
        
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
    
    def update_hover(self, mouse_pos):
        """更新所有卡牌的悬停状态"""
        for card in self.cards:
            card.update_hover(mouse_pos)
