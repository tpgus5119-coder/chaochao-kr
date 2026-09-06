#!/usr/bin/env python3
"""오답지 품질을 잰다 — **정답이 둘인 문항**과 **너무 먼 오답**.

두 가지를 센다:
  ① 정답이 둘  : 보기 넷 가운데 둘이 같은 답이 되는 문항. 세 갈래로 본다 —
                 보기 글자가 같다 · 뜻 뿌리가 같다 · 베트남어 뜻이 겹친다.
                 (베트남어 퀴즈에서 실제로 나왔다: đau 와 ốm 이 둘 다 '아프다')
  ② 유의어 오답: 오답 자리에 정답의 **유의어**가 앉은 문항.
                 '가격'을 묻는데 보기에 '값'이 있으면 그건 틀린 보기가 아니다.
  ③ 가까운 오답: 오답 셋 가운데 뜻이 가까운 것(반의어·같은 의미범주)이 몇 개인가.
                 뜻이 아주 먼 낱말만 있으면 한국어를 몰라도 어울리지 않는 것을
                 지워 가며 맞힌다. 높을수록 좋다.

잣대는 국립국어원 등급별 어휘 12,010(유의어 3,283 · 반의어 760 · 의미범주 6,413).

실행: python3 tools/distractor_check.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ko_exam_gen as G

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
KINDS = ("dfn2word", "vi2word", "word2vi", "pic2word", "job")


def main():
    d = json.load(open(os.path.join(DATA, "ko_exams.json"), encoding="utf-8"))
    # 보기 글자 → 낱말. word2vi 는 보기가 베트남어 뜻이라 되짚어야 한다.
    words = json.load(open(os.path.join(DATA, "_ko_words.json"), encoding="utf-8"))
    by_vi = {}
    for w in words:
        by_vi.setdefault(str(w.get("vi", "")).split(",")[0].strip(), w["ko"])

    # ── 정답이 둘인 문항 — 보기 넷 가운데 둘이 같은 답이 되는가 ──────────
    # 세 갈래로 본다:
    #   ㉠ 보기 글자가 아예 같다
    #   ㉡ 뜻 뿌리가 같다 ('아프다' 와 '아프다 (병나다)')
    #   ㉢ 낱말형에서 정답과 오답의 베트남어 뜻이 겹친다 (= 둘 다 맞는 답)
    # 순서 배열 문항은 보기가 '(나)-(라)-(다)-(가)' 꼴이라 ㉡ 검사에서 빼야 한다 —
    # 괄호 앞을 자르면 넷 다 빈 글자가 되어 전부 결함으로 잡힌다(실제로 12건 잡혔다).
    def stem(s):
        return re.split(r"[,;(·]", str(s or ""))[0].strip()

    def pieces(s):
        return {p.strip().lower() for p in re.split(r"[,;/]", str(s or "")) if p.strip()}

    VI = {w["ko"]: str(w.get("vi", "")) for w in words}
    two, twobad = 0, []
    for e in d["exams"]:
        for q in e["questions"]:
            if q.get("short") or not q.get("options"):
                continue
            opts = [str(o) for o in q["options"]]
            why = None
            if len(set(opts)) != len(opts):
                why = "보기 글자가 같다"
            else:
                st = [stem(o) for o in opts]
                if all(st) and len(set(st)) != len(st):
                    why = "뜻 뿌리가 같다"
                elif q.get("type") in ("dfn2word", "vi2word", "pic2word") and q.get("word"):
                    av = pieces(VI.get(q["word"], ""))
                    same = [o for i, o in enumerate(opts)
                            if i != q["answer"] and av and (av & pieces(VI.get(o, "")))]
                    if same:
                        why = f"'{q['word']}' 와 뜻이 겹친다: {same}"
            if why:
                two += 1
                if len(twobad) < 10:
                    twobad.append((f"{e['id']} {e['set']}회 {q['no']}번", why, opts))

    dup, near, tot, seen_near = 0, 0, 0, 0
    bad = []
    for e in d["exams"]:
        for q in e["questions"]:
            if q.get("type") not in KINDS or q.get("short") or not q.get("options"):
                continue
            ans = q.get("word")
            if not ans:
                continue
            others = []
            for i, o in enumerate(q["options"]):
                if i == q["answer"]:
                    continue
                s = str(o).split(",")[0].strip()
                others.append(by_vi.get(s, s))       # 베트남어 보기면 낱말로 되짚는다
            if not others:
                continue
            tot += 1
            hit = [o for o in others if G.is_syn(ans, o)]
            if hit:
                dup += 1
                if len(bad) < 12:
                    bad.append((f"{e['id']} {e['set']}회 {q['no']}번", ans, hit))
            k = sum(1 for o in others if G.close_to(ans, o))
            near += k
            seen_near += len(others)

    print(f"검사 대상 {sum(len(e['questions']) for e in d['exams'])}문항 "
          f"(그중 낱말형 {tot}개)")
    print(f"① 정답이 둘: {two}개  ← 0 이어야 한다")
    for where, why, opts in twobad:
        print(f"     {where}  {why}")
    print(f"② 오답에 정답의 유의어: {dup}개  ← 0 이어야 한다")
    for where, a, h in bad:
        print(f"     {where}  '{a}' 인데 보기에 {h}")
    print(f"③ 뜻이 가까운 오답: {near}/{seen_near} = {100*near/max(1,seen_near):.1f}%"
          f"  ← 높을수록 좋다")
    return 1 if (dup or two) else 0


if __name__ == "__main__":
    sys.exit(main())
