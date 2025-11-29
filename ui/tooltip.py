"""
卡牌信息提示框
当鼠标悬停在卡牌上时显示详细信息
"""
import pygame
import time
from config import *

"""卡牌提示框类"""
class CardTooltip:
    def __init__(self):
        # 延迟显示
        self.hover_start_time = None
        self.show_delay = 0.1

        self.visible = False
        self.card_data = None
        self.position = (0, 0)
        self.surface = None
        
        # 提示框样式
        self.padding = int(20 * UI_SCALE)
        self.line_spacing = int(2 * UI_SCALE)
        self.border_width = max(3, int(3 * UI_SCALE))
        
        # 字体
        self.stat_font = get_font(int(64 * UI_SCALE)) # ATK / HP
        self.title_font = get_font(int(35 * UI_SCALE)) # 名称
        self.info_font = get_font(int(25 * UI_SCALE)) # 其他信息
        self.desc_font = get_font(int(25 * UI_SCALE)) # 描述
        
    """显示提示框"""  
    def show(self, card_data, mouse_pos):
        if card_data is None:
            self.hide()
            return
        
        current_time = time.time()
        
        # 如果是新卡牌，重置计时
        if self.card_data != card_data:
            self.hover_start_time = current_time
            self.card_data = card_data
            self.visible = False
        
        # 更新鼠标位置
        self.position = mouse_pos
        
        # 检查是否达到延迟时间
        if self.hover_start_time and current_time - self.hover_start_time >= self.show_delay:
            if not self.visible:
                self._create_surface()
            self.visible = True
    
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
        
        # 顶部大号 ATK / HP
        atk_surface = self.stat_font.render(f"{self.card_data.atk}", True, (215, 50, 50))
        hp_surface = self.stat_font.render(f"{self.card_data.hp}", True, (50, 215, 100))
        top_section_height = max(atk_surface.get_height(), hp_surface.get_height())
        stat_gap_min = int(30 * UI_SCALE)
        
        lines = [] # 下方信息
        title_text = f"{self.card_data.name}" # 名称
        title_surface = self.title_font.render(title_text, True, COLORS.get(self.card_data.rarity, (255, 255, 255)))
        lines.append(('title', title_surface))
        
        # 稀有度
        rarity_text = f"LV: {self.card_data.rarity}"
        rarity_surface = self.info_font.render(rarity_text, True, (200, 200, 200))
        lines.append(('info', rarity_surface))
        
        # 属性：CD
        cd_text = f"CD: {self.card_data.cd}"
        lines.append(('info', self.info_font.render(cd_text, True, (255, 215, 100))))
        
        # 特性
        if self.card_data.traits:
            lines.append(('separator', None))
            traits_text = f"{self.card_data.traits}"
            traits_surface = self.desc_font.render(traits_text, True, (150, 255, 150))
            lines.append(('desc', traits_surface))
        
        # 描述（10字符换行）
        if self.card_data.description:
            lines.append(('separator', None))
            desc_text = self.card_data.description
            for i in range(0, len(desc_text), 10):
                line_text = desc_text[i:i+10]
                desc_surface = self.desc_font.render(line_text, True, (220, 220, 220))
                lines.append(('desc', desc_surface))
        
        # 计算尺寸
        max_width = max((s.get_width() for t, s in lines if s), default=0)
        stats_required_width = self.padding * 2 + atk_surface.get_width() + hp_surface.get_width() + stat_gap_min
        max_width = max(max_width, stats_required_width - self.padding * 2)
        total_height = 0
        
        separator_height = int(10 * UI_SCALE)
        for line_type, surface in lines:
            if line_type == 'separator':
                total_height += separator_height
            elif surface:
                total_height += surface.get_height() + self.line_spacing
        
        # 创建surface
        width = max_width + self.padding * 2
        line_padding = int(4 * UI_SCALE)
        post_line_spacing = int(8 * UI_SCALE)
        height = (
            self.padding * 2
            + top_section_height
            + line_padding
            + post_line_spacing
            + total_height
        )
        
        self.surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # 背景
        self.surface.fill((20, 20, 30, 180))
        
        # 边框
        border_color = COLORS.get(self.card_data.rarity, (150, 150, 150))
        pygame.draw.rect(self.surface, border_color, 
                        (0, 0, width, height), 
                        self.border_width,
                        border_radius=max(5, int(10 * UI_SCALE)))
        
        # 绘制顶部 ATK / HP
        y = self.padding
        self.surface.blit(atk_surface, (self.padding, y))
        hp_x = width - self.padding - hp_surface.get_width()
        self.surface.blit(hp_surface, (hp_x, y))
        y += top_section_height
        sep_y = y + line_padding
        pygame.draw.line(
            self.surface,
            (100, 100, 100),
            (self.padding, sep_y),
            (width - self.padding, sep_y),
            1
        )
        y = sep_y + post_line_spacing
        
        # 绘制文本
        for line_type, surface in lines:
            if line_type == 'separator':
                pygame.draw.line(
                    self.surface,
                    (60, 60, 60),
                    (self.padding, y),
                    (width - self.padding, y),
                    1
                )
                y += separator_height
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
        
        return lines if lines else [text]
    
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

    def stop_monitoring(self):
        """停止监控，清理资源"""
        self.hide()


# 全局提示框实例
_tooltip = None

def get_tooltip():
    """获取全局提示框实例"""
    global _tooltip
    if _tooltip is None:
        _tooltip = CardTooltip()
    return _tooltip
