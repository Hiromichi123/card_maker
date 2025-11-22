"""
自选卡牌场景Draft 玩家为双方选择卡牌
"""
import pygame
import os
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.panel import Panel
from utils.draft_manager import get_draft_manager
from config import *

# ==================== Draft场景配置 ====================
# 背景设置
DRAFT_BG_PATH = "assets/battle_bg.png"
DRAFT_BG_BRIGHTNESS = 0.7
DRAFT_BG_ALPHA = 200

# 卡牌布局设置
card_width = int(216 * UI_SCALE) # Draft卡牌基础宽度
card_height = int(324 * UI_SCALE) # Draft卡牌基础高度
spacing_x = int(25 * UI_SCALE) # 水平间距
spacing_y = int(25 * UI_SCALE) # 垂直间距
DRAFT_ROW_COUNTS = [9, 10, 9] # 三层布局 (9, 10, 9)

# 位置配置
DRAFT_CENTER_Y_RATIO = 0.40   # 卡牌区域中心Y位置

"""Draft卡牌类"""
class DraftCard:
    def __init__(self, card_data, x, y, width, height, index):
        self.data = card_data
        self.rect = pygame.Rect(x, y, width, height)
        self.index = index
        
        self.is_hovered = False
        self.is_picked = False
        self.picked_by = None  # "player1" 或 "player2"
        
        # 动画
        self.scale = 1.0
        self.target_scale = 1.0
        
        # 加载图片
        self.load_image()

        # 从数据库加载完整的 CardData
        from utils.card_database import get_card_database
        db = get_card_database()
        self.card_data = db.get_card_by_path(card_data.get('path'))
    
    def load_image(self):
        """加载卡牌图片"""
        try:
            if os.path.exists(self.data["path"]):
                original = pygame.image.load(self.data["path"])
                self.image = pygame.transform.smoothscale(
                    original, (self.rect.width, self.rect.height)
                )
            else:
                self.image = self.create_placeholder()
        except:
            self.image = self.create_placeholder()
        
        self.image = self.image.convert_alpha()
    
    def create_placeholder(self):
        """创建占位符"""
        surface = pygame.Surface((self.rect.width, self.rect.height))
        color = COLORS.get(self.data.get("rarity", "D"), (100, 100, 100))
        surface.fill(color)
        
        border_width = max(2, int(3 * UI_SCALE))
        pygame.draw.rect(surface, (255, 255, 255), 
                        (0, 0, self.rect.width, self.rect.height), border_width)
        
        font = get_font(max(16, int(24 * UI_SCALE)))
        text = font.render(self.data.get("rarity", "?"), True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        surface.blit(text, text_rect)
        
        return surface
    
    def update(self, dt):
        """更新动画"""
        # 悬停缩放
        self.target_scale = 1.15 if self.is_hovered and not self.is_picked else 1.0
        self.scale += (self.target_scale - self.scale) * min(1.0, dt * 10)
    
    def draw(self, screen):
        """绘制卡牌"""
        if self.is_picked:
            # 已被选择的卡牌变暗
            dark_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            dark_surface.blit(self.image, (0, 0))
            dark_surface.fill((0, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
            
            screen.blit(dark_surface, self.rect)
            
            # 显示被谁选择
            font = get_font(max(12, int(16 * UI_SCALE)))
            text = "下方" if self.picked_by == "player1" else "上方"
            color = (100, 255, 100) if self.picked_by == "player1" else (100, 150, 255)
            text_surface = font.render(text, True, color)
            text_rect = text_surface.get_rect(center=self.rect.center)
            
            # 半透明背景
            bg = pygame.Surface((text_rect.width + 10, text_rect.height + 5), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 180))
            screen.blit(bg, (text_rect.x - 5, text_rect.y - 2))
            screen.blit(text_surface, text_rect)
        else:
            # 未被选择的卡牌
            if self.scale != 1.0:
                # 缩放绘制
                scaled_width = int(self.rect.width * self.scale)
                scaled_height = int(self.rect.height * self.scale)
                scaled_image = pygame.transform.smoothscale(self.image, (scaled_width, scaled_height))
                
                scaled_rect = scaled_image.get_rect(center=self.rect.center)
                screen.blit(scaled_image, scaled_rect)
            else:
                screen.blit(self.image, self.rect)
            
            # 悬停边框
            if self.is_hovered:
                border_color = COLORS.get(self.data.get("rarity", "D"), (255, 255, 255))
                border_width = max(3, int(4 * UI_SCALE))
                if self.scale != 1.0:
                    scaled_width = int(self.rect.width * self.scale)
                    scaled_height = int(self.rect.height * self.scale)
                    scaled_rect = pygame.Rect(0, 0, scaled_width, scaled_height)
                    scaled_rect.center = self.rect.center
                    pygame.draw.rect(screen, border_color, scaled_rect, border_width)
                else:
                    pygame.draw.rect(screen, border_color, self.rect, border_width)

"""自选卡牌场景"""
class DraftScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.draft_manager = get_draft_manager() # Draft管理器
        self.background = self.load_background() # 背景
        
        # 字体
        self.title_font = get_font(max(24, int(48 * UI_SCALE)))
        self.info_font = get_font(max(16, int(28 * UI_SCALE)))
        self.small_font = get_font(max(12, int(20 * UI_SCALE)))
        
        self.draft_cards = [] # Draft卡牌列表
        self.create_ui() # 创建UI
        self.initialized = False # 是否已初始化
    
    def load_background(self):
        """加载背景"""
        if os.path.exists(DRAFT_BG_PATH):
            try:
                bg = pygame.image.load(DRAFT_BG_PATH)
                bg = pygame.transform.smoothscale(bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
                bg = bg.convert()
                
                # 应用亮度
                bg = self.adjust_brightness(bg, DRAFT_BG_BRIGHTNESS)
                
                # 应用透明度
                if DRAFT_BG_ALPHA < 255:
                    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 255 - DRAFT_BG_ALPHA))
                    bg.blit(overlay, (0, 0))
                
                return bg
            except Exception as e:
                print(f"Draft背景加载失败: {e}")
                return self.create_default_background()
        else:
            return self.create_default_background()
    
    def adjust_brightness(self, surface, brightness):
        """调整亮度"""
        adjusted = surface.copy()
        
        if brightness < 1.0:
            darken = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            darken.fill((0, 0, 0))
            darken.set_alpha(int(255 * (1 - brightness)))
            adjusted.blit(darken, (0, 0))
        elif brightness > 1.0:
            brighten = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            brighten.fill((255, 255, 255))
            brighten.set_alpha(int(255 * (brightness - 1)))
            adjusted.blit(brighten, (0, 0), special_flags=pygame.BLEND_ADD)
        
        return adjusted
    
    def create_default_background(self):
        """创建默认背景"""
        bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # 渐变背景
        for y in range(WINDOW_HEIGHT):
            ratio = y / WINDOW_HEIGHT
            color = (
                int((40 + ratio * 30) * DRAFT_BG_BRIGHTNESS),
                int((30 + ratio * 50) * DRAFT_BG_BRIGHTNESS),
                int((60 + ratio * 40) * DRAFT_BG_BRIGHTNESS)
            )
            pygame.draw.line(bg, color, (0, y), (WINDOW_WIDTH, y))
        
        return bg
    
    def create_ui(self):
        """创建UI"""
        # 信息面板（顶部）
        info_panel_width = int(WINDOW_WIDTH * 0.8)
        info_panel_height = int(80 * UI_SCALE)
        info_panel_x = (WINDOW_WIDTH - info_panel_width) // 2
        info_panel_y = int(20 * UI_SCALE)
        
        self.info_panel = Panel(info_panel_x, info_panel_y, info_panel_width, info_panel_height,
                               alpha=180)
        
        # 玩家1卡组面板（底部左）
        player_panel_width = int(300 * UI_SCALE)
        player_panel_height = int(120 * UI_SCALE)
        player1_panel_x = int(WINDOW_WIDTH * 0.05)
        player1_panel_y = int(WINDOW_HEIGHT * 0.85)
        
        self.player1_panel = Panel(player1_panel_x, player1_panel_y, 
                                   player_panel_width, player_panel_height, alpha=180)
        
        # 玩家2卡组面板（顶部左）
        player2_panel_x = int(WINDOW_WIDTH * 0.05)
        player2_panel_y = int(WINDOW_HEIGHT * 0.02)
        
        self.player2_panel = Panel(player2_panel_x, player2_panel_y, 
                                   player_panel_width, player_panel_height, alpha=180)
        
        # 按钮
        button_width = int(150 * UI_SCALE)
        button_height = int(50 * UI_SCALE)
        
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
    
    def initialize_draft_cards(self):
        """初始化Draft卡牌显示"""
        self.draft_cards = []
        center_y = int(WINDOW_HEIGHT * DRAFT_CENTER_Y_RATIO) # 三层布局
        card_index = 0
        for row_idx, card_count in enumerate(DRAFT_ROW_COUNTS):
            # 计算该行的总宽度
            total_width = card_count * card_width + (card_count - 1) * spacing_x
            start_x = (WINDOW_WIDTH - total_width) // 2
            
            # 计算Y位置（交替排列）
            if row_idx == 0:
                y = center_y - card_height - spacing_y
            elif row_idx == 1:
                y = center_y
            else:  # row_idx == 2
                y = center_y + card_height + spacing_y
            
            # 创建该行的卡牌
            for col_idx in range(card_count):
                x = start_x + col_idx * (card_width + spacing_x)
                
                if card_index < len(self.draft_manager.draft_pool):
                    card_data = self.draft_manager.draft_pool[card_index]
                    draft_card = DraftCard(card_data, x, y, card_width, card_height, card_index)
                    
                    # 设置已被选择的状态
                    if card_data["picked"]:
                        draft_card.is_picked = True
                        draft_card.picked_by = card_data["picked_by"]
                    
                    self.draft_cards.append(draft_card)
                
                card_index += 1
    
    def enter(self):
        """进入场景"""
        super().enter()
        
        # 初始化Draft
        self.draft_manager.initialize_draft()
        self.initialize_draft_cards()
        self.initialized = True
    
    """获取鼠标悬停的卡牌数据"""
    def get_hovered_card(self, mouse_pos):
        for draft_card in self.draft_cards:
            if draft_card.rect.collidepoint(mouse_pos):
                if hasattr(draft_card, 'card_data'):
                    return draft_card.card_data
        return None
    
    """处理事件"""
    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")
        
        # 鼠标移动
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            for card in self.draft_cards:
                if not card.is_picked:
                    card.is_hovered = card.rect.collidepoint(mouse_pos)
        
        # 鼠标点击
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
            for card in self.draft_cards:
                if not card.is_picked and card.rect.collidepoint(mouse_pos):
                    # 选择卡牌
                    if self.draft_manager.pick_card(card.index):
                        card.is_picked = True
                        card.picked_by = self.draft_manager.current_turn if self.draft_manager.current_turn == "player1" else "player2"
                        
                        # 检查是否完成
                        if self.draft_manager.is_draft_complete():
                            self.on_draft_complete()
                    break
        
        # 按钮事件
        self.back_button.handle_event(event)
    
    def on_draft_complete(self):
        """Draft完成"""
        print("Draft完成！")
        self.draft_manager.save_draft() # 保存结果
        
        # 延迟后进入战斗场景
        pygame.time.delay(1000)
        self.switch_to("battle")
    
    def update(self, dt):
        """更新"""
        # 更新卡牌动画
        for card in self.draft_cards:
            card.update(dt)
    
    def draw(self):
        """绘制"""
        self.screen.blit(self.background, (0, 0)) # 背景
        self.draw_info_panel() # 信息面板
        
        # 玩家面板
        self.draw_player1_panel()
        self.draw_player2_panel()
        
        # Draft卡牌
        for card in self.draft_cards:
            card.draw(self.screen)
        
        self.draw_turn_indicator() # 回合指示器
        self.back_button.draw(self.screen) # 按钮
    
    def draw_info_panel(self):
        """绘制信息面板"""
        self.info_panel.draw(self.screen)
        
        # 标题
        title = self.title_font.render("双方交替选择12张卡牌进入战斗", True, (255, 215, 0))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 
                                            self.info_panel.rect.centery - int(10 * UI_SCALE)))
        self.screen.blit(title, title_rect)
    
    def draw_player1_panel(self):
        """绘制玩家1面板（下方/己方）"""
        self.player1_panel.draw(self.screen)
        
        # 标题
        x = self.player1_panel.rect.x + int(15 * UI_SCALE)
        y = self.player1_panel.rect.y + int(10 * UI_SCALE)
        
        title = self.info_font.render("下方卡组（己方）", True, (100, 255, 100))
        self.screen.blit(title, (x, y))
        
        # 卡牌数量
        count = len(self.draft_manager.player1_cards)
        count_text = self.info_font.render(f"{count}/12", True, (255, 255, 255))
        count_rect = count_text.get_rect(right=self.player1_panel.rect.right - int(15 * UI_SCALE), 
                                         top=y)
        self.screen.blit(count_text, count_rect)
        
        # 进度条
        bar_y = y + int(40 * UI_SCALE)
        bar_width = self.player1_panel.rect.width - int(30 * UI_SCALE)
        bar_height = int(20 * UI_SCALE)
        
        # 背景
        bar_bg = pygame.Rect(x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (50, 50, 50), bar_bg, border_radius=int(10 * UI_SCALE))
        
        # 进度
        progress = count / 12
        progress_width = int(bar_width * progress)
        if progress_width > 0:
            progress_rect = pygame.Rect(x, bar_y, progress_width, bar_height)
            pygame.draw.rect(self.screen, (100, 255, 100), progress_rect, 
                           border_radius=int(10 * UI_SCALE))
        
        # 边框
        pygame.draw.rect(self.screen, (150, 150, 150), bar_bg, 2, 
                        border_radius=int(10 * UI_SCALE))
    
    def draw_player2_panel(self):
        """绘制玩家2面板（上方/对方）"""
        self.player2_panel.draw(self.screen)
        
        # 标题
        x = self.player2_panel.rect.x + int(15 * UI_SCALE)
        y = self.player2_panel.rect.y + int(10 * UI_SCALE)
        
        title = self.info_font.render("上方卡组（对方）", True, (100, 150, 255))
        self.screen.blit(title, (x, y))
        
        # 卡牌数量
        count = len(self.draft_manager.player2_cards)
        count_text = self.info_font.render(f"{count}/12", True, (255, 255, 255))
        count_rect = count_text.get_rect(right=self.player2_panel.rect.right - int(15 * UI_SCALE), 
                                         top=y)
        self.screen.blit(count_text, count_rect)
        
        # 进度条
        bar_y = y + int(40 * UI_SCALE)
        bar_width = self.player2_panel.rect.width - int(30 * UI_SCALE)
        bar_height = int(20 * UI_SCALE)
        
        # 背景
        bar_bg = pygame.Rect(x, bar_y, bar_width, bar_height)
        pygame.draw.rect(self.screen, (50, 50, 50), bar_bg, border_radius=int(10 * UI_SCALE))
        
        # 进度
        progress = count / 12
        progress_width = int(bar_width * progress)
        if progress_width > 0:
            progress_rect = pygame.Rect(x, bar_y, progress_width, bar_height)
            pygame.draw.rect(self.screen, (100, 150, 255), progress_rect, 
                           border_radius=int(10 * UI_SCALE))
        
        # 边框
        pygame.draw.rect(self.screen, (150, 150, 150), bar_bg, 2, 
                        border_radius=int(10 * UI_SCALE))
    
    def draw_turn_indicator(self):
        """绘制回合指示器"""
        if self.draft_manager.current_turn == "player1":
            text = "为下方（己方）选择卡牌"
            color = (100, 255, 100)
        else:
            text = "为上方（对方）选择卡牌"
            color = (100, 150, 255)
        
        indicator = self.info_font.render(text, True, color)
        indicator_rect = indicator.get_rect(center=(WINDOW_WIDTH // 2, 
                                                    int(WINDOW_HEIGHT * 0.12)))
        
        # 半透明背景
        bg_padding = int(15 * UI_SCALE)
        bg = pygame.Surface((indicator_rect.width + bg_padding * 2, 
                            indicator_rect.height + bg_padding), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        self.screen.blit(bg, (indicator_rect.x - bg_padding, indicator_rect.y - bg_padding // 2))
        
        self.screen.blit(indicator, indicator_rect)