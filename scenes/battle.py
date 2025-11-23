"""战斗场景"""
import pygame
import time
from config import *
from scenes.battle_base_scene import BattleBaseScene # 战斗场景基类
from utils.draft_manager import get_draft_manager # draft抽卡管理器
from game.hand_card import HandManager, HandCard # 手牌管理器，手牌类
from game.deck_renderer import DeckRenderer #　卡堆渲染器
from game.card_animation import AttackAnimation # 攻击动画

# 抽卡动画
GACHA_DELAY_INIT = 0.5  # 首张卡抽取延迟
GACHA_DELAY_BETWEEN = 0.3  # 每张卡间隔时间

"""战斗场景"""
class BattleScene(BattleBaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.battle_initialized = False # 初始化标志
        
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

    def enter(self):
        """进入场景初始化"""
        super().enter()
        if not self.battle_initialized:
            self.initialize_battle()
            self.battle_initialized = True

    """事件处理"""
    def handle_event(self, event):
        super().handle_event(event)
        # 游戏结束时只允许返回菜单
        if self.game_over:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")
            return
        
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
        super().update(dt)
        if self.game_over:
            return
        
        # 更新手牌
        self.player_hand.update(dt)
        self.enemy_hand.update(dt)
        
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
            self.enemy_auto_mode):
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
        super().draw()
        # 卡堆
        self.player_deck_renderer.draw(self.screen)
        self.enemy_deck_renderer.draw(self.screen)
        # 手牌
        self.player_hand.draw(self.screen)
        self.enemy_hand.draw(self.screen)

        # 绘制战斗动画
        for anim in self.battle_animations:
            if hasattr(anim, 'draw'):
                anim.draw(self.screen)
        # 游戏结束提示
        if self.game_over:
            self.draw_game_over_overlay()
    
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
                else:
                    # 战斗区已满
                    print(f"  [{owner_name}] 战斗区已满，{waiting_slot.card_data.name} 保留在准备区")

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
        if self.can_end_turn():
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
    
    def play_blocking_move_animation(self, card_data, start_rect, end_rect, duration=0.5):
        """播放阻塞式移动动画"""
        start_time = time.time()
        clock = pygame.time.Clock()
        
        # 创建临时卡牌图片
        temp_card = self.create_temp_card_surface(card_data, start_rect.width, start_rect.height)
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            elapsed = time.time() - start_time
            
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
        start_time = time.time()
        clock = pygame.time.Clock()
        
        # 创建临时卡牌图片
        base_card = self.create_temp_card_surface(card_data, start_rect.width, start_rect.height)
        
        while True:
            dt = clock.tick(FPS) / 1000.0
            elapsed = time.time() - start_time
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
