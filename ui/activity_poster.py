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
        self._poster_surfs: List[Optional[pygame.Surface]] = []

        self.set_posters() # 从assets/poster目录读取海报

    # ---------- poster 管理 ----------
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

        # 初始化报缓存
        self._poster_surfs = [None] * len(self.poster_paths)
        for i, p in enumerate(self.poster_paths):
            self._poster_surfs[i] = self._try_load_image(p)

        # 重置索引与计时器
        self.current_index = 0
        self._timer = 0.0

    def clear_posters(self):
        self.poster_paths = []
        self._poster_surfs = []
        self.current_index = 0
        self._timer = 0.0

    # ---------- loading ----------
    def _try_load_image(self, path: str) -> Optional[pygame.Surface]:
        """加载图片"""
        if os.path.exists(path):
            surf = pygame.image.load(path).convert_alpha()
            return surf

        return None

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

        # 目标盒子surface
        box_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        box_surf.fill((0, 0, 0, 0))  # 先全透明

        # 绘制带圆角的背景矩形
        rect_inner = pygame.Rect(0, 0, self.width, self.height)
        if self.bg_color:
            pygame.draw.rect(box_surf, self.bg_color, rect_inner, border_radius=self.border_radius)
        
        # 计算可用内部区域
        inner_x = self.border_width + self.padding
        inner_y = self.border_width + self.padding
        inner_w = max(2, self.width - 2 * (self.border_width + self.padding))
        inner_h = max(2, self.height - 2 * (self.border_width + self.padding))

        # 绘制海报
        if self.poster_paths and self._poster_surfs:
            # 获取当前与目标图片 surface
            cur_idx = self.current_index
            to_idx = self._anim_to if self._is_animating else cur_idx

            cur_surf = self._poster_surfs[cur_idx] if cur_idx < len(self._poster_surfs) else None
            if cur_surf is None and cur_idx < len(self.poster_paths):
                cur_surf = self._try_load_image(self.poster_paths[cur_idx])
                self._poster_surfs[cur_idx] = cur_surf

            to_surf = self._poster_surfs[to_idx] if to_idx < len(self._poster_surfs) else None
            if to_surf is None and to_idx < len(self.poster_paths):
                to_surf = self._try_load_image(self.poster_paths[to_idx])
                self._poster_surfs[to_idx] = to_surf

            # 辅助绘制函数
            def _get_draw_surf(s):
                if s:
                    return self._scale_and_crop_to_fit(s, (inner_w, inner_h))
                else:
                    # 占位图
                    ph = pygame.Surface((inner_w, inner_h), pygame.SRCALPHA)
                    ph.fill(DEFAULT_PLACEHOLDER_COLOR)
                    return ph

            if not self._is_animating:
                draw_surf = _get_draw_surf(cur_surf)
                dx = inner_x + (inner_w - draw_surf.get_width()) // 2
                dy = inner_y + (inner_h - draw_surf.get_height()) // 2
                box_surf.blit(draw_surf, (dx, dy))
            else:
                # 计算动画偏移（基于 inner_w）
                p = max(0.0, min(1.0, self._anim_progress))
                dir = self._anim_direction
                cur_draw = _get_draw_surf(cur_surf)
                to_draw = _get_draw_surf(to_surf)
                if dir >= 0:
                    cur_x = inner_x - int(p * inner_w)
                    to_x = inner_x + inner_w - int(p * inner_w)
                else:
                    cur_x = inner_x + int(p * inner_w)
                    to_x = inner_x - inner_w + int(p * inner_w)

                cur_y = inner_y + (inner_h - cur_draw.get_height()) // 2
                to_y = inner_y + (inner_h - to_draw.get_height()) // 2
                box_surf.blit(to_draw, (to_x, to_y))
                box_surf.blit(cur_draw, (cur_x, cur_y))
        else:
            # 没有海报时绘制占位
            placeholder = pygame.Surface((inner_w, inner_h), pygame.SRCALPHA)
            placeholder.fill(DEFAULT_PLACEHOLDER_COLOR)
            pygame.draw.rect(placeholder, (140, 140, 140), placeholder.get_rect(), 2, border_radius=max(4, self.border_radius // 2))
            box_surf.blit(placeholder, (inner_x, inner_y))

        # 绘制边框（圆角）
        if self.border_width > 0:
            pygame.draw.rect(box_surf, self.border_color, rect_inner, width=self.border_width, border_radius=self.border_radius)

        # 绘制到主 surface
        surface.blit(box_surf, (x, y))

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
