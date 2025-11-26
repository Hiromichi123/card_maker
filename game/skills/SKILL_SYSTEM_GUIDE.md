## 技能系统使用指南和示例

### 架构说明

- `SkillEffect`: 技能效果基类（策略模式）
- `Skill`: 技能类（包含多个效果的组合）
- `BattleContext`: 战斗上下文（封装战斗状态，避免技能直接访问场景）
- `SkillRegistry`: 技能注册表（管理所有技能，支持通过trait查询）

## 如何集成到现有战斗系统

### 1. 修改 CardData（已有）

在卡牌JSON中添加traits字段：

```json
{
    "id": "001",
    "name": "火焰法师",
    "atk": 2,
    "hp": 3,
    "cd": 2,
    "traits": ["火球1"],  // 技能标签
    "description": "攻击前对随机敌人造成1点伤害"
}
```

### 2. 修改 execute_attack 方法

在 `battle_base_scene.py` 中修改攻击逻辑：

```python
def execute_attack(self, attacker_slot, defender_slot, defender_hp_ref):
    \"\"\"执行单次攻击（集成技能系统）\"\"\"
    from game.skills import BattleContext, get_skill_registry, SkillTrigger
    
    attacker_card = attacker_slot.card_data
    
    # 1. 创建战斗上下文
    context = BattleContext(self)
    context.set_attacker(attacker_slot, "player" if defender_hp_ref == "enemy" else "enemy")
    context.set_defender(defender_slot, defender_hp_ref)
    context.set_damage(attacker_card.atk)
    
    # 2. 获取攻击者的所有技能
    registry = get_skill_registry()
    skills = registry.get_skills_from_traits(attacker_card.traits)
    
    # 3. 执行 BEFORE_ATTACK 技能（如火球、飞行）
    for skill in skills:
        animations = skill.execute_trigger(SkillTrigger.BEFORE_ATTACK, context)
        self.battle_animations.extend(animations)
    
    # 4. 创建普通攻击动画
    attack_anim = AttackAnimation(attacker_slot, context.defender_slot)
    self.battle_animations.append(attack_anim)
    
    # 5. 执行普通攻击伤害（使用context中可能被修改的damage）
    if context.defender_slot and context.defender_slot.has_card():
        defender_card = context.defender_slot.card_data
        old_hp = defender_card.hp
        new_hp = old_hp - context.damage
        defender_card.hp = new_hp
        context.defender_slot.card_data = defender_card
        context.defender_slot.start_hp_flash(old_hp, new_hp)
    else:
        # 攻击玩家（飞行等技能可能清空了defender_slot）
        context.deal_damage_to_player(context.damage)
    
    # 6. 执行 AFTER_ATTACK 技能（如吸血、抽卡）
    for skill in skills:
        animations = skill.execute_trigger(SkillTrigger.AFTER_ATTACK, context)
        self.battle_animations.extend(animations)
```

### 3. 处理其他触发时机

```python
def play_card_to_waiting(self, card_data):
    \"\"\"出牌到等候区（添加ON_DEPLOY触发）\"\"\"
    # ... 原有代码 ...
    
    # 触发部署技能
    from game.skills import BattleContext, get_skill_registry, SkillTrigger
    context = BattleContext(self)
    context.set_attacker(target_slot, "player")
    
    registry = get_skill_registry()
    skills = registry.get_skills_from_traits(card_data.traits)
    
    for skill in skills:
        skill.execute_trigger(SkillTrigger.ON_DEPLOY, context)
```

## 创建新技能示例

### 示例1：简单技能（闪电链）

```python
class LightningChainEffect(SkillEffect):
    \"\"\"闪电链：对3个随机敌人各造成1点伤害\"\"\"
    def __init__(self):
        super().__init__(
            name="闪电链",
            description="对3个随机敌人各造成1点伤害",
            trigger=SkillTrigger.BEFORE_ATTACK
        )
    
    def execute(self, context):
        targets = context.get_all_enemy_slots()
        if len(targets) > 3:
            targets = random.sample(targets, 3)
        
        for target in targets:
            context.deal_damage_to_slot(target, 1)
        
        return len(targets) > 0
    
    def get_animation(self, context):
        from game.skills.skill_animations import LightningAnimation
        return LightningAnimation(context.attacker_slot, context.get_all_enemy_slots()[:3])
```

### 示例2：复杂技能（凤凰涅槃）

```python
def create_phoenix_skill():
    \"\"\"
    凤凰涅槃：
    1. 死亡时：对所有敌人造成2点伤害
    2. 死亡时：在原位置召唤一只1/1的凤凰雏鸟
    \"\"\"
    from game.skills.skill_base import Skill
    
    skill = Skill("phoenix_rebirth", "凤凰涅槃")
    skill.add_effect(AOEDamageEffect(2))  # 死亡时触发
    skill.add_effect(SummonEffect("phoenix_baby", slot_type="battle"))
    
    return skill
```

### 示例3：条件技能（处刑人）

```python
def create_executioner_skill():
    \"\"\"
    处刑人：如果目标HP≤3，造成10点伤害；否则造成2点伤害
    \"\"\"
    from game.skills.skill_base import Skill
    
    skill = Skill("executioner", "处刑人")
    
    # 条件函数
    def target_low_hp(context):
        if context.defender_slot and context.defender_slot.has_card():
            return context.defender_slot.card_data.hp <= 3
        return False
    
    high_damage = DirectDamageEffect(10, TargetType.OPPOSITE) # 高伤害效果
    
    low_damage = DirectDamageEffect(2, TargetType.OPPOSITE) # 低伤害效果
    skill.add_effect(ConditionalEffect(target_low_hp, high_damage, low_damage))
    return skill
```

## 技能动画系统（可选）

创建 `game/skills/skill_animations.py`：

```python
class FireballAnimation:
    \"\"\"火球动画：从施法者到目标的抛物线\"\"\"
    def __init__(self, source_slot, target_slot, damage):
        self.source_slot = source_slot
        self.target_slot = target_slot
        self.damage = damage
        self.progress = 0.0
        self.duration = 0.5
    
    def update(self, dt):
        self.progress += dt / self.duration
        return self.progress >= 1.0
    
    def draw(self, screen):
        if self.progress >= 1.0:
            return
        
        # 计算火球位置（抛物线）
        start = self.source_slot.rect.center
        end = self.target_slot.rect.center
        
        t = self.progress
        x = start[0] + (end[0] - start[0]) * t
        y = start[1] + (end[1] - start[1]) * t - 100 * math.sin(math.pi * t)
        
        # 绘制火球
        pygame.draw.circle(screen, (255, 100, 0), (int(x), int(y)), 15)
```

### 新增技能流程

1. 创建效果类（继承SkillEffect）
2. 在skill_registry.py中注册
3. 在卡牌JSON中添加trait标签

## 注意事项

1. **性能优化**：技能注册表使用单例模式，避免重复创建
2. **动画管理**：技能动画和战斗动画统一管理在battle_animations列表
3. **错误处理**：如果卡牌traits中的标签未注册，会被忽略（不会报错）
4. **扩展性**：可以轻松添加新的SkillTrigger（如TURN_START、ON_DEATH等）

## 下一步

1. 创建skill_animations.py实现技能动画
2. 在card_database.py确保CardData包含traits字段
3. 修改battle_base_scene.py集成技能系统
4. 添加更多技能效果类
"""
