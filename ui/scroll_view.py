"""滚动视图组件"""
import pygame
import math
from config import UI_SCALE

"""滚动视图类"""
class ScrollView:
    def __init__(self, x, y, width, height, content_height):
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
                
class DashboardView:
    def __init__(self, x, y, width, height, content_height, bg_alpha=255, tilt_angle=0, 
                 highlight_center=True, highlight_box_height=None, highlight_glow_speed=6,
                 highlight_border_width=3, highlight_base_alpha=180, highlight_alpha_range=75):
        """
        初始化仪表盘式滚动视图
        
        Args:
            x: X坐标
            y: Y坐标
            width: 宽度
            height: 高度
            content_height: 内容总高度
            bg_alpha: 背景透明度 (0-255)
            tilt_angle: 倾斜角度（度数），0为垂直
            highlight_center: 是否显示中心高亮选择框
            highlight_box_height: 高亮框高度（None 则自动计算）
            highlight_glow_speed: 高亮框呼吸速度
            highlight_border_width: 高亮框边框宽度
            highlight_base_alpha: 高亮框基础透明度
            highlight_alpha_range: 高亮框透明度呼吸范围
        """
        self.x = x
        self. y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        self.content_height = content_height
        self.scroll_y = 0
        self.max_scroll = max(0, content_height - height)
        
        # 透明度和倾斜设置
        self.bg_alpha = max(0, min(255, bg_alpha))
        self.tilt_angle = tilt_angle
        self.highlight_center = highlight_center
        
        # 滚动速度
        self.scroll_speed = max(30, int(50 * UI_SCALE))
        
        # 拖拽相关
        self. is_dragging = False
        self.drag_start_y = 0
        self.drag_start_scroll = 0
        
        # 滚动条
        self.scrollbar_width = max(8, int(12 * UI_SCALE))
        self.scrollbar_color = (100, 100, 120, 150)
        self.scrollbar_hover_color = (130, 130, 150, 200)
        self.is_scrollbar_hovered = False
        
        # 创建带透明度的surface
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # 中心高亮框配置（可自定义）
        self.highlight_box_height = highlight_box_height if highlight_box_height else int(110 * UI_SCALE)
        self.highlight_y = (height - self.highlight_box_height) // 2
        self.highlight_glow_speed = highlight_glow_speed
        self.highlight_border_width = highlight_border_width
        self.highlight_base_alpha = highlight_base_alpha
        self.highlight_alpha_range = highlight_alpha_range
        
        # 呼吸效果动画变量
        self.glow_timer = 0
        self.glow_intensity = 0
    
    def update_content_height(self, content_height):
        """更新内容高度"""
        self.content_height = content_height
        self.max_scroll = max(0, content_height - self.rect.height)
        self.scroll_y = min(self.scroll_y, self.max_scroll)
    
    def update(self, dt):
        """更新动画（呼吸效果）"""
        self.glow_timer += dt
        # 平滑呼吸效果，使用可配置的速度参数
        self.glow_intensity = (math.sin(self.glow_timer * self.highlight_glow_speed) + 1) / 2  # 0 to 1
    
    def handle_event(self, event):
        """处理滚动事件"""
        if event.type == pygame.MOUSEWHEEL:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                self.scroll_y -= event.y * self.scroll_speed
                self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
                return True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event. button == 1:
                mouse_pos = event.pos
                if self.rect.collidepoint(mouse_pos):
                    self.is_dragging = True
                    self.drag_start_y = mouse_pos[1]
                    self.drag_start_scroll = self.scroll_y
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event. button == 1:
                self.is_dragging = False
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                mouse_pos = event. pos
                delta_y = mouse_pos[1] - self.drag_start_y
                self.scroll_y = self.drag_start_scroll - delta_y
                self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
                return True
            
            scrollbar_rect = self.get_scrollbar_rect()
            if scrollbar_rect:
                self.is_scrollbar_hovered = scrollbar_rect.collidepoint(event.pos)
        
        return False
    
    def get_scrollbar_rect(self):
        """获取滚动条矩形（倾斜跟随）"""
        if self.max_scroll <= 0:
            return None
        
        scrollbar_height = max(30, 
                              int(self.rect.height * (self.rect.height / self.content_height)))
        
        scrollbar_y = self.rect.y + int(
            (self.rect.height - scrollbar_height) * (self.scroll_y / self.max_scroll)
        )
        
        # 滚动条跟随倾斜角度
        if self.tilt_angle != 0:
            offset = int((scrollbar_y - self.rect. y) * math.tan(math.radians(self.tilt_angle)))
            scrollbar_x = self.rect.right - self.scrollbar_width - 5 + offset
        else:
            scrollbar_x = self.rect. right - self.scrollbar_width - 5
        
        return pygame.Rect(scrollbar_x, scrollbar_y, 
                          self.scrollbar_width, scrollbar_height)
    
    def get_highlight_box_rect(self):
        """获取中心高亮选择框的矩形"""
        return pygame.Rect(
            self.rect.x,
            self.rect.y + self.highlight_y,
            self.rect.width,
            self.highlight_box_height
        )
    
    def begin_draw(self):
        """开始绘制内容"""
        self.surface. fill((0, 0, 0, 0))
        
        # 绘制半透明背景
        if self.bg_alpha > 0:
            bg_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, self. bg_alpha))
            self. surface.blit(bg_surface, (0, 0))
        
        return self.surface, -self.scroll_y
    
    def end_draw(self, screen):
        """结束绘制（将内容绘制到屏幕，支持倾斜）"""
        # 先绘制中心高亮框（在倾斜之前）
        if self.highlight_center:
            self._draw_highlight_box(self.surface)
        
        # 应用倾斜变换
        if self.tilt_angle != 0:
            # 创建倾斜变换后的surface
            tilted_surface = self._apply_tilt_transform(self.surface)
            
            # 计算倾斜后的位置
            tilted_rect = tilted_surface.get_rect()
            tilted_rect.center = self.rect.center
            
            screen.blit(tilted_surface, tilted_rect)
        else:
            screen.blit(self.surface, self.rect)
        
        # 绘制滚动条（在倾斜后的位置）
        self._draw_scrollbar(screen)
    
    def _draw_highlight_box(self, surface):
        """绘制中心高亮选择框 - 参考 MenuButton 的呼吸效果"""
        box_rect = pygame.Rect(0, self.highlight_y, self.width, self.highlight_box_height)
        
        # 多层发光效果（呼吸式）- 参考 MenuButton
        for i in range(5, 0, -1):
            # 动态 alpha 值，随 glow_intensity 呼吸
            base_alpha = 30 * (6 - i)
            alpha = int(base_alpha * (0.6 + self.glow_intensity * 0.4))
            glow_rect = box_rect.inflate(i * 4, i * 4)
            glow_surface = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            
            # 颜色也随呼吸变化
            glow_r = 255
            glow_g = int(215 + 20 * self.glow_intensity)
            glow_b = int(0 + 30 * self.glow_intensity)
            
            pygame.draw.rect(glow_surface, (glow_r, glow_g, glow_b, alpha), glow_surface.get_rect(),
                           border_radius=8)
            surface.blit(glow_surface, (glow_rect.x, glow_rect.y))
        
        # 主边框（使用可配置的透明度参数）
        border_alpha = int(self.highlight_base_alpha + self.highlight_alpha_range * self.glow_intensity)
        border_color_r = 255
        border_color_g = int(215 + 20 * self.glow_intensity)
        border_color_b = int(0 + 30 * self.glow_intensity)
        
        pygame.draw.rect(surface, (border_color_r, border_color_g, border_color_b, border_alpha), box_rect, 
                        width=self.highlight_border_width, border_radius=8)
        
        # 内部半透明填充（呼吸）
        inner_alpha = int(20 + 20 * self.glow_intensity)
        inner_surface = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        inner_surface.fill((255, 215, 0, inner_alpha))
        surface.blit(inner_surface, box_rect)
    
    def _apply_tilt_transform(self, surface):
        """应用倾斜变换（使用 shear 模拟）"""
        # 使用斜切变换而不是旋转，保持按钮内容可读
        width, height = surface.get_size()
        
        # 计算倾斜偏移
        offset = int(height * math.tan(math.radians(self.tilt_angle)))
        
        # 创建新的surface，宽度增加以容纳倾斜
        new_width = width + abs(offset)
        tilted_surface = pygame.Surface((new_width, height), pygame. SRCALPHA)
        
        # 逐行复制并偏移，创建倾斜效果
        for y in range(height):
            # 计算当前行的x偏移
            x_offset = int(y * math.tan(math.radians(self. tilt_angle)))
            
            if self.tilt_angle > 0:
                # 向右倾斜
                tilted_surface.blit(surface, (x_offset, y), 
                                  pygame. Rect(0, y, width, 1))
            else:
                # 向左倾斜
                tilted_surface.blit(surface, (abs(offset) + x_offset, y), 
                                  pygame.Rect(0, y, width, 1))
        
        return tilted_surface
    
    def _draw_scrollbar(self, screen):
        """绘制滚动条"""
        if self.max_scroll > 0:
            scrollbar_rect = self.get_scrollbar_rect()
            if scrollbar_rect:
                color = (self.scrollbar_hover_color if self.is_scrollbar_hovered 
                        else self.scrollbar_color)
                
                scrollbar_surface = pygame.Surface((scrollbar_rect.width, scrollbar_rect.height), 
                                                   pygame.SRCALPHA)
                pygame.draw.rect(scrollbar_surface, color,
                               scrollbar_surface.get_rect(), 
                               border_radius=self.scrollbar_width // 2)
                screen.blit(scrollbar_surface, scrollbar_rect)
    
    def get_center_item_index(self, item_height, item_spacing):
        """获取中心高亮区域对应的项目索引"""
        center_y = self.scroll_y + self.height // 2  # 计算视图中心的绝对位置

        # 减去顶部填充（假设顶部填充 = 视图高度的一半）
        top_padding = self.height // 2
        adjusted_center_y = center_y - top_padding

        # 计算对应的项目索引（使用 round 与吸附逻辑一致）
        item_size = item_height + item_spacing
        if adjusted_center_y <= 0:
            return 0

        index = round(adjusted_center_y / item_size)
        return int(index)
        
    def set_alpha(self, alpha):
        """动态设置透明度"""
        self.bg_alpha = max(0, min(255, alpha))
    
    def set_tilt_angle(self, angle):
        """动态设置倾斜角度"""
        self. tilt_angle = angle
