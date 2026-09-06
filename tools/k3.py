#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""한국어 과정 3단계 — EPS 60단원에 어휘를 배분한다.

재료: data/eps_units.json  (공식 표준교재 차례·어휘 색인에서 추출한 **사실** — 표현 아님)
      data/_ko_words.json  (국립국어원 5,744 + 베트남어 뜻)
산출: data/_ko_units.json  단원마다
      · match : 교재 색인 단어 중 우리 창고에 있는 것 (뜻·등급·한자 동봉)
      · extra : 교재에만 있는 단어 (EPS 특화 — 다음 공정에서 krdict 로 뜻 달아 카드화)
      · pool  : 색인 밖 A등급 후보 (빈도순 — 단원 카드 수 맞출 때 채움용)
실행: python3 tools/k3.py
"""
import json, pathlib, re, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
TAIL = re.compile(r'\d+$')

def norm(s):
    s = unicodedata.normalize("NFC", s)
    s = re.sub(r'\(하다\)$', '하다', s)      # 색인의 '배송(하다)' → 배송하다 도 같이 본다
    return s.replace(' ', '').strip()

def main():
    store = json.loads((ROOT / "data" / "_ko_words.json").read_text())
    eps = json.loads((ROOT / "data" / "eps_units.json").read_text())
    byko = {}
    for w in store:
        byko.setdefault(norm(w["ko"]), w)
    used = set()
    out_units = []
    for u in eps["units"]:
        match, extra = [], []
        for it in u["words"]:
            k = norm(it["ko"])
            base = norm(re.sub(r'\(하다\)$', '', it["ko"]))     # '배송(하다)' → 배송 도 시도
            w = byko.get(k) or byko.get(base)
            if w:
                match.append({**{x: w[x] for x in ("ko", "pos", "grade", "rank") if x in w},
                              **({"vi": w["vi"]} if "vi" in w else {}),
                              **({"hanja": w["hanja"]} if "hanja" in w else {}),
                              "en": it["en"]})
                used.add(norm(w["ko"]))
            else:
                extra.append(it)
        out_units.append({"no": u["no"], "title": u["title"],
                          "match": match, "extra": extra})
    # 색인에 안 나온 A등급 — 빈도순 후보 풀 (2권 단원과 카드 수 균형 맞출 때 쓴다)
    pool = [w for w in store if w["grade"] == "A" and norm(w["ko"]) not in used]
    pool.sort(key=lambda x: x["rank"])
    out = {"units": out_units,
           "pool_A": [{k: w[k] for k in ("ko", "pos", "rank") if k in w} for w in pool]}
    (ROOT / "data" / "_ko_units.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))

    m = sum(len(u["match"]) for u in out_units)
    e = sum(len(u["extra"]) for u in out_units)
    a_used = sum(1 for u in out_units for w in u["match"] if w["grade"] == "A")
    print(f"교재 색인 1권: 창고와 겹침 {m} · 교재 특화 {e}")
    print(f"A등급 사용 {a_used}/949 · 남은 A 후보 풀 {len(pool)}")
    top5 = sorted(out_units[:30], key=lambda u: -len(u["match"]))[:3]
    for u in top5: print(f"  예) {u['no']} {u['title']}: 겹침 {len(u['match'])} / 특화 {len(u['extra'])}")

if __name__ == "__main__":
    main()
