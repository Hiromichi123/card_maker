"""战斗场景基类"""
import os
import pygame
from time import time
from config import *
from scenes.base_scene import BaseScene
from ui.button import Button
from utils.battle_component import CardSlot, HealthBar # 战斗场景组件
from game.hand_card import HandManager, HandCard # 手牌管理器，手牌类
from game.deck_renderer import DeckRenderer #　卡堆渲染器
from game.card_animation import SlideAnimation # 滑动动画
from game.card_animation import AttackAnimation # 攻击动画

# region  常量配置
# 背景设置
BATTLE_BG_BRIGHTNESS = 0.7  # 背景亮度 (0.0-1.0)
BATTLE_BG_ALPHA = 200       # 背景透明度 (0-255)

# 战斗区卡牌槽位尺寸
BATTLE_CARD_BASE_WIDTH = 288   # 战斗区卡牌基础宽度
BATTLE_CARD_BASE_HEIGHT = 432  # 战斗区卡牌基础高度
BATTLE_CARD_SPACING = 15       # 战斗区卡牌间距

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
HEALTH_BAR_WIDTH = 400         # 宽度
HEALTH_BAR_HEIGHT = 80         # 高度
PLAYER_HEALTH_Y_RATIO = 0.85   # 玩家血量条Y位置
ENEMY_HEALTH_Y_RATIO = 0.08    # 敌人血量条Y位置
# 玩家和敌人血量
PLAYER_MAX_HP = 20
PLAYER_CURRENT_HP = 20
ENEMY_MAX_HP = 20
ENEMY_CURRENT_HP = 20
# endregion

"""战斗场景基类"""
class BattleBaseScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.battle_initialized = False # 初始化标志

        # 背景图片路径
        self.background_image_path = "assets/battle_bg.png"
        self.background = self.load_background()
        
        # 字体
        self.title_font = get_font(max(20, int(32 * UI_SCALE)))
        self.info_font = get_font(max(14, int(20 * UI_SCALE)))

        self.load_turn_indicator_bg() # 回合指示器背景

        # 血量初始化
        self.player_max_hp = PLAYER_MAX_HP
        self.player_current_hp = PLAYER_CURRENT_HP
        self.enemy_max_hp = ENEMY_MAX_HP
        self.enemy_current_hp = ENEMY_CURRENT_HP
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

        # 双方牌堆
        self.player_deck = []
        self.enemy_deck = []

        # 抽卡动画队列
        self.draw_queue = []
        self.draw_timer = 0.0

        # 手牌管理器
        self.player_hand = HandManager(is_player=True)
        self.player_hand.deck_position = (self.player_deck_renderer.position[0] + 60, self.player_deck_renderer.position[1] + 90)
        self.enemy_hand = HandManager(is_player=False)
        self.enemy_hand.deck_position = (self.enemy_deck_renderer.position[0] + 60, self.enemy_deck_renderer.position[1] + 90)

        # 回合状态
        self.current_turn = "player1"  # player1, player2
        self.turn_phase = "playing"    # playing（出牌阶段）, battling（战斗结算中）
        self.turn_number = 1           # 回合数
        self.cards_played_this_turn = 0  # 本回合已出牌数
        self.max_cards_per_turn = 1    # 每回合最多出牌数
        
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
        self.winner = None

    """====================核心功能类===================="""
    def enter(self):
        super().enter()

    def update(self, dt):
        if self.game_over:
            return
        
        super().update(dt)
        
        # 更新血量条
        self.player_health_bar.update(dt)
        self.enemy_health_bar.update(dt)

        # 更新卡槽动画
        all_slots = (
            self.player_battle_slots + 
            self.enemy_battle_slots + 
            self.player_waiting_slots + 
            self.enemy_waiting_slots
        )
        for slot in all_slots:
            slot.update_animations(dt)
          
        # 更新手牌
        self.player_hand.update(dt)
        self.enemy_hand.update(dt)
        
        # 进行战斗
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

    def handle_events(self, event):
        # 基本按键处理
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.player_hand.clear_selection()
                self.switch_to("main_menu")

    def draw(self):
        self.screen.blit(self.background, (0, 0)) # 背景
        self.draw_turn_indicator() # 回合指示器
        self.draw_scene_labels() # 场景标识
        self.draw_health_bars() # 血量条
        self.draw_slots() # 槽位
        # 绘制按钮
        self.back_button.draw(self.screen)
        self.end_turn_button.draw(self.screen)
        self.enemy_ai_toggle_button.draw(self.screen)

    def initialize_battle(self):
        # 从卡牌数据库获取卡组
        from utils.card_database import get_card_database
        db = get_card_database()
        return db

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
            print("[游戏结束] 3秒后返回主菜单...")
            pygame.time.delay(3000)
            self.switch_to("main_menu")
            return True
        elif enemy_hp <= 0 or not enemy_has_cards:
            self.game_over = True
            self.winner = "player1"
            print("游戏结束，玩家获胜！")
            print("[游戏结束] 3秒后返回主菜单...")
            self.show_game_over_screen()
            pygame.time.delay(3000)
            self.switch_to("main_menu")
            return True
        return False

    """====================回合控制类===================="""
    def switch_turn(self):
        """切换回合"""
        if self.current_turn == "player1":
            self.current_turn = "player2"
        else:
            self.current_turn = "player1"
            self.turn_number += 1
        
        # 重置回合状态
        self.turn_phase = "playing"
        self.cards_played_this_turn = 0
        self.auto_timer = 0.0
        
        # 为当前回合玩家抽一张卡
        draw_who = "player" if self.current_turn == "player1" else "enemy"
        self.draw_card(draw_who, animate=True)

    def end_turn(self):
        """结束回合"""
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

    def update_battle_animations(self, dt):
        """更新战斗动画序列"""
        if self.battle_phase == "idle":
            return
        
        # 确定攻击方和防御方
        if self.current_turn == "player1":
            attacker_slots = self.player_battle_slots
            defender_slots = self.enemy_battle_slots
            defender_hp_ref = "enemy"
        else:
            attacker_slots = self.enemy_battle_slots
            defender_slots = self.player_battle_slots
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
                        self.execute_attack(
                            attacker_slot,
                            defender_slots[self.current_attack_index],
                            defender_hp_ref
                        )
                        self.current_attack_index += 1
                        break
                    
                    self.current_attack_index += 1
                
            if self.current_attack_index >= len(attacker_slots):
                # 当攻击完成，进入清理阶段
                self.battle_phase = "cleaning"
                self.battle_timer = 0.0
        
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
 

    """====================初始化和资源加载类===================="""
    def load_background(self):
        """加载背景图片"""
        if os.path.exists(self.background_image_path):
            try:
                bg = pygame.image.load(self.background_image_path)
                bg = pygame.transform.smoothscale(bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
                bg = bg.convert()
                bg = self.adjust_brightness(bg, BATTLE_BG_BRIGHTNESS) # 应用亮度调整
                
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
        """调整Surface亮度"""
        adjusted = surface.copy() # 创建亮度调整后的surface
        
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

    """====================UI组件创建类===================="""
    def create_health_bars(self):
        """创建血量条"""
        bar_width = int(HEALTH_BAR_WIDTH * UI_SCALE)
        bar_height = int(HEALTH_BAR_HEIGHT * UI_SCALE)
        margin_x = int(30 * UI_SCALE)
        
        # 玩家血量条
        player_y = int(WINDOW_HEIGHT * PLAYER_HEALTH_Y_RATIO)
        self.player_health_bar = HealthBar(
            margin_x, player_y, bar_width, bar_height,
            self.player_max_hp, self.player_current_hp, is_player=True
        )
        
        # 敌人血量条
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

    """====================基础绘制类===================="""
    def draw_scene_labels(self):
        """绘制场景标签"""
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
        battle_label_font = get_font(max(12, int(16 * UI_SCALE))) # 战斗区标签
        
        # 玩家战斗区
        for slot in self.player_battle_slots:
            slot.draw(self.screen)
        
        # 敌人战斗区
        for slot in self.enemy_battle_slots:
            slot.draw(self.screen)
        
        waiting_label = battle_label_font.render("等候区", True, (200, 200, 150)) # 等候区标签和槽位
        
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
        
        discard_label = battle_label_font.render("弃牌堆", True, (200, 150, 150)) # 弃牌堆标签和槽位
        
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

    """====================辅助工具类===================="""
    def draw_card(self, who, animate=True):
        """抽卡"""
        if who == 'player':
            if self.player_deck:
                card_data = self.player_deck.pop(0)
                self.player_hand.add_card(card_data, animate=animate)
                self.player_deck_renderer.set_count(len(self.player_deck))
                return True
        elif who == 'enemy':
            if self.enemy_deck:
                card_data = self.enemy_deck.pop(0)
                self.enemy_hand.add_card(card_data, animate=animate)
                self.enemy_deck_renderer.set_count(len(self.enemy_deck))
                return True
        return False

    def execute_attack(self, attacker_slot, defender_slot, defender_hp_ref):
        """执行单次攻击"""
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
            
            defender_slot.card_data = defender_card # 更新槽位数据
            defender_slot.start_hp_flash(old_hp, new_hp) # 触发HP闪烁
        else:
            # 攻击玩家
            if defender_hp_ref == "player":
                self.player_current_hp -= attacker_card.atk
                self.player_health_bar.set_hp(self.player_current_hp)
            else:
                self.enemy_current_hp -= attacker_card.atk
                self.enemy_health_bar.set_hp(self.enemy_current_hp)

    def process_waiting_area(self):
        """处理双方准备区 减少CD"""
        for slot in self.player_waiting_slots + self.enemy_waiting_slots:
            if slot.has_card():
                slot.reduce_cd(1)

    def get_hovered_card(self, mouse_pos):
        """获取鼠标悬停的卡牌数据"""
         # 检查手牌（最上层）
        player_card_data = self.player_hand.get_hovered_card_data()
        if player_card_data:
            return player_card_data
        enemy_card_data = self.enemy_hand.get_hovered_card_data()
        if enemy_card_data:
            return enemy_card_data
        
        # 检查槽位中的卡牌
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
     
    def highlight_valid_slots(self):
        """高亮准备区空槽位"""
        if self.turn_phase == "prepare":
            for slot in self.player_waiting_slots:
                if not slot.has_card():
                    slot.is_highlighted = True
    
    def clear_slot_highlights(self):
        """清除所有槽位高亮"""
        all_slots = (
            self.player_battle_slots + 
            self.enemy_battle_slots + 
            self.player_waiting_slots + 
            self.enemy_waiting_slots + 
            [self.player_discard_slot, self.enemy_discard_slot]
        )
        for slot in all_slots:
            slot.is_highlighted = False

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

    def play_card_to_waiting(self, hand_card):
        """将手牌打出到等候区"""
        # 检查是否可以出牌
        if not self.can_play_card():
            print("本回合已出过牌或不在出牌阶段！")
            return
        
        # 根据当前回合选择对应的准备区
        if self.current_turn == "player1":
            target_slots = self.player_waiting_slots
            hand_manager = self.player_hand
        elif self.current_turn == "player2":
            target_slots = self.enemy_waiting_slots
            hand_manager = self.enemy_hand
        
        # 找到第一个空槽位
        target_slot = None
        for slot in target_slots:
            if not slot.has_card():
                target_slot = slot
                break
        
        if target_slot:
            start_rect = hand_card.get_rect()
            end_rect = target_slot.rect.copy()
            
            self.play_blocking_move_animation(
                hand_card.card_data,
                start_rect,
                end_rect,
                duration=0.3
            )
            
            target_slot.set_card(hand_card.card_data) # 放置卡牌
            hand_manager.remove_card(hand_card) # 从手牌移除
            self.cards_played_this_turn += 1 # 增加出牌计数
        else:
            print("准备区已满！")

    """====================卡牌移动动画===================="""
    def play_blocking_move_animation(self, card_data, start_rect, end_rect, duration=0.5):
        """播放阻塞式移动动画"""
        start_time = time()
        clock = pygame.time.Clock()
        
        # 创建临时卡牌图片
        temp_card = self.create_temp_card_surface(card_data, start_rect.width, start_rect.height)
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            elapsed = time() - start_time
            
            if elapsed >= duration:
                break
            
            # 计算当前位置（ease-out缓动）
            progress = elapsed / duration
            t = 1 - (1 - progress) ** 3  # 三次缓动
            
             # 插值位置
            current_x = start_rect.x + (end_rect.x - start_rect.x) * t
            current_y = start_rect.y + (end_rect.y - start_rect.y) * t
            # 插值尺寸（平滑缩放）
            current_width = int(start_rect.width + (end_rect.width - start_rect.width) * t)
            current_height = int(start_rect.height + (end_rect.height - start_rect.height) * t)
            current_rect = pygame.Rect(int(current_x), int(current_y), current_width, current_height)
            # 动态创建当前尺寸的卡牌
            temp_card = self.create_temp_card_surface(card_data, current_width, current_height)
        
            self.draw() # 重绘整个场景
            self.screen.blit(temp_card, current_rect) # 在动画卡牌上方绘制
            pygame.display.flip()
            
            # 处理退出事件（避免卡死）
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
        
    def play_blocking_fade_move_animation(self, card_data, start_rect, end_rect, duration=0.5):
        """播放阻塞式淡出移动动画（用于阵亡）"""
        start_time = time()
        clock = pygame.time.Clock()
        
        # 创建临时卡牌图片
        base_card = self.create_temp_card_surface(card_data, start_rect.width, start_rect.height)
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            elapsed = time() - start_time
            if elapsed >= duration:
                break
            
            # 计算当前位置和透明度
            progress = elapsed / duration
            t = 1 - (1 - progress) ** 2  # 二次缓动
            current_x = start_rect.x + (end_rect.x - start_rect.x) * t
            current_y = start_rect.y + (end_rect.y - start_rect.y) * t
            
            alpha = int(255 * (1 - progress)) # 透明度从255渐变到0
            current_rect = pygame.Rect(int(current_x), int(current_y), start_rect.width, start_rect.height)
            
            # 创建带透明度的临时表面
            temp_card = base_card.copy()
            temp_card.set_alpha(alpha)
            self.draw() # 重绘整个场景
            self.screen.blit(temp_card, current_rect) # 绘制淡出的卡牌
            pygame.display.flip()
            
            # 处理退出事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
        
    def create_temp_card_surface(self, card_data, width, height):
        """创建临时卡牌表面（用于动画）"""
        card_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        # 尝试加载图片
        if card_data.image_path and os.path.exists(card_data.image_path):
            try:
                img = pygame.image.load(card_data.image_path).convert_alpha()
                img = pygame.transform.smoothscale(img, (width, height))
                card_surface.blit(img, (0, 0))
            except:
                card_surface.fill((80, 80, 120))  # 加载失败用灰色
        else:
            card_surface.fill((80, 80, 120))  # 没有图片用灰色
        
        pygame.draw.rect(card_surface, (255, 255, 255), (0, 0, width, height), 3) # 边框
        
        return card_surface

    def move_ready_cards_to_battle(self):
        """准备区CD归零的卡牌移动到战斗区"""
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
        for waiting_slot in waiting_slots:
            if waiting_slot.has_card() and waiting_slot.cd_remaining == 0:
                # 找到第一个空的战斗区槽位
                target_battle_slot = None
                for battle_slot in battle_slots:
                    if not battle_slot.has_card():
                        target_battle_slot = battle_slot
                        break
                
                if target_battle_slot:
                    card_data = waiting_slot.card_data
                    
                    # 播放入场动画
                    start_rect = waiting_slot.rect.copy()
                    end_rect = target_battle_slot.rect.copy()
                    
                    self.play_blocking_move_animation(
                        card_data,
                        start_rect,
                        end_rect,
                        duration=0.3
                    )
                    
                    # 移动卡牌
                    target_battle_slot.set_card(card_data)
                    waiting_slot.remove_card()

    def adjust_battle_slots(self):
        """调整战斗槽位（向左填补空位）"""
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

    def remove_dead_cards(self):
        """移除 HP <= 0 的卡牌到弃牌堆"""
        dead_cards_info = [] # 收集所有死亡卡牌信息
        
        # 检查玩家战斗区
        for slot in self.player_battle_slots:
            if slot.has_card() and slot.card_data.hp <= 0:
                dead_cards_info.append({
                    'card_data': slot.card_data,
                    'slot': slot,
                    'owner': 'player',
                    'discard_slot': self.player_discard_slot
                })
        
        # 检查敌人战斗区
        for slot in self.enemy_battle_slots:
            if slot.has_card() and slot.card_data.hp <= 0:
                dead_cards_info.append({
                    'card_data': slot.card_data,
                    'slot': slot,
                    'owner': 'enemy',
                    'discard_slot': self.enemy_discard_slot
                })
        
        # 播放阵亡动画
        for info in dead_cards_info:
            start_rect = info['slot'].rect.copy()
            end_rect = info['discard_slot'].rect.copy()
            
            self.play_blocking_fade_move_animation(
                info['card_data'],
                start_rect,
                end_rect,
                duration=0.5
            )
            info['slot'].remove_card() # 移除卡牌
