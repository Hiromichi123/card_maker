import pygame
import sys
import config
from config import *
from startup import SplashScreen
from ui.transition import Transition
from scenes.menu import MainMenuScene
from scenes.gacha_scene import GachaScene
from scenes.gacha_menu import GachaMenuScene
from scenes.collection import CollectionScene
from scenes.deck_builder_scene import DeckBuilderScene
from scenes.battle_menu import BattleMenuScene
from scenes.draft_scene import DraftScene
from scenes.battle.draft_battle import DraftBattleScene
from scenes.battle.simple_battle import SimpleBattleScene

"""场景管理器"""
class SceneManager:
    def __init__(self):
        pygame.init()
        # 创建窗口
        self.screen = pygame.display.set_mode((0, 0), 
                                             pygame.FULLSCREEN | 
                                             pygame.HWSURFACE | 
                                             pygame.DOUBLEBUF)
        
        # 获取屏幕信息并更新配置
        screen_info = pygame.display.Info()
        config.update_ui_scale(screen_info.current_w, screen_info.current_h)
        
        pygame.display.set_caption("抽卡模拟器")
        self.clock = pygame.time.Clock()
        
        # 场景字典
        self.scenes = {}
        self.current_scene = None
        
        # 转场效果
        self.transition = Transition()
        self.pending_scene = None  # 等待切换的场景
        
        # 直接注册并切换主菜单（旧）
        #self.register_scenes() # 注册场景
        #self.switch_scene("main_menu") # 切换到主菜单
        
        # 启动画面，在淡出完成后再注册场景并切换到主菜单(新)
        self.splash = SplashScreen()
        # 开始后台加载（loader 在后台线程运行，on_finished 在主线程 splash 完成时调用）
        self.splash.start_loading(loader_func=self._background_load, on_finished=self._on_splash_finished)

    """注册所有场景"""
    def register_scenes(self):
        self.scenes["main_menu"] = MainMenuScene(self.screen)
        self.scenes["gacha_menu"] = GachaMenuScene(self.screen)
        self.scenes["gacha"] = GachaScene(self.screen)
        self.scenes["collection"] = CollectionScene(self.screen)
        self.scenes["deck_builder"] = DeckBuilderScene(self.screen)
        self.scenes["battle_menu"] = BattleMenuScene(self.screen)
        self.scenes["draft_scene"] = DraftScene(self.screen)
        self.scenes["draft_battle"] = DraftBattleScene(self.screen)
        self.scenes["simple_battle"] = SimpleBattleScene(self.screen)
        
    def switch_scene(self, scene_name):
        """切换场景（带转场效果）"""
        if scene_name not in self.scenes:
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
            dt = self.clock.tick(FPS) / 1000.0

            # 事件处理：如果splash正在运行优先交给splash处理，否则交给当前场景
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    if hasattr(self, "splash") and self.splash.running:
                        self.splash.handle_event(event)
                    else:
                        if self.current_scene and not self.transition.is_transitioning:
                            self.current_scene.handle_event(event)

            # 如果 splash 正在运行，则让 splash 接管更新与绘制，然后跳过常规场景逻辑
            if hasattr(self, "splash") and self.splash.running:
                self.splash.update(dt)
                self.splash.draw(self.screen)
                # 显示 FPS 并翻转缓冲区
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
                self.current_scene.draw_with_tooltip()

            # 绘制转场效果、FPS
            self.transition.draw(self.screen)
            self.draw_fps()
            pygame.display.flip()

        # 退出前清理悬停框资源
        from ui.tooltip import get_tooltip
        tooltip = get_tooltip()
        tooltip.stop_monitoring()

        # 退出
        pygame.quit()
        sys.exit()
    
    def draw_fps(self):
        """绘制FPS信息"""
        font = get_font(max(12, int(20 * UI_SCALE)))
        fps_text = font.render(
            f"FPS: {int(self.clock.get_fps())}", 
            True, (150, 150, 150)
        )
        self.screen.blit(fps_text, (int(WINDOW_WIDTH * 0.92), int(WINDOW_HEIGHT * 0.02)))

    """===========后台加载==========="""
    def _background_load(self):
        """在后台线程运行"""
        try:
            import time, os
            # 示例：预读取 data 下的 json 文件内容（IO-bound，线程安全）
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
            # 可选：短暂 sleep 模拟 / 等待
            time.sleep(0.4)
        except Exception as e:
            print("[SceneManager] background load error:", e)

    def _on_splash_finished(self):
        """
        在主线程由 SplashScreen 在这里注册场景并切换到主菜单（安全地在主线程内执行 pygame 相关操作）。
        """
        # 注册所有场景（在主线程执行，避免线程安全问题）
        self.register_scenes()
        # 切换到主菜单
        self.switch_scene("main_menu")

if __name__ == "__main__":
    game = SceneManager()
    game.run()