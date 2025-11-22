"""
战斗菜单场景
"""
import pygame
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.panel import Panel
from config import *
from config import get_font

class BattleMenuScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.background = self.create_background() # 创建背景
        title_font_size = max(48, int(96 * UI_SCALE))
        self.title_font = get_font(title_font_size) # 标题
        
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
        
        # 战斗1
        battle_btn1 = Button(
            button_x, 
            panel_y + int(120 * UI_SCALE),
            button_width, 
            button_height,
            "单人战役",
            color=(200, 50, 50),  # 红色
            hover_color=(230, 80, 80),
            on_click=lambda: self.switch_to("battle")
        )
        self.buttons.append(battle_btn1)

        # 战斗2
        battle_btn2 = Button(
            button_x, 
            panel_y + int(120 * UI_SCALE) + button_spacing,
            button_width, 
            button_height,
            "局域网 卡组对战",
            color=(200, 50, 50),  # 红色
            hover_color=(230, 80, 80),
            on_click=lambda: self.switch_to("battle")
        )
        self.buttons.append(battle_btn2)

        # 战斗3
        battle_btn3 = Button(
            button_x, 
            panel_y + int(120 * UI_SCALE) + button_spacing * 2,
            button_width, 
            button_height,
            "局域网 任选对战",
            color=(200, 50, 50),  # 红色
            hover_color=(230, 80, 80),
            on_click=lambda: self.switch_to("battle")
        )
        self.buttons.append(battle_btn3)

        # 战斗4
        battle_btn4 = Button(
            button_x, 
            panel_y + int(120 * UI_SCALE) + button_spacing * 3,
            button_width, 
            button_height,
            "本地 任选对战（双人）",
            color=(200, 50, 50),  # 红色
            hover_color=(230, 80, 80),
            on_click=lambda: self.switch_to("draft_scene")
        )
        self.buttons.append(battle_btn4)
        
        # 返回主菜单按钮
        back_btn = Button(
            button_x,
            panel_y + int(120 * UI_SCALE) + button_spacing * 4,
            button_width,
            button_height,
            "返回主菜单",
            color=(100, 150, 255),
            hover_color=(130, 180, 255),
            on_click=lambda: self.switch_to("main_menu")
        )
        self.buttons.append(back_btn)
        
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
        title_text = self.title_font.render("选择对战模式", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.12)))
        
        # 标题阴影
        shadow_offset = max(3, int(3 * UI_SCALE))
        shadow_text = self.title_font.render("选择对战模式", True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(center=(WINDOW_WIDTH // 2 + shadow_offset, 
                                                   int(WINDOW_HEIGHT * 0.12) + shadow_offset))
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
        
        # 绘制面板
        self.panel.draw(self.screen)
        
        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen)
