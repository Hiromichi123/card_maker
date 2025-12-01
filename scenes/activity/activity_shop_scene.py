"""活动商店：使用活动徽章兑换限定卡牌"""
import json
import os
import random
from datetime import datetime

import pygame
from config import *
from scenes.base.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.menu_button import MenuButton
from ui.system_ui import CurrencyLevelUI, DEFAULT_BADGE_ICON
from utils.card_database import CardDatabase
from utils.inventory import get_inventory

BADGE_PRICE_RULES = {
    "#elna": 1080,
    "SSS": 1354,
    "SS+": 869,
    "SS": 621,
    "S+": 440,
    "S": 287,
    "A+": 198,
    "A": 156,
    "B+": 99,
    "B": 85,
    "C+": 51,
    "C": 44,
    "D": 30,
}
DEFAULT_BADGE_PRICE = 60
TOP_PANEL_COLOR = (214, 92, 138)
TOP_LABEL_COLOR = (255, 220, 235)
BADGE_TEXT_COLOR = (255, 205, 185)


class ActivityShopScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "bg/activity")
        self.title_font = get_font(int(90 * UI_SCALE))
        self.subtitle_font = get_font(int(34 * UI_SCALE))
        self.card_title_font = get_font(int(28 * UI_SCALE))
        self.card_stats_font = get_font(int(20 * UI_SCALE))
        self.notice_font = get_font(int(34 * UI_SCALE))
        self.chart_title_font = get_font(int(26 * UI_SCALE))
        self.chart_axis_font = get_font(int(18 * UI_SCALE))
        self.badge_counter_font = get_font(int(28 * UI_SCALE))

        self.currency_ui = CurrencyLevelUI()
        self.currency_ui.load_state()

        self.card_db = CardDatabase()
        self.card_image_cache = {}
        self.badge_icon = self._load_badge_icon(int(46 * UI_SCALE))
        self.badge_icon_small = self._load_badge_icon(int(28 * UI_SCALE))
        self.inventory = get_inventory()

        left_width = int(WINDOW_WIDTH * 0.62)
        left_x = int(WINDOW_WIDTH * 0.04)
        panel_y = int(WINDOW_HEIGHT * 0.18)
        panel_height = int(WINDOW_HEIGHT * 0.78)
        self.left_panel_rect = pygame.Rect(left_x, panel_y, left_width, panel_height)
        self.right_panel_rect = pygame.Rect(
            self.left_panel_rect.right + int(26 * UI_SCALE),
            self.left_panel_rect.y,
            WINDOW_WIDTH - (self.left_panel_rect.right + int(40 * UI_SCALE)),
            self.left_panel_rect.height,
        )

        self.buttons = self._create_buttons()
        self.notice_message = ""
        self.notice_timer = 0.0

        self.shelf_specs = self._build_shelf_specs()
        self.card_offers = {}
        self.price_hitboxes = []
        self.hoverable_cards = []
        self.sold_out_cards = set()

        self.shop_state_path = os.path.join("data", "activity_shop_state.json")
        self.daily_seed_key = None
        self.daily_seed_value = None
        self._load_shop_state()
        self._ensure_daily_rng()
        self._populate_card_offers()

        self.exchange_history = self._generate_exchange_history()
        self.chart_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        self.top_return_button = MenuButton(
            int(WINDOW_WIDTH * 0.82),
            int(WINDOW_HEIGHT * 0.05),
            int(240 * UI_SCALE),
            int(58 * UI_SCALE),
            "返回活动菜单",
            color=(150, 205, 255),
            hover_color=(190, 230, 255),
            text_color=(25, 25, 25),
            on_click=lambda: self.switch_to("activity_scene"),
            persistent_glow=True,
            persistent_glow_alpha=90,
        )

    def _build_shelf_specs(self):
        return {
            "top": {
                "label": "活动精选",
                "rarities": ("#elna",),
                "count_range": (2, 3),
                "card_size": (int(210 * UI_SCALE), int(310 * UI_SCALE)),
                "height": int(420 * UI_SCALE),
                "allow_repeat": False,
                "panel_color": TOP_PANEL_COLOR,
                "label_color": TOP_LABEL_COLOR,
            },
            "middle": {
                "label": "稀有兑换",
                "rarities": ("SS+", "SS", "S+", "S", "A+", "A"),
                "count_range": (3, 4),
                "card_size": (int(200 * UI_SCALE), int(300 * UI_SCALE)),
                "height": int(410 * UI_SCALE),
                "allow_repeat": False,
            },
            "bottom": {
                "label": "常规兑换",
                "rarities": ("A", "B+", "B", "C+", "C", "D"),
                "count_range": (4, 5),
                "card_size": (int(180 * UI_SCALE), int(270 * UI_SCALE)),
                "height": int(390 * UI_SCALE),
                "allow_repeat": True,
            },
        }

    def _load_badge_icon(self, size):
        try:
            if DEFAULT_BADGE_ICON and os.path.exists(DEFAULT_BADGE_ICON):
                surf = pygame.image.load(DEFAULT_BADGE_ICON).convert_alpha()
                return pygame.transform.smoothscale(surf, (size, size))
        except Exception:
            pass
        fallback = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(fallback, (255, 200, 200, 220), (size // 2, size // 2), size // 2)
        pygame.draw.circle(fallback, (220, 120, 150, 255), (size // 2, size // 2), size // 2 - 4)
        return fallback

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.switch_to("activity_scene")
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
        title = self.title_font.render("活动商店", True, (255, 248, 240))
        self.screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.11))))
        subtitle = self.subtitle_font.render("使用活动徽章兑换限定奖励，库存每日刷新。", True, (240, 238, 240))
        self.screen.blit(subtitle, subtitle.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.16))))
        self._draw_badge_counter()

    def _draw_badge_counter(self):
        amount = self.currency_ui.get_badges()
        text = self.badge_counter_font.render(f"徽章  x {amount}", True, BADGE_TEXT_COLOR)
        width = text.get_width() + self.badge_icon.get_width() + int(24 * UI_SCALE)
        height = max(text.get_height(), self.badge_icon.get_height()) + int(12 * UI_SCALE)
        panel = pygame.Surface((width + int(24 * UI_SCALE), height), pygame.SRCALPHA)
        panel.fill((30, 20, 40, 180))
        panel.blit(self.badge_icon, (int(12 * UI_SCALE), (height - self.badge_icon.get_height()) // 2))
        panel.blit(text, (self.badge_icon.get_width() + int(20 * UI_SCALE), (height - text.get_height()) // 2))
        pos = (int(WINDOW_WIDTH * 0.72), int(WINDOW_HEIGHT * 0.08))
        self.screen.blit(panel, pos)

    def _draw_left_panel(self):
        panel = pygame.Surface(self.left_panel_rect.size, pygame.SRCALPHA)
        panel.fill((15, 20, 46, 160))
        pygame.draw.rect(panel, (80, 120, 200, 60), panel.get_rect(), width=2, border_radius=24)
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
            current_y += spec["height"] + int(26 * UI_SCALE)

    def _draw_shelf(self, spec, rect, offers):
        label_color = spec.get("label_color", (255, 255, 255))
        label_text = self.card_title_font.render(spec["label"], True, label_color)
        self.screen.blit(label_text, (rect.x, rect.y - int(12 * UI_SCALE)))

        shelf_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        base_color = spec.get("panel_color", (30, 40, 80, 110))
        shelf_surface.fill((*base_color[:3], 140) if len(base_color) == 3 else base_color)
        pygame.draw.rect(shelf_surface, (120, 160, 210, 90), shelf_surface.get_rect(), width=2, border_radius=18)
        self.screen.blit(shelf_surface, rect.topleft)

        if not offers:
            placeholder = self.card_stats_font.render("库存补货中...", True, (220, 220, 220))
            self.screen.blit(placeholder, placeholder.get_rect(center=rect.center))
            return

        card_w, card_h = spec["card_size"]
        count = len(offers)
        total_card_width = card_w * count
        space = max(int(20 * UI_SCALE), (rect.width - total_card_width) // max(1, count + 1))
        current_x = rect.x + space
        card_y = rect.y + int(50 * UI_SCALE)

        for offer in offers:
            card_rect = pygame.Rect(current_x, card_y, card_w, card_h)
            self._draw_card_offer(card_rect, offer, spec)
            current_x += card_w + space

    def _draw_card_offer(self, card_rect, offer, spec):
        card = offer.get("card")
        rarity = offer.get("rarity", "A")
        name = card.name if card else "待补货"
        sold_out = offer.get("sold_out")

        name_surface = self.card_title_font.render(name, True, (255, 255, 255))
        name_rect = name_surface.get_rect(center=(card_rect.centerx, card_rect.y - int(26 * UI_SCALE)))
        self.screen.blit(name_surface, name_rect)

        frame_rect = card_rect.inflate(int(16 * UI_SCALE), int(16 * UI_SCALE))
        pygame.draw.rect(self.screen, (*COLORS.get(rarity, (200, 200, 200)), 90), frame_rect, border_radius=16)

        image_surface = self._get_card_image(card, card_rect.size)
        self.screen.blit(image_surface, card_rect)

        if sold_out:
            overlay = pygame.Surface(card_rect.size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, card_rect.topleft)
            sold_text = self.card_title_font.render("已售罄", True, (255, 190, 190))
            sold_rect = sold_text.get_rect(center=card_rect.center)
            self.screen.blit(sold_text, sold_rect)

        stats_text = f"ATK {getattr(card, 'atk', 0)} / HP {getattr(card, 'hp', 0)}"
        stats_surface = self.card_stats_font.render(stats_text, True, (220, 220, 235))
        stats_rect = stats_surface.get_rect(center=(card_rect.centerx, card_rect.bottom + int(18 * UI_SCALE)))
        self.screen.blit(stats_surface, stats_rect)

        price_rect = pygame.Rect(card_rect.x, stats_rect.bottom + int(6 * UI_SCALE), card_rect.width, int(44 * UI_SCALE))
        self._draw_price_button(price_rect, offer["price"], disabled=sold_out)
        if not sold_out:
            self.price_hitboxes.append({"rect": price_rect, "offer": offer})

        if card:
            self.hoverable_cards.append((card_rect, card))

    def _draw_price_button(self, rect, price, disabled=False):
        amount = price.get("amount", DEFAULT_BADGE_PRICE)
        button_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        base_color = (140, 140, 140) if disabled else (255, 210, 240)
        button_surface.fill((120, 50, 90, 30) if not disabled else (60, 60, 60, 40))
        pygame.draw.rect(button_surface, base_color, button_surface.get_rect(), border_radius=20)
        self.screen.blit(button_surface, rect.topleft)

        label = "售罄" if disabled else f"兑换 {amount}"
        text_color = (70, 70, 70) if disabled else (40, 20, 40)
        icon = None if disabled else self.badge_icon_small
        text_surface = self.card_stats_font.render(label, True, text_color)
        total_width = text_surface.get_width()
        if icon:
            total_width += icon.get_width() + int(10 * UI_SCALE)
        start_x = rect.x + (rect.width - total_width) // 2
        if icon:
            self.screen.blit(icon, (start_x, rect.y + (rect.height - icon.get_height()) // 2))
            start_x += icon.get_width() + int(10 * UI_SCALE)
        self.screen.blit(text_surface, (start_x, rect.y + (rect.height - text_surface.get_height()) // 2))

    def _draw_right_panel(self):
        panel = pygame.Surface(self.right_panel_rect.size, pygame.SRCALPHA)
        panel.fill((20, 24, 48, 150))
        pygame.draw.rect(panel, (120, 150, 210, 60), panel.get_rect(), width=2, border_radius=20)
        self.screen.blit(panel, self.right_panel_rect.topleft)

        chart_rect = pygame.Rect(
            self.right_panel_rect.x + int(24 * UI_SCALE),
            self.right_panel_rect.y + int(32 * UI_SCALE),
            self.right_panel_rect.width - int(48 * UI_SCALE),
            self.right_panel_rect.height - int(64 * UI_SCALE),
        )
        self._draw_line_chart(
            chart_rect,
            self.exchange_history,
            "徽章兑换汇率走势",
            unit="%",
        )

    def _draw_line_chart(self, rect, series, title, unit=""):
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((15, 18, 35, 120))
        pygame.draw.rect(panel, (90, 110, 160, 70), panel.get_rect(), width=2, border_radius=14)
        self.screen.blit(panel, rect.topleft)

        title_surface = self.chart_title_font.render(title, True, (230, 230, 240))
        self.screen.blit(title_surface, (rect.x + int(12 * UI_SCALE), rect.y + int(6 * UI_SCALE)))

        plot_rect = pygame.Rect(rect.x + int(40 * UI_SCALE), rect.y + int(40 * UI_SCALE), rect.width - int(60 * UI_SCALE), rect.height - int(70 * UI_SCALE))
        pygame.draw.line(self.screen, (120, 120, 140), (plot_rect.x, plot_rect.bottom), (plot_rect.right, plot_rect.bottom), 1)
        pygame.draw.line(self.screen, (120, 120, 140), (plot_rect.x, plot_rect.bottom), (plot_rect.x, plot_rect.top), 1)

        all_values = [value for values in series.values() for value in values]
        if not all_values:
            return
        min_val = min(all_values)
        max_val = max(all_values)
        if max_val == min_val:
            max_val += 1

        step_x = plot_rect.width / max(1, len(self.chart_labels) - 1)
        for label_index, label in enumerate(self.chart_labels):
            x = plot_rect.x + label_index * step_x
            pygame.draw.line(self.screen, (80, 80, 90), (x, plot_rect.bottom), (x, plot_rect.bottom + int(6 * UI_SCALE)), 1)
            lbl_surface = self.chart_axis_font.render(label, True, (200, 200, 200))
            self.screen.blit(lbl_surface, lbl_surface.get_rect(center=(x, plot_rect.bottom + int(16 * UI_SCALE))))

        for name, values in series.items():
            color = COLORS.get(name, (200, 200, 200))
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
        legend_y = plot_rect.top - int(18 * UI_SCALE)
        for idx, name in enumerate(series.keys()):
            color = COLORS.get(name, (200, 200, 200))
            pygame.draw.circle(self.screen, color, (legend_x, legend_y + idx * int(18 * UI_SCALE)), 5)
            lbl = self.chart_axis_font.render(name + unit, True, (220, 220, 220))
            self.screen.blit(lbl, (legend_x + int(12 * UI_SCALE), legend_y - int(6 * UI_SCALE) + idx * int(18 * UI_SCALE)))

    # ---------------- state & rng ----------------
    def _current_day_key(self):
        return datetime.now().strftime("%Y%m%d")

    def _derive_seed_from_key(self, key):
        try:
            return int(key)
        except (TypeError, ValueError):
            return abs(hash(key)) % (2 ** 31 - 1)

    def _load_shop_state(self):
        if not os.path.exists(self.shop_state_path):
            return
        try:
            with open(self.shop_state_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self.daily_seed_key = data.get("day_key")
            self.daily_seed_value = data.get("seed")
            sold = data.get("sold_out", [])
            if isinstance(sold, list):
                self.sold_out_cards = set(sold)
        except Exception:
            self.daily_seed_key = None
            self.daily_seed_value = None
            self.sold_out_cards = set()

    def _save_shop_state(self):
        state = {
            "day_key": self.daily_seed_key,
            "seed": self.daily_seed_value,
            "sold_out": sorted(self.sold_out_cards),
        }
        try:
            os.makedirs(os.path.dirname(self.shop_state_path), exist_ok=True)
            with open(self.shop_state_path, "w", encoding="utf-8") as fh:
                json.dump(state, fh, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _ensure_daily_rng(self):
        current_key = self._current_day_key()
        if self.daily_seed_key != current_key:
            self.daily_seed_key = current_key
            self.daily_seed_value = self._derive_seed_from_key(f"activity_{current_key}")
            self.sold_out_cards = set()
            self._save_shop_state()
        elif self.daily_seed_value is None:
            self.daily_seed_value = self._derive_seed_from_key(f"activity_{current_key}")
            self._save_shop_state()
        return random.Random(self.daily_seed_value)

    def _get_card_identifier(self, card):
        if not card:
            return None
        return getattr(card, "card_id", getattr(card, "name", None))

    def _is_card_sold_out(self, card):
        identifier = self._get_card_identifier(card)
        if not identifier:
            return False
        return identifier in self.sold_out_cards

    def _mark_card_sold(self, card):
        identifier = self._get_card_identifier(card)
        if identifier:
            self.sold_out_cards.add(identifier)

    def _mark_offer_sold_out(self, offer):
        offer["sold_out"] = True
        self._mark_card_sold(offer.get("card"))
        self._save_shop_state()

    def _populate_card_offers(self):
        rng = self._ensure_daily_rng()
        for key, spec in self.shelf_specs.items():
            min_c, max_c = spec["count_range"]
            target_count = rng.randint(min_c, max_c)
            offers = self._sample_cards(
                spec["rarities"],
                target_count,
                spec.get("allow_repeat", False),
                rng=rng,
            )
            self.card_offers[key] = offers

    def _sample_cards(self, rarities, count, allow_repeat, rng=None):
        rng = rng or random
        pool = []
        for rarity in rarities:
            pool.extend(self.card_db.get_cards_by_rarity(rarity))
        if not pool:
            return []

        if allow_repeat or len(pool) < count:
            selected = [rng.choice(pool) for _ in range(count)]
        else:
            selected = rng.sample(pool, count)

        offers = []
        for card in selected:
            offers.append({
                "card": card,
                "rarity": card.rarity,
                "price": {"amount": self._get_badge_price(card)},
                "sold_out": self._is_card_sold_out(card),
            })
        return offers

    def _get_badge_price(self, card):
        rarity = getattr(card, "rarity", None)
        return BADGE_PRICE_RULES.get(rarity, DEFAULT_BADGE_PRICE)

    def _handle_price_click(self, pos):
        for entry in self.price_hitboxes:
            if entry["rect"].collidepoint(pos):
                self._attempt_purchase(entry["offer"])
                return True
        return False

    def _attempt_purchase(self, offer):
        if offer.get("sold_out"):
            self._show_notice("该奖励已售罄")
            return
        price = offer["price"]
        amount = price.get("amount", DEFAULT_BADGE_PRICE)
        if not self.currency_ui.has_enough_badges(amount):
            self._show_notice("活动徽章不足，无法兑换")
            return
        if not self.currency_ui.spend_badges(amount):
            self._show_notice("兑换失败，请稍后重试")
            return
        card = offer.get("card")
        name = card.name if card else "奖励"
        self._mark_offer_sold_out(offer)
        self._grant_card_to_inventory(card)
        self._show_notice(f"已兑换 {name}")

    def _refresh_inventory(self):
        self._populate_card_offers()
        self._show_notice("活动货架已刷新")

    def _grant_card_to_inventory(self, card):
        if not card or not getattr(card, "image_path", None):
            return False
        rarity = getattr(card, "rarity", "A")
        normalized = card.image_path.replace("\\", "/")
        try:
            self.inventory.add_card(normalized, rarity)
            self.inventory.save()
            return True
        except Exception:
            return False

    def _show_notice(self, text):
        self.notice_message = text
        self.notice_timer = 2.3

    def _draw_notice(self):
        notice_surface = self.notice_font.render(self.notice_message, True, (255, 245, 230))
        notice_rect = notice_surface.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.92)))
        bg = pygame.Surface((notice_rect.width + int(40 * UI_SCALE), notice_rect.height + int(20 * UI_SCALE)), pygame.SRCALPHA)
        bg.fill((15, 15, 30, 190))
        self.screen.blit(bg, (notice_rect.x - int(20 * UI_SCALE), notice_rect.y - int(10 * UI_SCALE)))
        self.screen.blit(notice_surface, notice_rect)

    def _create_buttons(self):
        base_x = self.right_panel_rect.x + self.right_panel_rect.width - int(20 * UI_SCALE)
        base_y = self.right_panel_rect.bottom + int(12 * UI_SCALE)
        width = int(260 * UI_SCALE)
        height = int(52 * UI_SCALE)
        spacing = int(70 * UI_SCALE)
        specs = [
            ("常规商店", (180, 220, 255), (210, 240, 255), lambda: self.switch_to("shop_scene")),
            ("刷新货架", (255, 210, 160), (255, 230, 210), self._refresh_inventory),
            ("返回活动大厅", (120, 245, 210), (170, 255, 230), lambda: self.switch_to("activity_scene")),
            ("返回主菜单", (140, 200, 255), (180, 230, 255), lambda: self.switch_to("main_menu")),
        ]
        buttons = []
        for idx, (label, color, hover, action) in enumerate(specs):
            btn = MenuButton(
                base_x,
                base_y + spacing * idx,
                width,
                height,
                label,
                color=color,
                hover_color=hover,
                text_color=(25, 25, 25),
                on_click=action,
            )
            buttons.append(btn)
        return buttons

    def _generate_exchange_history(self):
        series = {
            "徽章/水晶": 1.8,
            "徽章/金币": 0.08,
        }
        data = {}
        for name, base in series.items():
            values = []
            current = base
            for _ in range(7):
                current += random.uniform(-0.05, 0.05) * base
                current = max(0.01, current)
                values.append(round(current, 3))
            data[name] = values
        return data

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

    def get_hovered_card(self, mouse_pos):
        for rect, card in self.hoverable_cards:
            if rect.collidepoint(mouse_pos):
                return card
        return None
