"""
卡牌战斗动画系统
"""
import pygame
import math
import random


class CardAnimation:
    """卡牌动画基类"""
    
    def __init__(self, slot, duration=1.0):
        self.slot = slot
        self.duration = duration
        self.elapsed = 0.0
        self.finished = False
        self.original_pos = slot.rect.copy()
    
    def update(self, dt):
        """更新动画"""
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finished = True
            self.on_finish()
        return self.finished
    
    def on_finish(self):
        """动画结束回调"""
        pass
    
    def draw(self, screen):
        """绘制动画"""
        pass


class AttackAnimation(CardAnimation):
    """攻击动画：上抬 → 加速下砸 → 归位"""
    
    def __init__(self, attacker_slot, target_slot=None, duration=0.7):
        super().__init__(attacker_slot, duration)
        self.target_slot = target_slot
        
        # 动画阶段时长
        self.pullback_duration = duration * 0.2   # 上抬：0.14秒
        self.strike_duration = duration * 0.3     # 下砸：0.21秒
        self.return_duration = duration * 0.5     # 归位：0.35秒
        
        # 位置偏移
        self.offset_x = 0
        self.offset_y = 0
        
        # 动画阶段
        self.phase = "pullback"
        self.phase_timer = 0.0
    
    def update(self, dt):
        """更新攻击动画"""
        self.elapsed += dt
        self.phase_timer += dt
        
        # === 上抬阶段 ===
        if self.phase == "pullback":
            progress = min(1.0, self.phase_timer / self.pullback_duration)
            # 缓动：ease-out（快速上抬后减速）
            t = 1 - (1 - progress) ** 2
            self.offset_y = -50 * t  # 向上抬起50像素
            
            if self.phase_timer >= self.pullback_duration:
                self.phase = "strike"
                self.phase_timer = 0.0
        
        # === 下砸阶段（加速度攻击）===
        elif self.phase == "strike":
            progress = min(1.0, self.phase_timer / self.strike_duration)
            # 缓动：ease-in（加速下砸）
            t = progress ** 3  # 三次方，模拟重力加速
            self.offset_y = -50 + 70 * t  # 从-50加速下砸到+20
            
            # 轻微左右浮动（冲击感）
            self.offset_x = 3 * math.sin(progress * math.pi * 2)
            
            if self.phase_timer >= self.strike_duration:
                self.phase = "return"
                self.phase_timer = 0.0
                # 触发目标震动
                if self.target_slot:
                    self.target_slot.start_shake_animation(duration=0.25, intensity=8)
        
        # === 归位阶段 ===
        elif self.phase == "return":
            progress = min(1.0, self.phase_timer / self.return_duration)
            # 缓动：ease-out（减速归位）
            t = 1 - (1 - progress) ** 3
            self.offset_y = 20 * (1 - t)  # 从+20平滑返回0
            self.offset_x = 0
            
            if self.phase_timer >= self.return_duration:
                self.finished = True
                self.offset_x = 0
                self.offset_y = 0
        
        return self.finished
    
    def draw(self, screen):
        """绘制攻击动画"""
        if self.slot.has_card() and self.slot.card_image:
            # 创建偏移后的矩形
            animated_rect = self.slot.rect.copy()
            animated_rect.x += int(self.offset_x)
            animated_rect.y += int(self.offset_y)
            
            # 绘制卡牌
            screen.blit(self.slot.card_image, animated_rect)
            
            # 绘制属性
            self.slot.draw_stats(screen, offset_x=int(self.offset_x), offset_y=int(self.offset_y))


class ShakeAnimation(CardAnimation):
    """受击震动动画（快速抖动）"""
    
    def __init__(self, slot, duration=0.25, intensity=8):
        super().__init__(slot, duration)
        self.intensity = intensity
        self.offset_x = 0
        self.offset_y = 0
        self.shake_frequency = 30  # 每秒30次震动（高频）
        self.last_shake_time = 0.0
    
    def update(self, dt):
        """更新震动动画"""
        self.elapsed += dt
        self.last_shake_time += dt
        
        if self.elapsed >= self.duration:
            self.finished = True
            self.offset_x = 0
            self.offset_y = 0
        else:
            # 高频震动
            shake_interval = 1.0 / self.shake_frequency
            
            if self.last_shake_time >= shake_interval:
                self.last_shake_time = 0.0
                
                # 震动强度随时间衰减
                progress = self.elapsed / self.duration
                current_intensity = self.intensity * (1 - progress ** 0.5)
                
                # 随机方向快速抖动
                angle = random.uniform(0, math.pi * 2)
                self.offset_x = current_intensity * math.cos(angle)
                self.offset_y = current_intensity * math.sin(angle)
        
        return self.finished
    
    def draw(self, screen):
        """绘制震动动画"""
        if self.slot.has_card() and self.slot.card_image:
            animated_rect = self.slot.rect.copy()
            animated_rect.x += int(self.offset_x)
            animated_rect.y += int(self.offset_y)
            
            # 绘制卡牌
            screen.blit(self.slot.card_image, animated_rect)
            
            # 绘制属性
            self.slot.draw_stats(screen, offset_x=int(self.offset_x), offset_y=int(self.offset_y))


class SlideAnimation(CardAnimation):
    """滑动动画：用于填补空位"""
    
    def __init__(self, slot, target_x, target_y, duration=0.4):
        super().__init__(slot, duration)
        self.start_x = slot.rect.x
        self.start_y = slot.rect.y
        self.target_x = target_x
        self.target_y = target_y
    
    def update(self, dt):
        """更新滑动动画"""
        self.elapsed += dt
        
        if self.elapsed >= self.duration:
            self.finished = True
            self.slot.rect.x = self.target_x
            self.slot.rect.y = self.target_y
        else:
            # 缓动函数：ease-out（开始快，结束慢）
            progress = self.elapsed / self.duration
            t = 1 - (1 - progress) ** 3
            
            self.slot.rect.x = int(self.start_x + (self.target_x - self.start_x) * t)
            self.slot.rect.y = int(self.start_y + (self.target_y - self.start_y) * t)
        
        return self.finished