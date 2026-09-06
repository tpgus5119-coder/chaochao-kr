#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**카드로 내기 전에 의심스러운 줄만 뽑아 준다** → 클로드가 그것만 원문과 대조한다

대표님 결정 (2026-09-02): "3으로 해" — Qwen 이 초안을 쓰고 **아침에 클로드가 검수**한다.
72줄을 다 읽으면 품이 많이 든다. 그래서 기계가 먼저 **셀 수 있는 것**을 세고,
걸리는 줄만 보여 준다. 클로드는 그 줄만 원문과 맞춰 보면 된다.

## 무엇을 세나
 ① 기사에 없는 숫자를 지어냈나
 ② 베트남 단위를 잘못 옮겼나 — tỷ(10억)를 '억' 으로 쓰면 열 배가 작아진다
 ③ 날짜를 거꾸로 읽었나 — 베트남은 2/9 가 9월 2일이다
 ④ 훈수·느낌·기사 얘기·오타·한자·베트남어가 남았나 (card_fill 의 잣대 그대로)
 ⑤ 같은 말이 두 줄인가

쓰기: python3 tools/card_check.py [--pub 2026-09-02]
"""
import argparse, json, pathlib, re, sys

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))

# 베트남 단위 → 우리 단위. 본문에 'N tỷ USD' 가 있으면 요약은 N×10 억 달러여야 한다
UNIT = [(r"([\d.,]+)\s*(?:tỷ|ty)\s*(?:USD|đô|đô la)", 10 ** 9, "tỷ USD"),
        (r"([\d.,]+)\s*(?:triệu)\s*(?:USD|đô)", 10 ** 6, "triệu USD"),
        (r"([\d.,]+)\s*(?:nghìn tỷ|nghin ty)\s*(?:đồng|dong)", 10 ** 12, "nghìn tỷ 동"),
        (r"([\d.,]+)\s*(?:tỷ|ty)\s*(?:đồng|dong)", 10 ** 9, "tỷ 동")]


def vi_num(s):
    """베트남식 수를 값으로. 쉼표가 소수점, 점이 천 단위 구분이다 (35,2 → 35.2)"""
    s = s.strip().rstrip(".,")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(".", "") if s.count(".") > 1 or len(s.split(".")[-1]) == 3 else s
    try:
        return float(s)
    except ValueError:
        return None


def ko_num(t):
    """한국어 수를 값으로 — '352억', '1조 3,430억', '2억 8,300만'"""
    out = []
    for m in re.finditer(r"((?:[\d,]+\s*[조억만천]\s*)+[\d,]*)", t):
        v, chunk = 0, m.group(1)
        for n, u in re.findall(r"([\d,]+)\s*([조억만천]?)", chunk):
            if not n:
                continue
            k = int(n.replace(",", ""))
            v += k * {"조": 10 ** 12, "억": 10 ** 8, "만": 10 ** 4, "천": 10 ** 3, "": 1}[u]
        if v:
            out.append((v, m.group(1).strip()))
    return out


def check(d, body):
    from card_fill import bad_line, _nums
    bad = []
    # 본문의 베트남 단위 값을 우리 단위로 미리 풀어 둔다 (2,31 tỷ USD → 23억 1,000만)
    want = []
    for pat, mul, name in UNIT:
        for m in re.finditer(pat, body, re.I):
            v = vi_num(m.group(1))
            if v:
                want.append((v * mul, f"{m.group(1)} {name}"))

    def converted(ln):
        """단위를 **제대로 옮긴** 줄인가 — 그러면 '없는 수' 로 보지 않는다"""
        return any(abs(kv - v) < max(v, 1) * 0.02
                   for kv, _ in ko_num(ln) for v, _ in want)

    for ln in d.get("sum5") or []:
        why = bad_line(ln)
        if why:
            bad.append((why, ln))
        # ① 지어낸 수 — 단위를 옮긴 줄은 빼고 본다
        gap = _nums(ln) - _nums(body)
        if gap and not converted(ln):
            bad.append((f"기사에 없는 수 {sorted(gap)}", ln))
    # ② 단위를 잘못 옮겼나 — 본문의 값과 요약의 값이 **열 배씩** 어긋나는지 본다
    for v, src in want:
        hit = [(kv, ks) for ln in (d.get("sum5") or []) for kv, ks in ko_num(ln)]
        if not hit:
            continue
        near = [(kv, ks) for kv, ks in hit if abs(kv - v) < v * 0.02]
        off = [(kv, ks) for kv, ks in hit if kv and (abs(kv * 10 - v) < v * 0.02
                                                    or abs(kv / 10 - v) < v * 0.02)]
        if not near and off:
            bad.append((f"단위가 열 배 어긋남 (원문 {src})", off[0][1]))
    # ③ 날짜 거꾸로 — 본문에 2/9 가 있는데 요약에 '2월 9일' 이 있으면 뒤집힌 것
    for m in re.finditer(r"\b(\d{1,2})/(\d{1,2})\b", body):
        a, b = int(m.group(1)), int(m.group(2))
        if 1 <= a <= 31 and 1 <= b <= 12:
            wrong = f"{a}월 {b}일"
            for ln in (d.get("sum5") or []):
                if wrong in ln.replace(" ", " "):
                    bad.append((f"날짜가 뒤집힘 (원문 {a}/{b} = {b}월 {a}일)", ln))
    # ⑤ 겹치는 줄
    seen = {}
    for ln in (d.get("sum5") or []):
        k = tuple(sorted(_nums(ln)))
        if k and k in seen:
            bad.append(("앞줄과 같은 수", ln))
        seen[k] = 1
    return bad


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--pub", default="")
    a = a.parse_args()
    j = json.loads((R / "data" / "news_days.json").read_text(encoding="utf-8"))
    bodies = json.loads((R / "data" / "_bodies.json").read_text(encoding="utf-8"))
    pub = a.pub or max((d.get("pub") or "") for d in j["days"])
    D = [d for d in j["days"] if d.get("pub") == pub]
    print(f"펴낼날 {pub} · 기사 {len(D)}편 · 줄 {sum(len(d.get('sum5') or []) for d in D)}\n")
    total = 0
    for d in D:
        body = bodies.get(d.get("u") or "") or ""
        if not body:
            print(f"■ {(d.get('title_card') or d.get('title') or '')[:34]}")
            print("   ⚠ 본문이 없어 대조 못 함 — 사람이 봐야 한다\n"); total += 1; continue
        bad = check(d, body)
        if not bad:
            continue
        total += len(bad)
        print(f"■ {(d.get('title_card') or d.get('title') or '')[:34]}")
        for why, ln in bad:
            print(f"   [{why}] {ln}")
        print()
    print(f"의심스러운 줄 {total} — 이것만 원문과 맞춰 보면 된다"
          if total else "걸리는 줄 없음. 그래도 눈으로 한 번 훑어라")


if __name__ == "__main__":
    main()
