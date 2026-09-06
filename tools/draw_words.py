#!/usr/bin/env python3
"""색·무늬·도형은 **AI에게 맡기지 않고 직접 그린다.** (Day 43.5 열 장)

왜 여기만 손으로 그리나:
  생성 모델은 '하늘색'과 '남색'을 구별해 내지 못한다. 줄무늬 개수도 못 맞춘다.
  개수·국기·달력을 draw_exact.py 로 뺀 것과 같은 이유다 — 정확해야 하는 그림이다.

색맹 배려 (프로젝트 규칙: 색상 단독 금지):
  색 이름을 색칠판 하나로만 보이면, 색을 구별 못 하는 학습자에게는 아무 뜻이 없다.
  그래서 **그 색을 가진 실제 사물**을 같이 그린다 —
  하늘색엔 하늘과 구름, 남색엔 깊은 바다, 초록엔 잎, 주황엔 귤, 회색엔 돌.
  색이 안 보여도 사물로 뜻이 전해지고, 보이는 사람에게는 정확한 색이 전해진다.
  (글자는 넣지 않는다 — 우리 그림 규칙이다.)

실행: python3 tools/draw_words.py
"""
import math
import pathlib

from PIL import Image, ImageDraw

R = pathlib.Path(__file__).resolve().parent.parent
IMG = R / "img"
S = 640
BG = (255, 255, 255)
LINE = (60, 60, 70)
W = max(3, S // 160)            # 앱 그림체가 굵은 테두리다


def new():
    im = Image.new("RGB", (S, S), BG)
    return im, ImageDraw.Draw(im)


def swatch(dr, col, x=S * 0.09, y=S * 0.66, w=S * 0.82, h=S * 0.20):
    """아래쪽 색칠판 — '이 색이다'를 정확히 못 박는 자리."""
    dr.rounded_rectangle([x, y, x + w, y + h], radius=h * 0.28, fill=col,
                         outline=LINE, width=W)


def save(im, name):
    im.save(IMG / f"{name}.webp", "WEBP", quality=88)


# ── 색 다섯 — 사물 + 색칠판 ──────────────────────────────────
def sky(name, col):
    """하늘색 — 하늘과 구름."""
    im, dr = new()
    dr.rounded_rectangle([S * .09, S * .10, S * .91, S * .58], radius=S * .05,
                         fill=col, outline=LINE, width=W)
    for cx, cy, r in ((S * .34, S * .30, S * .085), (S * .45, S * .27, S * .11),
                      (S * .57, S * .31, S * .075)):
        dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255))
    dr.ellipse([S * .70, S * .17, S * .84, S * .31], fill=(255, 214, 92),
               outline=LINE, width=W)                       # 해
    swatch(dr, col)
    save(im, name)


def sea(name, col):
    """남색·바다색 — 깊은 바다의 물결."""
    im, dr = new()
    dr.rounded_rectangle([S * .09, S * .10, S * .91, S * .58], radius=S * .05,
                         fill=col, outline=LINE, width=W)
    for k in range(3):
        y = S * (.26 + k * .11)
        pts = []
        for i in range(41):
            x = S * .13 + (S * .74) * i / 40
            pts.append((x, y + math.sin(i / 40 * math.pi * 3) * S * .022))
        dr.line(pts, fill=(255, 255, 255), width=W, joint="curve")
    swatch(dr, col)
    save(im, name)


def leaf(name, col):
    """초록색 — 나뭇잎."""
    im, dr = new()
    dr.polygon([(S * .50, S * .10), (S * .84, S * .34), (S * .50, S * .58),
                (S * .16, S * .34)], fill=col, outline=LINE, width=W)
    dr.line([S * .50, S * .12, S * .50, S * .56], fill=(255, 255, 255), width=W)
    for k in range(1, 4):                                    # 잎맥
        y = S * (.20 + k * .09)
        dr.line([S * .50, y, S * .50 - S * .13, y + S * .05],
                fill=(255, 255, 255), width=max(2, W - 1))
        dr.line([S * .50, y, S * .50 + S * .13, y + S * .05],
                fill=(255, 255, 255), width=max(2, W - 1))
    swatch(dr, col)
    save(im, name)


def fruit(name, col):
    """주황색 — 귤 한 알."""
    im, dr = new()
    dr.ellipse([S * .26, S * .13, S * .74, S * .56], fill=col, outline=LINE, width=W)
    dr.arc([S * .32, S * .18, S * .56, S * .40], 150, 250, fill=(255, 255, 255), width=W)
    dr.line([S * .50, S * .14, S * .50, S * .07], fill=(122, 78, 46), width=W)
    dr.polygon([(S * .50, S * .10), (S * .64, S * .04), (S * .58, S * .14)],
               fill=(86, 158, 86), outline=LINE, width=max(2, W - 1))
    swatch(dr, col)
    save(im, name)


def stone(name, col):
    """회색 — 돌."""
    im, dr = new()
    dr.polygon([(S * .22, S * .48), (S * .30, S * .20), (S * .55, S * .12),
                (S * .78, S * .28), (S * .74, S * .52), (S * .40, S * .57)],
               fill=col, outline=LINE, width=W)
    dr.line([S * .34, S * .30, S * .55, S * .24], fill=(255, 255, 255), width=max(2, W - 1))
    swatch(dr, col)
    save(im, name)


# ── 색깔(총칭) · 무늬 · 줄무늬 · 투명 · 동그라미 ──────────────
def colors(name):
    """색깔 — 여러 색이 나란히. 명도도 함께 달라서 색맹이어도 여섯 칸이 갈린다."""
    im, dr = new()
    cols = [(214, 62, 74), (240, 146, 42), (247, 205, 60),
            (92, 168, 88), (58, 122, 198), (120, 84, 168)]
    n = len(cols)
    w = S * .76 / n
    for i, c in enumerate(cols):
        x = S * .12 + w * i
        dr.rounded_rectangle([x, S * .22, x + w * .88, S * .78],
                             radius=w * .18, fill=c, outline=LINE, width=W)
    save(im, name)


def pattern(name):
    """무늬 — 같은 모양이 규칙적으로 되풀이되는 것."""
    im, dr = new()
    dr.rounded_rectangle([S * .12, S * .12, S * .88, S * .88], radius=S * .06,
                         fill=(250, 246, 238), outline=LINE, width=W)
    col = (214, 62, 74)
    for r in range(5):
        for c in range(5):
            cx = S * (.20 + c * .15)
            cy = S * (.20 + r * .15)
            if (r + c) % 2 == 0:                      # 마름모
                d = S * .045
                dr.polygon([(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)],
                           fill=col)
            else:                                     # 동그라미
                d = S * .034
                dr.ellipse([cx - d, cy - d, cx + d, cy + d], outline=col, width=W)
    save(im, name)


def stripes(name):
    """줄무늬 — 굵기가 같은 띠가 나란히. 개수를 정확히 맞춘다(모델은 이걸 못 한다)."""
    im, dr = new()
    x0, x1 = S * .12, S * .88
    y0, y1 = S * .12, S * .88
    dr.rounded_rectangle([x0, y0, x1, y1], radius=S * .06, fill=(250, 250, 250),
                         outline=LINE, width=W)
    n = 7
    band = (y1 - y0) / n
    for i in range(n):
        if i % 2:
            continue
        dr.rectangle([x0 + W, y0 + band * i + W, x1 - W, y0 + band * (i + 1)],
                     fill=(58, 122, 198))
    dr.rounded_rectangle([x0, y0, x1, y1], radius=S * .06, outline=LINE, width=W)
    save(im, name)


def clear(name):
    """투명하다 — 뒤가 비쳐 보인다. 유리컵 너머로 바둑판이 이어져 보이게 그린다."""
    im, dr = new()
    # 뒤에 깔린 바둑판
    for r in range(6):
        for c in range(6):
            if (r + c) % 2:
                continue
            dr.rectangle([S * (.14 + c * .12), S * (.14 + r * .12),
                          S * (.14 + (c + 1) * .12), S * (.14 + (r + 1) * .12)],
                         fill=(226, 226, 232))
    # 유리컵 — 안쪽을 칠하지 않아 뒤가 그대로 보인다
    gx0, gx1 = S * .30, S * .70
    dr.polygon([(gx0, S * .22), (gx1, S * .22), (gx1 - S * .04, S * .78),
                (gx0 + S * .04, S * .78)], outline=LINE, width=W)
    dr.line([gx0 + S * .06, S * .28, gx0 + S * .09, S * .70],
            fill=(140, 190, 225), width=W)                   # 빛 반사 한 줄
    save(im, name)


def circle(name):
    """동그라미·원 — 세모·네모와 나란히 놓아 '어느 것이 원인가'가 분명하게."""
    im, dr = new()
    dr.polygon([(S * .22, S * .40), (S * .34, S * .19), (S * .46, S * .40)],
               fill=(226, 226, 232), outline=LINE, width=W)
    dr.rectangle([S * .56, S * .19, S * .78, S * .40],
                 fill=(226, 226, 232), outline=LINE, width=W)
    dr.ellipse([S * .30, S * .48, S * .70, S * .88],
               fill=(214, 62, 74), outline=LINE, width=W * 2)
    save(im, name)


JOBS = [
    ("d435-xanh-da-troi", sky, (126, 196, 235)),      # 하늘색
    ("d435-xanh-nuoc-bien", sea, (30, 62, 130)),      # 바다색·남색
    ("d435-xanh-la-cay", leaf, (76, 160, 74)),        # 초록색
    ("d435-da-cam", fruit, (238, 132, 36)),           # 주황색
    ("d435-xam", stone, (150, 152, 158)),             # 회색
]

if __name__ == "__main__":
    IMG.mkdir(exist_ok=True)
    for name, fn, col in JOBS:
        fn(name, col)
    colors("d435-mau-sac")
    pattern("d435-hoa-van")
    stripes("d435-ke-soc")
    clear("d435-trong-suot")
    circle("d435-hinh-tron")
    print(f"직접 그린 그림 {len(JOBS) + 5}장 — img/d435-*.webp")
