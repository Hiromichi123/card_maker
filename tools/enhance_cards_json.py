"""
为现有的 cards.json 添加默认属性
"""
import json
import os

BASE_PATH = "assets/outputs"

# 为每个等级定义默认属性
DEFAULT_STATS = {
    0: {"atk": 120, "hp": 150},  # SSS
    1: {"atk": 100, "hp": 120},  # SS
    2: {"atk": 80, "hp": 100},   # S
    3: {"atk": 60, "hp": 80},    # A
    4: {"atk": 40, "hp": 60},    # B
    5: {"atk": 30, "hp": 50},    # C
    6: {"atk": 20, "hp": 40}     # D
}

def enhance_level_cards(level):
    """为指定等级的卡牌添加默认属性"""
    level_dir = f"level{level}"
    cards_json_path = os.path.join(BASE_PATH, level_dir, "cards.json")
    
    if not os.path.exists(cards_json_path):
        print(f"未找到: {cards_json_path}")
        return
    
    with open(cards_json_path, 'r', encoding='utf-8') as f:
        cards = json.load(f)
    
    enhanced = 0
    for card in cards:
        # 如果没有 atk，添加默认值
        if "atk" not in card:
            card["atk"] = DEFAULT_STATS[level]["atk"]
            enhanced += 1
        
        # 如果没有 hp，添加默认值
        if "hp" not in card:
            card["hp"] = DEFAULT_STATS[level]["hp"]
            enhanced += 1
        
        # 如果没有 traits，添加空列表
        if "traits" not in card:
            card["traits"] = []
        
        # 如果没有 description，添加空字符串
        if "description" not in card:
            card["description"] = ""
    
    # 保存回文件
    with open(cards_json_path, 'w', encoding='utf-8') as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)
    
    print(f"Level {level}: 增强了 {len(cards)} 张卡牌（添加了 {enhanced} 个属性）")

def main():
    """处理所有等级"""
    print("开始增强 cards.json...\n")
    
    for level in range(7):
        enhance_level_cards(level)
    
    print("\n完成！")

if __name__ == "__main__":
    main()