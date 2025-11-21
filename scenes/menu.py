"""
主菜单场景
"""
import pygame
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.panel import Panel
from config import *
from config import get_font

class MainMenuScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        
        # 创建背景
        self.background = self.create_background()
        
        # 标题
        title_font_size = max(48, int(96 * UI_SCALE))
        self.title_font = get_font(title_font_size)
        
        # 创建面板
        panel_width = int(WINDOW_WIDTH * 0.4)
        panel_height = int(WINDOW_HEIGHT * 0.6)
        panel_x = (WINDOW_WIDTH - panel_width) // 2
        panel_y = int(WINDOW_HEIGHT * 0.25)
        
        self.panel = Panel(panel_x, panel_y, panel_width, panel_height)
        
        # 创建按钮
        button_width = int(panel_width * 0.7)
        button_height = int(60 * UI_SCALE)
        button_x = panel_x + (panel_width - button_width) // 2
        button_spacing = int(80 * UI_SCALE)
        
        self.buttons = []
        
        # 战斗按钮
        battle_btn = Button(
            button_x, 
            panel_y + int(120 * UI_SCALE),
            button_width, 
            button_height,
            "开始战斗",
            color=(200, 50, 50),  # 红色表示战斗
            hover_color=(230, 80, 80),
            on_click=lambda: self.switch_to("battle")
        )
        self.buttons.append(battle_btn)

        # 抽卡按钮
        gacha_btn = Button(
            button_x, 
            panel_y + int(120 * UI_SCALE) + button_spacing,
            button_width, 
            button_height,
            "抽卡",
            color=(255, 140, 0),
            hover_color=(255, 165, 0),
            on_click=lambda: self.switch_to("gacha")
        )
        self.buttons.append(gacha_btn)

        # 卡组配置按钮
        deck_btn = Button(
            button_x, 
            panel_y + int(120 * UI_SCALE) + button_spacing * 2,
            button_width, 
            button_height,
            "出战卡组配置",
            color=(100, 150, 255),
            hover_color=(130, 180, 255),
            on_click=lambda: self.switch_to("deck_builder")
        )
        self.buttons.append(deck_btn)
        
        # 图鉴按钮
        collection_btn = Button(
            button_x,
            panel_y + int(120 * UI_SCALE) + button_spacing * 3,
            button_width,
            button_height,
            "卡牌图鉴",
            color=(100, 150, 255),
            hover_color=(130, 180, 255),
            on_click=lambda: self.switch_to("collection")
        )
        self.buttons.append(collection_btn)
        
        # 设置按钮
        settings_btn = Button(
            button_x,
            panel_y + int(120 * UI_SCALE) + button_spacing * 4,
            button_width,
            button_height,
            "设置",
            color=(100, 150, 255),
            hover_color=(130, 180, 255),
            on_click=lambda: self.switch_to("settings")
        )
        self.buttons.append(settings_btn)
        
        # 退出按钮
        quit_btn = Button(
            button_x,
            panel_y + int(120 * UI_SCALE) + button_spacing * 5,
            button_width,
            button_height,
            "退出游戏",
            color=(200, 50, 50),
            hover_color=(255, 70, 70),
            on_click=self.quit_game
        )
        self.buttons.append(quit_btn)
        
        self.quit_flag = False
        
    def create_background(self):
        """创建背景"""
        bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        bg.fill(BACKGROUND_COLOR)
        
        # 网格
        grid_size = max(20, int(40 * UI_SCALE))
        for x in range(0, WINDOW_WIDTH, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (0, y), (WINDOW_WIDTH, y), 1)
        
        return bg
    
    def quit_game(self):
        """退出游戏"""
        self.quit_flag = True
    
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_flag = True
        
        # 按钮事件
        for button in self.buttons:
            button.handle_event(event)
    
    def update(self, dt):
        """更新"""
        pass
    
    def draw(self):
        """绘制"""
        # 绘制背景
        self.screen.blit(self.background, (0, 0))
        
        # 绘制标题
        title_text = self.title_font.render("抽卡模拟器", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.12)))
        
        # 标题阴影
        shadow_offset = max(3, int(3 * UI_SCALE))
        shadow_text = self.title_font.render("抽卡模拟器", True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(center=(WINDOW_WIDTH // 2 + shadow_offset, 
                                                   int(WINDOW_HEIGHT * 0.12) + shadow_offset))
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        # 绘制面板
        self.panel.draw(self.screen)
        
        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen)