#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""뜻(한국어)의 **깨진 글자**를 고친다 → data/order.json

대표님 지적 (2026-08-31): "사전에 나오는 단어가 아닌것들이 있는지 점검해봐.
                         처음부터 끝까지 다 검사해라."
전수 검사에서 나온 것 — 뜻이 잘리거나 괄호 짝이 안 맞는 것 27개.

고치는 것 (규칙으로 확실한 것만. 뜻을 바꾸지는 않는다)
  ① 여는 괄호가 사라진 품사 표시   '명) 풍자 만화'  → '(명) 풍자 만화'
  ② 짝 없는 닫는 괄호·대괄호       '낙엽 ]' '연극 )' → '낙엽' '연극'
  ③ 닫히지 않은 괄호               '자주(빈도'      → '자주(빈도)'
  ④ 짝 없는 여는 괄호가 끝에 홀로   '응용, 적용 ('   → '응용, 적용'

**뜻 자체가 잘려 나간 것**(악기 설명이 중간에서 끊긴 것 등)은 사람이 채워야 하므로
고치지 않고 목록으로만 알린다.

쓰기: python3 tools/ko_fix.py            # 무엇이 바뀌는지 보기만
      python3 tools/ko_fix.py --write
"""
import json, pathlib, re, sys, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
WRITE = "--write" in sys.argv
POS = "명|동|형|부|관용|전|접|대|수|조|감"


def walk(v):
    for t in (v.get("tracks") or [v]):
        for c in t["chapters"]:
            for l in c["lessons"]:
                yield from l["words"]


def fix(ko):
    """고친 뜻과 '사람이 봐야 하는가'를 돌려준다."""
    t = U.normalize("NFC", str(ko)).strip()
    o = t

    # ① 여는 괄호가 사라진 품사 표시
    t = re.sub(rf"^({POS})\)\s*", r"(\1) ", t)

    # ② 짝 없는 닫는 괄호·대괄호를 뒤에서 떼어 낸다
    while t and t[-1] in ")]":
        close, open_ = t[-1], "(" if t[-1] == ")" else "["
        if t.count(open_) >= t.count(close):
            break
        t = t[:-1].rstrip(" ·,")

    # ④ 끝에 홀로 남은 여는 괄호
    while t and t[-1] in "([" and t.count(t[-1]) > t.count(")" if t[-1] == "(" else "]"):
        t = t[:-1].rstrip(" ·,")

    # ③ 닫히지 않은 괄호 — 끝에 닫아 준다
    if t.count("(") == t.count(")") + 1 and t.rfind("(") < len(t) - 1:
        t += ")"
    if t.count("[") == t.count("]") + 1 and t.rfind("[") < len(t) - 1:
        t += "]"

    t = re.sub(r"\s+", " ", t).strip()
    hand = t.count("(") != t.count(")") or t.count("[") != t.count("]")
    return t, (t != o), hand


def main():
    p = R / "data" / "order.json"
    O = json.loads(p.read_text(encoding="utf-8"))
    words = [w for v in O["vols"] for w in walk(v)] + O.get("gramwords", [])
    changed, hand = [], []
    for w in words:
        new, did, need = fix(w["ko"])
        if did:
            changed.append((w["vi"], w["ko"], new))
            w["ko"] = new
        if need:
            hand.append((w["vi"], new))

    print(f"고친 뜻 {len(changed)}개")
    for vi, a, b in changed:
        print(f"  {vi:24} {a!r} → {b!r}")
    if hand:
        print(f"\n사람이 채워야 하는 것 {len(hand)}개 (뜻이 중간에서 끊겼다)")
        for vi, t in hand:
            print(f"  {vi:24} {t}")
    if WRITE and changed:
        p.write_text(json.dumps(O, ensure_ascii=False), encoding="utf-8")
        print("\n실제로 썼습니다.")
    elif changed:
        print("\n보기만 했습니다 — 쓰려면 --write")


main()
