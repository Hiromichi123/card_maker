"""全局配置文件"""
import ctypes
import pygame
import os
import sys

# 窗口设置
WINDOW_WIDTH = 2880
WINDOW_HEIGHT = 1800
FPS = 90
BACKGROUND_COLOR = (30, 30, 50)
UI_SCALE = 1.0 # UI缩放因子

# 目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(BASE_DIR, "assets") # 资源路径
CARD_BASE_PATH = os.path.join(ASSETS_PATH, "outputs") # 卡牌路径

# 概率配置
CARD_PROBABILITIES = {
    "SSS": 0.5,  # SSS - 0.5%
    "SS": 2,     # SS - 2%
    "S": 4,      # S - 4%
    "A": 8.5,    # A - 8.5%
    "B": 15,     # B - 15%
    "C": 30,     # C - 30%
    "D": 40      # D - 20%
}

# 颜色设置（按等级）
COLORS = {
    "SSS": (255, 0, 0),    # 红色 - SSS
    "SS": (255, 100, 20),  # 橙色 - SS
    "S": (255, 215, 0),    # 金色 - S
    "A": (138, 43, 226),   # 紫色 - A
    "B": (0, 191, 255),    # 蓝色 - B
    "C": (0, 255, 0),      # 绿色 - C
    "D": (205, 205, 205)   # 灰色 - D
}

# 高DPI适配（仅Windows）
try:
    ctypes.windll.user32.SetProcessDPIAware()
except:
    pass

# 基础按钮设置
BASE_BUTTON_WIDTH = 300
BASE_BUTTON_HEIGHT = 90
BUTTON_COLOR = (100, 150, 255)
BUTTON_HOVER_COLOR = (130, 180, 255)
BUTTON_TEXT_COLOR = (255, 255, 255)
# 实际按钮
BUTTON_WIDTH = BASE_BUTTON_WIDTH
BUTTON_HEIGHT = BASE_BUTTON_HEIGHT
BUTTON_POSITION = (0, 0) 

def update_ui_scale(screen_width, screen_height):
    """根据屏幕尺寸更新UI缩放"""
    global UI_SCALE, CARD_WIDTH, CARD_HEIGHT, CARD_SPACING
    global BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_POSITION, WINDOW_WIDTH, WINDOW_HEIGHT
    
    WINDOW_WIDTH = screen_width
    WINDOW_HEIGHT = screen_height
    
    # 基于2880x1800计算缩放比例
    scale_x = screen_width / 2880
    scale_y = screen_height / 1800
    UI_SCALE = min(scale_x, scale_y)
    
    # 更新按钮尺寸
    BUTTON_WIDTH = int(BASE_BUTTON_WIDTH * UI_SCALE)
    BUTTON_HEIGHT = int(BASE_BUTTON_HEIGHT * UI_SCALE)
    BUTTON_POSITION = (
        WINDOW_WIDTH // 2 - BUTTON_WIDTH // 2,
        int(WINDOW_HEIGHT * 0.85)  # 屏幕85%的位置
    )

# ==================== 字体配置 ====================
def get_chinese_font():
    """获取系统中文字体"""
    if sys.platform == 'win32':
        # Windows系统
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',      # 微软雅黑
            'C:/Windows/Fonts/simhei.ttf',    # 黑体
            'C:/Windows/Fonts/simsun.ttc',    # 宋体
            'C:/Windows/Fonts/simkai.ttf',    # 楷体
        ]
    elif sys.platform == 'darwin':
        # macOS系统
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',           # 苹方
            '/System/Library/Fonts/STHeiti Light.ttc',      # 黑体-简
            '/Library/Fonts/Arial Unicode.ttf',
        ]
    else:
        # Linux系统
        font_paths = [
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
        ]
    
    # 查找可用字体
    for font_path in font_paths:
        if os.path.exists(font_path):
            print(f"使用中文字体: {font_path}")
            return font_path
    
    print("警告: 未找到中文字体，将使用默认字体")
    return None

# 中文字体路径
CHINESE_FONT_PATH = get_chinese_font()

def get_font(size):
    """获取指定大小的字体"""
    if CHINESE_FONT_PATH:
        return pygame.font.Font(CHINESE_FONT_PATH, size)
    else:
        return pygame.font.Font(None, size)