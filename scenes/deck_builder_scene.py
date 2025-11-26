"""
卡组配置场景
"""
import pygame
import os
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.panel import Panel
from ui.scroll_view import ScrollView
from utils.inventory import get_inventory
from utils.deck_manager import get_deck_manager
from config import *

# 左侧卡组面板
deck_panel_width = int(WINDOW_WIDTH * 0.35)
deck_panel_height = int(WINDOW_HEIGHT * 0.9)
deck_panel_x = int(WINDOW_WIDTH * 0.05)
deck_panel_y = int(WINDOW_HEIGHT * 0.05)
# 滚动视图（右侧，用于显示收藏的卡牌）
scroll_x = int(WINDOW_WIDTH * 0.45)
scroll_y = int(WINDOW_HEIGHT * 0.15)
scroll_width = int(WINDOW_WIDTH * 0.5)
scroll_height = int(WINDOW_HEIGHT * 0.7)
# 创建12个卡组槽位（2列6行）
slot_width = int(216 * UI_SCALE)
slot_height = int(324 * UI_SCALE)
slot_spacing = int(30 * UI_SCALE)
cols = 3
rows = 4
# 卡牌widget设置
card_width = int(216 * UI_SCALE)
card_height = int(324 * UI_SCALE)
card_spacing = int(30 * UI_SCALE)
cards_per_row = 5

"""可拖拽的卡牌类"""
class DraggableCard:
    # 图片缓存 避免重复加载和缩放
    _image_cache = {}  # key: (path, width, height), value: scaled surface
    
    def __init__(self, card_data, x, y, width, height, source="collection"):
        self.data = card_data
        self.rect = pygame.Rect(x, y, width, height)
        self.original_pos = (x, y)  # 原始位置
        self.source = source
        
        self.is_hovered = False
        self.is_dragging = False
        self.drag_offset = (0, 0)

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
                if cache_key not in DraggableCard._image_cache:
                    # 首次加载时缓存
                    original = pygame.image.load(self.data["path"])
                    scaled = pygame.transform.smoothscale(
                        original, (self.rect.width, self.rect.height)
                    )
                    DraggableCard._image_cache[cache_key] = scaled.convert_alpha()
                
                self.image = DraggableCard._image_cache[cache_key]
            else:
                self.image = self.create_placeholder()
        except:
            self.image = self.create_placeholder()
        
        if not hasattr(self.image, 'get_alpha'):
            self.image = self.image.convert_alpha()
    
    def create_placeholder(self):
        """创建占位符"""
        surface = pygame.Surface((self.rect.width, self.rect.height))
        color = COLORS.get(self.data.get("rarity", "D"), (100, 100, 100))
        surface.fill(color)
        
        border_width = max(2, int(3 * UI_SCALE))
        pygame.draw.rect(surface, (255, 255, 255), 
                        (0, 0, self.rect.width, self.rect.height), border_width)
        
        font = get_font(max(20, int(30 * UI_SCALE)))
        text = font.render(self.data.get("rarity", "?"), True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        surface.blit(text, text_rect)
        
        return surface
    
    def start_drag(self, mouse_pos):
        """开始拖拽"""
        self.is_dragging = True
        self.drag_offset = (
            mouse_pos[0] - self.rect.x,
            mouse_pos[1] - self.rect.y
        )
    
    def update_drag(self, mouse_pos):
        """更新拖拽位置"""
        if self.is_dragging:
            self.rect.x = mouse_pos[0] - self.drag_offset[0]
            self.rect.y = mouse_pos[1] - self.drag_offset[1]
    
    def end_drag(self):
        """结束拖拽"""
        self.is_dragging = False
    
    def reset_position(self):
        """重置到原始位置"""
        self.rect.x, self.rect.y = self.original_pos
    
    def draw(self, surface):
        """绘制卡牌"""
        surface.blit(self.image, self.rect) # 绘制图片
        
        # 拖拽时的半透明效果
        if self.is_dragging:
            overlay = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 150))
            surface.blit(overlay, self.rect)
        
        # 悬停或拖拽时的边框
        if self.is_hovered or self.is_dragging:
            border_width = max(3, int(4 * UI_SCALE))
            border_color = COLORS.get(self.data.get("rarity", "D"), (255, 255, 255))
            pygame.draw.rect(surface, border_color, self.rect, border_width)

class DeckSlot:
    """卡组槽位类"""
    # 图片缓存 避免重复加载和缩放
    _image_cache = {}  # key: (path, width, height), value: scaled surface
    
    def __init__(self, x, y, width, height, index):
        self.rect = pygame.Rect(x, y, width, height)
        self.index = index
        self.card = None  # 当前槽位的卡牌数据
        self.is_hovered = False
    
    def set_card(self, card_data):
        """设置卡牌"""
        self.card = card_data
    
    def remove_card(self):
        """移除卡牌"""
        card = self.card
        self.card = None
        return card
    
    def has_card(self):
        """是否有卡牌"""
        return self.card is not None
    
    def draw(self, screen):
        """绘制槽位"""
        # 槽位背景
        if self.card: # 绘制卡牌
            if os.path.exists(self.card["path"]):
                # 使用缓存避免重复加载和缩放
                cache_key = (self.card["path"], self.rect.width, self.rect.height)
                if cache_key not in DeckSlot._image_cache:
                    # 首次加载时缓存
                    img = pygame.image.load(self.card["path"])
                    img = pygame.transform.smoothscale(img, (self.rect.width, self.rect.height))
                    DeckSlot._image_cache[cache_key] = img
                
                screen.blit(DeckSlot._image_cache[cache_key], self.rect)
            else:
                self.draw_placeholder(screen)
            
            # 边框
            border_color = COLORS.get(self.card.get("rarity", "D"), (255, 255, 255))
            border_width = max(2, int(3 * UI_SCALE))
            pygame.draw.rect(screen, border_color, self.rect, border_width)
        else:
            # 空槽位
            slot_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            alpha = 120 if self.is_hovered else 60
            slot_surface.fill((100, 100, 100, alpha))
            
            border_color = (200, 200, 200) if self.is_hovered else (150, 150, 150)
            border_width = max(2, int(3 * UI_SCALE))
            pygame.draw.rect(slot_surface, border_color, 
                           (0, 0, self.rect.width, self.rect.height), 
                           border_width, border_radius=max(5, int(8 * UI_SCALE)))
            
            screen.blit(slot_surface, self.rect)
            
            # 槽位编号
            font = get_font(max(16, int(24 * UI_SCALE)))
            text = font.render(str(self.index + 1), True, (180, 180, 180))
            text_rect = text.get_rect(center=self.rect.center)
            screen.blit(text, text_rect)
    
    def draw_placeholder(self, screen):
        """绘制占位符卡牌"""
        color = COLORS.get(self.card.get("rarity", "D"), (100, 100, 100))
        pygame.draw.rect(screen, color, self.rect)
        
        font = get_font(max(20, int(30 * UI_SCALE)))
        text = font.render(self.card.get("rarity", "?"), True, (255, 255, 255))
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

"""卡组配置场景"""
class DeckBuilderScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.inventory = get_inventory() # 获取库存
        self.deck_manager = get_deck_manager() # 获取卡组管理器
        self.background = self.create_background() # 背景
        
        # 字体
        self.title_font = get_font(max(32, int(64 * UI_SCALE)))
        self.info_font = get_font(max(14, int(24 * UI_SCALE)))
        self.small_font = get_font(max(12, int(18 * UI_SCALE)))
        
        self.deck_slots = [] # 卡组槽位（12个）
        self.collection_cards = [] # 收藏卡牌列表
        
        # 拖拽相关
        self.dragging_card = None
        self.drag_source_index = None
        
        self.create_ui() # 创建UI
        self.reload_cards() # 加载卡牌
    
    def create_background(self):
        """创建背景"""
        bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        bg.fill(BACKGROUND_COLOR)
        
        grid_size = max(20, int(40 * UI_SCALE))
        for x in range(0, WINDOW_WIDTH, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, grid_size):
            pygame.draw.line(bg, (40, 40, 60), (0, y), (WINDOW_WIDTH, y), 1)
        
        return bg

    """创建UI组件"""
    def create_ui(self):
        self.deck_panel = Panel(deck_panel_x, deck_panel_y, deck_panel_width, deck_panel_height)

        total_width = cols * slot_width + (cols - 1) * slot_spacing
        total_height = rows * slot_height + (rows - 1) * slot_spacing
        
        start_x = deck_panel_x + (deck_panel_width - total_width) // 2
        start_y = deck_panel_y + int(50 * UI_SCALE)
        
        for i in range(12):
            row = i // cols
            col = i % cols
            x = start_x + col * (slot_width + slot_spacing)
            y = start_y + row * (slot_height + slot_spacing)
            
            slot = DeckSlot(x, y, slot_width, slot_height, i)
            self.deck_slots.append(slot)
        
        self.scroll_view = ScrollView(scroll_x, scroll_y, scroll_width, scroll_height, 0)
        
        # 按钮
        button_width = int(200 * UI_SCALE)
        button_height = int(75 * UI_SCALE)
        button_spacing = int(30 * UI_SCALE)
        
        # 保存按钮
        self.save_button = Button(
            deck_panel_x,
            int(WINDOW_HEIGHT * 0.95),
            button_width,
            button_height,
            "保存卡组",
            color=(100, 200, 100),
            hover_color=(130, 230, 130),
            font_size=24,
            on_click=self.save_deck
        )
        
        # 清空按钮
        self.clear_button = Button(
            deck_panel_x + button_width + button_spacing,
            int(WINDOW_HEIGHT * 0.95),
            button_width,
            button_height,
            "清空卡组",
            color=(200, 100, 100),
            hover_color=(230, 130, 130),
            font_size=24,
            on_click=self.clear_deck
        )
        
        # 返回按钮
        self.back_button = Button(
            int(WINDOW_WIDTH * 0.85),
            int(WINDOW_HEIGHT * 0.92),
            button_width,
            button_height,
            "返回菜单",
            color=(100, 100, 100),
            hover_color=(130, 130, 130),
            font_size=24,
            on_click=lambda: self.switch_to("main_menu")
        )
    
    """重新加载卡牌"""
    def reload_cards(self):
        deck_data = self.deck_manager.get_deck()
        for i, card_data in enumerate(deck_data):
            if i < len(self.deck_slots):
                self.deck_slots[i].set_card(card_data)
        
        collection_data = self.inventory.get_unique_cards() # 加载收藏的卡牌
        
        # 按稀有度排序
        rarity_order = {"SSS": 0, "SS": 1, "S": 2, "A": 3, "B": 4, "C": 5, "D": 6}
        collection_data.sort(key=lambda x: (rarity_order.get(x["rarity"], 99)))
        
        # 创建卡牌widget
        self.collection_cards = []
        for i, card_data in enumerate(collection_data):
            row = i // cards_per_row
            col = i % cards_per_row
            
            x = card_spacing + col * (card_width + card_spacing)
            y = card_spacing + row * (card_height + card_spacing)
            
            card_widget = DraggableCard(card_data, x, y, card_width, card_height, "collection")
            self.collection_cards.append(card_widget)
        
        # 更新滚动视图高度
        if collection_data:
            total_rows = (len(collection_data) + cards_per_row - 1) // cards_per_row
            content_height = card_spacing + total_rows * (card_height + card_spacing) + card_spacing
        else:
            content_height = 0
        
        self.scroll_view.update_content_height(content_height)
    
    def save_deck(self):
        """保存卡组"""
        self.deck_manager.clear() # 清空卡组管理器
        
        # 添加所有槽位中的卡牌
        for slot in self.deck_slots:
            if slot.has_card():
                card = slot.card
                self.deck_manager.add_card(card["path"], card["rarity"])
        
        # 保存到文件
        if self.deck_manager.save():
            print("✔卡组已保存")
    
    def clear_deck(self):
        """清空卡组"""
        for slot in self.deck_slots:
            slot.remove_card()
        print("✔卡组已清空")
    
    def enter(self):
        """进入场景时重新加载"""
        super().enter()
        self.inventory.load()
        self.deck_manager.load()
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
        for card in self.collection_cards:
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
        
        # 鼠标事件
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # 左键
            mouse_pos = event.pos
            
            # 检查是否点击收藏卡牌（在滚动视图内）
            if self.scroll_view.rect.collidepoint(mouse_pos):
                local_mouse_x = mouse_pos[0] - self.scroll_view.rect.x
                local_mouse_y = mouse_pos[1] - self.scroll_view.rect.y + self.scroll_view.scroll_y
                local_mouse_pos = (local_mouse_x, local_mouse_y)
                
                for card in self.collection_cards:
                    if card.rect.collidepoint(local_mouse_pos):
                        # 开始拖拽
                        self.dragging_card = DraggableCard(
                            card.data,
                            mouse_pos[0] - card.rect.width // 2,
                            mouse_pos[1] - card.rect.height // 2,
                            int(120 * UI_SCALE),
                            int(160 * UI_SCALE),
                            "collection"
                        )
                        self.dragging_card.start_drag(mouse_pos)
                        break
            
            # 检查是否点击卡组槽位中的卡牌
            for i, slot in enumerate(self.deck_slots):
                if slot.rect.collidepoint(mouse_pos) and slot.has_card():
                    # 从卡组中拖出
                    self.dragging_card = DraggableCard(
                        slot.card,
                        mouse_pos[0] - slot.rect.width // 2,
                        mouse_pos[1] - slot.rect.height // 2,
                        slot.rect.width,
                        slot.rect.height,
                        "deck"
                    )
                    self.dragging_card.start_drag(mouse_pos)
                    self.drag_source_index = i
                    slot.remove_card()  # 移除槽位中的卡牌
                    break
        
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            
            # 更新拖拽
            if self.dragging_card:
                self.dragging_card.update_drag(mouse_pos)
            
            # 更新槽位悬停
            for slot in self.deck_slots:
                slot.is_hovered = slot.rect.collidepoint(mouse_pos)
            
            # 更新收藏卡牌悬停
            if self.scroll_view.rect.collidepoint(mouse_pos) and not self.dragging_card:
                local_mouse_x = mouse_pos[0] - self.scroll_view.rect.x
                local_mouse_y = mouse_pos[1] - self.scroll_view.rect.y + self.scroll_view.scroll_y
                local_mouse_pos = (local_mouse_x, local_mouse_y)
                
                for card in self.collection_cards:
                    card.is_hovered = card.rect.collidepoint(local_mouse_pos)
            else:
                for card in self.collection_cards:
                    card.is_hovered = False
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  # 左键释放
            if self.dragging_card:
                mouse_pos = event.pos
                dropped = False
                
                # 检查是否放置到卡组槽位
                for slot in self.deck_slots:
                    if slot.rect.collidepoint(mouse_pos):
                        # 放置卡牌
                        if slot.has_card(): # 槽位已有卡牌，交换
                            old_card = slot.remove_card()
                            slot.set_card(self.dragging_card.data)
                            if self.drag_source_index is not None:
                                self.deck_slots[self.drag_source_index].set_card(old_card) # 如果拖拽来源是卡组，将旧卡牌放回
                        else:
                            slot.set_card(self.dragging_card.data) # 空槽位，直接放置
                        
                        dropped = True
                        break
                
                # 如果没有放置成功且来源是卡组，放回原位
                if not dropped and self.drag_source_index is not None:
                    self.deck_slots[self.drag_source_index].set_card(self.dragging_card.data)
                
                # 结束拖拽
                self.dragging_card = None
                self.drag_source_index = None
        
        # 按钮事件
        self.save_button.handle_event(event)
        self.clear_button.handle_event(event)
        self.back_button.handle_event(event)
    
    """更新"""
    def update(self, dt):
        pass

    """绘制场景"""
    def draw(self):
        self.screen.blit(self.background, (0, 0)) # 背景
        self.draw_title() # 标题
        self.deck_panel.draw(self.screen) # 卡组面板
        
        # 卡组标题
        deck_title = self.info_font.render("我的卡组", True, (255, 215, 0))
        deck_title_pos = (self.deck_panel.rect.x + int(20 * UI_SCALE), 
                         self.deck_panel.rect.y + int(15 * UI_SCALE))
        self.screen.blit(deck_title, deck_title_pos)
        
        # 卡组计数
        deck_count = len([s for s in self.deck_slots if s.has_card()])
        count_text = self.small_font.render(f"{deck_count}/12", True, (200, 200, 200))
        count_pos = (self.deck_panel.rect.right - int(80 * UI_SCALE), 
                    self.deck_panel.rect.y + int(15 * UI_SCALE))
        self.screen.blit(count_text, count_pos)
        
        # 卡组槽位
        for slot in self.deck_slots:
            slot.draw(self.screen)
        
        # 收藏标题
        collection_title = self.info_font.render("卡牌收藏", True, (255, 215, 0))
        collection_title_pos = (self.scroll_view.rect.x, 
                               self.scroll_view.rect.y - int(35 * UI_SCALE))
        self.screen.blit(collection_title, collection_title_pos)
        
        # 滚动视图中的收藏卡牌
        self.draw_collection()
        
        # 按钮
        self.save_button.draw(self.screen)
        self.clear_button.draw(self.screen)
        self.back_button.draw(self.screen)
        
        # 拖拽中的卡牌（最后绘制，在最上层）
        if self.dragging_card:
            self.dragging_card.draw(self.screen)
    
    def draw_title(self):
        """绘制标题"""
        title_y = int(WINDOW_HEIGHT * 0.05)
        title_text = self.title_font.render("卡组配置", True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, title_y))
        
        shadow_offset = max(2, int(2 * UI_SCALE))
        shadow_text = self.title_font.render("卡组配置", True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(
            center=(WINDOW_WIDTH // 2 + shadow_offset, title_y + shadow_offset)
        )
        
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)
    
    def draw_collection(self):
        """绘制收藏卡牌"""
        surface, offset_y = self.scroll_view.begin_draw()
        
        if not self.collection_cards:
            no_card_text = self.info_font.render(
                "还没有收集到卡牌哦~", True, (150, 150, 150)
            )
            text_rect = no_card_text.get_rect(
                center=(self.scroll_view.rect.width // 2, 
                       self.scroll_view.rect.height // 2)
            )
            surface.blit(no_card_text, text_rect)
        else:
            for card in self.collection_cards:
                # 跳过正在拖拽的卡牌
                if self.dragging_card and card.data == self.dragging_card.data:
                    continue
                
                # 创建临时rect用于绘制
                temp_rect = card.rect.copy()
                temp_rect.y += offset_y
                
                # 检查是否在可见区域
                if -card.rect.height < temp_rect.y < self.scroll_view.rect.height:
                    temp_pos = (card.rect.x, temp_rect.y)
                    surface.blit(card.image, temp_pos)
                    
                    # 边框
                    if card.is_hovered:
                        border_color = COLORS.get(card.data.get("rarity", "D"), (255, 255, 255))
                        border_width = max(3, int(4 * UI_SCALE))
                        pygame.draw.rect(surface, border_color, 
                                       (temp_pos[0], temp_pos[1], card.rect.width, card.rect.height), 
                                       border_width)
        
        self.scroll_view.end_draw(self.screen)
