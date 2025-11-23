"""
检查 JSON 文件内容
"""
import json
import os

BASE_PATH = "assets/outputs"
rarity = "D"
card_id = "008"

json_path = os.path.join(BASE_PATH, rarity, "cards.json")

print(f"读取文件: {json_path}")
print(f"文件存在: {os.path.exists(json_path)}")
print()

if os.path.exists(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"总共 {len(data)} 张卡牌")
    print()
    
    # 查找 008 号卡牌
    for card in data:
        if card['id'] == card_id:
            print(f"找到卡牌 {card_id}:")
            print(json.dumps(card, ensure_ascii=False, indent=2))
            print()
            print(f"atk = {card.get('atk')} (类型: {type(card.get('atk'))})")
            print(f"hp = {card.get('hp')} (类型: {type(card.get('hp'))})")
            print(f"cd = {card.get('cd')} (类型: {type(card.get('cd'))})")
            break
    else:
        print(f"未找到卡牌 {card_id}")
        print(f"现有卡牌ID: {[c['id'] for c in data[:10]]}")