import ctypes
import pygame

# 高DPI适配（仅Windows）
try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

# 窗口设置
WINDOW_WIDTH = 2880
WINDOW_HEIGHT = 1620
FPS = 60  # 提高上限，让pygame尽可能跑快
BACKGROUND_COLOR = (30, 30, 50)

# UI缩放因子
UI_SCALE = 1.0

# 卡牌设置
BASE_CARD_WIDTH = 360  #原720
BASE_CARD_HEIGHT = 540 #原1080
BASE_CARD_SPACING = 20
CARDS_PER_ROW = 5
TOTAL_CARDS = 10

# 实际使用的卡牌尺寸（运行时计算）
CARD_WIDTH = BASE_CARD_WIDTH
CARD_HEIGHT = BASE_CARD_HEIGHT
CARD_SPACING = BASE_CARD_SPACING

# 卡牌路径
CARD_BASE_PATH = "outputs"

# 抽卡概率配置 (总和为100)
CARD_PROBABILITIES = {
    "SSS": 0.5,
    "SS": 2,
    "S": 5,
    "A": 7.5,
    "B": 15,
    "C": 30,
    "D": 40
}

# 颜色设置
COLORS = {
    "SSS": (255, 0, 0),   # 红色
    "SS": (255, 100, 20), # 橙色
    "S": (255, 215, 0),   # 金色
    "A": (138, 43, 226),  # 紫色 
    "B": (0, 191, 255),   # 天蓝色
    "C": (0, 255, 0),     # 绿色
    "D": (205, 205, 205)  # 灰色
}

# 动画设置
ANIMATION_DURATION = 0.5  # 秒
CARD_FLIP_DURATION = 0.3  # 秒
STAGGER_DELAY = 0.1       # 每张卡片之间的延迟

# 按钮设置（基础值）
BASE_BUTTON_WIDTH = 300
BASE_BUTTON_HEIGHT = 90
BUTTON_COLOR = (100, 150, 255)
BUTTON_HOVER_COLOR = (130, 180, 255)
BUTTON_TEXT_COLOR = (255, 255, 255)

# 实际按钮尺寸（运行时计算）
BUTTON_WIDTH = BASE_BUTTON_WIDTH
BUTTON_HEIGHT = BASE_BUTTON_HEIGHT
BUTTON_POSITION = (0, 0)  # 运行时计算

def update_ui_scale(screen_width, screen_height):
    """根据屏幕尺寸更新UI缩放"""
    global UI_SCALE, CARD_WIDTH, CARD_HEIGHT, CARD_SPACING
    global BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_POSITION, WINDOW_WIDTH, WINDOW_HEIGHT
    
    WINDOW_WIDTH = screen_width
    WINDOW_HEIGHT = screen_height
    
    # 基于1920x1080计算缩放比例
    scale_x = screen_width / 1920
    scale_y = screen_height / 1080
    UI_SCALE = min(scale_x, scale_y)
    
    # 更新卡牌尺寸
    CARD_WIDTH = int(BASE_CARD_WIDTH * UI_SCALE)
    CARD_HEIGHT = int(BASE_CARD_HEIGHT * UI_SCALE)
    CARD_SPACING = int(BASE_CARD_SPACING * UI_SCALE)
    
    # 更新按钮尺寸
    BUTTON_WIDTH = int(BASE_BUTTON_WIDTH * UI_SCALE)
    BUTTON_HEIGHT = int(BASE_BUTTON_HEIGHT * UI_SCALE)
    BUTTON_POSITION = (
        WINDOW_WIDTH // 2 - BUTTON_WIDTH // 2,
        int(WINDOW_HEIGHT * 0.85)  # 屏幕85%的位置
    )