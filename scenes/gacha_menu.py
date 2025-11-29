"""抽卡菜单场景"""
import os
import pygame
import math
from config import *
from scenes.base_scene import BaseScene
from ui.background import ParallaxBackground
from ui.button import Button
from ui.scroll_view import DashboardView
from ui.tooltip import CardTooltip
from ui.system_ui import CurrencyLevelUI, DEFAULT_GOLD_ICON, DEFAULT_CRYSTAL_ICON
from utils.card_database import CardDatabase
from utils.scene_payload import set_payload
from game.gacha_probabilities import GACHA_POOLS, get_prob_table # 卡池配置

# 仪表盘属性
DASHBOARD_ALPHA = 50
DASHBOARD_ANGLE = 10
DASHBOARD_START_X = int(WINDOW_WIDTH * 0.02)
# 仪表盘位置参数
DASHBOARD_X = int(WINDOW_WIDTH * 0.05)
DASHBOARD_Y = int(WINDOW_HEIGHT * 0.05)
DASHBOARD_WIDTH = int(WINDOW_WIDTH * 0.18)
DASHBOARD_HEIGHT = int(WINDOW_HEIGHT * 0.9)
# 仪表盘按钮参数
DASHBOARD_BTN_HEIGHT = int(DASHBOARD_HEIGHT * 0.08)
DASHBOARD_BTN_WIDTH = int(DASHBOARD_WIDTH * 0.8)
DASHBOARD_BTN_SPACING = int(DASHBOARD_HEIGHT * 0.01)

# 呼吸效果参数
GLOW_SPEED = 5  # 呼吸速度
GLOW_BASE_COLOR = (255, 215, 180)  # 淡金色 RGB
GLOW_INTENSITY_R = 0  # 红色通道呼吸强度
GLOW_INTENSITY_G = 30  # 绿色通道呼吸强度
GLOW_INTENSITY_B = 30  # 蓝色通道呼吸强度

# 轮盘选中框参数
HIGHLIGHT_BOX_HEIGHT = int(90 * UI_SCALE)  # 选中框高度
HIGHLIGHT_GLOW_SPEED = 6  # 选中框呼吸速度
HIGHLIGHT_BORDER_WIDTH = 3  # 选中框边框宽度
HIGHLIGHT_BASE_ALPHA = 75  # 选中框基础透明度
HIGHLIGHT_ALPHA_RANGE = 25  # 选中框透明度呼吸范围

# 功能按钮位置参数
BUTTON_X_RATIO = 0.6  # 按钮 X 位置比例（相对窗口宽度）
BUTTON_Y_RATIO = 0.85  # 按钮 Y 位置比例
BUTTON_WIDTH = int(250 * UI_SCALE)  # 功能按钮宽度
BUTTON_HEIGHT = int(80 * UI_SCALE)  # 功能按钮高度

# 卡牌展示区域参数
SHOWCASE_X_RATIO = 0.45  # 展示区域 X 位置比例
SHOWCASE_Y_RATIO = 0.30   # 展示区域 Y 位置比例
SHOWCASE_WIDTH_RATIO = 0.4  # 展示区域宽度比例
SHOWCASE_HEIGHT_RATIO = 0.6  # 展示区域高度比例
CARD_WIDTH = int(300 * UI_SCALE)  # 展示卡宽度
CARD_HEIGHT = int(450 * UI_SCALE)  # 展示卡高度
CARD_HOVER_SCALE = 1.15  # 悬停时放大倍数
CARD_HOVER_ELEVATION = int(10 * UI_SCALE)  # 悬停时提升高度
CARD_SHADOW_OFFSET = int(5 * UI_SCALE)  # 阴影偏移

# 卡牌布局间距参数（相较与卡宽）
CARD_HORIZONTAL_SPACING_RATIO = 0.3  # 水平排列时卡牌间距比例
CARD_FAN_RADIUS_RATIO = 2.0  # 扇形排列时半径比例
CARD_FAN_CENTER_Y_OFFSET_RATIO = 0.28  # 扇形排列时中心点Y偏移比例
CARD_FAN_ANGLE_START = -90  # 扇形排列起始角度
CARD_FAN_ANGLE_RANGE = 180  # 扇形排列角度范围
CARD_DOUBLE_FAN_INNER_RATIO = 0.50  # 双层扇形内环半径比例
CARD_DOUBLE_FAN_OUTER_RATIO = 1.15  # 双层扇形外环半径比例
CARD_DOUBLE_FAN_RATE = 0.3  # 双层扇形前后层卡牌比例，50%表示均分
CARD_GRID_OFFSET_X_RATIO = 0.056  # 网格排列随机偏移X比例
CARD_GRID_OFFSET_Y_RATIO = 0.042  # 网格排列随机偏移Y比例

# 抽卡消耗
SINGLE_GOLD_COST = 500
TEN_GOLD_COST = 4500
SINGLE_CRYSTAL_COST = 30
TEN_CRYSTAL_COST = 270
NOTICE_DURATION = 2.0

# 字体大小
TITLE_FONT_SIZE = int(80 * UI_SCALE) # 主标题字体大小
DESC_FONT_SIZE = int(40 * UI_SCALE) # 描述字体大小
POOL_NAME_FONT_SIZE = int(45 * UI_SCALE) # 卡池名称字体大小

class GachaMenuScene(BaseScene):
    def __init__(self, screen):
        super().__init__(screen)
        
        self.blink_timer = 0  # 金色闪烁计时器
        self.glow_intensity = 0  # 发光强度（0-1）
        self.is_snapping = False  # 是否正在吸附对齐
        self.card_image_cache = {} # 图片缓存

        self.selected_pool_index = 0  # 选中卡池索引
        self.background = self._create_background_for_pool(self.selected_pool_index)
        
        # 字体
        self.title_font = get_font(TITLE_FONT_SIZE)
        self.desc_font = get_font(DESC_FONT_SIZE)
        self.pool_name_font = get_font(POOL_NAME_FONT_SIZE)
        self.notice_font = get_font(int(32 * UI_SCALE))
        self.cost_font = get_font(int(34 * UI_SCALE))
        self.cost_icon_size = int(32 * UI_SCALE)
        self.cost_icons = {
            "gold": self._load_cost_icon(DEFAULT_GOLD_ICON),
            "crystal": self._load_cost_icon(DEFAULT_CRYSTAL_ICON)
        }
        
        # 按钮配置
        self.button_height = int(120 * UI_SCALE)
        self.button_spacing = int(20 * UI_SCALE)

        # 创建仪表盘视图 添加顶部和底部填充
        top_padding = DASHBOARD_HEIGHT // 2
        bottom_padding = DASHBOARD_HEIGHT // 2
        buttons_height = len(GACHA_POOLS) * (self.button_height + self.button_spacing)
        content_height = top_padding + buttons_height + bottom_padding
        self.dashboard_view = DashboardView(
            DASHBOARD_X, DASHBOARD_Y,
            DASHBOARD_WIDTH, DASHBOARD_HEIGHT,
            content_height,
            bg_alpha=DASHBOARD_ALPHA,
            tilt_angle=DASHBOARD_ANGLE,
            highlight_center=True,
            highlight_box_height=HIGHLIGHT_BOX_HEIGHT,
            highlight_glow_speed=HIGHLIGHT_GLOW_SPEED,
            highlight_border_width=HIGHLIGHT_BORDER_WIDTH,
            highlight_base_alpha=HIGHLIGHT_BASE_ALPHA,
            highlight_alpha_range=HIGHLIGHT_ALPHA_RANGE
        )

        self._create_buttons()
        
        # 卡池选项按钮列表
        self.dashboard_buttons = []
        self._create_dashboard_buttons()
        
        # 卡牌展示相关
        self.card_db = CardDatabase()
        self.showcase_cards = []  # 当前展示的卡牌数据
        self.card_rects = []  # 卡牌矩形位置
        self.hovered_card_index = -1  # 鼠标悬停的卡牌索引
        self.card_tooltip = CardTooltip()  # 卡牌提示框
        self._update_showcase_cards()

        # 货币和等级 UI
        self.currency_ui = CurrencyLevelUI()
        self.currency_ui.load_state()
        self.currency_notice = ""
        self.currency_notice_timer = 0.0

    def _create_background_for_pool(self, pool_index):
        """根据卡池索引创建对应的视差背景"""
        if 0 <= pool_index < len(GACHA_POOLS):
            bg_type = GACHA_POOLS[pool_index]["bg_type"]
        return ParallaxBackground(WINDOW_WIDTH, WINDOW_HEIGHT, bg_type)

    def _load_cost_icon(self, path):
        size = self.cost_icon_size
        try:
            if path and os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, (size, size))
        except Exception:
            pass

        # fallback simple circle
        placeholder = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(placeholder, (255, 215, 0, 220), (size // 2, size // 2), size // 2)
        return placeholder

    def _current_pool(self):
        if 0 <= self.selected_pool_index < len(GACHA_POOLS):
            return GACHA_POOLS[self.selected_pool_index]
        return GACHA_POOLS[0]

    def _get_currency_profile(self, pool=None):
        pool = pool or self._current_pool()
        currency = pool.get("currency", "gold")
        single_cost = pool.get("single_cost")
        ten_cost = pool.get("ten_cost")

        if currency == "crystal":
            return {
                "currency": "crystal",
                "label": "水晶",
                "suffix": "水晶",
                "single_cost": single_cost if single_cost is not None else SINGLE_CRYSTAL_COST,
                "ten_cost": ten_cost if ten_cost is not None else TEN_CRYSTAL_COST,
                "balance": self.currency_ui.get_crystals(),
                "has_fn": self.currency_ui.has_enough_crystals,
                "spend_fn": self.currency_ui.spend_crystals,
                "icon": self.cost_icons.get("crystal")
            }

        return {
            "currency": "gold",
            "label": "金币",
            "suffix": "G",
            "single_cost": single_cost if single_cost is not None else SINGLE_GOLD_COST,
            "ten_cost": ten_cost if ten_cost is not None else TEN_GOLD_COST,
            "balance": self.currency_ui.get_golds(),
            "has_fn": self.currency_ui.has_enough_golds,
            "spend_fn": self.currency_ui.spend_golds,
            "icon": self.cost_icons.get("gold")
        }

    def _get_blink_color(self):
        """获取金色闪烁颜色"""
        base_r, base_g, base_b = GLOW_BASE_COLOR
        glow_r = int(base_r + GLOW_INTENSITY_R * self.glow_intensity)
        glow_g = int(base_g + GLOW_INTENSITY_G * self.glow_intensity)
        glow_b = int(base_b + GLOW_INTENSITY_B * self.glow_intensity)
        return (glow_r, glow_g, glow_b)
    
    def _create_dashboard_buttons(self):
        """创建卡池选项按钮"""
        self.dashboard_buttons = []
        
        top_padding = self.dashboard_view.height // 2 - self.button_height // 2
        start_y = top_padding

        for i, pool in enumerate(GACHA_POOLS):
            btn_y = start_y + i * (self.button_height + self.button_spacing)
            
            if i == self.selected_pool_index:
                color = self._get_blink_color()
            else:
                color = (60, 80, 120)
            
            btn = Button(
                DASHBOARD_START_X, btn_y,
                DASHBOARD_BTN_WIDTH, self.button_height,
                pool["name"],
                color=color,
                hover_color=(80, 120, 180),
                text_color=(255, 255, 255),
                font_size=28,
                on_click=None
            )
            self.dashboard_buttons.append(btn)
    
    def _create_buttons(self):
        """创建右侧功能按钮"""
        button_x = int(WINDOW_WIDTH * BUTTON_X_RATIO)
        button_y = int(WINDOW_HEIGHT * BUTTON_Y_RATIO)
        spacing = self.button_spacing

        # 十连抽按钮
        self.ten_draw_button = Button(
            button_x, button_y,
            BUTTON_WIDTH, BUTTON_HEIGHT,
            f"十 连 抽",
            color=(255, 170, 80),
            hover_color=(255, 200, 120),
            on_click=lambda: self._attempt_draw(10)
        )

        # 单抽按钮
        self.single_draw_button = Button(
            button_x - BUTTON_WIDTH - spacing, button_y,
            BUTTON_WIDTH, BUTTON_HEIGHT,
            f"单 抽",
            color=(255, 170, 80),
            hover_color=(255, 200, 120),
            on_click=lambda: self._attempt_draw(1)
        )

        # 返回主菜单按钮
        self.back_button = Button(
            button_x + BUTTON_WIDTH + spacing, button_y,
            BUTTON_WIDTH, BUTTON_HEIGHT,
            "返回主菜单",
            color=(100, 150, 255), hover_color=(130, 180, 255),
            on_click=lambda: self.switch_to("main_menu")
        )

    def _update_pool_button_colors(self):
        """更新卡池按钮颜色以反映选中状态"""
        for i, btn in enumerate(self.dashboard_buttons):
            if i == self.selected_pool_index:
                btn.color = self._get_blink_color()
            else:
                btn.color = (60, 80, 120)
    
    def _update_showcase_cards(self):
        """更新当前卡池的展示卡牌"""
        if 0 <= self.selected_pool_index < len(GACHA_POOLS):
            pool = GACHA_POOLS[self.selected_pool_index]
            card_ids = pool.get("showcase_cards", [])
            self.showcase_cards = []
            
            for card_id in card_ids:
                # 解析格式："等级_编号"，如 "A_001"
                if "_" in card_id:
                    parts = card_id.split("_")
                    if len(parts) == 2:
                        level, number = parts
                        # 从指定等级目录加载卡牌
                        card_data = self.card_db.get_card_by_level(level, number)
                        if card_data:
                            self.showcase_cards.append(card_data)
                else:
                    # 兼容旧格式（纯数字ID）
                    card_data = self.card_db.get_card(card_id)
                    if card_data:
                        self.showcase_cards.append(card_data)
            
            self._layout_showcase_cards()
    
    def _layout_showcase_cards(self):
        """卡牌布局"""
        self.card_rects = []
        if not self.showcase_cards:
            return
        
        num_cards = len(self.showcase_cards)
        
        # 少于4张时才使用偏移
        if num_cards < 4:
            offset_x = int(WINDOW_WIDTH * -0.1)
            offset_y = int(WINDOW_HEIGHT * -0.1)
        else:
            offset_x = 0
            offset_y = 0
        
        showcase_x = int(WINDOW_WIDTH * SHOWCASE_X_RATIO) + offset_x
        showcase_y = int(WINDOW_HEIGHT * SHOWCASE_Y_RATIO) + offset_y
        showcase_width = int(WINDOW_WIDTH * SHOWCASE_WIDTH_RATIO)
        showcase_height = int(WINDOW_HEIGHT * SHOWCASE_HEIGHT_RATIO)
        
        card_width = CARD_WIDTH
        card_height = CARD_HEIGHT
        
        if num_cards < 4:
            # 少量水平排列 - 使用放大尺寸
            enlarged_width = int(360 * UI_SCALE)
            enlarged_height = int(540 * UI_SCALE)
            x_spacing = int(enlarged_width * CARD_HORIZONTAL_SPACING_RATIO)  # 等比放大间距
            total_width = num_cards * enlarged_width + (num_cards - 1) * x_spacing if num_cards > 1 else enlarged_width
            start_x = showcase_x + (showcase_width - total_width) // 2
            y = showcase_y + (showcase_height - enlarged_height) // 2
            
            for i, card in enumerate(self.showcase_cards):
                x = start_x + i * (enlarged_width + x_spacing)
                self.card_rects.append(pygame.Rect(x, y, enlarged_width, enlarged_height))
        
        elif num_cards <= 7:
            # 中量扇形排列
            center_x = showcase_x + showcase_width // 2
            center_y = showcase_y + showcase_height // 2 + int(card_width * CARD_FAN_CENTER_Y_OFFSET_RATIO)
            radius = int(card_width * CARD_FAN_RADIUS_RATIO)
            angle_start = CARD_FAN_ANGLE_START
            angle_range = CARD_FAN_ANGLE_RANGE
            
            for i, card in enumerate(self.showcase_cards):
                angle = math.radians(angle_start + (angle_range / (num_cards - 1)) * i if num_cards > 1 else 0)
                x = int(center_x + radius * math.sin(angle) - card_width // 2)
                y = int(center_y - radius * math.cos(angle) - card_height // 2)
                self.card_rects.append(pygame.Rect(x, y, card_width, card_height))
        
        else: # 大量双层扇形排列
            center_x = showcase_x + showcase_width // 2
            center_y = showcase_y + showcase_height // 2 + int(card_width * CARD_FAN_CENTER_Y_OFFSET_RATIO)
            
            # 使用全局比例参数分配卡牌到前后层
            first_layer_count = int(num_cards * CARD_DOUBLE_FAN_RATE)  # 前层（内环）卡牌数量
            second_layer_count = num_cards - first_layer_count  # 后层（外环）卡牌数量
            
            # 前层较小半径
            radius_front = int(card_width * CARD_FAN_RADIUS_RATIO * CARD_DOUBLE_FAN_INNER_RATIO)
            # 后层较大半径
            radius_back = int(card_width * CARD_FAN_RADIUS_RATIO * CARD_DOUBLE_FAN_OUTER_RATIO)
            angle_start = CARD_FAN_ANGLE_START
            angle_range = CARD_FAN_ANGLE_RANGE
            
            # 先绘制后层（外环，较远的卡牌）
            for i in range(second_layer_count):
                angle = math.radians(angle_start + (angle_range / (second_layer_count - 1)) * i if second_layer_count > 1 else 0)
                x = int(center_x + radius_back * math.sin(angle) - card_width // 2)
                y = int(center_y - radius_back * math.cos(angle) - card_height // 2)
                self.card_rects.append(pygame.Rect(x, y, card_width, card_height))
            # 再绘制前层（内环，较近的卡牌）
            for i in range(first_layer_count):
                angle = math.radians(angle_start + (angle_range / (first_layer_count - 1)) * i if first_layer_count > 1 else 0)
                x = int(center_x + radius_front * math.sin(angle) - card_width // 2)
                y = int(center_y - radius_front * math.cos(angle) - card_height // 2)
                self.card_rects.append(pygame.Rect(x, y, card_width, card_height))
    
    def _attempt_draw(self, draw_count: int):
        pool = self._current_pool()
        profile = self._get_currency_profile(pool)
        cost = profile["ten_cost"] if draw_count >= 10 else profile["single_cost"]

        if not profile["has_fn"](cost):
            self._set_currency_notice(f"{profile['label']}不足，无法抽卡")
            return

        if not profile["spend_fn"](cost):
            self._set_currency_notice("抽卡失败，请稍后重试")
            return

        self._set_currency_notice(f"已消耗 {cost}{profile['suffix']}")
        self._launch_gacha_scene(pool, draw_count)

    def _launch_gacha_scene(self, pool, draw_count: int):
        payload = self._build_pool_payload(pool, draw_count)
        set_payload("gacha", payload)
        self.switch_to("gacha")

    def _build_pool_payload(self, pool, draw_count: int) -> dict:
        prob_source = pool.get("prob_table")
        if isinstance(prob_source, dict):
            prob_table = prob_source
        else:
            prob_table = get_prob_table(prob_source)

        normalized_draw = 10 if draw_count >= 10 else 1
        auto_delay = 0.65 if normalized_draw == 1 else 0.85

        return {
            "pool_id": pool.get("id") or f"pool_{self.selected_pool_index}",
            "pool_name": pool.get("name"),
            "pool_description": pool.get("description"),
            "prob_label": pool.get("prob_label"),
            "prob_table": prob_table,
            "bg_type": pool.get("bg_type"),
            "draw_count": normalized_draw,
            "auto_delay": auto_delay,
        }

    def _set_currency_notice(self, text: str):
        self.currency_notice = text
        self.currency_notice_timer = NOTICE_DURATION
    
    def handle_event(self, event):
        """处理事件"""
        super().handle_event(event)
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_to("main_menu")
            elif event.key == pygame.K_UP:
                # 向上滚动一个按钮的距离
                self.dashboard_view.scroll_y -= (self.button_height + self. button_spacing)
                self. dashboard_view.scroll_y = max(0, self.dashboard_view.scroll_y)
                self. is_snapping = False
            elif event.key == pygame.K_DOWN:
                # 向下滚动一个按钮的距离
                self.dashboard_view.scroll_y += (self.button_height + self.button_spacing)
                self.dashboard_view.scroll_y = min(self.dashboard_view.scroll_y, self.dashboard_view.max_scroll)
                self.is_snapping = False
        
        # 鼠标滚轮控制滚动
        elif event.type == pygame.MOUSEWHEEL:
            scroll_amount = (self.button_height + self.button_spacing)
            if event.y > 0:  # 向上滚
                self.dashboard_view. scroll_y -= scroll_amount
            else:  # 向下滚
                self.dashboard_view.scroll_y += scroll_amount
            
            self.dashboard_view.scroll_y = max(0, min(self.dashboard_view.scroll_y, self.dashboard_view.max_scroll))
            self.is_snapping = False
            return
        
        # 处理拖拽滚动
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.dashboard_view.rect. collidepoint(mouse_pos):
                self.dashboard_view.is_dragging = True
                self.dashboard_view.drag_start_y = mouse_pos[1]
                self.dashboard_view.drag_start_scroll = self.dashboard_view.scroll_y
                self.is_snapping = False
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dashboard_view.is_dragging:
                self. dashboard_view.is_dragging = False
                self.is_snapping = True  # 开始吸附
        
        elif event.type == pygame.MOUSEMOTION:
            # 更新视差背景
            self.background.update_mouse_position(event.pos)
            
            # 检测卡牌悬停
            mouse_pos = event.pos
            self.hovered_card_index = -1
            for i, rect in enumerate(self.card_rects):
                if rect.collidepoint(mouse_pos):
                    self.hovered_card_index = i
                    if i < len(self.showcase_cards):
                        self.card_tooltip.show(self.showcase_cards[i], mouse_pos)
                    break
            else:
                self.card_tooltip.hide()
            
            # 处理拖拽
            if self. dashboard_view.is_dragging:
                mouse_pos = event.pos
                delta_y = mouse_pos[1] - self.dashboard_view. drag_start_y
                self.dashboard_view.scroll_y = self.dashboard_view.drag_start_scroll - delta_y
                self.dashboard_view.scroll_y = max(0, min(self.dashboard_view.scroll_y, self.dashboard_view.max_scroll))
        
        # 功能按钮事件
        self.single_draw_button.handle_event(event)
        self.ten_draw_button.handle_event(event)
        self.back_button.handle_event(event)
    
    def update(self, dt):
        self.blink_timer += dt
        # 更新发光强度
        self.glow_intensity = (math.sin(self.blink_timer * GLOW_SPEED) + 1) / 2  # 0 to 1
        self.background.update(dt)
        
        # 更新仪表盘视图的呼吸动画
        self.dashboard_view.update(dt)
        
        # 吸附效果：滚动停止后自动对齐到按钮
        if self.is_snapping and not self.dashboard_view.is_dragging:
            item_size = self.button_height + self.button_spacing
            top_padding = self.dashboard_view.height // 2
            
            # 计算当前最接近中心的按钮索引
            center_y = self.dashboard_view.scroll_y + self.dashboard_view.height // 2
            adjusted_center_y = center_y - top_padding
            target_index = round(adjusted_center_y / item_size)
            
            # 限制索引范围
            target_index = max(0, min(target_index, len(GACHA_POOLS) - 1))
            
            # 计算目标滚动位置
            target_scroll = top_padding + target_index * item_size - self.dashboard_view.height // 2
            
            # 限制滚动范围
            target_scroll = max(0, min(target_scroll, self. dashboard_view.max_scroll))
            
            # 如果偏离目标位置，平滑吸附
            if abs(self.dashboard_view.scroll_y - target_scroll) > 1:
                self.dashboard_view.scroll_y += (target_scroll - self.dashboard_view.scroll_y) * 0.2
            else:
                self.dashboard_view.scroll_y = target_scroll
                self.is_snapping = False
        
        # 根据当前滚动位置，自动检测中心项
        center_index = self.dashboard_view.get_center_item_index(
            self.button_height, self.button_spacing
        )
        
        # 如果中心项改变，更新选中状态
        if 0 <= center_index < len(GACHA_POOLS) and center_index != self.selected_pool_index:
            self.selected_pool_index = center_index
            self.background = self._create_background_for_pool(center_index)
            self._update_pool_button_colors()
            self._update_showcase_cards()  # 更新展示卡牌
        
        # 更新选中按钮的闪烁颜色
        if 0 <= self.selected_pool_index < len(self.dashboard_buttons):
            self.dashboard_buttons[self.selected_pool_index].color = self._get_blink_color()

        if self.currency_notice_timer > 0:
            self.currency_notice_timer -= dt
            if self.currency_notice_timer <= 0:
                self.currency_notice_timer = 0.0
                self.currency_notice = ""

    def draw(self):
        self.background.draw(self.screen)
        self._draw_title()
        self._draw_pool_list()
        
        # 绘制卡牌展示
        self._draw_showcase_cards()
        
        pool = self._current_pool()
        currency_profile = self._get_currency_profile(pool) # 获取当前卡池的货币配置
        single_affordable = currency_profile["balance"] >= currency_profile["single_cost"]
        ten_affordable = currency_profile["balance"] >= currency_profile["ten_cost"]
        self._draw_cost_label(self.single_draw_button, currency_profile["single_cost"], single_affordable, currency_profile)
        self._draw_cost_label(self.ten_draw_button, currency_profile["ten_cost"], ten_affordable, currency_profile)

        # 绘制功能按钮
        self.single_draw_button.draw(self.screen)
        self.ten_draw_button.draw(self.screen)
        self.back_button.draw(self.screen)

        if self.currency_notice:
            notice_text = self.notice_font.render(self.currency_notice, True, (255, 240, 180))
            notice_rect = notice_text.get_rect()
            notice_rect.midtop = (
                self.ten_draw_button.rect.centerx,
                self.ten_draw_button.rect.bottom + int(10 * UI_SCALE)
            )

            bg_rect = pygame.Rect(
                notice_rect.x - 12,
                notice_rect.y - 6,
                notice_rect.width + 24,
                notice_rect.height + 12
            )
            bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(bg_surface, (20, 20, 20, 180), bg_surface.get_rect(), border_radius=12)
            self.screen.blit(bg_surface, bg_rect.topleft)
            self.screen.blit(notice_text, notice_rect)

        self.currency_ui.draw(self.screen, (WINDOW_WIDTH*0.75, WINDOW_HEIGHT*0.03)) # 货币和等级 UI
        
        # 绘制卡牌提示框（最后绘制，在最上层）
        if self.card_tooltip.visible:
            self.card_tooltip.draw(self.screen)
    
    def _draw_title(self):
        """绘制标题：显示当前选中卡池的名称和描述"""
        if 0 <= self.selected_pool_index < len(GACHA_POOLS):
            pool = GACHA_POOLS[self.selected_pool_index]
            
            # 主标题：卡池名称（使用闪烁颜色）
            title_y = int(WINDOW_HEIGHT * 0.06)
            blink_color = self._get_blink_color()
            title_text = self.title_font.render(pool["name"], True, blink_color)
            title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, title_y))
            
            # 阴影
            shadow_offset = max(2, int(2 * UI_SCALE))
            shadow_text = self.title_font.render(pool["name"], True, (0, 0, 0))
            shadow_rect = shadow_text.get_rect(center=(
                WINDOW_WIDTH // 2 + shadow_offset,
                title_y + shadow_offset
            ))
            
            self.screen.blit(shadow_text, shadow_rect)
            self.screen.blit(title_text, title_rect)
            
            # 副标题：卡池描述
            subtitle_y = title_y + int(70 * UI_SCALE)
            subtitle_text = self.desc_font.render(pool["description"], True, (128, 0, 128))
            subtitle_rect = subtitle_text.get_rect(center=(WINDOW_WIDTH // 2, subtitle_y))
            self.screen.blit(subtitle_text, subtitle_rect)
    
    def _draw_pool_list(self):
        """绘制卡池列表"""
        surface, scroll_offset = self.dashboard_view.begin_draw()
        
        for i, btn in enumerate(self.dashboard_buttons):
            original_y = btn. rect.y
            btn.rect.y = original_y + scroll_offset
            btn.text_rect.centery = btn.rect.centery
            
            # 只绘制可见的按钮
            if -self.button_height < btn.rect.y < self. dashboard_view.height + self. button_height:
                btn. draw(surface)
                
                # 如果是高亮选中的按钮，在上层覆盖红色文字
                if i == self.selected_pool_index:
                    highlight_font = get_font(int(40 * UI_SCALE))
                    highlight_text = highlight_font.render(GACHA_POOLS[i]["name"], True, (255, 25, 25))
                    highlight_rect = highlight_text.get_rect(center=(btn.rect.centerx, btn.rect.centery))
                    surface.blit(highlight_text, highlight_rect)
            
            btn.rect.y = original_y
            btn. text_rect.centery = btn.rect.centery
        
        self.dashboard_view.end_draw(self.screen)
    
    def _draw_showcase_cards(self):
        """绘制展示卡牌"""
        for i, (card, rect) in enumerate(zip(self.showcase_cards, self.card_rects)):
            is_hovered = (i == self.hovered_card_index) # 判断是否悬停
            
            # 悬停时放大和提升
            if is_hovered:
                scale = CARD_HOVER_SCALE
                elevation = CARD_HOVER_ELEVATION
                scaled_width = int(rect.width * scale)
                scaled_height = int(rect.height * scale)
                draw_rect = pygame.Rect(
                    rect.centerx - scaled_width // 2,
                    rect.centery - scaled_height // 2 - elevation,
                    scaled_width,
                    scaled_height
                )
            else:
                draw_rect = rect
            
            # 绘制卡牌阴影
            shadow_rect = draw_rect.copy()
            shadow_rect.x += CARD_SHADOW_OFFSET
            shadow_rect.y += CARD_SHADOW_OFFSET
            shadow_surface = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            shadow_surface.fill((0, 0, 0, 100 if not is_hovered else 150))
            self.screen.blit(shadow_surface, shadow_rect)
            
            # 加载并绘制卡牌图片
            try:
                if hasattr(card, 'image_path') and card.image_path:
                    # 使用缓存避免重复加载和缩放
                    cache_key = (card.image_path, draw_rect.width, draw_rect.height)
                    if cache_key not in self.card_image_cache:
                        # 首次加载时缓存
                        original_image = pygame.image.load(card.image_path)
                        scaled_image = pygame.transform.smoothscale(original_image, (draw_rect.width, draw_rect.height))
                        self.card_image_cache[cache_key] = scaled_image
                    
                    card_image = self.card_image_cache[cache_key]
                    
                    # 悬停发光效果
                    if is_hovered:
                        rarity_color = COLORS.get(card.rarity, (200, 200, 200))
                        glow_surface = pygame.Surface((draw_rect.width + 20, draw_rect.height + 20), pygame.SRCALPHA)
                        for j in range(3):
                            alpha = 80 - j * 25
                            glow_color = (*rarity_color, alpha)
                            offset = (j + 1) * 6
                            glow_rect = pygame.Rect(offset, offset, draw_rect.width + 20 - offset * 2, draw_rect.height + 20 - offset * 2)
                            pygame.draw.rect(glow_surface, glow_color, glow_rect, border_radius=10)
                        self.screen.blit(glow_surface, (draw_rect.x - 10, draw_rect.y - 10))
                    
                    # 绘制卡牌图片
                    self.screen.blit(card_image, draw_rect)
                else:
                    # 如果没有图片路径，绘制占位符
                    placeholder = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
                    rarity_color = COLORS.get(card.rarity, (100, 100, 100))
                    pygame.draw.rect(placeholder, rarity_color, placeholder.get_rect(), border_radius=8)
                    inner_rect = pygame.Rect(3, 3, draw_rect.width - 6, draw_rect.height - 6)
                    pygame.draw.rect(placeholder, (40, 40, 50, 230), inner_rect, border_radius=6)
                    
                    # 显示卡牌名称作为占位
                    name_font = get_font(max(14, int(20 * UI_SCALE)))
                    name_text = name_font.render(card.name[:6], True, (255, 255, 255))
                    name_rect = name_text.get_rect(center=(draw_rect.width // 2, draw_rect.height // 2))
                    placeholder.blit(name_text, name_rect)
                    
                    self.screen.blit(placeholder, draw_rect)
                    
            except Exception as e:
                # 图片加载失败，绘制错误占位符
                error_surface = pygame.Surface((draw_rect.width, draw_rect.height), pygame.SRCALPHA)
                pygame.draw.rect(error_surface, (100, 100, 100), error_surface.get_rect(), border_radius=8)
                error_font = get_font(max(12, int(16 * UI_SCALE)))
                error_text = error_font.render("加载失败", True, (255, 100, 100))
                error_rect = error_text.get_rect(center=(draw_rect.width // 2, draw_rect.height // 2))
                error_surface.blit(error_text, error_rect)
                self.screen.blit(error_surface, draw_rect)

    def _draw_cost_label(self, button, cost, affordable, currency_profile):
        if cost <= 0:
            return
        color = (255, 215, 0) if affordable else (255, 80, 80)
        text_surface = self.cost_font.render(str(cost), True, color)
        icon = currency_profile.get("icon")
        gap = int(8 * UI_SCALE) if icon else 0
        icon_width = icon.get_width() if icon else 0
        total_width = text_surface.get_width() + icon_width + gap
        base_x = button.rect.centerx - total_width // 2
        base_y = button.rect.top - text_surface.get_height() - int(12 * UI_SCALE)
        self.screen.blit(text_surface, (base_x, base_y))
        if icon:
            icon_y = base_y + (text_surface.get_height() - icon.get_height()) // 2
            icon_x = base_x + text_surface.get_width() + gap
            self.screen.blit(icon, (icon_x, icon_y))
