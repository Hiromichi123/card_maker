"""
卡牌数据库系统 基于assets/outputs目录结构 目录名直接对应稀有度 (SSS, SS, S, A, B, C, D)
"""
import json
import os
from collections import defaultdict

"""卡牌数据类"""
class CardData:
    RARITY_TO_LEVEL = {
        "SSS": 0,
        "SS": 1,
        "S": 2,
        "A": 3,
        "B": 4,
        "C": 5,
        "D": 6
    }
    
    def __init__(self, card_id, name, rarity, atk=0, hp=0, cd=0, traits=None, description="", image_path=""):
        self.card_id = card_id
        self.name = name
        self.rarity = rarity
        self.level = self.RARITY_TO_LEVEL.get(rarity, 3)  # 根据稀有度计算等级
        self.atk = atk
        self.hp = hp
        self.cd = cd
        self.traits = traits if traits else []
        self.description = description
        self.image_path = image_path  
    
    def to_dict(self):
        """转换为字典（用于保存）"""
        result = {
            "id": self.card_id.split('_')[-1],  # 只保存id部分，如 "001"
            "name": self.name,
            "level": self.level,
            "atk": self.atk,
            "hp": self.hp,
            "cd": self.cd
        }
        
        if self.traits:
            result["traits"] = self.traits
        if self.description:
            result["description"] = self.description
        
        return result
    
    """从字典创建"""
    @staticmethod
    def from_dict(data, rarity):
        card_id = f"{rarity}_{data['id']}"
        image_path = f"assets/outputs/{rarity}/{data['id']}.png"
        
        return CardData(
            card_id=card_id,
            name=data.get("name", "未命名"),
            rarity=rarity,
            atk=data.get("atk", 0),
            hp=data.get("hp", 0),
            cd=data.get("cd", 0),
            traits=data.get("traits", []),
            description=data.get("description", ""),
            image_path=image_path
        )
    
    def __str__(self):
        """字符串表示"""
        traits_str = ", ".join(self.traits) if self.traits else "无"
        return (f"[{self.rarity}] {self.name} Lv.{self.level}\n"
                f"ATK: {self.atk} | HP: {self.hp} | CD: {self.cd}\n"
                f"{traits_str}\n"
                f"{self.description if self.description else '暂无描述'}")


class CardDatabase:
    """卡牌数据库"""
    BASE_PATH = "assets/outputs"
    RARITY_DIRS = ["SSS", "SS", "S", "A", "B", "C", "D"]
    
    def __init__(self):
        self.cards = {}  # {card_id: CardData}
        self.cards_by_rarity = defaultdict(list)  # {rarity: [CardData]}
        self.path_to_id_map = {}  # {image_path: card_id}
        self.load_all() # 加载所有目录的卡牌
    
    def load_all(self):
        """加载所有稀有度目录下的卡牌"""
        total_loaded = 0
        
        for rarity in self.RARITY_DIRS:
            count = self.load_rarity_cards(rarity)
            total_loaded += count
        
        if total_loaded > 0:
            print(f"卡牌数据库已加载: {total_loaded} 张卡牌")
        else:
            print("警告: 未加载任何卡牌，请检查目录结构和 cards.json 文件")
    
    def load_rarity_cards(self, rarity):
        cards_json_path = os.path.join(self.BASE_PATH, rarity, "cards.json")
        
        if not os.path.exists(cards_json_path):
            return 0
        
        try:
            with open(cards_json_path, 'r', encoding='utf-8') as f:
                cards_data = json.load(f)
            count = 0
            for card_dict in cards_data:
                card = CardData.from_dict(card_dict, rarity)
                self.add_card(card)
                count += 1
            print(f"从 {rarity}/ 加载了 {count} 张卡牌")
            return count
            
        except Exception as e:
            print(f"加载 {cards_json_path} 失败: {e}")
            return 0
    
    def add_card(self, card_data):
        """添加卡牌到数据库"""
        self.cards[card_data.card_id] = card_data
        self.cards_by_rarity[card_data.rarity].append(card_data)
        
        # 建立路径映射
        if card_data.image_path:
            # 规范化路径
            normalized_path = card_data.image_path.replace('\\', '/')
            self.path_to_id_map[normalized_path] = card_data.card_id
    
    def get_card(self, card_id):
        """根据ID获取卡牌"""
        return self.cards.get(card_id)
    
    def get_card_by_level(self, level, number):
        """
        根据等级和编号获取卡牌
        level: 等级字符串，如 "A", "SSS", "S" 等
        number: 卡牌编号，如 "001", "002" 等
        返回: CardData 或 None
        """
        # 构造完整的 card_id
        card_id = f"{level}_{number}"
        return self.cards.get(card_id)
    
    def get_card_by_path(self, image_path):
        """根据图片路径获取卡牌"""
        normalized_path = image_path.replace('\\', '/')
        card_id = self.path_to_id_map.get(normalized_path) # 先查映射表
        if card_id:
            card = self.cards.get(card_id)
            return card
        print(f"未找到路径对应的卡牌: {image_path}")
        return None
    
    def get_cards_by_rarity(self, rarity):
        """获取指定稀有度的所有卡牌"""
        return self.cards_by_rarity.get(rarity, [])
    
    def get_all_cards(self):
        """获取所有卡牌"""
        return list(self.cards.values())
    
    def save_rarity_cards(self, rarity):
        cards_json_path = os.path.join(self.BASE_PATH, rarity, "cards.json")
        cards = self.get_cards_by_rarity(rarity) # 获取该稀有度的所有卡牌
        
        if not cards:
            print(f"稀有度 {rarity} 没有卡牌需要保存")
            return False
        
        cards_data = [card.to_dict() for card in sorted(cards, key=lambda c: c.card_id)] # 转换为字典列表
        os.makedirs(os.path.dirname(cards_json_path), exist_ok=True) # 确保目录存在
        
        try:
            with open(cards_json_path, 'w', encoding='utf-8') as f:
                json.dump(cards_data, f, ensure_ascii=False, indent=2)
            print(f"已保存 {len(cards)} 张卡牌到 {cards_json_path}")
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False
    
    def save_all(self):
        """保存所有稀有度的卡牌"""
        success = True
        for rarity in self.RARITY_DIRS:
            if self.get_cards_by_rarity(rarity):
                if not self.save_rarity_cards(rarity):
                    success = False
        return success
    
    def update_card(self, card_id, **kwargs):
        """更新卡牌信息"""
        if card_id in self.cards:
            card = self.cards[card_id]
            for key, value in kwargs.items():
                if hasattr(card, key):
                    setattr(card, key, value)
            print(f"卡牌 {card_id} 已更新")
            return True
        return False

# 全局卡牌数据库实例
_card_database = None
"""获取全局卡牌数据库实例"""
def get_card_database():
    global _card_database
    if _card_database is None:
        _card_database = CardDatabase()
    return _card_database
