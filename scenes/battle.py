"""战斗场景"""
import pygame
import os
from scenes.base_scene import BaseScene
from ui.button import Button
from config import *
from game.hand_card import HandManager
from utils.draft_manager import get_draft_manager # draft抽卡管理器
from utils.battle_component import CardSlot, HealthBar # 战斗组件
from game.deck_renderer import DeckRenderer #　卡堆渲染器

# 抽卡动画
GACHA_DELAY_INIT = 0.5  # 首张卡抽取延迟
GACHA_DELAY_BETWEEN = 0.3  # 每张卡间隔时间

# 背景设置
BATTLE_BG_BRIGHTNESS = 0.7  # 背景亮度 (0.0-1.0)
BATTLE_BG_ALPHA = 200       # 背景透明度 (0-255)

# 战斗区卡牌槽位尺寸
BATTLE_CARD_BASE_WIDTH = 288   # 战斗区卡牌基础宽度
BATTLE_CARD_BASE_HEIGHT = 432  # 战斗区卡牌基础高度
BATTLE_CARD_SPACING = 10       # 战斗区卡牌间距

# 等候区卡牌槽位尺寸
WAITING_CARD_BASE_WIDTH = 144   # 等候区卡牌基础宽度
WAITING_CARD_BASE_HEIGHT = 216  # 等候区卡牌基础高度
WAITING_CARD_SPACING = 15      # 等候区卡牌间距

# 弃牌堆槽位尺寸
DISCARD_CARD_BASE_WIDTH = 216  # 弃牌堆基础宽度
DISCARD_CARD_BASE_HEIGHT = 324  # 弃牌堆基础高度

# 战斗区布局
BATTLE_SLOTS_COUNT = 5         # 战斗区槽位数量
WAITING_SLOTS_COUNT = 8        # 等候区槽位数量

# 位置配置（屏幕百分比）
PLAYER_BATTLE_Y_RATIO = 0.50   # 玩家战斗区Y位置
ENEMY_BATTLE_Y_RATIO = 0.23    # 敌人战斗区Y位置
PLAYER_WAITING_Y_RATIO = 0.85  # 玩家等候区Y位置
ENEMY_WAITING_Y_RATIO = 0.02   # 敌人等候区Y位置

PLAYER_DISCARD_X_RATIO = 0.92  # 玩家弃牌堆X位置
PLAYER_DISCARD_Y_RATIO = 0.80  # 玩家弃牌堆Y位置
ENEMY_DISCARD_X_RATIO = 0.92   # 敌人弃牌堆X位置
ENEMY_DISCARD_Y_RATIO = 0.05   # 敌人弃牌堆Y位置

# 血量条配置
HEALTH_BAR_WIDTH = 300         # 血量条基础宽度
HEALTH_BAR_HEIGHT = 50         # 血量条基础高度
PLAYER_HEALTH_Y_RATIO = 0.85   # 玩家血量条Y位置
ENEMY_HEALTH_Y_RATIO = 0.08    # 敌人血量条Y位置

"""战斗场景"""
class BattleScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        
        # 背景图片路径
        self.background_image_path = "assets/battle_bg.png"
        self.background = self.load_background()
        
        # 字体
        self.title_font = get_font(max(20, int(32 * UI_SCALE)))
        self.info_font = get_font(max(14, int(20 * UI_SCALE)))
        
        # 玩家和敌人血量
        self.player_max_hp = 100
        self.player_current_hp = 100
        self.enemy_max_hp = 100
        self.enemy_current_hp = 100
        
        # 创建血量条
        self.create_health_bars()
        
        # 卡牌槽位
        self.player_battle_slots = []  # 玩家战斗区
        self.enemy_battle_slots = []   # 敌人战斗区
        self.player_waiting_slots = [] # 玩家等候区
        self.enemy_waiting_slots = []  # 敌人等候区
        self.player_discard_slot = None  # 玩家弃牌堆
        self.enemy_discard_slot = None   # 敌人弃牌堆
        self.create_slots() # 创建槽位
        self.create_buttons() # 创建按钮
        
        # 卡堆渲染器
        player_deck_x = int(WINDOW_WIDTH * 0.05)
        player_deck_y = int(WINDOW_HEIGHT * 0.65)  # 玩家卡堆位置（左下）
        self.player_deck_renderer = DeckRenderer(player_deck_x, player_deck_y, is_player=True)
        enemy_deck_x = int(WINDOW_WIDTH * 0.05)
        enemy_deck_y = int(WINDOW_HEIGHT * 0.15)  # 敌人卡堆位置（左上）
        self.enemy_deck_renderer = DeckRenderer(enemy_deck_x, enemy_deck_y, is_player=False)

        # 手牌管理器
        self.player_hand = HandManager(is_player=True)
        self.player_hand.deck_position = (player_deck_x + 60, player_deck_y + 90)
        self.enemy_hand = HandManager(is_player=False)
        self.enemy_hand.deck_position = (enemy_deck_x + 60, enemy_deck_y + 90)
        
        # 牌堆（从draft获取）
        self.player_deck = []
        self.enemy_deck = []

        # 抽卡动画队列
        self.draw_queue = []  # [(hand_manager, card_data, delay), ...]
        self.draw_timer = 0.0

        # 初始化标志
        self.battle_initialized = False
        
    def load_background(self):
        """加载背景图片"""
        if os.path.exists(self.background_image_path):
            try:
                bg = pygame.image.load(self.background_image_path)
                bg = pygame.transform.smoothscale(bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
                bg = bg.convert()
                
                # 应用亮度调整
                bg = self.adjust_brightness(bg, BATTLE_BG_BRIGHTNESS)
                
                # 应用透明度
                if BATTLE_BG_ALPHA < 255:
                    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 255 - BATTLE_BG_ALPHA))
                    bg.blit(overlay, (0, 0))
                
                return bg
            except Exception as e:
                print(f"背景图片加载失败: {self.background_image_path}, 错误: {e}")
                return self.create_default_background()
        else:
            print(f"背景图片不存在: {self.background_image_path}")
            return self.create_default_background()
    
    def adjust_brightness(self, surface, brightness):
        """
        调整Surface亮度
        Args:
            surface: pygame.Surface
            brightness: 亮度值 (0.0-1.0)
        Returns:
            调整后的Surface
        """
        # 创建亮度调整后的surface
        adjusted = surface.copy()
        
        # 创建亮度遮罩
        if brightness < 1.0:
            # 变暗
            darken = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            darken.fill((0, 0, 0))
            darken.set_alpha(int(255 * (1 - brightness)))
            adjusted.blit(darken, (0, 0))
        elif brightness > 1.0:
            # 变亮
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
            # 应用亮度调整
            base_color = (
                int((30 + ratio * 20) * BATTLE_BG_BRIGHTNESS),
                int((30 + ratio * 40) * BATTLE_BG_BRIGHTNESS),
                int((50 + ratio * 30) * BATTLE_BG_BRIGHTNESS)
            )
            pygame.draw.line(bg, base_color, (0, y), (WINDOW_WIDTH, y))
        
        # 中间分界线
        middle_y = WINDOW_HEIGHT // 2
        line_color = tuple(int(c * BATTLE_BG_BRIGHTNESS) for c in (100, 100, 120))
        pygame.draw.line(bg, line_color, 
                        (0, middle_y), (WINDOW_WIDTH, middle_y), 
                        max(2, int(3 * UI_SCALE)))
        
        # 应用透明度
        if BATTLE_BG_ALPHA < 255:
            bg.set_alpha(BATTLE_BG_ALPHA)
        
        return bg
    
    def create_health_bars(self):
        """创建血量条"""
        bar_width = int(HEALTH_BAR_WIDTH * UI_SCALE)
        bar_height = int(HEALTH_BAR_HEIGHT * UI_SCALE)
        margin_x = int(30 * UI_SCALE)
        
        # 玩家血量条（左下）
        player_y = int(WINDOW_HEIGHT * PLAYER_HEALTH_Y_RATIO)
        self.player_health_bar = HealthBar(
            margin_x, player_y, bar_width, bar_height,
            self.player_max_hp, self.player_current_hp, is_player=True
        )
        
        # 敌人血量条（左上）
        enemy_y = int(WINDOW_HEIGHT * ENEMY_HEALTH_Y_RATIO)
        self.enemy_health_bar = HealthBar(
            margin_x, enemy_y, bar_width, bar_height,
            self.enemy_max_hp, self.enemy_current_hp, is_player=False
        )
    
    def create_slots(self):
        """创建所有卡牌槽位"""
        # 战斗区卡牌尺寸（应用UI缩放）
        battle_card_width = int(BATTLE_CARD_BASE_WIDTH * UI_SCALE)
        battle_card_height = int(BATTLE_CARD_BASE_HEIGHT * UI_SCALE)
        battle_card_spacing = int(BATTLE_CARD_SPACING * UI_SCALE)
        
        # 等候区卡牌尺寸（应用UI缩放）
        waiting_card_width = int(WAITING_CARD_BASE_WIDTH * UI_SCALE)
        waiting_card_height = int(WAITING_CARD_BASE_HEIGHT * UI_SCALE)
        waiting_card_spacing = int(WAITING_CARD_SPACING * UI_SCALE)
        
        # 弃牌堆尺寸（应用UI缩放）
        discard_width = int(DISCARD_CARD_BASE_WIDTH * UI_SCALE)
        discard_height = int(DISCARD_CARD_BASE_HEIGHT * UI_SCALE)
        
        # === 战斗区槽位（中间两列，对战）===
        total_battle_width = BATTLE_SLOTS_COUNT * battle_card_width + (BATTLE_SLOTS_COUNT - 1) * battle_card_spacing
        battle_start_x = (WINDOW_WIDTH - total_battle_width) // 2
        
        # 玩家战斗区（下方）
        player_battle_y = int(WINDOW_HEIGHT * PLAYER_BATTLE_Y_RATIO)
        for i in range(BATTLE_SLOTS_COUNT):
            x = battle_start_x + i * (battle_card_width + battle_card_spacing)
            slot = CardSlot(x, player_battle_y, battle_card_width, battle_card_height, "battle")
            self.player_battle_slots.append(slot)
        
        # 敌人战斗区（上方）
        enemy_battle_y = int(WINDOW_HEIGHT * ENEMY_BATTLE_Y_RATIO)
        for i in range(BATTLE_SLOTS_COUNT):
            x = battle_start_x + i * (battle_card_width + battle_card_spacing)
            slot = CardSlot(x, enemy_battle_y, battle_card_width, battle_card_height, "battle")
            self.enemy_battle_slots.append(slot)
        
        # === 等候区槽位（边缘一排）===
        total_waiting_width = WAITING_SLOTS_COUNT * waiting_card_width + (WAITING_SLOTS_COUNT - 1) * waiting_card_spacing
        waiting_start_x = (WINDOW_WIDTH - total_waiting_width) // 2
        
        # 玩家等候区（靠近玩家侧底部）
        player_waiting_y = int(WINDOW_HEIGHT * PLAYER_WAITING_Y_RATIO)
        for i in range(WAITING_SLOTS_COUNT):
            x = waiting_start_x + i * (waiting_card_width + waiting_card_spacing)
            slot = CardSlot(x, player_waiting_y, waiting_card_width, waiting_card_height, "waiting")
            self.player_waiting_slots.append(slot)
        
        # 敌人等候区（靠近敌人侧顶部）
        enemy_waiting_y = int(WINDOW_HEIGHT * ENEMY_WAITING_Y_RATIO)
        for i in range(WAITING_SLOTS_COUNT):
            x = waiting_start_x + i * (waiting_card_width + waiting_card_spacing)
            slot = CardSlot(x, enemy_waiting_y, waiting_card_width, waiting_card_height, "waiting")
            self.enemy_waiting_slots.append(slot)
        
        # === 弃牌堆（角落）===
        # 玩家弃牌堆（右下角）
        player_discard_x = int(WINDOW_WIDTH * PLAYER_DISCARD_X_RATIO)
        player_discard_y = int(WINDOW_HEIGHT * PLAYER_DISCARD_Y_RATIO)
        self.player_discard_slot = CardSlot(
            player_discard_x, player_discard_y, discard_width, discard_height, "discard"
        )
        
        # 敌人弃牌堆（右上角）
        enemy_discard_x = int(WINDOW_WIDTH * ENEMY_DISCARD_X_RATIO)
        enemy_discard_y = int(WINDOW_HEIGHT * ENEMY_DISCARD_Y_RATIO)
        self.enemy_discard_slot = CardSlot(
            enemy_discard_x, enemy_discard_y, discard_width, discard_height, "discard"
        )
    
    def create_buttons(self):
        """创建UI按钮"""
        button_width = int(150 * UI_SCALE)
        button_height = int(50 * UI_SCALE)
        margin = int(20 * UI_SCALE)
        
        # 返回按钮（左下角）
        self.back_button = Button(
            margin,
            int(WINDOW_HEIGHT * 0.95),
            button_width,
            button_height,
            "返回菜单",
            color=(100, 100, 100),
            hover_color=(130, 130, 130),
            font_size=24,
            on_click=lambda: self.switch_to("main_menu")
        )
        
        # 结束回合按钮（右侧中间）
        self.end_turn_button = Button(
            int(WINDOW_WIDTH * 0.85),
            int(WINDOW_HEIGHT * 0.5),
            button_width,
            button_height,
            "结束回合",
            color=(200, 100, 50),
            hover_color=(230, 130, 80),
            font_size=24,
            on_click=self.end_turn
        )
    
    def end_turn(self):
        """结束回合"""
        print("回合结束")
        # TODO: 实现回合逻辑

    """获取鼠标悬停的卡牌数据"""
    def get_hovered_card(self, mouse_pos):
         # 优先检查手牌（最上层）
        player_card_data = self.player_hand.get_hovered_card_data()
        if player_card_data:
            return player_card_data
        
        enemy_card_data = self.enemy_hand.get_hovered_card_data()
        if enemy_card_data:
            return enemy_card_data
        
        # 然后检查槽位中的卡牌
        all_slots = (
            self.player_battle_slots + 
            self.enemy_battle_slots + 
            self.player_waiting_slots + 
            self.enemy_waiting_slots +
            [self.player_discard_slot, self.enemy_discard_slot]
        )
        
        for slot in all_slots:
            if slot.has_card() and slot.rect.collidepoint(mouse_pos):
                return slot.card.card_data
        
        return None
     
    """事件处理"""
    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")

        # 手牌事件（优先处理）
        selected_card = self.player_hand.handle_event(event)
        if selected_card:
            print(f"选中卡牌: {selected_card.card_data.name}")
        # TODO: 处理出牌逻辑
        
        # 鼠标移动
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            
            # 更新槽位悬停
            all_slots = (
                self.player_battle_slots + 
                self.enemy_battle_slots + 
                self.player_waiting_slots + 
                self.enemy_waiting_slots + 
                [self.player_discard_slot, self.enemy_discard_slot]
            )
            
            for slot in all_slots:
                slot.is_hovered = slot.rect.collidepoint(mouse_pos)
        
        # 按钮事件
        self.back_button.handle_event(event)
        self.end_turn_button.handle_event(event)
    
    def update(self, dt):
        """更新"""
        # 更新血量条动画
        self.player_health_bar.update(dt)
        self.enemy_health_bar.update(dt)
        # 更新手牌动画
        self.player_hand.update(dt)
        self.enemy_hand.update(dt)

        # 处理抽卡队列
        if self.draw_queue:
            self.draw_timer += dt
            
            # 检查是否到时间抽卡
            while self.draw_queue and self.draw_timer >= self.draw_queue[0][1]:
                who, _ = self.draw_queue.pop(0)
                self.draw_card(who, animate=True)
        
    """绘制场景"""
    def draw(self):
        self.screen.blit(self.background, (0, 0)) # 背景
        self.draw_scene_labels() # 场景标识
        self.draw_health_bars() # 血量条
        self.draw_slots() # 槽位
        # 卡堆
        self.player_deck_renderer.draw(self.screen)
        self.enemy_deck_renderer.draw(self.screen)
        # 手牌
        self.player_hand.draw(self.screen)
        self.enemy_hand.draw(self.screen)
        # 绘制按钮
        self.back_button.draw(self.screen)
        self.end_turn_button.draw(self.screen)
    
    def draw_scene_labels(self):
        """绘制场景标签（敌人区域/玩家区域提示）"""
        # 敌人区域标签
        enemy_label = self.title_font.render("敌方区域", True, (255, 100, 100))
        enemy_rect = enemy_label.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.15)))
        
        # 半透明背景
        label_bg = pygame.Surface((enemy_rect.width + 20, enemy_rect.height + 10), pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 120))
        self.screen.blit(label_bg, (enemy_rect.x - 10, enemy_rect.y - 5))
        self.screen.blit(enemy_label, enemy_rect)
        
        # 玩家区域标签
        player_label = self.title_font.render("我方区域", True, (100, 255, 100))
        player_rect = player_label.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.73)))
        
        label_bg = pygame.Surface((player_rect.width + 20, player_rect.height + 10), pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 120))
        self.screen.blit(label_bg, (player_rect.x - 10, player_rect.y - 5))
        self.screen.blit(player_label, player_rect)
    
    def draw_health_bars(self):
        """绘制血量条"""
        # 玩家名称和血量条
        player_name = self.info_font.render("玩家", True, (200, 255, 200))
        player_name_pos = (self.player_health_bar.rect.x, 
                          self.player_health_bar.rect.y - int(25 * UI_SCALE))
        self.screen.blit(player_name, player_name_pos)
        self.player_health_bar.draw(self.screen)
        
        # 敌人名称和血量条
        enemy_name = self.info_font.render("敌人", True, (255, 200, 200))
        enemy_name_pos = (self.enemy_health_bar.rect.x, 
                         self.enemy_health_bar.rect.y - int(25 * UI_SCALE))
        self.screen.blit(enemy_name, enemy_name_pos)
        self.enemy_health_bar.draw(self.screen)
    
    def draw_slots(self):
        """绘制所有槽位"""
        # 战斗区标签
        battle_label_font = get_font(max(12, int(16 * UI_SCALE)))
        
        # 玩家战斗区
        for slot in self.player_battle_slots:
            slot.draw(self.screen)
        
        # 敌人战斗区
        for slot in self.enemy_battle_slots:
            slot.draw(self.screen)
        
        # 等候区标签和槽位
        waiting_label = battle_label_font.render("等候区", True, (200, 200, 150))
        
        # 玩家等候区
        if self.player_waiting_slots:
            label_x = self.player_waiting_slots[0].rect.x - int(80 * UI_SCALE)
            label_y = self.player_waiting_slots[0].rect.centery
            self.screen.blit(waiting_label, (label_x, label_y))
            
        for slot in self.player_waiting_slots:
            slot.draw(self.screen)
        
        # 敌人等候区
        if self.enemy_waiting_slots:
            label_x = self.enemy_waiting_slots[0].rect.x - int(80 * UI_SCALE)
            label_y = self.enemy_waiting_slots[0].rect.centery
            self.screen.blit(waiting_label, (label_x, label_y))
            
        for slot in self.enemy_waiting_slots:
            slot.draw(self.screen)
        
        # 弃牌堆标签和槽位
        discard_label = battle_label_font.render("弃牌堆", True, (200, 150, 150))
        
        # 玩家弃牌堆
        discard_x = self.player_discard_slot.rect.x
        discard_y = self.player_discard_slot.rect.y - int(25 * UI_SCALE)
        self.screen.blit(discard_label, (discard_x, discard_y))
        self.player_discard_slot.draw(self.screen)
        
        # 敌人弃牌堆
        discard_x = self.enemy_discard_slot.rect.x
        discard_y = self.enemy_discard_slot.rect.y - int(25 * UI_SCALE)
        self.screen.blit(discard_label, (discard_x, discard_y))
        self.enemy_discard_slot.draw(self.screen)

    """进入场景时初始化"""
    def enter(self):
        super().enter()
    
        if not self.battle_initialized:
            self.initialize_battle()
            self.battle_initialized = True

    """初始化战斗"""
    def initialize_battle(self):
        draft_manager = get_draft_manager()
        
        # 从draft获取双方卡组
        from utils.card_database import get_card_database
        db = get_card_database()
        
        # 玩家1卡组（下方）
        for card_dict in draft_manager.player1_cards:
            card_data = db.get_card_by_path(card_dict.get('path'))
            if card_data:
                self.player_deck.append(card_data)
        
        # 玩家2卡组（上方）
        for card_dict in draft_manager.player2_cards:
            card_data = db.get_card_by_path(card_dict.get('path'))
            if card_data:
                self.enemy_deck.append(card_data)
        
        # 洗牌
        import random
        random.shuffle(self.player_deck)
        random.shuffle(self.enemy_deck)
        
        # 更新卡堆数量
        self.player_deck_renderer.set_count(len(self.player_deck))
        self.enemy_deck_renderer.set_count(len(self.enemy_deck))
        
        # 设置抽卡动画队列（开局各抽3张，交替抽取）
        self.draw_queue = []
        delay = GACHA_DELAY_INIT
        for i in range(3):
            # 玩家抽卡
            self.draw_queue.append(('player', delay))
            delay += GACHA_DELAY_BETWEEN  # 每张卡间隔0.3秒
            # 敌人抽卡
            self.draw_queue.append(('enemy', delay))
            delay += GACHA_DELAY_BETWEEN
        print(f"战斗初始化完成")

    """抽卡"""
    def draw_card(self, who, animate=True):
        if who == 'player':
            if self.player_deck:
                card_data = self.player_deck.pop(0)
                self.player_hand.add_card(card_data, animate=animate)
                self.player_deck_renderer.set_count(len(self.player_deck))
                return True
        else:  # enemy
            if self.enemy_deck:
                card_data = self.enemy_deck.pop(0)
                self.enemy_hand.add_card(card_data, animate=animate)
                self.enemy_deck_renderer.set_count(len(self.enemy_deck))
                return True
        
        return False