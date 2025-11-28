"""担任战役 - 章节地图场景"""
from __future__ import annotations

import math
import os
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, UI_SCALE, get_font
from scenes.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.map_poster import MapPoster
from ui.poster_detail_panel import PosterDetailPanel
from ui.button import Button
from utils.scene_payload import pop_payload, set_payload
from game.chapter_config import CHAPTER_LOOKUP, WORLD_CHAPTERS

POSTER_WIDTH = int(540 * UI_SCALE)
POSTER_HEIGHT = int(360 * UI_SCALE)
MAX_COLUMNS = 4
ENEMY_DECK_ROOT = os.path.join("data", "deck", "enemy_deck", "single_player")

class ChapterMapScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, "bg/chapter_1_map")
        self.title_font = get_font(int(72 * UI_SCALE))
        self.subtitle_font = get_font(int(32 * UI_SCALE))
        self.posters: list[MapPoster] = []
        self.current_chapter_id = WORLD_CHAPTERS[0]["id"]
        self.chapter_data = CHAPTER_LOOKUP[self.current_chapter_id]
        self.status_message = "选择一个关卡开始作战"
        self.status_font = get_font(int(40 * UI_SCALE))
        detail_rect = pygame.Rect(
            int(WINDOW_WIDTH * 0.72),
            int(WINDOW_HEIGHT * 0.18),
            int(WINDOW_WIDTH * 0.24),
            int(WINDOW_HEIGHT * 0.68),
        )
        self.detail_panel = PosterDetailPanel(detail_rect)
        self.selected_stage_id: str | None = None
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
            on_click=lambda: self.switch_to("world_map"),
        )
        self._build_posters()
        self._sync_stage_selection(auto_fill=True)

    def enter(self):
        super().enter()
        payload = pop_payload("chapter_map") or {}
        chapter_id = payload.get("chapter_id") or self.current_chapter_id
        if chapter_id not in CHAPTER_LOOKUP:
            chapter_id = WORLD_CHAPTERS[0]["id"]
        self.current_chapter_id = chapter_id
        self.chapter_data = CHAPTER_LOOKUP[chapter_id]
        self.selected_stage_id = None
        self.background = ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, self.chapter_data.get("bg_type", "bg/world_map"))
        self._build_posters()
        self._sync_stage_selection(auto_fill=True)
        self._update_detail_panel()

    def _build_posters(self):
        self.posters.clear()
        stages = self.chapter_data.get("stages", [])
        if not stages:
            return
        columns = min(MAX_COLUMNS, max(1, math.ceil(len(stages) / 2)))
        rows = math.ceil(len(stages) / columns)
        if rows < 1:
            rows = 1
        usable_width = int(WINDOW_WIDTH * 0.62)
        left_margin = int(WINDOW_WIDTH * 0.07)
        vertical_spacing = int(WINDOW_HEIGHT * 0.3)
        base_y = int(WINDOW_HEIGHT * 0.35)
        for idx, stage in enumerate(stages):
            row = idx // columns
            col = idx % columns
            col_ratio = (col + 0.5) / columns
            center_x = left_margin + int(usable_width * col_ratio)
            center_y = base_y + row * vertical_spacing
            rect = pygame.Rect(0, 0, POSTER_WIDTH, POSTER_HEIGHT)
            rect.center = (center_x, center_y)
            poster = MapPoster(
                rect,
                image_path=stage.get("poster"),
                label=f"{stage.get('id')} {stage.get('name')}",
                on_click=self._handle_stage_click,
                payload=stage.get("id"),
            )
            self.posters.append(poster)
        self._sync_stage_selection(auto_fill=not self.selected_stage_id)

    def _handle_stage_click(self, stage_id: str):
        if not stage_id:
            return
        if self.selected_stage_id == stage_id:
            self._enter_stage(stage_id)
            return
        self.selected_stage_id = stage_id
        self._sync_stage_selection()
        self._update_detail_panel()

    def _sync_stage_selection(self, auto_fill: bool = False):
        for poster in self.posters:
            poster.set_selected(poster.payload == self.selected_stage_id)
        if auto_fill and not self.selected_stage_id and self.posters:
            self.selected_stage_id = self.posters[0].payload
            for poster in self.posters:
                poster.set_selected(poster.payload == self.selected_stage_id)
            self._update_detail_panel()

    def _update_detail_panel(self):
        if not self.selected_stage_id:
            self.detail_panel.hide()
            return
        stages = self.chapter_data.get("stages", [])
        stage = next((s for s in stages if s.get("id") == self.selected_stage_id), None)
        if not stage:
            self.detail_panel.hide()
            return
        index = stages.index(stage)
        recommended = stage.get("recommended_power") or f"{1500 + index * 120}+"
        difficulty_lane = ["普通", "困难", "噩梦"]
        difficulty = stage.get("difficulty") or difficulty_lane[min(index // 2, len(difficulty_lane) - 1)]
        summary = stage.get("summary") or f"清除 {stage.get('name')} 的敌军，夺回章节点 {stage.get('id')}。"
        tags = ["精英巡逻"] if index % 2 == 1 else ["资源据点"]
        if index == len(stages) - 1:
            tags.append("BOSS")
        rewards = stage.get("rewards") or ["角色经验", "战利品宝箱"]
        entry = {
            "title": stage.get("name"),
            "subtitle": f"关卡 {stage.get('id')}",
            "description": summary,
            "recommended": recommended,
            "difficulty": difficulty,
            "rewards": rewards,
            "tags": tags,
            "preview": stage.get("poster"),
        }
        self.detail_panel.set_entry(entry)

    def _enter_stage(self, stage_id: str):
        stage = next((s for s in self.chapter_data.get("stages", []) if s.get("id") == stage_id), None)
        enemy_path = os.path.join(ENEMY_DECK_ROOT, f"{stage_id}.json")
        stage_name = stage.get("name") if stage else stage_id
        payload = {
            "stage_id": stage_id,
            "stage_name": stage_name,
            "chapter_id": self.current_chapter_id,
            "chapter_name": self.chapter_data.get("name"),
            "background": stage.get("poster") if stage else None,
            "enemy_deck": enemy_path,
        }
        set_payload("simple_battle", payload)
        self.status_message = f"前往 {stage_id} - {stage_name}"
        self.switch_to("simple_battle")

    def handle_event(self, event):
        super().handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("world_map")
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
        self._draw_status()
        self.detail_panel.draw(self.screen)
        self.back_button.draw(self.screen)

    def _draw_titles(self):
        title = self.title_font.render(self.chapter_data.get("name", "章节"), True, (255, 240, 200))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.12)))
        self.screen.blit(title, title_rect)
        subtitle = self.subtitle_font.render("选择关卡（ESC 返回世界地图）", True, (220, 220, 255))
        subtitle_rect = subtitle.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.2)))
        self.screen.blit(subtitle, subtitle_rect)

    def _draw_status(self):
        status = self.status_font.render(self.status_message, True, (255, 255, 255))
        status_rect = status.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.9)))
        self.screen.blit(status, status_rect)
