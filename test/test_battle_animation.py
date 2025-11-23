"""
战斗动画测试脚本
演示两张卡牌循环互相攻击
"""
import pygame
import sys
import os

# 获取项目根目录（父目录）
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config import *
from game.card_animation import AttackAnimation, ShakeAnimation
from utils.card_database import CardData

# 测试用简化槽位类
class TestCardSlot:
    """测试用卡槽"""
    
    def __init__(self, x, y, width, height, card_name, owner="player"):
        self.rect = pygame.Rect(x, y, width, height)
        self.owner = owner
        self.original_rect = self.rect.copy()
        
        # 创建测试卡牌数据
        self.card_data = CardData(
            card_id=f"TEST_{card_name}",
            name=card_name,
            image_path="",
            rarity="SS",
            cd=3,
            atk=1,
            hp=999
        )
        
        # 动画
        self.shake_animation = None
        
        # 创建卡牌图片
        self.create_card_image()
    
    def create_card_image(self):
        """创建测试卡牌图片"""
        self.card_image = pygame.Surface((self.rect.width, self.rect.height))
        
        # 根据所有者选择颜色
        if self.owner == "player":
            color = (50, 100, 200)
        else:
            color = (200, 50, 50)
        
        self.card_image.fill(color)
        
        # 边框
        pygame.draw.rect(self.card_image, (255, 255, 255), 
                        (0, 0, self.rect.width, self.rect.height), 3)
        
        # 卡牌名称
        font = get_font(24)
        name_text = font.render(self.card_data.name, True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        self.card_image.blit(name_text, name_rect)
    
    def has_card(self):
        return True
    
    def start_shake_animation(self, duration=0.25, intensity=8):
        """开始震动动画"""
        self.shake_animation = ShakeAnimation(self, duration, intensity)
    
    def update_animations(self, dt):
        """更新动画"""
        if self.shake_animation:
            if self.shake_animation.update(dt):
                self.shake_animation = None
    
    def draw(self, screen, offset_x=0, offset_y=0):
        """绘制卡槽"""
        # 检查是否有震动动画
        if self.shake_animation:
            self.shake_animation.draw(screen)
        else:
            # 正常绘制
            draw_rect = self.rect.copy()
            draw_rect.x += int(offset_x)
            draw_rect.y += int(offset_y)
            
            screen.blit(self.card_image, draw_rect)
            self.draw_stats(screen, offset_x, offset_y)
    
    def draw_stats(self, screen, offset_x=0, offset_y=0):
        """绘制属性"""
        font = get_font(28)
        
        # ATK（左下角红色）
        atk_text = f"{self.card_data.atk}"
        atk_surface = font.render(atk_text, True, (255, 50, 50))
        atk_outline = font.render(atk_text, True, (0, 0, 0))
        
        atk_pos = (
            self.rect.left + 10 + offset_x,
            self.rect.bottom - 30 + offset_y
        )
        
        # 描边
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            screen.blit(atk_outline, (atk_pos[0] + dx, atk_pos[1] + dy))
        screen.blit(atk_surface, atk_pos)
        
        # HP（右下角绿色）
        hp_text = f"{self.card_data.hp}"
        hp_surface = font.render(hp_text, True, (50, 255, 50))
        hp_outline = font.render(hp_text, True, (0, 0, 0))
        
        hp_rect = hp_surface.get_rect()
        hp_pos = (
            self.rect.right - hp_rect.width - 10 + offset_x,
            self.rect.bottom - 30 + offset_y
        )
        
        # 描边
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            screen.blit(hp_outline, (hp_pos[0] + dx, hp_pos[1] + dy))
        screen.blit(hp_surface, hp_pos)


class BattleAnimationTest:
    """战斗动画测试"""
    
    def __init__(self):
        pygame.init()
        
        # 创建窗口
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("战斗动画测试 - 两张卡牌循环攻击")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # 创建背景
        self.create_background()
        
        # 创建两张测试卡牌
        card_width = 200
        card_height = 300
        
        # 玩家卡牌（左侧）
        self.player_slot = TestCardSlot(
            150, 250, card_width, card_height,
            "玩家卡", "player"
        )
        
        # 敌人卡牌（右侧）
        self.enemy_slot = TestCardSlot(
            WINDOW_WIDTH - 150 - card_width, 250, card_width, card_height,
            "敌人卡", "enemy"
        )
        
        # 动画状态
        self.animations = []
        self.attack_timer = 0.0
        self.attack_interval = 1.5  # 1.5秒一次攻击
        self.current_attacker = "player"  # player 或 enemy
        
        # UI字体
        self.title_font = get_font(36)
        self.info_font = get_font(24)
        
        print("=" * 60)
        print("战斗动画测试")
        print("=" * 60)
        print("说明：")
        print("  - 两张卡牌轮流发动攻击")
        print("  - ATK: 1, HP: 999")
        print("  - 攻击动画：后退 → 加速冲刺 → 归位")
        print("  - 受击动画：快速震动")
        print("  - 按 ESC 退出")
        print("=" * 60)
    
    def create_background(self):
        """创建背景"""
        self.background = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # 渐变背景
        for y in range(WINDOW_HEIGHT):
            ratio = y / WINDOW_HEIGHT
            color = (
                int(30 + ratio * 20),
                int(30 + ratio * 40),
                int(50 + ratio * 30)
            )
            pygame.draw.line(self.background, color, (0, y), (WINDOW_WIDTH, y))
    
    def trigger_attack(self):
        """触发一次攻击"""
        if self.current_attacker == "player":
            attacker = self.player_slot
            defender = self.enemy_slot
            attacker_name = "玩家"
        else:
            attacker = self.enemy_slot
            defender = self.player_slot
            attacker_name = "敌人"
        
        print(f"\n[攻击] {attacker_name} 发动攻击！")
        
        # 创建攻击动画
        attack_anim = AttackAnimation(attacker, defender, duration=0.7)
        self.animations.append(attack_anim)
        
        # 造成伤害（虽然HP很高，只是演示）
        old_hp = defender.card_data.hp
        defender.card_data.hp -= attacker.card_data.atk
        
        print(f"  → 造成 {attacker.card_data.atk} 点伤害")
        print(f"  → 剩余 HP: {defender.card_data.hp}/{old_hp}")
        
        # 切换攻击者
        self.current_attacker = "enemy" if self.current_attacker == "player" else "player"
    
    def update(self, dt):
        """更新"""
        # 更新卡槽动画
        self.player_slot.update_animations(dt)
        self.enemy_slot.update_animations(dt)
        
        # 更新攻击动画
        self.animations = [anim for anim in self.animations if not anim.update(dt)]
        
        # 攻击计时器
        self.attack_timer += dt
        if self.attack_timer >= self.attack_interval:
            self.attack_timer = 0.0
            self.trigger_attack()
    
    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                # 按空格手动触发攻击
                elif event.key == pygame.K_SPACE:
                    print("\n[手动] 触发攻击")
                    self.trigger_attack()
                    self.attack_timer = 0.0
    
    def draw(self):
        """绘制"""
        # 背景
        self.screen.blit(self.background, (0, 0))
        
        # 标题
        title = self.title_font.render("战斗动画测试", True, (255, 215, 0))
        title_rect = title.get_rect(centerx=WINDOW_WIDTH // 2, top=30)
        self.screen.blit(title, title_rect)
        
        # 说明文字
        instructions = [
            "两张卡牌循环攻击 (ATK:1, HP:999)",
            "按 SPACE 手动触发攻击",
            "按 ESC 退出"
        ]
        
        y_offset = 80
        for text in instructions:
            info_surface = self.info_font.render(text, True, (200, 200, 200))
            info_rect = info_surface.get_rect(centerx=WINDOW_WIDTH // 2, top=y_offset)
            self.screen.blit(info_surface, info_rect)
            y_offset += 30
        
        # 攻击倒计时
        next_attack_in = self.attack_interval - self.attack_timer
        countdown = self.info_font.render(
            f"下次攻击: {next_attack_in:.1f}秒", 
            True, (255, 200, 100)
        )
        countdown_rect = countdown.get_rect(centerx=WINDOW_WIDTH // 2, top=y_offset + 20)
        self.screen.blit(countdown, countdown_rect)
        
        # 当前攻击者提示
        current_text = f"当前攻击方: {'玩家' if self.current_attacker == 'player' else '敌人'}"
        current_surface = self.info_font.render(current_text, True, 
            (100, 255, 100) if self.current_attacker == "player" else (255, 100, 100)
        )
        current_rect = current_surface.get_rect(centerx=WINDOW_WIDTH // 2, top=y_offset + 60)
        self.screen.blit(current_surface, current_rect)
        
        # 绘制卡槽
        # 检查是否有攻击动画正在进行
        active_attack_anims = [anim for anim in self.animations if isinstance(anim, AttackAnimation)]
        
        if active_attack_anims:
            # 有攻击动画时，由动画绘制攻击方
            for anim in active_attack_anims:
                anim.draw(self.screen)
            
            # 绘制非攻击方
            if anim.slot == self.player_slot:
                self.enemy_slot.draw(self.screen)
            else:
                self.player_slot.draw(self.screen)
        else:
            # 正常绘制
            self.player_slot.draw(self.screen)
            self.enemy_slot.draw(self.screen)
        
        # 绘制箭头指示
        self.draw_attack_arrow()
        
        pygame.display.flip()
    
    def draw_attack_arrow(self):
        """绘制攻击方向箭头"""
        arrow_y = WINDOW_HEIGHT // 2
        
        if self.current_attacker == "player":
            # 玩家 → 敌人
            start_x = self.player_slot.rect.right + 20
            end_x = self.enemy_slot.rect.left - 20
            color = (100, 200, 255)
        else:
            # 敌人 → 玩家
            start_x = self.enemy_slot.rect.left - 20
            end_x = self.player_slot.rect.right + 20
            color = (255, 100, 100)
        
        # 绘制箭头线
        pygame.draw.line(self.screen, color, 
                        (start_x, arrow_y), (end_x, arrow_y), 3)
        
        # 绘制箭头头部
        arrow_size = 15
        if self.current_attacker == "player":
            # 向右箭头
            points = [
                (end_x, arrow_y),
                (end_x - arrow_size, arrow_y - arrow_size // 2),
                (end_x - arrow_size, arrow_y + arrow_size // 2)
            ]
        else:
            # 向左箭头
            points = [
                (end_x, arrow_y),
                (end_x + arrow_size, arrow_y - arrow_size // 2),
                (end_x + arrow_size, arrow_y + arrow_size // 2)
            ]
        
        pygame.draw.polygon(self.screen, color, points)
    
    def run(self):
        """运行测试"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()
        print("\n测试结束")


if __name__ == "__main__":
    test = BattleAnimationTest()
    test.run()