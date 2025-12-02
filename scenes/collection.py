"""图鉴场景"""
import pygame
import os
from scenes.base.base_scene import BaseScene
from ui.button import Button
from ui.panel import Panel
from ui.scroll_view import ScrollView
from utils.inventory import get_inventory
from config import *

RARITY_SEQUENCE = [
    "SSS", "SS+", "SS", "S+", "S",
    "A+", "A", "B+", "B", "C+", "C", "D"
]

# 卡牌布局参数
card_width = int(216 * UI_SCALE)
card_height = int(324 * UI_SCALE)
cards_per_row = 6
card_spacing = int(30 * UI_SCALE)

"""图鉴卡牌显示类"""
class CollectionCard:
    _image_cache = {}
    
    def __init__(self, card_data, x, y, width, height):
        self.data = card_data
        self.rect = pygame.Rect(x, y, width, height)
        self.is_hovered = False

        from utils.card_database import get_card_database
        db = get_card_database()
        self.card_data = db.get_card_by_path(card_data.get('path'))

        self.load_image() # 加载图片
        
    def load_image(self):
        """加载卡牌图片（使用缓存）"""
        try:
            if os.path.exists(self.data["path"]):
                # 使用缓存避免重复加载和缩放
                cache_key = (self.data["path"], self.rect.width, self.rect.height)
                if cache_key not in CollectionCard._image_cache:
                    # 首次加载时缓存
                    original = pygame.image.load(self.data["path"])
                    scaled = pygame.transform.smoothscale(
                        original, (self.rect.width, self.rect.height)
                    )
                    CollectionCard._image_cache[cache_key] = scaled.convert_alpha()
                
                self.image = CollectionCard._image_cache[cache_key]
            else:
                self.image = self.create_placeholder()
        except:
            self.image = self.create_placeholder()
        
        if not hasattr(self.image, 'get_alpha'):
            self.image = self.image.convert_alpha()
    
    def create_placeholder(self):
        """创建占位符"""
        surface = pygame.Surface((self.rect.width, self.rect.height))
        color = COLORS.get(self.data["rarity"], (100, 100, 100))
        surface.fill(color)
        
        # 边框
        border_width = max(2, int(3 * UI_SCALE))
        pygame.draw.rect(surface, (255, 255, 255), 
                        (0, 0, self.rect.width, self.rect.height), border_width)
        
        # 稀有度文字
        font = get_font(max(24, int(36 * UI_SCALE)))
        text = font.render(self.data["rarity"], True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        surface.blit(text, text_rect)
        
        return surface
    
    def update(self, mouse_pos, scroll_offset):
        """更新悬停状态"""
        adjusted_rect = self.rect.move(0, scroll_offset)
        self.is_hovered = adjusted_rect.collidepoint(mouse_pos)
    
    def draw(self, surface, offset_y=0):
        """绘制卡牌"""
        pos = (self.rect.x, self.rect.y + offset_y)
        
        surface.blit(self.image, pos) # 绘制图片
        
        # 悬停效果
        if self.is_hovered:
            hover_surface = pygame.Surface((self.rect.width, self.rect.height), 
                                          pygame.SRCALPHA)
            hover_surface.fill((255, 255, 255, 50))
            surface.blit(hover_surface, pos)
            
            # 边框高亮
            border_width = max(3, int(4 * UI_SCALE))
            border_color = COLORS.get(self.data["rarity"], (255, 255, 255))
            pygame.draw.rect(surface, border_color, 
                           (*pos, self.rect.width, self.rect.height), border_width)
        
        # 显示数量标签
        if self.data["count"] > 1:
            self.draw_count_badge(surface, pos)
    
    def draw_count_badge(self, surface, pos):
        """绘制数量标签"""
        badge_size = max(30, int(40 * UI_SCALE))
        badge_x = pos[0] + self.rect.width - badge_size - 5
        badge_y = pos[1] + 5
        
        # 圆形背景
        center = (badge_x + badge_size // 2, badge_y + badge_size // 2)
        pygame.draw.circle(surface, (0, 0, 0, 180), center, badge_size // 2)
        pygame.draw.circle(surface, (255, 215, 0), center, badge_size // 2, 2)
        
        # 数量文字
        font = get_font(int(18 * UI_SCALE))
        count_text = f"x{self.data['count']}"
        text = font.render(count_text, True, (255, 255, 255))
        text_rect = text.get_rect(center=center)
        surface.blit(text, text_rect)

"""图鉴场景"""
class CollectionScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.inventory = get_inventory() # 获取库存
        self.background = self.create_background()  # 背景
        
        # 字体
        self.title_font = get_font(max(45, int(64 * UI_SCALE)))
        self.info_font = get_font(max(30, int(40 * UI_SCALE)))
        self.small_font = get_font(max(30, int(40 * UI_SCALE)))
        self.create_ui() # 创建UI
        
        # 卡牌显示相关
        self.card_widgets = []
        self.selected_rarity = "全部"  # 当前选择的稀有度筛选
        
        # 标题缓存
        self._title_cache = None
        self._shadow_cache = None
        self._rebuild_title_cache()
        
        # 加载卡牌
        self.reload_cards()
    
    def create_background(self):
        """创建背景"""
        bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        bg.fill(BACKGROUND_COLOR)
        
        grid_size = int(40 * UI_SCALE)
        for x in range(0, WINDOW_WIDTH, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (0, y), (WINDOW_WIDTH, y), 1)
        
        return bg
    
    def create_ui(self):
        """创建UI组件"""
        # 统计面板
        panel_width = int(WINDOW_WIDTH * 0.25)
        panel_height = int(WINDOW_HEIGHT * 0.6)
        panel_x = int(WINDOW_WIDTH * 0.05)
        panel_y = int(WINDOW_HEIGHT * 0.15)
        
        self.stats_panel = Panel(panel_x, panel_y, panel_width, panel_height)
        
        # 滚动视图（用于显示卡牌）
        scroll_x = int(WINDOW_WIDTH * 0.35)
        scroll_y = int(WINDOW_HEIGHT * 0.15)
        scroll_width = int(WINDOW_WIDTH * 0.6)
        scroll_height = int(WINDOW_HEIGHT * 0.7)
        self.scroll_view = ScrollView(scroll_x, scroll_y, scroll_width, scroll_height, 0)
        
        # 返回按钮
        button_width = int(200 * UI_SCALE)
        button_height = int(50 * UI_SCALE)
        
        self.back_button = Button(
            int(WINDOW_WIDTH * 0.05),
            int(WINDOW_HEIGHT * 0.05),
            button_width,
            button_height,
            "返回主菜单",
            color=(100, 150, 255),
            hover_color=(130, 180, 255),
            font_size=28,
            on_click=lambda: self.switch_to("main_menu")
        )
        
        # 筛选按钮
        filter_button_width = int(panel_width * 0.45)
        filter_button_height = int(40 * UI_SCALE)
        filter_x = panel_x
        filter_y = panel_y + panel_height + int(20 * UI_SCALE)
        filter_spacing = int(10 * UI_SCALE)
        
        self.filter_buttons = []
        filters = ["全部"] + RARITY_SEQUENCE
        
        for i, rarity in enumerate(filters):
            row = i // 2
            col = i % 2
            
            btn = Button(
                filter_x + col * (filter_button_width + filter_spacing),
                filter_y + row * (filter_button_height + filter_spacing),
                filter_button_width,
                filter_button_height,
                rarity if rarity == "全部" else f"{rarity} 级",
                color=COLORS.get(rarity, (100, 100, 100)) if rarity != "全部" else (80, 80, 100),
                hover_color=tuple(min(255, c + 30) for c in COLORS.get(rarity, (100, 100, 100))) 
                           if rarity != "全部" else (110, 110, 130),
                font_size=20,
                on_click=lambda r=rarity: self.filter_by_rarity(r)
            )
            self.filter_buttons.append(btn)
    
    def filter_by_rarity(self, rarity):
        """按稀有度筛选"""
        self.selected_rarity = rarity
        self.reload_cards()
    
    def reload_cards(self):
        """重新加载卡牌显示"""
        # 获取卡牌数据
        if self.selected_rarity == "全部":
            cards_data = self.inventory.get_unique_cards()
        else:
            cards_data = self.inventory.get_cards_by_rarity(self.selected_rarity)
        
        # 按稀有度排序
        rarity_order = {rarity: idx for idx, rarity in enumerate(RARITY_SEQUENCE)}
        cards_data.sort(key=lambda x: rarity_order.get(x["rarity"], 99))
        self.card_widgets = [] # 创建卡牌widget
        
        for i, card_data in enumerate(cards_data):
            row = i // cards_per_row
            col = i % cards_per_row
            
            x = card_spacing + col * (card_width + card_spacing)
            y = card_spacing + row * (card_height + card_spacing)
            
            card_widget = CollectionCard(card_data, x, y, card_width, card_height)
            self.card_widgets.append(card_widget)
        
        # 更新滚动视图内容高度
        if cards_data:
            total_rows = (len(cards_data) + cards_per_row - 1) // cards_per_row
            content_height = card_height + total_rows * (card_height + card_spacing) + card_spacing
        else:
            content_height = 0
        
        self.scroll_view.update_content_height(content_height)
    
    def enter(self):
        """进入场景时重新加载"""
        super().enter()
        self.inventory.load()  # 重新加载库存
        self.reload_cards()
    
    """获取鼠标悬停的卡牌数据"""
    def get_hovered_card(self, mouse_pos):
        # 检查鼠标是否在滚动视图区域内
        if not self.scroll_view.rect.collidepoint(mouse_pos):
            return None
        
        # 转换鼠标坐标到滚动内容坐标系
        local_x = mouse_pos[0] - self.scroll_view.rect.x
        local_y = mouse_pos[1] - self.scroll_view.rect.y
        
        # 遍历卡牌，考虑滚动偏移
        for card in self.card_widgets:
            # 调整卡牌矩形位置（减去滚动偏移）
            adjusted_rect = card.rect.move(0, -self.scroll_view.scroll_y)
            
            # 使用转换后的坐标检测
            if adjusted_rect.collidepoint(local_x, local_y):
                if hasattr(card, 'card_data'):
                    return card.card_data

    """处理事件"""
    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")
        
        # 滚动视图事件
        self.scroll_view.handle_event(event)
        
        # 按钮事件
        self.back_button.handle_event(event)
        for btn in self.filter_buttons:
            btn.handle_event(event)
    
    def _rebuild_title_cache(self):
        self._title_cache = self.title_font.render("卡牌图鉴", True, (255, 215, 0))
        shadow_offset = max(2, int(2 * UI_SCALE))
        self._shadow_cache = (self.title_font.render("卡牌图鉴", True, (0, 0, 0)), shadow_offset)
    
    def update(self, dt):
        """更新"""
        # 更新卡牌悬停状态
        mouse_pos = pygame.mouse.get_pos()
        
        # 考虑滚动视图的裁剪区域
        if self.scroll_view.rect.collidepoint(mouse_pos):
            # 转换鼠标坐标到滚动内容空间
            local_mouse_x = mouse_pos[0] - self.scroll_view.rect.x
            local_mouse_y = mouse_pos[1] - self.scroll_view.rect.y
            scroll_mouse_pos = (local_mouse_x, local_mouse_y)
            
            for card in self.card_widgets:
                card.update(scroll_mouse_pos, -self.scroll_view.scroll_y)
        else:
            for card in self.card_widgets:
                card.is_hovered = False
    
    def draw(self):
        """绘制场景"""
        self.screen.blit(self.background, (0, 0)) # 背景
        self.draw_title() # 标题
        self.draw_stats_panel() # 统计面板
        
        for btn in self.filter_buttons: # 筛选按钮
            btn.draw(self.screen)
        
        self.draw_cards() # 滚动视图中的卡牌
        self.back_button.draw(self.screen) # 返回按钮
    
    def draw_title(self):
        """绘制标题"""
        title_y = int(WINDOW_HEIGHT * 0.05)
        if self._title_cache and self._shadow_cache:
            shadow_text, shadow_offset = self._shadow_cache
            title_rect = self._title_cache.get_rect(center=(WINDOW_WIDTH // 2, title_y))
            shadow_rect = shadow_text.get_rect(center=(WINDOW_WIDTH // 2 + shadow_offset, title_y + shadow_offset))
            self.screen.blit(shadow_text, shadow_rect)
            self.screen.blit(self._title_cache, title_rect)
    
    def draw_stats_panel(self):
        """绘制统计面板"""
        self.stats_panel.draw(self.screen)
        
        # 获取统计数据
        stats = self.inventory.get_collection_stats()
        
        # 面板内容
        panel_x = self.stats_panel.rect.x + int(20 * UI_SCALE)
        panel_y = self.stats_panel.rect.y + int(30 * UI_SCALE)
        line_height = int(40 * UI_SCALE)
        
        # 标题
        title = self.info_font.render("收集统计", True, (255, 215, 0))
        self.screen.blit(title, (panel_x, panel_y))
        panel_y += line_height + int(40 * UI_SCALE)
        
        # 统计信息
        stats_info = [
            f"总抽卡次数: {stats['total_draws']}",
            f"收集种类: {stats['unique_cards']}",
            f"卡牌总数: {stats['total_cards']}",
            "",
            "稀有度分布:"
        ]
        
        for info in stats_info:
            text = self.small_font.render(info, True, (200, 200, 200))
            self.screen.blit(text, (panel_x, panel_y))
            panel_y += int(40 * UI_SCALE)
        
        # 稀有度统计
        for rarity in RARITY_SEQUENCE:
            count = stats['rarity_stats'].get(rarity, 0)
            color = COLORS.get(rarity, (255, 255, 255))
            
            text = self.small_font.render(f"  {rarity}: {count} 张", True, color)
            self.screen.blit(text, (panel_x, panel_y))
            panel_y += int(40 * UI_SCALE)
    
    def draw_cards(self):
        """绘制卡牌网格"""
        surface, offset_y = self.scroll_view.begin_draw()
        
        if not self.card_widgets:
            # 没有卡牌时显示提示
            no_card_text = self.info_font.render(
                "还没有收集到卡牌哦~姆Q", True, (150, 150, 150)
            )
            text_rect = no_card_text.get_rect(
                center=(self.scroll_view.rect.width // 2, 
                       self.scroll_view.rect.height // 2)
            )
            surface.blit(no_card_text, text_rect)
        else:
            # 绘制所有卡牌
            for card in self.card_widgets:
                card.draw(surface, offset_y)
        
        self.scroll_view.end_draw(self.screen)
        