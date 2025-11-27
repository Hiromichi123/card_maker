"""具体的技能效果实现"""
import random
import re
from game.skills.skill_base import SkillEffect, SkillTrigger

"""=====单/群 火球、冰封、闪电====="""
class FireballDamageEffect(SkillEffect):
    """火球伤害效果：对随机敌人造成伤害并播放火球动画"""
    def __init__(self, damage):
        super().__init__(
            name=f"火球{damage}",
            description=f"对随机敌人造成{damage}点火球伤害",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.damage = damage
    
    def execute(self, context):
        target = context.skill_target if hasattr(context, 'skill_target') and context.skill_target else context.get_random_enemy_slot()
        return context.deal_damage_to_slot(target, self.damage)
    
    def get_animation(self, context):
        from game.skills.skill_animations import FireballAnimation
        target = context.get_random_enemy_slot()
        context.skill_target = target
        if target:
            return FireballAnimation(context.attacker_slot, target, self.damage)
        return None

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

def create_fireball_skill(damage=1):
    """
    火球n 对随机敌人造成n点伤害
    在回合开始时BEFORE_ATTACK触发
    """
    from game.skills.skill_base import Skill
    
    skill = Skill(f"fireball{damage}", f"火球{damage}")
    skill.add_effect(FireballDamageEffect(damage))
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

"""=====防御、治愈、恢复、反击、闪避、吸血====="""
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
        # 受到伤害时被调用
        if hasattr(context, 'damage_amount'):
            effective_reduction = self.reduction
            breaker = getattr(context, 'armor_break_amount', 0)
            if breaker > 0:
                ignored = min(effective_reduction, breaker)
                effective_reduction -= ignored
                context.armor_break_amount = max(0, breaker - ignored)
            context.damage_amount = max(0, context.damage_amount - effective_reduction)
        return True
    
    def get_animation(self, context):
        """返回盾牌动画"""
        from game.skills.skill_animations import ShieldAnimation
        
        # 显示在防御者身上
        if hasattr(context, 'defender_slot') and context.defender_slot:
            overlay = None
            pending_target = getattr(context, 'pending_armor_break_target', None)
            if pending_target and pending_target is context.defender_slot:
                overlay = "tear"
                context.pending_armor_break_target = None
            return ShieldAnimation(context.defender_slot, overlay=overlay)
        return None

class BreakArmorEffect(SkillEffect):
    """破甲：在普通攻击前无视对方部分防御"""
    def __init__(self, amount):
        super().__init__(
            name=f"破甲{amount}",
            description=f"普通攻击无视对方{amount}点防御",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.amount = max(1, amount)

    def _get_target_slot(self, context):
        if context.defender_slot and context.defender_slot.has_card():
            return context.defender_slot
        return None

    def _get_total_defense(self, slot):
        if not slot or not slot.has_card():
            return 0
        traits = getattr(slot.card_data, 'traits', []) or []
        total = 0
        for trait in traits:
            match = re.match(r"防御(\d+)", trait)
            if match:
                total += int(match.group(1))
        return total

    def execute(self, context):
        target = self._get_target_slot(context)
        if not target:
            return False
        defense_total = self._get_total_defense(target)
        if defense_total <= 0:
            return False
        current = getattr(context, 'armor_break_amount', 0)
        context.armor_break_amount = max(current, self.amount)
        context.pending_armor_break_target = target
        return True

    def get_animation(self, context):
        # 动画与盾牌同步，在防御触发时显示
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

class InjuryEffect(SkillEffect):
    """受伤效果：普攻结束后对自己造成伤害"""
    def __init__(self, damage):
        super().__init__(
            name=f"受伤{damage}",
            description=f"普通攻击结束后自身损失{damage}点生命",
            trigger=SkillTrigger.AFTER_ATTACK
        )
        self.damage = damage
        self.last_target = None
    
    def can_trigger(self, context):
        return context.attacker_slot is not None and context.attacker_slot.has_card()
    
    def execute(self, context):
        if not self.can_trigger(context):
            self.last_target = None
            return False
        card = context.attacker_slot.card_data
        old_hp = card.hp
        card.hp = max(0, card.hp - self.damage)
        if old_hp == card.hp:
            self.last_target = None
            return False
        context.attacker_slot.card_data = card
        if hasattr(context.attacker_slot, 'start_hp_flash'):
            context.attacker_slot.start_hp_flash(old_hp, card.hp)
        self.last_target = context.attacker_slot
        return True
    
    def get_animation(self, context):
        if not self.last_target:
            return None
        from game.skills.skill_animations import BleedAnimation
        return BleedAnimation(self.last_target, self.damage)

class CounterAttackEffect(SkillEffect):
    """反击效果：受到普通攻击伤害后反击"""
    def __init__(self, damage):
        super().__init__(
            name=f"反击{damage}",
            description=f"受到普通攻击伤害后返还{damage}点伤害",
            trigger=SkillTrigger.AFTER_DAMAGED
        )
        self.damage = damage
        self.last_target = None
    
    def can_trigger(self, context):
        return (
            getattr(context, 'last_damage_taken', 0) > 0 and
            context.defender_slot and context.defender_slot.has_card() and
            context.last_attacker_slot and context.last_attacker_slot.has_card()
        )
    
    def execute(self, context):
        if not self.can_trigger(context):
            self.last_target = None
            return False
        self.last_target = context.last_attacker_slot
        return True
    
    def get_animation(self, context):
        if not self.last_target:
            return None
        from game.skills.skill_animations import CounterAttackAnimation
        wait_anim = getattr(context, 'current_attack_animation', None)
        target_slot = self.last_target
        anim = CounterAttackAnimation(context.defender_slot, target_slot, self.damage, wait_animation=wait_anim)
        def apply_damage():
            context.deal_damage_to_slot(target_slot, self.damage)
        if anim:
            anim.on_complete = apply_damage
        else:
            apply_damage()
        self.last_target = None
        return anim

class DodgeEffect(SkillEffect):
    """闪避效果：一定概率闪避普通攻击"""
    def __init__(self, dodge_level):
        super().__init__(
            name=f"闪避{dodge_level}",
            description="提高闪避普通攻击的概率",
            trigger=SkillTrigger.ON_DAMAGED
        )
        self.dodge_level = max(1, dodge_level)
        self.last_success = False
    
    def _dodge_rate(self):
        exponent = max(0, self.dodge_level - 1)
        return 0.9 - 0.6 * (0.5 ** exponent)
    
    def execute(self, context):
        self.last_success = False
        if not context.defender_slot or not context.defender_slot.has_card():
            return False
        rate = self._dodge_rate()
        if random.random() <= rate:
            context.damage_amount = 0
            self.last_success = True
            context.last_dodge_success = True
            return True
        return False
    
    def get_animation(self, context):
        if not self.last_success:
            return None
        from game.skills.skill_animations import DodgeShakeAnimation
        return DodgeShakeAnimation(context.defender_slot)

class VampireEffect(SkillEffect):
    """吸血效果：普通攻击造成伤害后自我治疗"""
    def __init__(self, heal_amount):
        super().__init__(
            name=f"吸血{heal_amount}",
            description=f"普通攻击造成伤害后，回复{heal_amount}点生命",
            trigger=SkillTrigger.AFTER_ATTACK
        )
        self.heal_amount = heal_amount
        self.last_heal_amount = 0
        self.last_source_pos = None
    
    def can_trigger(self, context):
        return (
            context.attacker_slot and
            context.attacker_slot.has_card() and
            getattr(context, 'last_attack_damage', 0) > 0
        )
    
    def execute(self, context):
        if not self.can_trigger(context):
            self.last_heal_amount = 0
            return False
        card = context.attacker_slot.card_data
        max_hp = getattr(card, 'max_hp', card.hp)
        if card.hp >= max_hp:
            self.last_heal_amount = 0
            return False
        heal_value = min(self.heal_amount, max_hp - card.hp)
        if heal_value <= 0:
            self.last_heal_amount = 0
            return False
        old_hp = card.hp
        card.hp = min(max_hp, card.hp + heal_value)
        context.attacker_slot.card_data = card
        if hasattr(context.attacker_slot, 'start_hp_flash'):
            context.attacker_slot.start_hp_flash(old_hp, card.hp)
        self.last_heal_amount = heal_value
        self.last_source_pos = getattr(context, 'last_attack_target_pos', None)
        return True
    
    def get_animation(self, context):
        if self.last_heal_amount <= 0:
            return None
        from game.skills.skill_animations import LifeStealAnimation
        source_pos = self.last_source_pos
        if not source_pos and getattr(context, 'last_attack_target_slot', None):
            slot = context.last_attack_target_slot
            if slot and hasattr(slot, 'rect'):
                source_pos = slot.rect.center
        return LifeStealAnimation(source_pos, context.attacker_slot, self.last_heal_amount)

def create_defense_skill(reduction): 
    """创建防御技能"""
    from game.skills.skill_base import Skill
    
    skill = Skill(f"defense_{reduction}", f"防御{reduction}")
    skill.add_effect(DefenseEffect(reduction))
    return skill

def create_break_armor_skill(amount=1):
    """创建破甲技能"""
    from game.skills.skill_base import Skill
    skill = Skill(f"break_armor_{amount}", f"破甲{amount}")
    skill.add_effect(BreakArmorEffect(amount))
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

def create_vampire_skill(heal_amount):
    """创建吸血技能"""
    from game.skills.skill_base import Skill
    skill = Skill(f"vampire_{heal_amount}", f"吸血{heal_amount}")
    skill.add_effect(VampireEffect(heal_amount))
    return skill

def create_injury_skill(damage):
    """创建受伤技能"""
    from game.skills.skill_base import Skill
    skill = Skill(f"injury_{damage}", f"受伤{damage}")
    skill.add_effect(InjuryEffect(damage))
    return skill

def create_counter_skill(damage):
    """创建反击技能"""
    from game.skills.skill_base import Skill
    skill = Skill(f"counter_{damage}", f"反击{damage}")
    skill.add_effect(CounterAttackEffect(damage))
    return skill

def create_dodge_skill(level):
    """创建闪避技能"""
    from game.skills.skill_base import Skill
    skill = Skill(f"dodge_{level}", f"闪避{level}")
    skill.add_effect(DodgeEffect(level))
    return skill

"""=====抽卡、还魂、加速、延迟、自毁====="""
class DrawCardsEffect(SkillEffect):
    """抽卡效果：普通攻击前从牌堆抽牌"""
    def __init__(self, amount):
        super().__init__(
            name=f"抽卡{amount}",
            description=f"普通攻击前从牌堆抽取{amount}张",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.amount = max(1, amount)
    
    def _resolve_owner(self, context):
        if context.attacker_owner:
            return context.attacker_owner
        return "player" if context.attacker_slot in context.scene.player_battle_slots else "enemy"
    
    def execute(self, context):
        owner = self._resolve_owner(context)
        deck = context.scene.player_deck if owner == "player" else context.scene.enemy_deck
        if len(deck) < self.amount:
            return False
        drawn = context.scene.draw_cards_from_deck(owner, self.amount, animate=True)
        return drawn == self.amount

    def get_animation(self, context):
        from game.skills.skill_animations import EnergyOrbAnimation
        owner = self._resolve_owner(context)
        deck = context.scene.player_deck if owner == "player" else context.scene.enemy_deck
        if len(deck) < self.amount:
            return None
        target_pos = context.scene.get_hand_entry_position(owner)
        if not target_pos:
            return None
        color = (255, 255, 255) if owner == "player" else (230, 230, 255)
        return EnergyOrbAnimation(context.attacker_slot, target_pos, color=color, radius=14)

class ReviveFromDiscardEffect(SkillEffect):
    """还魂效果：普通攻击前从弃牌堆取回卡牌"""
    def __init__(self, amount):
        super().__init__(
            name=f"还魂{amount}",
            description=f"普通攻击前从弃牌堆取回{amount}张",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.amount = max(1, amount)
    
    def _resolve_owner(self, context):
        if context.attacker_owner:
            return context.attacker_owner
        return "player" if context.attacker_slot in context.scene.player_battle_slots else "enemy"
    
    def execute(self, context):
        owner = self._resolve_owner(context)
        pile = context.scene.player_discard_pile if owner == "player" else context.scene.enemy_discard_pile
        if len(pile) < self.amount:
            return False
        restored = context.scene.draw_from_discard(owner, self.amount, animate=True)
        return restored == self.amount

    def get_animation(self, context):
        from game.skills.skill_animations import EnergyOrbAnimation
        owner = self._resolve_owner(context)
        pile = context.scene.player_discard_pile if owner == "player" else context.scene.enemy_discard_pile
        if len(pile) < self.amount:
            return None
        target_pos = context.scene.get_discard_center(owner)
        if not target_pos:
            return None
        color = (255, 245, 200) if owner == "player" else (200, 255, 240)
        return EnergyOrbAnimation(context.attacker_slot, target_pos, color=color, radius=18)

class AccelerateWaitingEffect(SkillEffect):
    """加速效果：减少己方准备区最左侧卡牌CD"""
    def __init__(self, amount):
        super().__init__(
            name=f"加速{amount}",
            description=f"令己方最左等待位CD减少{amount}",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.amount = max(1, amount)

    def _resolve_owner(self, context):
        if context.attacker_owner:
            return context.attacker_owner
        return "player" if context.attacker_slot in context.scene.player_battle_slots else "enemy"

    def execute(self, context):
        owner = self._resolve_owner(context)
        slot = context.scene.get_first_waiting_slot(owner)
        if not slot:
            return False
        slot.reduce_cd(self.amount)
        return True

    def get_animation(self, context):
        from game.skills.skill_animations import EnergyOrbAnimation
        owner = self._resolve_owner(context)
        slot = context.scene.get_first_waiting_slot(owner)
        if not slot:
            return None
        color = (255, 230, 180)
        return EnergyOrbAnimation(context.attacker_slot, slot.rect.center, color=color, radius=16)

class DelayWaitingEffect(SkillEffect):
    """延迟效果：增加敌方准备区最左侧卡牌CD"""
    def __init__(self, amount):
        super().__init__(
            name=f"延迟{amount}",
            description=f"令敌方最左等待位CD增加{amount}",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.amount = max(1, amount)

    def _resolve_owner(self, context):
        if context.attacker_owner:
            return context.attacker_owner
        return "player" if context.attacker_slot in context.scene.player_battle_slots else "enemy"

    def execute(self, context):
        owner = self._resolve_owner(context)
        target_owner = "enemy" if owner == "player" else "player"
        slot = context.scene.get_first_waiting_slot(target_owner)
        if not slot:
            return False
        return slot.increase_cd(self.amount)

    def get_animation(self, context):
        from game.skills.skill_animations import EnergyOrbAnimation
        owner = self._resolve_owner(context)
        target_owner = "enemy" if owner == "player" else "player"
        slot = context.scene.get_first_waiting_slot(target_owner)
        if not slot:
            return None
        color = (220, 200, 255)
        return EnergyOrbAnimation(context.attacker_slot, slot.rect.center, color=color, radius=16)

class SelfDestructEffect(SkillEffect):
    """自毁效果：释放完技能后自毁"""
    def __init__(self):
        super().__init__(
            name="自毁",
            description="释放完技能后自身HP归零并进入弃牌堆",
            trigger=SkillTrigger.BEFORE_ATTACK
        )

    def _resolve_owner(self, context):
        if context.attacker_owner:
            return context.attacker_owner
        return "player" if context.attacker_slot in context.scene.player_battle_slots else "enemy"

    def execute(self, context):
        slot = context.attacker_slot
        if not slot or not slot.has_card():
            return False
        owner = self._resolve_owner(context)
        scene = context.scene
        discard_slot = scene.player_discard_slot if owner == "player" else scene.enemy_discard_slot
        card_data = slot.card_data
        card_data.hp = 0
        if discard_slot and hasattr(slot, 'rect'):
            start_rect = slot.rect.copy()
            end_rect = discard_slot.rect.copy()
            scene.play_blocking_fade_move_animation(card_data, start_rect, end_rect, duration=0.4)
        slot.remove_card()
        scene.add_card_to_discard(owner, card_data)
        if hasattr(scene, '_handle_post_death_traits'):
            scene._handle_post_death_traits(card_data, owner)
        return True

    def get_animation(self, context):
        from game.skills.skill_animations import ExplosionAnimation
        if not context.attacker_slot:
            return None
        return ExplosionAnimation(context.attacker_slot)

def create_draw_skill(amount=1):
    """创建抽卡技能"""
    from game.skills.skill_base import Skill
    skill = Skill(f"draw_{amount}", f"抽卡{amount}")
    skill.add_effect(DrawCardsEffect(amount))
    return skill

def create_revive_skill(amount=1):
    """创建还魂技能"""
    from game.skills.skill_base import Skill
    skill = Skill(f"revive_{amount}", f"还魂{amount}")
    skill.add_effect(ReviveFromDiscardEffect(amount))
    return skill

def create_accelerate_skill(amount=1):
    """创建加速技能"""
    from game.skills.skill_base import Skill
    skill = Skill(f"accelerate_{amount}", f"加速{amount}")
    skill.add_effect(AccelerateWaitingEffect(amount))
    return skill

def create_delay_skill(amount=1):
    """创建延迟技能"""
    from game.skills.skill_base import Skill
    skill = Skill(f"delay_{amount}", f"延迟{amount}")
    skill.add_effect(DelayWaitingEffect(amount))
    return skill

def create_self_destruct_skill():
    """创建自毁技能"""
    from game.skills.skill_base import Skill
    skill = Skill("self_destruct", "自毁")
    skill.add_effect(SelfDestructEffect())
    return skill

class SilenceEffect(SkillEffect):
    """沉默技能：被动，禁用对面槽位卡牌的技能"""
    def __init__(self):
        super().__init__(
            name="沉默",
            description="禁用正对面槽位卡牌技能",
            trigger=SkillTrigger.ON_DEPLOY
        )

    def execute(self, context):
        # 实际逻辑由战斗场景判断沉默状态
        return False

def create_silence_skill():
    from game.skills.skill_base import Skill
    skill = Skill("silence", "沉默")
    skill.add_effect(SilenceEffect())
    return skill

"""=====免疫、不死、复活====="""
class ImmunityEffect(SkillEffect):
    """免疫技能伤害（通过场景逻辑实现）"""
    def __init__(self):
        super().__init__(
            name="免疫",
            description="免疫所有技能造成的伤害",
            trigger=SkillTrigger.ON_DEPLOY
        )

    def execute(self, context):
        return False

class UndyingEffect(SkillEffect):
    """不死效果：死亡后回到手牌"""
    def __init__(self):
        super().__init__(
            name="不死",
            description="阵亡后返回手牌",
            trigger=SkillTrigger.ON_DEATH
        )

    def execute(self, context):
        return False

class RebirthEffect(SkillEffect):
    """复活效果：死亡后一次性回到等待区"""
    def __init__(self):
        super().__init__(
            name="复活",
            description="阵亡后回到等待区重新冷却，仅触发一次",
            trigger=SkillTrigger.ON_DEATH
        )

    def execute(self, context):
        return False

def create_immunity_skill():
    from game.skills.skill_base import Skill
    skill = Skill("immunity", "免疫")
    skill.add_effect(ImmunityEffect())
    return skill

def create_undying_skill():
    from game.skills.skill_base import Skill
    skill = Skill("undying", "不死")
    skill.add_effect(UndyingEffect())
    return skill

def create_rebirth_skill():
    from game.skills.skill_base import Skill
    skill = Skill("rebirth", "复活")
    skill.add_effect(RebirthEffect())
    return skill

"""=====群/单、振奋、祝福====="""
class BlessingEffect(SkillEffect):
    """祝福效果：随机友方攻防提升"""
    def __init__(self, amount):
        super().__init__(
            name=f"祝福{amount}",
            description=f"随机友方ATK+{amount}、HP+{amount}",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.amount = max(1, amount)
        self.last_target = None
        self.pending_target = None

    def _resolve_owner(self, context):
        if context.attacker_owner:
            return context.attacker_owner
        return "player" if context.attacker_slot in context.scene.player_battle_slots else "enemy"

    def _get_friendly_slots(self, context):
        owner = self._resolve_owner(context)
        slots = context.scene.player_battle_slots if owner == "player" else context.scene.enemy_battle_slots
        return [slot for slot in slots if slot and slot.has_card()]

    def _apply_buff(self, slot):
        if not slot or not slot.has_card():
            return False
        card = slot.card_data
        old_hp = card.hp
        card.atk += self.amount
        card.hp += self.amount
        slot.card_data = card
        if hasattr(slot, 'start_hp_flash'):
            slot.start_hp_flash(old_hp, card.hp)
        return True

    def _select_target(self, context):
        if self.pending_target and self.pending_target.has_card():
            return self.pending_target
        slots = self._get_friendly_slots(context)
        if not slots:
            self.pending_target = None
            return None
        self.pending_target = random.choice(slots)
        return self.pending_target

    def execute(self, context):
        target = self.pending_target or self._select_target(context)
        self.pending_target = None
        if not target:
            self.last_target = None
            return False
        success = self._apply_buff(target)
        self.last_target = target if success else None
        return success

    def get_animation(self, context):
        target = self._select_target(context)
        if not target:
            return None
        from game.skills.skill_animations import BlessingAuraAnimation
        return BlessingAuraAnimation(target)

class GroupBlessingEffect(BlessingEffect):
    """群体祝福：所有友方攻防提升"""
    def __init__(self, amount):
        super().__init__(amount)
        self.name = f"群体祝福{amount}"
        self.description = f"所有友方ATK+{amount}、HP+{amount}"
        self.last_targets = []
        self.pending_targets = []
    def _collect_targets(self, context):
        valid = self._get_friendly_slots(context)
        self.pending_targets = [slot for slot in valid if slot and slot.has_card()]
        return self.pending_targets

    def execute(self, context):
        targets = self.pending_targets or self._collect_targets(context)
        self.pending_targets = []
        if not targets:
            self.last_targets = []
            return False
        success = False
        applied = []
        for slot in targets:
            if self._apply_buff(slot):
                success = True
                applied.append(slot)
        self.last_targets = applied
        return success

    def get_animation(self, context):
        targets = self.pending_targets or self._collect_targets(context)
        if not targets:
            return None
        from game.skills.skill_animations import MultiBlessingAuraAnimation
        return MultiBlessingAuraAnimation(targets)

class InspireEffect(SkillEffect):
    """振奋效果：入场时随机友方ATK提升"""
    def __init__(self, amount):
        super().__init__(
            name=f"振奋{amount}",
            description=f"随机友方ATK+{amount}",
            trigger=SkillTrigger.ON_DEPLOY
        )
        self.amount = max(1, amount)
        self.last_target = None
        self.pending_target = None

    def _resolve_owner(self, context):
        if context.attacker_owner:
            return context.attacker_owner
        return "player" if context.attacker_slot in context.scene.player_battle_slots else "enemy"

    def _get_friendly_slots(self, context):
        owner = self._resolve_owner(context)
        slots = context.scene.player_battle_slots if owner == "player" else context.scene.enemy_battle_slots
        valid = [slot for slot in slots if slot and slot.has_card()]
        if context.attacker_slot and context.attacker_slot.has_card() and context.attacker_slot not in valid:
            valid.append(context.attacker_slot)
        return valid

    def _apply_buff(self, slot):
        if not slot or not slot.has_card():
            return False
        card = slot.card_data
        card.atk += self.amount
        slot.card_data = card
        return True

    def _select_target(self, context):
        if self.pending_target and self.pending_target.has_card():
            return self.pending_target
        slots = self._get_friendly_slots(context)
        if not slots:
            self.pending_target = None
            return None
        self.pending_target = random.choice(slots)
        return self.pending_target

    def execute(self, context):
        target = self.pending_target or self._select_target(context)
        self.pending_target = None
        if not target:
            self.last_target = None
            return False
        success = self._apply_buff(target)
        self.last_target = target if success else None
        return success

    def get_animation(self, context):
        target = self._select_target(context)
        if not target:
            return None
        from game.skills.skill_animations import SwordInspireAnimation
        return SwordInspireAnimation(target)

class GroupInspireEffect(InspireEffect):
    """群体振奋：所有友方ATK提升"""
    def __init__(self, amount):
        super().__init__(amount)
        self.name = f"群体振奋{amount}"
        self.description = f"所有友方ATK+{amount}"
        self.last_targets = []
        self.pending_targets = []

    def _collect_targets(self, context):
        valid = self._get_friendly_slots(context)
        self.pending_targets = [slot for slot in valid if slot and slot.has_card()]
        return self.pending_targets

    def execute(self, context):
        targets = self.pending_targets or self._collect_targets(context)
        self.pending_targets = []
        if not targets:
            self.last_targets = []
            return False
        success = False
        applied = []
        for slot in targets:
            if self._apply_buff(slot):
                success = True
                applied.append(slot)
        self.last_targets = applied
        return success

    def get_animation(self, context):
        targets = self.pending_targets or self._collect_targets(context)
        if not targets:
            return None
        from game.skills.skill_animations import MultiSwordInspireAnimation
        return MultiSwordInspireAnimation(targets)

def create_blessing_skill(amount=1):
    from game.skills.skill_base import Skill
    skill = Skill(f"blessing_{amount}", f"祝福{amount}")
    skill.add_effect(BlessingEffect(amount))
    return skill

def create_group_blessing_skill(amount=1):
    from game.skills.skill_base import Skill
    skill = Skill(f"group_blessing_{amount}", f"群体祝福{amount}")
    skill.add_effect(GroupBlessingEffect(amount))
    return skill

def create_inspire_skill(amount=1):
    from game.skills.skill_base import Skill
    skill = Skill(f"inspire_{amount}", f"振奋{amount}")
    skill.add_effect(InspireEffect(amount))
    return skill

def create_group_inspire_skill(amount=1):
    from game.skills.skill_base import Skill
    skill = Skill(f"group_inspire_{amount}", f"群体振奋{amount}")
    skill.add_effect(GroupInspireEffect(amount))
    return skill

"""=====诅咒====="""
class CurseEffect(SkillEffect):
    """诅咒：攻击前削弱正对面敌方攻击力"""
    def __init__(self, amount):
        super().__init__(
            name=f"诅咒{amount}",
            description=f"正对面敌方ATK-{amount}",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
        self.amount = max(1, amount)
        self.pending_target = None
        self.last_target = None

    def _get_target_slot(self, context):
        if not context.attacker_slot:
            return None
        return context.scene.get_opposite_slot(context.attacker_slot)

    def execute(self, context):
        target = self.pending_target or self._get_target_slot(context)
        self.pending_target = None
        if not target or not target.has_card():
            self.last_target = None
            return False
        card = target.card_data
        old_atk = card.atk
        new_atk = max(0, card.atk - self.amount)
        if new_atk == old_atk:
            self.last_target = None
            return False
        card.atk = new_atk
        target.card_data = card
        self.last_target = target
        return True

    def get_animation(self, context):
        target = self._get_target_slot(context)
        if not target or not target.has_card():
            return None
        self.pending_target = target
        from game.skills.skill_animations import CurseMarkAnimation
        return CurseMarkAnimation(target)

def create_curse_skill(amount=1):
    from game.skills.skill_base import Skill
    skill = Skill(f"curse_{amount}", f"诅咒{amount}")
    skill.add_effect(CurseEffect(amount))
    return skill
