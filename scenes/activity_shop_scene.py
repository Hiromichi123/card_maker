"""活动商店"""
import random
import textwrap
import pygame
from config import *
from scenes.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.menu_button import MenuButton
from ui.system_ui import CurrencyLevelUI


class ActivityShopScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "bg/activity")
        self.title_font = get_font(int(82 * UI_SCALE))
        self.subtitle_font = get_font(int(32 * UI_SCALE))
        self.item_font = get_font(int(30 * UI_SCALE))
        self.desc_font = get_font(int(24 * UI_SCALE))
        self.notice_font = get_font(int(30 * UI_SCALE))
        self.price_font = get_font(int(28 * UI_SCALE))
        self.currency_ui = CurrencyLevelUI()
        self.currency_ui.load_state()

        self.shop_items = [
            {"name": "限定卡包·辰星", "desc": "保底获得 S 级以上卡牌，附赠限定立绘碎片。", "cost": "活动徽章 x120", "limit": "每周限购 2 次"},
            {"name": "觉醒素材箱", "desc": "包含 3 种稀有素材与 15 枚记忆芯片。", "cost": "活动徽章 x80", "limit": "每日限购 1 次"},
            {"name": "战术指令卡", "desc": "解锁活动限定被动技能栏位。", "cost": "活动徽章 x60", "limit": "库存 5"},
            {"name": "活动特典头像框", "desc": "赛季限定外观，参与突袭即可兑换。", "cost": "活动徽章 x40", "limit": "永久限购"},
            {"name": "协力支援补给", "desc": "立即恢复 3 次协力突袭次数，并获得奖励加成。", "cost": "活动徽章 x50", "limit": "每周限购 3 次"},
            {"name": "记忆火花", "desc": "用于在活动战役中随机强化卡组。", "cost": "活动徽章 x30", "limit": "库存 10"}
        ]
        self.item_rects = []
        self.highlight_index = 0
        self.highlight_timer = 0.0

        self.buttons = self._create_buttons()
        self.notice_message = ""
        self.notice_timer = 0.0

    def _create_buttons(self):
        base_x = int(WINDOW_WIDTH * 0.76)
        base_y = int(WINDOW_HEIGHT * 0.26)
        width = int(300 * UI_SCALE)
        height = int(56 * UI_SCALE)
        spacing = int(78 * UI_SCALE)
        specs = [
            ("常规商店", (180, 220, 255), (210, 240, 255), lambda: self.switch_to("shop_scene")),
            ("刷新库存", (255, 210, 140), (255, 235, 190), self._refresh_inventory),
            ("返回活动大厅", (120, 245, 210), (170, 255, 230), lambda: self.switch_to("activity_scene")),
            ("返回主菜单", (140, 200, 255), (180, 230, 255), lambda: self.switch_to("main_menu"))
        ]

        buttons = []
        for idx, (label, color, hover, action) in enumerate(specs):
            btn = MenuButton(
                base_x - int(12 * UI_SCALE) * idx,
                base_y + spacing * idx,
                width,
                height,
                label,
                color=color,
                hover_color=hover,
                text_color=(25, 25, 25),
                on_click=action
            )
            buttons.append(btn)
        return buttons

    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.switch_to("activity_scene")
        elif event.type == pygame.MOUSEMOTION:
            self.background.update_mouse_position(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_item_click(event.pos):
                return

        for button in self.buttons:
            button.handle_event(event)

    def update(self, dt):
        self.background.update(dt)
        for button in self.buttons:
            button.update(dt)

        self.highlight_timer += dt
        if self.highlight_timer >= 3.0:
            self.highlight_timer = 0.0
            self.highlight_index = (self.highlight_index + 1) % len(self.shop_items)

        if self.notice_timer > 0:
            self.notice_timer -= dt
            if self.notice_timer <= 0:
                self.notice_timer = 0.0
                self.notice_message = ""

    def draw(self):
        self.background.draw(self.screen)
        self.currency_ui.draw(self.screen)
        self._draw_header()
        self._draw_shop_items()

        for button in self.buttons:
            button.draw(self.screen)

        if self.notice_message:
            self._draw_notice()

    def _draw_header(self):
        title_text = self.title_font.render("活动商店", True, (255, 250, 235))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.12)))
        self.screen.blit(title_text, title_rect)

        subtitle = self.subtitle_font.render("使用活动徽章兑换限定奖励，库存每日刷新。", True, (240, 240, 240))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.18)))
        self.screen.blit(subtitle, subtitle_rect)

    def _draw_shop_items(self):
        columns = 2
        card_width = int(WINDOW_WIDTH * 0.34)
        card_height = int(150 * UI_SCALE)
        start_x = int(WINDOW_WIDTH * 0.08)
        start_y = int(WINDOW_HEIGHT * 0.26)
        gap_x = int(36 * UI_SCALE)
        gap_y = int(26 * UI_SCALE)

        self.item_rects = []
        for idx, item in enumerate(self.shop_items):
            row = idx // columns
            col = idx % columns
            rect = pygame.Rect(
                start_x + col * (card_width + gap_x),
                start_y + row * (card_height + gap_y),
                card_width,
                card_height
            )
            self.item_rects.append(rect)

            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            highlight = idx == self.highlight_index
            base_alpha = 230 if highlight else 160
            panel.fill((35, 45, 90, base_alpha))
            if highlight:
                glow = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(glow, (255, 225, 155, 120), glow.get_rect(), border_radius=18)
                self.screen.blit(glow, rect.topleft)
            border_width = 4 if highlight else 2
            border_color = (255, 220, 150, 220) if highlight else (120, 160, 230, 180)
            pygame.draw.rect(panel, border_color, panel.get_rect(), width=border_width, border_radius=18)
            self.screen.blit(panel, rect.topleft)

            name_text = self.item_font.render(item["name"], True, (255, 245, 220))
            self.screen.blit(name_text, (rect.x + int(18 * UI_SCALE), rect.y + int(14 * UI_SCALE)))

            wrapped = textwrap.wrap(item["desc"], width=16)
            for line_idx, line in enumerate(wrapped[:2]):
                desc_text = self.desc_font.render(line, True, (210, 225, 255))
                self.screen.blit(desc_text, (rect.x + int(18 * UI_SCALE), rect.y + int(48 * UI_SCALE) + line_idx * int(26 * UI_SCALE)))

            price_text = self.price_font.render(item["cost"], True, (255, 220, 140))
            self.screen.blit(price_text, (rect.x + int(18 * UI_SCALE), rect.y + int(110 * UI_SCALE)))

            limit_text = self.desc_font.render(item["limit"], True, (180, 220, 255))
            limit_rect = limit_text.get_rect(right=rect.right - int(18 * UI_SCALE), bottom=rect.bottom - int(12 * UI_SCALE))
            self.screen.blit(limit_text, limit_rect)

    def _draw_notice(self):
        notice_surface = self.notice_font.render(self.notice_message, True, (255, 245, 230))
        notice_rect = notice_surface.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.92)))
        bg = pygame.Surface((notice_rect.width + int(40 * UI_SCALE), notice_rect.height + int(20 * UI_SCALE)), pygame.SRCALPHA)
        bg.fill((15, 15, 30, 190))
        self.screen.blit(bg, (notice_rect.x - int(20 * UI_SCALE), notice_rect.y - int(10 * UI_SCALE)))
        self.screen.blit(notice_surface, notice_rect)

    def _handle_item_click(self, mouse_pos):
        for idx, rect in enumerate(self.item_rects):
            if rect.collidepoint(mouse_pos):
                self.highlight_index = idx
                item = self.shop_items[idx]
                self._show_notice(f"{item['name']} 兑换功能将在活动开启时解锁")
                return True
        return False

    def _refresh_inventory(self):
        random.shuffle(self.shop_items)
        self.highlight_index = 0
        self.highlight_timer = 0.0
        self._show_notice("活动商店库存已刷新")

    def _show_notice(self, text):
        self.notice_message = text
        self.notice_timer = 2.2
