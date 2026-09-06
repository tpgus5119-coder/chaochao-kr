#!/usr/bin/env python3
"""한국어 과정 780낱말의 베트남어 뜻이 **그 단원에 맞는 갈래인가**를 본다.

처음에 잘못 짚었던 것 — 기록해 둔다:
  뜻풀이가 '틀린 번역'인 줄 알았다. 아니었다. 전부 국립국어원 기초사전의
  정확한 번역이다. 진짜 문제는 **동형이의어에서 다른 갈래를 집어 온 것**이다.
      주문 → câu thần chú   맞다. 다만 그건 呪文이고, 우리가 가르치려는 건 注文이다.
      가장 → người chủ gia đình  맞다. 다만 그건 家長이고, 초급에서 쓰는 건 '제일'이다.
      기관 → động cơ        맞다. 다만 그건 엔진이고, 중급 글에 나오는 건 機關이다.
  그래서 고칠 일은 '다시 번역'이 아니라 **갈래 고르기**다.

또 하나, 첫 판 검사기는 거짓 경보가 많았다:
  'mì ăn liền' vs 'mỳ ăn liền', 'tàu hỏa' vs 'tàu hoả' 를 서로 다른 뜻으로 셌다.
  베트남어는 같은 소리를 두 가지로 적는 일이 흔하다(i/y, 성조 부호 자리).
  그래서 견줄 때는 그 차이를 지운다.

내는 것
  갈래하나   사전에 갈래가 하나뿐 — 고를 일이 없다
  갈래여럿   갈래가 둘 이상인데 우리가 그중 하나를 골랐다 → **사람이 확인할 목록**
  못찾음     우리 뜻이 어느 갈래와도 안 겹친다 → 표기 차이인지 진짜 어긋남인지 봐야 한다
  사전없음   사전에 없는 낱말(외래어·합성어) — 지어내지 않고 그냥 둔다

실행: python3 tools/ko_gloss_audit.py            # 요약
      python3 tools/ko_gloss_audit.py --list     # 갈래여럿 전체를 갈래와 함께
"""
import json
import pathlib
import re
import sys
import unicodedata
from collections import Counter

R = pathlib.Path(__file__).resolve().parent.parent
DAYS = R / "data" / "ko_days.json"
GLOSS = R / "data" / "_ko_vi_gloss.json"


def loose(s):
    """베트남어를 느슨하게 견주는 꼴로.

    성조 부호와 모자 부호를 **떼고**, i 와 y 를 같게 본다.
    'mì ăn liền' 과 'mỳ ăn liền', 'tàu hỏa' 와 'tàu hoả' 는 같은 말이다.
    이걸 안 지우면 멀쩡한 뜻이 죄다 '어긋남'으로 잡힌다(첫 판에서 34개가 그랬다).
    """
    s = unicodedata.normalize("NFD", str(s or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("y", "i")
    return re.sub(r"[^a-z0-9 ]+", " ", s).strip()


def pieces(s):
    """'giá cả, giá' → {'gia ca','gia'} — 쉼표·세미콜론으로 갈라 조각끼리 견준다."""
    return {p.strip() for p in re.split(r"[,;]", str(s or "")) if loose(p).strip()
            for p in [loose(p)]}


def main():
    show = "--list" in sys.argv
    days = json.loads(DAYS.read_text(encoding="utf-8"))
    gl = json.loads(GLOSS.read_text(encoding="utf-8"))

    by_head = {}
    for k, v in gl.items():
        by_head.setdefault(re.sub(r"\d+$", "", k), []).append((k, v))

    kinds, multi, missed = Counter(), [], []
    for d in days["days"]:
        for w in d["words"]:
            ko, vi = w["ko"].strip(), w.get("vi", "")
            cands = by_head.get(ko) or []
            if not cands:
                kinds["사전없음"] += 1
                continue
            ours = pieces(vi)
            hit = [k for k, v in cands if ours & pieces(v.get("vi"))]
            if not hit:
                kinds["못찾음"] += 1
                missed.append((d["day"], ko, vi, cands))
            elif len(cands) == 1:
                kinds["갈래하나"] += 1
            else:
                kinds["갈래여럿"] += 1
                multi.append((d["day"], ko, vi, hit, cands))

    print(f"낱말 {sum(kinds.values())}개 — {dict(kinds)}")

    if missed:
        print(f"\n[못찾음] {len(missed)}개 — 표기 차이인지 진짜 어긋남인지 눈으로 본다")
        for day, ko, vi, cands in missed[:20]:
            print(f"  Day {day:>3} {ko:<7} 우리='{vi[:30]}'"
                  f"  사전='{cands[0][1].get('vi','')[:30]}'")

    print(f"\n[갈래여럿] {len(multi)}개 — 우리가 고른 갈래가 그 단원에 맞는가")
    for day, ko, vi, hit, cands in (multi if show else multi[:15]):
        print(f"  Day {day:>3} {ko:<7} 우리={hit} '{vi[:26]}'")
        if show:
            for k, v in cands:
                mark = "←" if k in hit else " "
                print(f"        {mark} {k}: {v.get('vi','')[:30]:<32} {v.get('ko_dfn','')[:38]}")
    if not show and len(multi) > 15:
        print(f"  ... 외 {len(multi)-15}개 (--list 로 전부)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
