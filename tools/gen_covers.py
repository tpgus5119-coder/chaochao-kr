#!/usr/bin/env python3
"""챕터 **표지**를 만든다 — 203장(한국어 78 · 베트남어 100 · 기사 25).

  python3 tools/gen_covers.py          → 없는 것만
  python3 tools/gen_covers.py --force  → 전부 다시

**새로 굽지 않는다.** 그 챕터가 이미 가진 낱말 그림 셋을 골라 얹고,
아래 띠에 제목을 적는다. 만드는 데 몇 초면 되고, 표지와 내용이 어긋날 일도 없다.

글자는 **모델이 아니라 우리가 PIL 로** 얹는다. 확산 모델은 한글·베트남어를
늘 깨뜨린다(그림 1,849장 중 14장이 그 흔적이다). 진짜 글꼴로 적으면 안 깨진다.
그래서 '자기소개'·'재는 말' 같은 **추상적인 주제도 표지가 된다** —
그림이 애매해도 글자가 뜻을 붙잡아 준다.

낱말 그림은 하얀 바탕 정사각, 표지는 **가로로 넓고 어두운 띠**가 있다.
넘길 때 장이 바뀐 것이 한눈에 보이라고 일부러 다르게 만든다.
"""
import argparse
import json
import pathlib
import re
import zlib

from PIL import Image, ImageDraw, ImageFont

R = pathlib.Path(__file__).resolve().parent.parent
IMG = R / "img"
FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"          # 한글
# 애플 고딕에는 **베트남어 글자가 없다** — Tự giới thiệu 가 T□ gi□i thi□u 로 깨졌다.
# 성조 붙은 라틴 글자는 따로 이 글꼴로 적는다.
FONT_VI = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
SETS = [("data/ko_days.json", "cvk"), ("data/days.json", "cvv"), ("data/news_days.json", "cvn")]

W, H, BAND = 768, 432, 118
PAD, GAP = 26, 14
# 과마다 바탕색을 조금씩 달리한다 — 넘길 때 장이 바뀐 것이 색으로도 보인다.
TINTS = [(238, 240, 244), (243, 238, 232), (234, 241, 237), (241, 236, 242), (240, 240, 232)]
INK, DIM, GOLD, DARK = (245, 245, 242), (168, 172, 180), (226, 160, 74), (23, 25, 30)


def fit(d, text, size, maxw, path=FONT):
    while size > 13:
        f = ImageFont.truetype(path, size)
        if d.textlength(text, font=f) <= maxw:
            return f
        size -= 2
    return ImageFont.truetype(path, 13)


def cover(pics, ko, vi, no, tint):
    im = Image.new("RGB", (W, H), tint)
    top = H - BAND
    # 그림 셋을 나란히 — 있는 만큼만. 한 장뿐이면 크게 하나.
    n = max(1, min(3, len(pics)))
    box_w = (W - PAD * 2 - GAP * (n - 1)) // n
    box_h = top - PAD * 2
    side = min(box_w, box_h)
    x = (W - (side * n + GAP * (n - 1))) // 2
    y = PAD + (box_h - side) // 2
    for p in pics[:n]:
        try:
            th = Image.open(p).convert("RGB").resize((side, side), Image.LANCZOS)
        except Exception:
            continue
        m = Image.new("L", (side, side), 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, side - 1, side - 1], radius=18, fill=255)
        im.paste(th, (x, y), m)
        x += side + GAP

    d = ImageDraw.Draw(im)
    d.rectangle([0, top, W, H], fill=DARK)
    d.rectangle([0, top, W, top + 3], fill=GOLD)
    fno = ImageFont.truetype(FONT, 21)
    d.text((PAD + 4, top + 20), no, font=fno, fill=GOLD)
    wno = d.textlength(no, font=fno) + 14
    d.text((PAD + 4 + wno, top + 15), ko, font=fit(d, ko, 34, W - PAD * 2 - wno), fill=INK)
    if vi:
        d.text((PAD + 4, top + 62), vi,
               font=fit(d, vi, 20, W - PAD * 2, FONT_VI), fill=DIM)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    made = skipped = 0
    for fn, pre in SETS:
        d = json.load(open(R / fn, encoding="utf-8"))
        days = d["days"] if isinstance(d, dict) and "days" in d else d
        for i, day in enumerate(days, 1):
            no = str(day.get("day", i))
            # 기사 세트의 day 는 'Nno=43920' 꼴이라 그대로 쓰면 파일 이름이 못 쓰게 된다.
            # 파일 이름은 안전한 글자만 쓰고, 화면에 적을 번호는 따로 만든다.
            safe = re.sub(r"[^0-9A-Za-z]+", "", no) or str(i)
            name = f"{pre}-{safe}.webp"
            shown = no if re.fullmatch(r"[\d.]+", no) else str(i)
            day["cover"] = name
            out = IMG / name
            if out.exists() and not a.force:
                skipped += 1
                continue
            ws = day.get("words", [])
            # 그날 그림 중 셋을 고른다 — 늘 앞의 셋이 아니라 챕터마다 다르게(씨앗 고정).
            pics = [IMG / w["img"] for w in ws if w.get("img") and (IMG / w["img"]).exists()]
            if len(pics) > 3:
                k = zlib.crc32(name.encode())
                pics = [pics[k % len(pics)], pics[(k // 7) % len(pics)], pics[(k // 53) % len(pics)]]
                pics = list(dict.fromkeys(pics))
            # theme 이 파일마다 다르다 — 한국어 과정은 {ko,vi}, 나머지는 그냥 글자다.
            th = day.get("theme")
            if isinstance(th, dict):
                ko, vi = th.get("ko") or "", th.get("vi") or ""
            else:
                ko, vi = (th or day.get("title") or f"{no}과"), ""
            cover(pics, ko, vi, shown, TINTS[i % len(TINTS)]).save(
                out, "WEBP", quality=84, method=6)
            made += 1
        (R / fn).write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {fn}")
    print(f"표지 만든 것 {made}장 · 이미 있던 것 {skipped}장 · 모든 챕터에 cover 칸을 적었다")


if __name__ == "__main__":
    main()
