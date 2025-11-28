"""Reusable detail panel to preview chapter or stage information."""
from __future__ import annotations

import os
import pygame
from typing import List, Optional
from config import UI_SCALE, get_font

BACKGROUND_COLOR = (8, 10, 24, 235)
BORDER_COLOR = (255, 196, 120)
TITLE_COLOR = (255, 240, 220)
SUBTITLE_COLOR = (180, 200, 255)
BODY_COLOR = (220, 220, 230)
TAG_BG = (255, 215, 120, 40)
TAG_COLOR = (255, 215, 120)
REWARD_COLOR = (140, 255, 210)


class PosterDetailPanel:
    """Shows additional information for the currently selected poster."""

    def __init__(self, rect: pygame.Rect):
        self.rect = pygame.Rect(rect)
        self.padding = int(18 * UI_SCALE)
        self.title_font = get_font(int(60 * UI_SCALE))
        self.subtitle_font = get_font(int(32 * UI_SCALE))
        self.body_font = get_font(int(28 * UI_SCALE))
        self.tag_font = get_font(int(28 * UI_SCALE))
        self.entry: Optional[dict] = None
        self.visible = False
        self._preview_surface: Optional[pygame.Surface] = None

    def set_entry(self, entry: dict):
        """Display the provided entry."""
        self.entry = entry or {}
        self.visible = bool(entry)
        self._preview_surface = self._load_preview(entry.get("preview")) if entry else None

    def hide(self):
        self.entry = None
        self.visible = False
        self._preview_surface = None

    def draw(self, surface: pygame.Surface):
        if not self.visible or not self.entry:
            return

        panel = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel.fill(BACKGROUND_COLOR)

        if self._preview_surface:
            preview_rect = self._preview_surface.get_rect()
            preview_rect.topleft = (self.padding, self.padding)
            panel.blit(self._preview_surface, preview_rect)
            text_offset_y = preview_rect.bottom + self.padding
        else:
            text_offset_y = self.padding

        title = self.entry.get("title", "")
        if title:
            title_surface = self.title_font.render(title, True, TITLE_COLOR)
            panel.blit(title_surface, (self.padding, text_offset_y))
            text_offset_y += title_surface.get_height() + int(10 * UI_SCALE)

        subtitle = self.entry.get("subtitle") or self.entry.get("difficulty")
        if subtitle:
            subtitle_surf = self.subtitle_font.render(subtitle, True, SUBTITLE_COLOR)
            panel.blit(subtitle_surf, (self.padding, text_offset_y))
            text_offset_y += subtitle_surf.get_height() + int(10 * UI_SCALE)

        tags = self._collect_tags()
        if tags:
            tag_x = self.padding
            tag_height = self.tag_font.get_height() + int(8 * UI_SCALE)
            for tag in tags:
                tag_surface = pygame.Surface((self.tag_font.size(tag)[0] + int(20 * UI_SCALE), tag_height), pygame.SRCALPHA)
                tag_surface.fill(TAG_BG)
                text = self.tag_font.render(tag, True, TAG_COLOR)
                text_rect = text.get_rect(center=(tag_surface.get_width() // 2, tag_surface.get_height() // 2))
                tag_surface.blit(text, text_rect)
                panel.blit(tag_surface, (tag_x, text_offset_y))
                tag_x += tag_surface.get_width() + int(12 * UI_SCALE)
            text_offset_y += tag_height + int(12 * UI_SCALE)

        description = self.entry.get("description")
        if description:
            text_offset_y = self._draw_multiline(panel, description, text_offset_y)

        rewards = self.entry.get("rewards")
        if rewards:
            reward_text = "奖励：" + "、".join(rewards)
            reward_surf = self.body_font.render(reward_text, True, REWARD_COLOR)
            panel.blit(reward_surf, (self.padding, text_offset_y))

        pygame.draw.rect(panel, BORDER_COLOR, panel.get_rect(), width=3, border_radius=18)
        surface.blit(panel, self.rect.topleft)

    def _draw_multiline(self, panel: pygame.Surface, description: str, start_y: int) -> int:
        use_space = " " in description
        words = description.split(" ") if use_space else list(description)
        max_width = self.rect.width - self.padding * 2
        lines: List[str] = []
        line = ""
        for word in words:
            separator = " " if use_space and line else ""
            proposal = f"{line}{separator}{word}" if line else word
            width, _ = self.body_font.size(proposal)
            if width <= max_width:
                line = proposal
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)

        y = start_y
        for line_text in lines:
            surf = self.body_font.render(line_text, True, BODY_COLOR)
            panel.blit(surf, (self.padding, y))
            y += surf.get_height() + int(6 * UI_SCALE)
        return y + int(4 * UI_SCALE)

    def _collect_tags(self) -> List[str]:
        tags: List[str] = []
        recommended = self.entry.get("recommended")
        if recommended:
            tags.append(f"推荐战力 {recommended}")
        difficulty = self.entry.get("difficulty")
        if difficulty:
            tags.append(f"难度 {difficulty}")
        extra = self.entry.get("tags")
        if extra:
            tags.extend(extra)
        return tags

    def _load_preview(self, path: Optional[str]):
        if not path or not os.path.exists(path):
            return None
        try:
            surf = pygame.image.load(path).convert_alpha()
        except Exception:
            return None
        preview_width = self.rect.width - self.padding * 2
        preview_height = int(self.rect.height * 0.35)
        return pygame.transform.smoothscale(surf, (preview_width, preview_height))
