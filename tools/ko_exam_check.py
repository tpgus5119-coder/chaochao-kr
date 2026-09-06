#!/usr/bin/env python3
"""출제 결과 자가 검수 — 자동 생성 문항이 빠지기 쉬운 함정만 골라 잡는다.

잡는 것:
  1) 보기 중복        — 같은 낱말이 두 번 나오면 문제가 성립하지 않는다
  2) 정답 누설        — 뜻풀이 안에 정답 낱말이 그대로 들어 있으면 뜻을 몰라도 맞힌다
  3) 뜻 겹침          — 보기 넷의 베트남어 뜻이 겹치면 정답이 둘이 된다
  4) 회차 간 같은 문항 — 1·2·3회차를 이어 풀 때 같은 문제가 또 나오면 시험이 안 된다
  5) 정답 쏠림        — 정답 번호가 한쪽에 몰리면 찍어서 맞는다
"""
import json, os, sys
from collections import Counter

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

def vi_tokens(s):
    """'y tá, bác sĩ' → {'y tá','bác sĩ'} — 쉼표로 갈라 낱낱이 비교한다."""
    return {t.strip().lower() for t in str(s).split(",") if t.strip()}


def length_cue(d):
    """유일하게 가장 긴 보기가 정답인 비율 — 우연이면 25%다.

    왜 따로 재나: 기존 검사(길이 차 12자 이상 + 정답이 끝값)는 극단만 잡는다.
    그런데 정답을 '정확하고 완전하게' 쓰다 보면 오답보다 조금씩 길어져,
    한 문항으로는 안 보여도 시험 전체로는 '긴 것 찍기'가 통하게 된다.
    실측 57.8%(2026-08-28, z=21.1)가 그렇게 나왔다. 목표 30% 이하.
    (문항 작성 지침의 고전적 결함이다 — Haladyna 외 2002, 지침 24·28)
    """
    from collections import Counter
    uni = Counter(); hit = Counter()
    for e in d["exams"]:
        for q in e["questions"]:
            if q.get("short"):        # 보기가 없으니 '긴 보기 찍기'가 아예 성립하지 않는다
                continue
            L = [len(str(o)) for o in q["options"]]
            mx = max(L)
            if L.count(mx) == 1:
                uni[q["type"]] += 1
                if L.index(mx) == q["answer"]:
                    hit[q["type"]] += 1
    U, H = sum(uni.values()), sum(hit.values())
    pct = 100 * H / max(1, U)
    print(f"\n긴 보기 = 정답: {H}/{U} = {pct:.1f}%  (우연 25% · 목표 30% 이하)")
    bad = [(t, hit[t], n) for t, n in uni.items() if n >= 8 and hit[t] / n > 0.5]
    for t, h, n in sorted(bad, key=lambda x: -x[1] / x[2]):
        print(f"   ! {t:<16} {h}/{n} = {100*h/n:.0f}%  — 오답을 늘리거나 정답을 줄여야 한다")

def main():
    d = json.load(open(os.path.join(DATA, "ko_exams.json"), encoding="utf-8"))
    problems = []
    seen_by_exam = {}

    for e in d["exams"]:
        key = e["id"]
        seen = seen_by_exam.setdefault(key, {})
        for q in e["questions"]:
            where = f"{e['id']} {e['set']}회 {q['no']}번"
            # 단답형(KIIP)은 보기가 없다 — 아래 검사는 전부 보기에 대한 것이라 따로 본다.
            # 대신 이쪽에서만 생기는 사고를 본다: 답이 뜻풀이 안에 그대로 있으면 거저 준 문항이다.
            if q.get("short"):
                ans = str(q.get("answerText") or "")
                body = q["stem"].split("\n", 1)[-1]
                if not ans:
                    problems.append(("단답형 정답 없음", where, q["stem"][:30]))
                elif ans in body:
                    problems.append(("정답누설", where, f"'{ans}' in 뜻풀이"))
                continue
            opts = [str(o) for o in q["options"]]

            # 1) 보기 중복
            dup = [o for o, c in Counter(opts).items() if c > 1]
            if dup:
                problems.append(("보기중복", where, str(dup)))

            # 2) 정답 누설 — 뜻풀이형에서 stem 안에 정답이 그대로 있는가
            if q["type"] == "dfn2word":
                ans = opts[q["answer"]]
                body = q["stem"].split("\n", 1)[-1]
                stem_word = ans[:-2] if ans.endswith("하다") and len(ans) > 3 else ans
                if stem_word and stem_word in body:
                    problems.append(("정답누설", where, f"'{stem_word}' in 뜻풀이"))

            # 3) 뜻 겹침 — 베트남어 뜻 보기끼리 같은 표현을 공유하는가
            if q["type"] == "word2vi":
                sets = [vi_tokens(o) for o in opts]
                for i in range(len(sets)):
                    for j in range(i + 1, len(sets)):
                        if sets[i] & sets[j]:
                            problems.append(("뜻겹침", where,
                                             f"{opts[i]} ↔ {opts[j]} (겹침: {sets[i] & sets[j]})"))

            # 4) 회차 간 같은 문항
            # 문두만 보면 안 된다. 그림 문항은 문두가 다 같고 그림만 다르고,
            # 듣기 문항은 문두가 다 같고 **들려주는 말**이 다르다.
            # "실제로 무엇을 묻는가"를 다 넣어야 진짜 중복만 잡힌다.
            #
            # 공통문항(anchor)은 **일부러** 모든 회차에 같이 넣은 것이다.
            # 이것이 없으면 1회차 70점과 2회차 70점을 견줄 수가 없다 —
            # 회차마다 문항이 다르니 점수 차이가 실력 차이인지 문제 차이인지 모른다.
            # 그러니 여기서 잡으면 안 된다.
            if q.get("anchor"):
                continue
            sig = (q["type"], q["stem"], q.get("img", ""), q.get("word", ""),
                   json.dumps(q.get("audio", ""), ensure_ascii=False),
                   q.get("passage", ""))
            if sig in seen:
                problems.append(("회차중복", where, f"{seen[sig]}와 같은 문항"))
            else:
                seen[sig] = where

    # 5) 정답 쏠림 — 시험별 정답 번호 분포
    skew = []
    for e in d["exams"]:
        # 단답형은 고를 번호가 없다 — 쏠림을 셀 대상이 아니다
        picks = [q for q in e["questions"] if not q.get("short")]
        c = Counter(q["answer"] for q in picks)
        n = len(picks)
        worst = max(c.values()) / n if n else 0
        if worst > 0.45:
            skew.append(f"{e['id']} {e['set']}회: {dict(sorted(c.items()))} (최다 {worst:.0%})")

    total_q = sum(len(e["questions"]) for e in d["exams"])
    # 정답만 유난히 길거나 짧으면 뜻을 몰라도 찍힌다 — 실제로 118문항이 그랬다.
    for e in d["exams"]:
        for q in e["questions"]:
            if q.get("optkind") == "img" or q.get("short"):
                continue
            L = [len(str(x)) for x in q["options"]]
            if max(L) - min(L) >= 12 and L[q["answer"]] in (max(L), min(L)):
                problems.append(("길이로 찍힘", f"{e['id']} {e['set']}회 {q['no']}번",
                                 f"보기 길이 {min(L)}~{max(L)}자 — 정답이 끝값이라 읽지 않고도 찍힌다"))

    print(f"검사 대상: {len(d['exams'])}개 세트 · {total_q}문항")
    if problems:
        by_kind = Counter(p[0] for p in problems)
        print(f"\n결함 {len(problems)}건: {dict(by_kind)}")
        for kind, where, detail in problems[:25]:
            print(f"  [{kind}] {where} — {detail}")
        if len(problems) > 25:
            print(f"  ... 외 {len(problems)-25}건")
    else:
        print("\n결함 없음 (중복·누설·뜻겹침·회차중복)")

    if skew:
        print("\n정답 쏠림 의심:")
        for s in skew:
            print("  " + s)
    else:
        length_cue(d)
    print("정답 번호 분포 고름")

    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main())
