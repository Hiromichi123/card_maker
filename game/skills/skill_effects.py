"""具体的技能效果实现"""
import random
import pygame
from game.skills.skill_base import SkillEffect, SkillTrigger, TargetType

"""=====单/群 火球、冰封、闪电====="""
class FlyingEffect(SkillEffect):
    """飞行效果：跳过对面卡牌，直接攻击玩家"""
    def __init__(self):
        super().__init__(
            name="飞行",
            description="无视对面卡牌，直接攻击玩家",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
    
    def can_trigger(self, context):
        """检查是否触发（对面有卡时才生效）"""
        return context.defender_slot and context.defender_slot.has_card()
    
    def execute(self, context):
        """跳过对面卡牌"""
        # 修改目标为玩家本体
        context.defender_slot = None  # 清空防御者
        
        # 伤害将由普通攻击流程处理（攻击空槽位会打玩家）
        return True
    
    def get_animation(self, context):
        """飞行动画"""
        from game.skills.skill_animations import FlyOverAnimation
        return FlyOverAnimation(context.attacker_slot)

class IceDamageEffect(SkillEffect):
    """冰封伤害效果：对随机敌人造成伤害并播放冰花动画"""
    def __init__(self, damage):
        super().__init__(
            name=f"冰封{damage}",
            description=f"对随机敌人造成{damage}点冰冻伤害",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.damage = damage
    
    def execute(self, context):
        """执行冰封伤害（使用缓存的目标）"""
        # 使用缓存的随机目标（在get_animation时已选择）
        target = context.skill_target if hasattr(context, 'skill_target') and context.skill_target else context.get_random_enemy_slot()
        return context.deal_damage_to_slot(target, self.damage)
    
    def get_animation(self, context):
        """返回冰花动画"""
        from game.skills.skill_animations import IceBloomAnimation
        
        # 随机选择目标并缓存
        target = context.get_random_enemy_slot()
        context.skill_target = target  # 缓存目标
        if target:
            return IceBloomAnimation(target, self.damage)
        
        return None

class LightningDamageEffect(SkillEffect):
    """闪电伤害效果：对随机敌人造成伤害并闪烁闪电动画"""
    def __init__(self, damage):
        super().__init__(
            name=f"闪电{damage}",
            description=f"对随机敌人造成{damage}点闪电伤害",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.damage = damage
    
    def execute(self, context):
        """执行闪电伤害（使用缓存的目标）"""
        # 使用缓存的随机目标（在get_animation时已选择）
        target = context.skill_target if hasattr(context, 'skill_target') and context.skill_target else context.get_random_enemy_slot()
        return context.deal_damage_to_slot(target, self.damage)
    
    def get_animation(self, context):
        """返回闪电动画"""
        from game.skills.skill_animations import LightningStrikeAnimation
        
        # 随机选择目标并缓存
        target = context.get_random_enemy_slot()
        context.skill_target = target  # 缓存目标
        if target:
            return LightningStrikeAnimation(context.attacker_slot, target, self.damage)
        
        return None

class AOEFireballEffect(SkillEffect):
    """群体火球效果：对所有敌人造成火球伤害"""
    def __init__(self, damage):
        super().__init__(
            name=f"群体火球{damage}",
            description=f"对所有敌人造成{damage}点火球伤害",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.damage = damage
    
    def execute(self, context):
        """对所有敌方造成伤害（使用缓存的目标列表）"""
        targets = context.skill_targets if hasattr(context, 'skill_targets') and context.skill_targets else context.get_all_enemy_slots()
        success = False
        for target in targets:
            if context.deal_damage_to_slot(target, self.damage):
                success = True
        return success
    
    def get_animation(self, context):
        """返回多个火球动画"""
        from game.skills.skill_animations import MultiFireballAnimation
        
        targets = context.get_all_enemy_slots()
        context.skill_targets = targets  # 缓存目标列表
        if targets:
            return MultiFireballAnimation(context.attacker_slot, targets, self.damage)
        return None

class AOEIceEffect(SkillEffect):
    """群体冰封效果：对所有敌人造成冰封伤害"""
    def __init__(self, damage):
        super().__init__(
            name=f"群体冰封{damage}",
            description=f"对所有敌人造成{damage}点冰封伤害",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.damage = damage
    
    def execute(self, context):
        """对所有敌方造成伤害（使用缓存的目标列表）"""
        targets = context.skill_targets if hasattr(context, 'skill_targets') and context.skill_targets else context.get_all_enemy_slots()
        success = False
        for target in targets:
            if context.deal_damage_to_slot(target, self.damage):
                success = True
        return success
    
    def get_animation(self, context):
        """返回多个冰花动画"""
        from game.skills.skill_animations import MultiIceBloomAnimation
        
        targets = context.get_all_enemy_slots()
        context.skill_targets = targets  # 缓存目标列表
        if targets:
            return MultiIceBloomAnimation(targets, self.damage)
        return None

class AOELightningEffect(SkillEffect):
    """群体闪电效果：对所有敌人造成闪电伤害"""
    def __init__(self, damage):
        super().__init__(
            name=f"群体闪电{damage}",
            description=f"对所有敌人造成{damage}点闪电伤害",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.damage = damage
    
    def execute(self, context):
        """对所有敌方造成伤害（使用缓存的目标列表）"""
        targets = context.skill_targets if hasattr(context, 'skill_targets') and context.skill_targets else context.get_all_enemy_slots()
        success = False
        for target in targets:
            if context.deal_damage_to_slot(target, self.damage):
                success = True
        return success
    
    def get_animation(self, context):
        """返回多个闪电动画"""
        from game.skills.skill_animations import MultiLightningAnimation
        
        targets = context.get_all_enemy_slots()
        context.skill_targets = targets  # 缓存目标列表
        if targets:
            return MultiLightningAnimation(context.attacker_slot, targets, self.damage)
        return None

"""=====其他通用技能效果====="""
class DirectDamageEffect(SkillEffect):
    """直接伤害效果"""
    def __init__(self, damage, target_type=TargetType.OPPOSITE):
        super().__init__(
            name=f"造成{damage}点伤害",
            description=f"对目标造成{damage}点伤害",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.damage = damage
        self.target_type = target_type
    
    def execute(self, context):
        """执行伤害效果（使用缓存的目标）"""
        if self.target_type == TargetType.OPPOSITE:
            # 攻击对面槽位
            return context.deal_damage_to_slot(context.defender_slot, self.damage)
        
        elif self.target_type == TargetType.ENEMY_RANDOM:
            # 使用缓存的随机目标（在get_animation时已选择）
            target = context.skill_target if hasattr(context, 'skill_target') and context.skill_target else context.get_random_enemy_slot()
            return context.deal_damage_to_slot(target, self.damage)
        
        elif self.target_type == TargetType.PLAYER:
            # 直接攻击玩家
            return context.deal_damage_to_player(self.damage)
        
        return False
    
    def get_animation(self, context):
        """返回伤害动画（先选择目标并缓存）"""
        from game.skills.skill_animations import FireballAnimation
        
        if self.target_type == TargetType.ENEMY_RANDOM:
            # 随机选择目标并缓存到context
            target = context.get_random_enemy_slot()
            context.skill_target = target  # 缓存目标
            if target:
                return FireballAnimation(context.attacker_slot, target, self.damage)
        
        elif self.target_type == TargetType.OPPOSITE and context.defender_slot:
            context.skill_target = context.defender_slot  # 缓存目标
            return FireballAnimation(context.attacker_slot, context.defender_slot, self.damage)
        
        return None

class HealEffect(SkillEffect):
    """治疗效果"""
    def __init__(self, amount, target_type=TargetType.SELF):
        super().__init__(
            name=f"治疗{amount}",
            description=f"回复{amount}点生命值",
            trigger=SkillTrigger.AFTER_ATTACK
        )
        self.amount = amount
        self.target_type = target_type
    
    def execute(self, context):
        """执行治疗"""
        if self.target_type == TargetType.SELF:
            return context.heal_slot(context.attacker_slot, self.amount)
        
        return False

class DamageModifierEffect(SkillEffect):
    """伤害修正效果（增加或减少伤害）"""
    def __init__(self, multiplier=1.0, bonus=0):
        super().__init__(
            name=f"伤害{'增加' if multiplier > 1 else '减少'}",
            description=f"攻击伤害 ×{multiplier} +{bonus}",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.multiplier = multiplier
        self.bonus = bonus
    
    def execute(self, context):
        """修改伤害值"""
        context.damage = int(context.damage * self.multiplier) + self.bonus
        return True

class ShieldEffect(SkillEffect):
    """护盾效果：减少受到的伤害"""
    def __init__(self, reduction):
        super().__init__(
            name=f"护盾{reduction}",
            description=f"减少{reduction}点受到的伤害",
            trigger=SkillTrigger.ON_DAMAGED
        )
        self.reduction = reduction
    
    def execute(self, context):
        """减少伤害"""
        context.damage = max(0, context.damage - self.reduction)
        return True

class DrawCardEffect(SkillEffect):
    """抽卡效果"""
    def __init__(self, count=1):
        super().__init__(
            name=f"抽{count}张卡",
            description=f"抽取{count}张卡牌",
            trigger=SkillTrigger.ON_DEPLOY
        )
        self.count = count
    
    def execute(self, context):
        """抽卡"""
        who = "player" if context.attacker_owner == "player" else "enemy"
        success = False
        
        for _ in range(self.count):
            if context.scene.draw_card(who, animate=True):
                success = True
        
        return success

class ConditionalEffect(SkillEffect):
    """条件效果：满足条件时执行包装的效果"""
    def __init__(self, condition_func, wrapped_effect):
        """
        Args:
            condition_func: 条件函数，接受context参数，返回bool
            wrapped_effect: 被包装的效果
        """
        super().__init__(
            name=f"条件：{wrapped_effect.name}",
            description=f"满足条件时：{wrapped_effect.description}",
            trigger=wrapped_effect.trigger
        )
        self.condition_func = condition_func
        self.wrapped_effect = wrapped_effect
    
    def can_trigger(self, context):
        """检查条件是否满足"""
        return self.condition_func(context)
    
    def execute(self, context):
        """执行包装的效果"""
        return self.wrapped_effect.execute(context)
    
    def get_animation(self, context):
        """获取包装效果的动画"""
        return self.wrapped_effect.get_animation(context)

# ============= 正式创建技能 =============

def create_fireball_skill(damage=1):
    """
    火球n 对随机敌人造成n点伤害
    在回合开始时BEFORE_ATTACK触发
    """
    from game.skills.skill_base import Skill
    
    skill = Skill(f"fireball{damage}", f"火球{damage}")
    skill.add_effect(DirectDamageEffect(damage, TargetType.ENEMY_RANDOM))
    return skill

def create_ice_skill(damage=1):
    """
    冰封n 对随机敌人造成n点冰冻伤害
    在回合开始时BEFORE_ATTACK触发
    """
    from game.skills.skill_base import Skill
    
    skill = Skill(f"ice{damage}", f"冰封{damage}")
    skill.add_effect(IceDamageEffect(damage))
    return skill

def create_lightning_skill(damage=1):
    """
    闪电n 对随机敌人造成n点闪电伤害
    在回合开始时BEFORE_ATTACK触发
    """
    from game.skills.skill_base import Skill
    
    skill = Skill(f"lightning{damage}", f"闪电{damage}")
    skill.add_effect(LightningDamageEffect(damage))
    return skill

def create_aoe_fireball_skill(damage=1):
    """
    群体火球n 对所有敌人造成n点火球伤害
    在回合开始时BEFORE_ATTACK触发
    """
    from game.skills.skill_base import Skill
    
    skill = Skill(f"aoe_fireball{damage}", f"群体火球{damage}")
    skill.add_effect(AOEFireballEffect(damage))
    return skill

def create_aoe_ice_skill(damage=1):
    """
    群体冰封n 对所有敌人造成n点冰封伤害
    在回合开始时BEFORE_ATTACK触发
    """
    from game.skills.skill_base import Skill
    
    skill = Skill(f"aoe_ice{damage}", f"群体冰封{damage}")
    skill.add_effect(AOEIceEffect(damage))
    return skill

def create_aoe_lightning_skill(damage=1):
    """
    群体闪电n 对所有敌人造成n点闪电伤害
    在回合开始时BEFORE_ATTACK触发
    """
    from game.skills.skill_base import Skill
    
    skill = Skill(f"aoe_lightning{damage}", f"群体闪电{damage}")
    skill.add_effect(AOELightningEffect(damage))
    return skill

"""=====防御、治愈、恢复====="""
class DefenseEffect(SkillEffect):
    """防御效果：受到普通攻击时减伤"""
    def __init__(self, reduction):
        super().__init__(
            name=f"防御{reduction}",
            description=f"受到普通攻击时减少{reduction}点伤害",
            trigger=SkillTrigger.ON_DAMAGED
        )
        self.reduction = reduction
    
    def execute(self, context):
        """减少伤害"""
        # 这个方法会在受到伤害时被调用
        # 实际减伤逻辑需要在战斗系统中处理
        # 这里只是标记，实际减伤在battle_base_scene中处理
        if hasattr(context, 'damage_amount'):
            context.damage_amount = max(0, context.damage_amount - self.reduction)
        return True
    
    def get_animation(self, context):
        """返回盾牌动画"""
        from game.skills.skill_animations import ShieldAnimation
        
        # 显示在防御者身上
        if hasattr(context, 'defender_slot') and context.defender_slot:
            return ShieldAnimation(context.defender_slot)
        return None

class HealAllyEffect(SkillEffect):
    """治愈效果：对随机友方恢复生命"""
    def __init__(self, heal_amount):
        super().__init__(
            name=f"治愈{heal_amount}",
            description=f"对随机友方恢复{heal_amount}点生命",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.heal_amount = heal_amount
    
    def execute(self, context):
        """执行治愈效果"""
        # 使用缓存的目标
        target = context.skill_target if hasattr(context, 'skill_target') and context.skill_target else None
        
        if not target or not target.has_card():
            return False
        
        card = target.card_data
        max_hp = card.max_hp if hasattr(card, 'max_hp') else card.hp
        
        # 如果已满血则不治疗
        if card.hp >= max_hp:
            return False
        
        # 恢复生命
        old_hp = card.hp
        card.hp = min(max_hp, card.hp + self.heal_amount)
        
        # 更新槽位
        target.card_data = card
        if hasattr(target, 'start_hp_flash'):
            target.start_hp_flash(old_hp, card.hp)
        
        return True
    
    def get_animation(self, context):
        """返回治愈动画"""
        from game.skills.skill_animations import HealAnimation
        
        # 获取友方随机单位（不包括自己）
        attacker_owner = "player" if context.attacker_slot in context.scene.player_battle_slots else "enemy"
        
        if attacker_owner == "player":
            ally_slots = [s for s in context.scene.player_battle_slots 
                         if s.has_card() and s != context.attacker_slot]
        else:
            ally_slots = [s for s in context.scene.enemy_battle_slots 
                         if s.has_card() and s != context.attacker_slot]
        
        # 过滤掉满血的
        valid_targets = []
        for slot in ally_slots:
            card = slot.card_data
            max_hp = card.max_hp if hasattr(card, 'max_hp') else card.hp
            if card.hp < max_hp:
                valid_targets.append(slot)
        
        # 如果有友方可治疗，随机选择一个
        if valid_targets:
            import random
            target = random.choice(valid_targets)
            context.skill_target = target  # 缓存目标
            return HealAnimation(context.attacker_slot, target, self.heal_amount)
        
        # 如果没有友方，治疗自己
        card = context.attacker_slot.card_data
        max_hp = card.max_hp if hasattr(card, 'max_hp') else card.hp
        if card.hp < max_hp:
            context.skill_target = context.attacker_slot
            return HealAnimation(context.attacker_slot, context.attacker_slot, self.heal_amount)
        
        return None

class SelfHealEffect(SkillEffect):
    """恢复效果：对自己恢复生命"""
    def __init__(self, heal_amount):
        super().__init__(
            name=f"恢复{heal_amount}",
            description=f"恢复{heal_amount}点生命",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.heal_amount = heal_amount
    
    def execute(self, context):
        """执行恢复效果"""
        if not context.attacker_slot or not context.attacker_slot.has_card():
            return False
        
        card = context.attacker_slot.card_data
        max_hp = card.max_hp if hasattr(card, 'max_hp') else card.hp
        
        # 如果已满血则不恢复
        if card.hp >= max_hp:
            return False
        
        # 恢复生命
        old_hp = card.hp
        card.hp = min(max_hp, card.hp + self.heal_amount)
        
        # 更新槽位
        context.attacker_slot.card_data = card
        if hasattr(context.attacker_slot, 'start_hp_flash'):
            context.attacker_slot.start_hp_flash(old_hp, card.hp)
        
        return True
    
    def get_animation(self, context):
        """返回恢复动画"""
        from game.skills.skill_animations import SelfHealAnimation
        
        # 检查是否满血
        card = context.attacker_slot.card_data
        max_hp = card.max_hp if hasattr(card, 'max_hp') else card.hp
        
        if card.hp < max_hp:
            return SelfHealAnimation(context.attacker_slot, self.heal_amount)
        
        return None

def create_defense_skill(reduction):
    """创建防御技能"""
    from game.skills.skill_base import Skill
    
    skill = Skill(f"defense_{reduction}", f"防御{reduction}")
    skill.add_effect(DefenseEffect(reduction))
    return skill

def create_heal_ally_skill(heal_amount):
    """创建治愈技能"""
    from game.skills.skill_base import Skill
    
    skill = Skill(f"heal_ally_{heal_amount}", f"治愈{heal_amount}")
    skill.add_effect(HealAllyEffect(heal_amount))
    return skill

def create_self_heal_skill(heal_amount):
    """创建恢复技能"""
    from game.skills.skill_base import Skill
    skill = Skill(f"self_heal_{heal_amount}", f"恢复{heal_amount}")
    skill.add_effect(SelfHealEffect(heal_amount))
    return skill

""""=====吸血、飞行等====="""
# def create_vampire_skill():
#     """吸血：攻击后回复等量生命"""
#     from game.skills.skill_base import Skill
#     
#     skill = Skill("vampire", "吸血")
#     # 攻击后触发治疗，治疗量等于攻击力
#     skill.add_effect(HealEffect(0, TargetType.SELF))  # 具体数值在执行时计算
#     return skill

# def create_flying_skill():
#     """
#     飞行：跳过对面卡牌直接攻击玩家
#     """
#     from game.skills.skill_base import Skill
#     
#     skill = Skill("flying", "飞行")
#     skill.add_effect(FlyingEffect())
#     return skill

