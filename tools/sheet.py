#!/usr/bin/env python3
"""그림을 격자로 붙여 한 장씩 본다 — 검수용. 이름을 밑에 적어 어느 그림인지 바로 알게.
사용: python3 tools/sheet.py <목록파일> <내보낼폴더> [칸수]"""
import sys, pathlib
from PIL import Image, ImageDraw, ImageFont
R = pathlib.Path(__file__).resolve().parent.parent
names = [l.strip() for l in pathlib.Path(sys.argv[1]).read_text().splitlines() if l.strip()]
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
N = int(sys.argv[3]) if len(sys.argv) > 3 else 4          # N×N
CELL, LAB = 300, 26
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 17)
except Exception: F = ImageFont.load_default()
sheets = 0
for s in range(0, len(names), N * N):
    grp = names[s:s + N * N]
    W = N * CELL; H = ((len(grp) + N - 1) // N) * (CELL + LAB)
    sheet = Image.new('RGB', (W, H), 'white'); d = ImageDraw.Draw(sheet)
    for i, nm in enumerate(grp):
        p = R / 'img' / f'{nm}.webp'
        x, y = (i % N) * CELL, (i // N) * (CELL + LAB)
        if p.exists():
            sheet.paste(Image.open(p).convert('RGB').resize((CELL, CELL)), (x, y))
        d.rectangle([x, y + CELL, x + CELL, y + CELL + LAB], fill='#111')
        d.text((x + 5, y + CELL + 4), f'{s+i+1}. {nm}', font=F, fill='#fff')
    f = out / f'sheet{sheets:02d}.png'; sheet.save(f); sheets += 1
print(f'{sheets}장 · 그림 {len(names)}개 → {out}')
