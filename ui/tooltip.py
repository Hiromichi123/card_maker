"""
卡牌信息提示框 当鼠标悬停在卡牌上时显示详细信息
"""
import pygame
import threading
import time
from config import *

"""卡牌提示框类"""
class CardTooltip:
    def __init__(self):
        self.visible = False
        self.card_data = None
        self.position = (0, 0)
        self.surface = None
        
        # 提示框样式
        self.padding = int(15 * UI_SCALE)
        self.line_spacing = int(8 * UI_SCALE)
        self.border_width = max(2, int(3 * UI_SCALE))
        
        # 字体
        self.title_font = get_font(max(18, int(28 * UI_SCALE)))
        self.info_font = get_font(max(14, int(20 * UI_SCALE)))
        self.desc_font = get_font(max(12, int(18 * UI_SCALE)))
        
        # 延迟显示
        self.hover_start_time = None
        self.show_delay = 0.3  # 悬停0.3秒后显示
        
        # 监控线程
        self.monitor_thread = None
        self.running = False
        self.last_mouse_pos = (0, 0)
    
    def start_monitoring(self):
        """启动鼠标监控线程"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_mouse, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
    
    def _monitor_mouse(self):
        """监控鼠标位置（在线程中运行）"""
        while self.running:
            try:
                # 检查 pygame 是否已初始化
                if pygame.get_init():
                    # 获取当前鼠标位置
                    mouse_pos = pygame.mouse.get_pos()
                    
                    # 如果鼠标移动了，重置悬停计时
                    if mouse_pos != self.last_mouse_pos:
                        self.last_mouse_pos = mouse_pos
                        if self.hover_start_time is not None:
                            self.hover_start_time = time.time()
            except:
                pass  # 忽略错误，继续监控
            
            time.sleep(0.016)  # 约60fps
    
    def show(self, card_data, mouse_pos):
        """
        显示提示框
        Args:
            card_data: CardData对象
            mouse_pos: 鼠标位置
        """
        if card_data is None:
            self.hide()
            return
        
        # 如果是新卡牌，重置计时
        if self.card_data != card_data:
            self.hover_start_time = time.time()
            self.card_data = card_data
            self.visible = False
        
        # 检查是否达到延迟时间
        if self.hover_start_time and time.time() - self.hover_start_time >= self.show_delay:
            self.visible = True
            self.position = mouse_pos
            self._create_surface()
    
    def hide(self):
        """隐藏提示框"""
        self.visible = False
        self.card_data = None
        self.hover_start_time = None
        self.surface = None
    
    def _create_surface(self):
        """创建提示框surface"""
        if not self.card_data:
            return
        
        # 准备文本
        lines = []
        
        # 标题：名称和等级
        title_text = f"{self.card_data.name} Lv.{self.card_data.level}"
        title_surface = self.title_font.render(title_text, True, 
                                               COLORS.get(self.card_data.rarity, (255, 255, 255)))
        lines.append(('title', title_surface))
        
        # 稀有度
        rarity_names = {"A": "SSR", "B": "SR", "C": "R", "D": "N"}
        rarity_text = f"稀有度: {rarity_names.get(self.card_data.rarity, self.card_data.rarity)}"
        rarity_surface = self.info_font.render(rarity_text, True, (200, 200, 200))
        lines.append(('info', rarity_surface))
        
        # 属性：ATK/HP
        stats_text = f"ATK: {self.card_data.atk}  |  HP: {self.card_data.hp}"
        stats_surface = self.info_font.render(stats_text, True, (255, 215, 100))
        lines.append(('info', stats_surface))
        
        # 分隔线
        lines.append(('separator', None))
        
        # 特性
        if self.card_data.traits:
            traits_text = "特性: " + ", ".join(self.card_data.traits)
            # 如果特性太长，分行
            if len(traits_text) > 30:
                lines.append(('desc', self.desc_font.render("特性:", True, (150, 255, 150))))
                for trait in self.card_data.traits:
                    trait_surface = self.desc_font.render(f"  • {trait}", True, (150, 255, 150))
                    lines.append(('desc', trait_surface))
            else:
                traits_surface = self.desc_font.render(traits_text, True, (150, 255, 150))
                lines.append(('desc', traits_surface))
        
        # 描述（可能需要分行）
        if self.card_data.description:
            lines.append(('separator', None))
            desc_lines = self._wrap_text(self.card_data.description, 
                                        self.desc_font, 
                                        int(300 * UI_SCALE))
            for desc_line in desc_lines:
                desc_surface = self.desc_font.render(desc_line, True, (220, 220, 220))
                lines.append(('desc', desc_surface))
        
        # 计算尺寸
        max_width = max((s.get_width() for t, s in lines if s), default=0)
        total_height = 0
        
        for line_type, surface in lines:
            if line_type == 'separator':
                total_height += int(10 * UI_SCALE)
            elif surface:
                total_height += surface.get_height() + self.line_spacing
        
        # 创建surface
        width = max_width + self.padding * 2
        height = total_height + self.padding * 2
        
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # 背景
        self.surface.fill((20, 20, 30, 240))
        
        # 边框
        border_color = COLORS.get(self.card_data.rarity, (150, 150, 150))
        pygame.draw.rect(self.surface, border_color, 
                        (0, 0, width, height), 
                        self.border_width,
                        border_radius=max(5, int(10 * UI_SCALE)))
        
        # 绘制文本
        y = self.padding
        for line_type, surface in lines:
            if line_type == 'separator':
                # 分隔线
                sep_y = y + int(5 * UI_SCALE)
                pygame.draw.line(self.surface, (100, 100, 100),
                               (self.padding, sep_y),
                               (width - self.padding, sep_y), 1)
                y += int(10 * UI_SCALE)
            elif surface:
                self.surface.blit(surface, (self.padding, y))
                y += surface.get_height() + self.line_spacing
    
    def _wrap_text(self, text, font, max_width):
        """文本换行"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = font.render(test_line, True, (255, 255, 255))
            
            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def draw(self, screen):
        """绘制提示框"""
        if not self.visible or not self.surface:
            return
        
        # 调整位置，确保不超出屏幕
        x, y = self.position
        offset_x = int(15 * UI_SCALE)
        offset_y = int(15 * UI_SCALE)
        
        # 默认显示在鼠标右下方
        draw_x = x + offset_x
        draw_y = y + offset_y
        
        # 检查右边界
        if draw_x + self.surface.get_width() > screen.get_width():
            draw_x = x - self.surface.get_width() - offset_x
        
        # 检查下边界
        if draw_y + self.surface.get_height() > screen.get_height():
            draw_y = y - self.surface.get_height() - offset_y
        
        # 绘制阴影
        shadow_offset = max(2, int(4 * UI_SCALE))
        shadow = pygame.Surface((self.surface.get_width(), self.surface.get_height()), 
                               pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 100))
        screen.blit(shadow, (draw_x + shadow_offset, draw_y + shadow_offset))
        
        # 绘制提示框
        screen.blit(self.surface, (draw_x, draw_y))


# 全局提示框实例
_tooltip = None

def get_tooltip():
    """获取全局提示框实例"""
    global _tooltip
    if _tooltip is None:
        _tooltip = CardTooltip()
        _tooltip.start_monitoring()
    return _tooltip