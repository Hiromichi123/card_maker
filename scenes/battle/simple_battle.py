"""基于预设的牌库deck 关卡常规战斗场景（玩家 vs AI）"""
import os
import json
import random
import pygame
import copy
from scenes.battle.battle_base_scene import BattleBaseScene # 战斗场景基类
from utils.card_database import get_card_database, CardData # 卡牌数据库
from utils.scene_payload import pop_payload

PLAYER_DECK_PATH = "data/deck/player_deck/deck.json"  # 玩家牌库JSON路径
DEFAULT_ENEMY_DECK_PATH = "data/deck/enemy_deck/deck.json"    # 敌人默认配置
ENEMY_STAGE_DIR = os.path.join("data", "deck", "enemy_deck", "single_player")

class SimpleBattleScene(BattleBaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self._init_stage_settings()

    def _init_stage_settings(self):
        # JSON 文件路径
        self.player_deck_json = PLAYER_DECK_PATH
        self.enemy_deck_json = DEFAULT_ENEMY_DECK_PATH
        self.stage_id = "1-1"
        self.stage_name = ""
        self.default_background_path = self.background_image_path
        self.enemy_stage_dir = ENEMY_STAGE_DIR

        # 工作牌堆（按顺序抽取）
        self.w_pi_player_drale = []
        self._enemy_draw_pile = []

        # 敌人AI设置（SimpleBattle自带AI，一定开启）
        self.auto_timer = 0.0
        self.auto_delay = 1.0  # AI 思考时间

    """====================核心功能===================="""
    def enter(self):
        payload = pop_payload("simple_battle") or {}

        # 如果已执行过一局战斗，重新初始化基类以保证状态干净
        if self.battle_initialized:
            BattleBaseScene.__init__(self, self.screen)
            self._init_stage_settings()

        self._apply_payload(payload)
        super().enter()
    
    def update(self, dt):
        super().update(dt)
        
        # AI出牌逻辑
        if (self.current_turn == "player2" and self.turn_phase == "playing"):
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
                    self.auto_timer = 0.0
                    self.end_turn()
    
    def handle_event(self, event):
        super().handle_event(event)

        # 只处理玩家的手牌交互
        if self.current_turn == "player1":
            action = self.player_hand.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if action == "play" and self.can_play_card():
                    selected = self.player_hand.get_selected_card()
                    if selected:
                        self.play_card_to_waiting(selected)
                        self.clear_slot_highlights()
                    elif not selected:
                        print("本回合已出过牌！")

                elif action == "select" and self.can_play_card():
                    self.highlight_valid_slots()
                elif action == "deselect":
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
        
        # 玩家回合自动结束回合
        if self.can_end_turn():
            self.end_turn()
    
    def initialize_battle(self):
        # 加载双方decks
        self.player_deck = self._load_deck_json(self.player_deck_json)
        self.enemy_deck = self._load_deck_json(self.enemy_deck_json)

        random.shuffle(self.player_deck)
        random.shuffle(self.enemy_deck)

        # 填充抽牌堆
        self._player_draw_pile = self.player_deck[:]
        self._enemy_draw_pile = self.enemy_deck[:]

        random.shuffle(self._player_draw_pile)
        random.shuffle(self._enemy_draw_pile)

        # 更新卡堆渲染器计数
        self.player_deck_renderer.set_count(len(self._player_draw_pile))
        self.enemy_deck_renderer.set_count(len(self._enemy_draw_pile))

        # 设置抽卡动画队列（开局各抽3张，交替抽取）
        self.draw_queue = []
        delay = 0.5
        initial_draw = getattr(self, "INITIAL_HAND_SIZE", 3)
        for _ in range(initial_draw):
            self.draw_queue.append(("player", delay))
            delay += 0.3
            self.draw_queue.append(("enemy", delay))
            delay += 0.3
        print(f"战斗初始化完成 - 关卡 {self.stage_id}")

    """====================回合控制===================="""
    def switch_turn(self):
        """切换回合后 检查是否手牌为空并自动进入战斗"""
        super().switch_turn()

        # 检查手牌数量，决定是否跳过出牌阶段
        current_hand = self.player_hand if self.current_turn == "player1" else self.enemy_hand
        if len(current_hand.cards) == 0:
            self.cards_played_this_turn = self.max_cards_per_turn # 已无手牌，标记为已完成出牌
            pygame.time.delay(500) # 延迟0.5秒（给玩家反应时间）
            self.end_turn() # 进入战斗，结束回合
        elif self.current_turn == "player2":
            print("敌人回合，AI 将自动出牌")

    """====================其他===================="""
    def _load_deck_json(self, json_path):
        """从json文件或DeckManager获取deck entries，并转换为CardData列表"""
        deck = []
        entries = self._load_deck_entries(json_path)
        db = get_card_database()
        for entry in entries:
            path = entry.get("path", "")
            rarity = entry.get("rarity", "C")

            card_data = None
            try:
                card_data = copy.deepcopy(db.get_card_by_path(path)) # 使用 deepcopy 避免双方卡组引用同一对象！！
            except Exception as e:
                print(f"[SimpleBattle] db.get_card_by_path 抛出异常: path='{path}', err={e}")
                card_data = None

            if card_data is None:
                filename = os.path.splitext(os.path.basename(path))[0]
                inferred_id = f"{rarity}_{filename}"
                print(f"[SimpleBattle] 在数据库中找不到卡牌 record: path='{path}', inferred_id='{inferred_id}' - 使用 fallback CardData")
                card_data = CardData(
                    card_id=inferred_id,
                    name=entry.get("name", f"Card {filename}"),
                    rarity=rarity,
                    atk=entry.get("atk", 0),
                    hp=entry.get("hp", 0),
                    cd=entry.get("cd", 0),
                    image_path=path
                )

            deck.append(card_data)
    
        return deck

    def enemy_ai_play_card(self):
        """简单的敌人AI：随机出一张手牌（如果可出）"""
        if not self.can_play_card():
            return False

        if getattr(self.enemy_hand, "cards", None):
            # 假设 enemy_hand.cards 是 Card 对象列表，使用随机出一张
            try:
                from random import choice
                card_obj = choice(self.enemy_hand.cards)
                self.play_card_to_waiting(card_obj)
                return True
            except Exception as e:
                print(f"[AI] 出牌失败: {e}")
                return False

        return False

    def _load_deck_entries(self, json_path):
        if not json_path:
            return []
        if not os.path.exists(json_path):
            print(f"[SimpleBattle] 未找到卡组文件: {json_path}")
            return []
        try:
            with open(json_path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            return data.get("deck", [])
        except Exception as err:
            print(f"[SimpleBattle] 读取卡组失败: {json_path} -> {err}")
            return []

    def _apply_payload(self, payload: dict):
        stage_id = payload.get("stage_id") or payload.get("stage")
        if stage_id:
            self.stage_id = stage_id
        self.stage_name = payload.get("stage_name", self.stage_name)

        player_deck_path = payload.get("player_deck")
        if player_deck_path and os.path.exists(player_deck_path):
            self.player_deck_json = player_deck_path
        else:
            self.player_deck_json = PLAYER_DECK_PATH

        requested_enemy_path = payload.get("enemy_deck")
        self.enemy_deck_json = self._resolve_enemy_deck_path(requested_enemy_path)

        background_path = payload.get("background")
        self._apply_background(background_path)

    def _resolve_enemy_deck_path(self, requested_path=None) -> str:
        candidates = []
        if requested_path:
            candidates.append(requested_path)
        if self.stage_id:
            candidates.append(os.path.join(self.enemy_stage_dir, f"{self.stage_id}.json"))
        candidates.append(DEFAULT_ENEMY_DECK_PATH)
        for path in candidates:
            if path and os.path.exists(path):
                return path
        return DEFAULT_ENEMY_DECK_PATH

    def _apply_background(self, requested_path=None):
        if requested_path and os.path.exists(requested_path):
            self.background_image_path = requested_path
        elif self.stage_id:
            fallback = os.path.join("assets", "poster", f"{self.stage_id}.png")
            if os.path.exists(fallback):
                self.background_image_path = fallback
            else:
                self.background_image_path = self.default_background_path
        else:
            self.background_image_path = self.default_background_path
        self.background = self.load_background()
