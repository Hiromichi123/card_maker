"""
技能系统初始化
"""
from game.skills.skill_base import SkillEffect, Skill, BattleContext, SkillTrigger, TargetType
from game.skills.skill_effects import *
from game.skills.skill_registry import get_skill_registry
from game.skills.skill_animations import (
    SkillAnimation,
    FireballAnimation,
    IceBloomAnimation,
    LightningStrikeAnimation,
    MultiFireballAnimation,
    MultiIceBloomAnimation,
    MultiLightningAnimation,
    HealAnimation,
)

__all__ = [
    'SkillEffect',
    'Skill',
    'BattleContext',
    'SkillTrigger',
    'TargetType',
    'get_skill_registry',
    'SkillAnimation',
    'FireballAnimation',
    'IceBloomAnimation',
    'LightningStrikeAnimation',
    'MultiFireballAnimation',
    'MultiIceBloomAnimation',
    'MultiLightningAnimation',
    'FlyOverAnimation',
    'ExplosionAnimation',
    'LightningAnimation',
    'HealAnimation',
]
