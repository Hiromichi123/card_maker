"""基于预设的牌库deck 关卡常规战斗场景（玩家 vs AI）"""
import os
import json
import pygame
from scenes.battle.battle_base_scene import BattleBaseScene  # 战斗场景基类
from utils.card_database import CardData

class SimpleBattleScene(BattleBaseScene):
    def __init__(self, screen, player_deck_json, enemy_deck_json):
        super().__init__(screen)
        self.player_deck_json = player_deck_json
        self.enemy_deck_json = enemy_deck_json

        # 内部牌堆（list of CardData 或 image path）
        self.player_deck = []
        self.enemy_deck = []

        # 抽卡索引或shuffle后的堆
        self._player_draw_pile = []
        self._enemy_draw_pile = []

        # 标记是否为 AI 自动模式（默认 True）
        self.enemy_auto_mode = True

    # ---------- Deck 载入 ----------
    def load_deck_from_json(self, json_path):
        """
        载入一个 deck JSON，返回 CardData 列表（只包含必要字段）。
        JSON 格式:
        {
          "deck": [
            {"path": "assets/outputs\\SS\\003.png", "rarity": "SS"},
            ...
          ]
        }
        """
        if not os.path.exists(json_path):
            print(f"[SimpleBattle] Deck JSON 不存在: {json_path}")
            return []

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cards = []
        for item in data.get("deck", []):
            path = item.get("path")
            rarity = item.get("rarity", "C")
            # 尝试从现有 CardData 数据库或按路径构造简单 CardData
            # 先尝试使用已有的数据库查找（若你的项目有 get_card_by_path）
            from utils.card_database import get_card_database
            db = get_card_database()
            card = db.get_card_by_path(path) if db else None

            if card is None:
                # fallback: 从路径解析 id，构造 minimal CardData
                filename = os.path.splitext(os.path.basename(path))[0]  # "003"
                card_id = f"{rarity}_{filename}"
                card = CardData(
                    card_id=card_id,
                    name=f"Card {filename}",
                    rarity=rarity,
                    atk=item.get("atk", 0),
                    hp=item.get("hp", 0),
                    cd=item.get("cd", 0),
                    image_path=path
                )
            cards.append(card)
        return cards

    # ---------- 初始化 ----------
    def initialize_battle(self):
        """
        初始化回合、血量、槽位、手牌，并以 JSON deck 填充牌堆。
        调用父类的 create_* 和 UI 初始化（在 Base 已实现）。
        """
        super().initialize_battle()  # 如果 base 有公共 init 行为

        # 载入 decks
        self.player_deck = self.load_deck_from_json(self.player_deck_json)
        self.enemy_deck = self.load_deck_from_json(self.enemy_deck_json)

        # shuffle or keep order
        import random
        self._player_draw_pile = self.player_deck[:]
        self._enemy_draw_pile = self.enemy_deck[:]
        random.shuffle(self._player_draw_pile)
        random.shuffle(self._enemy_draw_pile)

        # 清空手牌与准备区/战斗区（假设 base 提供）
        self.player_hand.clear()
        self.enemy_hand.clear()
        for s in (self.player_waiting_slots + self.player_battle_slots +
                  self.enemy_waiting_slots + self.enemy_battle_slots):
            s.remove_card()

        # 初始化 HP / 回合数等（如果 base 未完成）
        self.player_current_hp = getattr(self, "player_current_hp", 100)
        self.enemy_current_hp = getattr(self, "enemy_current_hp", 100)
        self.turn_number = 1
        self.current_turn = "player1"
        self.turn_phase = "playing"
        self.cards_played_this_turn = 0

        # 抽初始手牌（如果游戏规则是 INITIAL_HAND_SIZE）
        initial = getattr(self, "INITIAL_HAND_SIZE", 3)
        for _ in range(initial):
            self.draw_card_to_hand("player1", animate=False)
            self.draw_card_to_hand("player2", animate=False)

    # ---------- 抽卡/发牌接口（覆写 base 的抽卡函数或提供新的） ----------
    def draw_card_to_hand(self, who, animate=True):
        """
        从对应堆抽一张到手牌（player1 或 player2）。
        animate 可选用于禁用动画（初始化时禁用）。
        """
        if who == "player1":
            if not self._player_draw_pile:
                print("[SimpleBattle] 玩家抽牌堆已空")
                return None
            card_data = self._player_draw_pile.pop(0)
            self.player_hand.add_card(card_data, animate=animate)
            return card_data
        else:
            if not self._enemy_draw_pile:
                print("[SimpleBattle] 敌人抽牌堆已空")
                return None
            card_data = self._enemy_draw_pile.pop(0)
            self.enemy_hand.add_card(card_data, animate=animate)
            return card_data

    # ---------- 覆盖/扩展行为 ----------
    def switch_turn(self):
        """
        切换回合：复用 Base 的 switch_turn（若 base 有标准实现）。
        在 Simple 模式下保持同样的流程，AI 自动触发出牌逻辑由 update 处理。
        """
        super().switch_turn()
        # 如果你需要立即触发 AI，可以在这里触发状态重置
        if self.current_turn == "player2" and self.enemy_auto_mode:
            # 重置 AI 相关计时器（base 可能已有）
            self.auto_timer = 0.0
            # 如果没有 base 的 AI 主体，确保有 enemy_ai_play_card 可用

    def update(self, dt):
        """
        每帧更新：复用 Base 的 update（渲染+动画+战斗阶段等），
        并在 playing 阶段加入简单的 AI 出牌控制（如果 base 没有通用实现）。
        """
        # 调用 base 的 update 处理 UI、战斗动画等
        super().update(dt)

        # 仅当在 playing 且为敌人回合时，触发简单 AI（使用 base 的 enemy_ai_play_card）
        if (self.current_turn == "player2" and self.turn_phase == "playing" and
                self.enemy_auto_mode and not getattr(self, "is_switching_turn", False)):
            self.auto_timer += dt
            if getattr(self, "cards_played_this_turn", 0) < getattr(self, "max_cards_per_turn", 1):
                if self.auto_timer >= getattr(self, "auto_delay", 1.0):
                    self.auto_timer = 0.0
                    # 尝试调用 base 的 AI 出牌方法（如果在 base）
                    if hasattr(self, "enemy_ai_play_card"):
                        played = self.enemy_ai_play_card()
                        if not played:
                            # 无法出牌，可能手牌空或等待区满
                            pass
            else:
                # 达到本回合出牌数，触发结束回合
                if self.auto_timer >= getattr(self, "auto_delay", 1.0) * 0.5:
                    if hasattr(self, "end_turn"):
                        self.end_turn()
                        self.auto_timer = 0.0

    # ---------- 事件处理（player 操作） ----------
    def handle_event(self, event):
        """
        复用 Base 的 handle_event（包含鼠标点击手牌、拖拽、结束回合按钮）。
        如果必须区分 draft 的特殊交互，覆盖这里并调用 super 的通用处理。
        """
        super().handle_event(event)
