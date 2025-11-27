""""战斗组件类，包括卡牌槽位和血量条等"""
import pygame
from config import *
from game.card_animation import ShakeAnimation
from utils.image_cache import get_scaled_image

STATE_FONT_SIZE = int(60 * UI_SCALE)
STATE_X_OFFSET = int(20 * UI_SCALE)
STATE_Y_OFFSET = int(80 * UI_SCALE)
ATK_COLOR = (200, 0, 0) # 暗红色
HP_COLOR = (20, 200, 20) # 绿色

"""卡牌槽位类"""
class CardSlot:
    def __init__(self, x, y, width, height, slot_type="battle", owner="player"):
        self.rect = pygame.Rect(x, y, width, height)
        self.slot_type = slot_type  # battle, waiting, discard
        self.owner = owner  # player, enemy
        self.card = None
        self.card_data = None  # 存储 CardData
        self.is_hovered = False
        self.is_highlighted = False
        
        from utils.card_database import get_card_database
        self.card_database = get_card_database()
        self.cd_remaining = 0 # CD倒计时

        # 动画相关
        self.current_animation = None
        self.shake_animation = None
        self.hp_flash_animation = None
        self.original_rect = pygame.Rect(x, y, width, height)

    def set_card(self, card_data):
        """
        放置卡牌
        Args:
            card_data: CardData 对象
        """
        self.card_data = card_data
        self.card = card_data  # 兼容性
        
        # 如果是准备区，初始化 CD
        if self.slot_type == "waiting":
            self.cd_remaining = card_data.cd
        
        # 加载卡牌图片
        self.load_card_image()

    def load_card_image(self):
        """加载卡牌图片"""
        if not self.card_data:
            self.card_image = None
            return
        
        cached = get_scaled_image(
            getattr(self.card_data, 'image_path', None),
            (self.rect.width, self.rect.height)
        )
        if cached:
            self.card_image = cached
        else:
            self.card_image = self.create_placeholder_image()

    def create_placeholder_image(self):
        """创建占位符图片"""
        surface = pygame.Surface((self.rect.width, self.rect.height))
        from config import COLORS
        color = COLORS.get(self.card_data.rarity, (100, 100, 100))
        surface.fill(color)
        
        from config import get_font, UI_SCALE
        border_width = max(2, int(3 * UI_SCALE))
        pygame.draw.rect(surface, (255, 255, 255), 
                        (0, 0, self.rect.width, self.rect.height), border_width)
        
        font = get_font(max(16, int(24 * UI_SCALE)))
        text = font.render(self.card_data.name[:4], True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.rect.width // 2, self.rect.height // 2))
        surface.blit(text, text_rect)
        
        return surface

    def remove_card(self):
        """移除卡牌"""
        card = self.card_data
        self.card = None
        self.card_data = None
        self.card_image = None
        self.cd_remaining = 0
        return card

    def has_card(self):
        """是否有卡牌"""
        return self.card_data is not None

    def reduce_cd(self, amount=1):
        """减少CD 用于准备区"""
        if self.slot_type == "waiting" and self.has_card():
            self.cd_remaining = max(0, self.cd_remaining - amount)
            return self.cd_remaining == 0
        return False

    def increase_cd(self, amount=1):
        """增加CD（延迟上场）"""
        if self.slot_type == "waiting" and self.has_card() and amount > 0:
            self.cd_remaining = max(0, self.cd_remaining + amount)
            return True
        return False

    def draw(self, screen):
        """绘制槽位"""
        if self.has_card():
            # 检查是否有震动动画
            if self.shake_animation:
                self.shake_animation.draw(screen)
            else:
                # 正常绘制卡牌
                if self.card_image:
                    screen.blit(self.card_image, self.rect)
                
                # 准备区：显示 CD
                if self.slot_type == "waiting":
                    self.draw_cd_indicator(screen)
                
                # 战斗区：显示 ATK 和 HP
                elif self.slot_type == "battle":
                    self.draw_stats(screen)
                
                # 悬停高亮
                if self.is_hovered:
                    border_color = (255, 255, 100)
                    border_width = max(3, int(4 * UI_SCALE))
                    pygame.draw.rect(screen, border_color, self.rect, border_width,
                                   border_radius=max(5, int(8 * UI_SCALE)))
            
            # 绘制HP闪烁动画
            if self.hp_flash_animation:
                self.hp_flash_animation.draw(screen)
        else:
            # 空槽位
            alpha = 150 if self.is_highlighted else 80
            slot_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            
            # 根据槽位类型选择颜色
            if self.slot_type == "battle":
                color = (100, 150, 200, alpha)
                border_color = (150, 200, 255, 200)
            elif self.slot_type == "waiting":
                color = (150, 150, 100, alpha)
                border_color = (200, 200, 150, 200)
            else:  # discard
                color = (150, 100, 100, alpha)
                border_color = (200, 150, 150, 200)
            
            slot_surface.fill(color)
            
            # 边框
            border_width = max(2, int(3 * UI_SCALE))
            if self.is_hovered:
                border_width = max(3, int(4 * UI_SCALE))
                border_color = (255, 255, 255, 255)
            
            pygame.draw.rect(slot_surface, border_color, 
                           (0, 0, self.rect.width, self.rect.height), 
                           border_width, border_radius=max(5, int(8 * UI_SCALE)))
            
            screen.blit(slot_surface, self.rect)
    
    """CD指示器（准备区）"""
    def draw_cd_indicator(self, screen):
        from config import get_font, UI_SCALE
        
        # CD 背景框
        cd_width = int(60 * UI_SCALE)
        cd_height = int(40 * UI_SCALE)
        cd_x = self.rect.centerx - cd_width // 2
        cd_y = self.rect.top - cd_height - int(5 * UI_SCALE)
        
        cd_rect = pygame.Rect(cd_x, cd_y, cd_width, cd_height)
        
        # 背景
        cd_surface = pygame.Surface((cd_width, cd_height), pygame.SRCALPHA)
        
        # 根据 CD 状态选择颜色
        if self.cd_remaining == 0:
            bg_color = (100, 255, 100, 200)  # 绿色：准备好
            text_color = (0, 100, 0)
        else:
            bg_color = (255, 200, 100, 200)  # 橙色：冷却中
            text_color = (100, 50, 0)
        
        cd_surface.fill(bg_color)
        pygame.draw.rect(cd_surface, (255, 255, 255), 
                        (0, 0, cd_width, cd_height), 2,
                        border_radius=max(5, int(8 * UI_SCALE)))
        
        screen.blit(cd_surface, cd_rect)
        
        # CD 文字
        font = get_font(max(14, int(20 * UI_SCALE)))
        if self.cd_remaining == 0:
            cd_text = "就绪"
        else:
            cd_text = f"CD:{self.cd_remaining}"
        
        text_surface = font.render(cd_text, True, text_color)
        text_rect = text_surface.get_rect(center=cd_rect.center)
        screen.blit(text_surface, text_rect)
    
    """绘制属性（战斗区）"""
    def draw_stats(self, screen, offset_x=0, offset_y=0):
        font = get_font(STATE_FONT_SIZE)
        
        # ATK（左下角红色）
        atk_text = f"{self.card_data.atk}"
        atk_surface = font.render(atk_text, True, ATK_COLOR)  # 红色
        outline_font = font
        outline_surfaces = [outline_font.render(atk_text, True, (0, 0, 0))]
        atk_pos = (
            self.rect.left + STATE_X_OFFSET + offset_x,
            self.rect.bottom - STATE_Y_OFFSET + offset_y
        )
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            screen.blit(outline_surfaces[0], (atk_pos[0] + dx, atk_pos[1] + dy)) # 绘制描边
        screen.blit(atk_surface, atk_pos) # 绘制ATK
        
        # HP（右下角绿色）
        hp_text = f"{self.card_data.hp}"
        hp_surface = font.render(hp_text, True, HP_COLOR)
        hp_outline = outline_font.render(hp_text, True, (0, 0, 0))
        hp_rect = hp_surface.get_rect()
        hp_pos = (
            self.rect.right - hp_rect.width - STATE_X_OFFSET + offset_x,
            self.rect.bottom - STATE_Y_OFFSET + offset_y
        )
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            screen.blit(hp_outline, (hp_pos[0] + dx, hp_pos[1] + dy)) # 绘制描边
        screen.blit(hp_surface, hp_pos) # 绘制HP

    def start_shake_animation(self, duration=0.4, intensity=5):
        """开始震动动画"""
        self.shake_animation = ShakeAnimation(self, duration, intensity)
    
    def start_hp_flash(self, old_hp, new_hp):
        """开始HP闪烁动画"""
        #from game.card_animation import HPFlashAnimation
        #self.hp_flash_animation = HPFlashAnimation(self, old_hp, new_hp)
    
    def update_animations(self, dt):
        """更新动画"""
        # 更新震动动画
        if self.shake_animation:
            if self.shake_animation.update(dt):
                self.shake_animation = None
        
        # 更新HP闪烁动画
        if self.hp_flash_animation:
            if self.hp_flash_animation.update(dt):
                self.hp_flash_animation = None
    

"""血量条类"""
class HealthBar:
    def __init__(self, x, y, width, height, max_hp, current_hp, is_player=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.is_player = is_player
        self.animated_hp = current_hp # 动画当前血量（用于平滑过渡）
        
    def set_hp(self, hp):
        """设置血量"""
        self.current_hp = max(0, min(hp, self.max_hp))
        
    def update(self, dt):
        """更新血量动画"""
        # 平滑过渡到目标血量
        diff = self.current_hp - self.animated_hp
        self.animated_hp += diff * min(1.0, dt * 5)
        
    def draw(self, screen):
        """绘制血量条"""
        # 背景
        bg_color = (50, 50, 50)
        pygame.draw.rect(screen, bg_color, self.rect, 
                        border_radius=max(5, int(10 * UI_SCALE)))
        
        # 血量条
        hp_ratio = self.animated_hp / self.max_hp
        hp_width = int(self.rect.width * hp_ratio)
        
        if hp_width > 0:
            hp_rect = pygame.Rect(self.rect.x, self.rect.y, hp_width, self.rect.height)
            
            # 根据血量百分比选择颜色
            if hp_ratio > 0.6:
                hp_color = (100, 255, 100) if self.is_player else (255, 100, 100)
            elif hp_ratio > 0.3:
                hp_color = (255, 200, 100)
            else:
                hp_color = (255, 100, 100) if self.is_player else (100, 255, 100)
            
            pygame.draw.rect(screen, hp_color, hp_rect, 
                           border_radius=max(5, int(10 * UI_SCALE)))
        
        # 边框
        border_color = (100, 100, 100)
        border_width = max(2, int(3 * UI_SCALE))
        pygame.draw.rect(screen, border_color, self.rect, border_width,
                        border_radius=max(5, int(10 * UI_SCALE)))
        
        # 血量数字
        font = get_font(max(16, int(24 * UI_SCALE)))
        hp_text = f"{int(self.current_hp)}/{self.max_hp}"
        text_surface = font.render(hp_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
