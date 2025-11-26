"""抽卡菜单场景 - 卡池选择中介页面"""
import pygame
from config import *
from scenes.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.button import Button
from ui.panel import Panel
from ui.scroll_view import ScrollView


# 卡池配置列表
GACHA_POOLS = [
    {"id": "normal", "name": "常规卡池", "bg_type": "gacha_normal", "description": "常驻卡池，标准概率"},
    {"id": "activity", "name": "活动卡池", "bg_type": "gacha_activity", "description": "限时活动卡池，提高概率"},
    {"id": "special", "name": "特别卡池", "bg_type": "gacha_special", "description": "特别卡池，高级卡牌"},
]


class GachaMenuScene(BaseScene):
    """抽卡菜单场景"""
    
    def __init__(self, screen):
        super().__init__(screen)
        
        # 当前选中的卡池索引
        self.selected_pool_index = 0
        
        # 创建视差背景（使用第一个卡池的背景）
        self.background = self._create_background_for_pool(self.selected_pool_index)
        
        # 字体
        self.title_font = get_font(max(32, int(64 * UI_SCALE)))
        self.pool_name_font = get_font(max(20, int(36 * UI_SCALE)))
        self.desc_font = get_font(max(12, int(24 * UI_SCALE)))
        
        # 创建左侧滚动面板
        self._create_pool_panel()
        
        # 创建右侧按钮
        self._create_buttons()
        
        # 卡池选项按钮列表
        self.pool_buttons = []
        self._create_pool_buttons()
    
    def _create_background_for_pool(self, pool_index):
        """根据卡池索引创建对应的视差背景"""
        if 0 <= pool_index < len(GACHA_POOLS):
            bg_type = GACHA_POOLS[pool_index]["bg_type"]
        else:
            bg_type = "gacha_menu"
        return ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, bg_type)
    
    def _create_pool_panel(self):
        """创建左侧卡池选择面板"""
        panel_width = int(WINDOW_WIDTH * 0.3)
        panel_height = int(WINDOW_HEIGHT * 0.7)
        panel_x = int(WINDOW_WIDTH * 0.05)
        panel_y = int(WINDOW_HEIGHT * 0.15)
        
        # 创建半透明面板
        self.pool_panel = Panel(
            panel_x, panel_y, panel_width, panel_height,
            color=(30, 30, 50),
            alpha=180,
            border_color=(100, 150, 255),
            border_width=2
        )
        
        # 创建滚动视图
        content_height = len(GACHA_POOLS) * int(120 * UI_SCALE) + int(20 * UI_SCALE)
        self.scroll_view = ScrollView(
            panel_x + int(10 * UI_SCALE),
            panel_y + int(10 * UI_SCALE),
            panel_width - int(20 * UI_SCALE),
            panel_height - int(20 * UI_SCALE),
            content_height
        )
    
    def _create_pool_buttons(self):
        """创建卡池选项按钮"""
        self.pool_buttons = []
        
        button_width = int(WINDOW_WIDTH * 0.25)
        button_height = int(100 * UI_SCALE)
        button_spacing = int(20 * UI_SCALE)
        start_x = int(15 * UI_SCALE)
        start_y = int(15 * UI_SCALE)
        
        for i, pool in enumerate(GACHA_POOLS):
            btn = Button(
                start_x,
                start_y + i * (button_height + button_spacing),
                button_width,
                button_height,
                pool["name"],
                color=(60, 80, 120) if i != self.selected_pool_index else (100, 150, 255),
                hover_color=(80, 120, 180),
                text_color=(255, 255, 255),
                font_size=32,
                on_click=lambda idx=i: self._select_pool(idx)
            )
            self.pool_buttons.append(btn)
    
    def _create_buttons(self):
        """创建右侧功能按钮"""
        button_width = int(300 * UI_SCALE)
        button_height = int(90 * UI_SCALE)
        button_x = int(WINDOW_WIDTH * 0.7)
        
        # 进入抽卡按钮
        self.enter_gacha_button = Button(
            button_x,
            int(WINDOW_HEIGHT * 0.4),
            button_width, button_height,
            "进入抽卡",
            color=(255, 140, 0), hover_color=(255, 180, 50),
            on_click=self._enter_gacha
        )
        
        # 返回按钮
        self.back_button = Button(
            button_x,
            int(WINDOW_HEIGHT * 0.6),
            button_width, button_height,
            "返回主菜单",
            color=(100, 150, 255), hover_color=(130, 180, 255),
            on_click=lambda: self.switch_to("main_menu")
        )
    
    def _select_pool(self, index):
        """选择卡池"""
        if 0 <= index < len(GACHA_POOLS):
            self.selected_pool_index = index
            # 更新背景
            self.background = self._create_background_for_pool(index)
            # 更新按钮颜色以显示选中状态
            self._update_pool_button_colors()
    
    def _update_pool_button_colors(self):
        """更新卡池按钮颜色以反映选中状态"""
        for i, btn in enumerate(self.pool_buttons):
            if i == self.selected_pool_index:
                btn.color = (100, 150, 255)
            else:
                btn.color = (60, 80, 120)
    
    def _enter_gacha(self):
        """进入抽卡场景"""
        self.switch_to("gacha")
    
    def handle_event(self, event):
        """处理事件"""
        super().handle_event(event)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")
        
        # 更新视差背景
        if event.type == pygame.MOUSEMOTION:
            self.background.update_mouse_position(event.pos)
        
        # 滚动视图事件
        self.scroll_view.handle_event(event)
        
        # 卡池按钮事件（需要考虑滚动偏移）
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            mouse_pos = event.pos
            # 检查是否在滚动视图区域内
            if self.scroll_view.rect.collidepoint(mouse_pos):
                # 调整鼠标位置以考虑滚动偏移
                adjusted_pos = (
                    mouse_pos[0] - self.scroll_view.rect.x,
                    mouse_pos[1] - self.scroll_view.rect.y + self.scroll_view.scroll_y
                )
                # 创建调整后的事件
                event_kwargs = {'pos': adjusted_pos}
                if event.type == pygame.MOUSEBUTTONDOWN:
                    event_kwargs['button'] = event.button
                adjusted_event = pygame.event.Event(event.type, **event_kwargs)
                for btn in self.pool_buttons:
                    btn.handle_event(adjusted_event)
        
        # 功能按钮事件
        self.enter_gacha_button.handle_event(event)
        self.back_button.handle_event(event)
    
    def update(self, dt):
        """更新场景"""
        self.background.update(dt)
    
    def draw(self):
        """绘制场景"""
        # 绘制背景
        self.background.draw(self.screen)
        
        # 绘制标题
        self._draw_title()
        
        # 绘制左侧面板
        self.pool_panel.draw(self.screen)
        
        # 绘制滚动视图中的卡池按钮
        self._draw_pool_list()
        
        # 绘制右侧信息和按钮
        self._draw_pool_info()
        self.enter_gacha_button.draw(self.screen)
        self.back_button.draw(self.screen)
    
    def _draw_title(self):
        """绘制标题"""
        title_y = int(WINDOW_HEIGHT * 0.06)
        title_text = self.title_font.render("选择卡池", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, title_y))
        
        # 标题阴影
        shadow_offset = max(2, int(2 * UI_SCALE))
        shadow_text = self.title_font.render("选择卡池", True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(center=(
            WINDOW_WIDTH // 2 + shadow_offset,
            title_y + shadow_offset
        ))
        
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
    
    def _draw_pool_list(self):
        """绘制卡池列表"""
        surface, scroll_offset = self.scroll_view.begin_draw()
        
        # 在滚动视图的surface上绘制按钮
        for btn in self.pool_buttons:
            # 调整按钮位置以考虑滚动
            original_y = btn.rect.y
            btn.rect.y = original_y + scroll_offset
            btn.text_rect.centery = btn.rect.centery
            
            btn.draw(surface)
            
            # 恢复按钮位置
            btn.rect.y = original_y
            btn.text_rect.centery = btn.rect.centery
        
        self.scroll_view.end_draw(self.screen)
    
    def _draw_pool_info(self):
        """绘制当前选中卡池的信息"""
        if 0 <= self.selected_pool_index < len(GACHA_POOLS):
            pool = GACHA_POOLS[self.selected_pool_index]
            
            info_x = int(WINDOW_WIDTH * 0.7)
            info_y = int(WINDOW_HEIGHT * 0.2)
            
            # 卡池名称
            name_text = self.pool_name_font.render(pool["name"], True, (255, 215, 0))
            name_rect = name_text.get_rect(center=(info_x + int(150 * UI_SCALE), info_y))
            self.screen.blit(name_text, name_rect)
            
            # 卡池描述
            desc_text = self.desc_font.render(pool["description"], True, (200, 200, 200))
            desc_rect = desc_text.get_rect(center=(info_x + int(150 * UI_SCALE), info_y + int(50 * UI_SCALE)))
            self.screen.blit(desc_text, desc_rect)
