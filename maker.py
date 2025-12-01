import cv2
import numpy as np
import os
import glob
import json
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CARDS_BASE_PATH = os.path.join(PROJECT_ROOT, "assets", "cards")
OUTPUT_BASE_PATH = os.path.join(PROJECT_ROOT, "assets", "outputs")
FRAME_PATH = os.path.join(CARDS_BASE_PATH, "frame.png")

x_offset = 20  # 名称水平偏移量
y_offset = 50 # 名称向下垂直偏移量
FONT_SIZE = 50  # 字体大小
STROKE_WIDTH = 1  # 描边宽度
MAX_WIDTH = 1920
MAX_HEIGHT = 1080

# bgr颜色
def choose_color_by_level(level_value):
    colors = {
        0.0: (0, 0, 255),      # 红色
        0.5: (114, 128, 255),  # 粉色
        1.0: (20, 100, 255),   # 橙色
        1.5: (45, 82, 160),    # 赭色
        2.0: (0, 215, 255),    # 金色
        2.5: (130, 0, 75),     # 深紫色
        3.0: (226, 43, 138),   # 紫色
        3.5: (160, 0, 0),      # 深蓝色
        4.0: (255, 191, 0),    # 天蓝色
        4.5: (0, 128, 0),    # 深绿色
        5.0: (0, 255, 0),      # 绿色
        6.0: (128, 128, 128),  # 灰色
    }

    try:
        level = float(level_value)
    except (TypeError, ValueError):
        level = 0.0

    if level in colors:
        return colors[level]

    rounded = round(level, 1)
    if rounded in colors:
        return colors[rounded]

    integer_level = int(level)
    if float(integer_level) in colors:
        return colors[float(integer_level)]

    closest_key = min(colors.keys(), key=lambda key: abs(key - level))
    return colors[closest_key]

def load_cards_json(json_path):
    if not os.path.exists(json_path):
        return []
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_card_image(card_id, cards_dir='cards'):
    if not os.path.isdir(cards_dir):
        return None
    pattern = os.path.join(cards_dir, f"{card_id}.*")
    matches = glob.glob(pattern)
    if not matches:
        return None
    for ext in ('.png', '.jpg', '.jpeg', '.webp'):
        for m in matches:
            if m.lower().endswith(ext):
                return m
    return matches[0]

def find_system_font():
    candidates = [
        r"C:/Windows/Fonts/simsun.ttc",
        r"C:/Windows/Fonts/simsun.ttf",
        r"C:/Windows/Fonts/msyh.ttc",
        r"C:/Windows/Fonts/msyh.ttf",
        r"C:/Windows/Fonts/simhei.ttf",
        r"C:/Windows/Fonts/msyhbd.ttf",
        r"C:/Windows/Fonts/arial.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def draw_text(img, text, color_bgr, font_path=None, font_size=40, italic=False, italic_angle=15):
    has_alpha = (img.shape[2] == 4)
    if has_alpha:
        cv2_to_pil = cv2.COLOR_BGRA2RGBA
        pil_to_cv2 = cv2.COLOR_RGBA2BGRA
    else:
        cv2_to_pil = cv2.COLOR_BGR2RGB
        pil_to_cv2 = cv2.COLOR_RGB2BGR

    pil_img = Image.fromarray(cv2.cvtColor(img, cv2_to_pil)).convert('RGBA')

    # 尝试加载字体
    font = None
    if font_path and os.path.exists(font_path):
        try:
            font = ImageFont.truetype(font_path, font_size)
        except Exception:
            font = None
    if font is None:
        sys_font = find_system_font()
        if sys_font:
            try:
                font = ImageFont.truetype(sys_font, font_size)
            except Exception:
                font = ImageFont.load_default()
        else:
            font = ImageFont.load_default()

    # 文本绘制在独立透明图层上，便于斜体变换
    W, H = pil_img.size
    txt_layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)

    # PIL 颜色为 RGB
    color_rgb = (int(color_bgr[2]), int(color_bgr[1]), int(color_bgr[0]))

    try:
        text_w, text_h = draw.textsize(text, font=font)
    except Exception:
        text_w, text_h = draw.textbbox((0, 0), text, font=font)[2:]

    x = (W - text_w) // 2
    outline_color = (0, 0, 0, 255) # 描边提高可读性
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(1,1),(-1,1),(1,-1)]:
        draw.text((x_offset+x+dx, y_offset+dy), text, font=font, fill=outline_color, stroke_width=STROKE_WIDTH)
    draw.text((x_offset+x+dx, y_offset), text, font=font, fill=color_rgb + (255,))
    # 斜体处理：对文本层进行水平切变
    if italic:
        import math
        angle = float(italic_angle)
        shear = math.tan(math.radians(angle))
        txt_layer = txt_layer.transform((W, H), Image.AFFINE, (1, shear, 0, 0, 1, 0), resample=Image.BICUBIC)

    # 将文本层合并到原图
    combined = Image.alpha_composite(pil_img, txt_layer)
    out = cv2.cvtColor(np.array(combined), pil_to_cv2)
    return out

def overlay_card(content_path, frame_path, output_path,
                 card_name=None, level=0, font_path=None):
    frame = cv2.imread(frame_path, cv2.IMREAD_UNCHANGED)
    content = cv2.imread(content_path, cv2.IMREAD_UNCHANGED)

    if frame is None or content is None:
        raise ValueError(f"路径错误：无法读取图片: {content_path} or {frame_path}")

    if frame.shape[2] == 4:
        frame_bgr = frame[:, :, :3].astype(np.float32) / 255.0
        frame_alpha = frame[:, :, 3].astype(np.float32) / 255.0
    else:
        frame_bgr = frame.astype(np.float32) / 255.0
        frame_alpha = np.ones(frame_bgr.shape[:2], dtype=np.float32)

    # 尺寸调整
    fh, fw = frame_bgr.shape[:2]
    if fw > MAX_WIDTH or fh > MAX_HEIGHT:
        scale = min(MAX_WIDTH / fw, MAX_HEIGHT / fh)
        new_fw = int(fw * scale)
        new_fh = int(fh * scale)
        
        frame_bgr_resized = cv2.resize((frame_bgr * 255.0).astype(np.uint8), (new_fw, new_fh), 
                                       interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        frame_alpha_resized = cv2.resize((frame_alpha * 255.0).astype(np.uint8), (new_fw, new_fh), 
                                         interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        
        frame_bgr = frame_bgr_resized
        frame_alpha = frame_alpha_resized
        fw, fh = new_fw, new_fh

    if content.shape[2] == 4:
        content_bgr = content[:, :, :3].astype(np.float32) / 255.0
        content_alpha = content[:, :, 3].astype(np.float32) / 255.0
        content_bgr = content_bgr * content_alpha[:, :, None] + (1.0 - content_alpha[:, :, None]) * 1.0
    else:
        content_bgr = content.astype(np.float32) / 255.0

    content_resized = cv2.resize((content_bgr * 255.0).astype(np.uint8), (fw, fh), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0

    # 合成内容与边框
    content_on_bg = content_resized
    fa = frame_alpha[:, :, None]
    output = content_on_bg * (1.0 - fa) + frame_bgr * fa
    output_uint8 = (np.clip(output, 0.0, 1.0) * 255.0).astype(np.uint8)

    # 绘制文字，顶部居中，使用宋体并模拟斜体
    output_uint8 = draw_text(
        output_uint8,
        card_name,
        color_bgr=choose_color_by_level(level),
        font_path=font_path if (font_path and os.path.exists(font_path)) else find_system_font(), # 使用传入字体或系统字体
        font_size=FONT_SIZE,
        italic=True,
    )

    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    cv2.imwrite(output_path, output_uint8)
    print("✔ 成功生成:", output_path)


def iter_level_directories():
    if not os.path.isdir(CARDS_BASE_PATH):
        print(f"未找到卡牌目录: {CARDS_BASE_PATH}")
        return []
    candidates = []
    for entry in sorted(os.listdir(CARDS_BASE_PATH)):
        dir_path = os.path.join(CARDS_BASE_PATH, entry)
        if os.path.isdir(dir_path) and os.path.exists(os.path.join(dir_path, "cards.json")):
            candidates.append(entry)
    return candidates


def generate_cards_for_directory(dir_name):
    cards_path = os.path.join(CARDS_BASE_PATH, dir_name)
    json_path = os.path.join(cards_path, "cards.json")
    output_path = os.path.join(OUTPUT_BASE_PATH, dir_name)

    entries = load_cards_json(json_path)
    if not entries:
        print(f"⚠ {dir_name}: 未找到 cards.json 或没有配置，跳过")
        return

    for e in entries:
        cid = e.get('id')
        card_name = e.get('name')
        level = e.get('level')
        if not cid:
            continue

        card_img = find_card_image(cid, cards_path)
        if not card_img:
            print(f"⚠ {dir_name}: 未找到图片 {cid}，跳过")
            continue

        output = os.path.join(output_path, f"{cid}.png")
        if os.path.exists(output):
            continue

        overlay_card(card_img, FRAME_PATH, output, card_name=card_name, level=level)



if __name__ == "__main__":
    processed_any = False
    for directory in iter_level_directories():
        generate_cards_for_directory(directory)
        processed_any = True

    if not processed_any:
        print("没有找到需要处理的稀有度目录。")