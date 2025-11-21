import cv2
import numpy as np
import os
import glob
import json
from PIL import Image, ImageDraw, ImageFont

lv = "C"
cards_path = "C:\\Users\\22716\\Desktop\\cards\\" + lv
frame_path = "C:\\Users\\22716\\Desktop\\cards\\frame.png"
#frame_path = "C:\\Users\\22716\\Desktop\\cards\\frame.webp"
json_path = "C:\\Users\\22716\\Desktop\\cards\\" + lv + "\\cards.json"
output_path = "C:\\Users\\22716\\Desktop\\outputs\\" + lv
x_offset = 20  # 名称水平偏移量
y_offset = 50 # 名称向下垂直偏移量
FONT_SIZE = 50  # 字体大小
STROKE_WIDTH = 1  # 描边宽度
MAX_WIDTH = 1920
MAX_HEIGHT = 1080

# bgr颜色
def choose_color_by_level(n):
    colors = {
        0: (0, 0, 255),    # 红色
        1: (20, 100, 255), # 橙色
        2: (0, 215, 255),  # 金色
        3: (226, 43, 138), # 紫色
        4: (255, 191, 0),  # 天蓝色
        5: (0, 255, 0),   # 绿色
        6: (128, 128, 128) # 灰色
    }
    return colors[int(n) % 7]

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
        # 优先尝试宋体（SimSun）用于中文正体
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

    cv2.imwrite(output_path, output_uint8)
    print("✔ 成功生成:", output_path)



if __name__ == "__main__":
    entries = load_cards_json(json_path)
    for e in entries:
        cid = e.get('id')
        card_name = e.get('name')
        level = e.get('level')
        card_img = find_card_image(cid, cards_path)
        output = os.path.join(output_path, f"{cid}.png")
        if os.path.exists(output):
            continue
        overlay_card(card_img, frame_path, output, card_name=card_name, level=level)