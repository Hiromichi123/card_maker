import pygame
import sys
import os
from card_system import CardSystem
import config
from config import *

class Button:
    """按钮类"""
    def __init__(self, x, y, width, height, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.is_hovered = False
        
    def update_position(self, x, y, width, height):
        """更新按钮位置和大小"""
        self.rect = pygame.Rect(x, y, width, height)
        
    def draw(self, screen):
        """绘制按钮"""
        color = BUTTON_HOVER_COLOR if self.is_hovered else BUTTON_COLOR
        border_radius = max(10, int(10 * UI_SCALE))
        border_width = max(3, int(3 * UI_SCALE))
        
        pygame.draw.rect(screen, color, self.rect, border_radius=border_radius)
        pygame.draw.rect(screen, (255, 255, 255), self.rect, border_width, border_radius=border_radius)
        
        font_size = max(18, int(36 * UI_SCALE))
        font = pygame.font.Font(None, font_size)
        text_surface = font.render(self.text, True, BUTTON_TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered:
                return True
        return False


class GachaSimulator:
    """抽卡模拟器主类"""
    def __init__(self):
        pygame.init()
        
        # 高DPI适配
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass
        
        # 全屏模式
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        screen_info = pygame.display.Info()
        
        # 更新UI缩放
        config.update_ui_scale(screen_info.current_w, screen_info.current_h)
        
        pygame.display.set_caption("Gacha Simulator")
        self.clock = pygame.time.Clock()
        
        # 启用硬件加速
        pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        
        # 创建卡牌系统
        self.card_system = CardSystem()
        
        # 创建按钮
        self.draw_button = Button(
            BUTTON_POSITION[0], 
            BUTTON_POSITION[1],
            BUTTON_WIDTH,
            BUTTON_HEIGHT,
            "Draw"
        )
        
        # 创建卡牌目录
        self.create_card_directories()
        
        # 字体
        self.title_font = pygame.font.Font(None, max(32, int(64 * UI_SCALE)))
        self.info_font = pygame.font.Font(None, max(12, int(24 * UI_SCALE)))
        
        # 背景缓存
        self.background = self.create_background()
        
    def create_background(self):
        """预渲染背景"""
        bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        bg.fill(BACKGROUND_COLOR)
        
        # 网格
        grid_size = max(20, int(40 * UI_SCALE))
        for x in range(0, WINDOW_WIDTH, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (0, y), (WINDOW_WIDTH, y), 1)
        
        return bg
        
    def create_card_directories(self):
        """创建卡牌目录结构"""
        if not os.path.exists(CARD_BASE_PATH):
            os.makedirs(CARD_BASE_PATH)
            
        for rarity in CARD_PROBABILITIES.keys():
            path = os.path.join(CARD_BASE_PATH, rarity)
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"创建目录: {path}")
    
    def draw_title(self):
        """绘制标题"""
        title_y = int(WINDOW_HEIGHT * 0.04)
        
        title_text = self.title_font.render("Gacha Simulator", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, title_y))
        
        shadow_text = self.title_font.render("Gacha Simulator", True, (0, 0, 0))
        shadow_offset = max(2, int(2 * UI_SCALE))
        shadow_rect = shadow_text.get_rect(center=(WINDOW_WIDTH // 2 + shadow_offset, title_y + shadow_offset))
        
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
    
    def draw_probability_info(self):
        """绘制概率信息"""
        y_offset = int(WINDOW_HEIGHT * 0.92)  # 屏幕92%的位置
        x_start = int(WINDOW_WIDTH * 0.05)
        x_spacing = int(WINDOW_WIDTH * 0.12)
        
        for idx, (rarity, prob) in enumerate(CARD_PROBABILITIES.items()):
            color = COLORS.get(rarity, (255, 255, 255))
            info_text = f"{rarity}({prob}%)"
            text = self.info_font.render(info_text, True, color)
            self.screen.blit(text, (x_start + idx * x_spacing, y_offset))
    
    def run(self):
        """主循环"""
        running = True
        
        while running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        if not self.card_system.is_animating:
                            self.card_system.draw_cards()
                
                if self.draw_button.handle_event(event):
                    if not self.card_system.is_animating:
                        self.card_system.draw_cards()
            
            # 更新
            self.card_system.update(dt)
            
            # 绘制（使用缓存背景）
            self.screen.blit(self.background, (0, 0))
            self.draw_title()
            self.card_system.draw(self.screen)
            self.draw_button.draw(self.screen)
            self.draw_probability_info()
            
            # 显示FPS和分辨率信息
            fps_text = self.info_font.render(
                f"FPS: {int(self.clock.get_fps())} | {WINDOW_WIDTH}x{WINDOW_HEIGHT} | Scale: {UI_SCALE:.2f}", 
                True, (150, 150, 150)
            )
            self.screen.blit(fps_text, (int(WINDOW_WIDTH * 0.7), int(WINDOW_HEIGHT * 0.02)))
            
            pygame.display.flip()
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    simulator = GachaSimulator()
    simulator.run()