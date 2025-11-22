"""抽卡场景"""
import pygame
from streamlit import event
from scenes.base_scene import BaseScene
from ui.button import Button
from game.card_system import CardSystem
from utils.inventory import get_inventory
from config import *

# 卡牌设置
CARD_WIDTH = 360  #原720
CARD_HEIGHT = 540 #原1080
CARD_SPACING = 40

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
        button_width = int(300 * UI_SCALE)
        button_height = int(90 * UI_SCALE)
        button_spacing = int(30 * UI_SCALE)
        
        # 抽卡按钮
        self.draw_button = Button(
            WINDOW_WIDTH // 2 - button_width - button_spacing // 2,
            int(WINDOW_HEIGHT * 0.85),
            button_width,
            button_height,
            "4500G 抽10连",
            color=(255, 140, 0),
            hover_color=(255, 165, 0),
            on_click=self.draw_cards
        )
        
        # 返回按钮
        self.back_button = Button(
            WINDOW_WIDTH // 2 + button_spacing // 2,
            int(WINDOW_HEIGHT * 0.85),
            button_width,
            button_height,
            "返回主菜单",
            color=(100, 150, 255),
            hover_color=(130, 180, 255),
            on_click=lambda: self.switch_to("main_menu")
        )

    """创建背景"""
    def create_background(self):
        bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        bg.fill(BACKGROUND_COLOR)
        
        grid_size = max(20, int(40 * UI_SCALE))
        for x in range(0, WINDOW_WIDTH, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (0, y), (WINDOW_WIDTH, y), 1)
        
        return bg
    
    """抽卡"""
    def draw_cards(self):
        if not self.card_system.is_animating:
            drawn_cards = self.card_system.draw_cards() # 执行抽卡
            
            # 保存到库存
            cards_to_save = [(card.image_path, card.rarity) 
                            for card in self.card_system.cards]
            self.inventory.add_cards(cards_to_save)

    """获取鼠标悬停的卡牌数据"""
    def get_hovered_card(self, mouse_pos):
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
    
    """处理事件"""
    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")
            elif event.key == pygame.K_SPACE:
                self.draw_cards()

        # 按钮事件
        self.draw_button.handle_event(event)
        self.back_button.handle_event(event)
    
    """更新"""
    def update(self, dt):
        self.card_system.update(dt)
    
    """绘制"""
    def draw(self):
        self.screen.blit(self.background, (0, 0)) # 背景
        self.draw_title() # 标题
        self.card_system.draw(self.screen) # 卡牌
        self.draw_button.draw(self.screen) # 抽卡按钮
        self.back_button.draw(self.screen) # 返回按钮
        self.draw_probability_info() # 概率信息
    
    def draw_title(self):
        """绘制标题"""
        title_y = int(WINDOW_HEIGHT * 0.04)
        title_text = self.title_font.render("抽卡模拟器", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, title_y))
        
        shadow_offset = max(2, int(2 * UI_SCALE))
        shadow_text = self.title_font.render("抽卡模拟器", True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(center=(WINDOW_WIDTH // 2 + shadow_offset, 
                                                   title_y + shadow_offset))
        
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
    
    def draw_probability_info(self):
        """绘制概率信息"""
        y_offset = int(WINDOW_HEIGHT * 0.92)
        x_start = int(WINDOW_WIDTH * 0.05)
        x_spacing = int(WINDOW_WIDTH * 0.12)
        
        for idx, (rarity, prob) in enumerate(CARD_PROBABILITIES.items()):
            color = COLORS.get(rarity, (255, 255, 255))
            info_text = f"{rarity}({prob}%)"
            text = self.info_font.render(info_text, True, color)
            self.screen.blit(text, (x_start + idx * x_spacing, y_offset))