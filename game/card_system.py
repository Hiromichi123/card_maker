"""卡牌系统"""
import math
import os
import random
import pygame
import config

cfg = config
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

# 抽卡参数（设计分辨率尺寸）
BASE_CARD_WIDTH = 360  # 原720
BASE_CARD_HEIGHT = 540 # 原1080
BASE_CARD_SPACING = 40
CARD_WIDTH = BASE_CARD_WIDTH
CARD_HEIGHT = BASE_CARD_HEIGHT
CARD_SPACING = BASE_CARD_SPACING

def apply_card_scale(scale):
    """按照可见区域缩放抽卡卡牌尺寸。"""
    global CARD_WIDTH, CARD_HEIGHT, CARD_SPACING
    factor = max(0.4, min(1.2, float(scale)))
    CARD_WIDTH = max(80, int(BASE_CARD_WIDTH * factor))
    CARD_HEIGHT = max(120, int(BASE_CARD_HEIGHT * factor))
    CARD_SPACING = max(12, int(BASE_CARD_SPACING * factor))
CARDS_PER_ROW = 5
TOTAL_CARDS = 10
# 动画设置
ANIMATION_DURATION = 0.5  # 秒
CARD_FLIP_DURATION = 0.3  # 秒
STAGGER_DELAY = 0.1       # 每张卡片之间的延迟

HIGH_RARITY_LEVELS = {"A", "A+", "S", "S+", "SS", "SS+", "SSS", "#elna"}

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
        self.is_high_rarity = self.rarity in HIGH_RARITY_LEVELS
        self.entry_duration = ANIMATION_DURATION * (1.35 if self.is_high_rarity else 1.0)
        self.flip_duration = CARD_FLIP_DURATION * (1.35 if self.is_high_rarity else 1.0)
        self.post_flip_timer = 0.0
        self.bright_phase_duration = 0.6 if self.is_high_rarity else 0.35
        self.dim_phase_duration = 1.8 if self.is_high_rarity else 0.45
        self.glow_timer = 0.0
        self.glow_speed = 4.5 if self.is_high_rarity else 2.4
        self.glow_margin = (
            max(14, int(14 * cfg.UI_SCALE))
            if self.is_high_rarity else max(10, int(10 * cfg.UI_SCALE))
        )
        if self.is_high_rarity:
            self.glow_min_alpha = 130
            self.glow_max_alpha = 255
        else:
            self.glow_min_alpha = 60
            self.glow_max_alpha = 170
        
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
        color = cfg.COLORS.get(self.card_data.rarity, (100, 100, 100))
        surface.fill(color)
        
        pygame.draw.rect(surface, (255, 255, 255), 
                (0, 0, CARD_WIDTH, CARD_HEIGHT), max(3, int(3 * cfg.UI_SCALE)))
        
        # 使用数据库中的名称
        font_size = max(16, int(24 * cfg.UI_SCALE))
        font = cfg.get_font(font_size)
        
        # 名称（可能需要换行）
        name_lines = self._wrap_name(self.card_data.name, font, CARD_WIDTH - 20)
        y_offset = CARD_HEIGHT // 4
        for line in name_lines:
            name_text = font.render(line, True, (255, 255, 255))
            name_rect = name_text.get_rect(center=(CARD_WIDTH // 2, y_offset))
            surface.blit(name_text, name_rect)
            y_offset += int(30 * cfg.UI_SCALE)
        
        # ATK/HP
        font_small = cfg.get_font(max(12, int(16 * cfg.UI_SCALE)))
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
        
        border_width = (
            max(7, int(7 * cfg.UI_SCALE))
            if self.is_high_rarity else max(5, int(5 * cfg.UI_SCALE))
        )
        border_margin = max(10, int(10 * cfg.UI_SCALE))
        pygame.draw.rect(surface, (100, 100, 150), 
                        (border_margin, border_margin, 
                         CARD_WIDTH - border_margin * 2, 
                         CARD_HEIGHT - border_margin * 2), border_width)
        
        font = cfg.get_font(int(45 * cfg.UI_SCALE))
        text = font.render("？？？", True, (200, 200, 200))
        text_rect = text.get_rect(center=(CARD_WIDTH // 2, CARD_HEIGHT // 2))
        surface.blit(text, text_rect)
        
        return surface
    
    def create_glow_surface(self):
        """预创建发光效果surface"""
        surface = pygame.Surface((CARD_WIDTH + self.glow_margin * 2, 
                                 CARD_HEIGHT + self.glow_margin * 2), 
                                pygame.SRCALPHA)
        color = cfg.COLORS.get(self.card_data.rarity, (255, 255, 255))
        border_width = (
            max(8, int(8 * cfg.UI_SCALE))
            if self.is_high_rarity else max(5, int(5 * cfg.UI_SCALE))
        )
        pygame.draw.rect(surface, (*color, 140), 
                        (0, 0, CARD_WIDTH + self.glow_margin * 2, 
                         CARD_HEIGHT + self.glow_margin * 2), border_width)
        return surface
    
    def update(self, dt, start_time):
        """更新卡牌动画"""
        delay = self.index * STAGGER_DELAY
        elapsed = start_time - delay
        self.glow_timer += dt
        
        if elapsed < 0:
            return
        
        if self.animation_progress < 1.0:
            self.animation_progress = min(1.0, elapsed / self.entry_duration)
            t = self.ease_out_bounce(self.animation_progress)
            
            start_y = -CARD_HEIGHT
            self.current_position = (
                self.target_position[0],
                start_y + (self.target_position[1] - start_y) * t
            )
            
            self.scale = t
            self.alpha = int(255 * t)
        
        elif self.flip_progress < 1.0:
            flip_elapsed = elapsed - self.entry_duration
            if flip_elapsed >= 0:
                self.flip_progress = min(1.0, flip_elapsed / self.flip_duration)
                self.rotation = self.flip_progress * 180
        
        if self.flip_progress >= 1.0:
            max_phase = self.bright_phase_duration + self.dim_phase_duration
            self.post_flip_timer = min(self.post_flip_timer + dt, max_phase)
        else:
            self.post_flip_timer = 0.0
    
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
        
        if self.flip_progress >= 1.0 and self.is_high_rarity:
            self._apply_high_rarity_shading(scaled_img)

        screen.blit(scaled_img, pos)

        target_rect = pygame.Rect(pos[0], pos[1], width, height)
        if self.animation_progress > 0 and self.flip_progress >= 0.2:
            self.draw_rarity_glow(screen, target_rect)

    def _apply_high_rarity_shading(self, surface):
        """按需调整高稀有卡牌卡面高亮（当前要求移除卡面高亮）"""
        return

    def _get_border_highlight_ratio(self):
        if not self.is_high_rarity or self.post_flip_timer <= 0:
            return 0.0
        total_duration = self.bright_phase_duration + self.dim_phase_duration
        if total_duration <= 0:
            return 0.0
        norm = min(self.post_flip_timer / total_duration, 1.0)
        if norm <= 0:
            return 0.0
        bright_ratio = self.bright_phase_duration / total_duration
        if bright_ratio <= 0:
            return max(0.0, 1.0 - norm)

        if norm <= bright_ratio:
            local = norm / max(bright_ratio, 1e-3)
            # smoothstep from 1 to 0 during bright phase
            return 1.0 - (local * local * (3 - 2 * local))
        fade_local = (norm - bright_ratio) / max(1.0 - bright_ratio, 1e-3)
        fade_local = max(0.0, min(fade_local, 1.0))
        return max(0.0, 1.0 - fade_local)
    
    def draw_rarity_glow(self, screen, target_rect):
        """绘制带呼吸效果的稀有度光效"""
        glow_width = target_rect.width + self.glow_margin * 2
        glow_height = target_rect.height + self.glow_margin * 2
        cache_key = ("glow", glow_width, glow_height)
        pulse = (math.sin(self.glow_timer * self.glow_speed) + 1) / 2
        glow_alpha = int(self.glow_min_alpha + (self.glow_max_alpha - self.glow_min_alpha) * pulse)

        if self.is_high_rarity:
            highlight_ratio = self._get_border_highlight_ratio()
            base_color = cfg.COLORS.get(self.card_data.rarity, (255, 255, 255))
            mix_color = tuple(
                int(base_color[i] + (255 - base_color[i]) * highlight_ratio)
                for i in range(3)
            )
            border_width = max(8, int(8 * cfg.UI_SCALE))
            glow_surface = pygame.Surface((glow_width, glow_height), pygame.SRCALPHA)
            pygame.draw.rect(
                glow_surface,
                (*mix_color, glow_alpha),
                (0, 0, glow_width, glow_height),
                border_width
            )
            screen.blit(
                glow_surface,
                (target_rect.x - self.glow_margin, target_rect.y - self.glow_margin)
            )
            return

        cache_key = ("glow", glow_width, glow_height)
        if cache_key not in self.cached_surfaces:
            self.cached_surfaces[cache_key] = pygame.transform.smoothscale(
                self.glow_surface, (glow_width, glow_height)
            )
        glow_copy = self.cached_surfaces[cache_key].copy()
        glow_copy.set_alpha(glow_alpha)
        screen.blit(
            glow_copy,
            (target_rect.x - self.glow_margin, target_rect.y - self.glow_margin)
        )
    
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
        surface_w = max(1, cfg.VISIBLE_WIDTH)
        surface_h = max(1, cfg.VISIBLE_HEIGHT)
        position = ((surface_w - CARD_WIDTH) // 2, 
            (surface_h - CARD_HEIGHT) // 2)
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
            
            surface_w = max(1, cfg.VISIBLE_WIDTH)
            surface_h = max(1, cfg.VISIBLE_HEIGHT)
            total_width = CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_SPACING
            start_x = (surface_w - total_width) // 2
            start_y = int(surface_h * 0.15) + row * (CARD_HEIGHT + CARD_SPACING)
            
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

        if not self.cards:
            return

        all_flipped = True
        for card in self.cards:
            card.update(dt, self.animation_start_time)
            if card.flip_progress < 1.0:
                all_flipped = False

        if self.is_animating and all_flipped:
            self.is_animating = False
    
    def draw(self, screen):
        """绘制所有卡牌"""
        for card in self.cards:
            card.draw(screen)
    
    def update_hover(self, mouse_pos):
        """更新所有卡牌的悬停状态"""
        for card in self.cards:
            card.update_hover(mouse_pos)
