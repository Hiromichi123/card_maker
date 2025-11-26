"""货币和等级系统 UI组件"""
# 使用示例:
#     nit中创建实例
#     ui = CurrencyLevelUI()
#     ui.load_state()

#     ui.draw(screen, (10,10)) # 在draw循环中调用

#     结算时调用:
#     result = ui.award_victory(golds=100, xp=50, crystals=5)
#     ui.add_golds(50)
#     ui.add_xp(120)
#     ui.save_state()

import os
import json
import math
import pygame
from config import get_font, UI_SCALE

DEFAULT_DATA_DIR = "data"
DEFAULT_DATA_FILE = os.path.join(DEFAULT_DATA_DIR, "profile.json") # 数据文件路径
DEFAULT_AVATAR = "assets/ui/avatar.jpg" # 头像图片路径
DEFAULT_GOLD_ICON = "assets/ui/gold.png" # 金币图标路径
DEFAULT_CRYSTAL_ICON = "assets/ui/crystal.png" # 水晶图标路径

# XP成长参数
base_xp = 100           # 升级基础经验值
xp_multiplier = 1.2     # 经验值增长倍率

avatar_size = int(128 * UI_SCALE) # 头像大小
icon_size = int(56 * UI_SCALE)   # 图标大小
xp_bar_size = (int(360 * UI_SCALE), int(32 * UI_SCALE)) # 经验条尺寸
padding = int(16 * UI_SCALE) # 内边距
bg_color = (20, 20, 20, 200) # 背景颜色 (RGBA)

UI_START_X = int(30 * UI_SCALE) # UI 起始 X 坐标
UI_START_Y = int(1500 * UI_SCALE) # UI 起始 Y 坐标

class CurrencyLevelUI:
    def __init__(self):
        self.avatar_size = avatar_size
        self.icon_size = icon_size
        self.bar_w, self.bar_h = xp_bar_size
        self.padding = padding
        self.bg_color = bg_color
        self.base_xp = base_xp
        self.xp_multiplier = xp_multiplier

        # 基础状态
        self.golds = 0
        self.crystals = 0
        self.level = 1
        self.xp = 0

        # 资源路径
        os.makedirs(DEFAULT_DATA_DIR, exist_ok=True)
        self.data_file = DEFAULT_DATA_FILE
        self._avatar_path = DEFAULT_AVATAR
        self._gold_icon_path = DEFAULT_GOLD_ICON
        self._crystal_icon_path = DEFAULT_CRYSTAL_ICON
        self._avatar_surf = None
        self._gold_surf = None
        self._crystal_surf = None

        self.font = get_font(int(24 * UI_SCALE))
        self.font_large = get_font(int(30 * UI_SCALE))

        # 回调变量
        self.on_level_up = None

        # 加载资源
        self._load_assets()

    # ---------------- assets ----------------
    def _load_assets(self):
        self._avatar_surf = self._load_image(self._avatar_path, (self.avatar_size, self.avatar_size))
        self._gold_surf = self._load_image(self._gold_icon_path, (self.icon_size, self.icon_size))
        self._crystal_surf = self._load_image(self._crystal_icon_path, (self.icon_size, self.icon_size))

    def _load_image(self, path, size):
        if path and os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, size)
            return img

        # 占位图
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((100, 100, 100, 255))

        pygame.draw.rect(surf, (180, 180, 180), surf.get_rect(), 2)
        return surf

    # ---------------- persistence ----------------
    def load_state(self):
        if not os.path.exists(self.data_file):
            return False
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.golds = int(data.get("golds", self.golds))
            self.crystals = int(data.get("crystals", self.crystals))
            self.level = int(data.get("level", self.level))
            self.xp = int(data.get("xp", self.xp))
            self.base_xp = int(data.get("base_xp", self.base_xp))
            self.xp_multiplier = float(data.get("xp_multiplier", self.xp_multiplier))
            return True
        except Exception as e:
            print(f"[Currency]读取失败: {e}")
            return False
 
    def save_state(self):
        try:
            data = {
                "golds": int(self.golds),
                "crystals": int(self.crystals),
                "level": int(self.level),
                "xp": int(self.xp),
                "base_xp": int(self.base_xp),
                "xp_multiplier": float(self.xp_multiplier)
            }
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[Currency]保存失败: {e}")
            return False

    # ---------------- progression math ----------------
    def xp_to_next(self, level=None):
        """计算升级所需的经验值"""
        if level is None:
            level = self.level
        # 指数增长
        return int(math.ceil(self.base_xp * (self.xp_multiplier ** (level - 1))))

    # ---------------- mutators ----------------
    def add_golds(self, amount: int):
        try:
            self.golds += int(amount)
            if self.golds < 0:
                self.golds = 0
        except Exception:
            pass

    def add_crystals(self, amount: int):
        try:
            self.crystals += int(amount)
            if self.crystals < 0:
                self.crystals = 0
        except Exception:
            pass

    def add_xp(self, amount: int):
        info = {"levels_gained": 0, "xp_overflow": 0}
        try:
            amt = int(amount)
        except Exception:
            return info

        self.xp += amt
        # 检查升级
        while self.xp >= self.xp_to_next():
            req = self.xp_to_next()
            self.xp -= req
            self.level += 1
            info["levels_gained"] += 1
            # 回调
            if callable(self.on_level_up):
                try:
                    self.on_level_up(self.level)
                except Exception:
                    pass
        info["xp_overflow"] = int(self.xp)
        return info

    def award_victory(self, golds: int = 50, xp: int = 30, crystals: int = 0):
        """玩家赢得一场战斗时调用。添加货币/经验值"""
        before_level = self.level
        self.add_golds(golds)
        self.add_crystals(crystals)
        res = self.add_xp(xp)
        self.save_state()
        return {
            "golds_added": golds,
            "xp_added": xp,
            "crystals_added": crystals,
            "levels_gained": res["levels_gained"],
            "new_level": self.level,
            "xp": self.xp
        }

    def set_values(self, golds=None, crystals=None, level=None, xp=None):
        if golds is not None:
            self.golds = int(golds)
        if crystals is not None:
            self.crystals = int(crystals)
        if level is not None:
            self.level = int(level)
        if xp is not None:
            self.xp = int(xp)

    # ---------------- drawing ----------------
    def draw(self, surface: pygame.Surface):
        x, y = (UI_START_X, UI_START_Y)
        # 计算整体尺寸
        width = self.avatar_size + self.padding + max(self.bar_w, 120) + self.padding + self.icon_size + 60
        height = max(self.avatar_size, self.bar_h + self.padding * 2 + 32)

        # 半透明背景表面
        bg_rect = pygame.Rect(x, y, width, height + 20)
        try:
            bg_surf = pygame.Surface((width, height + 20), pygame.SRCALPHA)
            if len(self.bg_color) == 4:
                bg_surf.fill(self.bg_color)
            else:
                bg_surf.fill((*self.bg_color, 220))
        except Exception:
            # 回退方案
            bg_surf = pygame.Surface((width, height))
            bg_surf.fill((30, 30, 30))

        # 头像
        avatar_x = self.padding
        avatar_y = (height - self.avatar_size) // 2 + 10
        if self._avatar_surf is None:
            self._avatar_surf = self._load_image(self._avatar_path, (self.avatar_size, self.avatar_size))
        bg_surf.blit(self._avatar_surf, (avatar_x, avatar_y))

        # 头像上的等级文字（右下角）
        level_txt = f"Lv {self.level}"
        txt_surf = self.font_large.render(level_txt, True, (255, 255, 255))
        txt_rect = txt_surf.get_rect()
        txt_pos = (avatar_x + self.avatar_size - txt_rect.width - 6, avatar_y + self.avatar_size - txt_rect.height - 4)
        bg_surf.blit(txt_surf, txt_pos)

        # XP 进度条区域（头像右侧）
        bar_x = avatar_x + self.avatar_size + self.padding
        bar_y = self.padding + 6
        # 绘制标签
        lbl_surf = self.font.render("XP", True, (200, 200, 200))
        bg_surf.blit(lbl_surf, (bar_x, bar_y))
        # 进度条背景
        bar_bg_rect = pygame.Rect(bar_x + 30, bar_y, self.bar_w + 30, self.bar_h)
        pygame.draw.rect(bg_surf, (80, 80, 80), bar_bg_rect, border_radius=6)
        # 进度条填充
        req = self.xp_to_next()
        fill_w = 0
        if req > 0:
            fill_w = int(self.bar_w * min(1.0, max(0.0, self.xp / req)))
        fill_rect = pygame.Rect(bar_bg_rect.x, bar_bg_rect.y, fill_w, self.bar_h)
        pygame.draw.rect(bg_surf, (90, 200, 120), fill_rect, border_radius=6)
        # XP 标签
        xp_text = f"{self.xp}/{req}"
        xp_surf = self.font.render(xp_text, True, (230, 230, 230))
        xp_x = bar_bg_rect.x + (self.bar_w + 30 - xp_surf.get_width()) // 2
        xp_y = bar_bg_rect.y + (self.bar_h - xp_surf.get_height()) // 2
        bg_surf.blit(xp_surf, (xp_x, xp_y))

        # 金币和水晶区域（xp下方）
        icons_x = bar_x + self.padding
        icons_y = self.padding + self.bar_h + 16

        # 金币（经验条下方）
        gold_pos = (icons_x, icons_y)
        bg_surf.blit(self._gold_surf, gold_pos)
        gold_txt = self.font.render(str(self.golds), True, (255, 220, 120))
        bg_surf.blit(gold_txt, (gold_pos[0] + self.icon_size + 6, gold_pos[1] + (self.icon_size - gold_txt.get_height()) // 2))

        # 水晶（金币右侧）
        crystal_pos = (icons_x + self.icon_size + int(200 * UI_SCALE), icons_y)
        bg_surf.blit(self._crystal_surf, crystal_pos)
        crystal_txt = self.font.render(str(self.crystals), True, (170, 200, 255))
        bg_surf.blit(crystal_txt, (crystal_pos[0] + self.icon_size + 6, crystal_pos[1] + (self.icon_size - crystal_txt.get_height()) // 2))

        # 最后将 bg_surf 绘制到提供的表面上
        surface.blit(bg_surf, (x, y))
        return bg_rect
