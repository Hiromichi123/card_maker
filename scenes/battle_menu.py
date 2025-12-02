"""战斗菜单场景"""
import pygame
import config
from scenes.base.base_scene import BaseScene
from ui.menu_button import MenuButton
from ui.background import ParallaxBackground
from ui.system_ui import CurrencyLevelUI
from ui.activity_poster import PosterUI
from utils.scene_payload import set_payload

# 海报跳转映射表：index -> scene_name
poster_to_scene = {
    0: "gacha",
    1: "battle_menu"
}

class BattleMenuScene(BaseScene):
    force_native_resolution = True

    def __init__(self, screen):
        super().__init__(screen)
        self.background = None
        self.title_font = None
        self.button_width = 0
        self.button_height = 0
        self.base_x = 0
        self.start_y = 0
        self.button_spacing = 0
        self.stagger_offset = 0
        self._poster_topleft = (0, 0)

        # 货币和等级 UI
        self.currency_ui = CurrencyLevelUI()
        self.currency_ui.load_state()

        self.poster_ui = None
        self.buttons = []
        self._title_cache = None
        self._shadow_cache = None
        self._refresh_layout_metrics()
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
    
    def _refresh_layout_metrics(self):
        width = config.WINDOW_WIDTH
        height = config.WINDOW_HEIGHT
        ui_scale = config.UI_SCALE

        self.background = ParallaxBackground(width, height, "battle_menu")
        title_font_size = max(48, int(96 * ui_scale))
        self.title_font = config.get_font(title_font_size)
        self.button_width = int(300 * ui_scale)
        self.button_height = int(50 * ui_scale)
        self.base_x = int(width * 0.75)
        self.start_y = int(height * 0.25)
        self.button_spacing = int(90 * ui_scale)
        self.stagger_offset = int(30 * ui_scale)
        self._poster_topleft = (int(width * 0.58), int(height * 0.6))

        self.poster_ui = PosterUI()
        self.poster_ui.on_click = self._on_poster_click

        self.buttons.clear()
        self.create_buttons()
        self._rebuild_title_cache()

    def on_design_resolution_changed(self):
        self._refresh_layout_metrics()

    def _rebuild_title_cache(self):
        title_text = self.title_font.render("选择对战模式", True, (255, 215, 0))
        shadow_offset = max(3, int(3 * config.UI_SCALE))
        shadow_text = self.title_font.render("选择对战模式", True, (0, 0, 0))
        self._title_cache = title_text
        self._shadow_cache = (shadow_text, shadow_offset)

    def draw(self):
        self.background.draw(self.screen) # 背景
        
        # 绘制标题（使用缓存）
        if self._title_cache and self._shadow_cache:
            shadow_text, shadow_offset = self._shadow_cache
            center_x = config.WINDOW_WIDTH // 2
            center_y = int(config.WINDOW_HEIGHT * 0.12)
            shadow_rect = shadow_text.get_rect(center=(center_x + shadow_offset, center_y + shadow_offset))
            title_rect = self._title_cache.get_rect(center=(center_x, center_y))
            self.screen.blit(shadow_text, shadow_rect)
            self.screen.blit(self._title_cache, title_rect)

        self.currency_ui.draw(self.screen) # 货币和等级 UI
        self.poster_ui.draw(self.screen, self._poster_topleft) #绘制活动海报
        
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
                "action": lambda: self._start_simple_battle("lan_deck")
            },
            {
                "label": "局域网 任选对战",
                "color": (200, 90, 50),
                "hover": (255, 120, 80),
                "action": lambda: self._start_simple_battle("lan_free")
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

    def _start_simple_battle(self, mode_tag=None):
        payload = {
            "return_scene": "battle_menu",
            "return_payload": {"focus_mode": mode_tag} if mode_tag else None,
        }
        if payload["return_payload"] is None:
            payload.pop("return_payload")
        set_payload("simple_battle", payload)
        self.switch_to("simple_battle")
