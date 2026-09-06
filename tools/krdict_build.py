#!/usr/bin/env python3
"""국립국어원 한국어기초사전에서 **한-베 낱말 뭉치**를 뽑는다.

  python3 tools/krdict_build.py            → data/krdict_kovi.json
  python3 tools/krdict_build.py --stats    → 세기만 하고 쓰지 않음

왜 이게 필요한가: 우리는 지금 국립국어원 학습용 어휘 5,543개 중 **1,042개(18.8%)**만
가르친다. 중급 21%, 고급 6.6%다 — 이대로면 TOPIK Ⅱ 위로 못 올라간다.
그리고 지금까지 쓰던 한-베 대역표는 손으로 모은 것이라 오역이 있었다
(계단 → giai đoạn 같은). 국가가 검수한 뜻으로 갈아탄다.

**이용 조건** — 크리에이티브 커먼즈 저작자표시-동일조건변경허락 2.0 대한민국(CC BY-SA 2.0 KR).
상업 이용도 변경도 된다. 대신 이것을 바탕으로 만든 자료는 **같은 조건으로 풀어야 한다.**
그래서 만든 파일 안에 출처와 조건을 함께 적는다 — 지우면 조건 위반이다.

받는 곳: krdict.korean.go.kr → 사전 전체 내려받기 → Json (~/krdict/json/)
"""
import argparse
import collections
import glob
import json
import os
import pathlib
import re

SRC = pathlib.Path.home() / "krdict" / "json"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "krdict_kovi.json"
KEEP_LEVEL = {"초급", "중급"}          # 고급 37,024개는 TOPIK Ⅱ 6급 이상 — 나중 일
LICENSE = ("국립국어원 한국어기초사전 (krdict.korean.go.kr) · "
           "CC BY-SA 2.0 KR — 이 자료를 바탕으로 만든 것도 같은 조건으로 풀어야 합니다.")


def feats(o):
    """이 사전은 같은 자리가 dict 이기도 list 이기도 하다 — 둘 다 받는다."""
    if isinstance(o, list):
        o = o[0] if o else {}
    f = o.get("feat") if isinstance(o, dict) else None
    if f is None:
        return {}
    return {x["att"]: x["val"] for x in (f if isinstance(f, list) else [f])
            if isinstance(x, dict) and "att" in x}


def entries():
    for fn in sorted(glob.glob(str(SRC / "*.json"))):
        d = json.load(open(fn, encoding="utf-8"))
        for e in d["LexicalResource"]["Lexicon"]["LexicalEntry"]:
            yield e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    a = ap.parse_args()
    if not SRC.exists():
        raise SystemExit(f"사전이 없다: {SRC}\n  krdict.korean.go.kr 에서 Json 전체를 받아 풀 것.")

    out, seen, cnt = [], set(), collections.Counter()
    for e in entries():
        fd = feats(e)
        lv = fd.get("vocabularyLevel", "")
        cnt[lv or "없음"] += 1
        if lv not in KEEP_LEVEL:
            continue
        ko = feats(e["Lemma"]).get("writtenForm", "").strip()
        if not ko or re.search(r"[^가-힣ㆍ\- ]", ko):
            continue                                  # 접사(-답다)·기호 섞인 표제어는 뺀다
        han = fd.get("origin", "")
        han = han if re.search(r"[一-鿿]", han) else ""
        ss = e["Sense"] if isinstance(e["Sense"], list) else [e["Sense"]]
        vi = videf = ""
        for s in ss:                                   # 첫 뜻만 — 여러 뜻은 낱말 카드에 안 들어간다
            eq = s.get("Equivalent") or []
            for q in (eq if isinstance(eq, list) else [eq]):
                m = feats(q)
                if m.get("language") == "베트남어" and m.get("lemma"):
                    vi, videf = m["lemma"].strip(), (m.get("definition") or "").strip()
                    break
            if vi:
                break
        if not vi:
            continue
        # **같은 한글에 여러 한자가 있다.** 인상 = 人相 / 引上 / 印象.
        # 하나만 남기면 뜻과 한자가 어긋난 카드가 나온다 — 베트남 학습자에게 가장
        # 해로운 종류의 잘못이다(한자를 다리로 쓰기 때문에). 그래서 **다 남기고**
        # 몇 갈래인지 적어 둔다. 고르는 것은 사람 몫이지 이 도구의 몫이 아니다.
        key = (ko, han)
        if key in seen:
            continue
        seen.add(key)
        row = {"ko": ko, "vi": vi, "lv": lv}
        if han:
            row["han"] = han                           # 베트남 학습자에게 한자가 다리다
        if videf:
            row["def"] = videf
        pos = feats(e).get("partOfSpeech", "")
        if pos:
            row["pos"] = pos
        out.append(row)

    # 여러 갈래인 낱말에 표를 단다 — 쓰는 쪽이 모르고 지나치지 못하게.
    by_ko = collections.Counter(r["ko"] for r in out)
    for r in out:
        if by_ko[r["ko"]] > 1:
            r["amb"] = by_ko[r["ko"]]
    many = sum(1 for k, v in by_ko.items() if v > 1)

    print("사전 전체 등급 분포:", dict(cnt))
    print(f"뽑은 뜻 {len(out):,}개 · 낱말 {len(by_ko):,}개 (초급·중급) · "
          f"한자 붙은 것 {sum(1 for r in out if 'han' in r):,}")
    print(f"한 글자에 여러 한자가 걸린 낱말 {many:,}개 — 'amb' 표가 붙는다. "
          f"카드로 낼 때 반드시 사람이 고를 것")
    if a.stats:
        return
    OUT.write_text(json.dumps(
        {"note": LICENSE, "n": len(out), "words": out},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"→ {OUT} ({OUT.stat().st_size/1024/1024:.1f}MB)")


if __name__ == "__main__":
    main()
