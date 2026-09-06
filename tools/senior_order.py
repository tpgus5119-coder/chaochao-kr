#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**네 기수가 실제로 배운 차례**를 낱말마다 매긴다 → data/_senior_order.json

생각의 뼈대 (2026-08-30)
  선배들 시험은 회차 번호가 곧 배운 날짜다. 그러니 어떤 낱말이
  **몇 번째 회차에 처음 나왔나**가 그 낱말을 언제 배웠는지를 말해 준다.
  기수마다 회차 수가 다르니(17기 107 · 20기 84) 0~1 로 자를 맞춘 뒤
  기수들의 **가운뎃값**을 쓴다 — 한 기수가 유별나게 늦게/일찍 낸 것에 안 흔들린다.
  이 값으로 줄을 세우면 그게 곧 **네 기수 공통 차례**다. 내가 지어낸 순서가 아니다.
쓰기: python3 tools/senior_order.py
"""
import json, pathlib, statistics, unicodedata as U, re, collections

R = pathlib.Path(__file__).resolve().parent.parent
SRC = {"17": "_senior_words-17.json", "18": "_senior_words-18.json",
       "19": "_senior_words-19.json", "20": "_senior_words.json"}

def norm(v):
    """낱말 하나를 견주기 좋은 꼴로 — 홑화(NFC) · 소문자 · 겹빈칸 · 끝 문장부호"""
    s = U.normalize("NFC", str(v)).strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^[\d.\)\s]+", "", s)
    return s.strip(" .,;:!?~-–—/")

def main():
    first = collections.defaultdict(dict)     # 낱말 -> {기수: 0~1 위치}
    forms, means = {}, collections.defaultdict(collections.Counter)
    for gi, f in SRC.items():
        d = json.loads((R / "data" / f).read_text(encoding="utf-8"))
        sets = [s for s in d["sets"] if s["kind"] == "일일" and s["no"] > 0]
        if not sets: continue
        hi = max(s["no"] for s in sets)
        for s in sets:
            pos = s["no"] / hi
            for w in s["words"]:
                k = norm(w["vi"])
                if not k or len(k) > 40: continue
                if k not in first[gi] if False else True:
                    pass
                cur = first[k].get(gi)
                if cur is None or pos < cur: first[k][gi] = pos
                forms.setdefault(k, w["vi"].strip())
                if w.get("ko"): means[k][w["ko"].strip()] += 1
    out = []
    for k, gis in first.items():
        med = statistics.median(gis.values())
        out.append({"vi": forms[k], "key": k, "ko": means[k].most_common(1)[0][0] if means[k] else "",
                    "gi": "".join(sorted(gis)), "n": len(gis),
                    "pos": round(med, 4), "spread": round(max(gis.values()) - min(gis.values()), 3)})
    out.sort(key=lambda w: (w["pos"], -w["n"]))
    (R / "data" / "_senior_order.json").write_text(
        json.dumps({"note": "네 기수 시험 회차로 잰 '배운 차례'. pos=0 이 첫날, 1 이 마지막날.",
                    "words": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"낱말 {len(out)}개")
    print("  기수 겹침:", dict(collections.Counter(w['n'] for w in out)))
    multi = [w for w in out if w["n"] >= 2]
    print(f"  두 기수 이상 {len(multi)}개 · 자리 어긋남 가운뎃값 {statistics.median(w['spread'] for w in multi):.2f}")
    for lo in range(0, 10):
        chunk = [w for w in out if lo/10 <= w["pos"] < (lo+1)/10]
        print(f"  {lo*10:>3}~{lo*10+10:<3}% ({len(chunk):>4}개): " +
              " · ".join(w["ko"].split("/")[0].split("(")[0].strip()[:6] for w in chunk[:16]))

main()
