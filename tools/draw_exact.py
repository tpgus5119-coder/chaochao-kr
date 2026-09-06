#!/usr/bin/env python3
"""개수·국기처럼 **정확해야 하는 그림은 AI에게 맡기지 않고 직접 그린다.**

검수에서 드러난 것: 숫자 단어 그림 7장이 전부 개수가 틀렸다(năm=5인데 사과 3개,
chín=9인데 14개). 국기도 4괘가 엉터리였다. 생성 모델은 '정확히 N개'와 '정해진 문양'을
못 그린다 — 이건 프롬프트를 고쳐도 안 된다. 그래서 이 둘만 코드로 그린다.

사용: python3 tools/draw_exact.py
"""
import math, pathlib
from PIL import Image, ImageDraw, ImageFont

R = pathlib.Path(__file__).resolve().parent.parent
IMG = R / 'img'
S = 640
BG = (255, 255, 255)

def apple(dr, cx, cy, r):
    """납작한 사과 하나 — 앱의 플랫 일러스트와 같은 결로."""
    body = (200, 72, 72)
    dr.ellipse([cx - r, cy - r * .92, cx + r, cy + r * 1.05], fill=body)
    dr.ellipse([cx - r * .95, cy - r * .95, cx - r * .1, cy - r * .1],
               fill=(228, 116, 116))                       # 빛 받는 쪽
    dr.line([cx, cy - r * .85, cx + r * .1, cy - r * 1.28], fill=(122, 78, 46), width=max(3, int(r * .13)))
    dr.polygon([(cx + r * .1, cy - r * 1.2), (cx + r * .75, cy - r * 1.4),
                (cx + r * .5, cy - r * .95)], fill=(86, 158, 86))   # 잎

def count_sheet(n, path):
    """정확히 n개. 줄 수는 보기 좋게 나눈다."""
    im = Image.new('RGB', (S, S), BG)
    dr = ImageDraw.Draw(im)
    cols = 1 if n == 1 else 2 if n <= 4 else 3 if n <= 6 else 4 if n <= 8 else 5 if n <= 10 else 5
    rows = math.ceil(n / cols)
    cw, ch = S / cols, (S - 60) / rows
    r = min(cw, ch) * 0.33
    left = n
    for row in range(rows):
        k = min(cols, left)                                 # 마지막 줄은 남은 만큼
        left -= k
        y = 40 + ch * (row + .5)
        x0 = (S - k * cw) / 2 + cw / 2
        for c in range(k):
            apple(dr, x0 + cw * c, y, r)
    im.save(path, 'WEBP', quality=88)

NUM = {'d07-mot': 1, 'd07-hai': 2, 'd07-ba': 3, 'd07-bon': 4, 'd07-nam': 5,
       'd07-sau': 6, 'd07-bay': 7, 'd07-tam': 8, 'd07-chin': 9, 'd07-muoi': 10, 'd102-chuc': 10}

def flag_vn(path):
    """베트남 국기 — 빨강 바탕에 한가운데 노란 오각별."""
    im = Image.new('RGB', (S, S), BG)
    dr = ImageDraw.Draw(im)
    w, h = 520, 347                                        # 3:2
    x0, y0 = (S - w) // 2, (S - h) // 2
    dr.rectangle([x0, y0, x0 + w, y0 + h], fill=(218, 37, 29))
    cx, cy, rr = x0 + w / 2, y0 + h / 2, h * 0.32
    pts = []
    for i in range(10):                                    # 오각별 = 바깥 5 + 안쪽 5
        rad = rr if i % 2 == 0 else rr * 0.382
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
    dr.polygon(pts, fill=(255, 205, 0))
    dr.rectangle([x0, y0, x0 + w, y0 + h], outline=(220, 220, 226), width=2)
    im.save(path, 'WEBP', quality=90)

def flag_kr(path):
    """태극기 — 태극과 4괘를 자로 잰 듯이. AI는 괘를 절대 못 그린다."""
    im = Image.new('RGB', (S, S), BG)
    big = Image.new('RGB', (S * 3, S * 3), BG)             # 3배로 그린 뒤 줄여서 매끄럽게
    dr = ImageDraw.Draw(big)
    W, H = 540 * 3, 360 * 3
    X, Y = (S * 3 - W) // 2, (S * 3 - H) // 2
    dr.rectangle([X, Y, X + W, Y + H], fill=(255, 255, 255))
    cx, cy = X + W / 2, Y + H / 2
    r = H / 4
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 71, 160))          # 아래 파랑
    # 각도 부호가 반대였다 (2026-08-29, 대표님 지적).
    #    -33.69 로 두니 빨강이 **왼쪽 90%** 로 몰려 좌우로 갈렸다. 태극기는 위아래다.
    #    각도를 바꿔 가며 재서 찾았다: +33.69 에서 빨강이 위 90% · 왼 56% 로 제자리에 온다.
    #    처음에 점 여덟 개만 찍어 보고 '맞다'고 했는데, 그 점들이 하필 두 배치에서
    #    같은 색이 나오는 자리였다. **넓이로 재야 했다.**
    dr.pieslice([cx - r, cy - r, cx + r, cy + r], 33.69 - 180, 33.69, fill=(205, 46, 58))
    a = math.radians(33.69)
    hx, hy = math.cos(a) * r / 2, math.sin(a) * r / 2
    dr.ellipse([cx - hx - r / 2, cy - hy - r / 2, cx - hx + r / 2, cy - hy + r / 2], fill=(205, 46, 58))
    dr.ellipse([cx + hx - r / 2, cy + hy - r / 2, cx + hx + r / 2, cy + hy + r / 2], fill=(0, 71, 160))
    # 4괘 — 막대 3줄, 끊긴 줄은 가운데를 비운다
    BARS = {'건': [1, 1, 1], '곤': [0, 0, 0], '감': [0, 1, 0], '이': [1, 0, 1]}
    bl, bw, gap = r * 1.0, r * 0.16, r * 0.09
    def gua(name, ang):
        rad = math.radians(ang)
        ox, oy = cx + math.cos(rad) * r * 2.0, cy + math.sin(rad) * r * 2.0
        for i, solid in enumerate(BARS[name]):
            off = (i - 1) * (bw + gap)
            px, py = ox + math.cos(rad) * off, oy + math.sin(rad) * off
            dx, dy = -math.sin(rad), math.cos(rad)          # 막대는 반지름에 직각
            def seg(t0, t1):
                dr.polygon([(px + dx * t0 - math.cos(rad) * bw / 2, py + dy * t0 - math.sin(rad) * bw / 2),
                            (px + dx * t1 - math.cos(rad) * bw / 2, py + dy * t1 - math.sin(rad) * bw / 2),
                            (px + dx * t1 + math.cos(rad) * bw / 2, py + dy * t1 + math.sin(rad) * bw / 2),
                            (px + dx * t0 + math.cos(rad) * bw / 2, py + dy * t0 + math.sin(rad) * bw / 2)],
                           fill=(0, 0, 0))
            if solid: seg(-bl / 2, bl / 2)
            else:
                seg(-bl / 2, -bl * 0.09); seg(bl * 0.09, bl / 2)
    # 실제 태극기 배치: 왼위 건 · 오위 감 · 왼아래 리 · 오아래 곤
    # (화면 좌표는 y가 아래로 커진다 — 위쪽이 음수 각도다)
    gua('건', 180 + 33.69); gua('감', -33.69); gua('이', 180 - 33.69); gua('곤', 33.69)
    dr.rectangle([X, Y, X + W, Y + H], outline=(220, 220, 226), width=6)
    im = big.resize((S, S), Image.LANCZOS)
    im.save(path, 'WEBP', quality=90)


# ── 달력 ───────────────────────────────────────────────────────────
# AI 가 그린 달력은 요일 칸에 "SON FUN TUU WEIE" 같은 없는 글자를 박아 놓는다.
# 열세 장이 전부 그랬다. 그래서 직접 그린다 — 깨질 글자가 아예 없어진다.
# 요일 머리글은 **베트남 달력이 실제로 쓰는 표기**를 그대로 쓴다:
#   T2 T3 T4 T5 T6 T7 CN  (thứ hai … thứ bảy, chủ nhật). 배우는 사람이 현지 달력을 읽게 된다.
CAL_H = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']

def _font(sz):
    for f in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
              '/System/Library/Fonts/Supplemental/Arial.ttf',
              '/System/Library/Fonts/Helvetica.ttc'):
        try: return ImageFont.truetype(f, sz)
        except Exception: pass
    return ImageFont.load_default()

def calendar(path, cols=(), cells=(), rows=(), dim=()):
    """cols/rows/cells 를 붉게 표시한 달력. dim 은 흐리게. 좌표는 (열,행) 0부터."""
    S, B = 640, 4
    big = Image.new('RGB', (S * B, S * B), 'white')
    d = ImageDraw.Draw(big)
    L, T = int(S * .07) * B, int(S * .17) * B
    CW, CH = int(S * .123) * B, int(S * .108) * B
    RED, GREY, INK, SOFT = (214, 62, 74), (150, 152, 160), (34, 36, 42), (246, 232, 233)
    fh, fn = _font(int(CW * .38)), _font(int(CW * .42))
    # 위쪽 붉은 띠 — 달 이름 대신 글자 없는 고리 두 개 (글자를 안 쓰면 깨질 것도 없다)
    d.rounded_rectangle([L - CW // 3, T - int(CH * 1.45), L + CW * 7 + CW // 3, T - int(CH * .35)],
                        radius=CH // 3, fill=RED)
    for i in (2, 5):
        cx = L + CW * i + CW // 2
        d.ellipse([cx - CW // 8, T - int(CH * 1.95), cx + CW // 8, T - int(CH * 1.25)],
                  outline=(120, 130, 145), width=B * 3)
    for c in range(7):                                     # 요일 머리글
        x = L + CW * c
        col = RED if c >= 5 else GREY
        w = d.textlength(CAL_H[c], font=fh)
        d.text((x + (CW - w) / 2, T - int(CH * 1.12)), CAL_H[c], font=fh, fill=(255, 255, 255)
               if True else col)
    n = 1
    for r in range(5):
        for c in range(7):
            x, y = L + CW * c, T + CH * r
            on = (c in cols) or (r in rows) or ((c, r) in cells)
            off = (c, r) in dim
            if on:
                d.rounded_rectangle([x + B, y + B, x + CW - B, y + CH - B], radius=CH // 4, fill=SOFT)
            t = str(n)
            w = d.textlength(t, font=fn)
            fill = RED if on else (200, 202, 208) if off else (INK if c < 5 else (120, 122, 130))
            d.text((x + (CW - w) / 2, y + CH * .28), t, font=fn, fill=fill)
            n += 1
    for c in cols:                                         # 세로줄 통째 표시
        d.rounded_rectangle([L + CW * c + B, T + B, L + CW * (c + 1) - B, T + CH * 5 - B],
                            radius=CH // 4, outline=RED, width=B * 3)
    for r in rows:
        d.rounded_rectangle([L + B, T + CH * r + B, L + CW * 7 - B, T + CH * (r + 1) - B],
                            radius=CH // 4, outline=RED, width=B * 3)
    for (c, r) in cells:
        d.ellipse([L + CW * c + CW * .12, T + CH * r + CH * .02,
                   L + CW * c + CW * .88, T + CH * r + CH * .96], outline=RED, width=B * 4)
    big.resize((S, S), Image.LANCZOS).save(path, 'WEBP', quality=90)

# 어느 그림을 어떻게 그릴지 (열은 0=월 … 5=토, 6=일)
CAL = {
    'd56-lich':    {},                                     # 달력 그 자체
    'd04-hom-nay': {'cells': [(2, 2)]},                     # 오늘 — 가운데 한 칸에 동그라미
    'd06-mai':     {'cells': [(3, 2)], 'dim': [(2, 2)]},    # 내일 — 오늘은 흐리게, 다음 칸에 동그라미
    'd10-hom-qua': {'cells': [(1, 2)], 'dim': [(2, 2)]},    # 어제
    'd10-tuan':    {'rows': [2]},                           # 주 — 한 줄 통째
    'x-cuoi-tuan': {'cols': [5, 6]},                        # 주말 — 토·일 두 줄
    'd10-thu-hai': {'cols': [0]}, 'x-thu-ba': {'cols': [1]}, 'x-thu-tu': {'cols': [2]},
    'x-thu-nam':   {'cols': [3]}, 'x-thu-sau': {'cols': [4]}, 'x-thu-bay': {'cols': [5]},
    'd10-chu-nhat': {'cols': [6]},
    'x-thang':     {'rows': [0, 1, 2, 3, 4]},              # 달 — 한 달 통째
    'x-hom-kia':   {'cells': [(0, 2)], 'dim': [(1, 2), (2, 2)]},   # 그저께
    'x-ngay-cong': {'cells': [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1),
                              (0, 2), (1, 2), (2, 2)]},    # 근무일수 — 나온 날들
    'x-dat-phong': {'cells': [(4, 3)]},                     # 예약 — 앞날 하나
    'x-nam-moi':   {'cells': [(0, 0)]},                     # 새해 — 첫 칸
}


# ── 셈 기호 ─────────────────────────────────────────────────────────
# 더하기·빼기·곱하기·나누기·같다. 생성 모델은 기호와 개수를 늘 틀린다
# (곱하기 그림에 "1:1==4·=" 같은 것이 박혀 나왔다). 그래서 직접 그린다.
def _sym(d, kind, cx, cy, r, col=(214, 62, 74)):
    t = max(6, r // 3)
    if kind in '+x=':
        pass
    if kind == '+':
        d.rectangle([cx - r, cy - t, cx + r, cy + t], fill=col)
        d.rectangle([cx - t, cy - r, cx + t, cy + r], fill=col)
    elif kind == '-':
        d.rectangle([cx - r, cy - t, cx + r, cy + t], fill=col)
    elif kind == 'x':
        for a in (45, -45):
            import math as _m
            dx, dy = _m.cos(_m.radians(a)) * r, _m.sin(_m.radians(a)) * r
            d.line([cx - dx, cy - dy, cx + dx, cy + dy], fill=col, width=t * 2)
    elif kind == '/':                       # 나누기 — 점이 막대에 붙으면 더하기처럼 보인다
        t2 = int(t * .72)
        d.rectangle([cx - r, cy - t2, cx + r, cy + t2], fill=col)
        for k in (-1, 1):
            cy2 = cy + k * r * .78
            d.ellipse([cx - t2, cy2 - t2, cx + t2, cy2 + t2], fill=col)
    elif kind == '=':
        for k in (-1, 1):
            d.rectangle([cx - r, cy + k * r * .45 - t, cx + r, cy + k * r * .45 + t], fill=col)

def math_sheet(path, left, kind, right, cross=0):
    """왼쪽 사과 n개 · 기호 · 오른쪽 사과 m개. cross 개는 오른쪽에서 X 표시(빼기)."""
    S, B = 640, 4
    big = Image.new('RGB', (S * B, S * B), 'white')
    d = ImageDraw.Draw(big)
    RB = int(S * .058) * B
    def group(n, cx, cy, xed=0):
        per = 3 if n > 4 else 2
        rows = (n + per - 1) // per
        R = int(RB * (0.78 if n > 4 else 1))       # 많으면 조금 작게 — 기호와 겹치지 않게
        for i in range(n):
            r_, c_ = i // per, i % per
            inrow = min(per, n - r_ * per)
            x = cx + (c_ - (inrow - 1) / 2) * R * 2.4
            y = cy + (r_ - (rows - 1) / 2) * R * 2.4
            apple(d, x, y, R)
            if i >= n - xed:
                w = R // 3
                for a in (1, -1):
                    d.line([x - R * .8, y - a * R * .8, x + R * .8, y + a * R * .8],
                           fill=(120, 122, 130), width=w)
    cy = S * B // 2
    group(left, S * B * .26, cy)
    _sym(d, kind, S * B * .5, cy, int(S * .052) * B)
    group(right, S * B * .74, cy, cross)
    big.resize((S, S), Image.LANCZOS).save(path, 'WEBP', quality=90)

def grid_sheet(path, cols, rows):
    """작은 사과를 cols×rows 로 빽빽하게 (백 = 10×10)."""
    S, B = 640, 4
    big = Image.new('RGB', (S * B, S * B), 'white')
    d = ImageDraw.Draw(big)
    R = int(S * .9 / max(cols, rows) / 2.35) * B
    w, h = (cols - 1) * R * 2.35, (rows - 1) * R * 2.35
    for r_ in range(rows):
        for c_ in range(cols):
            apple(d, S * B / 2 - w / 2 + c_ * R * 2.35, S * B / 2 - h / 2 + r_ * R * 2.35, R)
    big.resize((S, S), Image.LANCZOS).save(path, 'WEBP', quality=90)

MATH = {
    'd102-cong': dict(left=3, kind='+', right=2),        # 더하다
    'd102-tru':  dict(left=5, kind='-', right=2, cross=2),   # 빼다 — 빠지는 둘에 X
    'd67-nhan':  dict(left=3, kind='x', right=4),        # 곱하다
    'd67-chia':  dict(left=6, kind='/', right=2),        # 나누다
    'd102-bang': dict(left=3, kind='=', right=3),        # 같다
}


# ── 방향 화살표 ────────────────────────────────────────────────
# 확산 모델은 좌우를 못 가린다. "pointing to the LEFT" 이라고 못 박아도 오른쪽을 그렸다.
# 개수·국기와 같은 부류다 — 정확해야 하는 것은 코드로 그린다.
ARROW = {'d39-ben-trai': 'left', 'd39-ben-phai': 'right',
         'x-tren': 'up', 'x-duoi': 'down', 'd42-di-thang': 'up'}
TURN = {'d42-re-trai': 'left', 'd42-re-phai': 'right'}   # 좌회전·우회전 — 좌우가 뜻의 전부

def turn(path, side):
    """ㄱ자로 꺾이는 회전 화살표 — 아래에서 올라와 옆으로 꺾인다."""
    im = Image.new('RGB', (S, S), BG)
    d = ImageDraw.Draw(im)
    fill, line = (108, 164, 214), (52, 96, 142)
    sw, hw = S * .105, S * .20
    cx, ty, by, hx = S * .60, S * .34, S * .84, S * .14
    pts = [(hx, ty), (hx + hw, ty - hw), (hx + hw, ty - sw),
           (cx + sw, ty - sw), (cx + sw, by), (cx - sw, by),
           (cx - sw, ty + sw), (hx + hw, ty + sw), (hx + hw, ty + hw)]
    if side == 'right':
        pts = [(S - x, y) for x, y in pts]
    d.polygon(pts, fill=fill, outline=line, width=max(4, int(S * .012)))
    im.save(path, 'WEBP', quality=88)

def arrow(path, way):
    """굵은 파스텔 화살표 하나. 앱의 다른 그림과 같은 결로, 배경과 확실히 구분되게."""
    im = Image.new('RGB', (S, S), BG)
    d = ImageDraw.Draw(im)
    fill, line = (108, 164, 214), (52, 96, 142)
    c, L, hw, sw = S / 2, S * .34, S * .20, S * .105       # 길이·머리폭·자루폭
    pts = [(c + L, c), (c + L - hw, c - hw), (c + L - hw, c - sw),
           (c - L, c - sw), (c - L, c + sw), (c + L - hw, c + sw), (c + L - hw, c + hw)]
    if way in ('left', 'up'):  pts = [(2 * c - x, y) for x, y in pts]
    if way in ('up', 'down'):  pts = [(c + (y - c), c + (x - c)) for x, y in pts]
    d.polygon(pts, fill=fill, outline=line, width=max(4, int(S * .012)))
    im.save(path, 'WEBP', quality=88)


# ── 베트남 지도 ────────────────────────────────────────────────
# 생성 모델에 맡겼더니 넷 다 **떠 있는 손**이 지도를 붙잡고 있었다(북부·남부·지방·성).
# 좌우 화살표와 같은 부류다 — 어디가 위고 어디가 아래인지가 뜻의 전부인데
# 모델은 그것을 못 지킨다. 그래서 코드로 그린다.
# 실제 국경선을 그대로 옮긴 것은 아니고, 남북이 한눈에 갈리는 **약식 지도**다.
VN_OUTLINE = [
    (.30,.06),(.44,.02),(.56,.05),(.62,.12),(.58,.19),(.50,.23),   # 북부 (홍강 삼각주)
    (.52,.30),(.58,.40),(.64,.49),(.70,.57),                        # 중부 (좁은 허리)
    (.74,.65),(.70,.74),(.58,.82),(.44,.86),(.32,.82),(.28,.74),    # 남부 (메콩 삼각주)
    (.34,.68),(.40,.60),(.38,.50),(.32,.40),(.28,.30),(.24,.18),(.24,.10),
]
NORTH = 8      # 이 점까지가 북부, 그 뒤가 남부 (허리에서 가른다)

def _vn_pts(sc=1.0, dx=0.0, dy=0.0):
    return [((x * sc + dx) * S, (y * sc + dy) * S) for x, y in VN_OUTLINE]

def vn_map(path, mode):
    """mode: 'three'(남북을 두 빛깔로) · 'north' · 'south' · 'one'(성 하나)"""
    im = Image.new('RGB', (S, S), BG)
    d = ImageDraw.Draw(im)
    pts = _vn_pts(.92, .04, .04)
    dim, hot, line = (214, 219, 224), (108, 164, 214), (70, 92, 112)
    d.polygon(pts, fill=dim, outline=line, width=max(3, int(S * .008)))
    n = len(pts)
    if mode in ('north', 'south', 'three'):
        # 허리(가운데)를 가로지르는 선으로 남북을 가른다
        cut = (pts[NORTH][1] + pts[n - NORTH][1]) / 2
        box_n = [(0, 0), (S, 0), (S, cut), (0, cut)]
        box_s = [(0, cut), (S, cut), (S, S), (0, S)]
        for which, box, col in (('north', box_n, hot), ('south', box_s, hot)):
            if mode == which or mode == 'three':
                lay = Image.new('RGB', (S, S), BG)
                ld = ImageDraw.Draw(lay)
                ld.polygon(pts, fill=col if mode != 'three' else
                           ((124, 178, 224) if which == 'north' else (236, 160, 120)))
                msk = Image.new('L', (S, S), 0)
                ImageDraw.Draw(msk).polygon(box, fill=255)
                im.paste(lay, (0, 0), msk)
        d.polygon(pts, outline=line, width=max(3, int(S * .008)))
    if mode == 'one':                                  # 성 하나만 콕
        cx, cy, r = S * .46, S * .30, S * .075
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=hot, outline=line, width=4)
    im.save(path, 'WEBP', quality=88)

VNMAP = {'x-mien': 'three', 'x-mien-bac': 'north', 'x-mien-nam': 'south', 'x-tinh': 'one'}


# ── 기호 하나짜리 ─────────────────────────────────────────────────
# 확산 모델은 X 와 물음표를 붓으로 문지른 것처럼 그린다(획이 굽고 굵기가 들쭉날쭉하다).
# 뜻이 **모양 자체**인 그림은 자로 그어야 한다 (대표님 지적, 2026-08-29).
def cross_mark(path, col=(214, 62, 74)):
    """없다·아니다 — 곧은 X.

    크기는 옆칸 '있다'(초록 체크 x-cos)에 맞춘다 (대표님 지적, 2026-08-29).
    처음엔 그림 폭의 70%·잉크 22% 로 그려서 체크(35%·3.2%)보다 두 배 컸다.
    같은 줄에 나란히 놓이는 그림은 크기가 비슷해야 한 벌로 보인다.
    끝을 둥글게 하는 것도 체크와 맞춘 것이다."""
    im = Image.new('RGB', (S, S), BG)
    big = Image.new('RGB', (S * 3, S * 3), BG)
    dr = ImageDraw.Draw(big)
    c = S * 3 // 2
    r = S * 3 * 0.175 * 0.72          # 체크와 같은 35% 크기
    w = int(S * 3 * 0.052)            # 획 굵기도 체크와 맞춘다
    for a, b in (((-1, -1), (1, 1)), ((-1, 1), (1, -1))):
        dr.line([c + a[0] * r, c + a[1] * r, c + b[0] * r, c + b[1] * r],
                fill=col, width=w, joint='curve')
        for e in (a, b):              # 끝을 둥글게
            dr.ellipse([c + e[0] * r - w / 2, c + e[1] * r - w / 2,
                        c + e[0] * r + w / 2, c + e[1] * r + w / 2], fill=col)
    big.resize((S, S), Image.LANCZOS).save(path, 'WEBP', quality=92)


def question_mark(path, col=(58, 68, 64)):
    """어느·무엇 — 물음표 하나. 진짜 글꼴로 찍는다(모델이 그리면 늘 뭉개진다)."""
    im = Image.new('RGB', (S, S), BG)
    dr = ImageDraw.Draw(im)
    f = _font(int(S * 0.72))
    try:
        l, t, rr, b = dr.textbbox((0, 0), '?', font=f)
        dr.text(((S - (rr - l)) / 2 - l, (S - (b - t)) / 2 - t), '?', font=f, fill=col)
    except Exception:
        dr.text((S * 0.36, S * 0.12), '?', fill=col)
    im.save(path, 'WEBP', quality=92)


# x-nao(어느)·x-the-nao(어떻다)는 x-gi(무엇)의 말풍선 물음표를 **같이 쓴다** (대표님 지시).
# x-gi 는 손대지 않는다 — 이미 좋은 그림이다. question_mark 는 이제 안 쓰지만 남겨 둔다.
def bars(path, hi):
    """정도를 나타내는 막대 — **한 칸만 색을 넣는다** (대표님 지시, 2026-08-29).

    hi='max' 면 가장 높은 칸에, hi='min' 이면 가장 낮은 칸에 색을 넣는다.
    나머지는 모두 같은 회색이다. 전에는 네 칸이 다 다른 색이라 **무엇을 가리키는지**
    가 안 보였다. 색은 뜻을 나르는 자리에만 쓴다.
    '매우(rất)'와 '조금(một chút)'이 같은 그림에 색만 다른 짝이 되게 했다 —
    두 낱말이 같은 잣대의 양 끝이라는 것이 한눈에 보인다."""
    im = Image.new('RGB', (S, S), BG)
    big = Image.new('RGB', (S * 3, S * 3), BG)
    dr = ImageDraw.Draw(big)
    W = S * 3
    n, gap = 4, W * 0.035
    bw = (W * 0.52 - gap * (n - 1)) / n
    x0, base = W * 0.24, W * 0.72
    heights = [0.13, 0.22, 0.31, 0.40]
    pick = n - 1 if hi == 'max' else 0
    ON, OFF = (94, 178, 166), (214, 219, 215)
    for i, h in enumerate(heights):
        x, top = x0 + i * (bw + gap), base - W * h
        dr.rounded_rectangle([x, top, x + bw, base], radius=W * 0.012,
                             fill=ON if i == pick else OFF)
    dr.line([x0 - gap, base, x0 + n * (bw + gap), base], fill=(150, 158, 152), width=int(W * 0.008))
    big.resize((S, S), Image.LANCZOS).save(path, 'WEBP', quality=92)


def kr_bubble(path):
    """한국어 — 태극과 4괘를 **말풍선 안에** (대표님 지시).
       베트남어 그림(d05-tieng-viet)이 '국기 = 말풍선' 꼴이라 짝을 맞춘다."""
    im = Image.new('RGB', (S, S), BG)
    big = Image.new('RGB', (S * 3, S * 3), BG)
    dr = ImageDraw.Draw(big)
    W = S * 3
    L, T, R, B = W * 0.13, W * 0.17, W * 0.87, W * 0.70
    dr.rounded_rectangle([L, T, R, B], radius=W * 0.13, fill=(255, 255, 255),
                         outline=(58, 68, 64), width=int(W * 0.022))
    tx = W * 0.34                                  # 꼬리
    dr.polygon([(tx, B - W * 0.01), (tx + W * 0.10, B - W * 0.01), (tx + W * 0.02, B + W * 0.13)],
               fill=(255, 255, 255), outline=(58, 68, 64))
    dr.polygon([(tx + W * 0.008, B - W * 0.03), (tx + W * 0.092, B - W * 0.03),
                (tx + W * 0.02, B + W * 0.10)], fill=(255, 255, 255))
    cx, cy, r = (L + R) / 2, (T + B) / 2, (B - T) * 0.30
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(0, 71, 160))
    dr.pieslice([cx - r, cy - r, cx + r, cy + r], 33.69 - 180, 33.69, fill=(205, 46, 58))
    a = math.radians(33.69)
    hx, hy = math.cos(a) * r / 2, math.sin(a) * r / 2
    dr.ellipse([cx - hx - r / 2, cy - hy - r / 2, cx - hx + r / 2, cy - hy + r / 2], fill=(205, 46, 58))
    dr.ellipse([cx + hx - r / 2, cy + hy - r / 2, cx + hx + r / 2, cy + hy + r / 2], fill=(0, 71, 160))
    BARS = {'건': [1, 1, 1], '곤': [0, 0, 0], '감': [0, 1, 0], '이': [1, 0, 1]}
    bl, bw2, gp = r * 0.75, r * 0.13, r * 0.07
    def gua(name, ang):
        rad = math.radians(ang)
        ox, oy = cx + math.cos(rad) * r * 1.75, cy + math.sin(rad) * r * 1.75
        for i, solid in enumerate(BARS[name]):
            off = (i - 1) * (bw2 + gp)
            px, py = ox + math.cos(rad) * off, oy + math.sin(rad) * off
            dx, dy = -math.sin(rad), math.cos(rad)
            def seg(t0, t1):
                dr.polygon([(px + dx * t0 - math.cos(rad) * bw2 / 2, py + dy * t0 - math.sin(rad) * bw2 / 2),
                            (px + dx * t1 - math.cos(rad) * bw2 / 2, py + dy * t1 - math.sin(rad) * bw2 / 2),
                            (px + dx * t1 + math.cos(rad) * bw2 / 2, py + dy * t1 + math.sin(rad) * bw2 / 2),
                            (px + dx * t0 + math.cos(rad) * bw2 / 2, py + dy * t0 + math.sin(rad) * bw2 / 2)],
                           fill=(0, 0, 0))
            if solid: seg(-bl / 2, bl / 2)
            else: seg(-bl / 2, -bl * 0.09); seg(bl * 0.09, bl / 2)
    gua('건', 180 + 33.69); gua('감', -33.69); gua('이', 180 - 33.69); gua('곤', 33.69)
    big.resize((S, S), Image.LANCZOS).save(path, 'WEBP', quality=92)


BARS_IMG = {'x-rat': 'max', 'x-mot-chut': 'min'}   # 매우 · 조금

SYM = {'x-khong': cross_mark}


def word_mark(path, text, col=(58, 68, 64)):
    """뜻이 **낱말 하나**인 기능어 — 글자를 진짜 글꼴로 찍는다.

    '그리고 · ~도 · 아주' 같은 말은 그림으로 만들면 억지가 된다(대표님 지시:
    억지로 만들 필요 없다, 심플하고 직관적이면 된다). 짧은 영어 한 낱말이
    한국인에게 가장 빨리 읽힌다. 확산 모델은 글자를 늘 뭉개므로 여기서 찍는다."""
    im = Image.new('RGB', (S, S), BG)
    dr = ImageDraw.Draw(im)
    sz = int(S * 0.40)
    while sz > 10:
        f = _font(sz)
        l, t, r, b = dr.textbbox((0, 0), text, font=f)
        if r - l <= S * 0.78:
            break
        sz -= 6
    dr.text(((S - (r - l)) / 2 - l, (S - (b - t)) / 2 - t), text, font=f, fill=col)
    im.save(path, 'WEBP', quality=92)


# 기능어 — 짧은 영어 한 낱말로 (대표님 지시)
# x-lam(아주)은 x-rat(매우)의 막대를 같이 쓴다 — 같은 뜻이라 글자보다 그림이 낫다
WORDMK = {'x-va': 'and', 'x-cung': 'also', 'd2-cua': 'of', 'x-o': 'at'}

if __name__ == '__main__':
    made = 0
    for name, n in NUM.items():
        count_sheet(n, IMG / f'{name}.webp'); made += 1
    for name in ['d03-viet-nam', 'd03-tieng-viet']:
        p = IMG / f'{name}.webp'
        if p.exists() or name == 'd03-viet-nam': flag_vn(p); made += 1
    for name in ['d03-han-quoc', 'd05-tieng-han']:
        p = IMG / f'{name}.webp'
        if name == 'd03-han-quoc': flag_kr(p); made += 1   # d05-tieng-han 은 말풍선판을 따로 그린다
    for name, how in CAL.items():
        calendar(IMG / f'{name}.webp', **how); made += 1
    for name, how in MATH.items():
        math_sheet(IMG / f'{name}.webp', **how); made += 1
    grid_sheet(IMG / 'd102-tram.webp', 10, 10); made += 1      # 백 = 열 줄 열 개
    for name, mode in VNMAP.items():
        vn_map(IMG / f'{name}.webp', mode); made += 1
    for name, way in ARROW.items():
        arrow(IMG / f'{name}.webp', way); made += 1
    for name, side in TURN.items():
        turn(IMG / f'{name}.webp', side); made += 1
    for name, fn in SYM.items():
        fn(IMG / f'{name}.webp'); made += 1
    for name, hi in BARS_IMG.items():
        bars(IMG / f'{name}.webp', hi); made += 1
    kr_bubble(IMG / 'd05-tieng-han.webp'); made += 1
    for name, txt in WORDMK.items():
        word_mark(IMG / f'{name}.webp', txt); made += 1
    print(f'직접 그린 그림 {made}장')
