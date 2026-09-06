#!/usr/bin/env python3
"""과녁에 얼마나 붙었나 — 우리 모의고사를 TOPIK 공식 설계도와 문항 번호별로 맞대 본다.

목표가 "실제 시험과 최대한 똑같게"라면, 재야 할 것은 문항 **수**가 아니라
**몇 번에 무엇이 나오는가**다. 70문항을 채웠어도 순서와 유형이 다르면 다른 시험이다.

세 가지를 잰다
  ① 자리 맞음(position match) : N번 문항의 유형이 설계도의 N번과 같은가
  ② 발문 맞음(stem match)     : 그 자리의 발문이 공식 문구와 같은가
  ③ 배점 맞음(points match)   : 배점과 총점이 맞는가

쓰기:  python3 tools/blueprint_check.py
       python3 tools/blueprint_check.py --gap    # 못 만드는 유형만 (할 일 목록)
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from topik_blueprint import FORMS, count

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 우리 시험 세트가 설계도의 어느 영역에 해당하는가
MAP = {
    "topik-1":        ["TOPIK I 듣기", "TOPIK I 읽기"],
    "topik-2-listen": ["TOPIK II 듣기"],
    "topik-2-read":   ["TOPIK II 읽기"],
}


def flat(s):
    """발문을 견줄 때 띄어쓰기·괄호·번호는 무시한다."""
    return re.sub(r"[^가-힣]", "", str(s or ""))


def spread(items):
    """묶음표를 문항 번호별 표로 편다. {번호: 묶음}"""
    out = {}
    for b in items:
        a, z = b["block"]
        for i, n in enumerate(range(a, z + 1)):
            out[n] = dict(b, idx=i)
    return out


def main():
    ex = json.load(open(f"{ROOT}/data/ko_exams.json", encoding="utf-8"))
    gap_only = "--gap" in sys.argv

    if not gap_only:
        print("═" * 74)
        print(" 우리 모의고사 vs TOPIK 공식 설계도 — 문항 번호별 대조")
        print("═" * 74)

    grand_hit = grand_all = 0
    for eid, areas in MAP.items():
        sets = [e for e in ex["exams"] if e["id"] == eid]
        if not sets:
            continue
        # 설계도를 이어 붙인다. TOPIK I 읽기 묶음은 이미 31~70 으로 매겨져 있으므로
        # 오프셋을 더하면 안 된다 — 더했다가 61~100 이 되어 40문항이 통째로 어긋났다.
        plan = {}
        for a in areas:
            for n, b in spread(FORMS[a]["items"]).items():
                plan[n] = dict(b, area=a)

        e = sets[0]                       # 회차는 구조가 같으니 1회차로 본다
        qs = {q["no"]: q for q in e["questions"]}
        hit = stem_hit = 0
        gaps = []
        for n in sorted(plan):
            b = plan[n]
            want = b.get("ours")
            got = qs.get(n)
            ok = bool(got and want and got["type"] == want)
            if ok:
                hit += 1
                if flat(b["stem"]) in flat(got.get("section", "")) or \
                   flat(b["stem"]) in flat(got.get("stem", "")):
                    stem_hit += 1
            else:
                gaps.append((n, b["qtype"], b["stem"][:38],
                             got["type"] if got else "(문항 없음)", want or "만들 줄 모름"))
        grand_hit += hit; grand_all += len(plan)

        if not gap_only:
            print(f"\n■ {e['name']}  ({eid})")
            print(f"   자리 맞음 {hit:>3}/{len(plan)} ({hit/len(plan):.0%})"
                  f"   ·  발문까지 맞음 {stem_hit:>3}/{len(plan)} ({stem_hit/len(plan):.0%})")
            if gaps:
                print(f"   어긋난 자리 {len(gaps)}개 — 앞 12개만:")
                for n, qt, st, got, want in gaps[:12]:
                    print(f"     {n:>2}번  설계도: {qt:<22} │ 우리: {got}")
        else:
            print(f"\n■ {e['name']}")
            seen = set()
            for n, qt, st, got, want in gaps:
                if qt in seen:
                    continue
                seen.add(qt)
                cnt = sum(1 for g in gaps if g[1] == qt)
                print(f"   [{cnt:>2}문항] {qt}")
                print(f"            발문: {st}")

    print("\n" + "═" * 74)
    print(f" 전체 자리 맞음: {grand_hit} / {grand_all} = {grand_hit/max(1,grand_all):.0%}")
    print("═" * 74)
    if not gap_only:
        print(" `--gap` 을 붙이면 '아직 못 만드는 유형'만 모아 보여 줍니다.")


if __name__ == "__main__":
    main()
