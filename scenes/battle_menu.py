"""
战斗菜单场景
"""
import pygame
from scenes.base_scene import BaseScene
from ui.menu_button import MenuButton
from ui.background import ParallaxBackground
from config import *
from config import get_font

class BattleMenuScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        
        # 创建视差背景
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "battle")
        
        # 标题
        title_font_size = max(48, int(96 * UI_SCALE))
        self.title_font = get_font(title_font_size)
        
        # 按钮配置 - 右侧阶梯布局
        button_width = int(300 * UI_SCALE)
        button_height = int(50 * UI_SCALE)
        
        # 起始位置（右侧）
        base_x = int(WINDOW_WIDTH * 0.75)
        start_y = int(WINDOW_HEIGHT * 0.25)
        button_spacing = int(90 * UI_SCALE)
        stagger_offset = int(30 * UI_SCALE)  # 阶梯偏移
        
        self.buttons = []
        
        # 战斗1
        battle_btn1 = MenuButton(
            base_x, 
            start_y,
            button_width, 
            button_height,
            "单人战役",
            color=(200, 50, 50),
            hover_color=(255, 80, 80),
            on_click=lambda: self.switch_to("battle")
        )
        self.buttons.append(battle_btn1)

        # 战斗2
        battle_btn2 = MenuButton(
            base_x - stagger_offset, 
            start_y + button_spacing,
            button_width, 
            button_height,
            "局域网 卡组对战",
            color=(200, 70, 50),
            hover_color=(255, 100, 80),
            on_click=lambda: self.switch_to("battle")
        )
        self.buttons.append(battle_btn2)

        # 战斗3
        battle_btn3 = MenuButton(
            base_x - stagger_offset * 2, 
            start_y + button_spacing * 2,
            button_width, 
            button_height,
            "局域网 任选对战",
            color=(200, 90, 50),
            hover_color=(255, 120, 80),
            on_click=lambda: self.switch_to("battle")
        )
        self.buttons.append(battle_btn3)

        # 战斗4
        battle_btn4 = MenuButton(
            base_x - stagger_offset * 3, 
            start_y + button_spacing * 3,
            button_width, 
            button_height,
            "本地 任选对战（双人）",
            color=(200, 110, 50),
            hover_color=(255, 140, 80),
            on_click=lambda: self.switch_to("draft_scene")
        )
        self.buttons.append(battle_btn4)
        
        # 返回主菜单按钮
        back_btn = MenuButton(
            base_x - stagger_offset * 4,
            start_y + button_spacing * 4,
            button_width,
            button_height,
            "返回主菜单",
            color=(100, 150, 255),
            hover_color=(150, 200, 255),
            on_click=lambda: self.switch_to("main_menu")
        )
        self.buttons.append(back_btn)
        
        self.quit_flag = False
        
    def quit_game(self):
        """退出游戏"""
        self.quit_flag = True
    
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_flag = True
        
        # 更新视差背景
        if event.type == pygame.MOUSEMOTION:
            self.background.update_mouse_position(event.pos)
        
        # 按钮事件
        for button in self.buttons:
            button.handle_event(event)
    
    def update(self, dt):
        """更新"""
        # 更新背景
        self.background.update(dt)
        
        # 更新按钮动画
        for button in self.buttons:
            button.update(dt)
    
    def draw(self):
        """绘制"""
        # 绘制背景
        self.background.draw(self.screen)
        
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
        
        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen)
