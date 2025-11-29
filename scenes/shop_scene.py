"""常规商店场景"""
import math
import os
import random
import pygame
from config import *
from scenes.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.menu_button import MenuButton
from ui.system_ui import CurrencyLevelUI, DEFAULT_GOLD_ICON, DEFAULT_CRYSTAL_ICON
from utils.card_database import CardDatabase

CARD_PRICE_RULES = {
    "SSS": {"currency": "crystal", "amount": 551},
    "SS": {"currency": "crystal", "amount": 324},
    "S": {"currency": "crystal", "amount": 120},
    "A": {"currency": "gold", "amount": 4153},
    "B": {"currency": "gold", "amount": 2589},
    "C": {"currency": "gold", "amount": 1354},
    "D": {"currency": "gold", "amount": 690}
}

PACK_DEFINITIONS = [
    {"name": "天空典藏包", "rarity": "SSS", "currency": "crystal", "amount": 1880, "note": "必出SSS"},
    {"name": "星辉补给包", "rarity": "SS", "currency": "crystal", "amount": 520, "note": "至少一张SS"},
    {"name": "战术构筑包", "rarity": "S", "currency": "gold", "amount": 15000, "note": "高阶构筑素材"}
]

CURRENCY_COLORS = {
    "gold": (255, 210, 120),
    "crystal": (170, 210, 255)
}


class ShopScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "bg/shop")
        self.title_font = get_font(int(100 * UI_SCALE)) # 标题
        self.subtitle_font = get_font(int(40 * UI_SCALE)) # 副标题
        self.card_title_font = get_font(int(26 * UI_SCALE)) # 卡牌名称
        self.card_stats_font = get_font(int(20 * UI_SCALE)) # 卡牌属性
        self.notice_font = get_font(int(50 * UI_SCALE)) # 提示信息
        self.chart_title_font = get_font(int(28 * UI_SCALE)) # 图表标题
        self.chart_axis_font = get_font(int(20 * UI_SCALE)) # 图表坐标轴
        
        # 系统货币与等级UI
        self.currency_ui = CurrencyLevelUI()
        self.currency_ui.load_state()

        self.card_db = CardDatabase()
        self.card_image_cache = {}
        self.cost_icons = self._load_cost_icons()
        self.pack_image = self._load_pack_image()
        self.pack_glow_time = 0.0

        left_width = int(WINDOW_WIDTH * 0.62)
        left_x = int(WINDOW_WIDTH * 0.04)
        panel_y = int(WINDOW_HEIGHT * 0.18)
        panel_height = int(WINDOW_HEIGHT * 0.78)
        self.left_panel_rect = pygame.Rect(left_x, panel_y, left_width, panel_height)
        self.right_panel_rect = pygame.Rect(self.left_panel_rect.right + int(26 * UI_SCALE), self.left_panel_rect.y,
                                            WINDOW_WIDTH - (self.left_panel_rect.right + int(40 * UI_SCALE)),
                                            self.left_panel_rect.height)

        self.buttons = self._create_buttons()
        self.top_return_button = MenuButton(
            int(WINDOW_WIDTH * 0.84),
            int(WINDOW_HEIGHT * 0.05),
            int(240 * UI_SCALE),
            int(60 * UI_SCALE),
            "返回主菜单",
            color=(120, 180, 255),
            hover_color=(170, 210, 255),
            text_color=(25, 25, 25),
            on_click=lambda: self.switch_to("main_menu"),
            persistent_glow=True,
            persistent_glow_alpha=90
        )
        self.notice_message = ""
        self.notice_timer = 0.0

        self.shelf_specs = self._build_shelf_specs()
        self.card_offers = {}
        self._populate_card_offers()

        self.pack_offers = [definition.copy() for definition in PACK_DEFINITIONS]
        self.price_hitboxes = []
        self.hoverable_cards = []

        self.price_history = self._generate_price_history()
        self.exchange_history = self._generate_exchange_history()
        self.chart_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        self.extra_series_colors = {
            "金币/水晶": (255, 215, 120),
            "金币/徽章": (180, 240, 200),
            "水晶/徽章": (170, 210, 255)
        }

    def _build_shelf_specs(self):
        return {
            "top": {
                "label": "神话",
                "rarities": ("SSS", "SS"),
                "count_range": (1, 2),
                "card_size": (int(200 * UI_SCALE), int(300 * UI_SCALE)),
                "height": int(400 * UI_SCALE),
                "allow_repeat": False
            },
            "middle": {
                "label": "传承",
                "rarities": ("S", "A"),
                "count_range": (3, 4),
                "card_size": (int(200 * UI_SCALE), int(300 * UI_SCALE)),
                "height": int(400 * UI_SCALE),
                "allow_repeat": False
            },
            "bottom": {
                "label": "探索",
                "rarities": ("B", "C", "D"),
                "count_range": (5, 5),
                "card_size": (int(160 * UI_SCALE), int(240 * UI_SCALE)),
                "height": int(380 * UI_SCALE),
                "allow_repeat": True
            }
        }

    def _load_cost_icons(self):
        size = int(30 * UI_SCALE)
        return {
            "gold": self._load_icon(DEFAULT_GOLD_ICON, size),
            "crystal": self._load_icon(DEFAULT_CRYSTAL_ICON, size)
        }

    def _load_icon(self, path, size):
        try:
            if path and os.path.exists(path):
                surf = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(surf, (size, size))
        except Exception:
            pass
        fallback = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(fallback, (255, 255, 255, 180), (size // 2, size // 2), size // 2)
        return fallback

    def _load_pack_image(self):
        path = "assets/ui/card_back.png"
        try:
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                return img
        except Exception:
            pass
        surf = pygame.Surface((200, 280), pygame.SRCALPHA)
        pygame.draw.rect(surf, (80, 80, 120), surf.get_rect(), border_radius=20)
        return surf

    def _populate_card_offers(self):
        for key, spec in self.shelf_specs.items():
            min_c, max_c = spec["count_range"]
            target_count = random.randint(min_c, max_c)
            offers = self._sample_cards(spec["rarities"], target_count, spec.get("allow_repeat", False))
            self.card_offers[key] = offers

    def _sample_cards(self, rarities, count, allow_repeat):
        pool = []
        for rarity in rarities:
            pool.extend(self.card_db.get_cards_by_rarity(rarity))
        if not pool:
            return []

        if allow_repeat or len(pool) < count:
            selected = [random.choice(pool) for _ in range(count)]
        else:
            selected = random.sample(pool, count)

        offers = []
        for card in selected:
            rule = CARD_PRICE_RULES.get(card.rarity, {"currency": "gold", "amount": 1000})
            offers.append({
                "card": card,
                "rarity": card.rarity,
                "price": {"currency": rule["currency"], "amount": rule["amount"]}
            })
        return offers

    def _create_buttons(self):
        base_x = self.right_panel_rect.x + self.right_panel_rect.width - int(20 * UI_SCALE)
        base_y = self.right_panel_rect.bottom + int(12 * UI_SCALE)
        width = int(260 * UI_SCALE)
        height = int(52 * UI_SCALE)
        spacing = int(70 * UI_SCALE)
        specs = [
            ("活动商店", (120, 245, 210), (170, 255, 230), lambda: self.switch_to("activity_shop_scene")),
            ("刷新货架", (255, 210, 140), (255, 235, 190), self._refresh_wares),
            ("返回主菜单", (140, 200, 255), (180, 230, 255), lambda: self.switch_to("main_menu"))
        ]

        buttons = []
        for idx, (label, color, hover, action) in enumerate(specs):
            btn = MenuButton(
                base_x, base_y + spacing * idx,
                width, height,
                label,
                color=color, hover_color=hover, text_color=(25, 25, 25),
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
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_price_click(event.pos):
                return

        for button in self.buttons:
            button.handle_event(event)
        self.top_return_button.handle_event(event)

    def update(self, dt):
        self.background.update(dt)
        for button in self.buttons:
            button.update(dt)
        self.top_return_button.update(dt)

        self.pack_glow_time = (self.pack_glow_time + dt) % 1000

        if self.notice_timer > 0:
            self.notice_timer -= dt
            if self.notice_timer <= 0:
                self.notice_timer = 0.0
                self.notice_message = ""

    def draw(self):
        self.background.draw(self.screen)
        self.currency_ui.draw(self.screen, (int(WINDOW_WIDTH * 0.04), int(WINDOW_HEIGHT * 0.03)))
        self._draw_header()
        self._draw_left_panel()
        self._draw_right_panel()

        for button in self.buttons:
            button.draw(self.screen)
        self.top_return_button.draw(self.screen)

        if self.notice_message:
            self._draw_notice()

    def _draw_header(self):
        title_text = self.title_font.render("星辰商店", True, (255, 245, 225))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.11)))
        shadow = self.title_font.render("星辰商店", True, (0, 0, 0))
        shadow_rect = shadow.get_rect(center=(title_rect.centerx + int(3 * UI_SCALE), title_rect.centery + int(3 * UI_SCALE)))
        self.screen.blit(shadow, shadow_rect)
        self.screen.blit(title_text, title_rect)

        subtitle = self.subtitle_font.render("精选卡牌供货 / 卡包特典 / 市场行情一览", True, (235, 235, 235))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.16)))
        self.screen.blit(subtitle, subtitle_rect)

    def _draw_left_panel(self):
        panel = pygame.Surface(self.left_panel_rect.size, pygame.SRCALPHA)
        panel.fill((15, 25, 50, 130))
        pygame.draw.rect(panel, (80, 120, 180, 60), panel.get_rect(), width=2, border_radius=24)
        self.screen.blit(panel, self.left_panel_rect.topleft)

        self.price_hitboxes = []
        self.hoverable_cards = []

        current_y = self.left_panel_rect.y + int(30 * UI_SCALE)
        inner_x = self.left_panel_rect.x + int(30 * UI_SCALE)
        inner_width = self.left_panel_rect.width - int(60 * UI_SCALE)

        for key in ("top", "middle", "bottom"):
            spec = self.shelf_specs[key]
            rect = pygame.Rect(inner_x, current_y, inner_width, spec["height"])
            self._draw_shelf(spec, rect, self.card_offers.get(key, []))
            current_y += spec["height"] + int(28 * UI_SCALE)

    def _draw_shelf(self, spec, rect, offers):
        label_text = self.card_title_font.render(spec["label"], True, (255, 255, 255))
        self.screen.blit(label_text, (rect.x, rect.y - int(8 * UI_SCALE)))

        shelf_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        shelf_surface.fill((25, 35, 70, 110))
        pygame.draw.rect(shelf_surface, (90, 140, 200, 80), shelf_surface.get_rect(), width=2, border_radius=18)
        self.screen.blit(shelf_surface, rect.topleft)

        if not offers:
            placeholder = self.card_stats_font.render("库存补货中...", True, (200, 200, 200))
            ph_rect = placeholder.get_rect(center=rect.center)
            self.screen.blit(placeholder, ph_rect)
            return

        card_w, card_h = spec["card_size"]
        count = len(offers)
        total_card_width = card_w * count
        space = max(int(16 * UI_SCALE), (rect.width - total_card_width) // (count + 1))
        current_x = rect.x + space
        card_y = rect.y + int(50 * UI_SCALE)

        for offer in offers:
            card_rect = pygame.Rect(current_x, card_y, card_w, card_h)
            self._draw_card_offer(card_rect, offer)
            current_x += card_w + space

    def _draw_card_offer(self, card_rect, offer):
        card = offer.get("card")
        rarity = offer.get("rarity", "A")
        name = card.name if card else "待补货"

        name_surface = self.card_title_font.render(name, True, (255, 255, 255))
        name_rect = name_surface.get_rect(center=(card_rect.centerx, card_rect.y - int(26 * UI_SCALE)))
        self.screen.blit(name_surface, name_rect)

        frame_rect = card_rect.inflate(int(16 * UI_SCALE), int(16 * UI_SCALE))
        pygame.draw.rect(self.screen, (*COLORS.get(rarity, (200, 200, 200)), 80), frame_rect, border_radius=14)

        image_surface = self._get_card_image(card, card_rect.size)
        self.screen.blit(image_surface, card_rect)

        stats_text = f"ATK {getattr(card, 'atk', 0)} / HP {getattr(card, 'hp', 0)}"
        stats_surface = self.card_stats_font.render(stats_text, True, (220, 220, 230))
        stats_rect = stats_surface.get_rect(center=(card_rect.centerx, card_rect.bottom + int(18 * UI_SCALE)))
        self.screen.blit(stats_surface, stats_rect)

        price_rect = pygame.Rect(card_rect.x, stats_rect.bottom + int(6 * UI_SCALE), card_rect.width, int(44 * UI_SCALE))
        self._draw_price_button(price_rect, offer["price"], f"购买")
        self.price_hitboxes.append({"rect": price_rect, "offer": offer, "category": "card"})

        if card:
            self.hoverable_cards.append((card_rect, card))

    def _draw_price_button(self, rect, price, label):
        currency = price.get("currency", "gold")
        amount = price.get("amount", 0)
        base_color = CURRENCY_COLORS.get(currency, (255, 255, 255))
        button_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        button_surface.fill((*base_color, 30))
        pygame.draw.rect(button_surface, base_color, button_surface.get_rect(), border_radius=20)
        self.screen.blit(button_surface, rect.topleft)

        icon = self.cost_icons.get(currency)
        text_surface = self.card_stats_font.render(f"{label} {amount}", True, (25, 25, 25))
        total_width = text_surface.get_width()
        icon_width = icon.get_width() if icon else 0
        gap = int(8 * UI_SCALE) if icon else 0
        total_width += icon_width + gap
        start_x = rect.x + (rect.width - total_width) // 2
        if icon:
            self.screen.blit(icon, (start_x, rect.y + (rect.height - icon.get_height()) // 2))
            start_x += icon_width + gap
        self.screen.blit(text_surface, (start_x, rect.y + (rect.height - text_surface.get_height()) // 2))

    def _draw_right_panel(self):
        panel = pygame.Surface(self.right_panel_rect.size, pygame.SRCALPHA)
        panel.fill((25, 28, 50, 130))
        pygame.draw.rect(panel, (120, 150, 210, 50), panel.get_rect(), width=2, border_radius=20)
        self.screen.blit(panel, self.right_panel_rect.topleft)

        upper_height = int(self.right_panel_rect.height * 0.45)
        pack_rect = pygame.Rect(self.right_panel_rect.x + int(20 * UI_SCALE),
                                self.right_panel_rect.y + int(24 * UI_SCALE),
                                self.right_panel_rect.width - int(40 * UI_SCALE),
                                upper_height)
        chart_rect = pygame.Rect(self.right_panel_rect.x + int(20 * UI_SCALE),
                                 pack_rect.bottom + int(24 * UI_SCALE),
                                 self.right_panel_rect.width - int(40 * UI_SCALE),
                                 self.right_panel_rect.bottom - pack_rect.bottom - int(40 * UI_SCALE))

        self._draw_pack_panel(pack_rect)
        self._draw_charts(chart_rect)

    def _draw_pack_panel(self, rect):
        title = self.card_title_font.render("特典卡包", True, (255, 255, 255))
        self.screen.blit(title, (rect.x, rect.y - int(4 * UI_SCALE)))

        pack_width = int(150 * UI_SCALE)
        pack_height = int(210 * UI_SCALE)
        spacing = (rect.width - pack_width * len(self.pack_offers)) // (len(self.pack_offers) + 1)
        start_x = rect.x + spacing
        y = rect.y + int(30 * UI_SCALE)

        for offer in self.pack_offers:
            pack_rect = pygame.Rect(start_x, y, pack_width, pack_height)
            self._draw_pack_offer(pack_rect, offer)
            price_rect = pygame.Rect(pack_rect.x - int(10 * UI_SCALE), pack_rect.bottom + int(12 * UI_SCALE),
                                     pack_rect.width + int(20 * UI_SCALE), int(40 * UI_SCALE))
            self._draw_price_button(price_rect, offer, offer["note"])
            self.price_hitboxes.append({"rect": price_rect, "offer": offer, "category": "pack"})
            start_x += pack_width + spacing

    def _draw_pack_offer(self, rect, offer):
        rarity = offer.get("rarity", "S")
        glow_color = COLORS.get(rarity, (255, 255, 255))
        glow_surface = pygame.Surface(rect.inflate(int(50 * UI_SCALE), int(50 * UI_SCALE)).size, pygame.SRCALPHA)
        glow_alpha = int((math.sin(self.pack_glow_time * 2) + 1) * 40 + 50)
        pygame.draw.ellipse(glow_surface, (*glow_color, glow_alpha), glow_surface.get_rect())
        glow_pos = (rect.centerx - glow_surface.get_width() // 2, rect.centery - glow_surface.get_height() // 2)
        self.screen.blit(glow_surface, glow_pos)

        resized = pygame.transform.smoothscale(self.pack_image, rect.size)
        self.screen.blit(resized, rect)

        name_surface = self.card_stats_font.render(offer["name"], True, (255, 255, 255))
        name_rect = name_surface.get_rect(center=(rect.centerx, rect.top - int(18 * UI_SCALE)))
        self.screen.blit(name_surface, name_rect)

    def _draw_charts(self, rect):
        upper = pygame.Rect(rect.x, rect.y, rect.width, rect.height // 2 - int(10 * UI_SCALE))
        lower = pygame.Rect(rect.x, upper.bottom + int(16 * UI_SCALE), rect.width, rect.height // 2 - int(10 * UI_SCALE))

        self._draw_line_chart(
            upper,
            self.price_history,
            "成交价走势 (SSS-D)",
            unit="G"
        )
        self._draw_line_chart(
            lower,
            self.exchange_history,
            "汇率波动 (金币/水晶/徽章)",
            unit="%"
        )

    def _draw_line_chart(self, rect, series, title, unit=""):
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((15, 18, 35, 120))
        pygame.draw.rect(panel, (90, 110, 160, 70), panel.get_rect(), width=2, border_radius=14)
        self.screen.blit(panel, rect.topleft)

        title_surface = self.chart_title_font.render(title, True, (230, 230, 240))
        self.screen.blit(title_surface, (rect.x + int(12 * UI_SCALE), rect.y + int(6 * UI_SCALE)))

        plot_rect = pygame.Rect(rect.x + int(40 * UI_SCALE), rect.y + int(40 * UI_SCALE),
                                rect.width - int(60 * UI_SCALE), rect.height - int(70 * UI_SCALE))
        pygame.draw.line(self.screen, (120, 120, 140), (plot_rect.x, plot_rect.bottom), (plot_rect.right, plot_rect.bottom), 1)
        pygame.draw.line(self.screen, (120, 120, 140), (plot_rect.x, plot_rect.bottom), (plot_rect.x, plot_rect.top), 1)

        all_values = [value for values in series.values() for value in values]
        if not all_values:
            return
        min_val = min(all_values)
        max_val = max(all_values)
        if max_val == min_val:
            max_val += 1

        labels = self.chart_labels
        step_x = plot_rect.width / max(1, len(labels) - 1)

        for label_index, label in enumerate(labels):
            x = plot_rect.x + label_index * step_x
            pygame.draw.line(self.screen, (80, 80, 90), (x, plot_rect.bottom), (x, plot_rect.bottom + int(6 * UI_SCALE)), 1)
            lbl_surface = self.chart_axis_font.render(label, True, (200, 200, 200))
            lbl_rect = lbl_surface.get_rect(center=(x, plot_rect.bottom + int(16 * UI_SCALE)))
            self.screen.blit(lbl_surface, lbl_rect)

        for name, values in series.items():
            color = COLORS.get(name)
            if color is None:
                color = self.extra_series_colors.get(name, (200, 200, 200))
            points = []
            for idx, value in enumerate(values):
                norm = (value - min_val) / (max_val - min_val)
                y = plot_rect.bottom - norm * plot_rect.height
                x = plot_rect.x + idx * step_x
                points.append((x, y))
            if len(points) >= 2:
                pygame.draw.lines(self.screen, color, False, points, 2)
            for point in points:
                pygame.draw.circle(self.screen, color, (int(point[0]), int(point[1])), 3)

        legend_x = plot_rect.right - int(100 * UI_SCALE)
        legend_y = plot_rect.top - int(22 * UI_SCALE)
        for idx, name in enumerate(series.keys()):
            color = COLORS.get(name, self.extra_series_colors.get(name, (200, 200, 200)))
            pygame.draw.circle(self.screen, color, (legend_x, legend_y + idx * int(18 * UI_SCALE)), 5)
            lbl = self.chart_axis_font.render(name + unit, True, (220, 220, 220))
            self.screen.blit(lbl, (legend_x + int(12 * UI_SCALE), legend_y - int(6 * UI_SCALE) + idx * int(18 * UI_SCALE)))

    def _draw_notice(self):
        notice_surface = self.notice_font.render(self.notice_message, True, (255, 245, 230))
        notice_rect = notice_surface.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.94)))
        bg = pygame.Surface((notice_rect.width + int(40 * UI_SCALE), notice_rect.height + int(20 * UI_SCALE)), pygame.SRCALPHA)
        bg.fill((10, 10, 20, 190))
        self.screen.blit(bg, (notice_rect.x - int(20 * UI_SCALE), notice_rect.y - int(10 * UI_SCALE)))
        self.screen.blit(notice_surface, notice_rect)

    def _handle_price_click(self, pos):
        for entry in self.price_hitboxes:
            if entry["rect"].collidepoint(pos):
                offer = entry["offer"]
                if entry["category"] == "card":
                    self._attempt_purchase(offer)
                else:
                    self._attempt_purchase_pack(offer)
                return True
        return False

    def _attempt_purchase(self, offer):
        price = offer["price"]
        currency = price.get("currency", "gold")
        amount = price.get("amount", 0)
        card = offer.get("card")
        if currency == "gold":
            if not self.currency_ui.has_enough_golds(amount):
                self._show_notice("金币不足，无法购买")
                return
            if not self.currency_ui.spend_golds(amount):
                self._show_notice("交易失败，请重试")
                return
        else:
            if not self.currency_ui.has_enough_crystals(amount):
                self._show_notice("水晶不足，无法购买")
                return
            if not self.currency_ui.spend_crystals(amount):
                self._show_notice("交易失败，请重试")
                return
        self._show_notice(f"已购入 {card.name if card else '卡牌'}")

    def _attempt_purchase_pack(self, offer):
        currency = offer.get("currency", "crystal")
        amount = offer.get("amount", 0)
        if currency == "gold":
            if not self.currency_ui.has_enough_golds(amount):
                self._show_notice("金币不足，无法购买卡包")
                return
            if not self.currency_ui.spend_golds(amount):
                self._show_notice("交易失败，请稍后重试")
                return
        else:
            if not self.currency_ui.has_enough_crystals(amount):
                self._show_notice("水晶不足，无法购买卡包")
                return
            if not self.currency_ui.spend_crystals(amount):
                self._show_notice("交易失败，请稍后重试")
                return
        self._show_notice(f"已购买 {offer['name']}")

    def _refresh_wares(self):
        self._populate_card_offers()
        self._show_notice("货架已刷新")

    def _show_notice(self, text):
        self.notice_message = text
        self.notice_timer = 2.4

    def _get_card_image(self, card, size):
        key = (getattr(card, 'image_path', 'placeholder'), size)
        if key in self.card_image_cache:
            return self.card_image_cache[key]

        try:
            if card and card.image_path and os.path.exists(card.image_path):
                image = pygame.image.load(card.image_path).convert_alpha()
                scaled = pygame.transform.smoothscale(image, size)
            else:
                scaled = self._create_placeholder(size, COLORS.get(getattr(card, 'rarity', 'A'), (120, 120, 120)))
        except Exception:
            scaled = self._create_placeholder(size, (120, 120, 120))

        self.card_image_cache[key] = scaled
        return scaled

    def _create_placeholder(self, size, color):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (*color, 200), surf.get_rect(), border_radius=12)
        return surf

    def _generate_price_history(self):
        data = {}
        for rarity, rule in CARD_PRICE_RULES.items():
            baseline = rule["amount"]
            values = []
            current = baseline
            for _ in range(7):
                current += random.randint(-int(baseline * 0.08), int(baseline * 0.08))
                current = max(int(baseline * 0.6), current)
                values.append(current)
            data[rarity] = values
        return data

    def _generate_exchange_history(self):
        series = {
            "水晶/金币": 1034.0,
            "徽章/金币": 253,
            "水晶/徽章": 3.7
        }
        data = {}
        for name, base in series.items():
            values = []
            current = base
            for _ in range(7):
                current += random.uniform(-0.08, 0.08)
                current = max(0.2, current)
                values.append(round(current, 2))
            data[name] = values
        return data

    def get_hovered_card(self, mouse_pos):
        for rect, card in self.hoverable_cards:
            if rect.collidepoint(mouse_pos):
                return card
        return None
