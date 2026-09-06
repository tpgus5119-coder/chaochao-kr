#!/usr/bin/env python3
"""**베트남어 퀴즈**의 문제 질을 잰다 — 한국어 시험만 재던 것을 이쪽에도 붙인다.

왜 필요했나: 잣대가 다섯 개 있었는데 전부 **한국어 시험** 쪽이었다.
  베트남어 퀴즈는 한 번도 잰 적이 없었다. 재 보니 대체로 좋았지만
  **정답이 둘인 문항**이 있었다 — Day 16 의 đau 와 ốm 이 둘 다 '아프다'였다.

퀴즈 보기는 app.js 의 buildQuestions() 가 화면에서 만든다. 여기서는 그 규칙을
그대로 따라 해서 미리 잰다 — 규칙이 바뀌면 이 파일도 같이 고쳐야 한다.
  · 오답은 **같은 날(단원)** 에서 먼저 뽑고, 모자라면 전체에서 채운다
  · 뜻이 같은 낱말은 오답이 될 수 없다(괄호 앞 알맹이로 견준다)

세는 것
  ① 정답이 둘 : 보기 중에 정답과 뜻이 같은 것. **0이어야 한다.**
  ② 길이 단서 : 정답이 유일하게 가장 긴 보기인 비율(우연 25%) ·
                길이 차 12자 이상인데 정답이 끝값인 문항 수
  ③ 같은 단원 : 오답이 같은 단원에서 나온 비율(높을수록 헷갈리는 진짜 보기)

실행: python3 tools/vi_quiz_check.py
"""
import json
import os
import random
import re
import sys

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
ROUNDS = 5          # 보기를 무작위로 뽑으므로 여러 판을 돌려 흔들림까지 본다


def stem(s):
    """'아프다 (병나다)' → '아프다'. 괄호 앞 알맹이가 같으면 같은 뜻으로 본다."""
    return re.split(r"[,;(·]", str(s or ""))[0].strip()


def main():
    days = json.load(open(os.path.join(DATA, "days.json"), encoding="utf-8"))["days"]
    words, chap = [], {}
    for d in days:
        for w in d.get("words") or []:
            words.append(w)
            chap[w["vi"]] = d["day"]

    # 먼저 자료 자체를 본다. 두 가지를 갈라 봐야 한다:
    #   같은 뿌리(아프다 / 아프다(병나다)) — buildQuestions 가 한 문제에 같이 안 낸다.
    #     학습자는 괄호를 보고 가릴 수 있으니 **결함이 아니다.** 알려만 준다.
    #   글자까지 똑같음 — 이건 학습자도 못 가린다. **결함이다.**
    clash, note = [], []
    for d in days:
        seen, full = {}, {}
        for w in d.get("words") or []:
            k, f = stem(w["ko"]), str(w["ko"]).strip()
            if f in full:
                clash.append((d["day"], f, full[f], w["vi"]))
            elif k in seen:
                note.append((d["day"], k, seen[k], w["vi"]))
            full[f] = w["vi"]
            seen.setdefault(k, w["vi"])

    dup_r, long_r, gap_r, same_r = [], [], [], []
    for r in range(ROUNDS):
        rng = random.Random(100 + r)
        dup = gap = long = same = opts = 0
        for w in words:
            mine, home = stem(w["ko"]), chap[w["vi"]]
            ok = [x for x in words
                  if x["vi"] != w["vi"] and stem(x["ko"]) != mine]
            near = [x for x in ok if chap[x["vi"]] == home]
            rng.shuffle(near)
            pick = near[:3]
            if len(pick) < 3:
                rest = [x for x in ok if x not in pick]
                rng.shuffle(rest)
                pick += rest[:3 - len(pick)]
            if len(pick) < 3:
                continue
            opt = pick + [w]
            L = [len(str(x["ko"])) for x in opt]
            ai = opt.index(w)
            mx, mn = max(L), min(L)
            if L[ai] == mx and L.count(mx) == 1:
                long += 1
            if mx - mn >= 12 and L[ai] in (mx, mn):
                gap += 1
            for x in pick:
                opts += 1
                if chap[x["vi"]] == home:
                    same += 1
                if stem(x["ko"]) == mine:
                    dup += 1
        dup_r.append(dup)
        gap_r.append(gap)
        long_r.append(100 * long / len(words))
        same_r.append(100 * same / max(1, opts))

    print(f"베트남어 낱말 {len(words)}개 · {ROUNDS}판 돌림")
    print(f"① 정답이 둘: {dup_r}  ← 전부 0 이어야 한다")
    if clash:
        print("   ! 뜻풀이가 **글자까지 똑같은** 짝 — 학습자도 못 가린다. 갈라 적어야 한다:")
        for day, k, a, b in clash:
            print(f"     Day {day} · '{k}' : {a} ↔ {b}")
    if note:
        print("   (뿌리가 같아 한 문제에 같이 내지 않는 짝 — 괄호로 갈라져 있어 괜찮다:")
        for day, k, a, b in note:
            print(f"     Day {day} · '{k}' : {a} ↔ {b})")
    print(f"② 정답이 유일하게 가장 긴 보기: "
          f"{min(long_r):.1f}~{max(long_r):.1f}%  (우연 25%)")
    print(f"   길이차 12자 이상 + 정답이 끝값: {gap_r}개")
    print(f"③ 같은 단원에서 뽑은 오답: {min(same_r):.1f}~{max(same_r):.1f}%")
    return 1 if (any(dup_r) or clash) else 0


if __name__ == "__main__":
    sys.exit(main())
