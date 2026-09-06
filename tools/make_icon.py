#!/usr/bin/env python3
"""앱 아이콘을 코드로 그린다 — AI에게 맡기면 글자와 모양이 어긋난다.

무엇을 말해야 하는가:
  이 앱은 이제 **베트남 사람이 한국어 시험을 준비하는** 앱이다.
  예전 아이콘(말풍선 둘 + 별)은 '베트남'과 '말하기'만 말하고 **한국어를 말하지 않았다**.
  스토어 목록에서 경쟁 앱과 나란히 놓였을 때 한눈에 갈려야 한다.

지금 모양 — 겹친 두 겹:
  빨강 바탕 + 금별(뒤) + 흰 말풍선(앞) + 그 안에 빨간 '한'
    · 빨강·금별 = 베트남 (국기)
    · 말풍선    = 말하기·배우기 (예전 아이콘의 겹침 구조를 잇는다)
    · 한        = 한국어. 베트남 학습자에게 'tiếng Hàn'의 그 글자다

작은 크기에서 고른 이유(후보 넷을 28·48·72px과 원형 마스크로 실제로 비교했다):
  · 금별을 **금 말풍선** 뒤에 두면 같은 색끼리 붙어 별이 사라진다 → 풍선을 흰색으로
  · 별을 풍선 아래에 따로 두면 스토어에서 **평점 별**로 읽힌다 → 뒤에 겹치게
  · 별을 빼면 가장 깨끗하지만 '베트남'이 약해진다 → 남긴다

마스크 안전영역: 안드로이드는 아이콘을 원으로 깎을 수 있다(purpose maskable).
  중심에서 반지름 0.40 안에 모든 요소를 넣는다. 별의 가장 먼 끝이 0.376이라 안전하다.

사용: python3 tools/make_icon.py
"""
import math
import pathlib

from PIL import Image, ImageDraw, ImageFont

R = pathlib.Path(__file__).resolve().parent.parent
S = 1024                       # 크게 그리고 줄여야 가장자리가 매끈하다
RED, GOLD, WHITE = (218, 37, 29), (255, 205, 0), (255, 255, 255)
# 굵은 한글 — 얇은 획은 48px에서 뭉개진다
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
FONT_BOLD_INDEX = 6


def star(dr, cx, cy, rr, fill):
    pts = []
    for i in range(10):
        rad = rr if i % 2 == 0 else rr * 0.382
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    dr.polygon(pts, fill=fill)


def bubble(dr, x, y, w, h, fill, tail=(0.22, 0.28)):
    dr.rounded_rectangle([x, y, x + w, y + h], radius=h * 0.30, fill=fill)
    tx, ty = tail
    dr.polygon([(x + w * tx, y + h * 0.93), (x + w * (tx + 0.15), y + h * 0.93),
                (x + w * ty, y + h * 1.20)], fill=fill)


def centered(dr, cx, cy, text, font, fill):
    b = dr.textbbox((0, 0), text, font=font)
    dr.text((cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2), text, font=font, fill=fill)


def build(size=S, bg=True):
    im = Image.new("RGB", (S, S), RED) if bg else Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    star(dr, S * 0.315, S * 0.330, S * 0.125, GOLD)          # 뒤 — 베트남
    bubble(dr, S * 0.22, S * 0.365, S * 0.60, S * 0.40, WHITE)
    font = ImageFont.truetype(FONT, int(S * 0.34), index=FONT_BOLD_INDEX)
    centered(dr, S * 0.52, S * 0.555, "한", font, RED)        # 앞 — 한국어
    return im.resize((size, size), Image.LANCZOS)


def check():
    """마스크 안전영역 검산 — **실제로 그려지는 점**이 중심 반지름 0.40 안에 있는가.

    바운딩 박스의 모서리로 재면 안 된다. 말풍선은 모서리가 둥글고 꼬리는 한쪽에만
    있어서, 박스 모서리(0.471)는 그림에 존재하지 않는 점이다. 그 숫자로 판정하면
    멀쩡한 도안을 불합격시킨다.
    """
    c = 0.5
    far_star = math.hypot(c - 0.315, c - 0.330) + 0.125
    x, y, w, h = 0.22, 0.365, 0.60, 0.40
    r = h * 0.30                                   # 둥근 모서리 반지름
    corners = [(x + r, y + r), (x + w - r, y + r),
               (x + r, y + h - r), (x + w - r, y + h - r)]
    far_bub = max(math.hypot(cx - c, cy - c) for cx, cy in corners) + r
    tail = (x + w * 0.28, y + h * 1.20)            # 꼬리 끝
    far_tail = math.hypot(tail[0] - c, tail[1] - c)
    worst = max(far_star, far_bub, far_tail)
    assert worst < 0.40, f"안전영역 밖: 별 {far_star:.3f} 풍선 {far_bub:.3f} 꼬리 {far_tail:.3f}"
    return far_star, far_bub, far_tail


if __name__ == "__main__":
    fs, fb, ft = check()
    build(512).save(R / "icon.png")
    build(192).save(R / "icon-192.png")
    build(180).save(R / "icon-180.png")
    build(512).save(R / "img" / "app-icon.webp", "WEBP", quality=92)
    print(f"아이콘 만듦 — icon.png(512) · icon-192.png · icon-180.png · img/app-icon.webp")
    print(f"  마스크 안전영역(0.40 이내): 별 {fs:.3f} · 풍선 {fb:.3f} · 꼬리 {ft:.3f}")
