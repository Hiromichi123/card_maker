"""技能系统基类 使用策略模式和效果链模式"""
import pygame
from enum import Enum

class SkillTrigger(Enum):
    """技能触发时机"""
    ON_ATTACK = "on_attack"           # 攻击时触发
    BEFORE_ATTACK = "before_attack"   # 攻击前触发
    AFTER_ATTACK = "after_attack"     # 攻击后触发
    ON_DAMAGED = "on_damaged"         # 受到伤害时
    ON_DEPLOY = "on_deploy"           # 部署时：进入战斗槽位
    ON_DEATH = "on_death"             # 死亡时：进入弃牌堆
    TURN_START = "turn_start"         # 回合开始时
    TURN_END = "turn_end"             # 回合结束时


class TargetType(Enum):
    """目标类型"""
    NONE = "none"                     # 无目标
    SELF = "self"                     # 自身
    ENEMY_RANDOM = "enemy_random"     # 敌方随机
    ENEMY_ALL = "enemy_all"           # 敌方全体
    ALLY_RANDOM = "ally_random"       # 友方随机
    OPPOSITE = "opposite"             # 对面槽位
    PLAYER = "player"                 # 玩家本体


class SkillEffect:
    """技能效果基类"""
    def __init__(self, name, description="", trigger=SkillTrigger.BEFORE_ATTACK):
        self.name = name
        self.description = description
        self.trigger = trigger
        self.animation_duration = 0.5  # 动画持续时间
    
    def can_trigger(self, context):
        """检查是否可以触发"""
        return True
    
    def execute(self, context):
        """执行技能效果"""
        raise NotImplementedError("子类必须实现execute方法")
    
    def get_animation(self, context):
        """获取技能动画"""
        return None

class Skill:
    """技能类：包含多个技能效果的组合"""
    def __init__(self, skill_id, name, effects=None):
        self.skill_id = skill_id
        self.name = name
        self.effects = effects or []  # 技能效果列表
    
    def add_effect(self, effect):
        """添加技能效果"""
        self.effects.append(effect)
        return self
    
    def get_effects_by_trigger(self, trigger):
        """获取指定触发时机的效果"""
        return [e for e in self.effects if e.trigger == trigger]
    
    def execute_trigger(self, trigger, context):
        """执行指定触发时机的所有效果"""
        animations = []
        effects = self.get_effects_by_trigger(trigger)
        
        for effect in effects:
            if effect.can_trigger(context):
                success = effect.execute(context) # 执行效果
                
                # 获取动画
                if success:
                    anim = effect.get_animation(context)
                    if anim:
                        animations.append(anim)
        
        return animations


class BattleContext:
    """战斗上下文：封装战斗状态，避免技能直接访问场景"""
    def __init__(self, battle_scene):
        self.scene = battle_scene
        
        # 当前战斗信息
        self.attacker_slot = None      # 政击者槽位
        self.defender_slot = None      # 防御者槽位
        self.attacker_owner = None     # 政击者所属（player/enemy）
        self.defender_owner = None     # 防御者所属
        self.damage = 0                # 即将造成的伤害
        self.original_damage = 0       # 原始伤害（用于计算修正）
        self.skill_target = None       # 技能目标（缓存随机选择的目标）
        self.skill_targets = None      # 技能目标列表（群体技能用）
        
    def set_attacker(self, slot, owner):
        """设置攻击者"""
        self.attacker_slot = slot
        self.attacker_owner = owner
    
    def set_defender(self, slot, owner):
        """设置防御者"""
        self.defender_slot = slot
        self.defender_owner = owner
    
    def set_damage(self, damage):
        """设置伤害值"""
        self.damage = damage
        self.original_damage = damage
    
    def get_random_enemy_slot(self):
        """获取随机敌方战斗槽位"""
        import random
        if self.attacker_owner == "player":
            slots = [s for s in self.scene.enemy_battle_slots if s.has_card()]
        else:
            slots = [s for s in self.scene.player_battle_slots if s.has_card()]
        
        return random.choice(slots) if slots else None
    
    def get_all_enemy_slots(self):
        """获取所有敌方战斗槽位"""
        if self.attacker_owner == "player":
            return [s for s in self.scene.enemy_battle_slots if s.has_card()]
        else:
            return [s for s in self.scene.player_battle_slots if s.has_card()]
    
    def deal_damage_to_slot(self, target_slot, damage):
        """对槽位造成伤害"""
        if target_slot and target_slot.has_card():
            card = target_slot.card_data
            old_hp = card.hp
            card.hp = max(0, card.hp - damage)
            target_slot.card_data = card
            target_slot.start_hp_flash(old_hp, card.hp)
            return True
        return False
    
    def deal_damage_to_player(self, damage):
        """对玩家本体造成伤害"""
        owner = self.defender_owner
        if owner == "player":
            self.scene.player_current_hp -= damage
            self.scene.player_health_bar.set_hp(self.scene.player_current_hp)
        else:
            self.scene.enemy_current_hp -= damage
            self.scene.enemy_health_bar.set_hp(self.scene.enemy_current_hp)
        return True
    
    def heal_slot(self, target_slot, amount):
        """治疗槽位"""
        if target_slot and target_slot.has_card():
            card = target_slot.card_data
            old_hp = card.hp
            card.hp = min(card.max_hp, card.hp + amount)
            target_slot.card_data = card
            target_slot.start_hp_flash(old_hp, card.hp)
            return True
        return False
