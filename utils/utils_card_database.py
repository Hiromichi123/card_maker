"""
卡牌数据库系统
管理所有卡牌的详细信息
"""
import json
import os
from collections import defaultdict

class CardData:
    """卡牌数据类"""
    
    def __init__(self, card_id, name, rarity, atk, hp, level, traits, description, image_path):
        """
        Args:
            card_id: 卡牌唯一ID
            name: 卡牌名称
            rarity: 稀有度 (A/B/C/D)
            atk: 攻击力
            hp: 生命值
            level: 等级
            traits: 特性列表 ["特性1", "特性2"]
            description: 卡牌描述/介绍
            image_path: 图片路径
        """
        self.card_id = card_id
        self.name = name
        self.rarity = rarity
        self.atk = atk
        self.hp = hp
        self.level = level
        self.traits = traits if traits else []
        self.description = description
        self.image_path = image_path
    
    def to_dict(self):
        """转换为字典"""
        return {
            "card_id": self.card_id,
            "name": self.name,
            "rarity": self.rarity,
            "atk": self.atk,
            "hp": self.hp,
            "level": self.level,
            "traits": self.traits,
            "description": self.description,
            "image_path": self.image_path
        }
    
    @staticmethod
    def from_dict(data):
        """从字典创建"""
        return CardData(
            card_id=data.get("card_id", ""),
            name=data.get("name", "未命名"),
            rarity=data.get("rarity", "D"),
            atk=data.get("atk", 0),
            hp=data.get("hp", 0),
            level=data.get("level", 1),
            traits=data.get("traits", []),
            description=data.get("description", ""),
            image_path=data.get("image_path", "")
        )
    
    def __str__(self):
        """字符串表示"""
        traits_str = ", ".join(self.traits) if self.traits else "无"
        return (f"[{self.rarity}] {self.name} Lv.{self.level}\n"
                f"ATK: {self.atk} | HP: {self.hp}\n"
                f"特性: {traits_str}\n"
                f"{self.description}")


class CardDatabase:
    """卡牌数据库"""
    
    DATABASE_FILE = "data/card_database.json"
    
    def __init__(self):
        self.cards = {}  # {card_id: CardData}
        self.cards_by_rarity = defaultdict(list)  # {rarity: [CardData]}
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(self.DATABASE_FILE), exist_ok=True)
        
        # 加载数据库
        self.load()
    
    def add_card(self, card_data):
        """
        添加卡牌到数据库
        Args:
            card_data: CardData对象
        """
        self.cards[card_data.card_id] = card_data
        self.cards_by_rarity[card_data.rarity].append(card_data)
    
    def get_card(self, card_id):
        """
        根据ID获取卡牌
        Args:
            card_id: 卡牌ID
        Returns:
            CardData或None
        """
        return self.cards.get(card_id)
    
    def get_card_by_path(self, image_path):
        """
        根据图片路径获取卡牌
        Args:
            image_path: 图片路径
        Returns:
            CardData或None
        """
        for card in self.cards.values():
            if card.image_path == image_path:
                return card
        return None
    
    def get_cards_by_rarity(self, rarity):
        """获取指定稀有度的所有卡牌"""
        return self.cards_by_rarity.get(rarity, [])
    
    def get_all_cards(self):
        """获取所有卡牌"""
        return list(self.cards.values())
    
    def remove_card(self, card_id):
        """删除卡牌"""
        if card_id in self.cards:
            card = self.cards[card_id]
            self.cards_by_rarity[card.rarity].remove(card)
            del self.cards[card_id]
    
    def save(self):
        """保存数据库到文件"""
        data = {
            "cards": [card.to_dict() for card in self.cards.values()]
        }
        
        try:
            with open(self.DATABASE_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"卡牌数据库已保存: {len(self.cards)} 张卡牌")
            return True
        except Exception as e:
            print(f"卡牌数据库保存失败: {e}")
            return False
    
    def load(self):
        """从文件加载数据库"""
        if not os.path.exists(self.DATABASE_FILE):
            print("未找到卡牌数据库，创建示例数据")
            self.create_sample_data()
            self.save()
            return
        
        try:
            with open(self.DATABASE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.cards = {}
            self.cards_by_rarity = defaultdict(list)
            
            for card_dict in data.get("cards", []):
                card = CardData.from_dict(card_dict)
                self.add_card(card)
            
            print(f"卡牌数据库已加载: {len(self.cards)} 张卡牌")
        except Exception as e:
            print(f"卡牌数据库加载失败: {e}")
            self.create_sample_data()
    
    def create_sample_data(self):
        """创建示例数据"""
        sample_cards = [
            # SSR级别
            CardData(
                card_id="A_001",
                name="龙之怒",
                rarity="A",
                atk=100,
                hp=80,
                level=5,
                traits=["飞行", "火焰"],
                description="传说中的火龙，拥有焚烧一切的力量。",
                image_path="cards/A/dragon_fury.png"
            ),
            CardData(
                card_id="A_002",
                name="圣光守护者",
                rarity="A",
                atk=70,
                hp=120,
                level=5,
                traits=["守护", "治疗"],
                description="神圣的守护者，能够保护队友并恢复生命。",
                image_path="cards/A/holy_guardian.png"
            ),
            
            # SR级别
            CardData(
                card_id="B_001",
                name="暗影刺客",
                rarity="B",
                atk=80,
                hp=50,
                level=4,
                traits=["潜行", "暴击"],
                description="隐藏在黑暗中的杀手，一击必杀。",
                image_path="cards/B/shadow_assassin.png"
            ),
            CardData(
                card_id="B_002",
                name="冰霜法师",
                rarity="B",
                atk=60,
                hp=60,
                level=4,
                traits=["冰冻", "范围攻击"],
                description="操控冰雪的魔法师，能够冻结敌人。",
                image_path="cards/B/frost_mage.png"
            ),
            
            # R级别
            CardData(
                card_id="C_001",
                name="狂战士",
                rarity="C",
                atk=60,
                hp=60,
                level=3,
                traits=["狂暴"],
                description="失去理智的战士，攻击力随血量降低而提升。",
                image_path="cards/C/berserker.png"
            ),
            CardData(
                card_id="C_002",
                name="弓箭手",
                rarity="C",
                atk=50,
                hp=40,
                level=3,
                traits=["远程"],
                description="擅长远程攻击的弓箭手。",
                image_path="cards/C/archer.png"
            ),
            
            # N级别
            CardData(
                card_id="D_001",
                name="新兵",
                rarity="D",
                atk=30,
                hp=40,
                level=1,
                traits=[],
                description="刚入伍的普通士兵。",
                image_path="cards/D/recruit.png"
            ),
            CardData(
                card_id="D_002",
                name="村民",
                rarity="D",
                atk=20,
                hp=50,
                level=1,
                traits=["坚韧"],
                description="普通的村民，虽然弱小但意志坚定。",
                image_path="cards/D/villager.png"
            ),
        ]
        
        for card in sample_cards:
            self.add_card(card)
        
        print(f"创建了 {len(sample_cards)} 张示例卡牌")


# 全局卡牌数据库实例
_card_database = None

def get_card_database():
    """获取全局卡牌数据库实例"""
    global _card_database
    if _card_database is None:
        _card_database = CardDatabase()
    return _card_database