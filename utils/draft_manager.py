"""自选卡牌管理系统 用于存储Draft选择的卡牌"""
import json
import os
import random
from utils.card_database import get_card_database

CARD_BASE_PATH = "assets/outputs" # 路径
# 抽卡概率配置
CARD_PROBABILITIES = {
    "SSS": 8,
    "SS+": 8,
    "SS": 8,
    "S+": 8,
    "S": 8,
    "A+": 8,
    "A": 8,
    "B+": 8,
    "B": 8,
    "C+": 8,
    "C": 8,
    "D": 8,
    "#elna": 4
}

"""自选卡牌管理类"""
class DraftManager:
    TEMP_FILE = "data/draft_temp.json"
    TOTAL_CARDS = 28  # 总共28张卡牌
    CARDS_PER_PLAYER = 12  # 每位玩家12张

    def __init__(self):
        self.draft_pool = []  # 可选卡池 [{"path": ..., "rarity": ..., "picked": False, "picked_by": None}, ...]
        self.player1_cards = []  # 玩家1（下方）选择的卡牌
        self.player2_cards = []  # 玩家2（上方）选择的卡牌
        self.current_turn = "player1"  # 当前回合 ("player1" 或 "player2")
        self.card_db = get_card_database()
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.TEMP_FILE), exist_ok=True)
    
    def initialize_draft(self):
        """初始化自选卡池，随机抽取28张卡牌"""
        self.draft_pool = []
        self.player1_cards = []
        self.player2_cards = []
        self.current_turn = "player1"
        
        # 获取所有可用卡牌并按概率抽取
        cards_by_rarity = self.get_all_cards()
        selected_cards = self._select_cards_with_probabilities(cards_by_rarity)
        
        # 创建draft pool
        for card in selected_cards:
            self.draft_pool.append({
                "path": card["path"],
                "rarity": card["rarity"],
                "picked": False,
                "picked_by": None
            })
        
        print(f"Draft初始化完成: {len(self.draft_pool)}张卡牌")
    
    def get_all_cards(self):
        """获取所有可用的卡牌，按照稀有度分组"""
        grouped = {}

        if self.card_db:
            for card in self.card_db.get_all_cards():
                rarity = card.rarity
                if not card.image_path:
                    continue
                grouped.setdefault(rarity, []).append({
                    "path": card.image_path.replace('/', os.sep),
                    "rarity": rarity
                })
        else:
            for rarity in CARD_PROBABILITIES.keys():
                rarity_path = os.path.join(CARD_BASE_PATH, rarity)
                if not os.path.exists(rarity_path):
                    continue
                files = [f for f in os.listdir(rarity_path)
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                for file in files:
                    grouped.setdefault(rarity, []).append({
                        "path": os.path.join(rarity_path, file),
                        "rarity": rarity
                    })

        return grouped

    def _select_cards_with_probabilities(self, cards_by_rarity):
        """根据配置概率抽取目标数量卡牌"""
        total_available = sum(len(cards) for cards in cards_by_rarity.values())
        target = min(total_available, self.TOTAL_CARDS)
        if target <= 0:
            return []

        pools = {rarity: cards.copy() for rarity, cards in cards_by_rarity.items() if cards}
        rarities = [r for r in CARD_PROBABILITIES if r in pools and CARD_PROBABILITIES[r] > 0]
        weights = [CARD_PROBABILITIES[r] for r in rarities]

        selected = []
        while rarities and len(selected) < target:
            rarity = random.choices(rarities, weights=weights, k=1)[0]
            pool = pools.get(rarity)
            if not pool:
                idx = rarities.index(rarity)
                rarities.pop(idx)
                weights.pop(idx)
                continue
            card = pool.pop(random.randrange(len(pool)))
            selected.append(card)
            if not pool:
                idx = rarities.index(rarity)
                rarities.pop(idx)
                weights.pop(idx)

        if len(selected) < target:
            remaining = []
            for pool in pools.values():
                remaining.extend(pool)
            random.shuffle(remaining)
            needed = target - len(selected)
            selected.extend(remaining[:needed])

        return selected
    
    def pick_card(self, card_index):
        """选择一张卡牌"""
        if card_index < 0 or card_index >= len(self.draft_pool):
            return False
        
        card = self.draft_pool[card_index]
        
        # 检查卡牌是否已被选择
        if card["picked"]:
            return False
        
        # 检查当前玩家的卡组是否已满
        if self.current_turn == "player1":
            if len(self.player1_cards) >= self.CARDS_PER_PLAYER:
                return False
            self.player1_cards.append({
                "path": card["path"],
                "rarity": card["rarity"]
            })
            card["picked"] = True
            card["picked_by"] = "player1"
        else:  # player2
            if len(self.player2_cards) >= self.CARDS_PER_PLAYER:
                return False
            self.player2_cards.append({
                "path": card["path"],
                "rarity": card["rarity"]
            })
            card["picked"] = True
            card["picked_by"] = "player2"
        
        # 切换回合
        self.switch_turn()
        
        return True
    
    def switch_turn(self):
        """切换回合"""
        self.current_turn = "player2" if self.current_turn == "player1" else "player1"
    
    def is_draft_complete(self):
        """检查Draft是否完成"""
        return (len(self.player1_cards) >= self.CARDS_PER_PLAYER and 
                len(self.player2_cards) >= self.CARDS_PER_PLAYER)
    
    def save_draft(self):
        """保存Draft结果到临时文件"""
        data = {
            "player1_cards": self.player1_cards,
            "player2_cards": self.player2_cards,
            "completed": self.is_draft_complete()
        }
        
        try:
            with open(self.TEMP_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Draft结果已保存")
            return True
        except Exception as e:
            print(f"Draft保存失败: {e}")
            return False
    
    def load_draft(self):
        """加载Draft结果"""
        if not os.path.exists(self.TEMP_FILE):
            return False
        
        try:
            with open(self.TEMP_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.player1_cards = data.get("player1_cards", [])
            self.player2_cards = data.get("player2_cards", [])
            print(f"Draft结果已加载")
            return True
        except Exception as e:
            print(f"Draft加载失败: {e}")
            return False
    
    def get_available_cards(self):
        """获取未被选择的卡牌"""
        return [card for card in self.draft_pool if not card["picked"]]

# 全局Draft管理实例
_draft_manager = None
def get_draft_manager():
    """获取全局Draft管理实例"""
    global _draft_manager
    if _draft_manager is None:
        _draft_manager = DraftManager()
    return _draft_manager
