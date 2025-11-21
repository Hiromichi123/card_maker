"""
自选卡牌管理系统
用于临时存储Draft选择的卡牌
"""
import json
import os
import random
from config import CARD_BASE_PATH, CARD_PROBABILITIES

class DraftManager:
    """自选卡牌管理类"""
    
    TEMP_FILE = "data/draft_temp.json"
    TOTAL_CARDS = 28  # 总共28张卡牌
    CARDS_PER_PLAYER = 12  # 每位玩家12张
    
    def __init__(self):
        self.draft_pool = []  # 可选卡池 [{"path": ..., "rarity": ..., "picked": False, "picked_by": None}, ...]
        self.player1_cards = []  # 玩家1（下方）选择的卡牌
        self.player2_cards = []  # 玩家2（上方）选择的卡牌
        self.current_turn = "player1"  # 当前回合 ("player1" 或 "player2")
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.TEMP_FILE), exist_ok=True)
    
    def initialize_draft(self):
        """初始化自选卡池，随机抽取28张卡牌"""
        self.draft_pool = []
        self.player1_cards = []
        self.player2_cards = []
        self.current_turn = "player1"
        
        # 获取所有可用卡牌
        all_cards = self.get_all_cards()
        selected_cards = random.sample(all_cards, self.TOTAL_CARDS)
        
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
        """获取所有可用的卡牌"""
        all_cards = []
        
        for rarity in CARD_PROBABILITIES.keys():
            rarity_path = os.path.join(CARD_BASE_PATH, rarity)
            if os.path.exists(rarity_path):
                files = [f for f in os.listdir(rarity_path) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                
                for file in files:
                    all_cards.append({
                        "path": os.path.join(rarity_path, file),
                        "rarity": rarity
                    })

        return all_cards
    
    def pick_card(self, card_index):
        """
        选择一张卡牌
        Args:
            card_index: 卡牌在draft_pool中的索引
        Returns:
            bool: 是否选择成功
        """
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
            print(f"玩家1选择了卡牌: {card['rarity']} - {card['path']}")
        else:  # player2
            if len(self.player2_cards) >= self.CARDS_PER_PLAYER:
                return False
            self.player2_cards.append({
                "path": card["path"],
                "rarity": card["rarity"]
            })
            card["picked"] = True
            card["picked_by"] = "player2"
            print(f"玩家2选择了卡牌: {card['rarity']} - {card['path']}")
        
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