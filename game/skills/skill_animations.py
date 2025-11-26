"""技能动画效果"""
import pygame
import math
import random
from config import UI_SCALE


class SkillAnimation:
    """技能动画基类"""
    def __init__(self):
        self.finished = False
        self.start_time = None
        self.on_complete = None  # 完成回调
        self.on_hit = None  # 命中回调
    
    def start(self):
        """开始动画"""
        self.start_time = pygame.time.get_ticks()
    
    def update(self, dt):
        """更新动画（返回True表示动画结束）"""
        return self.finished
    
    def draw(self, screen):
        """绘制动画"""
        pass

# ============= 具体动画实现 =============

"""=====单/群 火球、冰封、闪电====="""
class FireballAnimation(SkillAnimation):
    """火球动画：从释放者飞向目标"""
    def __init__(self, attacker_slot, target_slot, damage):
        super().__init__()
        self.size = (int(200 * UI_SCALE), int(200 * UI_SCALE))
        self.attacker_slot = attacker_slot
        self.target_slot = target_slot
        self.damage = damage
        
        # 动画参数
        self.start_delay = 100   # 起始停留时间（毫秒）
        self.fly_duration = 1000  # 飞行时间（毫秒）
        self.end_delay = 100     # 结束停留时间（毫秒）
        self.total_duration = self.start_delay + self.fly_duration + self.end_delay
        self.hit_triggered = False  # 是否已触发命中回调
        
        # 加载火球图标
        self.fireball_image = None
        self.load_image()
        
        # 计算起点和终点
        self.start_pos = None
        self.end_pos = None
        self.current_pos = None
        
    def load_image(self):
        """加载火球图标"""
        original = pygame.image.load("assets/skill/fire_ball.png").convert_alpha()
        self.fireball_image = pygame.transform.scale(original, self.size) # 缩放
        
    def start(self):
        """开始动画"""
        super().start()
        
        # 获取起点（释放者中心）
        if self.attacker_slot and hasattr(self.attacker_slot, 'rect'):
            self.start_pos = self.attacker_slot.rect.center
        
        # 获取终点（目标中心）
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            self.end_pos = self.target_slot.rect.center
        
        self.current_pos = list(self.start_pos)
    
    def update(self, dt):
        """更新动画"""
        if self.start_time is None:
            return False
        
        # 计算总进度
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed < self.start_delay:
            # 阶段1：起始停留
            self.current_pos = self.start_pos
        
        elif elapsed < self.start_delay + self.fly_duration:
            # 阶段2：飞行
            fly_elapsed = elapsed - self.start_delay
            t = fly_elapsed / self.fly_duration
            # X轴线性插值
            x = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
            # Y轴抛物线（先上升后下降）
            y_start = self.start_pos[1]
            y_end = self.end_pos[1]
            arc_height = 100 * UI_SCALE # 抛物线高度
            y = y_start + (y_end - y_start) * t - arc_height * math.sin(t * math.pi)
            self.current_pos = (x, y)
        
        else:
            # 阶段3：结束停留
            self.current_pos = self.end_pos
            # 触发命中回调（只触发一次）
            if not self.hit_triggered:
                if self.on_hit:
                    self.on_hit()
                self.hit_triggered = True  # 无论on_hit是否存在，都标记为已触发
        
        # 检查是否完全结束
        if elapsed >= self.total_duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def draw(self, screen):
        """绘制火球"""
        if self.current_pos and self.fireball_image:
            rect = self.fireball_image.get_rect(center=self.current_pos)
            screen.blit(self.fireball_image, rect)

class IceBloomAnimation(SkillAnimation):
    """冰封动画：冰花在目标位置从小变大"""
    def __init__(self, target_slot, damage):
        super().__init__()
        self.target_slot = target_slot
        self.damage = damage
        
        # 动画参数
        self.start_delay = 100      # 初始停留时间（毫秒）
        self.grow_duration = 400    # 生长时间（毫秒）
        self.end_delay = 200        # 结束停留时间（毫秒）
        self.total_duration = self.start_delay + self.grow_duration + self.end_delay
        self.hit_triggered = False  # 是否已触发命中回调
        
        # 尺寸参数
        self.min_size = int(50 * UI_SCALE)  # 最小尺寸
        self.max_size = int(250 * UI_SCALE) # 最大尺寸
        self.current_size = self.min_size
        
        # 加载冰花图标
        self.ice_image_original = None
        self.ice_image_scaled = None
        self.load_image()
        
        # 目标位置
        self.target_pos = None
    
    def load_image(self):
        """加载冰花图标"""
        self.ice_image_original = pygame.image.load("assets/skill/ice.png").convert_alpha()
    
    def start(self):
        """开始动画"""
        super().start()
        
        # 获取目标中心位置
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            self.target_pos = self.target_slot.rect.center
        else:
            self.target_pos = (400, 300)
    
    def update(self, dt):
        """更新动画"""
        if self.start_time is None:
            return False
        
        # 计算总进度
        elapsed = pygame.time.get_ticks() - self.start_time
        
        if elapsed < self.start_delay:
            # 阶段1：初始停留（最小尺寸）
            self.current_size = self.min_size
        
        elif elapsed < self.start_delay + self.grow_duration:
            # 阶段2：生长
            grow_elapsed = elapsed - self.start_delay
            t = grow_elapsed / self.grow_duration
            
            # 尺寸线性插值
            self.current_size = self.min_size + (self.max_size - self.min_size) * t
            
            # 在生长到一半时触发命中回调（造成伤害）
            if t >= 0.5 and not self.hit_triggered:
                if self.on_hit:
                    self.on_hit()
                self.hit_triggered = True  # 无论on_hit是否存在，都标记为已触发
        
        else:
            # 阶段3：结束停留（最大尺寸）
            self.current_size = self.max_size
        
        # 缩放图片到当前尺寸
        size = int(self.current_size)
        self.ice_image_scaled = pygame.transform.scale(self.ice_image_original, (size, size))
        
        # 检查是否完全结束
        if elapsed >= self.total_duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def draw(self, screen):
        """绘制冰花"""
        if self.target_pos and self.ice_image_scaled:
            rect = self.ice_image_scaled.get_rect(center=self.target_pos)
            screen.blit(self.ice_image_scaled, rect)

class LightningStrikeAnimation(SkillAnimation):
    """闪电动画：在释放者和目标之间交替闪烁"""
    def __init__(self, attacker_slot, target_slot, damage):
        super().__init__()
        self.attacker_slot = attacker_slot
        self.target_slot = target_slot
        self.damage = damage
        
        # 动画参数
        self.total_duration = 700   # 总持续时间（毫秒）
        self.blink_interval = 100   # 闪烁间隔（毫秒）
        self.hit_triggered = False  # 是否已触发命中回调
        
        # 图标尺寸
        self.size = int(300 * UI_SCALE)
        
        # 加载闪电图标
        self.lightning_image = None
        self.load_image()
        
        # 位置
        self.attacker_pos = None
        self.target_pos = None
        self.current_pos = None
        self.show_at_target = False  # 当前是否显示在目标位置
    
    def load_image(self):
        """加载闪电图标"""
        try:
            original = pygame.image.load("assets/skill/lighten.png").convert_alpha()
            self.lightning_image = pygame.transform.scale(original, (self.size, self.size))
        except:
            # 如果图片不存在，创建一个简单的黄色闪电形状
            self.lightning_image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            # 绘制简单的闪电图案
            pygame.draw.polygon(self.lightning_image, (255, 255, 100), [
                (125, 50), (150, 125), (135, 125), (160, 200), (100, 140), (115, 140), (90, 50)
            ])
            # 添加白色高光
            pygame.draw.polygon(self.lightning_image, (255, 255, 255, 180), [
                (125, 50), (145, 115), (135, 115), (150, 180), (110, 130), (120, 130), (100, 50)
            ])
    
    def start(self):
        """开始动画"""
        super().start()
        
        # 获取释放者位置
        if self.attacker_slot and hasattr(self.attacker_slot, 'rect'):
            self.attacker_pos = self.attacker_slot.rect.center
        else:
            self.attacker_pos = (400, 300)
        
        # 获取目标位置
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            self.target_pos = self.target_slot.rect.center
        else:
            self.target_pos = (400, 300)
        
        # 初始显示在释放者位置
        self.current_pos = self.attacker_pos
        self.show_at_target = False
    
    def update(self, dt):
        """更新动画"""
        if self.start_time is None:
            return False
        
        # 计算总进度
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # 计算当前应该显示在哪个位置（交替闪烁）
        blink_count = int(elapsed / self.blink_interval)
        self.show_at_target = (blink_count % 2 == 1)  # 奇数次显示在目标，偶数次显示在释放者
        
        # 更新当前位置
        self.current_pos = self.target_pos if self.show_at_target else self.attacker_pos
        
        # 在中间时刻触发伤害（300ms）
        if elapsed >= self.total_duration / 2 and not self.hit_triggered:
            if self.on_hit:
                self.on_hit()
            self.hit_triggered = True  # 无论on_hit是否存在，都标记为已触发
        
        # 检查是否完全结束
        if elapsed >= self.total_duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def draw(self, screen):
        """绘制闪电"""
        if self.current_pos and self.lightning_image:
            rect = self.lightning_image.get_rect(center=self.current_pos)
            screen.blit(self.lightning_image, rect)

class MultiFireballAnimation(SkillAnimation):
    """群体火球动画：同时向多个目标发射火球"""
    def __init__(self, attacker_slot, target_slots, damage):
        super().__init__()
        self.attacker_slot = attacker_slot
        self.target_slots = target_slots
        self.damage = damage
        self.hit_triggered = False  # 确保伤害只触发一次
        
        # 为每个目标创建独立的火球动画
        self.fireballs = []
        for target in target_slots:
            fb = FireballAnimation(attacker_slot, target, damage)
            self.fireballs.append(fb)
    
    def start(self):
        """开始所有火球动画"""
        super().start()
        for fb in self.fireballs:
            fb.start()
            # 清除子动画的回调，由父级动画统一管理
            fb.on_hit = None
            fb.on_complete = None
    
    def update(self, dt):
        """更新所有火球"""
        if not self.fireballs:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        # 更新所有火球
        all_finished = True
        any_hit = False  # 检查是否有火球到达目标
        
        for fb in self.fireballs:
            if not fb.finished:
                fb.update(dt)
                all_finished = False
                # 检查火球是否已触发命中（到达目标）
                if fb.hit_triggered:
                    any_hit = True
        
        # 只要有一个火球到达目标，就触发伤害（只触发一次）
        if any_hit and not self.hit_triggered and self.on_hit:
            self.on_hit()
            self.hit_triggered = True
        
        if all_finished:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def draw(self, screen):
        """绘制所有火球"""
        for fb in self.fireballs:
            if not fb.finished:
                fb.draw(screen)

class MultiIceBloomAnimation(SkillAnimation):
    """群体冰封动画：在多个目标位置同时生成冰花"""
    def __init__(self, target_slots, damage):
        super().__init__()
        self.target_slots = target_slots
        self.damage = damage
        self.hit_triggered = False  # 确保伤害只触发一次
        
        # 为每个目标创建独立的冰花动画
        self.ice_blooms = []
        for target in target_slots:
            ice = IceBloomAnimation(target, damage)
            self.ice_blooms.append(ice)
    
    def start(self):
        """开始所有冰花动画"""
        super().start()
        for ice in self.ice_blooms:
            ice.start()
            # 清除子动画的回调，由父级动画统一管理
            ice.on_hit = None
            ice.on_complete = None
    
    def update(self, dt):
        """更新所有冰花"""
        if not self.ice_blooms:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        # 更新所有冰花
        all_finished = True
        any_hit = False
        
        for ice in self.ice_blooms:
            if not ice.finished:
                ice.update(dt)
                all_finished = False
                if ice.hit_triggered:
                    any_hit = True
        
        # 只要有一个冰花到达命中时刻，就触发伤害（只触发一次）
        if any_hit and not self.hit_triggered and self.on_hit:
            self.on_hit()
            self.hit_triggered = True
        
        if all_finished:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def draw(self, screen):
        """绘制所有冰花"""
        for ice in self.ice_blooms:
            if not ice.finished:
                ice.draw(screen)

class MultiLightningAnimation(SkillAnimation):
    """群体闪电动画：同时对多个目标释放闪电"""
    def __init__(self, attacker_slot, target_slots, damage):
        super().__init__()
        self.attacker_slot = attacker_slot
        self.target_slots = target_slots
        self.damage = damage
        self.hit_triggered = False  # 确保伤害只触发一次
        
        # 为每个目标创建独立的闪电动画
        self.lightnings = []
        for target in target_slots:
            lightning = LightningStrikeAnimation(attacker_slot, target, damage)
            self.lightnings.append(lightning)
    
    def start(self):
        """开始所有闪电动画"""
        super().start()
        for lightning in self.lightnings:
            lightning.start()
            # 清除子动画的回调，由父级动画统一管理
            lightning.on_hit = None
            lightning.on_complete = None
    
    def update(self, dt):
        """更新所有闪电"""
        if not self.lightnings:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        # 更新所有闪电
        all_finished = True
        any_hit = False
        
        for lightning in self.lightnings:
            if not lightning.finished:
                lightning.update(dt)
                all_finished = False
                if lightning.hit_triggered:
                    any_hit = True
        
        # 只要有一个闪电到达命中时刻，就触发伤害（只触发一次）
        if any_hit and not self.hit_triggered and self.on_hit:
            self.on_hit()
            self.hit_triggered = True
        
        if all_finished:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def draw(self, screen):
        """绘制所有闪电"""
        for lightning in self.lightnings:
            if not lightning.finished:
                lightning.draw(screen)

"""=====防御、治愈、恢复====="""
class ShieldAnimation(SkillAnimation):
    """盾牌动画：在受伤时显示盾牌图标"""
    def __init__(self, target_slot):
        super().__init__()
        self.target_slot = target_slot
        self.duration = 500  # 持续500ms
        
        # 加载盾牌图标
        self.shield_image = None
        self.load_image()
        
        # 位置
        self.target_pos = None
    
    def load_image(self):
        """加载盾牌图标"""
        try:
            original = pygame.image.load("assets/skill/shield.png").convert_alpha()
            size = int(250 * UI_SCALE)
            self.shield_image = pygame.transform.scale(original, (size, size))
        except:
            # 如果图片不存在，创建简单的盾牌图形
            size = int(250 * UI_SCALE)
            self.shield_image = pygame.Surface((size, size), pygame.SRCALPHA)
            # 绘制盾牌轮廓
            center = (size // 2, size // 2)
            pygame.draw.circle(self.shield_image, (100, 100, 255), center, size // 2 - 5, 10)
            pygame.draw.circle(self.shield_image, (150, 150, 255, 180), center, size // 2 - 15)
    
    def start(self):
        """开始动画"""
        super().start()
        
        # 获取目标位置
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            self.target_pos = self.target_slot.rect.center
        else:
            self.target_pos = (400, 300)
    
    def update(self, dt):
        """更新动画"""
        if self.start_time is None:
            return False
        
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # 检查是否结束
        if elapsed >= self.duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def draw(self, screen):
        """绘制盾牌"""
        if self.target_pos and self.shield_image:
            # 计算透明度（淡入淡出效果）
            elapsed = pygame.time.get_ticks() - self.start_time
            progress = elapsed / self.duration
            
            if progress < 0.2:
                # 淡入
                alpha = int(255 * (progress / 0.2))
            elif progress > 0.8:
                # 淡出
                alpha = int(255 * ((1 - progress) / 0.2))
            else:
                alpha = 255
            
            # 创建带透明度的图像
            img = self.shield_image.copy()
            img.set_alpha(alpha)
            
            rect = img.get_rect(center=self.target_pos)
            screen.blit(img, rect)

class HealAnimation(SkillAnimation):
    """治愈动画：光球飞向目标后爆开成螺旋上升的光粒子"""
    def __init__(self, caster_slot, target_slot, heal_amount):
        super().__init__()
        self.caster_slot = caster_slot
        self.target_slot = target_slot
        self.heal_amount = heal_amount
        
        # 动画阶段时长
        self.fly_duration = 800     # 光球飞行时间（加倍）
        self.particle_duration = 1200  # 粒子持续时间（加倍）
        self.total_duration = self.fly_duration + self.particle_duration
        self.hit_triggered = False
        
        # 位置
        self.caster_pos = None
        self.target_pos = None
        self.orb_pos = None  # 光球当前位置
        
        # 粒子系统（在光球到达后才创建）
        self.particles = []
        self.particles_created = False
    
    def start(self):
        """开始动画"""
        super().start()
        
        # 获取施法者位置
        if self.caster_slot and hasattr(self.caster_slot, 'rect'):
            self.caster_pos = self.caster_slot.rect.center
        else:
            self.caster_pos = (400, 300)
        
        # 获取目标位置（卡牌3/4处）
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            target_y = self.target_slot.rect.top + self.target_slot.rect.height * 0.75
            self.target_pos = (self.target_slot.rect.centerx, target_y)
        else:
            self.target_pos = (400, 300)
        
        self.orb_pos = list(self.caster_pos)
    
    def update(self, dt):
        """更新动画"""
        if self.start_time is None:
            return False
        
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # 阶段1：光球飞行
        if elapsed < self.fly_duration:
            t = elapsed / self.fly_duration
            # 缓动函数（ease-out）
            t = 1 - (1 - t) ** 2
            
            # 计算光球位置（抛物线）
            x = self.caster_pos[0] + (self.target_pos[0] - self.caster_pos[0]) * t
            y_linear = self.caster_pos[1] + (self.target_pos[1] - self.caster_pos[1]) * t
            arc_height = 50 * UI_SCALE
            y = y_linear - arc_height * math.sin(t * math.pi)
            self.orb_pos = (x, y)
        
        # 阶段2：光球到达，创建粒子
        elif not self.particles_created:
            self.particles_created = True
            self.orb_pos = self.target_pos
            
            # 触发治疗效果
            if not self.hit_triggered:
                if self.on_hit:
                    self.on_hit()
                self.hit_triggered = True
            
            # 创建螺旋上升的粒子
            num_particles = 30
            for i in range(num_particles):
                angle_offset = (i / num_particles) * math.pi * 2
                self.particles.append({
                    'angle_offset': angle_offset,
                    'radius_offset': random.uniform(0, 40 * UI_SCALE),  # 乘以UI_SCALE
                    'speed': random.uniform(160 * UI_SCALE, 240 * UI_SCALE),  # 乘以UI_SCALE
                    'spiral_speed': random.uniform(2, 4),
                    'life_offset': random.uniform(0, 0.3)
                })
        
        # 检查是否结束
        if elapsed >= self.total_duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def draw(self, screen):
        """绘制治愈效果"""
        if not self.caster_pos or not self.target_pos:
            return
        
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # 阶段1：绘制飞行的光球
        if elapsed < self.fly_duration:
            progress = elapsed / self.fly_duration
            
            # 绘制拖尾效果
            for i in range(5):
                trail_t = progress - i * 0.05
                if trail_t > 0:
                    trail_x = self.caster_pos[0] + (self.target_pos[0] - self.caster_pos[0]) * trail_t
                    y_linear = self.caster_pos[1] + (self.target_pos[1] - self.caster_pos[1]) * trail_t
                    arc_height = 50 * UI_SCALE
                    trail_y = y_linear - arc_height * math.sin(trail_t * math.pi)
                    
                    alpha = int(150 * (1 - i * 0.2))
                    size = int(15 * (1 - i * 0.15))
                    
                    surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (150, 255, 150, alpha), (size, size), size)
                    screen.blit(surf, (int(trail_x - size), int(trail_y - size)))
            
            # 绘制主光球（金绿色渐变）
            if self.orb_pos:
                size = int(20 * UI_SCALE)
                # 外层光晕
                glow_surf = pygame.Surface((size * 4, size * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (200, 255, 150, 80), (size * 2, size * 2), size * 2)
                screen.blit(glow_surf, (int(self.orb_pos[0] - size * 2), int(self.orb_pos[1] - size * 2)))
                
                # 内层核心
                core_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(core_surf, (255, 255, 200, 220), (size, size), size)
                pygame.draw.circle(core_surf, (150, 255, 150, 255), (size, size), int(size * 0.6))
                screen.blit(core_surf, (int(self.orb_pos[0] - size), int(self.orb_pos[1] - size)))
        
        # 阶段2：绘制螺旋上升的粒子
        else:
            particle_elapsed = elapsed - self.fly_duration
            particle_progress = particle_elapsed / self.particle_duration
            
            for particle in self.particles:
                # 计算粒子生命周期（考虑偏移）
                p_life = min(1.0, (particle_progress - particle['life_offset']) / (1 - particle['life_offset']))
                if p_life < 0:
                    continue
                
                # 螺旋上升
                angle = particle['angle_offset'] + p_life * math.pi * particle['spiral_speed']
                radius = particle['radius_offset'] + p_life * 80 * UI_SCALE  # 乘以UI_SCALE
                
                x = self.target_pos[0] + math.cos(angle) * radius
                y = self.target_pos[1] - p_life * particle['speed'] + math.sin(angle) * 20 * UI_SCALE  # 乘以UI_SCALE
                
                # 透明度（脉动效果）
                pulse = math.sin(p_life * math.pi * 6) * 0.2 + 0.8
                alpha = int(255 * (1 - p_life) * pulse)
                
                # 粒子大小
                size = int(12 * (1 - p_life * 0.5))  # 扩大2倍
                
                # 颜色渐变（绿色到金色）
                color_t = p_life
                r = int(150 + 105 * color_t)
                g = 255
                b = int(150 - 150 * color_t)
                
                # 绘制粒子（带光晕）
                particle_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
                # 外层光晕
                pygame.draw.circle(particle_surf, (r, g, b, alpha // 3), (size * 1.5, size * 1.5), size * 1.5)
                # 核心
                pygame.draw.circle(particle_surf, (r, g, b, alpha), (size * 1.5, size * 1.5), size)
                screen.blit(particle_surf, (int(x - size * 1.5), int(y - size * 1.5)))

class SelfHealAnimation(SkillAnimation):
    """恢复动画：直接在自身爆发螺旋上升的光粒子"""
    def __init__(self, target_slot, heal_amount):
        super().__init__()
        self.target_slot = target_slot
        self.heal_amount = heal_amount
        self.duration = 1400  # 持续1400ms（加倍）
        self.hit_triggered = False
        
        # 位置
        self.target_pos = None
        
        # 粒子系统
        self.particles = []
        self.particles_created = False
    
    def start(self):
        """开始动画"""
        super().start()
        
        # 获取目标位置（卡牌底部）
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            self.target_pos = (self.target_slot.rect.centerx, self.target_slot.rect.bottom)
        else:
            self.target_pos = (400, 300)
    
    def update(self, dt):
        """更新动画"""
        if self.start_time is None:
            return False
        
        elapsed = pygame.time.get_ticks() - self.start_time
        
        # 初始爆发，创建粒子
        if not self.particles_created:
            self.particles_created = True
            
            # 触发恢复效果
            if not self.hit_triggered:
                if self.on_hit:
                    self.on_hit()
                self.hit_triggered = True
            
            # 创建螺旋上升的粒子（比治愈动画稍少）
            num_particles = 25
            for i in range(num_particles):
                angle_offset = (i / num_particles) * math.pi * 2
                self.particles.append({
                    'angle_offset': angle_offset,
                    'radius_offset': random.uniform(0, 30 * UI_SCALE),  # 乘以UI_SCALE
                    'speed': random.uniform(140 * UI_SCALE, 220 * UI_SCALE),  # 乘以UI_SCALE
                    'spiral_speed': random.uniform(2.5, 4.5),
                    'life_offset': random.uniform(0, 0.2)
                })
        
        # 检查是否结束
        if elapsed >= self.duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        
        return False
    
    def draw(self, screen):
        """绘制恢复效果"""
        if not self.target_pos:
            return
        
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = elapsed / self.duration
        
        # 绘制初始爆发光环
        if progress < 0.2:
            ring_progress = progress / 0.2
            ring_radius = int(30 * ring_progress)
            ring_alpha = int(200 * (1 - ring_progress))
            
            ring_surf = pygame.Surface((ring_radius * 2 + 20, ring_radius * 2 + 20), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (150, 255, 150, ring_alpha), 
                             (ring_radius + 10, ring_radius + 10), ring_radius, 3)
            screen.blit(ring_surf, (int(self.target_pos[0] - ring_radius - 10), 
                                   int(self.target_pos[1] - ring_radius - 10)))
        
        # 绘制螺旋上升的粒子
        for particle in self.particles:
            # 计算粒子生命周期
            p_life = min(1.0, (progress - particle['life_offset']) / (1 - particle['life_offset']))
            if p_life < 0:
                continue
            
            # 螺旋上升
            angle = particle['angle_offset'] + p_life * math.pi * particle['spiral_speed']
            radius = particle['radius_offset'] + p_life * 70 * UI_SCALE  # 乘以UI_SCALE
            
            x = self.target_pos[0] + math.cos(angle) * radius
            y = self.target_pos[1] - p_life * particle['speed'] + math.sin(angle) * 16 * UI_SCALE  # 乘以UI_SCALE
            
            # 透明度（脉动效果）
            pulse = math.sin(p_life * math.pi * 5) * 0.25 + 0.75
            alpha = int(255 * (1 - p_life) * pulse)
            
            # 粒子大小
            size = int(10 * (1 - p_life * 0.4))  # 扩大2倍
            
            # 颜色（绿色到青绿色渐变）
            color_t = p_life
            r = int(100 + 55 * color_t)
            g = 255
            b = int(100 + 55 * color_t)
            
            # 绘制粒子（带光晕）
            particle_surf = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
            # 外层光晕
            pygame.draw.circle(particle_surf, (r, g, b, alpha // 3), (size * 1.5, size * 1.5), size * 1.5)
            # 核心
            pygame.draw.circle(particle_surf, (r, g, b, alpha), (size * 1.5, size * 1.5), size)
            screen.blit(particle_surf, (int(x - size * 1.5), int(y - size * 1.5)))
