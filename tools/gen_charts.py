#!/usr/bin/env python3
"""TOPIK II 듣기 [3번] 도표 문항에 쓸 막대그래프를 SVG 로 그린다.

왜 필요했나:
  설계도의 [1~3] 발문은 "가장 알맞은 그림 **또는 그래프**를 고르십시오"다.
  우리에게는 사진뿐이라 그래프 자리를 채울 수 없었다. 그래서 직접 그린다.
  들려준 수치대로 그린 것 하나와, **차례만 바꾼** 것 셋을 낸다 —
  눈으로 견주지 않으면 못 고르게 하려는 것이다(그래야 도표 읽기를 재게 된다).

왜 SVG 인가:
  글자와 선뿐이라 파일이 1~2KB다. 사진 한 장의 1/50이라 배터리·용량에 부담이 없다.
  확대해도 안 깨져서 작은 화면에서도 값을 읽을 수 있다.

색은 쓰지 않는다. 막대 넷을 색으로 나누면 색각이 다른 사람이 못 읽는다.
높이와 값만으로 읽히게 그렸고, 배경은 흰색으로 고정했다 —
어두운 화면에서도 그림 안쪽은 그대로 보여야 하기 때문이다.

쓰기:  python3 tools/gen_charts.py     (img/chart-*.svg 를 다시 만든다)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ko_t2_listen as L2

IMG = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img")

W, H = 260, 190
BASE, TOP = 150, 40          # 막대가 서는 바닥선과 100% 자리
BW, GAP = 38, 20             # 막대 너비·사이


def names(i):
    """i번째 도표의 보기 넷 파일 이름. 0번이 정답이다."""
    return [f"chart-{i + 1}-{j}.svg" for j in range(4)]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def wrap(label):
    """긴 항목 이름은 두 줄로 나눈다. 띄어쓰기가 없으면 가운데서 자른다."""
    if len(label) <= 6:
        return [label]
    if " " in label:
        a, _, b = label.partition(" ")
        return [a, b]
    m = len(label) // 2
    return [label[:m], label[m:]]


def svg(title, items, vals):
    left = (W - (len(vals) * BW + (len(vals) - 1) * GAP)) / 2
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           f'<text x="{W/2}" y="18" text-anchor="middle" font-size="11" '
           f'font-family="sans-serif" fill="#222">{esc(title)}</text>',
           f'<line x1="10" y1="{BASE}" x2="{W-10}" y2="{BASE}" stroke="#333" stroke-width="1"/>']
    for k, v in enumerate(vals):
        x = left + k * (BW + GAP)
        h = (BASE - TOP) * v / 100.0
        out.append(f'<rect x="{x:.1f}" y="{BASE-h:.1f}" width="{BW}" height="{h:.1f}" '
                   f'fill="#e9e9e9" stroke="#333" stroke-width="1"/>')
        out.append(f'<text x="{x+BW/2:.1f}" y="{BASE-h-4:.1f}" text-anchor="middle" '
                   f'font-size="10" font-family="sans-serif" fill="#222">{v}%</text>')
        for n, line in enumerate(wrap(items[k])):
            out.append(f'<text x="{x+BW/2:.1f}" y="{BASE+13+n*11}" text-anchor="middle" '
                       f'font-size="9" font-family="sans-serif" fill="#444">{esc(line)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def render_all(quiet=True):
    os.makedirs(IMG, exist_ok=True)
    made = 0
    for i, (title, _lines, items, right, wrongs, _why) in enumerate(L2.T2_CHART):
        for j, vals in enumerate([right] + list(wrongs)):
            path = os.path.join(IMG, names(i)[j])
            body = svg(title, items, vals)
            old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
            if old != body:                       # 안 바뀐 파일은 건드리지 않는다
                open(path, "w", encoding="utf-8").write(body)
                made += 1
    if not quiet:
        print(f"도표 {len(L2.T2_CHART)}개 × 보기 4 = {len(L2.T2_CHART)*4}장 "
              f"(새로 쓴 것 {made}장) → {IMG}")
    return made


if __name__ == "__main__":
    render_all(quiet=False)


# ── 말하기 5번(자료 해석하기)에 쓰는 도표 ────────────────────────
# 여기는 보기 넷이 아니라 **한 장**이다. 응시자가 도표를 보고 말로 설명하는 문항이라
# 고를 것이 없다. 수치는 문항 재료(tools/ko_speak_topik.py)의 data 칸과 같아야 한다 —
# 도표를 못 읽는 사람도 글로 읽고 답할 수 있어야 하기 때문이다(색각·저시력 배려).
SPEAK_CHART = [
    ("chart-speak-1.svg", "외국인 근로자의 한국어 공부 방법",
     ["휴대전화 앱", "회사 교실", "학원", "혼자 책으로"], [46, 27, 18, 9]),
    ("chart-speak-2.svg", "한국에 사는 외국인이 어려워하는 것",
     ["언어", "문화 차이", "병원 이용", "집 구하기"], [41, 24, 20, 15]),
]


def render_speak(quiet=True):
    os.makedirs(IMG, exist_ok=True)
    made = 0
    for name, title, items, vals in SPEAK_CHART:
        path = os.path.join(IMG, name)
        body = svg(title, items, vals)
        old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        if old != body:
            open(path, "w", encoding="utf-8").write(body)
            made += 1
    if not quiet:
        print(f"말하기 도표 {len(SPEAK_CHART)}장 (새로 쓴 것 {made}장)")
    return made
