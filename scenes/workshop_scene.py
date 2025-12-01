"""工坊场景：提供卡牌祭坛融合系统"""
import math
import os
import random
import pygame

from config import *
from scenes.base.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.button import Button
from ui.panel import Panel
from ui.scroll_view import ScrollView
from ui.system_ui import CurrencyLevelUI
from utils.inventory import get_inventory
from utils.card_database import get_card_database, CardData


class WorkshopScene(BaseScene):
    """允许玩家消耗卡牌进行融合"""

    RARITY_ORDER = [
        "SSS", "SS+", "SS", "S+", "S",
        "A+", "A", "B+", "B", "C+", "C", "D"
    ]

    def __init__(self, screen):
        super().__init__(screen)
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "bg/activity")
        self.title_font = get_font(int(68 * UI_SCALE))
        self.text_font = get_font(int(28 * UI_SCALE))
        self.small_font = get_font(int(22 * UI_SCALE))
        self.currency_ui = CurrencyLevelUI()
        self.currency_ui.load_state()

        self.inventory = get_inventory()
        self.card_db = get_card_database()
        self.card_entries = []
        panel_width = int(WINDOW_WIDTH * 0.35)
        panel_height = int(WINDOW_HEIGHT * 0.7)
        panel_x = int(WINDOW_WIDTH * 0.05)
        panel_y = int(WINDOW_HEIGHT * 0.18)
        self.left_panel = Panel(panel_x, panel_y, panel_width, panel_height, color=(20, 25, 40), alpha=220, border_color=(120, 150, 200))
        self.card_panel_padding = int(18 * UI_SCALE)
        scroll_rect = pygame.Rect(
            panel_x + self.card_panel_padding,
            panel_y + int(60 * UI_SCALE),
            panel_width - 2 * self.card_panel_padding,
            panel_height - int(80 * UI_SCALE),
        )
        self.scroll_inner_padding = int(12 * UI_SCALE)
        self.card_scroll_view = ScrollView(scroll_rect.x, scroll_rect.y, scroll_rect.width, scroll_rect.height, 0)
        self.panel_cols = 6
        self.panel_card_spacing = int(10 * UI_SCALE)
        self.panel_card_size = self._calculate_panel_card_size(scroll_rect.width)
        self.list_content_height = 0
        self.altar_card_size = (int(210 * UI_SCALE), int(315 * UI_SCALE))
        self.altar_center = (int(WINDOW_WIDTH * 0.58), int(WINDOW_HEIGHT * 0.5))
        self.altar_radius = int(320 * UI_SCALE)
        self.slot_positions = []
        self.altar_slots = [None] * 5
        self.pending_slots = set()
        self.animations = []
        self.result_message = ""
        self.result_timer = 0.0
        self.obtained_card = None

        button_width = int(240 * UI_SCALE)
        button_height = int(64 * UI_SCALE)
        self.fusion_button = Button(
            self.altar_center[0] - button_width // 2,
            int(WINDOW_HEIGHT * 0.82),
            button_width,
            button_height,
            "融合",
            color=(255, 160, 90),
            hover_color=(255, 200, 140),
            text_color=(40, 20, 10),
            on_click=self._on_fuse_click,
        )
        self.fusion_button_enabled = False

        back_btn_width = int(200 * UI_SCALE)
        back_btn_height = int(56 * UI_SCALE)
        self.back_button = Button(
            WINDOW_WIDTH - back_btn_width - int(30 * UI_SCALE),
            int(30 * UI_SCALE),
            back_btn_width,
            back_btn_height,
            "返回菜单",
            color=(100, 100, 120),
            hover_color=(140, 140, 180),
            on_click=lambda: self.switch_to("main_menu"),
        )

        self._build_slot_rects()
        self._refresh_card_entries()

    # ------------------------------------------------------------------
    # 场景生命周期
    # ------------------------------------------------------------------
    def enter(self):
        super().enter()
        self.inventory.load()
        self._refresh_card_entries()

    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.switch_to("main_menu")
            return

        if event.type == pygame.MOUSEMOTION:
            self.background.update_mouse_position(event.pos)

        self.card_scroll_view.handle_event(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.card_scroll_view.rect.collidepoint(event.pos):
                    self._handle_card_panel_click(event.pos)
                else:
                    self._handle_slot_click(event.pos)

        self.fusion_button_enabled = self._can_fuse()
        if self.fusion_button_enabled:
            self.fusion_button.handle_event(event)
        else:
            self.fusion_button.is_hovered = False

        self.back_button.handle_event(event)

    def update(self, dt):
        super().update(dt)
        self.background.update(dt)
        self._update_animations(dt)
        if self.result_timer > 0:
            self.result_timer -= dt
            if self.result_timer <= 0:
                self.result_message = ""
                self.obtained_card = None

    def draw(self):
        self.background.draw(self.screen)
        self.currency_ui.draw(self.screen, position=(int(WINDOW_WIDTH * 0.04), int(WINDOW_HEIGHT * 0.02)))
        self._draw_title()
        self.back_button.draw(self.screen)
        self._draw_card_panel()
        self._draw_altar()
        self._draw_side_info_panel()
        self._draw_animations()
        self._draw_fusion_button()

    # ------------------------------------------------------------------
    # 绘制
    # ------------------------------------------------------------------
    def _draw_title(self):
        title_surface = self.title_font.render("工 坊", True, (255, 235, 200))
        shadow = self.title_font.render("工 坊", True, (0, 0, 0))
        offset = int(4 * UI_SCALE)
        center = (WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.08))
        self.screen.blit(shadow, (center[0] - shadow.get_width() // 2 + offset, center[1] - shadow.get_height() // 2 + offset))
        self.screen.blit(title_surface, (center[0] - title_surface.get_width() // 2, center[1] - title_surface.get_height() // 2))

    def _draw_card_panel(self):
        self.left_panel.draw(self.screen)
        title = self.text_font.render("收藏卡牌", True, (255, 230, 180))
        title_pos = (
            self.left_panel.rect.x + self.card_panel_padding,
            self.left_panel.rect.y + int(16 * UI_SCALE),
        )
        self.screen.blit(title, title_pos)
        total_available = sum(max(0, entry["count"] - entry["in_use"]) for entry in self.card_entries)
        subtitle = self.small_font.render(f"可用卡牌 {total_available}", True, (200, 210, 220))
        self.screen.blit(
            subtitle,
            (
                self.left_panel.rect.x + self.card_panel_padding,
                title_pos[1] + title.get_height() + int(8 * UI_SCALE),
            ),
        )

        surface, offset_y = self.card_scroll_view.begin_draw()
        surface.fill((25, 30, 45))
        mouse_pos = pygame.mouse.get_pos()
        for idx, entry in enumerate(self.card_entries):
            col = idx % self.panel_cols
            row = idx // self.panel_cols
            item_rect = pygame.Rect(
                self.scroll_inner_padding + col * (self.panel_card_size[0] + self.panel_card_spacing),
                offset_y + self.scroll_inner_padding + row * (self.panel_card_size[1] + self.panel_card_spacing),
                self.panel_card_size[0],
                self.panel_card_size[1],
            )
            screen_rect = pygame.Rect(
                self.card_scroll_view.rect.x + item_rect.x,
                self.card_scroll_view.rect.y + item_rect.y,
                item_rect.width,
                item_rect.height,
            )
            entry["screen_rect"] = screen_rect

            if item_rect.bottom < 0 or item_rect.top > self.card_scroll_view.rect.height:
                continue

            surface.blit(entry["panel_surface"], item_rect)
            border_color = COLORS.get(entry["rarity"], (180, 180, 180))
            pygame.draw.rect(surface, border_color, item_rect, width=2, border_radius=int(10 * UI_SCALE))

            available = max(0, entry["count"] - entry["in_use"])
            if available <= 0:
                depleted_overlay = pygame.Surface(item_rect.size, pygame.SRCALPHA)
                depleted_overlay.fill((0, 0, 0, 160))
                surface.blit(depleted_overlay, item_rect)

            if screen_rect.collidepoint(mouse_pos):
                hover_overlay = pygame.Surface(item_rect.size, pygame.SRCALPHA)
                hover_overlay.fill((255, 255, 255, 45))
                surface.blit(hover_overlay, item_rect)

            badge_size = max(26, int(32 * UI_SCALE))
            badge_rect = pygame.Rect(
                item_rect.right - badge_size - int(6 * UI_SCALE),
                item_rect.top + int(6 * UI_SCALE),
                badge_size,
                badge_size,
            )
            pygame.draw.circle(surface, (0, 0, 0, 200), badge_rect.center, badge_size // 2)
            pygame.draw.circle(surface, (255, 215, 0), badge_rect.center, badge_size // 2, 2)
            count_text = self.small_font.render(f"x{available}", True, (255, 255, 255))
            surface.blit(count_text, count_text.get_rect(center=badge_rect.center))

        self.card_scroll_view.end_draw(self.screen)

    def _draw_altar(self):
        center = self.altar_center
        radius = self.altar_radius
        angles = (-90, -18, 54, 126, 198)
        points = []
        for angle_deg in angles:
            rad = math.radians(angle_deg)
            x = center[0] + int(math.cos(rad) * radius)
            y = center[1] + int(math.sin(rad) * radius)
            points.append((x, y))
        pygame.draw.polygon(self.screen, (255, 230, 150, 60), points, width=2)
        star_indices = [0, 2, 4, 1, 3, 0]
        star_points = [points[idx] for idx in star_indices]
        pygame.draw.lines(self.screen, (255, 200, 120, 80), False, star_points, width=2)
        pygame.draw.circle(self.screen, (80, 120, 160, 80), center, int(radius * 0.2), width=2)

        for idx, slot in enumerate(self.slot_positions):
            rect = slot["rect"]
            pygame.draw.rect(
                self.screen,
                (255, 255, 255, 90),
                rect,
                width=2,
                border_radius=int(14 * UI_SCALE)
            )
            stored = self.altar_slots[idx]
            if stored:
                surface = stored.get("surface")
                if surface:
                    self.screen.blit(surface, surface.get_rect(center=rect.center))
            else:
                placeholder = self._draw_placeholder_card(rect.size)
                self.screen.blit(placeholder, rect.topleft)

    def _draw_placeholder_card(self, size):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (40, 40, 60, 140), surf.get_rect(), border_radius=int(14 * UI_SCALE))
        pygame.draw.rect(surf, (90, 90, 120, 200), surf.get_rect(), width=2, border_radius=int(14 * UI_SCALE))
        text = self.small_font.render("空", True, (200, 200, 200))
        surf.blit(text, text.get_rect(center=surf.get_rect().center))
        return surf

    def _draw_side_info_panel(self):
        distribution = self._calculate_probabilities()
        panel_width = int(WINDOW_WIDTH * 0.18)
        panel_height = int(WINDOW_HEIGHT * 0.64)
        margin = int(20 * UI_SCALE)
        left = self.altar_center[0] + self.altar_radius + 0.1 * WINDOW_WIDTH
        left = min(WINDOW_WIDTH - panel_width - margin, max(margin, left))
        top = max(margin, self.left_panel.rect.y)
        panel_rect = pygame.Rect(left, top, panel_width, panel_height)
        panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (15, 20, 30, 220), panel_surf.get_rect(), border_radius=int(18 * UI_SCALE))
        pygame.draw.rect(panel_surf, (255, 210, 140, 200), panel_surf.get_rect(), width=2, border_radius=int(18 * UI_SCALE))

        inset = int(14 * UI_SCALE)
        y = inset
        prob_title = self.text_font.render("融合概率", True, (255, 240, 210))
        panel_surf.blit(prob_title, (inset, y))
        y += prob_title.get_height() + int(10 * UI_SCALE)

        if not distribution:
            hint = self.small_font.render("放入卡牌可查看", True, (220, 220, 235))
            panel_surf.blit(hint, (inset, y))
            y += hint.get_height() + int(6 * UI_SCALE)
        else:
            sorted_items = sorted(distribution.items(), key=lambda item: item[1], reverse=True)
            for rarity, pct in sorted_items:
                color = COLORS.get(rarity, (220, 220, 220))
                text = self.small_font.render(f"{rarity}: {pct * 100:.1f}%", True, color)
                panel_surf.blit(text, (inset, y))
                y += text.get_height() + int(4 * UI_SCALE)
                if y > panel_rect.height * 0.4:
                    break

        y += int(12 * UI_SCALE)
        pygame.draw.line(panel_surf, (255, 210, 140, 160), (inset, y), (panel_rect.width - inset, y), width=2)
        y += int(18 * UI_SCALE)

        result_title = self.text_font.render("最新结果", True, (255, 240, 210))
        panel_surf.blit(result_title, (inset, y))
        y += result_title.get_height() + int(10 * UI_SCALE)

        if self.result_message:
            preview_size = (int(96 * UI_SCALE), int(144 * UI_SCALE))
            if self.obtained_card:
                preview = self._load_card_surface(self.obtained_card.image_path, preview_size, self.obtained_card.rarity)
            else:
                preview = self._draw_placeholder_card(preview_size)
            preview_rect = preview.get_rect(topleft=(inset, y))
            panel_surf.blit(preview, preview_rect)

            text_x = preview_rect.right + int(10 * UI_SCALE)
            max_width = panel_rect.width - text_x - inset
            lines = self._wrap_text_lines(self.result_message, self.small_font, max_width)
            line_y = y
            for line in lines:
                text_surface = self.small_font.render(line, True, (255, 235, 200))
                panel_surf.blit(text_surface, (text_x, line_y))
                line_y += text_surface.get_height() + int(4 * UI_SCALE)
        else:
            empty = self.small_font.render("暂无融合记录", True, (200, 210, 220))
            panel_surf.blit(empty, (inset, y))

        self.screen.blit(panel_surf, panel_rect.topleft)

    def _draw_fusion_button(self):
        self.fusion_button_enabled = self._can_fuse()
        self.fusion_button.draw(self.screen)
        if not self.fusion_button_enabled:
            overlay = pygame.Surface(self.fusion_button.rect.size, pygame.SRCALPHA)
            overlay.fill((10, 10, 10, 160))
            self.screen.blit(overlay, self.fusion_button.rect.topleft)

    def _draw_animations(self):
        for anim in self.animations:
            surface = anim["surface"]
            start = anim["start"]
            end = anim["end"]
            t = anim["progress"]
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            rect = surface.get_rect(center=(int(x), int(y)))
            self.screen.blit(surface, rect)

    # ------------------------------------------------------------------
    # 逻辑
    # ------------------------------------------------------------------
    def _refresh_card_entries(self):
        unique_cards = self.inventory.get_unique_cards()
        entries = []
        for idx, record in enumerate(unique_cards):
            card = self.card_db.get_card_by_path(record["path"]) or self._build_fallback_card(record)
            panel_surface = self._load_card_surface(card.image_path, self.panel_card_size, card.rarity)
            altar_surface = self._load_card_surface(card.image_path, self.altar_card_size, card.rarity)
            entries.append({
                "id": idx,
                "path": record["path"],
                "rarity": record["rarity"],
                "count": record["count"],
                "in_use": 0,
                "card": card,
                "panel_surface": panel_surface,
                "altar_surface": altar_surface,
                "screen_rect": None,
            })
        entries.sort(key=lambda e: (self._rarity_index(e["rarity"]), e["card"].name))
        self.card_entries = entries
        self._update_scroll_content_height()

    def _update_scroll_content_height(self):
        total_items = len(self.card_entries)
        if total_items <= 0:
            content_height = self.card_scroll_view.rect.height
        else:
            rows = (total_items + self.panel_cols - 1) // self.panel_cols
            content_height = (
                2 * self.scroll_inner_padding
                + rows * self.panel_card_size[1]
                + max(0, rows - 1) * self.panel_card_spacing
            )
        self.list_content_height = content_height
        self.card_scroll_view.update_content_height(content_height)

    def _calculate_panel_card_size(self, scroll_width):
        available_width = scroll_width - 2 * self.scroll_inner_padding
        spacing_total = max(0, (self.panel_cols - 1) * self.panel_card_spacing)
        card_width = max(int(80 * UI_SCALE), (available_width - spacing_total) // max(1, self.panel_cols))
        card_height = int(card_width * 1.45)
        return (card_width, card_height)

    def _handle_card_panel_click(self, mouse_pos):
        entry = self._get_entry_at(mouse_pos)
        if not entry:
            return
        available = entry["count"] - entry["in_use"]
        if available <= 0:
            self._set_result_message("该卡牌数量不足")
            return
        slot_idx = self._get_first_empty_slot()
        if slot_idx is None:
            self._set_result_message("祭坛已满")
            return
        entry["in_use"] += 1
        start_pos = entry.get("screen_rect").center if entry.get("screen_rect") else mouse_pos
        self._start_add_animation(entry, slot_idx, start_pos)

    def _handle_slot_click(self, mouse_pos):
        idx = self._get_slot_index(mouse_pos)
        if idx is None:
            return
        if idx in self.pending_slots:
            return
        stored = self.altar_slots[idx]
        if not stored:
            return
        entry = stored.get("entry")
        if entry:
            entry["in_use"] = max(0, entry["in_use"] - 1)
        self.altar_slots[idx] = None

    def _start_add_animation(self, entry, slot_idx, start_pos):
        self.pending_slots.add(slot_idx)
        dest_center = self.slot_positions[slot_idx]["rect"].center
        animation = {
            "entry": entry,
            "slot": slot_idx,
            "surface": entry["altar_surface"],
            "start": start_pos,
            "end": dest_center,
            "duration": 0.35,
            "elapsed": 0.0,
            "progress": 0.0,
        }
        self.animations.append(animation)

    def _update_animations(self, dt):
        remaining = []
        for anim in self.animations:
            anim["elapsed"] += dt
            duration = max(0.001, anim["duration"])
            anim["progress"] = min(1.0, anim["elapsed"] / duration)
            if anim["progress"] >= 1.0:
                self._complete_animation(anim)
            else:
                remaining.append(anim)
        self.animations = remaining

    def _complete_animation(self, anim):
        slot_idx = anim["slot"]
        entry = anim["entry"]
        self.pending_slots.discard(slot_idx)
        self.altar_slots[slot_idx] = {
            "entry": entry,
            "path": entry["path"],
            "rarity": entry["rarity"],
            "card": entry["card"],
            "surface": entry["altar_surface"],
        }

    def _calculate_probabilities(self):
        filled_slots = [slot for slot in self.altar_slots if slot]
        if not filled_slots:
            return {}
        distribution = {rarity: 0.05 for rarity in self.RARITY_ORDER}
        for slot in filled_slots:
            rarity = slot["rarity"]
            idx = self._rarity_index(rarity)
            distribution[rarity] = distribution.get(rarity, 0.0) + 1.0
            if idx - 1 >= 0:
                neighbor = self.RARITY_ORDER[idx - 1]
                distribution[neighbor] = distribution.get(neighbor, 0.0) + 0.35
            if idx + 1 < len(self.RARITY_ORDER):
                neighbor = self.RARITY_ORDER[idx + 1]
                distribution[neighbor] = distribution.get(neighbor, 0.0) + 0.2
        total = sum(distribution.values())
        if total <= 0:
            return {}
        return {rarity: value / total for rarity, value in distribution.items()}

    def _on_fuse_click(self):
        if not self._can_fuse():
            self._set_result_message("需要 5 张卡牌才能融合")
            return
        distribution = self._calculate_probabilities()
        if not distribution:
            self._set_result_message("无法计算概率")
            return
        rarity = self._weighted_choice(distribution)
        new_card = self._draw_card_by_rarity(rarity)
        consumed_paths = [slot["path"] for slot in self.altar_slots if slot]
        for path in consumed_paths:
            self.inventory.remove_card(path)
        if new_card:
            normalized = new_card.image_path.replace("\\", "/") if new_card.image_path else ""
            self.inventory.add_card(normalized, new_card.rarity)
            self.obtained_card = new_card
            self._set_result_message(f"融合成功！获得 [{new_card.rarity}] {new_card.name}")
        else:
            self.obtained_card = None
            self._set_result_message("融合失败：未找到可用卡牌")
        self.inventory.save()
        self._clear_altar()
        self._refresh_card_entries()

    def _clear_altar(self):
        self.altar_slots = [None] * 5
        self.pending_slots.clear()
        self.animations.clear()

    def _set_result_message(self, text):
        self.result_message = text
        self.result_timer = 3.0

    def _get_entry_at(self, mouse_pos):
        for entry in self.card_entries:
            rect = entry.get("screen_rect")
            if rect and rect.collidepoint(mouse_pos):
                return entry
        return None

    def _get_first_empty_slot(self):
        for idx, slot in enumerate(self.altar_slots):
            if slot is None and idx not in self.pending_slots:
                return idx
        return None

    def _get_slot_index(self, mouse_pos):
        for idx, slot in enumerate(self.slot_positions):
            if slot["rect"].collidepoint(mouse_pos):
                return idx
        return None

    def _can_fuse(self):
        return all(slot for slot in self.altar_slots) and not self.animations

    def _weighted_choice(self, distribution):
        total = sum(distribution.values())
        roll = random.uniform(0, total)
        current = 0.0
        for rarity, weight in distribution.items():
            current += weight
            if roll <= current:
                return rarity
        return self.RARITY_ORDER[-1]

    def _draw_card_by_rarity(self, rarity):
        pool = self.card_db.get_cards_by_rarity(rarity)
        if pool:
            return random.choice(pool)
        return None

    def _build_slot_rects(self):
        angles = [-90, -18, 54, 126, 198]
        rects = []
        for angle in angles:
            rad = math.radians(angle)
            x = self.altar_center[0] + int(math.cos(rad) * self.altar_radius)
            y = self.altar_center[1] + int(math.sin(rad) * self.altar_radius)
            rect = pygame.Rect(0, 0, *self.altar_card_size)
            rect.center = (x, y)
            rects.append({"rect": rect})
        self.slot_positions = rects

    def get_hovered_card(self, mouse_pos):
        for idx, slot in enumerate(self.slot_positions):
            rect = slot["rect"]
            if rect.collidepoint(mouse_pos):
                stored = self.altar_slots[idx]
                if stored:
                    return stored.get("card")
        if self.card_scroll_view.rect.collidepoint(mouse_pos):
            for entry in self.card_entries:
                rect = entry.get("screen_rect")
                if rect and rect.collidepoint(mouse_pos):
                    return entry["card"]
        return None

    def _rarity_index(self, rarity):
        try:
            return self.RARITY_ORDER.index(rarity)
        except ValueError:
            return len(self.RARITY_ORDER) - 1

    def _build_fallback_card(self, record):
        name = os.path.splitext(os.path.basename(record.get("path", "")))[0] or "未知卡牌"
        return CardData(
            card_id=f"workshop_{name}",
            name=name,
            rarity=record.get("rarity", "A"),
            atk=0,
            hp=0,
            cd=0,
            image_path=record.get("path", ""),
        )

    def _wrap_text_lines(self, text, font, max_width):
        if not text:
            return []
        if max_width <= 0:
            return [text]
        lines = []
        current = ""
        for char in text:
            candidate = current + char
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = char
        if current:
            lines.append(current)
        return lines

    def _load_card_surface(self, path, size, rarity):
        width, height = size
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        image_loaded = False
        if path and os.path.exists(path):
            try:
                image = pygame.image.load(path).convert_alpha()
                surface = pygame.transform.smoothscale(image, (width, height))
                image_loaded = True
            except Exception:
                image_loaded = False
        if not image_loaded:
            color = COLORS.get(rarity, (120, 120, 120))
            pygame.draw.rect(surface, color, surface.get_rect(), border_radius=int(14 * UI_SCALE))
            pygame.draw.rect(surface, (255, 255, 255), surface.get_rect(), width=2, border_radius=int(14 * UI_SCALE))
            text = self.small_font.render(rarity, True, (0, 0, 0))
            surface.blit(text, text.get_rect(center=surface.get_rect().center))
        return surface
        