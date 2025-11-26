"""技能注册表：管理所有技能 支持通过ID或traits标签快速获取技能"""
import re
from game.skills.skill_effects import (
    create_fireball_skill, # 火球n
    create_ice_skill, # 冰封n
    create_lightning_skill, # 闪电n
    create_aoe_fireball_skill, # 群体火球n
    create_aoe_ice_skill, # 群体冰封n
    create_aoe_lightning_skill, # 群体闪电n
    create_defense_skill, # 防御n
    create_heal_ally_skill, # 治愈n
    create_self_heal_skill, # 恢复n
)

class SkillRegistry:
    """技能注册表（单例）"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.skills = {}  # skill_id -> Skill对象
        self.trait_to_skill = {}  # trait -> skill_id 映射
        self._initialized = True
        
    def register_skill(self, skill, traits=None):
        """注册技能"""
        self.skills[skill.skill_id] = skill
        
        if traits:
            for trait in traits:
                self.trait_to_skill[trait] = skill.skill_id
    
    def get_skill(self, skill_id):
        """通过ID获取技能"""
        return self.skills.get(skill_id)
    
    def get_skill_by_trait(self, trait):
        """通过trait标签获取技能"""
        # 先检查直接映射
        skill_id = self.trait_to_skill.get(trait)
        if skill_id:
            return self.skills.get(skill_id)
        
        # 动态解析参数化技能
        # 火球n
        match = re.match(r"火球(\d+)", trait)
        if match:
            damage = int(match.group(1))
            return create_fireball_skill(damage)
        
        # 冰封n
        match = re.match(r"冰封(\d+)", trait)
        if match:
            damage = int(match.group(1))
            return create_ice_skill(damage)
        
        # 闪电n
        match = re.match(r"闪电(\d+)", trait)
        if match:
            damage = int(match.group(1))
            return create_lightning_skill(damage)
        
        # 群体火球n
        match = re.match(r"群体火球(\d+)", trait)
        if match:
            damage = int(match.group(1))
            return create_aoe_fireball_skill(damage)
        
        # 群体冰封n
        match = re.match(r"群体冰封(\d+)", trait)
        if match:
            damage = int(match.group(1))
            return create_aoe_ice_skill(damage)
        
        # 群体闪电n
        match = re.match(r"群体闪电(\d+)", trait)
        if match:
            damage = int(match.group(1))
            return create_aoe_lightning_skill(damage)
        
        # 防御n
        match = re.match(r"防御(\d+)", trait)
        if match:
            reduction = int(match.group(1))
            return create_defense_skill(reduction)
        
        # 治愈n
        match = re.match(r"治愈(\d+)", trait)
        if match:
            heal_amount = int(match.group(1))
            return create_heal_ally_skill(heal_amount)
        
        # 恢复n
        match = re.match(r"恢复(\d+)", trait)
        if match:
            heal_amount = int(match.group(1))
            return create_self_heal_skill(heal_amount)
        
        return None
    
    def get_skills_from_traits(self, traits):
        """从卡牌的traits列表获取所有技能"""
        skills = []
        for trait in traits:
            skill = self.get_skill_by_trait(trait)
            if skill:
                skills.append(skill)
        return skills


# 全局单例
_skill_registry = None

def get_skill_registry():
    """获取技能注册表单例"""
    global _skill_registry
    if _skill_registry is None:
        _skill_registry = SkillRegistry()
    return _skill_registry
