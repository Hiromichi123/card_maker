"""战斗菜单场景"""
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
poster_topleft = (int(WINDOW_WIDTH * 0.58), int(WINDOW_HEIGHT * 0.6))

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

        # 活动海报轮播控件
        self.poster_ui = PosterUI()
        self.poster_ui.on_click = self._on_poster_click

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
        self.poster_ui.draw(self.screen, poster_topleft) #绘制活动海报
        
        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen)

    def create_buttons(self):
        button_specs = [
            {
                "label": "单人战役",
                "color": (200, 50, 50),
                "hover": (255, 80, 80),
                "action": lambda: self.switch_to("world_map")
            },
            {
                "label": "活动模式",
                "color": (255, 220, 120),
                "hover": (255, 255, 180),
                "action": lambda: self.switch_to("activity_scene"),
                "persistent_glow": True,
                "glow_alpha": 255
            },
            {
                "label": "局域网 卡组对战",
                "color": (200, 70, 50),
                "hover": (255, 100, 80),
                "action": lambda: self.switch_to("simple_battle")
            },
            {
                "label": "局域网 任选对战",
                "color": (200, 90, 50),
                "hover": (255, 120, 80),
                "action": lambda: self.switch_to("simple_battle")
            },
            {
                "label": "本地 任选对战（双人）",
                "color": (200, 110, 50),
                "hover": (255, 140, 80),
                "action": lambda: self.switch_to("draft_scene")
            },
            {
                "label": "返回主菜单",
                "color": (100, 150, 255),
                "hover": (150, 200, 255),
                "action": lambda: self.switch_to("main_menu")
            }
        ]

        for idx, spec in enumerate(button_specs):
            btn = MenuButton(
                self.base_x - self.stagger_offset * idx,
                self.start_y + self.button_spacing * idx,
                self.button_width,
                self.button_height,
                spec["label"],
                color=spec["color"],
                hover_color=spec["hover"],
                on_click=spec["action"],
                persistent_glow=spec.get("persistent_glow", False),
                persistent_glow_alpha=spec.get("glow_alpha", 120)
            )
            self.buttons.append(btn)
        
    def _on_poster_click(self, idx):
        if idx is None or idx < 0:
            return
        scene_name = poster_to_scene.get(idx) # 获取对应场景名称
        self.switch_to(scene_name) # 切换场景
