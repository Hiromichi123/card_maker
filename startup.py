"""
SplashScreen - 可复用的启动/加载过渡界面（Pygame）

功能
- 黑色背景 + 金色星星粒子背景（简单移动/闪烁）
- 中央白色高亮游戏/公司名称（支持字体路径或系统字体名）
- 可配置淡入、停留、淡出时长
- 在后台运行加载函数（线程），加载完成后淡出并调用回调切换场景
- 提供简单 API：start_loading(loader_func, on_finished) 或直接 set loader in constructor

注意与使用建议
- loader_func 会在后台线程运行。尽量在 loader_func 中避免调用 pygame 的图像/Surface API（pygame 在部分平台上不是线程安全的）。
  - 推荐：loader_func 做文件 I/O、解析、创建数据结构、读取 JSON、解压等耗时操作。
  - 若必须调用 pygame.image.load，请把它放到主线程或把文件路径缓存起来，在主场景 enter 时再加载为 Surface。
- 如果你的菜单加载涉及大量 pygame 操作，另一个策略是：
  - 在 loader_func 中只做非 pygame 的准备工作，然后在主线程中分批次（每帧）完成 pygame 层的资源创建（可用一个队列传回主线程）。
- 例子（集成到现有主循环）见模块末尾的注释示例。

类接口（主要）
- SplashScreen(width, height, title="Game", font_spec=None, fade_in=0.8, hold=0.6, fade_out=0.6, min_display=1.0, star_count=60)
- start_loading(loader_func, on_finished): 启动后台 loader（可多次调用）
- update(dt): 每帧调用
- draw(surface): 每帧绘制
- handle_event(event): 可用于响应 ESC 跳过（可选）

返回状态（属性）
- running: bool - splash 还在运行（淡出完成之前为 True）
- loading_done: bool - loader_func 已完成（但可能仍在淡出中）

"""

import os
import math
import time
import random
import threading
import pygame
from config import *
from typing import Callable, Optional, List, Tuple

# 时间常量
fade_in_default = 2.0
hold_default = 0.6
fade_out_default = 2.0
min_display_default = 1.0
# 星星数
star_count_default = 80

DEFAULT_BG_COLOR = (0, 0, 0)
STAR_COLOR = (230, 190, 90)  # 金色近似
TITLE_COLOR = (230, 190, 90) # 金色
SUBTITLE_COLOR = (200, 200, 200)

class _Star:
    """内部简单星体数据结构"""
    def __init__(self, w: int, h: int):
        self.w = w
        self.h = h
        self.reset()

    def reset(self):
        self.x = random.uniform(0, self.w)
        self.y = random.uniform(0, self.h)
        self.size = random.uniform(1.0, 3.6)
        self.speed = random.uniform(5.0, 30.0)  # vertical drift speed px/sec
        self.twinkle_phase = random.uniform(0.0, math.pi * 2.0)
        self.twinkle_speed = random.uniform(1.0, 3.0)
        self.h_speed = random.uniform(-8.0, 8.0)

    def update(self, dt: float):
        self.y += self.speed * dt * 0.02
        self.x += self.h_speed * dt * 0.02
        if self.y > self.h:
            self.y -= self.h
        if self.x < 0:
            self.x += self.w
        elif self.x > self.w:
            self.x -= self.w
        self.twinkle_phase += self.twinkle_speed * dt

    def alpha(self) -> int:
        a = 0.5 + 0.5 * math.sin(self.twinkle_phase)  # 0..1
        val = 60 + 195 * a * (self.size / 3.5)
        return max(0, min(255, int(val)))

class SplashScreen:
    def __init__(self):
        self.width = WINDOW_WIDTH
        self.height = WINDOW_HEIGHT
        self.title = "Card Battle Master"
        self.subtitle = "by Hiromichi"
        self.font_spec = get_chinese_font()

        # 动画参数
        self.fade_in = fade_in_default
        self.hold = hold_default
        self.fade_out = fade_out_default
        self.min_display = min_display_default

        # 状态
        self._time = 0.0
        self._phase = "fade_in" if self.fade_in > 0 else "hold"
        self.running = True
        self.loading_done = False
        self._loader_thread: Optional[threading.Thread] = None
        self._loader_exc: Optional[Exception] = None
        self._loader_func: Optional[Callable[[], None]] = None
        self._on_finished: Optional[Callable[[], None]] = None
        self._start_clock = time.time()

        # 星星
        self.stars: List[_Star] = [ _Star(self.width, self.height) for _ in range(max(8, int(star_count_default))) ]

        # 字体
        if not pygame.font.get_init():
            try:
                pygame.font.init()
            except Exception:
                pass
        # create fonts from spec if provided; fallback to default
        try:
            if isinstance(self.font_spec, str) and os.path.exists(self.font_spec):
                self.title_font = pygame.font.Font(self.font_spec, max(36, int(self.width / 18)))
                self.sub_font = pygame.font.Font(self.font_spec, max(12, int(self.width / 40)))
            elif isinstance(self.font_spec, str):
                self.title_font = pygame.font.SysFont(self.font_spec, max(36, int(self.width / 18)))
                self.sub_font = pygame.font.SysFont(self.font_spec, max(12, int(self.width / 40)))
            else:
                self.title_font = pygame.font.Font(None, max(36, int(self.width / 18)))
                self.sub_font = pygame.font.Font(None, max(12, int(self.width / 40)))
        except Exception:
            self.title_font = pygame.font.Font(None, max(36, int(self.width / 18)))
            self.sub_font = pygame.font.Font(None, max(12, int(self.width / 40)))

        # surfaces cache for performance
        self._title_surf = None
        self._subtitle_surf = None
        self._create_text_surfaces()

        # precreate a transparent overlay surface used for fade
        self._overlay = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
        
        # Cache star rendering surface to reduce per-frame creation
        self._star_surface_cache = None
        self._star_cache_dirty = True

    # ---------- loader handling ----------
    def start_loading(self, loader_func: Optional[Callable[[], None]] = None, on_finished: Optional[Callable[[], None]] = None):
        """
        启动后台加载器并指定完成回调
        loader_func: callable 执行耗时加载（不要在其中大量使用 pygame 绘制/Surface 操作）
        on_finished: callable 在加载完成并且淡出结束后调用（通常用于切换场景）
        """
        self._loader_func = loader_func
        self._on_finished = on_finished
        self.loading_done = False
        self._loader_exc = None

        if loader_func is None:
            # nothing to do; mark done immediately
            self.loading_done = True
            return

        def _run_loader():
            try:
                loader_func()
                self.loading_done = True
            except Exception as e:
                self._loader_exc = e
                self.loading_done = True

        self._loader_thread = threading.Thread(target=_run_loader, daemon=True)
        self._loader_thread.start()

    # ---------- lifecycle ----------
    def update(self, dt: float):
        """每帧调用，dt 单位秒"""
        # update star field
        for s in self.stars:
            s.update(dt)
        # Mark star cache dirty every few frames to refresh twinkling
        if int(self._time * 10) % 3 == 0:
            self._star_cache_dirty = True

        # advance time & manage phases
        self._time += dt

        # phase machine
        if self._phase == "fade_in":
            if self._time >= self.fade_in:
                self._time = 0.0
                self._phase = "hold"
        elif self._phase == "hold":
            # ensure min_display and loader done
            elapsed_since_start = time.time() - self._start_clock
            # if loader finished and held long enough -> fade_out
            if self.loading_done and elapsed_since_start >= self.min_display and self._time >= self.hold:
                self._time = 0.0
                self._phase = "fade_out"
        elif self._phase == "fade_out":
            if self._time >= self.fade_out:
                # finished: call callback on main thread after everything settled
                self.running = False
                try:
                    if callable(self._on_finished):
                        self._on_finished()
                except Exception:
                    pass
        # if loader thread raised, you can inspect self._loader_exc in outer code

    def handle_event(self, event: pygame.event.Event):
        # optionally allow skipping splash on key or mouse (comment/uncomment as desired)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # skip immediately to fade_out if loader is done; otherwise set loading_done True
            if not self.loading_done:
                self.loading_done = True
            else:
                self._phase = "fade_out"
                self._time = 0.0

    # ---------- drawing ----------
    def draw(self, surface: pygame.Surface):
        """把 splash 绘制到给定 surface（通常为整个窗口）。"""
        # background
        surface.fill(DEFAULT_BG_COLOR)

        # draw stars using cached surface
        if self._star_cache_dirty or self._star_surface_cache is None:
            self._star_surface_cache = pygame.Surface((self.width, self.height), flags=pygame.SRCALPHA)
            for s in self.stars:
                a = s.alpha()
                col = (*STAR_COLOR[:3], a)
                r = max(1, int(s.size))
                pygame.draw.circle(self._star_surface_cache, col, (int(s.x), int(s.y)), r)
            self._star_cache_dirty = False
        surface.blit(self._star_surface_cache, (0, 0))

        # title text (centered)
        if self._title_surf is None:
            self._create_text_surfaces()
        title_surf = self._title_surf
        tw, th = title_surf.get_size()
        tx = (self.width - tw) // 2
        ty = (self.height - th) // 2 - 12
        surface.blit(title_surf, (tx, ty))

        if self._subtitle_surf:
            sub_w, sub_h = self._subtitle_surf.get_size()
            sx = (self.width - sub_w) // 2
            sy = ty + th + 6
            surface.blit(self._subtitle_surf, (sx, sy))

        # calculate current overall alpha from phase & _time
        alpha = 255
        if self._phase == "fade_in" and self.fade_in > 0:
            alpha = int(255 * min(1.0, max(0.0, self._time / self.fade_in)))
        elif self._phase == "hold":
            alpha = 255
        elif self._phase == "fade_out" and self.fade_out > 0:
            alpha = int(255 * max(0.0, 1.0 - (self._time / self.fade_out)))

        # overlay for fade (draw full-screen translucent black with computed alpha for smooth fade)
        self._overlay.fill((0, 0, 0, 0))  # clear
        tmp = surface.copy()
        tmp.set_alpha(alpha)
        surface.blit(tmp, (0, 0))

        # optional small loading indicator (blinking dot) bottom center
        if not self.loading_done:
            dot = "." * (1 + int((time.time() * 2) % 3))
            try:
                info_surf = self.sub_font.render("加载中" + dot, True, SUBTITLE_COLOR)
                sx = (self.width - info_surf.get_width()) // 2
                sy = ty + th + 40
                surface.blit(info_surf, (sx, sy))
            except Exception:
                pass

    def _create_text_surfaces(self):
        try:
            # title: white boldish (we simulate bold by drawing shadow)
            self._title_surf = self.title_font.render(self.title, True, TITLE_COLOR)
            if self.subtitle:
                self._subtitle_surf = self.sub_font.render(self.subtitle, True, SUBTITLE_COLOR)
            else:
                self._subtitle_surf = None
        except Exception:
            # fallback: simple surfaces
            self._title_surf = pygame.Surface((200, 40), pygame.SRCALPHA)
            self._title_surf.fill((255, 255, 255, 255))
            self._subtitle_surf = None

    # ---------- utility ----------
    def is_finished(self) -> bool:
        return not self.running
