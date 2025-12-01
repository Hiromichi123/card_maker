"""全局配置文件"""
import ctypes
import pygame
import os
import sys

GAME_TITLE = "Card Battle Master Simulator v0.9.0"

# 窗口设置
WINDOW_WIDTH = 2880
WINDOW_HEIGHT = 1800
FPS = 90
BACKGROUND_COLOR = (30, 30, 50)
UI_SCALE = 1.0 # UI缩放因子

# 目录路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # 项目根目录
ASSETS_PATH = os.path.join(BASE_DIR, "assets") # 资源路径
CARD_BASE_PATH = os.path.join(ASSETS_PATH, "outputs") # 卡牌路径

# 默认颜色设置
COLORS = {
    "SSS": (255, 0, 0),        # level 0.0 红色
    "SS+": (255, 128, 114),    # level 0.5 粉色
    "SS": (255, 100, 20),      # level 1.0 橙色
    "S+": (160, 82, 45),       # level 1.5 赭色
    "S": (255, 215, 0),        # level 2.0 金色
    "A+": (75, 0, 130),        # level 2.5 深紫色
    "A": (138, 43, 226),       # level 3.0 紫色
    "B+": (0, 0, 160),         # level 3.5 深蓝色
    "B": (0, 191, 255),        # level 4.0 天蓝色
    "C+": (0, 128, 0),         # level 4.5 深绿色
    "C": (0, 255, 0),          # level 5.0 绿色
    "D": (128, 128, 128),      # level 6.0 灰色
    "#elna": (255, 20, 147),   # sp 玫红色
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
    global UI_SCALE, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_POSITION, WINDOW_WIDTH, WINDOW_HEIGHT
    
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

def set_ui_scale(scale_value):
    """手动设置UI缩放因子并刷新依赖的尺寸"""
    global UI_SCALE, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_POSITION
    clamped = max(0.5, min(1.5, float(scale_value)))
    UI_SCALE = clamped
    BUTTON_WIDTH = int(BASE_BUTTON_WIDTH * UI_SCALE)
    BUTTON_HEIGHT = int(BASE_BUTTON_HEIGHT * UI_SCALE)
    BUTTON_POSITION = (
        WINDOW_WIDTH // 2 - BUTTON_WIDTH // 2,
        int(WINDOW_HEIGHT * 0.85)
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
        print("使用默认字体，不支持中文显示")
        return pygame.font.Font(None, size)
    