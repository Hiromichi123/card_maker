"""Simple clickable poster used on map scenes."""
from __future__ import annotations

import os
import pygame
from typing import Callable, Optional
from config import get_font, UI_SCALE, COLORS

PANEL_COLOR = (20, 20, 35, 210)
BORDER_COLOR = (255, 215, 120)
HOVER_COLOR = (255, 255, 255)
SELECTED_COLOR = (255, 200, 40)
SELECTED_GLOW = (255, 220, 120, 90)
BORDER_WIDTH = 4
LABEL_COLOR = (245, 245, 245)
LABEL_BG = (0, 0, 0, 160)

class MapPoster:
    """Static poster with optional callback."""

    def __init__(
        self,
        rect: pygame.Rect,
        image_path: Optional[str] = None,
        label: str | None = None,
        on_click: Optional[Callable[[str], None]] = None,
        payload: str | None = None,
    ):
        self.rect = rect
        self.image_path = image_path
        self.label = label or ""
        self.on_click = on_click
        self.payload = payload
        self.hovered = False
        self.selected = False
        self._font = get_font(int(34 * UI_SCALE))
        self._image = self._load_image(image_path)
        self._panel_surface = self._build_panel_surface()
        self._glow_surface = self._build_glow_surface()

    def _load_image(self, path: Optional[str]):
        if not path:
            return None
        if os.path.exists(path):
            try:
                surf = pygame.image.load(path).convert_alpha()
            except Exception:
                return None
            return pygame.transform.smoothscale(surf, (self.rect.width, self.rect.height))
        return None

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos) and callable(self.on_click):
                self.on_click(self.payload or "")

    def draw(self, surface: pygame.Surface):
        if self._panel_surface:
            surface.blit(self._panel_surface, self.rect.topleft)
        if self.selected and self._glow_surface:
            surface.blit(self._glow_surface, (self.rect.x - 10, self.rect.y - 10), special_flags=pygame.BLEND_ADD)

        border_color = SELECTED_COLOR if self.selected else (HOVER_COLOR if self.hovered else BORDER_COLOR)
        pygame.draw.rect(surface, border_color, self.rect, BORDER_WIDTH, border_radius=16)

    def set_selected(self, value: bool):
        self.selected = value

    def _build_panel_surface(self):
        panel = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        panel.fill(PANEL_COLOR)
        if self._image:
            panel.blit(self._image, (0, 0))
        else:
            placeholder = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            placeholder.fill((60, 60, 70, 200))
            pygame.draw.rect(placeholder, COLORS.get("A", (180, 180, 180)), placeholder.get_rect(), 4)
            panel.blit(placeholder, (0, 0))

        if self.label:
            label_height = int(self.rect.height * 0.18)
            label_rect = pygame.Rect(0, self.rect.height - label_height, self.rect.width, label_height)
            label_bg = pygame.Surface((label_rect.width, label_rect.height), pygame.SRCALPHA)
            label_bg.fill(LABEL_BG)
            panel.blit(label_bg, label_rect.topleft)

            text_surface = self._font.render(self.label, True, LABEL_COLOR)
            text_rect = text_surface.get_rect(center=label_rect.center)
            panel.blit(text_surface, (text_rect.x - label_rect.x, text_rect.y - label_rect.y))
        return panel

    def _build_glow_surface(self):
        glow = pygame.Surface((self.rect.width + 20, self.rect.height + 20), pygame.SRCALPHA)
        inner_rect = glow.get_rect()
        border_thickness = max(4, BORDER_WIDTH * 2)
        pygame.draw.rect(glow, SELECTED_GLOW, inner_rect, width=border_thickness, border_radius=24)
        return glow