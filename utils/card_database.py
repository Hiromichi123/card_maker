"""
卡牌数据库系统
基于 assets/outputs 目录结构
目录名直接对应稀有度 (SSS, SS, S, A, B, C, D)
"""
import json
import os
from collections import defaultdict

class CardData:
    """卡牌数据类"""
    
    # 稀有度对应的默认等级（用于属性计算）
    RARITY_TO_LEVEL = {
        "SSS": 0,
        "SS": 1,
        "S": 2,
        "A": 3,
        "B": 4,
        "C": 5,
        "D": 6
    }
    
    def __init__(self, card_id, name, rarity, atk=0, hp=0, traits=None, description="", image_path=""):
        """
        Args:
            card_id: 卡牌ID（格式: SSS_001, A_002）
            name: 卡牌名称
            rarity: 稀有度 (SSS/SS/S/A/B/C/D)
            atk: 攻击力（可选）
            hp: 生命值（可选）
            traits: 特性列表（可选）
            description: 描述（可选）
            image_path: 图片路径
        """
        self.card_id = card_id
        self.name = name
        self.rarity = rarity
        self.level = self.RARITY_TO_LEVEL.get(rarity, 3)  # 根据稀有度计算等级
        
        self.atk = atk if atk > 0 else self._default_atk_by_rarity(rarity)
        self.hp = hp if hp > 0 else self._default_hp_by_rarity(rarity)
        self.traits = traits if traits else []
        self.description = description
        self.image_path = image_path
    
    def _default_atk_by_rarity(self, rarity):
        """根据稀有度返回默认攻击力"""
        defaults = {
            "SSS": 120,
            "SS": 100,
            "S": 80,
            "A": 60,
            "B": 40,
            "C": 30,
            "D": 20
        }
        return defaults.get(rarity, 30)
    
    def _default_hp_by_rarity(self, rarity):
        """根据稀有度返回默认生命值"""
        defaults = {
            "SSS": 150,
            "SS": 120,
            "S": 100,
            "A": 80,
            "B": 60,
            "C": 50,
            "D": 40
        }
        return defaults.get(rarity, 50)
    
    def to_dict(self):
        """转换为字典（用于保存）"""
        result = {
            "id": self.card_id.split('_')[-1],  # 只保存id部分，如 "001"
            "name": self.name,
            "level": self.level
        }
        
        # 只保存非默认值
        if self.atk != self._default_atk_by_rarity(self.rarity):
            result["atk"] = self.atk
        if self.hp != self._default_hp_by_rarity(self.rarity):
            result["hp"] = self.hp
        if self.traits:
            result["traits"] = self.traits
        if self.description:
            result["description"] = self.description
        
        return result
    
    @staticmethod
    def from_dict(data, rarity):
        """
        从字典创建
        Args:
            data: cards.json 中的数据
            rarity: 稀有度（目录名，如 "SSS", "A"）
        """
        card_id = f"{rarity}_{data['id']}"
        image_path = f"assets/outputs/{rarity}/{data['id']}.png"
        
        return CardData(
            card_id=card_id,
            name=data.get("name", "未命名"),
            rarity=rarity,
            atk=data.get("atk", 0),
            hp=data.get("hp", 0),
            traits=data.get("traits", []),
            description=data.get("description", ""),
            image_path=image_path
        )
    
    def __str__(self):
        """字符串表示"""
        traits_str = ", ".join(self.traits) if self.traits else "无"
        return (f"[{self.rarity}] {self.name} Lv.{self.level}\n"
                f"ATK: {self.atk} | HP: {self.hp}\n"
                f"特性: {traits_str}\n"
                f"{self.description if self.description else '暂无描述'}")


class CardDatabase:
    """卡牌数据库"""
    
    BASE_PATH = "assets/outputs"
    
    # 定义稀有度目录（按稀有度从高到低）
    RARITY_DIRS = ["SSS", "SS", "S", "A", "B", "C", "D"]
    
    def __init__(self):
        self.cards = {}  # {card_id: CardData}
        self.cards_by_rarity = defaultdict(list)  # {rarity: [CardData]}
        self.path_to_id_map = {}  # {image_path: card_id}
        
        # 加载所有目录的卡牌
        self.load_all()
    
    def load_all(self):
        """加载所有稀有度目录下的卡牌"""
        total_loaded = 0
        
        for rarity in self.RARITY_DIRS:
            count = self.load_rarity_cards(rarity)
            total_loaded += count
        
        if total_loaded > 0:
            print(f"卡牌数据库已加载: {total_loaded} 张卡牌")
            self.print_summary()
        else:
            print("警告: 未加载任何卡牌，请检查目录结构和 cards.json 文件")
            print(f"期望路径: {self.BASE_PATH}/{{SSS,SS,S,A,B,C,D}}/cards.json")
    
    def load_rarity_cards(self, rarity):
        """
        加载指定稀有度目录的卡牌
        Args:
            rarity: 稀有度（目录名，如 "SSS", "A"）
        Returns:
            加载的卡牌数量
        """
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
    
    def get_card_by_path(self, image_path):
        """根据图片路径获取卡牌"""
        # 规范化路径（统一使用正斜杠）
        normalized_path = image_path.replace('\\', '/')
        
        # 先查映射表
        card_id = self.path_to_id_map.get(normalized_path)
        if card_id:
            return self.cards.get(card_id)
        
        # 如果映射表没有，尝试从路径解析
        # 例如: assets/outputs/SSS/001.png -> SSS_001
        try:
            parts = normalized_path.split('/')
            if len(parts) >= 3 and parts[-3] == 'outputs':
                rarity = parts[-2]
                card_num = os.path.splitext(parts[-1])[0]
                card_id = f"{rarity}_{card_num}"
                card = self.cards.get(card_id)
                if card:
                    # 更新映射表
                    self.path_to_id_map[normalized_path] = card_id
                return card
        except Exception as e:
            print(f"解析路径失败: {image_path}, 错误: {e}")
        
        return None
    
    def get_cards_by_rarity(self, rarity):
        """获取指定稀有度的所有卡牌"""
        return self.cards_by_rarity.get(rarity, [])
    
    def get_all_cards(self):
        """获取所有卡牌"""
        return list(self.cards.values())
    
    def save_rarity_cards(self, rarity):
        """
        保存指定稀有度的卡牌到对应的 cards.json
        Args:
            rarity: 稀有度（如 "SSS", "A"）
        """
        cards_json_path = os.path.join(self.BASE_PATH, rarity, "cards.json")
        
        # 获取该稀有度的所有卡牌
        cards = self.get_cards_by_rarity(rarity)
        
        if not cards:
            print(f"稀有度 {rarity} 没有卡牌需要保存")
            return False
        
        # 转换为字典列表
        cards_data = [card.to_dict() for card in sorted(cards, key=lambda c: c.card_id)]
        
        # 确保目录存在
        os.makedirs(os.path.dirname(cards_json_path), exist_ok=True)
        
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
    
    def print_summary(self):
        """打印数据库摘要"""
        print("\n=== 卡牌数据库摘要 ===")
        for rarity in self.RARITY_DIRS:
            cards = self.get_cards_by_rarity(rarity)
            if cards:
                print(f"{rarity}: {len(cards)} 张")
        print(f"总计: {len(self.cards)} 张\n")


# 全局卡牌数据库实例
_card_database = None

def get_card_database():
    """获取全局卡牌数据库实例"""
    global _card_database
    if _card_database is None:
        _card_database = CardDatabase()
    return _card_database