"""ActivityPosterUI - 活动海报轮播控件"""

# 构造示例：
# poster_ui = PosterUI()
# poster_ui.on_click = lambda idx, path: switch_to_scene("...")

# 在 scene.update(dt):
# poster_ui.update(dt)

# 在 scene.handle_event(event):
# poster_ui.handle_event(event)

# 在 scene.draw:
# poster_ui.draw(screen, (100, 80)) # 绘制到指定位置

import os
import pygame
from typing import Callable, List, Optional, Tuple
from config import WINDOW_WIDTH, WINDOW_HEIGHT

# 路径
posters_dir = os.path.join("assets", "poster")
poster_width = int(WINDOW_WIDTH * 0.35)
poster_height = int(WINDOW_HEIGHT * 0.30)

# 视觉常量
DEFAULT_BG_COLOR = (30, 30, 30, 200) # 半透明背景
DEFAULT_BORDER_COLOR = (200, 200, 0) # 金色边框
DEFAULT_BORDER_WIDTH = 8 # 边框宽度
DEFAULT_BORDER_RADIUS = 24 # 边框圆角半径
DEFAULT_PADDING = 8 # 内边距
DEFAULT_PLACEHOLDER_COLOR = (90, 90, 90) # 占位图背景色

DEFAULT_INTERVAL = 5.0  # 轮播间隔
AUTOPLAY = True  # 是否自动播放
DEFAULT_ANIM_DURATION = 0.7  # 切换动画时长

class PosterUI:
    def __init__(self):
        self.width, self.height = (poster_width, poster_height)
        self.bg_color = DEFAULT_BG_COLOR
        self.border_color = DEFAULT_BORDER_COLOR
        self.border_width = DEFAULT_BORDER_WIDTH
        self.border_radius = DEFAULT_BORDER_RADIUS
        self.padding = DEFAULT_PADDING
        self.interval = DEFAULT_INTERVAL
        self.autoplay = AUTOPLAY

        # 轮播控制
        self._timer = 0.0
        self.current_index = 0
        self._playing = self.autoplay

        # 切换动画相关
        self._is_animating = False
        self._anim_progress = 0.0  # 0.0 -> 1.0
        self._anim_duration = DEFAULT_ANIM_DURATION
        self._anim_from = 0
        self._anim_to = 0
        self._anim_direction = 1  # 1 = next (left), -1 = prev (right)

        # 回调，当用户点击海报时触发 (index, path)
        self.on_click: Optional[Callable[[int, Optional[str]], None]] = None
        # 坐标
        self._topleft = (0, 0)
        self._rect = pygame.Rect(0, 0, self.width, self.height)

        # poster 数据
        self.poster_paths: List[str] = []
        self._poster_raw_surfs: List[Optional[pygame.Surface]] = []
        self._prepared_posters: List[Optional[pygame.Surface]] = []
        self._placeholder_surface: Optional[pygame.Surface] = None
        self._frame_surface: Optional[pygame.Surface] = None

        self._inner_x = 0
        self._inner_y = 0
        self._inner_w = 2
        self._inner_h = 2
        self._recompute_inner_area()

        self.set_posters() # 从assets/poster目录读取海报

    # ---------- poster 管理 ----------
    def _recompute_inner_area(self):
        border_total = self.border_width + self.padding
        self._inner_x = border_total
        self._inner_y = border_total
        self._inner_w = max(2, self.width - 2 * border_total)
        self._inner_h = max(2, self.height - 2 * border_total)
        self._placeholder_surface = None
        self._frame_surface = None
        if getattr(self, "_poster_raw_surfs", None):
            self._prepare_poster_cache()

    def set_posters(self):
        import glob
        import re

        found = []
        if os.path.isdir(posters_dir):
            exts = ("png", "jpg", "jpeg", "webp")
            for ext in exts:
                found.extend(glob.glob(os.path.join(posters_dir, f"poster*.{ext}")))

            # 去重并按文件名中数字排序
            def _extract_index(p):
                name = os.path.basename(p)
                m = re.search(r"poster0*([0-9]+)", name, re.IGNORECASE)
                if m:
                    return int(m.group(1))
                return float("inf"), name

            # 排序时先按数字，再按文件名确保稳定顺序
            found = sorted(found, key=lambda p: (_extract_index(p) if isinstance(_extract_index(p), int) else _extract_index(p)))

        self.poster_paths = found

        self._poster_raw_surfs = []
        for p in self.poster_paths:
            self._poster_raw_surfs.append(self._try_load_image(p))
        self._prepare_poster_cache()

        # 重置索引与计时器
        self.current_index = 0
        self._timer = 0.0

    def clear_posters(self):
        self.poster_paths = []
        self._poster_raw_surfs = []
        self._prepared_posters = []
        self.current_index = 0
        self._timer = 0.0

    # ---------- loading ----------
    def _try_load_image(self, path: str) -> Optional[pygame.Surface]:
        """加载图片"""
        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
            return surf

        return None

    def _prepare_poster_cache(self):
        self._prepared_posters = []
        if not self.poster_paths:
            return
        for surf in self._poster_raw_surfs:
            self._prepared_posters.append(self._prepare_surface(surf))

    def _prepare_surface(self, surf: Optional[pygame.Surface]) -> pygame.Surface:
        if not surf:
            return self._get_placeholder_surface()
        try:
            return self._scale_and_crop_to_fit(surf, (self._inner_w, self._inner_h))
        except Exception:
            return self._get_placeholder_surface()

    def _get_prepared_surface(self, index: int) -> pygame.Surface:
        if not self._prepared_posters:
            return self._get_placeholder_surface()
        if 0 <= index < len(self._prepared_posters):
            surf = self._prepared_posters[index]
            if surf:
                return surf
        return self._get_placeholder_surface()

    def _get_placeholder_surface(self) -> pygame.Surface:
        if self._placeholder_surface is None:
            placeholder = pygame.Surface((self._inner_w, self._inner_h), pygame.SRCALPHA)
            placeholder.fill(DEFAULT_PLACEHOLDER_COLOR)
            pygame.draw.rect(
                placeholder,
                (140, 140, 140),
                placeholder.get_rect(),
                2,
                border_radius=max(4, self.border_radius // 2)
            )
            self._placeholder_surface = placeholder
        return self._placeholder_surface

    def _create_frame_surface(self) -> pygame.Surface:
        frame = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        if self.bg_color:
            pygame.draw.rect(frame, self.bg_color, frame.get_rect(), border_radius=self.border_radius)
        if self.border_width > 0:
            pygame.draw.rect(frame, self.border_color, frame.get_rect(), width=self.border_width, border_radius=self.border_radius)
        return frame

    # ---------- interaction ----------
    def handle_event(self, event: pygame.event.Event):
        # 鼠标点击触发on_click回调
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if self._rect.collidepoint(mx, my):
                # 触发回调（提供当前 index ）
                idx = self.current_index if self.poster_paths else -1
                if callable(self.on_click):
                    self.on_click(idx)

    # ---------- update / draw ----------
    def update(self, dt: float):
        # 自动轮播计时（在未动画时累加）
        if not self.poster_paths or self.interval <= 0:
            return

        if not self._is_animating:
            if self._playing:
                self._timer += dt
                if self._timer >= self.interval:
                    steps = int(self._timer // self.interval)
                    # 只做一次步进（多步合并）
                    self._timer -= steps * self.interval
                    # 触发一次 next（忽略 steps>1 的额外步）
                    self.next()
        else:
            # 动画进行时更新进度
            self._anim_progress += dt / max(1e-6, self._anim_duration)
            if self._anim_progress >= 1.0:
                # 完成动画：设置新索引，结束动画
                self.current_index = self._anim_to
                self._is_animating = False
                self._anim_progress = 0.0
                self._timer = 0.0  # 重置轮播计时器

    def draw(self, surface: pygame.Surface, topleft: Tuple[int, int]):
        self._topleft = topleft
        x, y = topleft
        self._rect = pygame.Rect(x, y, self.width, self.height)
        if self._frame_surface is None:
            self._frame_surface = self._create_frame_surface()
        surface.blit(self._frame_surface, (x, y))

        inner_x = self._inner_x
        inner_y = self._inner_y
        inner_w = self._inner_w
        inner_h = self._inner_h
        poster_layer = pygame.Surface((inner_w, inner_h), pygame.SRCALPHA)

        if self.poster_paths and self._prepared_posters:
            cur_idx = self.current_index
            to_idx = self._anim_to if self._is_animating else cur_idx
            cur_draw = self._get_prepared_surface(cur_idx)
            to_draw = self._get_prepared_surface(to_idx)

            if not self._is_animating:
                poster_layer.blit(cur_draw, (0, 0))
            else:
                p = max(0.0, min(1.0, self._anim_progress))
                direction = self._anim_direction
                if direction >= 0:
                    cur_x = -int(p * inner_w)
                    to_x = inner_w - int(p * inner_w)
                else:
                    cur_x = int(p * inner_w)
                    to_x = -inner_w + int(p * inner_w)

                poster_layer.blit(to_draw, (to_x, 0))
                poster_layer.blit(cur_draw, (cur_x, 0))
        else:
            poster_layer.blit(self._get_placeholder_surface(), (0, 0))

        surface.blit(poster_layer, (x + inner_x, y + inner_y))

    # ---------- playback轮播控制 ----------
    def play(self):
        self._playing = True

    def pause(self):
        self._playing = False

    def start_animation(self, to_index: int, direction: int = 1):
        """开始滑动动画到 to_index，direction 1 表示向左（next），-1 表示向右（prev）。"""
        if not self.poster_paths:
            return
        to_index = to_index % len(self.poster_paths)
        if to_index == self.current_index:
            return
        # 如果已经在动画中，忽略新的请求以避免竞态
        if self._is_animating:
            return
        self._is_animating = True
        self._anim_progress = 0.0
        self._anim_from = self.current_index
        self._anim_to = to_index
        self._anim_direction = 1 if direction >= 0 else -1

    def next(self):
        if not self.poster_paths:
            return
        target = (self.current_index + 1) % len(self.poster_paths)
        self.start_animation(target, direction=1)
        self._timer = 0.0

    def prev(self):
        if not self.poster_paths:
            return
        target = (self.current_index - 1) % len(self.poster_paths)
        self.start_animation(target, direction=-1)
        self._timer = 0.0

    # ---------- helpers ----------
    def _scale_and_crop_to_fit(self, surf: pygame.Surface, target_size: Tuple[int, int]) -> pygame.Surface:
        """按cover模式缩放并裁剪图像以填充目标尺寸"""
        tw, th = target_size
        sw, sh = surf.get_width(), surf.get_height()
        if sw == 0 or sh == 0 or tw == 0 or th == 0:
            return pygame.Surface((tw, th), pygame.SRCALPHA)

        scale = max(tw / sw, th / sh)
        new_w = int(sw * scale)
        new_h = int(sh * scale)
        try:
            scaled = pygame.transform.smoothscale(surf, (new_w, new_h))
        except Exception:
            scaled = pygame.transform.scale(surf, (new_w, new_h))

        x = max(0, (new_w - tw) // 2)
        y = max(0, (new_h - th) // 2)
        cropped = scaled.subsurface((x, y, tw, th)).copy()
        return cropped

    def _blit_placeholder(self, target_surf: pygame.Surface, inner_rect: pygame.Rect):
        """绘制占位图和文字"""
        placeholder = pygame.Surface((inner_rect.width, inner_rect.height), pygame.SRCALPHA)
        placeholder.fill(DEFAULT_PLACEHOLDER_COLOR)
        pygame.draw.rect(placeholder, (140, 140, 140), placeholder.get_rect(), 2, border_radius=max(4, self.border_radius // 2))
        target_surf.blit(placeholder, (inner_rect.x, inner_rect.y))

    # ---------- properties for styling (expose for outside changes) ----------
    @property
    def border_radius(self):
        return self._border_radius if hasattr(self, "_border_radius") else DEFAULT_BORDER_RADIUS

    @border_radius.setter
    def border_radius(self, v):
        self._border_radius = max(0, int(v))

    @property
    def border_color(self):
        return self._border_color if hasattr(self, "_border_color") else DEFAULT_BORDER_COLOR

    @border_color.setter
    def border_color(self, v):
        self._border_color = v

    @property
    def border_width(self):
        return self._border_width if hasattr(self, "_border_width") else DEFAULT_BORDER_WIDTH

    @border_width.setter
    def border_width(self, v):
        self._border_width = max(0, int(v))
