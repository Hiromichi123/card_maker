"""库存管理系统 负责卡牌的保存、读取、统计"""
import json
import os
from collections import defaultdict

SAVE_FILE = "data/inventory.json"

"""库存管理类"""
class Inventory:
    def __init__(self):
        self.cards = []  # 所有收集到的卡牌列表
        self.card_count = defaultdict(int)  # 卡牌数量统计 {card_path: count}
        self.total_draws = 0  # 总抽卡次数
        self.rarity_stats = defaultdict(int)  # 稀有度统计
        
        os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True) # 确保数据目录存在
        
        self.load() # 加载数据
    
    def add_card(self, card_path, rarity):
        """添加卡牌到库存"""
        card_data = {
            "path": card_path,
            "rarity": rarity,
        }
        
        self.cards.append(card_data)
        self.card_count[card_path] += 1
        self.rarity_stats[rarity] += 1
        self.total_draws += 1
        
    def add_cards(self, cards_list):
        """批量添加卡牌"""
        for card_path, rarity in cards_list:
            self.add_card(card_path, rarity)
        
        # 批量添加后保存
        self.save()
    
    def get_unique_cards(self):
        """获取所有不重复的卡牌"""
        unique_cards = {}
        for card in self.cards:
            path = card["path"]
            if path not in unique_cards:
                unique_cards[path] = {
                    "path": path,
                    "rarity": card["rarity"],
                    "count": self.card_count[path]
                }
        return list(unique_cards.values())
    
    def get_cards_by_rarity(self, rarity):
        """获取指定稀有度的卡牌"""
        return [card for card in self.get_unique_cards() 
                if card["rarity"] == rarity]
    
    def get_collection_stats(self):
        """获取收集统计"""
        unique_count = len(self.card_count)
        return {
            "total_draws": self.total_draws,
            "unique_cards": unique_count,
            "total_cards": len(self.cards),
            "rarity_stats": dict(self.rarity_stats)
        }
    
    def save(self):
        """保存到本地文件"""
        data = {
            "cards": self.cards,
            "card_count": dict(self.card_count),
            "total_draws": self.total_draws,
            "rarity_stats": dict(self.rarity_stats)
        }
        
        try:
            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"库存已保存: {len(self.cards)} 张卡牌")
        except Exception as e:
            print(f"保存失败: {e}")
    
    def load(self):
        """从本地文件加载"""
        if not os.path.exists(SAVE_FILE):
            print("未找到存档，创建新库存")
            return
        
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.cards = data.get("cards", [])
            self.card_count = defaultdict(int, data.get("card_count", {}))
            self.total_draws = data.get("total_draws", 0)
            self.rarity_stats = defaultdict(int, data.get("rarity_stats", {}))
            
            print(f"库存已加载: {len(self.cards)} 张卡牌")
        except Exception as e:
            print(f"加载失败: {e}")
    
    def clear(self):
        """清空库存"""
        self.cards = []
        self.card_count = defaultdict(int)
        self.total_draws = 0
        self.rarity_stats = defaultdict(int)
        self.save()


# 全局库存实例
_inventory = None

def get_inventory():
    """获取全局库存实例"""
    global _inventory
    if _inventory is None:
        _inventory = Inventory()
    return _inventory