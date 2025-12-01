"""抽卡场景"""
import pygame
import config
from ui.button import Button
from ui.background import ParallaxBackground
from game.card_system import CardSystem
from scenes.base.base_scene import BaseScene
from utils.inventory import get_inventory
from utils.scene_payload import pop_payload
from scenes.gacha.gacha_probabilities import simple_prob, get_prob_table

def _card_width():
    return int(360 * config.UI_SCALE)

def _card_height():
    return int(540 * config.UI_SCALE)

class GachaScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        self.background = ParallaxBackground(config.WINDOW_WIDTH, config.WINDOW_HEIGHT, "bg/gacha_normal")
        self.dim_surface = pygame.Surface((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.SRCALPHA)
        self.dim_surface.fill((0, 0, 0, int(255 * 0.2)))
        self.card_system = CardSystem()
        self.inventory = get_inventory()
        
        # 字体
        self.title_font = config.get_font(max(32, int(64 * config.UI_SCALE)))
        self.info_font = config.get_font(max(12, int(24 * config.UI_SCALE)))
        
        # 当前卡池/概率信息
        self.current_pool_name = "常规卡池"
        self.current_pool_description = "标准概率"
        self.current_prob_label = "常规概率"
        self.active_prob_table = simple_prob
        self.pending_draw_count = 10
        self.auto_draw_delay = 0.8
        self.auto_draw_timer = 0.0
        self.auto_draw_started = False

        self._create_back_button() # 创建按钮

    def enter(self):
        super().enter()
        payload = pop_payload("gacha") or {}
        self._apply_payload(payload)

    def _apply_payload(self, payload):
        pool_name = payload.get("pool_name") or "常规卡池"
        self.current_pool_name = pool_name
        self.current_pool_description = payload.get("pool_description") or "标准概率"
        self.current_prob_label = payload.get("prob_label") or pool_name

        prob_source = payload.get("prob_table")
        if isinstance(prob_source, dict):
            self.active_prob_table = prob_source
        elif isinstance(prob_source, str):
            self.active_prob_table = get_prob_table(prob_source)
        else:
            self.active_prob_table = simple_prob

        draw_count = payload.get("draw_count", self.pending_draw_count)
        self.pending_draw_count = 10 if draw_count >= 10 else 1
        self.auto_draw_delay = payload.get("auto_delay", 0.8)
        self.auto_draw_timer = 0.0
        self.auto_draw_started = False

        bg_type = payload.get("bg_type") or "bg/gacha_normal"
        self.background = ParallaxBackground(config.WINDOW_WIDTH, config.WINDOW_HEIGHT, bg_type)

        # 重置卡牌展示
        self.card_system.cards = []
        self.card_system.is_animating = False
        self.card_system.animation_start_time = 0

    """==========核心方法=========="""
    def handle_event(self, event):
        super().handle_event(event)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("gacha_menu")
            elif event.key == pygame.K_SPACE:
                if self.trigger_draw():
                    self.auto_draw_started = True

        if event.type == pygame.MOUSEMOTION:
            self.background.update_mouse_position(event.pos)

        self.back_button.handle_event(event)

    def update(self, dt):
        self.background.update(dt)
        self.card_system.update(dt)

        if not self.auto_draw_started and self.pending_draw_count > 0:
            self.auto_draw_timer += dt
            if self.auto_draw_timer >= self.auto_draw_delay:
                if self.trigger_draw():
                    self.auto_draw_started = True

    def get_hovered_card(self, mouse_pos):
        """获取鼠标悬停的卡牌数据"""
        for card in self.card_system.cards:
            # 只检测已经翻开的卡牌（动画完成）
            if card.flip_progress >= 1.0:
                # 创建卡牌的矩形区域
                card_rect = pygame.Rect(
                    card.current_position[0],
                    card.current_position[1],
                    _card_width(),
                    _card_height()
                )
                
                # 检测鼠标是否在卡牌范围内
                if card_rect.collidepoint(mouse_pos):
                    return card.card_data
        return None

    """==========绘制场景=========="""
    def draw(self):
        self.background.draw(self.screen) # 背景
        self.screen.blit(self.dim_surface, (0, 0)) # 半透明遮罩
        self.draw_title() # 标题
        self.card_system.draw(self.screen) # 卡牌
        self.draw_probability_info() # 概率信息
        self.back_button.draw(self.screen) # 返回按钮

    def draw_title(self):
        """绘制标题"""
        title_y = int(config.WINDOW_HEIGHT * 0.04)
        title_text = self.title_font.render(self.current_pool_name, True, (255, 215, 0))
        title_rect = title_text.get_rect(center=(config.WINDOW_WIDTH // 2, title_y))
        
        shadow_offset = max(2, int(2 * config.UI_SCALE))
        shadow_text = self.title_font.render(self.current_pool_name, True, (0, 0, 0))
        shadow_rect = shadow_text.get_rect(center=(config.WINDOW_WIDTH // 2 + shadow_offset, 
                                                   title_y + shadow_offset))
        
        self.screen.blit(shadow_text, shadow_rect)
        self.screen.blit(title_text, title_rect)

        desc_text = self.info_font.render(self.current_pool_description, True, (210, 210, 210))
        desc_rect = desc_text.get_rect(center=(config.WINDOW_WIDTH // 2, title_y + int(40 * config.UI_SCALE)))
        self.screen.blit(desc_text, desc_rect)

    def draw_probability_info(self):
        """绘制概率信息"""
        prob_table = self.active_prob_table or simple_prob
        label_y = int(config.WINDOW_HEIGHT * 0.82)
        label_text = self.info_font.render(self.current_prob_label, True, (255, 255, 255))
        label_rect = label_text.get_rect(center=(config.WINDOW_WIDTH // 2, label_y))
        self.screen.blit(label_text, label_rect)

        y_offset = int(config.WINDOW_HEIGHT * 0.88)
        x_start = int(config.WINDOW_WIDTH * 0.05)
        x_spacing = int(config.WINDOW_WIDTH * 0.12)
        for idx, (rarity, probability) in enumerate(prob_table.items()):
            color = config.COLORS.get(rarity, (255, 255, 255))
            info_text = f"{rarity}({probability}%)"
            text = self.info_font.render(info_text, True, color)
            self.screen.blit(text, (x_start + idx * x_spacing, y_offset))

    """==========初始化=========="""
    def _create_back_button(self):
        button_width = int(360 * config.UI_SCALE)
        button_height = int(90 * config.UI_SCALE)
        button_x = (config.WINDOW_WIDTH - button_width) // 2
        button_y = int(config.WINDOW_HEIGHT * 0.92)

        self.back_button = Button(
            button_x,
            button_y,
            button_width,
            button_height,
            "返回卡池",
            color=(100, 150, 255),
            hover_color=(130, 180, 255),
            on_click=lambda: self.switch_to("gacha_menu")
        )

    """==========抽卡辅助=========="""
    def trigger_draw(self):
        if self.card_system.is_animating or self.pending_draw_count <= 0:
            return False

        if self.pending_draw_count >= 10:
            self.draw_ten_cards(prob=self.active_prob_table)
        else:
            self.draw_one_card(prob=self.active_prob_table)

        self.pending_draw_count = 0
        self.auto_draw_timer = 0.0
        return True

    def draw_one_card(self, prob=None):
        """单抽"""
        prob = prob or self.active_prob_table or simple_prob
        if not self.card_system.is_animating:
            drawn_card = self.card_system.draw_one_card(prob=prob)
            self.inventory.add_card(drawn_card.image_path, drawn_card.rarity)

    def draw_ten_cards(self, prob=None):
        """十连抽卡"""
        prob = prob or self.active_prob_table or simple_prob
        if not self.card_system.is_animating:
            drawn_cards = self.card_system.draw_ten_cards(prob=prob)
            cards_to_save = [(card.image_path, card.rarity) for card in drawn_cards]
            self.inventory.add_cards(cards_to_save)
