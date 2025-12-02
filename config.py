"""全局配置文件"""
import ctypes
import pygame
import os
import sys

GAME_TITLE = "Card Battle Master Simulator v1.0.0"

# 设计/窗口设置
BASE_DESIGN_WIDTH = 2880
BASE_DESIGN_HEIGHT = 1800
DESIGN_WIDTH = BASE_DESIGN_WIDTH
DESIGN_HEIGHT = BASE_DESIGN_HEIGHT
SCREEN_WIDTH = DESIGN_WIDTH  # 实际显示区域（物理屏幕）
SCREEN_HEIGHT = DESIGN_HEIGHT
WINDOW_WIDTH = DESIGN_WIDTH  # 渲染surface大小（按比例缩放后）
WINDOW_HEIGHT = DESIGN_HEIGHT
VIEW_DEST_X = 0  # 绘制到显示器时的目标偏移（黑边位置）
VIEW_DEST_Y = 0
VIEW_SRC_X = 0   # 当内容大于屏幕时的裁剪起点
VIEW_SRC_Y = 0
VISIBLE_WIDTH = DESIGN_WIDTH  # 实际可见区域大小
VISIBLE_HEIGHT = DESIGN_HEIGHT
AUTO_SCALE = 1.0  # 根据屏幕计算的基础缩放
USER_SCALE = 1.0  # 用户附加缩放（设置中）
UI_SCALE = 1.0    # 提供给 UI/字体的最终缩放
SCALE_POLICY = "cover"  # cover：一边贴满屏幕；fit：完整显示内容
SCALE_DIRTY = False  # 渲染surface需要重建时置为 True
FPS = 120 # 目标帧率
BACKGROUND_COLOR = (30, 30, 50)

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
    "#yoroikemomimi": (255, 20, 147), # sp 玫红色
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

def _apply_scale(scale_x, scale_y):
    """根据策略更新渲染区域/裁剪及UI尺寸"""
    global WINDOW_WIDTH, WINDOW_HEIGHT, VIEW_DEST_X, VIEW_DEST_Y
    global VIEW_SRC_X, VIEW_SRC_Y, VISIBLE_WIDTH, VISIBLE_HEIGHT
    global AUTO_SCALE, UI_SCALE, BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_POSITION

    if SCALE_POLICY == "fit":
        AUTO_SCALE = min(scale_x, scale_y)
    else:  # cover
        AUTO_SCALE = max(scale_x, scale_y)

    AUTO_SCALE = max(0.01, AUTO_SCALE)
    UI_SCALE = AUTO_SCALE * USER_SCALE

    content_width = max(1, int(round(DESIGN_WIDTH * AUTO_SCALE)))
    content_height = max(1, int(round(DESIGN_HEIGHT * AUTO_SCALE)))
    WINDOW_WIDTH = content_width
    WINDOW_HEIGHT = content_height

    if content_width <= SCREEN_WIDTH:
        VIEW_DEST_X = (SCREEN_WIDTH - content_width) // 2
        VIEW_SRC_X = 0
        VISIBLE_WIDTH = content_width
    else:
        VIEW_DEST_X = 0
        VIEW_SRC_X = (content_width - SCREEN_WIDTH) // 2
        VISIBLE_WIDTH = SCREEN_WIDTH

    if content_height <= SCREEN_HEIGHT:
        VIEW_DEST_Y = (SCREEN_HEIGHT - content_height) // 2
        VIEW_SRC_Y = 0
        VISIBLE_HEIGHT = content_height
    else:
        VIEW_DEST_Y = 0
        VIEW_SRC_Y = (content_height - SCREEN_HEIGHT) // 2
        VISIBLE_HEIGHT = SCREEN_HEIGHT

    BUTTON_WIDTH = int(BASE_BUTTON_WIDTH * UI_SCALE)
    BUTTON_HEIGHT = int(BASE_BUTTON_HEIGHT * UI_SCALE)
    BUTTON_POSITION = (
        WINDOW_WIDTH // 2 - BUTTON_WIDTH // 2,
        int(WINDOW_HEIGHT * 0.85)
    )

def update_ui_scale(screen_width, screen_height):
    """根据屏幕尺寸更新UI缩放"""
    global SCREEN_WIDTH, SCREEN_HEIGHT, SCALE_DIRTY

    SCREEN_WIDTH = max(1, int(screen_width))
    SCREEN_HEIGHT = max(1, int(screen_height))
    scale_x = SCREEN_WIDTH / DESIGN_WIDTH
    scale_y = SCREEN_HEIGHT / DESIGN_HEIGHT

    SCALE_DIRTY = True
    _apply_scale(scale_x, scale_y)

def set_ui_scale(scale_value):
    """手动设置UI缩放因子并刷新依赖的尺寸"""
    global USER_SCALE
    desired_ui = max(0.5, min(1.5, float(scale_value)))
    USER_SCALE = desired_ui / max(0.01, AUTO_SCALE)
    _apply_scale(SCREEN_WIDTH / DESIGN_WIDTH, SCREEN_HEIGHT / DESIGN_HEIGHT)

def set_scale_policy(policy):
    """切换缩放策略（fit / cover）"""
    global SCALE_POLICY, SCALE_DIRTY
    normalized = policy.lower()
    if normalized not in ("fit", "cover"):
        return
    SCALE_POLICY = normalized
    SCALE_DIRTY = True
    _apply_scale(SCREEN_WIDTH / DESIGN_WIDTH, SCREEN_HEIGHT / DESIGN_HEIGHT)

def initialize_design_resolution(screen_width, screen_height):
    """根据实际屏幕尺寸限制设计分辨率，避免额外的高分辨率渲染成本。"""
    screen_width = max(1, int(screen_width))
    screen_height = max(1, int(screen_height))
    target_width = min(BASE_DESIGN_WIDTH, screen_width)
    target_height = min(BASE_DESIGN_HEIGHT, screen_height)
    return set_design_resolution(target_width, target_height)

def set_design_resolution(width, height):
    """强制设置设计分辨率，返回是否发生变化。"""
    global DESIGN_WIDTH, DESIGN_HEIGHT, SCALE_DIRTY
    width = max(1, int(width))
    height = max(1, int(height))
    if width == DESIGN_WIDTH and height == DESIGN_HEIGHT:
        return False
    DESIGN_WIDTH = width
    DESIGN_HEIGHT = height
    SCALE_DIRTY = True
    return True

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
    