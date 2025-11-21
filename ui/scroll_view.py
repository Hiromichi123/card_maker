"""
滚动视图组件
支持鼠标滚轮和拖拽
"""
import pygame
from config import UI_SCALE

class ScrollView:
    """滚动视图类"""
    
    def __init__(self, x, y, width, height, content_height):
        """
        Args:
            x, y: 视图位置
            width, height: 视图尺寸
            content_height: 内容总高度
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.content_height = content_height
        self.scroll_y = 0  # 当前滚动位置
        self.max_scroll = max(0, content_height - height)
        
        # 滚动速度
        self.scroll_speed = max(30, int(50 * UI_SCALE))
        
        # 拖拽相关
        self.is_dragging = False
        self.drag_start_y = 0
        self.drag_start_scroll = 0
        
        # 滚动条
        self.scrollbar_width = max(8, int(12 * UI_SCALE))
        self.scrollbar_color = (100, 100, 120)
        self.scrollbar_hover_color = (130, 130, 150)
        self.is_scrollbar_hovered = False
        
        # 创建surface用于裁剪
        self.surface = pygame.Surface((width, height))
        
    def update_content_height(self, content_height):
        """更新内容高度"""
        self.content_height = content_height
        self.max_scroll = max(0, content_height - self.rect.height)
        self.scroll_y = min(self.scroll_y, self.max_scroll)
    
    def handle_event(self, event):
        """处理滚动事件"""
        if event.type == pygame.MOUSEWHEEL:
            # 检查鼠标是否在视图内
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                # 向上滚动为正，向下为负
                self.scroll_y -= event.y * self.scroll_speed
                self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                mouse_pos = event.pos
                if self.rect.collidepoint(mouse_pos):
                    self.is_dragging = True
                    self.drag_start_y = mouse_pos[1]
                    self.drag_start_scroll = self.scroll_y
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False
        
        elif event.type == pygame.MOUSEMOTION:
            # 拖拽滚动
            if self.is_dragging:
                mouse_pos = event.pos
                delta_y = mouse_pos[1] - self.drag_start_y
                self.scroll_y = self.drag_start_scroll - delta_y
                self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
                return True
            
            # 滚动条悬停检测
            scrollbar_rect = self.get_scrollbar_rect()
            if scrollbar_rect:
                self.is_scrollbar_hovered = scrollbar_rect.collidepoint(event.pos)
        
        return False
    
    def get_scrollbar_rect(self):
        """获取滚动条矩形"""
        if self.max_scroll <= 0:
            return None
        
        # 滚动条高度比例
        scrollbar_height = max(30, 
                              int(self.rect.height * (self.rect.height / self.content_height)))
        
        # 滚动条位置
        scrollbar_y = self.rect.y + int(
            (self.rect.height - scrollbar_height) * (self.scroll_y / self.max_scroll)
        )
        
        scrollbar_x = self.rect.right - self.scrollbar_width - 5
        
        return pygame.Rect(scrollbar_x, scrollbar_y, 
                          self.scrollbar_width, scrollbar_height)
    
    def begin_draw(self):
        """开始绘制内容（返回偏移后的surface）"""
        self.surface.fill((0, 0, 0, 0))
        return self.surface, -self.scroll_y
    
    def end_draw(self, screen):
        """结束绘制（将内容绘制到屏幕）"""
        screen.blit(self.surface, self.rect)
        
        # 绘制滚动条
        if self.max_scroll > 0:
            scrollbar_rect = self.get_scrollbar_rect()
            if scrollbar_rect:
                color = (self.scrollbar_hover_color if self.is_scrollbar_hovered 
                        else self.scrollbar_color)
                pygame.draw.rect(screen, color, scrollbar_rect, 
                               border_radius=self.scrollbar_width // 2)