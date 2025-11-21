"""
卡组管理系统
负责卡组的保存、读取、验证
"""
import json
import os
from datetime import datetime

class DeckManager:
    """卡组管理类"""
    
    SAVE_FILE = "data/deck.json"
    MAX_DECK_SIZE = 12  # 卡组最大卡牌数量
    
    def __init__(self):
        self.deck = []  # 当前卡组 [{"path": ..., "rarity": ...}, ...]
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.SAVE_FILE), exist_ok=True)
        
        # 加载卡组
        self.load()
    
    def add_card(self, card_path, rarity):
        """
        添加卡牌到卡组
        Args:
            card_path: 卡牌路径
            rarity: 稀有度
        Returns:
            bool: 是否成功添加
        """
        if len(self.deck) >= self.MAX_DECK_SIZE:
            print(f"卡组已满（最多{self.MAX_DECK_SIZE}张）")
            return False
        
        card_data = {
            "path": card_path,
            "rarity": rarity
        }
        
        self.deck.append(card_data)
        return True
    
    def remove_card(self, index):
        """
        从卡组中移除卡牌
        Args:
            index: 卡牌索引
        Returns:
            dict or None: 被移除的卡牌数据
        """
        if 0 <= index < len(self.deck):
            return self.deck.pop(index)
        return None
    
    def insert_card(self, index, card_path, rarity):
        """
        在指定位置插入卡牌
        Args:
            index: 插入位置
            card_path: 卡牌路径
            rarity: 稀有度
        Returns:
            bool: 是否成功插入
        """
        if len(self.deck) >= self.MAX_DECK_SIZE:
            return False
        
        card_data = {
            "path": card_path,
            "rarity": rarity
        }
        
        self.deck.insert(index, card_data)
        return True
    
    def replace_card(self, index, card_path, rarity):
        """
        替换指定位置的卡牌
        Args:
            index: 位置索引
            card_path: 卡牌路径
            rarity: 稀有度
        """
        if 0 <= index < len(self.deck):
            self.deck[index] = {
                "path": card_path,
                "rarity": rarity
            }
    
    def clear(self):
        """清空卡组"""
        self.deck = []
    
    def is_full(self):
        """卡组是否已满"""
        return len(self.deck) >= self.MAX_DECK_SIZE
    
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
            with open(self.SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"卡组已保存: {len(self.deck)}/{self.MAX_DECK_SIZE} 张卡牌")
            return True
        except Exception as e:
            print(f"卡组保存失败: {e}")
            return False
    
    def load(self):
        """从本地文件加载卡组"""
        if not os.path.exists(self.SAVE_FILE):
            print("未找到卡组存档，创建空卡组")
            return
        
        try:
            with open(self.SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.deck = data.get("deck", [])
            print(f"卡组已加载: {len(self.deck)}/{self.MAX_DECK_SIZE} 张卡牌")
        except Exception as e:
            print(f"卡组加载失败: {e}")


# 全局卡组管理实例
_deck_manager = None

def get_deck_manager():
    """获取全局卡组管理实例"""
    global _deck_manager
    if _deck_manager is None:
        _deck_manager = DeckManager()
    return _deck_manager