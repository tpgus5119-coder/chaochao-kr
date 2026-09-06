#!/usr/bin/env python3
"""낱말과 **이미 구워 둔 그림**을 다시 이어 붙인다.

  python3 tools/img_relink.py           → data/days.json · ko_days.json 에 img 채움
  python3 tools/img_relink.py --dry     → 세기만

왜 필요한가: `assemble.py` 는 커리큘럼 원본(tools/b*.py)에서 days.json 을 **다시 만든다.**
그런데 그림 이름 가운데 일부는 원본이 아니라 나중 도구가 붙인 것이라(색·무늬는
draw_words.py, 기능어 그림은 손으로) 다시 만들면 그 자리만 비어 버린다.
실제로 조립기를 한 번 돌리자 25개가 비었다 — 그림 파일은 img/ 에 그대로 있는데도.

**그림을 새로 굽지 않는다. 지우지도 않는다.** (사용자 지시: 좋은 그림은 건드리지 말 것)
파일 이름 규칙 `d{강번호}-{낱말}.webp` 로 이미 있는 파일을 찾아 이름만 도로 적는다.
강 번호는 `1` `01` `42.5→425` 세 가지로 적혀 있어 셋 다 본다.
"""
import json
import pathlib
import sys
import unicodedata

R = pathlib.Path(__file__).resolve().parent.parent
IMG = R / "img"


def slug(vi):
    s = unicodedata.normalize("NFD", vi)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.replace("đ", "d").replace("Đ", "d").lower().replace(" ", "-")


def keys(day, vi):
    n = str(day).replace(".", "")                 # 42.5 → 425
    g = slug(vi)
    return [f"d{n}-{g}.webp", f"d{int(float(day)):02d}-{g}.webp" if float(day).is_integer()
            else f"d{n}-{g}.webp", f"x-{g}.webp"]


def main():
    dry = "--dry" in sys.argv
    have = {p.name for p in IMG.glob("*.webp")}
    used = set()
    for f in ("days.json", "ko_days.json"):
        p = R / "data" / f
        d = json.loads(p.read_text(encoding="utf-8"))
        for day in d["days"]:
            for w in day.get("words", []):
                if w.get("img"):
                    used.add(w["img"])
    total = fixed = 0
    for f in ("days.json", "ko_days.json"):
        p = R / "data" / f
        d = json.loads(p.read_text(encoding="utf-8"))
        got = []
        for day in d["days"]:
            for w in day.get("words", []):
                if w.get("img"):
                    continue
                total += 1
                for k in keys(day["day"], w["vi"]):
                    # 남이 쓰고 있는 그림은 뺏지 않는다 — 한 그림을 둘이 나눠 쓰면
                    # 둘 중 하나는 반드시 엉뚱한 그림을 보게 된다
                    if k in have and k not in used:
                        w["img"] = k
                        used.add(k)
                        got.append((day["day"], w["vi"], k))
                        fixed += 1
                        break
        if got and not dry:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{f}: 그림 없던 낱말 중 {len(got)}개를 다시 이었다")
        for x in got[:6]:
            print(f"   {x[0]} {x[1]} → {x[2]}")
    print(f"\n합계 — 그림 없는 낱말 {total} · 이어 붙임 {fixed} · 아직 없음 {total - fixed}"
          + (" (돌려보기만 함)" if dry else ""))


if __name__ == "__main__":
    main()
