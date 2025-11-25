"""双人本地 选卡战斗场景"""
import pygame
from config import WINDOW_WIDTH, WINDOW_HEIGHT, UI_SCALE
from ui.button import Button
from scenes.battle.battle_base_scene import BattleBaseScene # 战斗场景基类
from utils.draft_manager import get_draft_manager # draft抽卡管理器

"""本地自选卡 战斗场景"""
class DraftBattleScene(BattleBaseScene):
    def __init__(self, screen):
        super().__init__(screen)

        # 敌人AI开关按钮（右侧中间偏上）
        self.toggle_width = int(160 * UI_SCALE)
        self.toggle_height = int(60 * UI_SCALE)
        self.create_buttons()

        # draft自动模式（仅用于敌人AI，可控制是否启用）
        self.enemy_auto_mode = True    # 敌人是否自动
        self.auto_timer = 0.0
        self.auto_delay = 2.0          # 敌人AI思考时间

    """====================核心功能===================="""
    def enter(self):
        super().enter()

    def update(self, dt):
        super().update(dt)
        
        # AI出牌逻辑
        if (self.current_turn == "player2" and self.turn_phase == "playing" and self.enemy_auto_mode):
            self.auto_timer += dt
            # 出牌阶段
            if self.cards_played_this_turn < self.max_cards_per_turn:
                if self.auto_timer >= self.auto_delay:
                    self.auto_timer = 0.0
                    played = self.enemy_ai_play_card()
                    if not played:
                        print("[AI] 无法出牌（无手牌或准备区满）")
            # 结束回合阶段
            elif self.cards_played_this_turn >= self.max_cards_per_turn:
                if self.auto_timer >= self.auto_delay * 0.5:
                    self.end_turn()
                    self.auto_timer = 0.0

    def handle_event(self, event):
        super().handle_event(event)

        # 手牌事件（根据回合判断）
        player_action = None
        enemy_action = None
        if self.current_turn == "player1":
            player_action = self.player_hand.handle_event(event)
        else:
            # 敌人回合，如果AI关闭则允许手动操作
            if not self.enemy_auto_mode:
                enemy_action = self.enemy_hand.handle_event(event)
        
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

    def draw(self):
        super().draw()
        self.end_turn_button.draw(self.screen) # 绘制结束回合按钮
        self.enemy_ai_toggle_button.draw(self.screen) # 绘制AI开关按钮
    
    def initialize_battle(self):
        db = super().initialize_battle()
        draft_manager = get_draft_manager()

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
        
        # 更新卡堆渲染器计数
        self.player_deck_renderer.set_count(len(self.player_deck))
        self.enemy_deck_renderer.set_count(len(self.enemy_deck))
        
        # 设置抽卡动画队列（开局各抽3张，交替抽取）
        self.draw_queue = []
        delay = 0.5
        for i in range(3):
            self.draw_queue.append(('player', delay))
            delay += 0.3
            self.draw_queue.append(('enemy', delay))
            delay += 0.3
        print(f"战斗初始化完成")

    """====================回合控制===================="""
    def switch_turn(self):
        """切换回合后 检查是否手牌为空并自动进入战斗"""
        super().switch_turn()

        # 检查手牌数量，决定是否跳过出牌阶段
        current_hand = self.player_hand if self.current_turn == "player1" else self.enemy_hand
        if len(current_hand.cards) == 0:
            self.cards_played_this_turn = self.max_cards_per_turn  # 已无手牌，标记为已完成出牌
            pygame.time.delay(500)  # 延迟0.5秒（给玩家反应时间）
            self.end_turn()  # 进入战斗，结束回合
        elif self.current_turn == "player2" and self.enemy_auto_mode: # 有手牌，正常提示
            print("[AI] 敌人AI将在 1.5秒后自动出牌")

    """====================其他===================="""
    def create_buttons(self):
        # 敌人AI开关按钮（右侧中间偏上）
        self.enemy_ai_toggle_button = Button(
            int(WINDOW_WIDTH * 0.85),
            int(WINDOW_HEIGHT * 0.45),
            self.toggle_width,
            self.toggle_height,
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
            self.button_width,
            self.button_height,
            "结束回合",
            color=(200, 100, 50),
            hover_color=(230, 130, 80),
            font_size=24,
            on_click=self.end_turn
        )

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

    def on_end_turn_click(self):
        """点击结束回合按钮"""
        if self.can_end_turn():
            self.end_turn()
        else:
            remaining = self.max_cards_per_turn - self.cards_played_this_turn
            print(f"必须先出 {remaining} 张卡才能结束回合！")

    def enemy_ai_play_card(self):
        """敌人AI自动出牌"""
        if not self.can_play_card():
            return False
        
        # 随机选择一张手牌
        if self.enemy_hand.cards:
            from random import choice
            random_card = choice(self.enemy_hand.cards)
            self.play_card_to_waiting(random_card)
            print(f"[AI] 敌人自动出牌: {random_card.card_data.name}")
            return True
        
        return False
