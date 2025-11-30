"""迷宫楼层商店"""
from __future__ import annotations

import copy
import json
import os
import random
from datetime import datetime
from types import SimpleNamespace

import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, UI_SCALE, get_font
from scenes.base.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.menu_button import MenuButton
from ui.system_ui import CurrencyLevelUI
from utils.card_database import get_card_database
from utils.inventory import get_inventory
from utils.scene_payload import pop_payload

class FloorShopScene(BaseScene):
    RARITY_COLORS = {
        "SSS": (255, 140, 140),
        "SS+": (255, 170, 140),
        "SS": (255, 180, 140),
        "S+": (255, 200, 150),
        "S": (255, 220, 160),
        "A+": (210, 215, 255),
        "A": (180, 255, 190),
        "B+": (170, 230, 255),
        "B": (160, 210, 255),
        "C+": (190, 255, 210),
        "C": (210, 210, 210),
        "D": (200, 200, 200),
    }
    CURRENCY_COLORS = {
        "gold": (255, 225, 150),
        "crystal": (170, 210, 255),
    }
    PRICE_RULES = {
        "SSS": {"currency": "crystal", "amount": 551},
        "SS+": {"currency": "crystal", "amount": 430},
        "SS": {"currency": "crystal", "amount": 324},
        "S+": {"currency": "crystal", "amount": 200},
        "S": {"currency": "crystal", "amount": 120},
        "A+": {"currency": "gold", "amount": 5200},
        "A": {"currency": "gold", "amount": 4153},
        "B+": {"currency": "gold", "amount": 3100},
        "B": {"currency": "gold", "amount": 2589},
        "C+": {"currency": "gold", "amount": 1900},
        "C": {"currency": "gold", "amount": 1354},
        "D": {"currency": "gold", "amount": 690},
    }

    def __init__(self, screen):
        super().__init__(screen)
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "bg/activity")
        self.title_font = get_font(int(72 * UI_SCALE))
        self.section_font = get_font(int(36 * UI_SCALE))
        self.text_font = get_font(int(26 * UI_SCALE))
        self.small_font = get_font(int(20 * UI_SCALE))
        self.notice_font = get_font(int(28 * UI_SCALE))
        self.currency_ui = CurrencyLevelUI()
        self.currency_ui.load_state()
        self.inventory = get_inventory()
        self.card_db = get_card_database()
        self.traits: list[dict] = []
        self.shop_cards: list[dict] = []
        self.card_panel_rect: pygame.Rect | None = None
        self.node_info: dict = {}
        self.generated_at: str = ""
        self.save_path: str = ""
        self.node_id: int | None = None
        self.shop_state: dict = {}
        self.card_button_rects: list[tuple[int, pygame.Rect]] = []
        self.hoverable_cards: list[tuple[pygame.Rect, object]] = []
        self.notice_text = ""
        self.notice_timer = 0.0
        self.card_image_cache: dict[tuple[str, tuple[int, int]], pygame.Surface] = {}
        self.buttons = self._build_buttons()

    def _build_buttons(self):
        width = int(260 * UI_SCALE)
        height = int(54 * UI_SCALE)
        spacing = int(24 * UI_SCALE)
        base_y = int(WINDOW_HEIGHT * 0.86)
        base_x = int(WINDOW_WIDTH * 0.32)
        buttons = [
            MenuButton(
                base_x,
                base_y,
                width,
                height,
                "返回迷宫",
                color=(120, 200, 255),
                hover_color=(160, 230, 255),
                text_color=(20, 25, 30),
                on_click=lambda: self.switch_to("activity_maze_scene"),
            ),
            MenuButton(
                base_x + width + spacing,
                base_y,
                width,
                height,
                "返回活动列表",
                color=(160, 245, 210),
                hover_color=(190, 255, 230),
                text_color=(20, 25, 30),
                on_click=lambda: self.switch_to("activity_scene"),
            ),
        ]
        return buttons

    def enter(self):
        super().enter()
        payload = pop_payload("floor_shop") or {}
        self._apply_payload(payload)

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("activity_maze_scene")
        elif event.type == pygame.MOUSEMOTION:
            self.background.update_mouse_position(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._handle_card_click(event.pos):
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
                self.notice_timer = 0
                self.notice_text = ""

    def draw(self):
        self.background.draw(self.screen)
        self.currency_ui.draw(self.screen, (int(WINDOW_WIDTH * 0.04), int(WINDOW_HEIGHT * 0.03)))
        self._draw_header()
        self._draw_cards()
        self._draw_traits()
        self._draw_footer()
        for button in self.buttons:
            button.draw(self.screen)
        self._draw_notice()

    def _draw_header(self):
        title = self.title_font.render("楼层补给站", True, (255, 245, 235))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.1)))
        self.screen.blit(title, title_rect)
        subtitle_text = self.section_font.render("抵达补给节点，选择临时增益与卡牌。", True, (215, 230, 255))
        subtitle_rect = subtitle_text.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.16)))
        self.screen.blit(subtitle_text, subtitle_rect)
        info = f"节点: {self.node_info.get('node_event', '未知')}  |  楼层: {self.node_info.get('floor', '-')}"
        info_surface = self.text_font.render(info, True, (230, 235, 255))
        info_rect = info_surface.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.21)))
        self.screen.blit(info_surface, info_rect)

    def _draw_traits(self):
        if not self.traits:
            return
        panel_rect = getattr(self, "card_panel_rect", None)
        width = int(WINDOW_WIDTH * 0.22)
        if panel_rect:
            base_x = max(int(panel_rect.x - width - int(24 * UI_SCALE)), int(WINDOW_WIDTH * 0.03))
        else:
            base_x = int(WINDOW_WIDTH * 0.08)
        base_y = int(WINDOW_HEIGHT * 0.28)
        height = int(110 * UI_SCALE)
        gap = int(18 * UI_SCALE)
        for idx, trait in enumerate(self.traits):
            rect = pygame.Rect(base_x, base_y + idx * (height + gap), width, height)
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            panel.fill((25, 40, 70, 200))
            pygame.draw.rect(panel, (90, 150, 220, 230), panel.get_rect(), width=2, border_radius=int(12 * UI_SCALE))
            self.screen.blit(panel, rect.topleft)
            rarity = trait.get("rarity", "A")
            color = self.RARITY_COLORS.get(rarity, (255, 255, 255))
            name = self.text_font.render(f"[{rarity}] {trait.get('name')}", True, color)
            self.screen.blit(name, (rect.x + int(16 * UI_SCALE), rect.y + int(12 * UI_SCALE)))
            desc_lines = self._wrap_text(trait.get("desc", ""), self.small_font, width - int(32 * UI_SCALE))
            for line_idx, surface in enumerate(desc_lines):
                self.screen.blit(surface, (rect.x + int(16 * UI_SCALE), rect.y + int(48 * UI_SCALE) + line_idx * int(24 * UI_SCALE)))

    def _draw_cards(self):
        self.card_panel_rect = None
        if not self.shop_cards:
            return
        panel_width = int(WINDOW_WIDTH * 0.78)
        panel_height = int(WINDOW_HEIGHT * 0.45)
        panel_rect = pygame.Rect(
            int((WINDOW_WIDTH - panel_width) / 2),
            int(WINDOW_HEIGHT * 0.28),
            panel_width,
            panel_height,
        )
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surface.fill((22, 32, 58, 150))
        pygame.draw.rect(panel_surface, (90, 150, 220, 150), panel_surface.get_rect(), width=3, border_radius=int(24 * UI_SCALE))
        self.screen.blit(panel_surface, panel_rect.topleft)
        self.card_panel_rect = panel_rect.copy()

        self.card_button_rects = []
        self.hoverable_cards = []
        columns = min(3, len(self.shop_cards))
        if columns <= 0:
            return
        slot_gap = int(32 * UI_SCALE)
        slot_width = int((panel_rect.width - slot_gap * (columns - 1)) / columns)
        slot_height = panel_rect.height - int(50 * UI_SCALE)
        start_x = panel_rect.x + (panel_rect.width - (slot_width * columns + slot_gap * (columns - 1))) // 2
        slot_top = panel_rect.y + int(24 * UI_SCALE)

        for idx in range(columns):
            entry = self.shop_cards[idx]
            slot_rect = pygame.Rect(
                start_x + idx * (slot_width + slot_gap),
                slot_top,
                slot_width,
                slot_height,
            )
            self._draw_card_slot(entry, slot_rect)

    def _draw_card_slot(self, entry, rect):
        source = entry.get("source", "regular")
        base_color = (40, 48, 90, 230) if source != "event" else (58, 42, 90, 235)
        border_color = (140, 200, 255, 230) if source != "event" else (255, 210, 150, 235)
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill(base_color)
        pygame.draw.rect(panel, border_color, panel.get_rect(), width=3, border_radius=int(18 * UI_SCALE))
        self.screen.blit(panel, rect.topleft)

        padding = int(18 * UI_SCALE)
        label_text = entry.get("label", "迷宫补给")
        label_color = (255, 225, 170) if source == "event" else (195, 225, 255)
        label_surface = self.text_font.render(label_text, True, label_color)
        self.screen.blit(label_surface, (rect.x + padding, rect.y + padding))

        card = entry.get("card", {})
        rarity = card.get("rarity", "A")
        rarity_color = self.RARITY_COLORS.get(rarity, (255, 255, 255))
        content_top = rect.y + padding + label_surface.get_height() + int(8 * UI_SCALE)
        available_width = max(int(80 * UI_SCALE), rect.width - padding * 2)
        max_img_width = min(int(260 * UI_SCALE), available_width)
        available_height = max(int(140 * UI_SCALE), rect.height - int(200 * UI_SCALE))
        img_height = min(int(260 * UI_SCALE), available_height)
        image_surface = self._get_card_image(card.get("image_path"), rarity, (max_img_width, img_height))
        img_rect = image_surface.get_rect()
        img_rect.centerx = rect.centerx
        img_rect.top = content_top
        self.screen.blit(image_surface, img_rect)
        tooltip_rect = pygame.Rect(rect.x + padding, rect.y + padding, rect.width - padding * 2, max(img_rect.bottom - rect.y - padding, int(140 * UI_SCALE)))
        tooltip_card = self._resolve_card_for_tooltip(card)
        if tooltip_card:
            self.hoverable_cards.append((tooltip_rect, tooltip_card))

        text_y = img_rect.bottom + int(12 * UI_SCALE)
        name_surface = self.text_font.render(card.get("name", "未知卡牌"), True, rarity_color)
        self.screen.blit(name_surface, (rect.x + padding, text_y))
        text_y += name_surface.get_height() + int(6 * UI_SCALE)

        stats = f"ATK {card.get('atk', 0)} | HP {card.get('hp', 0)}"
        stats_surface = self.small_font.render(stats, True, (230, 235, 255))
        self.screen.blit(stats_surface, (rect.x + padding, text_y))
        text_y += stats_surface.get_height() + int(4 * UI_SCALE)

        cd_surface = self.small_font.render(f"CD {card.get('cd', 0)}", True, (210, 215, 245))
        self.screen.blit(cd_surface, (rect.x + padding, text_y))
        text_y += cd_surface.get_height() + int(6 * UI_SCALE)

        traits = card.get("traits") or ["无特性"]
        for trait_text in traits[:3]:
            trait_surface = self.small_font.render(f"· {trait_text}", True, (180, 255, 210))
            self.screen.blit(trait_surface, (rect.x + padding, text_y))
            text_y += int(22 * UI_SCALE)

        qty_max = max(1, int(entry.get("quantity", 1)))
        remaining = 0 if entry.get("sold") else qty_max
        qty_surface = self.small_font.render(f"库存 {remaining}/{qty_max}", True, (245, 245, 255))
        self.screen.blit(qty_surface, (rect.x + padding, rect.bottom - int(86 * UI_SCALE)))

        price = self._ensure_price_payload(entry)
        price_text = self._format_price_text(price)
        price_surface = self.small_font.render(price_text, True, self.CURRENCY_COLORS.get(price.get("currency", "gold"), (235, 235, 235)))

        btn_height = int(42 * UI_SCALE)
        btn_rect = pygame.Rect(
            rect.x + padding,
            rect.bottom - btn_height - int(24 * UI_SCALE),
            rect.width - padding * 2,
            btn_height,
        )
        sold = bool(entry.get("sold"))
        btn_color = (120, 210, 255) if not sold else (90, 90, 110)
        pygame.draw.rect(self.screen, btn_color, btn_rect, border_radius=int(12 * UI_SCALE))
        btn_label = "购买" if not sold else "已售罄"
        btn_text = self.small_font.render(btn_label, True, (25, 30, 36) if not sold else (220, 220, 230))
        btn_text_rect = btn_text.get_rect(center=btn_rect.center)
        self.screen.blit(btn_text, btn_text_rect)
        price_pos = (btn_rect.x, btn_rect.y - price_surface.get_height() - int(6 * UI_SCALE))
        self.screen.blit(price_surface, price_pos)
        if not sold:
            self.card_button_rects.append((entry.get("slot", 0), btn_rect.copy()))
        else:
            overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
            overlay.fill((10, 10, 20, 120))
            sold_surface = self.text_font.render("已售罄", True, (255, 225, 225))
            sold_rect = sold_surface.get_rect(center=rect.center)
            overlay.blit(sold_surface, (sold_rect.x - rect.x, sold_rect.y - rect.y))
            self.screen.blit(overlay, rect.topleft)

    def _draw_footer(self):
        if not self.generated_at:
            return
        text = self.small_font.render(f"补给已刷新于 {self.generated_at}", True, (220, 235, 255))
        rect = text.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.78)))
        self.screen.blit(text, rect)

    def _draw_notice(self):
        if not self.notice_text:
            return
        text_surface = self.notice_font.render(self.notice_text, True, (255, 245, 235))
        text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.84)))
        bg = pygame.Surface((text_rect.width + int(40 * UI_SCALE), text_rect.height + int(20 * UI_SCALE)), pygame.SRCALPHA)
        bg.fill((10, 14, 26, 200))
        self.screen.blit(bg, (text_rect.x - int(20 * UI_SCALE), text_rect.y - int(10 * UI_SCALE)))
        self.screen.blit(text_surface, text_rect)

    def _apply_payload(self, payload):
        self.card_image_cache.clear()
        self.shop_state = payload.get("shop_state") or {}
        cards_payload = payload.get("cards") or self.shop_state.get("cards")
        if cards_payload:
            self.shop_cards = copy.deepcopy(cards_payload)
        else:
            self.shop_cards = self._build_placeholder_cards()
        self._normalize_shop_cards()

        traits_payload = payload.get("traits") or self.shop_state.get("traits")
        self.traits = traits_payload or self._build_placeholder_traits()
        self.generated_at = payload.get("generated_at") or self.shop_state.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.node_id = payload.get("node_id")
        self.node_info = {
            "floor": payload.get("floor", "未知"),
            "node_id": self.node_id,
            "node_event": payload.get("node_event") or f"节点 {payload.get('node_id', '?')}",
        }
        self.save_path = payload.get("save_path") or ""
        self.card_button_rects = []
        self.hoverable_cards = []
        self.notice_text = ""
        self.notice_timer = 0.0

    def _normalize_shop_cards(self):
        normalized = []
        for idx, slot in enumerate(self.shop_cards):
            slot_copy = dict(slot)
            slot_copy["slot"] = idx
            slot_copy.setdefault("label", "迷宫补给")
            slot_copy.setdefault("quantity", 1)
            slot_copy.setdefault("sold", False)
            slot_copy.setdefault("source", slot_copy.get("source", "regular"))
            slot_copy.setdefault("card", {})
            self._ensure_price_payload(slot_copy)
            normalized.append(slot_copy)
        self.shop_cards = normalized

    def _build_placeholder_traits(self):
        samples = [
            {"name": "临时强化", "desc": "下一场战斗攻击卡 +10%。", "rarity": "A"},
            {"name": "疾风", "desc": "首张卡牌费用 -1。", "rarity": "B"},
        ]
        return samples

    def _build_placeholder_cards(self):
        cards = self.card_db.get_all_cards()
        if not cards:
            return []
        random.shuffle(cards)
        picked = cards[:3]
        entries = []
        for idx, card in enumerate(picked):
            entries.append({
                "slot": idx,
                "label": "迷宫补给",
                "quantity": 1,
                "sold": False,
                "source": "placeholder",
                "card": {
                    "card_id": card.card_id,
                    "name": card.name,
                    "rarity": card.rarity,
                    "atk": card.atk,
                    "hp": card.hp,
                    "cd": card.cd,
                    "traits": card.traits,
                    "image_path": getattr(card, "image_path", ""),
                }
            })
        return entries

    def _handle_card_click(self, mouse_pos):
        for slot_index, rect in self.card_button_rects:
            if rect.collidepoint(mouse_pos):
                self._purchase_card(slot_index)
                return True
        return False

    def _purchase_card(self, slot_index):
        if slot_index is None or slot_index >= len(self.shop_cards):
            return
        slot = self.shop_cards[slot_index]
        if slot.get("sold"):
            self._show_notice("该补给已售罄")
            return
        price = self._ensure_price_payload(slot)
        currency = price.get("currency", "gold")
        amount = int(price.get("amount", 0))
        if not self._has_enough_currency(currency, amount):
            need_label = "金币" if currency == "gold" else "水晶"
            self._show_notice(f"{need_label}不足，无法购买")
            return
        if not self._spend_currency(currency, amount):
            self._show_notice("扣费失败，请稍后重试")
            return
        slot["sold"] = True
        if not self._persist_shop_purchase(slot_index):
            slot["sold"] = False
            self._refund_currency(currency, amount)
            self._show_notice("记录更新失败，已退款")
            return
        card_name = slot.get("card", {}).get("name", "补给卡牌")
        granted = self._grant_card_to_inventory(slot.get("card"))
        suffix = "，已加入库存" if granted else ""
        self._show_notice(f"已购入 {card_name}{suffix}")

    def _persist_shop_purchase(self, slot_index):
        if not self.save_path or self.node_id is None:
            return False
        try:
            with open(self.save_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
        except (OSError, json.JSONDecodeError):
            return False

        updated = False
        for node in data.get("nodes", []):
            if node.get("id") == self.node_id:
                shop_state = node.get("shop_state") or {}
                cards = shop_state.get("cards") or []
                if 0 <= slot_index < len(cards):
                    if not cards[slot_index].get("sold"):
                        cards[slot_index]["sold"] = True
                        updated = True
                    else:
                        updated = True
                break

        if not updated:
            return False
        try:
            with open(self.save_path, "w", encoding="utf-8") as fp:
                json.dump(data, fp, ensure_ascii=False, indent=2)
            return True
        except OSError:
            return False

    def _show_notice(self, text):
        self.notice_text = text
        self.notice_timer = 2.5

    def _get_card_image(self, image_path, rarity, size):
        width = max(10, size[0])
        height = max(10, size[1])
        normalized_size = (width, height)
        cache_key = (image_path or "placeholder", normalized_size)
        if cache_key in self.card_image_cache:
            return self.card_image_cache[cache_key]

        surface = None
        normalized_path = None
        if image_path:
            normalized_path = image_path.replace("/", os.sep)
            if os.path.exists(normalized_path):
                try:
                    image = pygame.image.load(normalized_path).convert_alpha()
                    surface = pygame.transform.smoothscale(image, normalized_size)
                except Exception:
                    surface = None

        if surface is None:
            surface = self._create_card_placeholder(normalized_size, rarity)

        self.card_image_cache[cache_key] = surface
        return surface

    def _create_card_placeholder(self, size, rarity):
        color = self.RARITY_COLORS.get(rarity, (160, 160, 160))
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (*color, 210), surf.get_rect(), border_radius=int(18 * UI_SCALE))
        pygame.draw.rect(surf, (255, 255, 255, 80), surf.get_rect(), width=2, border_radius=int(18 * UI_SCALE))
        return surf

    def _ensure_price_payload(self, slot):
        price = slot.get("price")
        if isinstance(price, dict) and price.get("currency") is not None:
            try:
                price["amount"] = int(price.get("amount", 0))
            except Exception:
                price["amount"] = 0
            if not price.get("currency"):
                price["currency"] = "gold"
            slot["price"] = price
            return price
        computed = self._build_price_for_card(slot.get("card"), slot.get("source"))
        slot["price"] = computed
        return computed

    def _build_price_for_card(self, card_payload, source):
        rarity = (card_payload or {}).get("rarity", "A")
        base_rule = self.PRICE_RULES.get(rarity, {"currency": "gold", "amount": 1200})
        price = {
            "currency": base_rule.get("currency", "gold"),
            "amount": int(base_rule.get("amount", 0))
        }
        if source == "regular":
            price["amount"] = max(50, int(price["amount"] * 0.85))
        elif source == "event":
            price["currency"] = "crystal"
            price["amount"] = max(75, int(price["amount"] * 1.2))
        return price

    def _format_price_text(self, price):
        currency = price.get("currency", "gold")
        amount = int(price.get("amount", 0))
        label = "金币" if currency == "gold" else "水晶"
        return f"{label} {amount}"

    def _resolve_card_for_tooltip(self, card_payload):
        if not card_payload:
            return None
        card_id = card_payload.get("card_id")
        if card_id:
            card_obj = self.card_db.get_card(card_id)
            if card_obj:
                return card_obj
        return SimpleNamespace(
            name=card_payload.get("name", "未知卡牌"),
            atk=card_payload.get("atk", 0),
            hp=card_payload.get("hp", 0),
            rarity=card_payload.get("rarity", "A"),
            cd=card_payload.get("cd", 0),
            traits=card_payload.get("traits", []),
            description=card_payload.get("description", "")
        )

    def _grant_card_to_inventory(self, card_payload):
        if not card_payload:
            return False
        path = card_payload.get("image_path")
        rarity = card_payload.get("rarity", "A")
        if not path:
            return False
        normalized = path.replace("\\", "/")
        self.inventory.add_card(normalized, rarity)
        self.inventory.save()
        return True

    def _has_enough_currency(self, currency, amount):
        if currency == "gold":
            return self.currency_ui.has_enough_golds(amount)
        return self.currency_ui.has_enough_crystals(amount)

    def _spend_currency(self, currency, amount):
        if currency == "gold":
            return self.currency_ui.spend_golds(amount)
        else:
            return self.currency_ui.spend_crystals(amount)

    def _refund_currency(self, currency, amount):
        if amount <= 0:
            return
        if currency == "gold":
            self.currency_ui.add_golds(amount)
        else:
            self.currency_ui.add_crystals(amount)
        self.currency_ui.save_state()

    def _wrap_text(self, text, font, max_width):
        if not text:
            return []
        words = list(text)
        lines = []
        current = ""
        for char in words:
            trial = current + char
            if font.size(trial)[0] > max_width and current:
                lines.append(font.render(current, True, (215, 225, 255)))
                current = char
            else:
                current = trial
        if current:
            lines.append(font.render(current, True, (215, 225, 255)))
        return lines

    def get_hovered_card(self, mouse_pos):
        for rect, card in self.hoverable_cards:
            if rect.collidepoint(mouse_pos):
                return card
        return None
