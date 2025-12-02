"""背景管理器，视差效果"""
import pygame
import os
import random

"""背景管理器"""
class ParallaxBackground:
    def __init__(self, width, height, bg_type):
        self.width = width
        self.height = height
        self.bg_type = bg_type
        
        # 视差偏移
        self.offset_x = 0
        self.offset_y = 0
        self.target_offset_x = 0
        self.target_offset_y = 0
        
        # 加载或创建背景
        self.background = self.create_background()
        
        # 创建更大的表面以实现视差效果（缓存避免每帧重建）
        self.parallax_width = int(width * 1.1)
        self.parallax_height = int(height * 1.1)
        self.parallax_surface = pygame.transform.smoothscale(
            self.background, (self.parallax_width, self.parallax_height)
        ).convert()  # convert to display format for faster blitting

    """==========核心组件=========="""
    def update(self, dt):
        """更新视差动画"""
        self.offset_x += (self.target_offset_x - self.offset_x) * 5 * dt
        self.offset_y += (self.target_offset_y - self.offset_y) * 5 * dt

    def update_mouse_position(self, mouse_pos):
        """根据鼠标位置更新视差偏移"""
        center_x = self.width / 2
        center_y = self.height / 2
        max_offset = 50
        self.target_offset_x = ((mouse_pos[0] - center_x) / center_x) * max_offset
        self.target_offset_y = ((mouse_pos[1] - center_y) / center_y) * max_offset
        
    def draw(self, screen):
        """绘制带视差效果的背景"""
        src_x = int((self.parallax_width - self.width) / 2 - self.offset_x)
        src_y = int((self.parallax_height - self.height) / 2 - self.offset_y)
        
        # 确保不超出边界
        src_x = max(0, min(src_x, self.parallax_width - self.width))
        src_y = max(0, min(src_y, self.parallax_height - self.height))
        
        # 绘制视差表面的部分区域
        screen.blit(self.parallax_surface, (0, 0), 
                   pygame.Rect(src_x, src_y, self.width, self.height))

    """==========初始化=========="""
    def create_background(self):
        # 支持jpg/png文件路径
        bg_filename = f"assets/{self.bg_type}_bg.png"
        bg_filename_jpg = f"assets/{self.bg_type}_bg.jpg"
        if os.path.exists(bg_filename):
            bg = pygame.image.load(bg_filename)
            bg = pygame.transform.smoothscale(bg, (self.width, self.height))
            return bg
        elif os.path.exists(bg_filename_jpg):
            bg = pygame.image.load(bg_filename_jpg)
            bg = pygame.transform.smoothscale(bg, (self.width, self.height))
            return bg
        else:
            print(f"[Background] 文件不存在:{bg_filename}和{bg_filename_jpg}使用程序化背景")
            # 生成默认背景
            bg = pygame.Surface((self.width, self.height))
            self._draw_gradient(bg, (20, 30, 60), (30, 50, 100))
            self._add_stars(bg, count=100, color=(100, 150, 255))
            self._add_circles(bg, count=5, color=(50, 100, 200, 30))
            return bg

    """==========默认背景生成组件=========="""
    def _draw_gradient(self, surface, color1, color2):
        """绘制垂直渐变背景"""
        for y in range(self.height):
            ratio = y / self.height
            r = int(color1[0] + (color2[0] - color1[0]) * ratio)
            g = int(color1[1] + (color2[1] - color1[1]) * ratio)
            b = int(color1[2] + (color2[2] - color1[2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))
    
    def _add_stars(self, surface, count, color):
        """添加星星粒子"""
        for _ in range(count):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(1, 3)
            alpha = random.randint(100, 255)
            
            # 创建临时表面以支持透明度
            star_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            star_color = (*color[:3], alpha) if len(color) > 3 else (*color, alpha)
            pygame.draw.circle(star_surf, star_color, (size, size), size)
            surface.blit(star_surf, (x - size, y - size))
    
    def _add_circles(self, surface, count, color):
        """添加装饰性圆圈"""
        temp_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        for _ in range(count):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            radius = random.randint(100, 300)
            
            if len(color) == 4:
                pygame.draw.circle(temp_surf, color, (x, y), radius)
            else:
                pygame.draw.circle(temp_surf, (*color, 30), (x, y), radius)
        
        surface.blit(temp_surf, (0, 0))
