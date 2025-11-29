"""活动大厅场景"""
import pygame
from config import *
from scenes.base.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.menu_button import MenuButton
from ui.system_ui import CurrencyLevelUI

class ActivityScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "bg/activity")
        self.title_font = get_font(int(86 * UI_SCALE))
        self.section_font = get_font(int(42 * UI_SCALE))
        self.desc_font = get_font(int(28 * UI_SCALE))
        self.notice_font = get_font(int(30 * UI_SCALE))
        self.currency_ui = CurrencyLevelUI()
        self.currency_ui.load_state()

        self.feature_cards = [
            {
                "title": "迷宫挑战",
                "desc": "进入限时迷宫，连续挑战三个阶段首领，获得最终奖励。",
                "schedule": "活动期间常驻开放"
            },
            {
                "title": "深渊挑战（未开放）",
                "desc": "携带自定义卡组车轮战挑战多层深渊，获取稀有奖励。",
                "schedule": "每周开放 3 个全新层级"
            },
            {
                "title": "协力突袭（未开放）",
                "desc": "匹配其他玩家共同击破巨型敌人，分享掉落。",
                "schedule": "周末限时开放"
            }
        ]
        self.feature_rects = []
        self.hovered_feature_index = -1

        self.notice_message = ""
        self.notice_timer = 0.0
        self.buttons = self._create_buttons()

    def _create_buttons(self):
        base_x = int(WINDOW_WIDTH * 0.8)
        base_y = int(WINDOW_HEIGHT * 0.3)
        width = int(320 * UI_SCALE)
        height = int(58 * UI_SCALE)
        spacing = int(90 * UI_SCALE)

        button_specs = [
            ("前往单人战役", (255, 180, 120), (255, 210, 150), lambda: self.switch_to("world_map")),
            ("活动商店", (180, 140, 255), (210, 180, 255), lambda: self.switch_to("activity_shop_scene")),
            ("返回主菜单", (120, 200, 255), (170, 230, 255), lambda: self.switch_to("main_menu"))
        ]

        buttons = []
        for idx, (label, color, hover, action) in enumerate(button_specs):
            btn = MenuButton(
                base_x - int(20 * UI_SCALE) * idx,
                base_y + spacing * idx,
                width, height,
                label, color=color,
                hover_color=hover, text_color=(25, 25, 25),
                on_click=action
            )
            buttons.append(btn)
        return buttons

    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.switch_to("main_menu")
        elif event.type == pygame.MOUSEMOTION:
            self.background.update_mouse_position(event.pos)
            self._update_feature_hover(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_feature_click(event.pos):
                return

        for button in self.buttons:
            button.handle_event(event)

    def update(self, dt):
        self.background.update(dt)
        for button in self.buttons:
            button.update(dt)

        if self.notice_timer > 0:
            self.notice_timer -= dt
            if self.notice_timer <= 0:
                self.notice_timer = 0.0
                self.notice_message = ""

    def draw(self):
        self.background.draw(self.screen)
        self.currency_ui.draw(self.screen)
        self._draw_title()
        self._draw_feature_cards()

        for button in self.buttons:
            button.draw(self.screen)

        if self.notice_message:
            self._draw_notice()

    def _draw_title(self):
        title_text = self.title_font.render("限时活动模式", True, (255, 245, 225))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.12)))
        shadow = self.title_font.render("限时活动模式", True, (0, 0, 0))
        shadow_rect = shadow.get_rect(center=(title_rect.centerx + int(3 * UI_SCALE), title_rect.centery + int(3 * UI_SCALE)))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title_text, title_rect)

        subtitle = self.desc_font.render("限时玩法与合作挑战在此汇集，完成目标可兑换限定卡牌奖励。", True, (240, 240, 240))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.18)))
        self.screen.blit(subtitle, subtitle_rect)

    def _draw_feature_cards(self):
        card_width = int(WINDOW_WIDTH * 0.45)
        card_height = int(WINDOW_HEIGHT * 0.10)
        start_x = int(WINDOW_WIDTH * 0.15)
        start_y = int(WINDOW_HEIGHT * 0.28)
        gap = int(WINDOW_HEIGHT * 0.04)

        self.feature_rects = []
        for idx, card in enumerate(self.feature_cards):
            rect = pygame.Rect(
                start_x,
                start_y + idx * (card_height + gap),
                card_width,
                card_height
            )
            self.feature_rects.append(rect)

            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            base_alpha = 210 if idx == self.hovered_feature_index else 150
            panel.fill((20, 35, 70, base_alpha))
            border_color = (255, 220, 120, 220) if idx == self.hovered_feature_index else (120, 160, 230, 160)
            pygame.draw.rect(panel, border_color, panel.get_rect(), width=3, border_radius=16)
            self.screen.blit(panel, rect.topleft)

            title_text = self.section_font.render(card["title"], True, (255, 230, 180))
            self.screen.blit(title_text, (rect.x + int(24 * UI_SCALE), rect.y + int(18 * UI_SCALE)))

            desc_text = self.desc_font.render(card["desc"], True, (215, 230, 255))
            self.screen.blit(desc_text, (rect.x + int(24 * UI_SCALE), rect.y + int(60 * UI_SCALE)))

            schedule_text = self.desc_font.render(card["schedule"], True, (150, 220, 255))
            self.screen.blit(schedule_text, (rect.x + int(24 * UI_SCALE), rect.y + int(92 * UI_SCALE)))

    def _draw_notice(self):
        notice_surface = self.notice_font.render(self.notice_message, True, (255, 245, 230))
        notice_rect = notice_surface.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.92)))
        bg = pygame.Surface((notice_rect.width + int(40 * UI_SCALE), notice_rect.height + int(20 * UI_SCALE)), pygame.SRCALPHA)
        bg.fill((10, 10, 20, 190))
        self.screen.blit(bg, (notice_rect.x - int(20 * UI_SCALE), notice_rect.y - int(10 * UI_SCALE)))
        self.screen.blit(notice_surface, notice_rect)

    def _handle_feature_click(self, mouse_pos):
        for idx, rect in enumerate(self.feature_rects):
            if rect.collidepoint(mouse_pos):
                if idx == 0:
                    self.switch_to("activity_maze_scene")
                else:
                    self._show_notice(f"{self.feature_cards[idx]['title']} 将随版本更新开放")
                return True
        return False

    def _update_feature_hover(self, mouse_pos):
        self.hovered_feature_index = -1
        for idx, rect in enumerate(self.feature_rects):
            if rect.collidepoint(mouse_pos):
                self.hovered_feature_index = idx
                break

    def _show_notice(self, text):
        self.notice_message = text
        self.notice_timer = 2.2
