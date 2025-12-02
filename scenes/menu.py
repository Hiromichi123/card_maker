"""主菜单场景"""
import pygame
import config
from config import *
from scenes.base.base_scene import BaseScene
from ui.menu_button import MenuButton
from ui.background import ParallaxBackground
from ui.system_ui import CurrencyLevelUI
from ui.activity_poster import PosterUI
from ui.settings_modal import SettingsModal

try:
    from version import __version__
except ImportError:
    __version__ = "1.0.0"

# 海报跳转映射表：index -> scene_name
poster_to_scene = {
    0: "gacha_menu",
    1: "battle_menu"
}

# 海报位置
poster_topleft = (int(WINDOW_WIDTH * 0.58), int(WINDOW_HEIGHT * 0.6))

class MainMenuScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.settings_modal = None
        self._build_static_ui()

    def _build_static_ui(self):
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
        self.base_x = int(WINDOW_WIDTH * 0.70)
        self.start_y = int(WINDOW_HEIGHT * 0.25)
        self.button_spacing = int(90 * UI_SCALE)
        self.stagger_offset = int(30 * UI_SCALE)  # 阶梯偏移
        self.secondary_base_x = self.base_x + int(self.button_width + self.stagger_offset * 2)
        
        self.buttons = []
        self.create_buttons() # 创建按钮列表
        self.quit_flag = False   # 退出标志
        self.notice_font = get_font(int(32 * UI_SCALE))
        self.notice_message = ""
        self.notice_timer = 0.0
        self._title_cache = None
        self._shadow_cache = None
        self._rebuild_title_cache()
        
        # Version display
        self.version_font = get_font(max(12, int(18 * UI_SCALE)))
        self._version_surface = self.version_font.render(f"v{__version__}", True, (150, 150, 150))
    
    def quit_game(self):
        """退出游戏"""
        self.quit_flag = True
    
    def _rebuild_title_cache(self):
        self._title_cache = self.title_font.render(config.GAME_TITLE, True, (255, 215, 0))
        shadow_offset = max(3, int(3 * UI_SCALE))
        self._shadow_cache = (self.title_font.render(config.GAME_TITLE, True, (0, 0, 0)), shadow_offset)
    
    def handle_event(self, event):
        if self.settings_modal:
            self.settings_modal.handle_event(event)
            return
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

        if self.notice_timer > 0:
            self.notice_timer -= dt
            if self.notice_timer <= 0:
                self.notice_timer = 0.0
                self.notice_message = ""
        if self.settings_modal:
            self.settings_modal.update(dt)
    
    def draw(self):
        self.background.draw(self.screen) # 背景
        
        # 绘制标题（使用缓存）
        if self._title_cache and self._shadow_cache:
            shadow_text, shadow_offset = self._shadow_cache
            center_x = WINDOW_WIDTH // 2
            center_y = int(WINDOW_HEIGHT * 0.12)
            shadow_rect = shadow_text.get_rect(center=(center_x + shadow_offset, center_y + shadow_offset))
            title_rect = self._title_cache.get_rect(center=(center_x, center_y))
            self.screen.blit(shadow_text, shadow_rect)
            self.screen.blit(self._title_cache, title_rect)

        self.currency_ui.draw(self.screen) # 货币和等级 UI
        self.poster_ui.draw(self.screen, poster_topleft) #绘制活动海报
        
        # 绘制按钮
        for button in self.buttons:
            button.draw(self.screen)

        if self.notice_message:
            notice_surface = self.notice_font.render(self.notice_message, True, (255, 240, 200))
            notice_rect = notice_surface.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.92)))
            bg_padding = int(16 * UI_SCALE)
            bg_rect = pygame.Rect(
                notice_rect.x - bg_padding,
                notice_rect.y - bg_padding // 2,
                notice_rect.width + bg_padding * 2,
                notice_rect.height + bg_padding
            )
            overlay = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            overlay.fill((20, 20, 20, 180))
            self.screen.blit(overlay, bg_rect.topleft)
            self.screen.blit(notice_surface, notice_rect)
        if self.settings_modal:
            self.settings_modal.draw(self.screen)
        
        # Draw version number in bottom right corner
        version_rect = self._version_surface.get_rect(
            bottomright=(WINDOW_WIDTH - int(10 * UI_SCALE), WINDOW_HEIGHT - int(10 * UI_SCALE))
        )
        self.screen.blit(self._version_surface, version_rect)

    def create_buttons(self):
        self.buttons.clear()
        self._create_primary_buttons()
        self._create_secondary_buttons()

    def open_settings_modal(self):
        if self.settings_modal:
            return
        self.settings_modal = SettingsModal(
            initial_scale=round(UI_SCALE, 2),
            on_apply=self._apply_ui_scale_change,
            on_cancel=self.close_settings_modal
        )

    def close_settings_modal(self):
        self.settings_modal = None

    def _apply_ui_scale_change(self, scale_value: float):
        config.set_ui_scale(scale_value)
        self.close_settings_modal()
        self._build_static_ui()
        self._rebuild_title_cache()

    def _create_primary_buttons(self):
        # 战斗按钮
        battle_btn = MenuButton(
            self.base_x, self.start_y,
            self.button_width, self.button_height,
            "进入战斗",
            color=(200, 50, 50), hover_color=(255, 80, 80), text_color=(25, 25, 25),
            on_click=lambda: self.switch_to("battle_menu")
        )
        self.buttons.append(battle_btn)

        # 抽卡按钮
        gacha_btn = MenuButton(
            self.base_x - self.stagger_offset, 
            self.start_y + self.button_spacing,
            self.button_width, self.button_height,
            "抽卡",
            color=(255, 140, 0), hover_color=(255, 180, 50), text_color=(25, 25, 25),
            on_click=lambda: self.switch_to("gacha_menu")
        )
        self.buttons.append(gacha_btn)

        # 卡组配置按钮
        deck_btn = MenuButton(
            self.base_x - self.stagger_offset * 2, 
            self.start_y + self.button_spacing * 2,
            self.button_width, self.button_height,
            "出战卡组配置",
            color=(100, 150, 255), hover_color=(150, 200, 255), text_color=(25, 25, 25),
            on_click=lambda: self.switch_to("deck_builder")
        )
        self.buttons.append(deck_btn)
        
        # 图鉴按钮
        collection_btn = MenuButton(
            self.base_x - self.stagger_offset * 3,
            self.start_y + self.button_spacing * 3,
            self.button_width, self.button_height,
            "卡牌图鉴",
            color=(100, 200, 150), hover_color=(150, 255, 200), text_color=(25, 25, 25),
            on_click=lambda: self.switch_to("collection")
        )
        self.buttons.append(collection_btn)
        
        # 设置按钮
        settings_btn = MenuButton(
            self.base_x - self.stagger_offset * 4,
            self.start_y + self.button_spacing * 4,
            self.button_width, self.button_height,
            "设置",
            color=(150, 100, 255), hover_color=(200, 150, 255), text_color=(25, 25, 25),
            on_click=self.open_settings_modal
        )
        self.buttons.append(settings_btn)
        
        # 退出按钮
        quit_btn = MenuButton(
            self.base_x - self.stagger_offset * 5,
            self.start_y + self.button_spacing * 5,
            self.button_width, self.button_height,
            "退出游戏",
            color=(200, 50, 50), hover_color=(255, 70, 70), text_color=(25, 25, 25),
            on_click=self.quit_game
        )
        self.buttons.append(quit_btn)

    def _create_secondary_buttons(self):
        secondary_specs = [
            {
                "label": "活动入口",
                "color": (255, 220, 120),
                "hover": (255, 245, 180),
                "action": lambda: self.switch_to("activity_scene")
            },
            {
                "label": "商店",
                "color": (180, 120, 255),
                "hover": (210, 160, 255),
                "action": lambda: self.switch_to("shop_scene")
            },
            {
                "label": "工坊",
                "color": (120, 210, 255),
                "hover": (170, 240, 255),
                "action": lambda: self.switch_to("workshop_scene")
            },
            {
                "label": "公告",
                "color": (255, 120, 160),
                "hover": (255, 170, 200)
            },
            {
                "label": "教学关卡",
                "color": (120, 255, 200),
                "hover": (170, 255, 230)
            },
        ]

        for idx, spec in enumerate(secondary_specs):
            action = spec.get("action")
            if action is None:
                on_click = lambda text=spec["label"]: self._show_feature_notice(text)
            else:
                on_click = action

            btn = MenuButton(
                self.secondary_base_x - self.stagger_offset * idx,
                self.start_y + self.button_spacing * idx,
                self.button_width, self.button_height,
                spec["label"], color=spec["color"],
                hover_color=spec["hover"], text_color=(30, 30, 30),
                on_click=on_click
            )
            self.buttons.append(btn)

    def _show_feature_notice(self, feature_name: str):
        self.notice_message = f"{feature_name} 功能即将开放"
        self.notice_timer = 2.0

    def _on_poster_click(self, idx):
        if idx is None or idx < 0:
            return
        scene_name = poster_to_scene.get(idx) # 获取对应场景名称
        self.switch_to(scene_name) # 切换场景
