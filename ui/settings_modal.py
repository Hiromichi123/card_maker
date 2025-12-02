"""主菜单设置弹窗"""
import pygame
from typing import Callable

from config import UI_SCALE, WINDOW_WIDTH, WINDOW_HEIGHT, get_font
from ui.button import Button
from ui.panel import Panel

class SettingsModal:
    """设置弹窗，允许在主菜单中调整 UI 缩放"""
    def __init__(
        self,
        initial_scale: float,
        on_apply: Callable[[float], None],
        on_cancel: Callable[[], None],
        min_scale: float = 0.6,
        max_scale: float = 1.4,
    ) -> None:
        self.on_apply = on_apply
        self.on_cancel = on_cancel
        self.min_scale = min_scale
        self.max_scale = max_scale
        self.scale_value = self._clamp(initial_scale)
        self.dragging = False

        self.overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 160))

        panel_width = int(640 * UI_SCALE)
        panel_height = int(380 * UI_SCALE)
        self.panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        self.panel_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        self.panel = Panel(self.panel_rect.x, self.panel_rect.y, panel_width, panel_height, alpha=235)

        self.title_font = get_font(max(24, int(50 * UI_SCALE)))
        self.text_font = get_font(max(18, int(32 * UI_SCALE)))
        self.value_font = get_font(max(20, int(44 * UI_SCALE)))

        slider_width = int(380 * UI_SCALE)
        slider_height = max(6, int(8 * UI_SCALE))
        slider_x = self.panel_rect.centerx - slider_width // 2
        slider_y = self.panel_rect.y + int(170 * UI_SCALE)
        self.slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
        self.knob_radius = max(12, int(14 * UI_SCALE))

        step_width = int(52 * UI_SCALE)
        step_height = int(44 * UI_SCALE)
        margin = int(20 * UI_SCALE)
        step_y = self.slider_rect.centery - step_height // 2
        minus_x = self.slider_rect.left - step_width - margin
        plus_x = self.slider_rect.right + margin

        self.minus_button = Button(
            minus_x,
            step_y,
            step_width,
            step_height,
            "-",
            color=(70, 70, 90),
            hover_color=(120, 120, 160),
            font_size=36,
            on_click=lambda: self.adjust_value(-0.05),
        )
        self.plus_button = Button(
            plus_x,
            step_y,
            step_width,
            step_height,
            "+",
            color=(70, 70, 90),
            hover_color=(120, 120, 160),
            font_size=36,
            on_click=lambda: self.adjust_value(0.05),
        )

        button_width = int(170 * UI_SCALE)
        button_height = int(56 * UI_SCALE)
        button_y = self.panel_rect.bottom - int(90 * UI_SCALE)
        gap = int(30 * UI_SCALE)
        self.confirm_button = Button(
            self.panel_rect.centerx - button_width - gap // 2,
            button_y,
            button_width,
            button_height,
            "应用",
            color=(100, 170, 120),
            hover_color=(140, 210, 150),
            on_click=self._apply_clicked,
        )
        self.cancel_button = Button(
            self.panel_rect.centerx + gap // 2,
            button_y,
            button_width,
            button_height,
            "取消",
            color=(170, 110, 110),
            hover_color=(210, 150, 150),
            on_click=self._cancel_clicked,
        )

        self.buttons = [
            self.minus_button,
            self.plus_button,
            self.confirm_button,
            self.cancel_button,
        ]
        
        # Text cache for performance
        self._text_cache = {}
        self._rebuild_text_cache()
    
    def _rebuild_text_cache(self):
        """Rebuild cached text surfaces"""
        self._text_cache['title'] = self.title_font.render("设置", True, (255, 255, 255))
        self._text_cache['desc'] = self.text_font.render("调整 UI 缩放 (0.6 - 1.4)", True, (230, 230, 230))
        self._text_cache['hint'] = self.text_font.render("确认后将重新构建UI", True, (180, 180, 200))

    def _clamp(self, value: float) -> float:
        return max(self.min_scale, min(self.max_scale, value))

    def adjust_value(self, delta: float) -> None:
        self.scale_value = round(self._clamp(self.scale_value + delta), 2)

    def _ratio(self) -> float:
        span = self.max_scale - self.min_scale
        if span <= 0:
            return 0.0
        return (self.scale_value - self.min_scale) / span

    def _pos_from_value(self) -> int:
        return int(self.slider_rect.left + self._ratio() * self.slider_rect.width)

    def _update_value_from_pos(self, pos_x: int) -> None:
        ratio = (pos_x - self.slider_rect.left) / max(1, self.slider_rect.width)
        ratio = max(0.0, min(1.0, ratio))
        value = self.min_scale + ratio * (self.max_scale - self.min_scale)
        self.scale_value = round(value, 2)

    def _apply_clicked(self) -> None:
        if self.on_apply:
            self.on_apply(self.scale_value)

    def _cancel_clicked(self) -> None:
        if self.on_cancel:
            self.on_cancel()

    def handle_event(self, event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._cancel_clicked()
            return True

        handled = False
        for button in self.buttons:
            if button.handle_event(event):
                handled = True
        if handled:
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            knob_pos = pygame.Rect(0, 0, self.knob_radius * 2, self.knob_radius * 2)
            knob_pos.center = (self._pos_from_value(), self.slider_rect.centery)
            if knob_pos.collidepoint(event.pos) or self.slider_rect.collidepoint(event.pos):
                self.dragging = True
                self._update_value_from_pos(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._update_value_from_pos(event.pos[0])
            return True
        return False

    def update(self, _dt: float) -> None:
        pass

    def draw(self, screen) -> None:
        screen.blit(self.overlay, (0, 0))
        self.panel.draw(screen)

        # 使用缓存文字
        title_surface = self._text_cache['title']
        title_rect = title_surface.get_rect(center=(self.panel_rect.centerx, self.panel_rect.y + int(45 * UI_SCALE)))
        screen.blit(title_surface, title_rect)

        desc_surface = self._text_cache['desc']
        desc_rect = desc_surface.get_rect(center=(self.panel_rect.centerx, self.panel_rect.y + int(95 * UI_SCALE)))
        screen.blit(desc_surface, desc_rect)

        ratio = self._ratio()
        fill_rect = pygame.Rect(self.slider_rect)
        fill_rect.width = max(2, int(self.slider_rect.width * ratio))
        pygame.draw.rect(screen, (60, 60, 80), self.slider_rect, border_radius=self.slider_rect.height // 2)
        pygame.draw.rect(screen, (180, 200, 255), fill_rect, border_radius=self.slider_rect.height // 2)

        knob_pos = (self._pos_from_value(), self.slider_rect.centery)
        pygame.draw.circle(screen, (255, 215, 0), knob_pos, self.knob_radius)
        pygame.draw.circle(screen, (60, 60, 60), knob_pos, self.knob_radius, max(2, int(2 * UI_SCALE)))

        # 值文字 - 按需更新缓存
        value_key = f"value_{self.scale_value:.2f}"
        if value_key not in self._text_cache:
            self._text_cache[value_key] = self.value_font.render(f"{self.scale_value:.2f}x", True, (255, 255, 255))
        value_surface = self._text_cache[value_key]
        value_rect = value_surface.get_rect(center=(self.panel_rect.centerx, self.slider_rect.bottom + int(40 * UI_SCALE)))
        screen.blit(value_surface, value_rect)

        hint_surface = self._text_cache['hint']
        hint_rect = hint_surface.get_rect(center=(self.panel_rect.centerx, value_rect.bottom + int(30 * UI_SCALE)))
        screen.blit(hint_surface, hint_rect)

        for button in self.buttons:
            button.draw(screen)
