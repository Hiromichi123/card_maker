"""战斗场景基类"""
import math
import os
import pygame
from time import time
from config import *
from scenes.base.base_scene import BaseScene
from ui.button import Button
from utils.battle_component import CardSlot, HealthBar # 战斗场景组件
from utils.image_cache import get_scaled_image
from game.hand_card import HandManager, HandCard, CARD_WIDTH, CARD_HEIGHT # 手牌管理器，手牌类
from game.deck_renderer import DeckRenderer #　卡堆渲染器
from game.card_animation import SlideAnimation # 滑动动画
from game.card_animation import AttackAnimation # 攻击动画
from game.skills import get_skill_registry, BattleContext, SkillTrigger # 技能系统

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
HEALTH_X_RATIO = 0.05         # 血量条X位置
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
        self.title_font = get_font(int(32 * UI_SCALE))
        self.info_font = get_font(int(20 * UI_SCALE))

        self.load_turn_indicator_bg() # 回合指示器背景
        self.turn_indicator_anim_progress = 0.0
        self.turn_indicator_anim_duration = 0.6
        self.turn_indicator_animating = False
        self.turn_indicator_scale = 1.0
        self.turn_indicator_flash_alpha = 0

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

        # 卡堆渲染器
        player_deck_x = int(WINDOW_WIDTH * 0.05)
        player_deck_y = int(WINDOW_HEIGHT * 0.65)  # 玩家卡堆位置（左下）
        self.player_deck_renderer = DeckRenderer(player_deck_x, player_deck_y, is_player=True)
        enemy_deck_x = int(WINDOW_WIDTH * 0.05)
        enemy_deck_y = int(WINDOW_HEIGHT * 0.15)  # 敌人卡堆位置（左上）
        self.enemy_deck_renderer = DeckRenderer(enemy_deck_x, enemy_deck_y, is_player=False)

        # 按钮
        self.button_width = int(150 * UI_SCALE)
        self.button_height = int(50 * UI_SCALE)
        self.margin = int(20 * UI_SCALE)
        self.create_base_buttons()

        # 双方牌堆
        self.player_deck = []
        self.enemy_deck = []
        self.player_discard_pile = []
        self.enemy_discard_pile = []

        # 抽卡动画队列
        self.draw_queue = []
        self.draw_timer = 0.0

        # 手牌管理器
        self.player_hand = HandManager(is_player=True)
        self.player_hand.deck_position = (self.player_deck_renderer.position[0] + 60, self.player_deck_renderer.position[1] + 90)
        self.enemy_hand = HandManager(is_player=False)
        self.enemy_hand.deck_position = (self.enemy_deck_renderer.position[0] + 60, self.enemy_deck_renderer.position[1] + 90)

        # 回合状态
        self.current_turn = "player1"    # player1, player2
        self.turn_phase = "playing"      # playing（出牌阶段）, battling（战斗结算中）
        self.turn_number = 1             # 回合数
        self.cards_played_this_turn = 0  # 本回合已出牌数
        self.max_cards_per_turn = 1      # 每回合最多出牌数
        
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
        if not self.battle_initialized:
            self.initialize_battle()
            self.battle_initialized = True

    def update(self, dt):
        if self.game_over:
            return
        
        super().update(dt)
        self.update_turn_indicator_animation(dt)
        
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
        
        # 游戏结束时只允许返回菜单
        if self.game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")
            return

    def draw(self):
        self.screen.blit(self.background, (0, 0)) # 背景
        self.draw_turn_indicator() # 回合指示器
        self.draw_scene_labels() # 场景标识
        self.draw_health_bars() # 血量条
        self.draw_slots() # 槽位
        # 绘制按钮
        self.back_button.draw(self.screen) # 绘制返回按钮
        # 卡堆
        self.player_deck_renderer.draw(self.screen)
        self.enemy_deck_renderer.draw(self.screen)
        # 手牌
        self.player_hand.draw(self.screen)
        self.enemy_hand.draw(self.screen)
        # 战斗动画
        for anim in self.battle_animations:
            if hasattr(anim, 'draw'):
                anim.draw(self.screen)
        # 游戏结束提示
        if self.game_over:
            self.draw_game_over_overlay()

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
        self.start_turn_indicator_animation()

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
            # 每隔0.9秒处理一次攻击
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

    def can_play_card(self):
        """检查当前回合是否可以出牌"""
        result = self.turn_phase == "playing" and self.cards_played_this_turn < self.max_cards_per_turn
        return result

    def can_end_turn(self):
        """检查是否可以结束回合"""
        result = self.turn_phase == "playing" and self.cards_played_this_turn >= self.max_cards_per_turn
        return result

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
        bg_path = os.path.join("assets", "ui", "indicator.png")
        
        if os.path.exists(bg_path):
            try:
                self.turn_bg = pygame.image.load(bg_path).convert_alpha()
                # 缩放到合适大小
                bg_width = int(300 * UI_SCALE)
                bg_height = int(300 * UI_SCALE)
                self.turn_bg = pygame.transform.smoothscale(self.turn_bg, (bg_width, bg_height))
            except:
                self.turn_bg = self.create_default_turn_bg()
        else:
            self.turn_bg = self.create_default_turn_bg()
        
        # 位置（左侧中间）
        self.turn_bg_rect = self.turn_bg.get_rect(
            left=int(WINDOW_WIDTH * 0.05),
            centery=int(WINDOW_HEIGHT * 0.45)
        )
    
    def create_default_turn_bg(self):
        """创建默认回合指示器背景"""
        width = int(300 * UI_SCALE)
        height = int(200 * UI_SCALE)
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
        
        # 玩家血量条
        player_x = int(WINDOW_WIDTH * HEALTH_X_RATIO)
        player_y = int(WINDOW_HEIGHT * PLAYER_HEALTH_Y_RATIO)
        self.player_health_bar = HealthBar(
            player_x, player_y, bar_width, bar_height,
            self.player_max_hp, self.player_current_hp, is_player=True
        )
        
        # 敌人血量条
        enemy_x = int(WINDOW_WIDTH * HEALTH_X_RATIO)
        enemy_y = int(WINDOW_HEIGHT * ENEMY_HEALTH_Y_RATIO)
        self.enemy_health_bar = HealthBar(
            enemy_x, enemy_y, bar_width, bar_height,
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
    
    def create_base_buttons(self):
        """创建UI按钮"""
        # 返回按钮（左下角）
        self.back_button = Button(
            self.margin,
            int(WINDOW_HEIGHT * 0.95),
            self.button_width,
            self.button_height,
            "返回菜单",
            color=(100, 100, 100),
            hover_color=(130, 130, 130),
            font_size=24,
            on_click=lambda: self.switch_to("main_menu")
        )

    """====================基础绘制类===================="""
    def draw_scene_labels(self):
        """绘制场景标签"""
        # 敌人区域标签
        enemy_label = self.title_font.render("敌方区域", True, (255, 100, 100))
        enemy_rect = enemy_label.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.2)))
        
        # 半透明背景
        label_bg = pygame.Surface((enemy_rect.width + 20, enemy_rect.height + 10), pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 120))
        self.screen.blit(label_bg, (enemy_rect.x - 10, enemy_rect.y - 5))
        self.screen.blit(enemy_label, enemy_rect)
        
        # 玩家区域标签
        player_label = self.title_font.render("我方区域", True, (100, 255, 100))
        player_rect = player_label.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.8)))
        
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

    def start_turn_indicator_animation(self):
        self.turn_indicator_anim_progress = 0.0
        self.turn_indicator_animating = True

    def update_turn_indicator_animation(self, dt):
        if not self.turn_indicator_animating:
            self.turn_indicator_scale = 1.0
            self.turn_indicator_flash_alpha = 0
            return
        self.turn_indicator_anim_progress += dt
        t = min(1.0, self.turn_indicator_anim_progress / max(0.001, self.turn_indicator_anim_duration))
        self.turn_indicator_scale = 1.0 + 0.25 * math.sin(math.pi * t)
        self.turn_indicator_flash_alpha = int(120 * (1 - t))
        if self.turn_indicator_anim_progress >= self.turn_indicator_anim_duration:
            self.turn_indicator_animating = False
            self.turn_indicator_scale = 1.0
            self.turn_indicator_flash_alpha = 0

    def draw_turn_indicator(self):
        """绘制回合指示器"""
        self.screen.blit(self.turn_bg, self.turn_bg_rect) # 背景图
        if self.turn_indicator_flash_alpha > 0:
            flash_surface = pygame.Surface(self.turn_bg.get_size(), pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, self.turn_indicator_flash_alpha))
            self.screen.blit(flash_surface, self.turn_bg_rect.topleft)
        
        # 回合数
        turn_font = get_font(int(48 * UI_SCALE))
        turn_text = turn_font.render(f"回合 {self.turn_number}", True, (255, 215, 0))
        top_padding = int(18 * UI_SCALE)
        content_gap = int(10 * UI_SCALE)
        turn_rect = turn_text.get_rect(
            centerx=self.turn_bg_rect.centerx,
            top=self.turn_bg_rect.top + top_padding
        )
        self.screen.blit(turn_text, turn_rect)
        
        # 当前玩家
        player_font = get_font(int(28 * UI_SCALE))
        
        if self.current_turn == "player1":
            player_text = "玩家回合"
            color = (100, 255, 100)
        else:
            player_text = "敌人回合"
            color = (255, 100, 100)
        
        player_surface = player_font.render(player_text, True, color)
        scale_factor = self.turn_indicator_scale
        if scale_factor != 1.0:
            new_size = (
                max(1, int(player_surface.get_width() * scale_factor)),
                max(1, int(player_surface.get_height() * scale_factor))
            )
            player_surface = pygame.transform.smoothscale(player_surface, new_size)
        player_rect = player_surface.get_rect(
            centerx=self.turn_bg_rect.centerx,
            top=turn_rect.bottom + content_gap
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
            top=player_rect.bottom + content_gap
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
        hint_font = get_font(int(28 * UI_SCALE))
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

    def draw_cards_from_deck(self, who, amount, animate=False):
        """尝试从牌堆连续抽取多张卡"""
        drawn = 0
        for _ in range(amount):
            if self.draw_card(who, animate=animate):
                drawn += 1
            else:
                break
        return drawn

    def _reset_card_state(self, card_data):
        if not card_data:
            return
        max_hp = getattr(card_data, 'max_hp', card_data.hp)
        card_data.hp = max_hp

    def add_card_to_discard(self, owner, card_data):
        """将卡牌加入对应弃牌堆并更新显示"""
        if not card_data:
            return
        self._reset_card_state(card_data)
        pile = self.player_discard_pile if owner == 'player' else self.enemy_discard_pile
        pile.append(card_data)
        self._update_discard_preview(owner)

    def draw_from_discard(self, owner, amount, animate=False):
        """从弃牌堆取回卡牌并放回牌堆顶部"""
        pile = self.player_discard_pile if owner == 'player' else self.enemy_discard_pile
        deck = self.player_deck if owner == 'player' else self.enemy_deck
        renderer = self.player_deck_renderer if owner == 'player' else self.enemy_deck_renderer
        slot = self.player_discard_slot if owner == 'player' else self.enemy_discard_slot
        drawn_cards = []
        while len(drawn_cards) < amount and pile:
            card_data = pile.pop()
            self._reset_card_state(card_data)
            drawn_cards.append(card_data)
        for card_data in drawn_cards:
            if animate and slot and renderer and self.screen:
                start_rect = slot.rect.copy()
                end_rect = self.get_deck_rect(owner)
                if end_rect:
                    self.play_blocking_move_animation(card_data, start_rect, end_rect, duration=0.35)
            deck.insert(0, card_data)
        if renderer:
            renderer.set_count(len(deck))
        self._update_discard_preview(owner)
        return len(drawn_cards)

    def _update_discard_preview(self, owner):
        """更新弃牌堆槽位展示顶牌"""
        pile = self.player_discard_pile if owner == 'player' else self.enemy_discard_pile
        slot = self.player_discard_slot if owner == 'player' else self.enemy_discard_slot
        if not slot:
            return
        if pile:
            slot.set_card(pile[-1])
        else:
            slot.remove_card()

    def get_hand_entry_position(self, owner):
        """获取手牌入场动画的目标位置"""
        hand = self.player_hand if owner == 'player' else self.enemy_hand
        if hasattr(hand, 'deck_position') and hand.deck_position:
            return hand.deck_position
        return (hand.center_x, hand.center_y)

    def get_discard_center(self, owner):
        """获取弃牌堆的中心点"""
        slot = self.player_discard_slot if owner == 'player' else self.enemy_discard_slot
        if slot and hasattr(slot, 'rect'):
            return slot.rect.center
        return None

    def get_deck_rect(self, owner):
        """获取牌堆矩形（用于动画终点）"""
        renderer = self.player_deck_renderer if owner == 'player' else self.enemy_deck_renderer
        if not renderer:
            return None
        rect = pygame.Rect(0, 0, renderer.card_width, renderer.card_height)
        rect.topleft = renderer.position
        return rect

    def _get_slot_owner(self, slot):
        """返回槽位归属"""
        if slot in self.player_battle_slots:
            return 'player'
        if slot in self.enemy_battle_slots:
            return 'enemy'
        return None

    def get_opposite_slot(self, slot):
        """获取战斗区中对面的槽位"""
        owner = self._get_slot_owner(slot)
        if owner is None:
            return None
        own_slots = self.player_battle_slots if owner == 'player' else self.enemy_battle_slots
        opp_slots = self.enemy_battle_slots if owner == 'player' else self.player_battle_slots
        try:
            idx = own_slots.index(slot)
        except ValueError:
            return None
        if 0 <= idx < len(opp_slots):
            return opp_slots[idx]
        return None

    def is_slot_silenced(self, slot):
        """判断槽位是否被正对面的沉默技能禁用"""
        if not slot or not slot.has_card():
            return False
        opposite = self.get_opposite_slot(slot)
        if not opposite or not opposite.has_card():
            return False
        traits = getattr(opposite.card_data, 'traits', []) or []
        return "沉默" in traits

    def get_first_waiting_slot(self, owner):
        """获取最左侧有卡牌的准备槽位"""
        slots = self.player_waiting_slots if owner == 'player' else self.enemy_waiting_slots
        for slot in slots:
            if slot and slot.has_card():
                return slot
        return None

    def execute_attack(self, attacker_slot, defender_slot, defender_hp_ref):
        """执行单次攻击（集成技能系统）"""
        attacker_card = attacker_slot.card_data
        
        # 创建战斗上下文
        context = BattleContext(self)
        context.reset_attack_result()
        context.armor_break_amount = 0
        context.pending_armor_break_target = None
        
        # 设置攻击者和防御者
        attacker_owner = "player" if attacker_slot in self.player_battle_slots else "enemy"
        context.set_attacker(attacker_slot, attacker_owner)
        
        if defender_slot and defender_slot.has_card():
            defender_owner = "player" if defender_slot in self.player_battle_slots else "enemy"
            context.set_defender(defender_slot, defender_owner)
        else:
            context.defender_slot = None
            context.defender_owner = defender_hp_ref
        
        # 获取攻击者的技能
        skill_registry = get_skill_registry()
        if self.is_slot_silenced(attacker_slot):
            skills = []
        else:
            skills = skill_registry.get_skills_from_traits(attacker_card.traits)
        
        # 定义普通攻击执行函数（在技能动画完成后调用）
        def execute_normal_attack():
            if attacker_slot is None or not attacker_slot.has_card():
                return
            context.reset_attack_result()
            def resolve_damage():
                if attacker_slot is None or not attacker_slot.has_card():
                    context.armor_break_amount = 0
                    context.pending_armor_break_target = None
                    context.current_attack_animation = None
                    return
                try:
                    # 普通攻击伤害
                    if context.defender_slot and context.defender_slot.has_card():
                        # 攻击卡牌
                        defender_card = context.defender_slot.card_data
                        attacker_traits = getattr(attacker_card, "traits", []) or []
                        defender_traits = getattr(defender_card, "traits", []) or []
                        attacker_is_flying = "飞行" in attacker_traits
                        defender_is_flying = "飞行" in defender_traits

                        if defender_is_flying and not attacker_is_flying:
                            # 地面单位无法对空：伤害转移到防御者玩家
                            target_owner = context.defender_owner
                            if not target_owner:
                                target_owner = "player" if context.defender_slot in self.player_battle_slots else "enemy"
                            damage = attacker_card.atk
                            target_pos = None
                            if target_owner == "player":
                                self.player_current_hp -= damage
                                self.player_health_bar.set_hp(self.player_current_hp)
                                target_pos = self.player_health_bar.rect.center
                            else:
                                self.enemy_current_hp -= damage
                                self.enemy_health_bar.set_hp(self.enemy_current_hp)
                                target_pos = self.enemy_health_bar.rect.center
                            context.set_attack_result(
                                damage,
                                target_slot=None,
                                target_owner=target_owner,
                                target_pos=target_pos,
                                hit_player=True
                            )
                        else:
                            # 计算基础伤害
                            base_damage = attacker_card.atk
                            
                            # 检查防御者是否有防御技能（ON_DAMAGED触发）
                            if self.is_slot_silenced(context.defender_slot):
                                defender_skills = []
                            else:
                                defender_skills = skill_registry.get_skills_from_traits(defender_card.traits)
                            context.damage_amount = base_damage  # 将伤害存入context
                            
                            # 设置防御者上下文
                            defender_owner = "player" if context.defender_slot in self.player_battle_slots else "enemy"
                            original_attacker = context.attacker_slot
                            original_attacker_owner = context.attacker_owner
                            context.set_attacker(context.defender_slot, defender_owner)  # 临时切换为防御者视角
                            
                            # 触发防御技能
                            shield_animations = []
                            for skill in defender_skills:
                                on_damaged_effects = skill.get_effects_by_trigger(SkillTrigger.ON_DAMAGED)
                                for effect in on_damaged_effects:
                                    if effect.can_trigger(context):
                                        # 执行防御效果（修改context.damage_amount）
                                        effect.execute(context)
                                        # 获取盾牌动画
                                        shield_anim = effect.get_animation(context)
                                        if shield_anim:
                                            shield_anim.start()
                                            shield_animations.append(shield_anim)
                                            self.battle_animations.append(shield_anim)
                            
                            # 恢复攻击者上下文
                            context.set_attacker(original_attacker, original_attacker_owner)
                            
                            # 应用减伤后的伤害
                            final_damage = max(0, context.damage_amount)
                            old_hp = defender_card.hp
                            new_hp = max(0, old_hp - final_damage)
                            defender_card.hp = new_hp
                            
                            context.defender_slot.card_data = defender_card
                            context.defender_slot.start_hp_flash(old_hp, new_hp)
                            actual_damage = max(0, old_hp - new_hp)
                            target_pos = context.defender_slot.rect.center if hasattr(context.defender_slot, "rect") else None
                            defender_owner = "player" if context.defender_slot in self.player_battle_slots else "enemy"
                            context.set_attack_result(
                                actual_damage,
                                target_slot=context.defender_slot,
                                target_owner=defender_owner,
                                target_pos=target_pos,
                                hit_player=False
                            )
                            context.last_damage_taken = actual_damage
                            context.last_attacker_slot = attacker_slot
                            context.last_attacker_owner = attacker_owner

                            # 触发 AFTER_DAMAGED 技能（如反击）
                            if actual_damage > 0 and context.defender_slot and context.defender_slot.has_card():
                                context.set_attacker(context.defender_slot, defender_owner)
                                for skill in defender_skills:
                                    after_damaged_effects = skill.get_effects_by_trigger(SkillTrigger.AFTER_DAMAGED)
                                    for effect in after_damaged_effects:
                                        if effect.can_trigger(context):
                                            executed = effect.execute(context)
                                            if executed:
                                                anim = effect.get_animation(context)
                                                if anim:
                                                    anim.start()
                                                    self.battle_animations.append(anim)
                                context.set_attacker(original_attacker, original_attacker_owner)
                    else:
                        # 攻击玩家（飞行等技能可能清空了defender_slot）
                        damage = attacker_card.atk
                        if defender_hp_ref == "player":
                            self.player_current_hp -= damage
                            self.player_health_bar.set_hp(self.player_current_hp)
                            target_owner = "player"
                            target_pos = self.player_health_bar.rect.center
                        else:
                            self.enemy_current_hp -= damage
                            self.enemy_health_bar.set_hp(self.enemy_current_hp)
                            target_owner = "enemy"
                            target_pos = self.enemy_health_bar.rect.center
                        context.set_attack_result(
                            damage,
                            target_slot=None,
                            target_owner=target_owner,
                            target_pos=target_pos,
                            hit_player=True
                        )
                    
                    # 执行 AFTER_ATTACK 技能（如吸血）
                    for skill in skills:
                        after_effects = skill.get_effects_by_trigger(SkillTrigger.AFTER_ATTACK)
                        for effect in after_effects:
                            if effect.can_trigger(context):
                                executed = effect.execute(context)
                                if executed:
                                    anim = effect.get_animation(context)
                                    if anim:
                                        anim.start()
                                        self.battle_animations.append(anim)
                finally:
                    context.armor_break_amount = 0
                    context.pending_armor_break_target = None
                    context.current_attack_animation = None

            target_slot_for_anim = context.defender_slot if context.defender_slot and context.defender_slot.has_card() else None
            attack_anim = AttackAnimation(attacker_slot, target_slot_for_anim, on_complete=resolve_damage)
            self.battle_animations.append(attack_anim)
            context.current_attack_animation = attack_anim
        
        # 1. 收集所有技能动画
        skill_animations = []
        for skill in skills:
            before_effects = skill.get_effects_by_trigger(SkillTrigger.BEFORE_ATTACK)
            for effect in before_effects:
                if effect.can_trigger(context):
                    skill_anim = effect.get_animation(context)
                    if skill_anim:
                        # 为每个动画创建独立的伤害回调（使用闭包捕获当前effect）
                        def create_damage_callback(eff):
                            def execute_skill_damage():
                                eff.execute(context)
                            return execute_skill_damage
                        
                        skill_anim.on_hit = create_damage_callback(effect)
                        skill_animations.append(skill_anim)
                        break  # 每个技能只取第一个效果
                    else:
                        # 允许无动画的技能（例如抽卡/还魂）立即结算
                        effect.execute(context)
        
        # 2. 播放所有技能动画，只在最后一个动画完成时执行普通攻击
        if skill_animations:
            for i, anim in enumerate(skill_animations):
                # 只有最后一个动画完成时才执行普通攻击
                if i == len(skill_animations) - 1:
                    anim.on_complete = execute_normal_attack
                anim.start()
                self.battle_animations.append(anim)
        else:
            # 没有技能动画，直接执行普通攻击
            execute_normal_attack()

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
        cached = get_scaled_image(getattr(card_data, 'image_path', None), (width, height))
        if cached:
            card_surface.blit(cached, (0, 0))
        else:
            card_surface.fill((80, 80, 120))  # 没有图片或加载失败用灰色
        
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
                    owner = 'player' if owner_name == '玩家' else 'enemy'
                    self._trigger_on_deploy(target_battle_slot, owner)

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
            self.add_card_to_discard(info['owner'], info['card_data'])
            self._handle_post_death_traits(info['card_data'], info['owner'])

    def _handle_post_death_traits(self, card_data, owner):
        traits = getattr(card_data, 'traits', []) or []
        if not traits:
            return
        if "不死" in traits:
            self._revive_card_to_hand(card_data, owner)
            return
        if "复活" in traits:
            self._revive_card_to_waiting(card_data, owner)

    def _remove_card_from_discard(self, card_data, owner):
        pile = self.player_discard_pile if owner == 'player' else self.enemy_discard_pile
        if card_data in pile:
            pile.remove(card_data)
            self._update_discard_preview(owner)
            return True
        return False

    def _revive_card_to_hand(self, card_data, owner):
        if not self._remove_card_from_discard(card_data, owner):
            return
        hand = self.player_hand if owner == 'player' else self.enemy_hand
        discard_slot = self.player_discard_slot if owner == 'player' else self.enemy_discard_slot
        self._reset_card_state(card_data)
        if discard_slot and self.screen:
            start_rect = discard_slot.rect.copy()
            end_rect = pygame.Rect(0, 0, CARD_WIDTH, CARD_HEIGHT)
            end_rect.center = self.get_hand_entry_position(owner)
            self.play_blocking_move_animation(card_data, start_rect, end_rect, duration=0.4)
        hand.add_card(card_data, animate=False)

    def _revive_card_to_waiting(self, card_data, owner):
        if not hasattr(card_data, '_revive_consumed'):
            card_data._revive_consumed = False
        if getattr(card_data, '_revive_consumed', False):
            return
        slots = self.player_waiting_slots if owner == 'player' else self.enemy_waiting_slots
        target_slot = None
        for slot in slots:
            if slot and not slot.has_card():
                target_slot = slot
                break
        if not target_slot:
            return
        if not self._remove_card_from_discard(card_data, owner):
            return
        discard_slot = self.player_discard_slot if owner == 'player' else self.enemy_discard_slot
        self._reset_card_state(card_data)
        if discard_slot and self.screen:
            start_rect = discard_slot.rect.copy()
            end_rect = target_slot.rect.copy()
            self.play_blocking_move_animation(card_data, start_rect, end_rect, duration=0.4)
        target_slot.set_card(card_data)
        card_data._revive_consumed = True

    def _trigger_on_deploy(self, slot, owner):
        if not slot or not slot.has_card():
            return
        if self.is_slot_silenced(slot):
            return
        card = slot.card_data
        traits = getattr(card, 'traits', []) or []
        if not traits:
            return
        registry = get_skill_registry()
        skills = registry.get_skills_from_traits(traits)
        if not skills:
            return
        context = BattleContext(self)
        context.set_attacker(slot, owner)
        for skill in skills:
            effects = skill.get_effects_by_trigger(SkillTrigger.ON_DEPLOY)
            for effect in effects:
                if not effect.can_trigger(context):
                    continue
                animation = effect.get_animation(context)
                executed = effect.execute(context)
                if executed and animation:
                    animation.start()
                    self.battle_animations.append(animation)
