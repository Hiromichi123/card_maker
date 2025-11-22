"""战斗场景"""
import pygame
import os
from scenes.base_scene import BaseScene
from ui.button import Button
from ui.panel import Panel
from config import *

# 背景设置
BATTLE_BG_BRIGHTNESS = 0.7  # 背景亮度 (0.0-1.0)
BATTLE_BG_ALPHA = 200       # 背景透明度 (0-255)

# 战斗区卡牌槽位尺寸
BATTLE_CARD_BASE_WIDTH = 288   # 战斗区卡牌基础宽度
BATTLE_CARD_BASE_HEIGHT = 432  # 战斗区卡牌基础高度
BATTLE_CARD_SPACING = 10       # 战斗区卡牌间距

# 等候区卡牌槽位尺寸
WAITING_CARD_BASE_WIDTH = 144   # 等候区卡牌基础宽度
WAITING_CARD_BASE_HEIGHT = 216  # 等候区卡牌基础高度
WAITING_CARD_SPACING = 15      # 等候区卡牌间距

# 弃牌堆槽位尺寸
DISCARD_CARD_BASE_WIDTH = 216  # 弃牌堆基础宽度
DISCARD_CARD_BASE_HEIGHT = 324  # 弃牌堆基础高度

# 战斗区布局
BATTLE_SLOTS_COUNT = 5         # 战斗区槽位数量
WAITING_SLOTS_COUNT = 8        # 等候区槽位数量

# 位置配置（屏幕百分比）
PLAYER_BATTLE_Y_RATIO = 0.55   # 玩家战斗区Y位置
ENEMY_BATTLE_Y_RATIO = 0.28    # 敌人战斗区Y位置
PLAYER_WAITING_Y_RATIO = 0.88  # 玩家等候区Y位置
ENEMY_WAITING_Y_RATIO = 0.02   # 敌人等候区Y位置

PLAYER_DISCARD_X_RATIO = 0.92  # 玩家弃牌堆X位置
PLAYER_DISCARD_Y_RATIO = 0.85  # 玩家弃牌堆Y位置
ENEMY_DISCARD_X_RATIO = 0.92   # 敌人弃牌堆X位置
ENEMY_DISCARD_Y_RATIO = 0.05   # 敌人弃牌堆Y位置

# 血量条配置
HEALTH_BAR_WIDTH = 300         # 血量条基础宽度
HEALTH_BAR_HEIGHT = 50         # 血量条基础高度
PLAYER_HEALTH_Y_RATIO = 0.85   # 玩家血量条Y位置
ENEMY_HEALTH_Y_RATIO = 0.08    # 敌人血量条Y位置

"""卡牌槽位类"""
class CardSlot:
    def __init__(self, x, y, width, height, slot_type="battle"):
        self.rect = pygame.Rect(x, y, width, height)
        self.slot_type = slot_type
        self.card = None  # 当前槽位的卡牌
        self.is_hovered = False
        self.is_highlighted = False  # 是否可放置提示
        from utils.card_database import get_card_database
        self.card_database = get_card_database()
        
    def set_card(self, card):
        """放置卡牌"""
        self.card = card
        
    def remove_card(self):
        """移除卡牌"""
        card = self.card
        self.card = None
        return card
        
    def has_card(self):
        """是否有卡牌"""
        return self.card is not None
        
    def draw(self, screen):
        """绘制槽位"""
        # 槽位背景
        if self.card:
            # 有卡牌时不显示槽位框
            pass
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
            
            # 空槽位提示（小圆点或图标）
            if not self.card and self.slot_type == "battle":
                center = self.rect.center
                radius = max(3, int(5 * UI_SCALE))
                pygame.draw.circle(screen, (200, 200, 200, 100), center, radius)

class HealthBar:
    """血量条类"""
    
    def __init__(self, x, y, width, height, max_hp, current_hp, is_player=True):
        """
        Args:
            x, y: 血量条位置
            width, height: 血量条尺寸
            max_hp: 最大血量
            current_hp: 当前血量
            is_player: 是否为玩家（影响颜色）
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.max_hp = max_hp
        self.current_hp = current_hp
        self.is_player = is_player
        
        # 动画当前血量（用于平滑过渡）
        self.animated_hp = current_hp
        
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

class BattleScene(BaseScene):
    """战斗场景"""
    
    def __init__(self, screen):
        super().__init__(screen)
        
        # 背景图片路径（可配置）
        self.background_image_path = "assets/battle_bg.png"
        self.background = self.load_background()
        
        # 字体
        self.title_font = get_font(max(20, int(32 * UI_SCALE)))
        self.info_font = get_font(max(14, int(20 * UI_SCALE)))
        
        # 玩家和敌人血量
        self.player_max_hp = 100
        self.player_current_hp = 100
        self.enemy_max_hp = 100
        self.enemy_current_hp = 100
        
        # 创建血量条
        self.create_health_bars()
        
        # 卡牌槽位
        self.player_battle_slots = []  # 玩家战斗区
        self.enemy_battle_slots = []   # 敌人战斗区
        self.player_waiting_slots = [] # 玩家等候区
        self.enemy_waiting_slots = []  # 敌人等候区
        self.player_discard_slot = None  # 玩家弃牌堆
        self.enemy_discard_slot = None   # 敌人弃牌堆
        
        # 创建槽位
        self.create_slots()
        
        # 创建按钮
        self.create_buttons()
        
    def load_background(self):
        """加载背景图片"""
        if os.path.exists(self.background_image_path):
            try:
                bg = pygame.image.load(self.background_image_path)
                bg = pygame.transform.smoothscale(bg, (WINDOW_WIDTH, WINDOW_HEIGHT))
                bg = bg.convert()
                
                # 应用亮度调整
                bg = self.adjust_brightness(bg, BATTLE_BG_BRIGHTNESS)
                
                # 应用透明度
                if BATTLE_BG_ALPHA < 255:
                    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 255 - BATTLE_BG_ALPHA))
                    bg.blit(overlay, (0, 0))
                
                return bg
            except Exception as e:
                print(f"背景图片加载失败: {self.background_image_path}, 错误: {e}")
                return self.create_default_background()
        else:
            print(f"背景图片不存在: {self.background_image_path}")
            return self.create_default_background()
    
    def adjust_brightness(self, surface, brightness):
        """
        调整Surface亮度
        Args:
            surface: pygame.Surface
            brightness: 亮度值 (0.0-1.0)
        Returns:
            调整后的Surface
        """
        # 创建亮度调整后的surface
        adjusted = surface.copy()
        
        # 创建亮度遮罩
        if brightness < 1.0:
            # 变暗
            darken = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            darken.fill((0, 0, 0))
            darken.set_alpha(int(255 * (1 - brightness)))
            adjusted.blit(darken, (0, 0))
        elif brightness > 1.0:
            # 变亮
            brighten = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            brighten.fill((255, 255, 255))
            brighten.set_alpha(int(255 * (brightness - 1)))
            adjusted.blit(brighten, (0, 0), special_flags=pygame.BLEND_ADD)
        
        return adjusted
    
    def create_default_background(self):
        """创建默认背景"""
        bg = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # 渐变背景
        for y in range(WINDOW_HEIGHT):
            ratio = y / WINDOW_HEIGHT
            # 应用亮度调整
            base_color = (
                int((30 + ratio * 20) * BATTLE_BG_BRIGHTNESS),
                int((30 + ratio * 40) * BATTLE_BG_BRIGHTNESS),
                int((50 + ratio * 30) * BATTLE_BG_BRIGHTNESS)
            )
            pygame.draw.line(bg, base_color, (0, y), (WINDOW_WIDTH, y))
        
        # 中间分界线
        middle_y = WINDOW_HEIGHT // 2
        line_color = tuple(int(c * BATTLE_BG_BRIGHTNESS) for c in (100, 100, 120))
        pygame.draw.line(bg, line_color, 
                        (0, middle_y), (WINDOW_WIDTH, middle_y), 
                        max(2, int(3 * UI_SCALE)))
        
        # 应用透明度
        if BATTLE_BG_ALPHA < 255:
            bg.set_alpha(BATTLE_BG_ALPHA)
        
        return bg
    
    def create_health_bars(self):
        """创建血量条"""
        bar_width = int(HEALTH_BAR_WIDTH * UI_SCALE)
        bar_height = int(HEALTH_BAR_HEIGHT * UI_SCALE)
        margin_x = int(30 * UI_SCALE)
        
        # 玩家血量条（左下）
        player_y = int(WINDOW_HEIGHT * PLAYER_HEALTH_Y_RATIO)
        self.player_health_bar = HealthBar(
            margin_x, player_y, bar_width, bar_height,
            self.player_max_hp, self.player_current_hp, is_player=True
        )
        
        # 敌人血量条（左上）
        enemy_y = int(WINDOW_HEIGHT * ENEMY_HEALTH_Y_RATIO)
        self.enemy_health_bar = HealthBar(
            margin_x, enemy_y, bar_width, bar_height,
            self.enemy_max_hp, self.enemy_current_hp, is_player=False
        )
    
    def create_slots(self):
        """创建所有卡牌槽位"""
        # 战斗区卡牌尺寸（应用UI缩放）
        battle_card_width = int(BATTLE_CARD_BASE_WIDTH * UI_SCALE)
        battle_card_height = int(BATTLE_CARD_BASE_HEIGHT * UI_SCALE)
        battle_card_spacing = int(BATTLE_CARD_SPACING * UI_SCALE)
        
        # 等候区卡牌尺寸（应用UI缩放）
        waiting_card_width = int(WAITING_CARD_BASE_WIDTH * UI_SCALE)
        waiting_card_height = int(WAITING_CARD_BASE_HEIGHT * UI_SCALE)
        waiting_card_spacing = int(WAITING_CARD_SPACING * UI_SCALE)
        
        # 弃牌堆尺寸（应用UI缩放）
        discard_width = int(DISCARD_CARD_BASE_WIDTH * UI_SCALE)
        discard_height = int(DISCARD_CARD_BASE_HEIGHT * UI_SCALE)
        
        # === 战斗区槽位（中间两列，对战）===
        total_battle_width = BATTLE_SLOTS_COUNT * battle_card_width + (BATTLE_SLOTS_COUNT - 1) * battle_card_spacing
        battle_start_x = (WINDOW_WIDTH - total_battle_width) // 2
        
        # 玩家战斗区（下方）
        player_battle_y = int(WINDOW_HEIGHT * PLAYER_BATTLE_Y_RATIO)
        for i in range(BATTLE_SLOTS_COUNT):
            x = battle_start_x + i * (battle_card_width + battle_card_spacing)
            slot = CardSlot(x, player_battle_y, battle_card_width, battle_card_height, "battle")
            self.player_battle_slots.append(slot)
        
        # 敌人战斗区（上方）
        enemy_battle_y = int(WINDOW_HEIGHT * ENEMY_BATTLE_Y_RATIO)
        for i in range(BATTLE_SLOTS_COUNT):
            x = battle_start_x + i * (battle_card_width + battle_card_spacing)
            slot = CardSlot(x, enemy_battle_y, battle_card_width, battle_card_height, "battle")
            self.enemy_battle_slots.append(slot)
        
        # === 等候区槽位（边缘一排）===
        total_waiting_width = WAITING_SLOTS_COUNT * waiting_card_width + (WAITING_SLOTS_COUNT - 1) * waiting_card_spacing
        waiting_start_x = (WINDOW_WIDTH - total_waiting_width) // 2
        
        # 玩家等候区（靠近玩家侧底部）
        player_waiting_y = int(WINDOW_HEIGHT * PLAYER_WAITING_Y_RATIO)
        for i in range(WAITING_SLOTS_COUNT):
            x = waiting_start_x + i * (waiting_card_width + waiting_card_spacing)
            slot = CardSlot(x, player_waiting_y, waiting_card_width, waiting_card_height, "waiting")
            self.player_waiting_slots.append(slot)
        
        # 敌人等候区（靠近敌人侧顶部）
        enemy_waiting_y = int(WINDOW_HEIGHT * ENEMY_WAITING_Y_RATIO)
        for i in range(WAITING_SLOTS_COUNT):
            x = waiting_start_x + i * (waiting_card_width + waiting_card_spacing)
            slot = CardSlot(x, enemy_waiting_y, waiting_card_width, waiting_card_height, "waiting")
            self.enemy_waiting_slots.append(slot)
        
        # === 弃牌堆（角落）===
        # 玩家弃牌堆（右下角）
        player_discard_x = int(WINDOW_WIDTH * PLAYER_DISCARD_X_RATIO)
        player_discard_y = int(WINDOW_HEIGHT * PLAYER_DISCARD_Y_RATIO)
        self.player_discard_slot = CardSlot(
            player_discard_x, player_discard_y, discard_width, discard_height, "discard"
        )
        
        # 敌人弃牌堆（右上角）
        enemy_discard_x = int(WINDOW_WIDTH * ENEMY_DISCARD_X_RATIO)
        enemy_discard_y = int(WINDOW_HEIGHT * ENEMY_DISCARD_Y_RATIO)
        self.enemy_discard_slot = CardSlot(
            enemy_discard_x, enemy_discard_y, discard_width, discard_height, "discard"
        )
    
    def create_buttons(self):
        """创建UI按钮"""
        button_width = int(150 * UI_SCALE)
        button_height = int(50 * UI_SCALE)
        margin = int(20 * UI_SCALE)
        
        # 返回按钮（左下角）
        self.back_button = Button(
            margin,
            int(WINDOW_HEIGHT * 0.95),
            button_width,
            button_height,
            "返回菜单",
            color=(100, 100, 100),
            hover_color=(130, 130, 130),
            font_size=24,
            on_click=lambda: self.switch_to("main_menu")
        )
        
        # 结束回合按钮（右侧中间）
        self.end_turn_button = Button(
            int(WINDOW_WIDTH * 0.85),
            int(WINDOW_HEIGHT * 0.5),
            button_width,
            button_height,
            "结束回合",
            color=(200, 100, 50),
            hover_color=(230, 130, 80),
            font_size=24,
            on_click=self.end_turn
        )
    
    def end_turn(self):
        """结束回合"""
        print("回合结束")
        # TODO: 实现回合逻辑

    """获取鼠标悬停的卡牌数据"""
    def get_hovered_card(self, mouse_pos):
        for card in self.player_battle_slots + self.enemy_battle_slots + self.player_waiting_slots + self.enemy_waiting_slots:
            if card.rect.collidepoint(mouse_pos):
                if hasattr(card, 'card_data'):
                    return card.card_data 
     
    """事件处理"""
    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")
        
        # 鼠标悬停检测
        if event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            
            # 检测所有槽位的悬停
            all_slots = (
                self.player_battle_slots + 
                self.enemy_battle_slots + 
                self.player_waiting_slots + 
                self.enemy_waiting_slots + 
                [self.player_discard_slot, self.enemy_discard_slot]
            )
            
            for slot in all_slots:
                slot.is_hovered = slot.rect.collidepoint(mouse_pos)
        
        # 按钮事件
        self.back_button.handle_event(event)
        self.end_turn_button.handle_event(event)
    
    def update(self, dt):
        """更新"""
        # 更新血量条动画
        self.player_health_bar.update(dt)
        self.enemy_health_bar.update(dt)
    
    def draw(self):
        """绘制场景"""
        # 绘制背景
        self.screen.blit(self.background, (0, 0))
        
        # 绘制场景标识（方便调试）
        self.draw_scene_labels()
        
        # 绘制血量条
        self.draw_health_bars()
        
        # 绘制所有槽位
        self.draw_slots()
        
        # 绘制按钮
        self.back_button.draw(self.screen)
        self.end_turn_button.draw(self.screen)
    
    def draw_scene_labels(self):
        """绘制场景标签（敌人区域/玩家区域提示）"""
        # 敌人区域标签
        enemy_label = self.title_font.render("敌方区域", True, (255, 100, 100))
        enemy_rect = enemy_label.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.15)))
        
        # 半透明背景
        label_bg = pygame.Surface((enemy_rect.width + 20, enemy_rect.height + 10), pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 120))
        self.screen.blit(label_bg, (enemy_rect.x - 10, enemy_rect.y - 5))
        self.screen.blit(enemy_label, enemy_rect)
        
        # 玩家区域标签
        player_label = self.title_font.render("我方区域", True, (100, 255, 100))
        player_rect = player_label.get_rect(center=(WINDOW_WIDTH // 2, int(WINDOW_HEIGHT * 0.73)))
        
        label_bg = pygame.Surface((player_rect.width + 20, player_rect.height + 10), pygame.SRCALPHA)
        label_bg.fill((0, 0, 0, 120))
        self.screen.blit(label_bg, (player_rect.x - 10, player_rect.y - 5))
        self.screen.blit(player_label, player_rect)
    
    def draw_health_bars(self):
        """绘制血量条"""
        # 玩家名称和血量条
        player_name = self.info_font.render("玩家", True, (200, 255, 200))
        player_name_pos = (self.player_health_bar.rect.x, 
                          self.player_health_bar.rect.y - int(25 * UI_SCALE))
        self.screen.blit(player_name, player_name_pos)
        self.player_health_bar.draw(self.screen)
        
        # 敌人名称和血量条
        enemy_name = self.info_font.render("敌人", True, (255, 200, 200))
        enemy_name_pos = (self.enemy_health_bar.rect.x, 
                         self.enemy_health_bar.rect.y - int(25 * UI_SCALE))
        self.screen.blit(enemy_name, enemy_name_pos)
        self.enemy_health_bar.draw(self.screen)
    
    def draw_slots(self):
        """绘制所有槽位"""
        # 战斗区标签
        battle_label_font = get_font(max(12, int(16 * UI_SCALE)))
        
        # 玩家战斗区
        for slot in self.player_battle_slots:
            slot.draw(self.screen)
        
        # 敌人战斗区
        for slot in self.enemy_battle_slots:
            slot.draw(self.screen)
        
        # 等候区标签和槽位
        waiting_label = battle_label_font.render("等候区", True, (200, 200, 150))
        
        # 玩家等候区
        if self.player_waiting_slots:
            label_x = self.player_waiting_slots[0].rect.x - int(80 * UI_SCALE)
            label_y = self.player_waiting_slots[0].rect.centery
            self.screen.blit(waiting_label, (label_x, label_y))
            
        for slot in self.player_waiting_slots:
            slot.draw(self.screen)
        
        # 敌人等候区
        if self.enemy_waiting_slots:
            label_x = self.enemy_waiting_slots[0].rect.x - int(80 * UI_SCALE)
            label_y = self.enemy_waiting_slots[0].rect.centery
            self.screen.blit(waiting_label, (label_x, label_y))
            
        for slot in self.enemy_waiting_slots:
            slot.draw(self.screen)
        
        # 弃牌堆标签和槽位
        discard_label = battle_label_font.render("弃牌堆", True, (200, 150, 150))
        
        # 玩家弃牌堆
        discard_x = self.player_discard_slot.rect.x
        discard_y = self.player_discard_slot.rect.y - int(25 * UI_SCALE)
        self.screen.blit(discard_label, (discard_x, discard_y))
        self.player_discard_slot.draw(self.screen)
        
        # 敌人弃牌堆
        discard_x = self.enemy_discard_slot.rect.x
        discard_y = self.enemy_discard_slot.rect.y - int(25 * UI_SCALE)
        self.screen.blit(discard_label, (discard_x, discard_y))
        self.enemy_discard_slot.draw(self.screen)