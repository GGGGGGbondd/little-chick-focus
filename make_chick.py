# -*- coding: utf-8 -*-
"""生成小鸡浮窗贴纸 chick.png
风格贴近范图：黄色小鸡 + 灰色圆框眼镜 + 蓝色数学书(MATHS)，去掉问号。
做法：4 倍超采样绘制后缩小，边缘平滑；再把半透明边缘二值化，
避免 Tk 透明色键控 (-transparentcolor) 留下粉红描边。
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

S = 4               # 超采样倍数
FW, FH = 116, 121   # 最终尺寸(px)
W, H = FW * S, FH * S

YELLOW   = (255, 213, 66, 255)
YELLOW_D = (243, 192, 50, 255)   # 底部柔光
BROWN    = (120, 72, 49, 255)    # 描边
ORANGE   = (246, 138, 37, 255)
BLUE     = (49, 146, 236, 255)
BLUE_D   = (39, 129, 220, 255)
WHITE    = (255, 246, 224, 255)
GRAY     = (154, 150, 144, 255)
LENS     = (255, 244, 220, 110)  # 半透明镜片
GLOSS    = (255, 255, 255, 90)   # 头顶高光

img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)


def P(x, y):
    return (x * S, y * S)


def E(x1, y1, x2, y2, **kw):
    d.ellipse([P(x1, y1), P(x2, y2)], **kw)


def L(x1, y1, x2, y2, **kw):
    d.line([P(x1, y1), P(x2, y2)], **kw)


def PL(pts, **kw):
    d.polygon([P(x, y) for x, y in pts], **kw)


def TX(center, text, size, fill):
    try:
        f = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', size * S)
    except Exception:
        try:
            f = ImageFont.truetype('arialbd.ttf', size * S)
        except Exception:
            f = ImageFont.load_default()
    d.text((center[0] * S, center[1] * S), text, font=f, fill=fill, anchor='mm')


# ---- 身体（蛋形，无头冠） ----
E(15, 16, 101, 110, fill=YELLOW)
E(26, 74, 92, 104, fill=YELLOW_D)                      # 底部柔光
E(15, 16, 101, 110, outline=BROWN, width=round(2.6 * S))
E(33, 25, 49, 37, fill=GLOSS)                          # 头顶高光

# ---- 翅膀 ----
E(7, 54, 31, 80, fill=YELLOW, outline=BROWN, width=round(2.2 * S))
E(85, 54, 109, 80, fill=YELLOW, outline=BROWN, width=round(2.2 * S))

# ---- 眼镜（灰圆框 + 半透明镜片，先画镜片后画眼睛） ----
E(33, 25, 53, 45, fill=LENS, outline=GRAY, width=round(2.4 * S))
E(63, 25, 83, 45, fill=LENS, outline=GRAY, width=round(2.4 * S))
L(53, 35, 63, 35, fill=GRAY, width=round(2.4 * S))     # 鼻梁
L(33, 32, 23, 28, fill=GRAY, width=round(2.0 * S))     # 镜腿
L(83, 32, 93, 28, fill=GRAY, width=round(2.0 * S))

# ---- 眼睛 + 高光 ----
E(39, 33, 47, 41, fill=BROWN)
E(65, 33, 73, 41, fill=BROWN)
E(41, 35, 44, 38, fill=WHITE)
E(67, 35, 70, 38, fill=WHITE)

# ---- 眉毛 ----
L(35, 24, 49, 21, fill=BROWN, width=round(2.2 * S))
L(81, 24, 67, 21, fill=BROWN, width=round(2.2 * S))

# ---- 嘴巴（小橙三角） ----
PL([(49, 48), (67, 48), (58, 58)], fill=ORANGE, outline=BROWN)

# ---- 蓝色数学书（开本，捧在胸前，像范图） ----
PL([(30, 67), (56, 73), (56, 96), (30, 90)], fill=BLUE, outline=BROWN, width=round(2 * S))
PL([(56, 73), (82, 67), (82, 90), (56, 96)], fill=BLUE_D, outline=BROWN, width=round(2 * S))
L(56, 74, 56, 95, fill=BROWN, width=round(2 * S))      # 书脊
TX((43, 79), 'MATHS', 7.5, WHITE)

# ---- 缩小到最终尺寸：RGB 与 Alpha 分开缩放，避免黑边 ----
rgb = img.convert('RGB').resize((FW, FH), Image.LANCZOS)
a = img.getchannel('A').resize((FW, FH), Image.LANCZOS)
img = Image.merge('RGBA', (*rgb.split(), a))
# 半透明边缘二值化，避免透明色键控留下粉边（贴纸式干净边缘）
a = img.getchannel('A').point(lambda v: 255 if v >= 160 else 0)
img.putalpha(a)

img.save(str(Path(__file__).with_name('chick.png')))
print('chick.png 已生成:', FW, 'x', FH)

# 头部小图标：直接缩小 chick.png（半透明边缘在纯色背景上自然混合）
small = img.resize((52, 54), Image.LANCZOS)
small.save(str(Path(__file__).with_name('chick_small.png')))
print('chick_small.png 已生成: 52 x 54')
