"""卡组管理系统 负责卡组的保存、读取、验证"""
import json
import os
from datetime import datetime

SAVE_FILE = "data/deck/player_deck/deck.json" # 默认保存路径
MAX_DECK_SIZE = 12  # 默认最大卡牌数量

"""卡组管理类"""
class DeckManager:
    def __init__(self, save_file: str = None, max_deck_size: int = None):
        if save_file is None:
            self.save_file = SAVE_FILE
        else:
            self.save_file = save_file
        if max_deck_size is None:
            self.max_deck_size = MAX_DECK_SIZE
        else:
            self.max_deck_size = max_deck_size

        self.deck = []
        os.makedirs(os.path.dirname(self.save_file), exist_ok=True) # 确保数据目录存在
        self.load() # 加载卡组
    
    def add_card(self, card_path, rarity):
        """添加卡牌到卡组"""
        if len(self.deck) >= self.max_deck_size:
            print(f"卡组已满（最多{self.max_deck_size}张）")
            return False
        
        card_data = {"path": card_path, "rarity": rarity}
        self.deck.append(card_data)
        return True
    
    def remove_card(self, index):
        """从卡组中移除卡牌"""
        if 0 <= index < len(self.deck):
            return self.deck.pop(index)
        return None
    
    def insert_card(self, index, card_path, rarity):
        """在指定位置插入卡牌"""
        if len(self.deck) >= self.max_deck_size:
            return False
        
        card_data = {"path": card_path, "rarity": rarity}
        self.deck.insert(index, card_data)
        return True
    
    def replace_card(self, index, card_path, rarity):
        """替换指定位置的卡牌"""
        if 0 <= index < len(self.deck):
            self.deck[index] = {"path": card_path, "rarity": rarity}
            return True
        return False

    def clear(self):
        """清空卡组"""
        self.deck = []
    
    def is_full(self):
        """卡组是否已满"""
        return len(self.deck) >= self.max_deck_size
    
    def get_deck(self):
        """获取当前卡组"""
        return self.deck.copy()
    
    def get_card_at(self, index):
        """获取指定位置的卡牌"""
        if 0 <= index < len(self.deck):
            return self.deck[index]
        return None
    
    def save(self):
        """保存卡组到本地文件"""
        data = {
            "deck": self.deck,
            "last_modified": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "deck_size": len(self.deck)
        }
        
        try:
            with open(self.save_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"卡组已保存: {len(self.deck)}/{self.max_deck_size} 张卡牌")
            return True
        except Exception as e:
            print(f"卡组保存失败: {e}")
            return False
    
    def load(self):
        """从本地文件加载卡组"""
        if not os.path.exists(self.save_file):
            print("未找到卡组存档，创建空卡组")
            return
        
        try:
            with open(self.save_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.deck = data.get("deck", [])
            print(f"卡组已加载: {len(self.deck)}/{self.max_deck_size} 张卡牌")
        except Exception as e:
            print(f"卡组加载失败: {e}")

# 全局卡组管理实例
_deck_manager = None

def get_deck_manager(save_file: str = None, max_deck_size: int = None):
    """获取全局卡组管理实例；首次可传 save_file/max_deck_size 覆盖默认设置"""
    global _deck_manager
    if _deck_manager is None:
        _deck_manager = DeckManager(save_file=save_file, max_deck_size=max_deck_size)
    return _deck_manager