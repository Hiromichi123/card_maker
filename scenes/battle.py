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
from game.card_animation import AttackAnimation # 攻击动画


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
        self.battle_initialized = False # 初始化标志
        
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
        self.create_health_bars() # 玩家血条
        
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

        # 回合状态
        self.current_turn = "player1"  # player1, player2
        self.turn_phase = "playing"    # playing（出牌阶段）, battling（战斗结算中）
        self.turn_number = 1           # 回合数
        self.cards_played_this_turn = 0  # 本回合已出牌数
        self.max_cards_per_turn = 1    # 每回合最多出牌数
        self.load_turn_indicator_bg() # 回合指示器背景
        
        # 自动模式（仅用于敌人AI）
        self.enemy_auto_mode = True    # 敌人是否自动
        self.auto_timer = 0.0
        self.auto_delay = 3.0          # 敌人AI思考时间
        
        # 战斗状态
        self.battle_in_progress = False  # 是否正在进行战斗结算
        self.battle_animations = []      # 战斗动画队列
        self.battle_timer = 0.0

        # 战斗动画
        self.battle_animations = []
        self.battle_phase = "idle"  # idle, attacking, cleaning, compacting
        self.battle_timer = 0.0
        self.current_attack_index = 0
                
        # 游戏结束状态
        self.game_over = False
        self.winner = None  # "player1" 或 "player2"

    """进入场景初始化"""
    def enter(self):
        super().enter()
        if not self.battle_initialized:
            self.initialize_battle()
            self.battle_initialized = True

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
    
    """创建所有卡牌槽位"""
    def create_slots(self):
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
            slot = CardSlot(x, player_battle_y, battle_card_width, battle_card_height, 
                          "battle", owner="player")
            self.player_battle_slots.append(slot)
        
        # 敌人战斗区（上方）
        enemy_battle_y = int(WINDOW_HEIGHT * ENEMY_BATTLE_Y_RATIO)
        for i in range(BATTLE_SLOTS_COUNT):
            x = battle_start_x + i * (battle_card_width + battle_card_spacing)
            slot = CardSlot(x, enemy_battle_y, battle_card_width, battle_card_height, 
                          "battle", owner="enemy")
            self.enemy_battle_slots.append(slot)
        
        # === 等候区槽位（边缘一排）===
        total_waiting_width = WAITING_SLOTS_COUNT * waiting_card_width + (WAITING_SLOTS_COUNT - 1) * waiting_card_spacing
        waiting_start_x = (WINDOW_WIDTH - total_waiting_width) // 2
        
        # 玩家等候区（靠近玩家侧底部）
        player_waiting_y = int(WINDOW_HEIGHT * PLAYER_WAITING_Y_RATIO)
        for i in range(WAITING_SLOTS_COUNT):
            x = waiting_start_x + i * (waiting_card_width + waiting_card_spacing)
            slot = CardSlot(x, player_waiting_y, waiting_card_width, waiting_card_height, 
                          "waiting", owner="player")
            self.player_waiting_slots.append(slot)
        
        # 敌人等候区（靠近敌人侧顶部）
        enemy_waiting_y = int(WINDOW_HEIGHT * ENEMY_WAITING_Y_RATIO)
        for i in range(WAITING_SLOTS_COUNT):
            x = waiting_start_x + i * (waiting_card_width + waiting_card_spacing)
            slot = CardSlot(x, enemy_waiting_y, waiting_card_width, waiting_card_height, 
                          "waiting", owner="enemy")
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

        # 敌人AI开关按钮（右侧中间偏上）
        toggle_width = int(120 * UI_SCALE)
        toggle_height = int(40 * UI_SCALE)
        
        self.enemy_ai_toggle_button = Button(
            int(WINDOW_WIDTH * 0.85),
            int(WINDOW_HEIGHT * 0.45),
            toggle_width,
            toggle_height,
            "AI: 开",
            color=(50, 200, 50),
            hover_color=(80, 230, 80),
            font_size=20,
            on_click=self.toggle_enemy_ai
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
                return slot.card_data
        
        return None
     
    """事件处理"""
    def handle_event(self, event):
        # 游戏结束时只允许返回菜单
        if self.game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")
            return
        
        super().handle_event(event)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.player_hand.clear_selection()
                self.switch_to("main_menu")
        
        # 手牌事件（根据回合判断）
        player_action = None
        enemy_action = None
        if self.current_turn == "player1":
            player_action = self.player_hand.handle_event(event)
        else:
            # 敌人回合，如果AI关闭则允许手动操作
            if not self.enemy_auto_mode:
                enemy_action = self.enemy_hand.handle_event(event)
            else:
                action = None
        
        # 处理手牌点击（当前回合的owner）
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.current_turn == "player1" and player_action == "play":
                selected = self.player_hand.get_selected_card()
                if selected and self.can_play_card():
                    self.play_card_to_waiting(selected)
                    self.clear_slot_highlights()
                elif not self.can_play_card():
                    print("本回合已出过牌！")
            
            elif self.current_turn == "player2" and enemy_action == "play":
                selected = self.enemy_hand.get_selected_card()
                if selected and self.can_play_card():
                    self.play_card_to_waiting(selected)
                    self.clear_slot_highlights()
                elif not self.can_play_card():
                    print("本回合已出过牌！")
            
            elif player_action == "select" and self.current_turn == "player1" and self.can_play_card():
                self.highlight_valid_slots()
            
            elif enemy_action == "select" and self.current_turn == "player2" and self.can_play_card():
                self.highlight_valid_slots()
            
            elif player_action == "deselect" or enemy_action == "deselect":
                self.clear_slot_highlights()
        
        # 鼠标移动
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
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
        self.enemy_ai_toggle_button.handle_event(event)
        # 只有完成出牌后才能点击结束回合按钮
        if self.can_end_turn():
            self.end_turn_button.handle_event(event)
    
    """更新"""
    def update(self, dt):
        if self.game_over:
            return
        
        # 更新血量条
        self.player_health_bar.update(dt)
        self.enemy_health_bar.update(dt)
        
        # 更新手牌
        self.player_hand.update(dt)
        self.enemy_hand.update(dt)
        
        # 更新卡槽动画
        all_slots = (
            self.player_battle_slots + 
            self.enemy_battle_slots + 
            self.player_waiting_slots + 
            self.enemy_waiting_slots
        )
        for slot in all_slots:
            slot.update_animations(dt)
        
        # 更新战斗动画
        self.battle_animations = [anim for anim in self.battle_animations if not anim.update(dt)]
        if self.turn_phase == "battling":
            self.update_battle_animations(dt)
            return  # 战斗阶段直接返回
        
        # 处理抽卡队列
        if self.draw_queue:
            self.draw_timer += dt
            
            while self.draw_queue and self.draw_timer >= self.draw_queue[0][1]:
                who, _ = self.draw_queue.pop(0)
                self.draw_card(who, animate=True)
        
        # 敌人AI逻辑
        if (self.current_turn == "player2" and 
            self.turn_phase == "playing" and 
            self.enemy_auto_mode and
            not self.is_switching_turn):  # 防止切换回合时触发
            self.auto_timer += dt
            
            # 分两个阶段：出牌阶段 → 结束回合阶段
            if self.cards_played_this_turn < self.max_cards_per_turn:
                # 出牌阶段
                if self.auto_timer >= self.auto_delay:
                    self.auto_timer = 0.0
                    played = self.enemy_ai_play_card()
                    if not played:
                        print("[AI] 无法出牌（无手牌或准备区满）")
            elif self.cards_played_this_turn >= self.max_cards_per_turn:
                if self.auto_timer >= self.auto_delay * 0.5:
                    self.end_turn()
                    self.auto_timer = 0.0

    """绘制场景"""
    def draw(self):
        self.screen.blit(self.background, (0, 0)) # 背景
        self.draw_turn_indicator() # 回合指示器
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
        # 结束回合按钮（根据状态变色）
        if self.can_end_turn():
            self.end_turn_button.color = (50, 200, 50)
            self.end_turn_button.hover_color = (80, 230, 80)
        else:
            self.end_turn_button.color = (100, 100, 100)
            self.end_turn_button.hover_color = (120, 120, 120)
        self.end_turn_button.draw(self.screen)
        self.enemy_ai_toggle_button.draw(self.screen)

        # 绘制战斗动画
        for anim in self.battle_animations:
            if hasattr(anim, 'draw'):
                anim.draw(self.screen)
        # 游戏结束提示
        if self.game_over:
            self.draw_game_over_overlay()
    
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

    def draw_turn_indicator(self):
        """绘制回合指示器"""
        self.screen.blit(self.turn_bg, self.turn_bg_rect) # 背景图
        
        # 回合数
        turn_font = get_font(max(32, int(48 * UI_SCALE)))
        turn_text = turn_font.render(f"回合 {self.turn_number}", True, (255, 215, 0))
        turn_rect = turn_text.get_rect(
            centerx=self.turn_bg_rect.centerx,
            top=self.turn_bg_rect.top + int(20 * UI_SCALE)
        )
        self.screen.blit(turn_text, turn_rect)
        
        # 当前玩家
        player_font = get_font(max(20, int(28 * UI_SCALE)))
        
        if self.current_turn == "player1":
            player_text = "玩家回合"
            color = (100, 255, 100)
        else:
            player_text = "敌人回合"
            color = (255, 100, 100)
        
        player_surface = player_font.render(player_text, True, color)
        player_rect = player_surface.get_rect(
            centerx=self.turn_bg_rect.centerx,
            centery=self.turn_bg_rect.centery
        )
        self.screen.blit(player_surface, player_rect)
        
        # 出牌状态
        status_font = get_font(max(16, int(20 * UI_SCALE)))
        if self.can_play_card():
            status_text = f"可出牌: {self.max_cards_per_turn - self.cards_played_this_turn}/{self.max_cards_per_turn}"
            status_color = (200, 200, 255)
        else:
            status_text = "已出牌"
            status_color = (150, 150, 150)
        
        status_surface = status_font.render(status_text, True, status_color)
        status_rect = status_surface.get_rect(
            centerx=self.turn_bg_rect.centerx,
            bottom=self.turn_bg_rect.bottom - int(15 * UI_SCALE)
        )
        self.screen.blit(status_surface, status_rect)

    def draw_game_over_overlay(self):
        """绘制游戏结束遮罩"""
        # 半透明黑色遮罩
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # 胜利/失败文字
        result_font = get_font(max(48, int(72 * UI_SCALE)))
        
        if self.winner == "player1":
            result_text = "胜利！"
            result_color = (100, 255, 100)
        else:
            result_text = "失败..."
            result_color = (255, 100, 100)
        
        result_surface = result_font.render(result_text, True, result_color)
        result_rect = result_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        self.screen.blit(result_surface, result_rect)
        
        # 提示文字
        hint_font = get_font(max(20, int(28 * UI_SCALE)))
        hint_text = "按 ESC 返回主菜单"
        hint_surface = hint_font.render(hint_text, True, (200, 200, 200))
        hint_rect = hint_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(hint_surface, hint_rect)

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
    
    """高亮显示可放置卡牌的槽位"""
    def highlight_valid_slots(self):
        # 高亮准备区空槽位
        if self.turn_phase == "prepare":
            for slot in self.player_waiting_slots:
                if not slot.has_card():
                    slot.is_highlighted = True
    
    """清除所有槽位高亮"""
    def clear_slot_highlights(self):
        all_slots = (
            self.player_battle_slots + 
            self.enemy_battle_slots + 
            self.player_waiting_slots + 
            self.enemy_waiting_slots + 
            [self.player_discard_slot, self.enemy_discard_slot]
        )
        
        for slot in all_slots:
            slot.is_highlighted = False

    """将手牌打出到等候区"""
    def play_card_to_waiting(self, hand_card):
        # 检查是否可以出牌
        if not self.can_play_card():
            print("本回合已出过牌或不在出牌阶段！")
            return
        
        # 根据当前回合选择对应的准备区
        if self.current_turn == "player1":
            target_slots = self.player_waiting_slots
            hand_manager = self.player_hand
        else:  # player2
            target_slots = self.enemy_waiting_slots
            hand_manager = self.enemy_hand
        
        # 找到第一个空槽位
        target_slot = None
        for slot in target_slots:
            if not slot.has_card():
                target_slot = slot
                break
        
        if target_slot:
            target_slot.set_card(hand_card.card_data) # 放置卡牌
            hand_manager.remove_card(hand_card) # 从手牌移除
            self.cards_played_this_turn += 1 # 增加出牌计数
        else:
            print("准备区已满！")

    """结束回合"""
    def end_turn(self):
        if self.turn_phase != "playing":
            print(f"当前阶段是 {self.turn_phase}，不能结束回合")
            return
    
        if self.cards_played_this_turn < self.max_cards_per_turn:
            print(f"未完成出牌 ({self.cards_played_this_turn}/{self.max_cards_per_turn})")
            return
        
        self.turn_phase = "battling" # 切换到战斗阶段
        self.battle_phase = "attacking"
        self.current_attack_index = 0
        self.battle_timer = 0.0

        if self.check_game_over(): # 检查游戏结束
            return
        
        self.process_waiting_area() # 减少准备区卡牌的 CD
        self.move_ready_cards_to_battle() # 将 CD 归零的卡牌移动到战斗区
    
    """切换回合"""
    def switch_turn(self):
        # 切换玩家
        if self.current_turn == "player1":
            self.current_turn = "player2"
        else:
            self.current_turn = "player1"
            self.turn_number += 1
        
        # 重置回合状态
        self.turn_phase = "playing"
        self.cards_played_this_turn = 0
        self.auto_timer = 0.0
        
        self.draw_card_for_turn() # 为当前玩家抽一张卡

        # 检查手牌数量，决定是否跳过出牌阶段
        current_hand = self.player_hand if self.current_turn == "player1" else self.enemy_hand
        if len(current_hand.cards) == 0:
            # 无手牌，直接进入战斗
            self.cards_played_this_turn = self.max_cards_per_turn  # 标记为已完成出牌
            pygame.time.delay(1000)  # 延迟1秒（给玩家反应时间）
            self.end_turn()  # 进入战斗，结束回合
        else:
            # 有手牌，正常提示
            if self.current_turn == "player2" and self.enemy_auto_mode:
                print("[AI] 敌人AI将在 1.5秒后自动出牌")

    """回合开始时抽一张卡"""
    def draw_card_for_turn(self):
        draw_who = "player" if self.current_turn == "player1" else "enemy"
        success = self.draw_card(draw_who, animate=True)

    """处理准备区 减少CD"""
    def process_waiting_area(self):
        # 处理双方的准备区
        for slot in self.player_waiting_slots + self.enemy_waiting_slots:
            if slot.has_card():
                is_ready = slot.reduce_cd(1)
                owner = "玩家" if slot.owner == "player" else "敌人"
    
    """准备区CD归零的卡牌移动到战斗区"""
    def move_ready_cards_to_battle(self):
        # 处理玩家准备区
        self._move_cards_from_waiting_to_battle(
            self.player_waiting_slots, 
            self.player_battle_slots,
            "玩家"
        )
        
        # 处理敌人准备区
        self._move_cards_from_waiting_to_battle(
            self.enemy_waiting_slots,
            self.enemy_battle_slots,
            "敌人"
        )

    def _move_cards_from_waiting_to_battle(self, waiting_slots, battle_slots, owner_name):
        """辅助方法：从准备区移动到战斗区"""
        ready_cards = []
        for slot in waiting_slots:
            if slot.has_card() and slot.cd_remaining == 0:
                ready_cards.append((slot, slot.card_data))
        
        for waiting_slot, card_data in ready_cards:
            # 找到战斗区第一个空槽位（从左到右）
            target_slot = None
            for battle_slot in battle_slots:
                if not battle_slot.has_card():
                    target_slot = battle_slot
                    break
            
            if target_slot:
                target_slot.set_card(card_data)
                waiting_slot.remove_card()
            else:
                print(f"  [{owner_name}] 战斗区已满，{card_data.name} 保留在准备区")
                break

    def load_turn_indicator_bg(self):
        """加载回合指示器背景"""
        import os
        bg_path = "assets/turn_indicator_bg.png"
        
        if os.path.exists(bg_path):
            try:
                self.turn_bg = pygame.image.load(bg_path)
                # 缩放到合适大小
                bg_width = int(200 * UI_SCALE)
                bg_height = int(150 * UI_SCALE)
                self.turn_bg = pygame.transform.smoothscale(self.turn_bg, (bg_width, bg_height))
            except:
                self.turn_bg = self.create_default_turn_bg()
        else:
            self.turn_bg = self.create_default_turn_bg()
        
        # 位置（左侧中间）
        self.turn_bg_rect = self.turn_bg.get_rect(
            left=int(WINDOW_WIDTH * 0.02),
            centery=int(WINDOW_HEIGHT * 0.5)
        )
    
    def create_default_turn_bg(self):
        """创建默认回合指示器背景"""
        width = int(200 * UI_SCALE)
        height = int(150 * UI_SCALE)
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # 渐变背景
        for y in range(height):
            ratio = y / height
            color = (
                int(30 + ratio * 50),
                int(40 + ratio * 60),
                int(80 + ratio * 80),
                200
            )
            pygame.draw.line(surface, color, (0, y), (width, y))
        
        # 边框
        pygame.draw.rect(surface, (150, 150, 200), (0, 0, width, height), 3,
                        border_radius=int(10 * UI_SCALE))
        
        return surface

    def toggle_enemy_ai(self):
        """切换敌人AI"""
        self.enemy_auto_mode = not self.enemy_auto_mode
        
        if self.enemy_auto_mode:
            self.enemy_ai_toggle_button.text = "AI: 开"
            self.enemy_ai_toggle_button.color = (50, 200, 50)
            self.enemy_ai_toggle_button.hover_color = (80, 230, 80)
            print("[AI] 敌人AI已开启")
        else:
            self.enemy_ai_toggle_button.text = "AI: 关"
            self.enemy_ai_toggle_button.color = (80, 80, 80)
            self.enemy_ai_toggle_button.hover_color = (100, 100, 100)
            print("[AI] 敌人AI已关闭（可手动操作敌人）")
    
    def can_play_card(self):
        """检查当前回合是否可以出牌"""
        result = self.turn_phase == "playing" and self.cards_played_this_turn < self.max_cards_per_turn
        return result

    def can_end_turn(self):
        """检查是否可以结束回合"""
        result = self.turn_phase == "playing" and self.cards_played_this_turn >= self.max_cards_per_turn
        return result

    def on_end_turn_click(self):
        """点击结束回合按钮"""
        print(f"\n[on_end_turn_click] 被点击")
        print(f"  当前回合: {self.current_turn}")
        print(f"  当前阶段: {self.turn_phase}")
        print(f"  已出牌: {self.cards_played_this_turn}/{self.max_cards_per_turn}")
        
        if self.can_end_turn():
            print(f"[on_end_turn_click] 条件满足，开始结束回合")
            self.end_turn()
        else:
            remaining = self.max_cards_per_turn - self.cards_played_this_turn
            print(f"[警告] 必须先出 {remaining} 张卡才能结束回合！")

    def enemy_ai_play_card(self):
        """敌人AI自动出牌"""
        import random
        if not self.can_play_card():
            return False
        
        # 随机选择一张手牌
        if self.enemy_hand.cards:
            random_card = random.choice(self.enemy_hand.cards)
            self.play_card_to_waiting(random_card)
            print(f"[AI] 敌人自动出牌: {random_card.card_data.name}")
            return True
        
        return False       

    def remove_dead_cards(self):
        """移除 HP <= 0 的卡牌到弃牌堆"""
        # 检查所有战斗区槽位
        all_battle_slots = self.player_battle_slots + self.enemy_battle_slots
        
        for slot in all_battle_slots:
            if slot.has_card() and slot.card_data.hp <= 0:
                card_name = slot.card_data.name
                owner = "玩家" if slot.owner == "player" else "敌人"
                slot.remove_card() # 移除卡牌 送入弃牌堆的逻辑后续添加
    
    def check_game_over(self):
        """检查游戏是否结束"""
        player_hp = self.player_current_hp
        enemy_hp = self.enemy_current_hp
        player_has_cards = self.has_cards_alive("player")
        enemy_has_cards = self.has_cards_alive("enemy")
        
        # 失败条件：HP ≤ 0 或 无卡牌
        if player_hp <= 0 or not player_has_cards:
            self.game_over = True
            self.winner = "player2"
            print("游戏结束，敌人获胜！")
            self.show_game_over_screen()
            return True
        elif enemy_hp <= 0 or not enemy_has_cards:
            self.game_over = True
            self.winner = "player1"
            print("游戏结束，玩家获胜！")
            self.show_game_over_screen()
            return True
        
        return False

    def show_game_over_screen(self):
        """显示游戏结束界面"""
        # 简单实现：延迟后返回主菜单
        # TODO: 可以添加更华丽的胜利/失败动画
        print("[游戏结束] 3秒后返回主菜单...")
        pygame.time.delay(3000)
        self.switch_to("main_menu")

    """战斗结算（启动动画序列）"""
    def process_battle(self):
        print("战斗结算")
        # 设置战斗阶段
        self.battle_phase = "attacking"
        self.current_attack_index = 0
        self.battle_timer = 0.0
    
    """更新战斗动画序列"""
    def update_battle_animations(self, dt):
        if self.battle_phase == "idle":
            return
        
        # 确定攻击方和防御方
        if self.current_turn == "player1":
            attacker_slots = self.player_battle_slots
            defender_slots = self.enemy_battle_slots
            attacker_name = "玩家"
            defender_name = "敌人"
            defender_hp_ref = "enemy"
        else:
            attacker_slots = self.enemy_battle_slots
            defender_slots = self.player_battle_slots
            attacker_name = "敌人"
            defender_name = "玩家"
            defender_hp_ref = "player"
        
        if self.battle_phase == "attacking":
            self.battle_timer += dt
            
            # 每隔0.8秒处理一次攻击
            if self.battle_timer >= 0.9:
                self.battle_timer = 0.0
                # 查找下一个可攻击的卡牌
                while self.current_attack_index < len(attacker_slots):
                    attacker_slot = attacker_slots[self.current_attack_index]
                    
                    if attacker_slot.has_card():
                        # 执行攻击
                        print(f"[战斗动画] 槽位 {self.current_attack_index} 发动攻击")
                        self.execute_attack(
                            attacker_slot,
                            defender_slots[self.current_attack_index],
                            attacker_name,
                            defender_name,
                            defender_hp_ref
                        )
                        self.current_attack_index += 1
                        break
                    
                    self.current_attack_index += 1
                
            if self.current_attack_index >= len(attacker_slots):
                # 所有攻击完成，进入清理阶段
                print("[战斗动画] 没有更多攻击者，进入清理阶段")
                self.battle_phase = "cleaning"
                self.battle_timer = 0.0
                print("\n所有攻击完成")
        
        elif self.battle_phase == "cleaning":
            self.battle_timer += dt
            # 等待1秒后清理死亡卡牌
            if self.battle_timer >= 1.0:
                self.remove_dead_cards()
                self.battle_phase = "compacting"
                self.battle_timer = 0.0
        
        elif self.battle_phase == "compacting":
            self.battle_timer += dt
            # 等待0.5秒后压缩槽位
            if self.battle_timer >= 0.5:
                self.adjust_battle_slots()
                self.battle_phase = "finishing"
                self.battle_timer = 0.0
        
        elif self.battle_phase == "finishing":
            self.battle_timer += dt
            # 等待动画完成
            if self.battle_timer >= 0.6:
                self.battle_phase = "idle"
                # 检查游戏是否结束
                if not self.check_game_over():
                    self.switch_turn()
    
    """执行单次攻击"""
    def execute_attack(self, attacker_slot, defender_slot, attacker_name, defender_name, defender_hp_ref):
        attacker_card = attacker_slot.card_data
        
        # 创建攻击动画
        attack_anim = AttackAnimation(attacker_slot, defender_slot if defender_slot.has_card() else None)
        self.battle_animations.append(attack_anim)
        
        if defender_slot.has_card():
            # 攻击卡牌
            defender_card = defender_slot.card_data
            old_hp = defender_card.hp
            new_hp = old_hp - attacker_card.atk
            defender_card.hp = new_hp
            
            # 更新槽位数据
            defender_slot.card_data = defender_card
            
            # 触发HP闪烁
            defender_slot.start_hp_flash(old_hp, new_hp)
        else:
            # 攻击玩家
            if defender_hp_ref == "player":
                self.player_current_hp -= attacker_card.atk
                self.player_health_bar.set_hp(self.player_current_hp)
            else:
                self.enemy_current_hp -= attacker_card.atk
                self.enemy_health_bar.set_hp(self.enemy_current_hp)
    
    def adjust_battle_slots(self):
        """调整战斗槽位（向左填补空位）"""
        from game.card_animation import SlideAnimation
        for battle_slots in [self.player_battle_slots, self.enemy_battle_slots]:
            # 收集所有有卡牌的槽位
            cards_with_slots = []
            for slot in battle_slots:
                if slot.has_card():
                    cards_with_slots.append((slot, slot.card_data))
            
            if not cards_with_slots:
                continue
            
            # 清空所有槽位
            for slot in battle_slots:
                slot.remove_card()
            
            # 从左到右重新放置
            for i, (old_slot, card_data) in enumerate(cards_with_slots):
                new_slot = battle_slots[i]
                new_slot.set_card(card_data)
                
                # 如果位置变化，创建滑动动画
                if old_slot != new_slot:
                    # 临时设置卡牌在旧位置
                    new_slot.rect.x = old_slot.original_rect.x
                    new_slot.rect.y = old_slot.original_rect.y
                    
                    # 创建滑动动画
                    slide_anim = SlideAnimation(
                        new_slot,
                        new_slot.original_rect.x,
                        new_slot.original_rect.y
                    )
                    self.battle_animations.append(slide_anim)

    def has_cards_alive(self, who):
        """检查指定玩家是否还有卡牌存活"""
        if who == "player":
            hand = self.player_hand
            waiting_slots = self.player_waiting_slots
            battle_slots = self.player_battle_slots
        else:
            hand = self.enemy_hand
            waiting_slots = self.enemy_waiting_slots
            battle_slots = self.enemy_battle_slots
        
        hand_count = len(hand.cards) # 检查手牌
        waiting_count = sum(1 for slot in waiting_slots if slot.has_card()) # 检查准备区
        battle_count = sum(1 for slot in battle_slots if slot.has_card()) # 检查战斗区
        total_cards = hand_count + waiting_count + battle_count
        
        return total_cards > 0
