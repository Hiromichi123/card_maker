"""战斗菜单场景"""
import pygame
from config import *
from scenes.base_scene import BaseScene
from ui.menu_button import MenuButton
from ui.background import ParallaxBackground
from ui.system_ui import CurrencyLevelUI

class BattleMenuScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        
        # 创建视差背景
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "battle_menu")
        
        # 标题
        title_font_size = max(48, int(96 * UI_SCALE))
        self.title_font = get_font(title_font_size)
        
        # 按钮配置 - 右侧阶梯布局
        self.button_width = int(300 * UI_SCALE)
        self.button_height = int(50 * UI_SCALE)
        
        # 起始位置（右侧）
        self.base_x = int(WINDOW_WIDTH * 0.75)
        self.start_y = int(WINDOW_HEIGHT * 0.25)
        self.button_spacing = int(90 * UI_SCALE)
        self.stagger_offset = int(30 * UI_SCALE)  # 阶梯偏移
        
        # 货币和等级 UI
        self.currency_ui = CurrencyLevelUI()
        self.currency_ui.load_state()

        self.buttons = []
        self.create_buttons() # 创建按钮列表
        self.quit_flag = False  # 退出标志
        
    def quit_game(self):
        """退出游戏"""
        self.quit_flag = True
    
    def handle_event(self, event):
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
        self.background.update(dt) # 背景
        
        # 更新按钮动画
        for button in self.buttons:
            button.update(dt)
    
    def draw(self):
        self.background.draw(self.screen) # 背景
        
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

        self.currency_ui.draw(self.screen) # 货币和等级 UI
        
        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen)

    def create_buttons(self):
        # 单人战役
        battle_btn1 = MenuButton(
            self.base_x, self.start_y,
            self.button_width, self.button_height,
            "单人战役",
            color=(200, 50, 50), hover_color=(255, 80, 80),
            on_click=lambda: self.switch_to("simple_battle")
        )
        self.buttons.append(battle_btn1)

        # 局域网 卡组对战
        battle_btn2 = MenuButton(
            self.base_x - self.stagger_offset, 
            self.start_y + self.button_spacing,
            self.button_width, self.button_height,
            "局域网 卡组对战",
            color=(200, 70, 50), hover_color=(255, 100, 80),
            on_click=lambda: self.switch_to("simple_battle")
        )
        self.buttons.append(battle_btn2)

        # 局域网 任选对战
        battle_btn3 = MenuButton(
            self.base_x - self.stagger_offset * 2, 
            self.start_y + self.button_spacing * 2,
            self.button_width, self.button_height,
            "局域网 任选对战",
            color=(200, 90, 50), hover_color=(255, 120, 80),
            on_click=lambda: self.switch_to("simple_battle")
        )
        self.buttons.append(battle_btn3)

        # 本地 任选对战（双人）
        battle_btn4 = MenuButton(
            self.base_x - self.stagger_offset * 3, 
            self.start_y + self.button_spacing * 3,
            self.button_width, self.button_height,
            "本地 任选对战（双人）",
            color=(200, 110, 50), hover_color=(255, 140, 80),
            on_click=lambda: self.switch_to("draft_scene")
        )
        self.buttons.append(battle_btn4)

        # 返回主菜单
        back_btn = MenuButton(
            self.base_x - self.stagger_offset * 4,
            self.start_y + self.button_spacing * 4,
            self.button_width, self.button_height,
            "返回主菜单",
            color=(100, 150, 255), hover_color=(150, 200, 255),
            on_click=lambda: self.switch_to("main_menu")
        )
        self.buttons.append(back_btn)
        