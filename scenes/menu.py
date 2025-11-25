"""主菜单场景"""
import pygame
from config import *
from scenes.base_scene import BaseScene
from ui.menu_button import MenuButton
from ui.background import ParallaxBackground
from ui.system_ui import CurrencyLevelUI
from ui.activity_poster import PosterUI

# 海报跳转映射表：index -> scene_name
poster_to_scene = {
    0: "gacha",
    1: "battle_menu"
}

# 海报位置
poster_topleft = (int(WINDOW_WIDTH * 0.6), int(WINDOW_HEIGHT * 0.6))

class MainMenuScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        
        # 创建视差背景
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "menu")
        
        # 标题
        title_font_size = max(48, int(96 * UI_SCALE))
        self.title_font = get_font(title_font_size)

        # 货币和等级 UI
        self.currency_ui = CurrencyLevelUI()
        self.currency_ui.load_state()
        
        # 活动海报轮播控件
        self.poster_ui = PosterUI()
        self.poster_ui.on_click = self._on_poster_click
        
        # 按钮配置 - 右侧阶梯布局
        self.button_width = int(300 * UI_SCALE)
        self.button_height = int(50 * UI_SCALE)
        
        # 起始位置（右侧）
        self.base_x = int(WINDOW_WIDTH * 0.75)
        self.start_y = int(WINDOW_HEIGHT * 0.25)
        self.button_spacing = int(90 * UI_SCALE)
        self.stagger_offset = int(30 * UI_SCALE)  # 阶梯偏移
        
        self.buttons = []
        self.create_buttons() # 创建按钮列表
        self.quit_flag = False   # 退出标志
    
    def quit_game(self):
        """退出游戏"""
        self.quit_flag = True
    
    def handle_event(self, event):
        # 退出事件
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_flag = True
        
        # 更新视差背景
        if event.type == pygame.MOUSEMOTION:
            self.background.update_mouse_position(event.pos)
        
        # 活动海报事件
        self.poster_ui.handle_event(event)

        # 按钮事件
        for button in self.buttons:
            button.handle_event(event)
    
    def update(self, dt):
        self.background.update(dt) # 背景
        self.poster_ui.update(dt) # 活动海报轮播控件

        # 更新按钮动画
        for button in self.buttons:
            button.update(dt)
    
    def draw(self):
        self.background.draw(self.screen) # 背景
        
        # 绘制标题
        title_text = self.title_font.render("Card Battle Master Simulator v1.0", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.12)))
        
        # 标题阴影
        shadow_offset = max(3, int(3 * UI_SCALE))
        shadow_text = self.title_font.render("Card Battle Master Simulator v1.0", True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(center=(WINDOW_WIDTH // 2 + shadow_offset, 
                                                   int(WINDOW_HEIGHT * 0.12) + shadow_offset))
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)

        self.currency_ui.draw(self.screen) # 货币和等级 UI
        self.poster_ui.draw(self.screen, poster_topleft) #绘制活动海报
        
        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen)

    def create_buttons(self):
        # 战斗按钮
        battle_btn = MenuButton(
            self.base_x, self.start_y,
            self.button_width, self.button_height,
            "进入战斗",
            color=(200, 50, 50), hover_color=(255, 80, 80),
            on_click=lambda: self.switch_to("battle_menu")
        )
        self.buttons.append(battle_btn)

        # 抽卡按钮
        gacha_btn = MenuButton(
            self.base_x - self.stagger_offset, 
            self.start_y + self.button_spacing,
            self.button_width, self.button_height,
            "抽卡",
            color=(255, 140, 0), hover_color=(255, 180, 50),
            on_click=lambda: self.switch_to("gacha")
        )
        self.buttons.append(gacha_btn)

        # 卡组配置按钮
        deck_btn = MenuButton(
            self.base_x - self.stagger_offset * 2, 
            self.start_y + self.button_spacing * 2,
            self.button_width, self.button_height,
            "出战卡组配置",
            color=(100, 150, 255), hover_color=(150, 200, 255),
            on_click=lambda: self.switch_to("deck_builder")
        )
        self.buttons.append(deck_btn)
        
        # 图鉴按钮
        collection_btn = MenuButton(
            self.base_x - self.stagger_offset * 3,
            self.start_y + self.button_spacing * 3,
            self.button_width, self.button_height,
            "卡牌图鉴",
            color=(100, 200, 150), hover_color=(150, 255, 200),
            on_click=lambda: self.switch_to("collection")
        )
        self.buttons.append(collection_btn)
        
        # 设置按钮
        settings_btn = MenuButton(
            self.base_x - self.stagger_offset * 4,
            self.start_y + self.button_spacing * 4,
            self.button_width, self.button_height,
            "设置",
            color=(150, 100, 255), hover_color=(200, 150, 255),
            on_click=lambda: self.switch_to("settings")
        )
        self.buttons.append(settings_btn)
        
        # 退出按钮
        quit_btn = MenuButton(
            self.base_x - self.stagger_offset * 5,
            self.start_y + self.button_spacing * 5,
            self.button_width, self.button_height,
            "退出游戏",
            color=(200, 50, 50), hover_color=(255, 70, 70),
            on_click=self.quit_game
        )
        self.buttons.append(quit_btn)
        
    def _on_poster_click(self, idx):
        if idx is None or idx < 0:
            return
        scene_name = poster_to_scene.get(idx) # 获取对应场景名称
        self.switch_to(scene_name) # 切换场景
