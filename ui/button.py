"""通用按钮组件"""
import pygame
from config import UI_SCALE, get_font

"""按钮类"""
class Button:
    def __init__(self, x, y, width, height, text, 
                 color=(100, 150, 255),
                 hover_color=(130, 180, 255),
                 text_color=(255, 255, 255),
                 font_size=36,
                 on_click=None):

        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.on_click = on_click
        
        # 根据UI缩放调整字体 - 使用中文字体
        scaled_font_size = int(font_size * UI_SCALE)
        self.font = get_font(scaled_font_size)  # 修改这里
        
        # 预渲染文字
        self.text_surface = self.font.render(text, True, text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
        
    def update_position(self, x, y, width=None, height=None):
        """更新按钮位置"""
        if width is None:
            width = self.rect.width
        if height is None:
            height = self.rect.height
        self.rect = pygame.Rect(x, y, width, height)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def set_text(self, text):
        """更新按钮文字"""
        self.text = text
        self.text_surface = self.font.render(text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
        
    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.is_hovered and event.button == 1:
                if self.on_click:
                    self.on_click()
                return True
        return False
    
    def draw(self, screen):
        """绘制按钮"""
        color = self.hover_color if self.is_hovered else self.color
        border_radius = int(10 * UI_SCALE)
        border_width = int(3 * UI_SCALE)
        
        # 绘制按钮背景
        pygame.draw.rect(screen, color, self.rect, border_radius=border_radius)
        # 绘制边框
        pygame.draw.rect(screen, (255, 255, 255), self.rect, 
                        border_width, border_radius=border_radius)
        
        # 绘制文字
        screen.blit(self.text_surface, self.text_rect)


class ImageButton(Button):
    """图片按钮"""
    
    def __init__(self, x, y, width, height, image_path, 
                 hover_scale=1.1, on_click=None):
        super().__init__(x, y, width, height, "", on_click=on_click)
        
        try:
            self.image = pygame.image.load(image_path)
            self.image = pygame.transform.smoothscale(self.image, (width, height))
        except:
            self.image = pygame.Surface((width, height))
            self.image.fill((100, 100, 100))
        
        self.hover_scale = hover_scale
        self.current_scale = 1.0
        
    def draw(self, screen):
        """绘制图片按钮"""
        target_scale = self.hover_scale if self.is_hovered else 1.0
        self.current_scale += (target_scale - self.current_scale) * 0.2
        
        if self.current_scale != 1.0:
            width = int(self.rect.width * self.current_scale)
            height = int(self.rect.height * self.current_scale)
            scaled_image = pygame.transform.smoothscale(self.image, (width, height))
            pos = (
                self.rect.centerx - width // 2,
                self.rect.centery - height // 2
            )
        else:
            scaled_image = self.image
            pos = self.rect.topleft
        
        screen.blit(scaled_image, pos)