"""单人战役 - 世界地图场景"""
from __future__ import annotations

import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, UI_SCALE, get_font
from scenes.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.map_poster import MapPoster
from ui.poster_detail_panel import PosterDetailPanel
from ui.button import Button
from utils.scene_payload import set_payload
from game.chapter_config import WORLD_CHAPTERS

TITLE_Y = int(WINDOW_HEIGHT * 0.15)
POSTER_WIDTH = int(540 * UI_SCALE)
POSTER_HEIGHT = int(360 * UI_SCALE)

class WorldMapScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "bg/world_map")
        self.title_font = get_font(int(100 * UI_SCALE))
        self.subtitle_font = get_font(int(40 * UI_SCALE))
        self.posters: list[MapPoster] = []
        detail_width = int(WINDOW_WIDTH * 0.26)
        detail_height = int(WINDOW_HEIGHT * 0.68)
        detail_rect = pygame.Rect(
            int(WINDOW_WIDTH * 0.7),
            int(WINDOW_HEIGHT * 0.18),
            detail_width,
            detail_height,
        )
        self.detail_panel = PosterDetailPanel(detail_rect)
        self.selected_chapter_id: str | None = None
        btn_width = int(240 * UI_SCALE)
        btn_height = int(72 * UI_SCALE)
        btn_x = int(WINDOW_WIDTH * 0.04)
        btn_y = int(WINDOW_HEIGHT * 0.86)
        self.back_button = Button(
            btn_x,
            btn_y,
            btn_width,
            btn_height,
            "返回上一级",
            color=(90, 90, 90),
            hover_color=(130, 130, 130),
            font_size=42,
            on_click=lambda: self.switch_to("battle_menu"),
        )
        self._build_posters()

    def _build_posters(self):
        self.posters.clear()
        total = len(WORLD_CHAPTERS)
        usable_width = int(WINDOW_WIDTH * 0.6)
        left_margin = int(WINDOW_WIDTH * 0.15)
        center_y = int(WINDOW_HEIGHT * 0.6)
        for idx, chapter in enumerate(WORLD_CHAPTERS):
            rect = pygame.Rect(0, 0, POSTER_WIDTH, POSTER_HEIGHT)
            if total == 1:
                center_x = left_margin + usable_width // 2
            else:
                ratio = idx / (total - 1)
                center_x = left_margin + int(usable_width * ratio)
            rect.center = (center_x, center_y)
            poster = MapPoster(
                rect,
                image_path=chapter.get("poster"),
                label=chapter.get("name"),
                on_click=self._handle_chapter_click,
                payload=chapter.get("id"),
            )
            self.posters.append(poster)
        self._sync_selection()

    def _handle_chapter_click(self, chapter_id: str):
        if not chapter_id:
            return
        if self.selected_chapter_id == chapter_id:
            self._enter_chapter(chapter_id)
            return
        self.selected_chapter_id = chapter_id
        self._sync_selection()
        self._update_detail_panel()

    def _sync_selection(self):
        for poster in self.posters:
            poster.set_selected(poster.payload == self.selected_chapter_id)
        if not self.selected_chapter_id and self.posters:
            # 默认选中第一项便于提示
            self.selected_chapter_id = self.posters[0].payload
            for poster in self.posters:
                poster.set_selected(poster.payload == self.selected_chapter_id)
            self._update_detail_panel()

    def _update_detail_panel(self):
        chapter = next((c for c in WORLD_CHAPTERS if c.get("id") == self.selected_chapter_id), None)
        if not chapter:
            self.detail_panel.hide()
            return
        index = WORLD_CHAPTERS.index(chapter)
        recommended = f"{1200 + index * 350}+"
        difficulty_labels = ["简单", "普通", "困难", "噩梦", "传奇"]
        difficulty = difficulty_labels[min(index, len(difficulty_labels) - 1)]
        stage_preview = chapter.get("stages", [])
        first_stage = stage_preview[0]["name"] if stage_preview else "未知前哨"
        summary = chapter.get("summary") or f"{chapter.get('name')} 前线战役，先抵达 {first_stage} 稳固补给线。"
        entry = {
            "title": chapter.get("name"),
            "subtitle": "章节总览",
            "description": summary,
            "recommended": recommended,
            "difficulty": difficulty,
            "rewards": chapter.get("rewards") or ["指挥经验", "金币", "随机卡牌"] ,
            "preview": chapter.get("poster"),
        }
        self.detail_panel.set_entry(entry)

    def _enter_chapter(self, chapter_id: str):
        set_payload("chapter_map", {"chapter_id": chapter_id})
        self.switch_to("chapter_map")

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.switch_to("battle_menu")
        if event.type == pygame.MOUSEMOTION:
            self.background.update_mouse_position(event.pos)
        for poster in self.posters:
            poster.handle_event(event)
        self.back_button.handle_event(event)

    def update(self, dt):
        self.background.update(dt)

    def draw(self):
        self.background.draw(self.screen)
        self._draw_titles()
        for poster in self.posters:
            poster.draw(self.screen)
        self.detail_panel.draw(self.screen)
        self.back_button.draw(self.screen)

    def _draw_titles(self):
        title = self.title_font.render("世界地图", True, (255, 230, 180))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, TITLE_Y))
        self.screen.blit(title, title_rect)
        subtitle = self.subtitle_font.render("点击章节进入关卡", True, (220, 220, 255))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, TITLE_Y + int(60 * UI_SCALE)))
        self.screen.blit(subtitle, subtitle_rect)
