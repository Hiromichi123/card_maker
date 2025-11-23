"""
测试卡牌数据库
"""
import sys
sys.path.append('..')

from utils.card_database import get_card_database

def test_database():
    """测试数据库功能"""
    db = get_card_database()
    
    print("\n=== 测试1: 按等级查询 ===")
    level3_cards = db.get_cards_by_level(3)
    print(f"Level 3 (A级) 有 {len(level3_cards)} 张卡牌:")
    for card in level3_cards[:3]:  # 只显示前3张
        print(f"  - {card.card_id}: {card.name}")
    
    print("\n=== 测试2: 按稀有度查询 ===")
    a_cards = db.get_cards_by_rarity("A")
    print(f"A级稀有度有 {len(a_cards)} 张卡牌")
    
    print("\n=== 测试3: 按路径查询 ===")
    test_path = "assets/outputs/level3/001.png"
    card = db.get_card_by_path(test_path)
    if card:
        print(f"找到卡牌: {card.name}")
        print(card)
    
    print("\n=== 测试4: 更新卡牌 ===")
    db.update_card("level3_001", atk=100, traits=["强化", "测试"])
    card = db.get_card("level3_001")
    print(f"更新后: {card.name} - ATK: {card.atk}, 特性: {card.traits}")
    
    print("\n=== 测试5: 保存数据 ===")
    db.save_level_cards(3)

if __name__ == "__main__":
    test_database()