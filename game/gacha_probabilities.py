"""抽卡概率配置表"""
from __future__ import annotations

# 全稀有度等级
RARITY_LEVELS = ("SSS", "SS", "S", "A", "B", "C", "D")

# 常规卡池 金币
simple_prob = {
    "SSS": 0.5,
    "SS": 1.5,
    "S": 2.5,
    "A": 8.5,
#===稀有率13%===
    "B": 17,
    "C": 30,
    "D": 40,
}

# 活动卡池 水晶
activity_prob = {
    "SSS": 1,
    "SS": 3,
    "S": 5,
    "A": 17,
#===稀有率26%===
    "B": 24,
    "C": 25,
    "D": 25,
}


# 特别卡池 水晶
special_prob = {
    "SSS": 5,
    "SS": 10,
    "S": 20,
    "A": 65
#===稀有率100%===
}

# 节日卡池 金币
holiday_prob = {
    "SSS": 2,
    "SS": 4,
    "S": 8,
    "A": 16,
#===稀有率30%===
    "B": 32,
    "C": 38
}

# 卡池映射表
_PROB_TABLES = {
    "simple": simple_prob,
    "activity": activity_prob,
    "special": special_prob,
    "holiday": holiday_prob,
    "SSS": {"SSS": 100},
    "SS": {"SS": 100},
    "S": {"S": 100},
    "A": {"A": 100}
}

def get_prob_table(key: str | None) -> dict[str, float]:
    """根据 key 返回概率表，默认 simple"""
    source = simple_prob if not key else _PROB_TABLES.get(key, simple_prob)
    return {rarity: float(source.get(rarity, 0)) for rarity in RARITY_LEVELS}



# 卡池配置列表&展示卡牌
GACHA_POOLS = [
    {"id": "normal", "name": "常规卡池", "bg_type": "bg/gacha_normal",
     "description": "常驻卡池，标准概率",
     "prob_table": "simple",
     "prob_label": "常规稀有爆率(13%)", "currency": "gold",
     "single_cost": 500, "ten_cost": 4500,
     "showcase_cards": ["D_001", "C_001", "B_001", "A_001", "S_001", "SS_001", "SSS_001", "SS_002", "S_002", "A_002", "B_002", "C_002", "D_002"]},
    {"id": "activity", "name": "活动卡池", "bg_type": "bg/gacha_activity",
     "description": "限时活动卡池，概率提升",
     "prob_table": "activity",
     "prob_label": "活动稀有爆率(26%)", "currency": "crystal",
     "single_cost": 30, "ten_cost": 270,
     "showcase_cards": ["SSS_001", "SSS_002", "SSS_003", "SSS_004", "SS_001", "SS_002", "S_001", "S_002"]},
    {"id": "special", "name": "特别卡池", "bg_type": "bg/gacha_special",
     "description": "特别卡池，高级卡牌",
     "prob_table": "special",
     "prob_label": "特别稀有爆率(100%)", "currency": "crystal",
     "single_cost": 100, "ten_cost": 880,
     "showcase_cards": ["SS_001", "SS_002", "SS_003", "SS_004", "SS_005", "SS_006"]},
    {"id": "holiday", "name": "节日卡池", "bg_type": "bg/gacha_holiday",
     "description": "节日限定卡池",
     "prob_table": "holiday",
     "prob_label": "节日稀有爆率(30%)", "currency": "gold",
     "single_cost": 1500, "ten_cost": 13500,
     "showcase_cards": ["A_003", "S_003", "SS_003", "SSS_003"]},
    {"id": "SSS级限定卡池", "name": "SSS限定卡池", "bg_type": "bg/gacha_sss",
     "description": "SSS特殊卡池",
     "prob_table": "SSS",
     "prob_label": "SSS特供爆率", "currency": "crystal",
     "single_cost": 600, "ten_cost": 5400,
     "showcase_cards": ["SSS_003", "SSS_004", "SSS_005"]},
    {"id": "SS级限定卡池", "name": "SS限定卡池", "bg_type": "bg/gacha_ss",
     "description": "SS特殊卡池",
     "prob_table": "SS",
     "prob_label": "SS特供爆率", "currency": "crystal",
     "single_cost": 280, "ten_cost": 2500,
     "showcase_cards": ["SS_001", "SS_002", "SS_003"]},
    {"id": "S级限定卡池", "name": "S限定卡池", "bg_type": "bg/gacha_s",
     "description": "S特殊卡池",
     "prob_table": "S",
     "prob_label": "S特供爆率", "currency": "crystal",
     "single_cost": 120, "ten_cost": 1080,
     "showcase_cards": ["S_001", "S_002", "S_003"]},
    {"id": "A级限定卡池", "name": "A级限定卡池", "bg_type": "bg/gacha_a",
     "description": "A特殊卡池",
     "prob_table": "A",
     "prob_label": "A特供爆率", "currency": "gold",
     "single_cost": 5000, "ten_cost": 45000,
     "showcase_cards": ["A_001", "A_002", "A_003", "A_004", "A_005"]}
]
