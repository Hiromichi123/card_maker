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

"""=====防御、治愈、恢复、反击、闪避、吸血====="""
class ShieldAnimation(SkillAnimation):
    """盾牌动画：在受伤时显示盾牌图标"""
    def __init__(self, target_slot, overlay=None):
        super().__init__()
        self.target_slot = target_slot
        self.duration = 500  # 持续500ms
        self.overlay_type = overlay
        self.overlay_image = None
        
        # 加载盾牌图标
        self.shield_image = None
        self.load_image()
        if self.overlay_type == "tear":
            self.load_overlay()
        
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

    def load_overlay(self):
        size = int(250 * UI_SCALE)
        try:
            original = pygame.image.load("assets/skill/tear.png").convert_alpha()
            self.overlay_image = pygame.transform.smoothscale(original, (size, size))
        except Exception:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            top = (size * 0.5, 0)
            left = (size * 0.2, size * 0.85)
            bottom = (size * 0.5, size)
            right = (size * 0.8, size * 0.85)
            pygame.draw.polygon(surf, (255, 210, 210, 230), [top, right, bottom, left])
            pygame.draw.polygon(surf, (255, 120, 120, 200), [top, right, bottom, left], 6)
            self.overlay_image = surf
    
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
            if self.overlay_image:
                overlay = pygame.transform.smoothscale(
                    self.overlay_image,
                    (img.get_width(), img.get_height())
                )
                overlay.set_alpha(alpha)
                screen.blit(overlay, rect)

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

class BleedAnimation(SkillAnimation):
    """受伤动画：在卡牌身上喷出血滴"""
    def __init__(self, target_slot, damage):
        super().__init__()
        self.target_slot = target_slot
        self.damage = damage
        self.duration = 1200
        self.particles = []
        self.target_pos = None
        self.scale = 2.0
        self.particle_count = int(18 * self.scale)
        self.speed_range = (
            120 * UI_SCALE * self.scale,
            220 * UI_SCALE * self.scale
        )
        self.gravity = 80 * UI_SCALE * self.scale
    
    def start(self):
        super().start()
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            rect = self.target_slot.rect
            self.target_pos = (rect.centerx, rect.centery)
        else:
            self.target_pos = (400, 300)
        for _ in range(self.particle_count):
            angle = random.uniform(-math.pi * 0.8, -math.pi * 0.2)
            speed = random.uniform(*self.speed_range)
            self.particles.append({
                'x': self.target_pos[0],
                'y': self.target_pos[1],
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed,
                'life': random.uniform(0.4, 0.8)
            })
    
    def update(self, dt):
        if self.start_time is None:
            return False
        elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
        for particle in self.particles:
            particle['life'] -= dt
            if particle['life'] > 0:
                particle['x'] += particle['vx'] * dt
                particle['y'] += particle['vy'] * dt + self.gravity * dt
        if elapsed >= self.duration / 1000:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        return False
    
    def draw(self, screen):
        if not self.target_pos:
            return
        for particle in self.particles:
            if particle['life'] <= 0:
                continue
            alpha = int(255 * particle['life'])
            size = int(6 * self.scale * UI_SCALE * particle['life']) + int(2 * self.scale)
            diameter = size * 2
            surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
            pygame.draw.circle(surf, (180, 0, 0, alpha), (size, size), size)
            screen.blit(surf, (int(particle['x'] - size), int(particle['y'] - size)))

class CounterAttackAnimation(SkillAnimation):
    """反击动画：等待对方攻击结束后，使用同款攻击动画进行反击"""
    def __init__(self, source_slot, target_slot, damage, wait_animation=None):
        super().__init__()
        self.source_slot = source_slot
        self.target_slot = target_slot
        self.damage = damage
        self.wait_animation = wait_animation
        self.counter_animation = None
        self.started = False
    
    def start(self):
        super().start()
        self.counter_animation = None
        self.started = False
    
    def _ensure_attack_animation(self):
        if not self.source_slot or not hasattr(self.source_slot, 'has_card'):
            return
        from game.card_animation import AttackAnimation
        self.counter_animation = AttackAnimation(self.source_slot, self.target_slot)
        self.started = True
    
    def update(self, dt):
        if self.start_time is None:
            return False
        if self.wait_animation and not getattr(self.wait_animation, 'finished', False):
            return False
        if not self.counter_animation:
            self._ensure_attack_animation()
        if not self.counter_animation:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        finished = self.counter_animation.update(dt)
        if finished:
            self.finished = True
            if self.on_complete:
                self.on_complete()
        return finished
    
    def draw(self, screen):
        if self.counter_animation:
            self.counter_animation.draw(screen)

class DodgeShakeAnimation(SkillAnimation):
    """闪避动画：左右快速抖动并发光"""
    def __init__(self, target_slot):
        super().__init__()
        self.target_slot = target_slot
        self.duration = 400
        self.target_rect = None
    
    def start(self):
        super().start()
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            self.target_rect = self.target_slot.rect.copy()
        else:
            self.target_rect = pygame.Rect(0, 0, 120, 180)
    
    def update(self, dt):
        if self.start_time is None:
            return False
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed >= self.duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        return False
    
    def draw(self, screen):
        if not self.target_rect:
            return
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = elapsed / self.duration
        offset = math.sin(progress * math.pi * 6) * 8 * UI_SCALE
        shake_rect = self.target_rect.move(offset, 0)
        glow = pygame.Surface(shake_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glow, (200, 200, 255, 90), glow.get_rect(), border_radius=int(12 * UI_SCALE))
        screen.blit(glow, shake_rect.topleft)

class LifeStealAnimation(SkillAnimation):
    """吸血动画：红色粒子从目标汇聚到攻击者"""
    def __init__(self, source_pos, attacker_slot, heal_amount):
        super().__init__()
        self.source_pos = source_pos
        self.attacker_slot = attacker_slot
        self.heal_amount = heal_amount
        self.duration = 1200
        self.particles = []
        self.end_pos = None
        self.direction = (0, 0)
        self.perp = (0, 0)
    
    def start(self):
        super().start()
        if self.attacker_slot and hasattr(self.attacker_slot, 'rect'):
            self.end_pos = self.attacker_slot.rect.center
        else:
            self.end_pos = self.source_pos or (400, 300)
        if not self.source_pos:
            offset = int(120 * UI_SCALE)
            self.source_pos = (self.end_pos[0], self.end_pos[1] - offset)
        dx = self.end_pos[0] - self.source_pos[0]
        dy = self.end_pos[1] - self.source_pos[1]
        length = max(1.0, math.hypot(dx, dy))
        self.direction = (dx / length, dy / length)
        self.perp = (-self.direction[1], self.direction[0])
        self._create_particles()
    
    def _create_particles(self):
        count = 30
        for _ in range(count):
            self.particles.append({
                'delay': random.uniform(0, 150),
                'duration': random.uniform(360, 520),
                'offset': random.uniform(-40 * UI_SCALE, 40 * UI_SCALE),
                'phase': random.uniform(0, math.pi * 2),
                'progress': 0.0
            })
    
    def update(self, dt):
        if self.start_time is None:
            return False
        elapsed = pygame.time.get_ticks() - self.start_time
        finished = True
        for particle in self.particles:
            local = elapsed - particle['delay']
            if local < 0:
                finished = False
                continue
            progress = min(1.0, local / particle['duration'])
            particle['progress'] = progress
            if progress < 1.0:
                finished = False
        if elapsed >= self.duration or finished:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        return False
    
    def draw(self, screen):
        if not self.source_pos or not self.end_pos:
            return
        # 绘制柔和能量束
        for i in range(12):
            t = i / 11
            base_x = self.source_pos[0] + (self.end_pos[0] - self.source_pos[0]) * t
            base_y = self.source_pos[1] + (self.end_pos[1] - self.source_pos[1]) * t
            radius = int(6 * UI_SCALE * (1 - abs(0.5 - t))) + 2
            alpha = int(80 * (1 - abs(0.5 - t)))
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 45, 70, alpha), (radius, radius), radius)
            screen.blit(surf, (int(base_x - radius), int(base_y - radius)))
        # 绘制粒子
        time_offset = (pygame.time.get_ticks() - self.start_time) / 1000 if self.start_time else 0
        for particle in self.particles:
            progress = particle['progress']
            if progress <= 0 or progress > 1:
                continue
            swirl = math.sin(progress * math.pi * 2 + particle['phase']) * (1 - progress) * 25 * UI_SCALE
            offset = particle['offset'] * (1 - progress) + swirl
            base_x = self.source_pos[0] + (self.end_pos[0] - self.source_pos[0]) * progress
            base_y = self.source_pos[1] + (self.end_pos[1] - self.source_pos[1]) * progress
            x = base_x + self.perp[0] * offset
            y = base_y + self.perp[1] * offset
            size = int(10 * UI_SCALE * (1 - progress * 0.6))
            alpha = int(220 * (1 - progress) + 35)
            color = (255, int(30 + 50 * (1 - progress)), int(40 + 30 * progress))
            particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (*color, alpha), (size, size), size)
            screen.blit(particle_surf, (int(x - size), int(y - size)))
        # 攻击者吸收时的脉冲
        pulse = (math.sin(time_offset * math.pi * 2) + 1) * 0.5
        glow_radius = int(18 * UI_SCALE + pulse * 8)
        glow_alpha = int(160 + pulse * 80)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 55, 70, glow_alpha // 2), (glow_radius, glow_radius), glow_radius)
        pygame.draw.circle(glow_surf, (255, 110, 120, glow_alpha), (glow_radius, glow_radius), int(glow_radius * 0.6))
        screen.blit(glow_surf, (int(self.end_pos[0] - glow_radius), int(self.end_pos[1] - glow_radius)))

"""=====抽卡、还魂、加速、延迟、自毁====="""
# ============= 通用能量球动画 =============
class EnergyOrbAnimation(SkillAnimation):
    """从释放者飞向目标位置的能量球动画"""
    def __init__(self, attacker_slot, target_pos, color=(255, 255, 255), radius=32, travel_duration=800, hold_time=200):
        super().__init__()
        self.attacker_slot = attacker_slot
        self.target_pos = target_pos
        self.color = color
        self.base_radius = int(radius * UI_SCALE)
        self.travel_duration = travel_duration
        self.hold_time = hold_time
        self.total_duration = self.travel_duration + self.hold_time
        self.start_pos = None
        self.current_pos = None
        self.hit_triggered = False
        self.trail_positions = []
        self.trail_max = 6
    
    def start(self):
        super().start()
        if self.attacker_slot and hasattr(self.attacker_slot, 'rect'):
            self.start_pos = self.attacker_slot.rect.center
        else:
            self.start_pos = self.target_pos or (0, 0)
        self.current_pos = self.start_pos
    
    def update(self, dt):
        if self.start_time is None or not self.target_pos or not self.start_pos:
            self.finished = True
            if not self.hit_triggered and self.on_hit:
                self.on_hit()
            if self.on_complete:
                self.on_complete()
            return True
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed < self.travel_duration:
            t = max(0.0, min(1.0, elapsed / self.travel_duration))
            x = self.start_pos[0] + (self.target_pos[0] - self.start_pos[0]) * t
            y = self.start_pos[1] + (self.target_pos[1] - self.start_pos[1]) * t
            self.current_pos = (x, y)
        else:
            self.current_pos = self.target_pos
            if not self.hit_triggered and self.on_hit:
                self.on_hit()
            self.hit_triggered = True
        # 记录拖尾
        if self.current_pos:
            self.trail_positions.append(self.current_pos)
            if len(self.trail_positions) > self.trail_max:
                self.trail_positions.pop(0)
        if elapsed >= self.total_duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        return False
    
    def draw(self, screen):
        if not self.current_pos:
            return
        # 绘制拖尾
        for idx, pos in enumerate(self.trail_positions):
            alpha = int(60 + 160 * (idx / max(1, len(self.trail_positions))))
            radius = int(self.base_radius * (0.6 + 0.4 * (idx / max(1, len(self.trail_positions)))))
            trail_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surface, (*self.color[:3], alpha), (radius, radius), radius)
            rect = trail_surface.get_rect(center=(int(pos[0]), int(pos[1])))
            screen.blit(trail_surface, rect)
        # 绘制主体
        glow_radius = int(self.base_radius * 1.8)
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (*self.color[:3], 120), (glow_radius, glow_radius), glow_radius)
        glow_rect = glow_surface.get_rect(center=(int(self.current_pos[0]), int(self.current_pos[1])))
        screen.blit(glow_surface, glow_rect)
        pygame.draw.circle(screen, self.color, (int(self.current_pos[0]), int(self.current_pos[1])), self.base_radius)

class ExplosionAnimation(SkillAnimation):
    """自毁动画：在目标位置快速膨胀的爆炸效果"""
    def __init__(self, target_slot):
        super().__init__()
        self.target_slot = target_slot
        self.start_delay = 400
        self.expand_duration = 600
        self.fade_duration = 400
        self.total_duration = self.start_delay + self.expand_duration + self.fade_duration
        self.current_size = 0
        self.max_size = int(300 * UI_SCALE)
        self.explosion_image_original = None
        self.explosion_image_scaled = None
        self.current_alpha = 255
        self.target_pos = None
        self.hit_triggered = False
        self.load_image()

    def load_image(self):
        try:
            self.explosion_image_original = pygame.image.load("assets/skill/explosion.png").convert_alpha()
        except Exception:
            size = int(256 * UI_SCALE)
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 200, 80), (size // 2, size // 2), size // 2)
            pygame.draw.circle(surf, (255, 120, 40), (size // 2, size // 2), size // 3)
            pygame.draw.circle(surf, (255, 255, 200), (size // 2, size // 2), size // 4)
            self.explosion_image_original = surf

    def start(self):
        super().start()
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            self.target_pos = self.target_slot.rect.center
        else:
            self.target_pos = (400, 300)

    def update(self, dt):
        if self.start_time is None:
            return False
        elapsed = pygame.time.get_ticks() - self.start_time
        if elapsed < self.start_delay:
            self.current_size = int(self.max_size * 0.2)
            self.current_alpha = 255
        elif elapsed < self.start_delay + self.expand_duration:
            t = (elapsed - self.start_delay) / self.expand_duration
            self.current_size = int(self.max_size * (0.2 + 0.8 * t))
            self.current_alpha = 255
            if t >= 0.5 and not self.hit_triggered:
                if self.on_hit:
                    self.on_hit()
                self.hit_triggered = True
        else:
            fade_elapsed = elapsed - self.start_delay - self.expand_duration
            fade_t = max(0.0, min(1.0, fade_elapsed / self.fade_duration))
            self.current_size = int(self.max_size)
            self.current_alpha = int(255 * (1 - fade_t))
            if not self.hit_triggered:
                if self.on_hit:
                    self.on_hit()
                self.hit_triggered = True
        size = max(10, self.current_size)
        self.explosion_image_scaled = pygame.transform.scale(self.explosion_image_original, (size, size))
        self.explosion_image_scaled.set_alpha(max(0, min(255, self.current_alpha)))
        if elapsed >= self.total_duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        return False

    def draw(self, screen):
        if not self.target_pos or not self.explosion_image_scaled:
            return
        rect = self.explosion_image_scaled.get_rect(center=self.target_pos)
        screen.blit(self.explosion_image_scaled, rect)

"""=====免疫、不死、复活====="""

"""=====群/单、振奋、祝福====="""
class BlessingAuraAnimation(SkillAnimation):
    """祝福光环：金色光球+粒子环绕目标"""
    def __init__(self, target_slot, duration=800):
        super().__init__()
        self.target_slot = target_slot
        self.duration = duration
        self.size = int(250 * UI_SCALE)
        self.target_pos = None
        self.progress = 0.0
        self.hit_triggered = False
        self.hit_delay = int(self.duration * 0.35)
        self.particles = []
        self.sparkles = []
        self.last_particle_emit = 0
        self.last_sparkle_emit = 0
        self.particle_interval = 70
        self.sparkle_interval = 140
    
    def start(self):
        super().start()
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            self.target_pos = self.target_slot.rect.center
        else:
            self.target_pos = (400, 300)
        now = pygame.time.get_ticks()
        self.last_particle_emit = now
        self.last_sparkle_emit = now
        # 预先生成一些粒子/闪光让动画更饱满
        for _ in range(12):
            self._emit_particle(now - random.randint(0, 200))
        for _ in range(6):
            self._emit_sparkle(now - random.randint(0, 160))
    
    def _emit_particle(self, start_time=None):
        base_time = start_time if start_time is not None else pygame.time.get_ticks()
        self.particles.append({
            "start": base_time,
            "lifetime": random.randint(450, 900),
            "angle": random.uniform(0, math.pi * 2),
            "radius": random.uniform(self.size * 0.15, self.size * 0.45),
            "size": int(random.randint(3, 6) * UI_SCALE),
            "phase": random.uniform(0, math.pi * 2)
        })
    
    def _emit_sparkle(self, start_time=None):
        base_time = start_time if start_time is not None else pygame.time.get_ticks()
        spread = self.size * 0.25
        self.sparkles.append({
            "start": base_time,
            "lifetime": random.randint(220, 360),
            "offset": (
                random.uniform(-spread, spread),
                random.uniform(-spread, spread)
            ),
            "size": int(random.randint(16, 26) * UI_SCALE)
        })
    
    def _trigger_hit(self):
        if not self.hit_triggered:
            self.hit_triggered = True
            if self.on_hit:
                self.on_hit()
    
    def _cleanup_effects(self, now):
        self.particles = [p for p in self.particles if now - p["start"] < p["lifetime"]]
        self.sparkles = [s for s in self.sparkles if now - s["start"] < s["lifetime"]]
    
    def update(self, dt):
        if self.start_time is None:
            return False
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        self.progress = min(1.0, elapsed / self.duration)
        if not self.hit_triggered and elapsed >= self.hit_delay:
            self._trigger_hit()
        if now - self.last_particle_emit >= self.particle_interval:
            self.last_particle_emit = now
            self._emit_particle()
        if now - self.last_sparkle_emit >= self.sparkle_interval:
            self.last_sparkle_emit = now
            self._emit_sparkle()
        self._cleanup_effects(now)
        if elapsed >= self.duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        return False
    
    def _draw_base_aura(self, screen, pulse):
        current_size = int(self.size * pulse)
        radius = current_size // 2
        base = pygame.Surface((current_size, current_size), pygame.SRCALPHA)
        pygame.draw.circle(base, (255, 215, 120, 65), (radius, radius), radius)
        pygame.draw.circle(base, (255, 235, 170, 140), (radius, radius), int(radius * 0.75))
        pygame.draw.circle(base, (255, 255, 210, 220), (radius, radius), int(radius * 0.45))
        screen.blit(base, base.get_rect(center=self.target_pos))
        # 光线
        ray_surface = pygame.Surface((current_size, current_size), pygame.SRCALPHA)
        ray_count = 8
        center = (radius, radius)
        for i in range(ray_count):
            angle = (i / ray_count) * (math.pi * 2) + self.progress * math.pi * 2
            end_pos = (
                center[0] + math.cos(angle) * radius,
                center[1] + math.sin(angle) * radius
            )
            pygame.draw.line(ray_surface, (255, 255, 200, 50), center, end_pos, 3)
        screen.blit(ray_surface, ray_surface.get_rect(center=self.target_pos))
        # 中心光球
        orb_radius = max(6, int(self.size * 0.18 + 8 * math.sin(self.progress * math.pi * 2)))
        orb = pygame.Surface((orb_radius * 2, orb_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(orb, (255, 255, 200, 230), (orb_radius, orb_radius), orb_radius)
        pygame.draw.circle(orb, (255, 255, 255, 255), (orb_radius, orb_radius), max(2, orb_radius // 2))
        screen.blit(orb, orb.get_rect(center=self.target_pos))

    def _draw_particles(self, screen, now):
        for particle in self.particles:
            age = now - particle["start"]
            progress = age / particle["lifetime"]
            if progress >= 1:
                continue
            angle = particle["angle"] + progress * math.pi * 1.5
            radius = particle["radius"] * (0.7 + 0.3 * math.sin(progress * math.pi))
            pos = (
                self.target_pos[0] + math.cos(angle) * radius,
                self.target_pos[1] + math.sin(angle) * radius
            )
            size = max(2, int(particle["size"] * (1 - progress * 0.6)))
            alpha = int(210 * (1 - progress))
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 240, 180, alpha), (size, size), size)
            screen.blit(surf, (int(pos[0] - size), int(pos[1] - size)))

    def _draw_sparkles(self, screen, now):
        for sparkle in self.sparkles:
            age = now - sparkle["start"]
            progress = age / sparkle["lifetime"]
            if progress >= 1:
                continue
            size = max(4, int(sparkle["size"] * (1 + progress * 0.2)))
            alpha = int(200 * (1 - progress))
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            color = (255, 255, 210, alpha)
            center = (size // 2, size // 2)
            pygame.draw.line(surf, color, (0, center[1]), (size, center[1]), max(1, size // 6))
            pygame.draw.line(surf, color, (center[0], 0), (center[0], size), max(1, size // 6))
            offset_pos = (
                int(self.target_pos[0] + sparkle["offset"][0]),
                int(self.target_pos[1] + sparkle["offset"][1])
            )
            screen.blit(surf, surf.get_rect(center=offset_pos))

    def draw(self, screen):
        if not self.target_pos:
            return
        now = pygame.time.get_ticks()
        pulse = 0.85 + 0.15 * math.sin(self.progress * math.pi * 2)
        self._draw_base_aura(screen, pulse)
        self._draw_particles(screen, now)
        self._draw_sparkles(screen, now)

class MultiBlessingAuraAnimation(SkillAnimation):
    def __init__(self, target_slots, duration=800):
        super().__init__()
        self.animations = [BlessingAuraAnimation(slot, duration) for slot in target_slots if slot]
        self.hit_triggered = False
        self.hit_delay = int(duration * 0.35)
    
    def start(self):
        super().start()
        self.hit_triggered = False
        for anim in self.animations:
            anim.start()
            anim.on_hit = None
            anim.on_complete = None
    
    def _trigger_hit(self):
        if not self.hit_triggered:
            self.hit_triggered = True
            if self.on_hit:
                self.on_hit()
    
    def update(self, dt):
        if not self.animations:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        now = pygame.time.get_ticks()
        if not self.hit_triggered and self.start_time and now - self.start_time >= self.hit_delay:
            self._trigger_hit()
        all_finished = True
        for anim in self.animations:
            if not anim.finished:
                anim.update(dt)
                all_finished = False
        if all_finished:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        return False
    
    def draw(self, screen):
        for anim in self.animations:
            if not anim.finished:
                anim.draw(screen)

class SwordInspireAnimation(SkillAnimation):
    """振奋动画：剑图标淡入淡出"""
    def __init__(self, target_slot, duration=800):
        super().__init__()
        self.target_slot = target_slot
        self.duration = duration
        self.target_pos = None
        self.alpha = 0
        self.size = int(250 * UI_SCALE)
        self.sword_image = None
        self.load_image()
    
    def load_image(self):
        try:
            original = pygame.image.load("assets/skill/sword.png").convert_alpha()
            self.sword_image = pygame.transform.smoothscale(original, (self.size, self.size))
        except Exception:
            surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.polygon(surf, (255, 255, 255, 200), [
                (self.size // 2, 0),
                (self.size * 3 // 4, self.size),
                (self.size // 4, self.size)
            ])
            self.sword_image = surf
    
    def start(self):
        super().start()
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            self.target_pos = self.target_slot.rect.center
        else:
            self.target_pos = (400, 300)
    
    def update(self, dt):
        if self.start_time is None:
            return False
        elapsed = pygame.time.get_ticks() - self.start_time
        progress = min(1.0, elapsed / self.duration)
        if progress < 0.5:
            self.alpha = int(255 * (progress / 0.5))
        else:
            self.alpha = int(255 * (1 - (progress - 0.5) / 0.5))
        if elapsed >= self.duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        return False
    
    def draw(self, screen):
        if not self.target_pos or not self.sword_image:
            return
        img = self.sword_image.copy()
        img.set_alpha(max(0, min(255, self.alpha)))
        rect = img.get_rect(center=self.target_pos)
        screen.blit(img, rect)

class MultiSwordInspireAnimation(SkillAnimation):
    def __init__(self, target_slots, duration=1000):
        super().__init__()
        self.animations = [SwordInspireAnimation(slot, duration) for slot in target_slots if slot]
    
    def start(self):
        super().start()
        for anim in self.animations:
            anim.start()
            anim.on_hit = None
            anim.on_complete = None
    
    def update(self, dt):
        if not self.animations:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        all_finished = True
        for anim in self.animations:
            if not anim.finished:
                anim.update(dt)
                all_finished = False
        if all_finished:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        return False
    
    def draw(self, screen):
        for anim in self.animations:
            if not anim.finished:
                anim.draw(screen)

"""=====诅咒====="""
class CurseMarkAnimation(SkillAnimation):
    """诅咒动画：curse.png 淡入淡出覆盖目标"""
    def __init__(self, target_slot, duration=900):
        super().__init__()
        self.target_slot = target_slot
        self.duration = duration
        self.size = int(250 * UI_SCALE)
        self.target_pos = None
        self.alpha = 0
        self.hit_triggered = False
        self.hit_time = int(self.duration * 0.35)
        self.image = None
        self.load_image()

    def load_image(self):
        try:
            raw = pygame.image.load("assets/skill/curse.png").convert_alpha()
            self.image = pygame.transform.smoothscale(raw, (self.size, self.size))
        except Exception:
            surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (120, 0, 120, 220), (self.size // 2, self.size // 2), self.size // 2)
            pygame.draw.circle(surf, (255, 0, 255, 180), (self.size // 2, self.size // 2), int(self.size * 0.3))
            self.image = surf

    def start(self):
        super().start()
        if self.target_slot and hasattr(self.target_slot, 'rect'):
            self.target_pos = self.target_slot.rect.center
        else:
            self.target_pos = (400, 300)

    def _trigger_hit(self):
        if not self.hit_triggered and self.on_hit:
            self.hit_triggered = True
            self.on_hit()

    def update(self, dt):
        if self.start_time is None:
            return False
        now = pygame.time.get_ticks()
        elapsed = now - self.start_time
        progress = min(1.0, elapsed / self.duration)
        fade = math.sin(progress * math.pi)
        self.alpha = int(255 * fade)
        if not self.hit_triggered and elapsed >= self.hit_time:
            self._trigger_hit()
        if elapsed >= self.duration:
            self.finished = True
            if self.on_complete:
                self.on_complete()
            return True
        return False

    def draw(self, screen):
        if not self.target_pos or not self.image or self.alpha <= 0:
            return
        # 轻微缩放脉冲
        respire = 1.0 + 0.05 * math.sin(pygame.time.get_ticks() * 0.01)
        scaled_size = max(10, int(self.size * respire))
        render_img = pygame.transform.smoothscale(self.image, (scaled_size, scaled_size))
        render_img.set_alpha(self.alpha)
        rect = render_img.get_rect(center=self.target_pos)
        screen.blit(render_img, rect)
