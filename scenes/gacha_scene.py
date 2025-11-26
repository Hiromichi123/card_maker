"""抽卡场景"""
import pygame
from scenes.base_scene import BaseScene
from ui.button import Button
from game.card_system import CardSystem
from utils.inventory import get_inventory
from config import *

# 常驻卡池概率
simple_prob = {
    "SSS": 0.5,  # SSS - 0.5%
    "SS": 1.5,   # SS - 1.5%
    "S": 2.5,    # S - 2.5%
    "A": 8.5,    # A - 8.5%
    #=====以上13%，以下87%=====
    "B": 17,     # B - 17%
    "C": 30,     # C - 30%
    "D": 40      # D - 40%
}

activity_prob = {
    "SSS": 1.0,  # SSS - 1.0%
    "SS": 3.0,   # SS - 3.0%
    "S": 5.0,    # S - 5.0%
    "A": 17.0,   # A - 17.0%
    #=====以上26%，以下74%=====
    "B": 24,     # B - 24%
    "C": 25,     # C - 25%
    "D": 25      # D - 25%
}

high_prob = {
    "SSS": 20.0,  # SSS - 20.0%
    "SS": 20.0,   # SS - 20.0%
    "S": 20.0,    # S - 20.0%
    "A": 40.0,    # A - 40.0%
}

CARD_WIDTH = int(360 * UI_SCALE)
CARD_HEIGHT = int(540 * UI_SCALE)

"""抽卡场景"""
class GachaScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.background = self.create_background() # 创建背景
        self.card_system = CardSystem() # 卡牌系统
        self.inventory = get_inventory() # 库存系统
        
        # 字体
        self.title_font = get_font(max(32, int(64 * UI_SCALE)))
        self.info_font = get_font(max(12, int(24 * UI_SCALE)))
        
        # 创建按钮
        self.create_button()
    
    """==========核心方法=========="""
    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")
            elif event.key == pygame.K_SPACE:
                self.draw_cards()

        # 按钮事件
        self.draw_one_button.handle_event(event)
        self.draw_ten_button.handle_event(event)
        self.high_prob_button.handle_event(event)
        self.back_button.handle_event(event)
    
    def update(self, dt):
        self.card_system.update(dt)
    
    def get_hovered_card(self, mouse_pos):
        """获取鼠标悬停的卡牌数据"""
        for card in self.card_system.cards:
            # 只检测已经翻开的卡牌（动画完成）
            if card.flip_progress >= 1.0:
                # 创建卡牌的矩形区域
                card_rect = pygame.Rect(
                    card.current_position[0],
                    card.current_position[1],
                    CARD_WIDTH,
                    CARD_HEIGHT
                )
                
                # 检测鼠标是否在卡牌范围内
                if card_rect.collidepoint(mouse_pos):
                    return card.card_data
        return None

    """==========绘制场景=========="""
    def draw(self):
        self.screen.blit(self.background, (0, 0)) # 背景
        self.draw_title() # 标题
        self.card_system.draw(self.screen) # 卡牌
        self.draw_probability_info() # 概率信息
        self.draw_button() # 按钮
    
    def draw_title(self):
        """绘制标题"""
        title_y = int(WINDOW_HEIGHT * 0.04)
        title_text = self.title_font.render("常规卡池", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, title_y))
        
        shadow_offset = max(2, int(2 * UI_SCALE))
        shadow_text = self.title_font.render("常规卡池", True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(center=(WINDOW_WIDTH // 2 + shadow_offset, 
                                                   title_y + shadow_offset))
        
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
    
    def draw_probability_info(self, prob=simple_prob):
        """绘制概率信息"""
        y_offset = int(WINDOW_HEIGHT * 0.92)
        x_start = int(WINDOW_WIDTH * 0.05)
        x_spacing = int(WINDOW_WIDTH * 0.12)
        for idx, (rarity, prob) in enumerate(prob.items()):
            color = COLORS.get(rarity, (255, 255, 255))
            info_text = f"{rarity}({prob}%)"
            text = self.info_font.render(info_text, True, color)
            self.screen.blit(text, (x_start + idx * x_spacing, y_offset))

    def draw_button(self):
        self.draw_one_button.draw(self.screen) # 单抽按钮
        self.draw_ten_button.draw(self.screen) # 十连抽按钮
        self.high_prob_button.draw(self.screen) # 高概率测试按钮
        self.back_button.draw(self.screen) # 返回按钮

    """==========初始化=========="""
    def create_background(self):
        """创建背景"""
        bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        bg.fill(BACKGROUND_COLOR)
        
        grid_size = max(20, int(40 * UI_SCALE))
        for x in range(0, WINDOW_WIDTH, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (0, y), (WINDOW_WIDTH, y), 1)
        
        return bg
    
    def create_button(self):
        button_width = int(300 * UI_SCALE)
        button_height = int(90 * UI_SCALE)
        button_spacing = int(30 * UI_SCALE)
        
        # 单抽按钮
        self.draw_one_button = Button(
            WINDOW_WIDTH//2-button_width*2-button_spacing//2,
            int(WINDOW_HEIGHT * 0.85),
            button_width, button_height,
            "500G 抽1张",
            color=(255, 140, 0), hover_color=(255, 165, 0),
            on_click=self.draw_one_card
        )

        # 十连抽按钮
        self.draw_ten_button = Button(
            WINDOW_WIDTH//2-button_width-button_spacing//2,
            int(WINDOW_HEIGHT * 0.85),
            button_width, button_height,
            "4500G 抽10连",
            color=(255, 140, 0), hover_color=(255, 165, 0),
            on_click=self.draw_ten_cards
        )
        
        # 高概率测试
        self.high_prob_button = Button(
            WINDOW_WIDTH//2-button_width*3-button_spacing//2,
            int(WINDOW_HEIGHT * 0.85),
            button_width, button_height,
            "高概率测试",
            color=(255, 140, 0), hover_color=(255, 165, 0),
            on_click=lambda: self.draw_ten_cards(prob=high_prob)
        )

        # 返回按钮
        self.back_button = Button(
            WINDOW_WIDTH // 2 + button_spacing // 2,
            int(WINDOW_HEIGHT * 0.85),
            button_width, button_height,
            "返回主菜单",
            color=(100, 150, 255), hover_color=(130, 180, 255),
            on_click=lambda: self.switch_to("main_menu")
        )

    """==========抽卡辅助=========="""
    def draw_one_card(self, prob=simple_prob):
        """单抽"""
        if not self.card_system.is_animating:
            drawn_card = self.card_system.draw_one_card(prob=prob)
            self.inventory.add_card(drawn_card.image_path, drawn_card.rarity) # 保存到库存
    
    def draw_ten_cards(self, prob=simple_prob):
        """十连抽卡"""
        if not self.card_system.is_animating:
            drawn_cards = self.card_system.draw_ten_cards(prob=prob)
            # 保存到库存
            cards_to_save = [(card.image_path, card.rarity) for card in drawn_cards]
            self.inventory.add_cards(cards_to_save)
