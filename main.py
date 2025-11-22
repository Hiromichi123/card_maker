import pygame
import sys
import ctypes
import config
from config import *
# 导入场景
from scenes.menu import MainMenuScene
from scenes.gacha import GachaScene
from scenes.collection import CollectionScene
from scenes.deck_builder_scene import DeckBuilderScene
from scenes.battle_menu import BattleMenuScene
from scenes.battle import BattleScene
from scenes.draft_scene import DraftScene

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
        
        self.register_scenes() # 注册场景
        self.switch_scene("main_menu") # 切换到主菜单
        
    """注册所有场景"""
    def register_scenes(self):
        self.scenes["main_menu"] = MainMenuScene(self.screen)
        self.scenes["gacha"] = GachaScene(self.screen)
        self.scenes["collection"] = CollectionScene(self.screen)
        self.scenes["deck_builder"] = DeckBuilderScene(self.screen)
        self.scenes["battle_menu"] = BattleMenuScene(self.screen)
        self.scenes["battle"] = BattleScene(self.screen)
        self.scenes["draft_scene"] = DraftScene(self.screen)
        
    def switch_scene(self, scene_name):
        """切换场景"""
        if scene_name not in self.scenes:
            print(f"警告: 场景 '{scene_name}' 不存在")
            return
        
        # 退出当前场景
        if self.current_scene:
            self.current_scene.exit()
        
        # 进入新场景
        self.current_scene = self.scenes[scene_name]
        self.current_scene.enter()
        
        print(f"切换到场景: {scene_name}")
    
    def run(self):
        """主循环"""
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    # 传递事件到当前场景
                    if self.current_scene:
                        self.current_scene.handle_event(event)
            
            # 检查主菜单的退出标志
            if hasattr(self.current_scene, 'quit_flag') and self.current_scene.quit_flag:
                running = False
            
            # 更新当前场景
            if self.current_scene:
                self.current_scene.update(dt)
                
                # 检查是否需要切换场景
                if self.current_scene.next_scene:
                    next_scene = self.current_scene.next_scene
                    self.current_scene.next_scene = None
                    self.switch_scene(next_scene)
            
            # 绘制当前场景
            if self.current_scene:
                self.current_scene.draw_with_tooltip() # 绘制场景和提示框
            
            self.draw_fps() # 显示FPS
            pygame.display.flip()
        
        # 清理悬停框资源
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

if __name__ == "__main__":
    game = SceneManager()
    game.run()