"""技能注册表：管理所有技能 支持通过ID或traits标签快速获取技能"""
import re
from game.skills.skill_effects import (
    create_fireball_skill, # 火球n
    create_ice_skill, # 冰封n
    create_lightning_skill, # 闪电n
    create_aoe_fireball_skill, # 群体火球n
    create_aoe_ice_skill, # 群体冰封n
    create_aoe_lightning_skill, # 群体闪电n
    create_draw_skill, # 抽卡n
    create_revive_skill, # 还魂n
    create_accelerate_skill, # 加速n
    create_delay_skill, # 延迟n
    create_self_destruct_skill, # 自毁
    create_silence_skill, # 沉默
    create_immunity_skill, # 免疫
    create_undying_skill, # 不死
    create_rebirth_skill, # 复活
    create_blessing_skill, # 祝福n
    create_group_blessing_skill, # 群体祝福n
    create_inspire_skill, # 振奋n
    create_group_inspire_skill, # 群体振奋n
    create_curse_skill, # 诅咒n
    create_break_armor_skill, # 破甲n
    create_defense_skill, # 防御n
    create_heal_ally_skill, # 治愈n
    create_group_heal_skill, # 群体治愈n
    create_self_heal_skill, # 恢复n
    create_vampire_skill, # 吸血n
    create_injury_skill, # 受伤n
    create_counter_skill, # 反击n
    create_dodge_skill, # 闪避n
    create_berserk_skill, # 狂暴
    create_clone_skill, # 分身
    create_copy_skill, # 复制
    create_bombard_skill, # 炮击n
    create_group_bombard_skill, # 群体爆破n
    create_explode_on_death_skill, # 爆裂
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

        # 抽卡n
        match = re.match(r"抽卡(\d+)", trait)
        if match:
            amount = int(match.group(1))
            return create_draw_skill(amount)

        # 还魂n
        match = re.match(r"还魂(\d+)", trait)
        if match:
            amount = int(match.group(1))
            return create_revive_skill(amount)

        # 加速n
        match = re.match(r"加速(\d+)", trait)
        if match:
            amount = int(match.group(1))
            return create_accelerate_skill(amount)

        # 延迟n
        match = re.match(r"延迟(\d+)", trait)
        if match:
            amount = int(match.group(1))
            return create_delay_skill(amount)

        # 自毁
        if trait == "自毁":
            return create_self_destruct_skill()

        # 沉默
        if trait == "沉默":
            return create_silence_skill()

        # 免疫
        if trait == "免疫":
            return create_immunity_skill()

        # 不死
        if trait == "不死":
            return create_undying_skill()

        # 复活
        if trait == "复活":
            return create_rebirth_skill()
        
        # 祝福n
        match = re.match(r"祝福(\d+)", trait)
        if match:
            amount = int(match.group(1))
            return create_blessing_skill(amount)

        # 群体祝福n
        match = re.match(r"群体祝福(\d+)", trait)
        if match:
            amount = int(match.group(1))
            return create_group_blessing_skill(amount)

        # 振奋n
        match = re.match(r"振奋(\d+)", trait)
        if match:
            amount = int(match.group(1))
            return create_inspire_skill(amount)

        # 群体振奋n
        match = re.match(r"群体振奋(\d+)", trait)
        if match:
            amount = int(match.group(1))
            return create_group_inspire_skill(amount)

        # 诅咒n
        match = re.match(r"诅咒(\d+)", trait)
        if match:
            amount = int(match.group(1))
            return create_curse_skill(amount)

        # 破甲n
        match = re.match(r"破甲(\d+)", trait)
        if match:
            amount = int(match.group(1))
            return create_break_armor_skill(amount)

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

        # 群体治愈n
        match = re.match(r"群体治愈(\d+)", trait)
        if match:
            heal_amount = int(match.group(1))
            return create_group_heal_skill(heal_amount)
        
        # 恢复n
        match = re.match(r"恢复(\d+)", trait)
        if match:
            heal_amount = int(match.group(1))
            return create_self_heal_skill(heal_amount)
        
        # 吸血n
        match = re.match(r"吸血(\d+)", trait)
        if match:
            heal_amount = int(match.group(1))
            return create_vampire_skill(heal_amount)
        
        # 受伤n
        match = re.match(r"受伤(\d+)", trait)
        if match:
            dmg = int(match.group(1))
            return create_injury_skill(dmg)
        
        # 反击n
        match = re.match(r"反击(\d+)", trait)
        if match:
            dmg = int(match.group(1))
            return create_counter_skill(dmg)
        
        # 闪避n
        match = re.match(r"闪避(\d+)", trait)
        if match:
            lvl = int(match.group(1))
            return create_dodge_skill(lvl)

        # 狂暴
        if trait == "狂暴":
            return create_berserk_skill()

        # 分身
        if trait == "分身":
            return create_clone_skill()

        # 复制
        if trait == "复制":
            return create_copy_skill()

        # 炮击n
        match = re.match(r"炮击(\d+)", trait)
        if match:
            damage = int(match.group(1))
            return create_bombard_skill(damage)

        # 群体爆破n
        match = re.match(r"群体爆破(\d+)", trait)
        if match:
            damage = int(match.group(1))
            return create_group_bombard_skill(damage)

        # 爆裂
        if trait == "爆裂":
            return create_explode_on_death_skill()
        
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
