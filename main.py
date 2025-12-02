import os
import sys

def _ensure_working_directory():
    """Adjust cwd so relative asset paths resolve in both dev and PyInstaller builds."""
    base_path = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    try:
        os.chdir(base_path)
    except OSError as err:
        print(f"[SceneManager] 无法切换工作目录: {err}")

_ensure_working_directory()

import pygame
import config
from importlib import import_module
from ui.transition import Transition

"""场景管理器"""
class SceneManager:
    def __init__(self):
        pygame.init()
        # 创建窗口
        self.display = pygame.display.set_mode((0, 0), 
                             pygame.FULLSCREEN | 
                             pygame.HWSURFACE | 
                             pygame.DOUBLEBUF)
        
        # 获取屏幕信息并更新配置
        screen_info = pygame.display.Info()
        self._screen_size = (screen_info.current_w, screen_info.current_h)
        config.initialize_design_resolution(*self._screen_size)
        config.update_ui_scale(*self._screen_size)
        
        pygame.display.set_caption("Card Battle Master")
        self.clock = pygame.time.Clock()
        
        # 场景字典
        self.scenes = {}
        self.scene_factories = {}
        self.current_scene = None
        self.render_surface = None
        self.screen = None  # 传递给场景的渲染surface
        self._raw_mouse_get_pos = pygame.mouse.get_pos

        def _patched_mouse_pos():
            raw_x, raw_y = self._raw_mouse_get_pos()
            return (
                raw_x - config.VIEW_DEST_X + config.VIEW_SRC_X,
                raw_y - config.VIEW_DEST_Y + config.VIEW_SRC_Y,
            )

        pygame.mouse.get_pos = _patched_mouse_pos
        self._patched_mouse_get_pos = _patched_mouse_pos
        self._handle_scale_change(force=True)
        self._design_override_active = False
        
        # 转场效果
        self.transition = Transition()
        self.pending_scene = None  # 等待切换的场景
        
        # 启动画面，在淡出完成后再注册场景并切换到主菜单
        from startup import SplashScreen  # 延迟导入以确保使用更新后的UI配置
        self.splash = SplashScreen()
        # 开始后台加载（loader 在后台线程运行，on_finished 在主线程 splash 完成时调用）
        self.splash.start_loading(loader_func=self._background_load, on_finished=self._on_splash_finished)

    """注册部分场景"""
    def register_scenes(self):
        scene_map = {
            "main_menu": ("scenes.menu", "MainMenuScene"),
            "gacha_menu": ("scenes.gacha.gacha_menu", "GachaMenuScene"),
            "gacha": ("scenes.gacha.gacha_scene", "GachaScene"),
            "collection": ("scenes.collection", "CollectionScene"),
            "deck_builder": ("scenes.deck_builder_scene", "DeckBuilderScene"),
            "activity_scene": ("scenes.activity.activity_scene", "ActivityScene"),
            "activity_maze_scene": ("scenes.activity.maze_scene", "ActivityMazeScene"),
            "floor_shop": ("scenes.activity.floor_shop_scene", "FloorShopScene"),
            "shop_scene": ("scenes.shop_scene", "ShopScene"),
            "activity_shop_scene": ("scenes.activity.activity_shop_scene", "ActivityShopScene"),
            "workshop_scene": ("scenes.workshop_scene", "WorkshopScene"),
            "battle_menu": ("scenes.battle_menu", "BattleMenuScene"),
            "draft_scene": ("scenes.draft_scene", "DraftScene"),
            "draft_battle": ("scenes.battle.draft_battle", "DraftBattleScene"),
            "simple_battle": ("scenes.battle.simple_battle", "SimpleBattleScene"),
            "world_map": ("scenes.map.world_map_scene", "WorldMapScene"),
            "chapter_map": ("scenes.map.chapter_map_scene", "ChapterMapScene"),
        }
        for name, (module_path, class_name) in scene_map.items():
            module = import_module(module_path)
            scene_cls = getattr(module, class_name)
            self._register_scene(name, scene_cls, lazy=True)

    def _register_scene(self, scene_name, scene_cls, lazy=False):
        if lazy:
            self.scene_factories[scene_name] = scene_cls
        else:
            self.scenes[scene_name] = scene_cls(self.screen)

    def _get_or_create_scene(self, scene_name):
        if scene_name in self.scenes:
            return self.scenes[scene_name]
        if scene_name in self.scene_factories:
            scene_cls = self.scene_factories.pop(scene_name)
            scene = scene_cls(self.screen)
            self.scenes[scene_name] = scene
            return scene
        return None
        
    def switch_scene(self, scene_name):
        """切换场景"""
        if scene_name not in self.scenes:
            scene = self._get_or_create_scene(scene_name)
            if scene is None:
                print(f"警告: 场景 '{scene_name}' 不存在")
                return
        
        # 如果正在转场，忽略新的切换请求
        if self.transition.is_transitioning:
            return
        
        # 开始淡出转场
        self.pending_scene = scene_name
        self.transition.start_fade_out(on_complete=self._complete_scene_switch)
    
    def _complete_scene_switch(self):
        """完成场景切换"""
        if not self.pending_scene:
            return
        
        # 退出当前场景
        if self.current_scene:
            self.current_scene.exit()
        
        # 进入新场景
        self.current_scene = self.scenes[self.pending_scene]
        self.current_scene.enter()
        
        print(f"切换到场景: {self.pending_scene}")
        self.pending_scene = None
        
        # 开始淡入转场
        self.transition.start_fade_in()
    
    def run(self):
        """主循环（已集成Splash）"""
        running = True

        while running:
            design_changed = self._apply_scene_design_policy()
            self._handle_scale_change(force=design_changed)
            dt = self.clock.tick(config.FPS) / 1000.0

            # 事件处理：如果splash正在运行优先交给splash处理，否则交给当前场景
            for raw_event in pygame.event.get():
                if raw_event.type == pygame.QUIT:
                    running = False
                else:
                    event = self._translate_event(raw_event)
                    if hasattr(self, "splash") and self.splash.running:
                        self.splash.handle_event(event)
                    else:
                        if self.current_scene and not self.transition.is_transitioning:
                            self.current_scene.handle_event(event)

            # 如果 splash 正在运行，则让 splash 接管更新与绘制，然后跳过常规场景逻辑
            if hasattr(self, "splash") and self.splash.running:
                self.splash.update(dt)
                self.render_surface.fill(config.BACKGROUND_COLOR)
                self.splash.draw(self.screen)
                self._blit_render_surface()
                self.transition.draw(self.display)
                self.draw_fps()
                pygame.display.flip()
                continue

            # 检查退出标志quit_flag，若为真则退出主循环
            if self.current_scene and getattr(self.current_scene, "quit_flag", False):
                running = False
                continue

            # 更新转场效果
            self.transition.update(dt)

            # 更新当前场景并处理场景内部请求的切换
            if self.current_scene:
                self.current_scene.update(dt)

                if self.current_scene.next_scene and not self.transition.is_transitioning:
                    next_scene = self.current_scene.next_scene
                    self.current_scene.next_scene = None
                    self.switch_scene(next_scene)

            # 绘制当前场景（含提示框）
            if self.current_scene:
                self.render_surface.fill(config.BACKGROUND_COLOR)
                self.current_scene.draw_with_tooltip()

            # 绘制到真实屏幕并叠加转场/FPS
            self._blit_render_surface()
            self.transition.draw(self.display)
            self.draw_fps()
            pygame.display.flip()

        # 退出前清理悬停框资源
        from ui.tooltip import get_tooltip
        tooltip = get_tooltip()
        tooltip.stop_monitoring()

        # 退出
        pygame.mouse.get_pos = self._raw_mouse_get_pos
        pygame.quit()
        sys.exit()
    
    def draw_fps(self):
        """绘制FPS信息"""
        font = config.get_font(max(12, int(20 * config.UI_SCALE)))
        fps_text = font.render(
            f"FPS: {int(self.clock.get_fps())}", 
            True, (150, 150, 150)
        )
        draw_x = config.VIEW_DEST_X + int(config.VISIBLE_WIDTH * 0.92)
        draw_y = config.VIEW_DEST_Y + int(config.VISIBLE_HEIGHT * 0.02)
        self.display.blit(fps_text, (draw_x, draw_y))

    def _translate_event(self, event):
        """将鼠标事件转换到渲染区域坐标系"""
        if hasattr(event, "pos"):
            adjusted = (
                event.pos[0] - config.VIEW_DEST_X + config.VIEW_SRC_X,
                event.pos[1] - config.VIEW_DEST_Y + config.VIEW_SRC_Y
            )
            payload = dict(getattr(event, "dict", {}))
            payload["pos"] = adjusted
            return pygame.event.Event(event.type, payload)
        return event

    def _handle_scale_change(self, force=False):
        """根据配置刷新渲染surface并同步给所有场景"""
        if not force and not config.SCALE_DIRTY:
            if self.render_surface is not None:
                return
        surface_size = (config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        if surface_size[0] <= 0 or surface_size[1] <= 0:
            return
        self.render_surface = pygame.Surface(surface_size).convert_alpha()
        self.render_surface.fill(config.BACKGROUND_COLOR)
        self.screen = self.render_surface
        for scene in self.scenes.values():
            scene.screen = self.render_surface
        if self.current_scene and self.current_scene not in self.scenes.values():
            self.current_scene.screen = self.render_surface
        config.SCALE_DIRTY = False

    def _blit_render_surface(self):
        if not self.render_surface:
            return
        self.display.fill((0, 0, 0))
        src_rect = pygame.Rect(
            config.VIEW_SRC_X,
            config.VIEW_SRC_Y,
            config.VISIBLE_WIDTH,
            config.VISIBLE_HEIGHT,
        )
        self.display.blit(
            self.render_surface,
            (config.VIEW_DEST_X, config.VIEW_DEST_Y),
            src_rect,
        )

    def _apply_scene_design_policy(self):
        """切换场景时根据需要强制原生设计分辨率。"""
        desired_override = bool(self.current_scene and getattr(self.current_scene, "force_native_resolution", False))
        if desired_override == self._design_override_active:
            return False
        if desired_override:
            config.set_design_resolution(config.BASE_DESIGN_WIDTH, config.BASE_DESIGN_HEIGHT)
        else:
            config.initialize_design_resolution(*self._screen_size)
        config.update_ui_scale(*self._screen_size)
        self._design_override_active = desired_override
        return True

    """===========后台加载==========="""
    def _background_load(self):
        """在后台线程运行"""
        try:
            # 预读取data的json文件（IO-bound，线程安全）
            data_dir = "data"
            for root, dirs, files in os.walk(data_dir):
                for fn in files:
                    if fn.lower().endswith(".json"):
                        p = os.path.join(root, fn)
                        try:
                            with open(p, "r", encoding="utf-8") as f:
                                _ = f.read()
                        except Exception:
                            pass
        except Exception as e:
            print("[SceneManager] background load error:", e)

    def _on_splash_finished(self):
        """在主线程由 SplashScreen 在这里注册场景并切换到主菜单"""
        self.register_scenes() # 注册所有场景（在主线程执行，避免线程安全问题）
        self.switch_scene("main_menu") # 切换到主菜单

if __name__ == "__main__":
    import ctypes

    # 设置任务栏图标（仅限Windows）
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("cardbattlemaster")

    icon_path = os.path.join("assets", "ui", "card_back.png")
    if os.path.exists(icon_path):
        try:
            icon_surface = pygame.image.load(icon_path)
            pygame.display.set_icon(icon_surface)
        except pygame.error as exc:
            print(f"[Icon] Failed to load {icon_path}: {exc}")
    else:
        print(f"[Icon] Missing icon at {icon_path}")

    pygame.display.set_caption("Card Battle Master")

    game = SceneManager()
    game.run()
