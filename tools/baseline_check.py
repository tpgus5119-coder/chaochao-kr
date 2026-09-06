#!/usr/bin/env python3
"""기출 기준선 ↔ 우리 모의고사 — 같은 잣대로 재서 나란히 놓는다.

왜 만드나:
  설계도 검사(blueprint_check.py)는 '몇 번에 무엇이 나오는가'를 잰다. 그건 뼈대다.
  그런데 뼈대가 같아도 **살**이 다르면 다른 시험이다 —
  지문이 너무 짧거나, 쓰는 낱말의 등급이 낮거나, 한자어가 적으면
  같은 자리에 있는 다른 난이도의 문제가 된다.
  이 파일이 그 살을 잰다. 앞으로 새 문항은 여기 나온 기준에 맞춰 쓴다.

무엇을 재나 (기출과 우리 것 양쪽에서 똑같이)
  ① 읽기 지문 길이   중앙값·상위 10%      — 난이도의 가장 큰 축
  ② 어휘 등급 분포   A/B/C/목록 밖         — 국립국어원 학습용 어휘 5,965 기준
  ③ 한자어 비율                            — 베트남 학습자에게 '한자 다리'가 걸리는 자리
  ④ 문장 길이       중앙값                 — 한 문장이 몇 자인가
  ⑤ 기출 고빈도 낱말 적중률                — 12회차 내내 나온 말이 우리 것에 있는가

기출 자료는 내려받아 글자화해 둔 폴더를 쓴다(기본값은 아래 SRC).
  python3 tools/baseline_check.py [기출텍스트폴더]
"""
import json, os, re, statistics as st, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
# 기출 통계는 미리 뽑아 둔 것을 쓴다(원본 스캔은 저작권 때문에 저장소에 안 넣는다)
EVID = os.path.join(TOOLS, "topik_evidence.json")

# 기출 실측 — analyze2.py 가 12회차에서 뽑은 값 (2014~2025, TOPIK I·II 각 12벌)
# 여기 숫자를 손으로 고치지 않는다. 새로 재려면 원본 폴더를 주고 --rebuild 를 쓴다.
FALLBACK = {
    "읽기지문": {"TOPIK I": {"중앙값": 56, "상위10": 219, "범위": [45, 70]},
                 "TOPIK II": {"중앙값": 100, "상위10": 376, "범위": [72, 164]}},
}


def nikl():
    """국립국어원 학습용 어휘 — {표제어: (등급, 한자어인가)}"""
    out = {}
    with open(os.path.join(TOOLS, "nikl_5965.tsv"), encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 5:
                continue
            w = re.sub(r"\d+$", "", p[1])          # '가격03' → '가격'
            # 풀이 칸에는 한자와 용례가 섞여 있다("가득 | ~ 차다"). 한자가 있어야 한자어다 —
            # 이걸 안 걸러서 처음에 한자어 비율이 44%로 부풀어 나왔다.
            out[w] = (p[4].strip(), bool(re.search(r"[\u4e00-\u9fff]", p[3])))
    return out


def words(text, kiwi):
    """뜻을 지닌 낱말만 남긴다 — 조사·어미·기호는 난이도와 상관이 없다.

    동사·형용사는 **사전형으로 되돌린다.** 형태소 분석기는 어간만 준다('읽', '좋', '고르')
    는데 국립국어원 표는 사전형('읽다', '좋다', '고르다')으로 적혀 있다.
    이걸 안 맞추면 동사·형용사가 통째로 '목록 밖'으로 떨어진다 —
    처음에 '목록 밖' 1위가 있·고르·읽이었고, 그래서 등급 분포가 전부 어긋나 있었다.
    """
    keep = {"NNG", "NNP", "MAG", "XR"}
    out = []
    for t in kiwi.tokenize(text):
        if t.tag in keep:
            out.append(t.form)
        elif t.tag in ("VV", "VA"):
            out.append(t.form + "다")
    return out


def profile(texts, kiwi, lex):
    """글 묶음 하나의 됨됨이 — 길이·등급·한자어."""
    lens = [len(t) for t in texts if t]
    sents = [s for t in texts for s in re.split(r"(?<=[.!?다])\s+", t) if len(s) > 3]
    ws = [w for t in texts for w in words(t, kiwi)]
    g = Counter(lex.get(w, ("밖", False))[0] for w in ws)
    han = sum(1 for w in ws if lex.get(w, ("밖", False))[1])
    n = max(1, len(ws))
    return {
        "글수": len(lens),
        "길이중앙": st.median(lens) if lens else 0,
        "길이상위10": sorted(lens)[int(len(lens) * 0.9)] if len(lens) >= 10 else (max(lens) if lens else 0),
        "문장중앙": st.median([len(s) for s in sents]) if sents else 0,
        "낱말수": len(ws),
        "등급": {k: round(100 * g.get(k, 0) / n, 1) for k in ("A", "B", "C", "밖")},
        "한자어": round(100 * han / n, 1),
        "어휘": Counter(ws),
    }


def bar(p, width=22):
    return "█" * round(p / 100 * width)


def main():
    from kiwipiepy import Kiwi
    kiwi, lex = Kiwi(), nikl()

    ex = json.load(open(os.path.join(ROOT, "data", "ko_exams.json"), encoding="utf-8"))
    # 우리 것 — 시험별로 '읽는 글'과 '듣는 대본'을 갈라 모은다
    ours = {}
    for e in ex["exams"]:
        fam = {"topik-1": "TOPIK I", "topik-2-read": "TOPIK II",
               "topik-2-listen": "TOPIK II 듣기"}.get(e["id"])
        if not fam:
            continue
        seen = ours.setdefault(fam, {"읽기": [], "듣기": [], "전체": []})
        for q in e["questions"]:
            # 길이를 잴 때 우리만 빈칸 문항을 빼면 안 된다. 기출 쪽은 '문항 본문 글자 수'라
            # 한 문장짜리 빈칸 문항도 세어 들어가 있다. 우리는 그 문장을 물음 둘째 줄에
            # 두었을 뿐이라, 빼고 재면 우리 중앙값만 부풀어 오른다(95자 대 실제).
            body = q.get("passage") or (q["stem"].split("\n")[1] if "\n" in q["stem"] else "")
            # **문항마다** 센다. 기출 쪽 수치가 '문항 본문 글자 수'라 묶음 지문이
            # 3문항에 걸리면 세 번 세어져 있다. 우리만 지문을 한 번씩 세면
            # 긴 지문이 실제보다 묻혀 상위 10%가 낮게 나온다.
            if body and not q.get("audio"):
                seen["읽기"].append(body)
            if q.get("script"):
                t = " ".join(re.sub(r"^[남여]:\s*", "", s) for s in q["script"])
                if t not in seen["듣기"]:
                    seen["듣기"].append(t)
            # 어휘 비교는 **시험지 전체**로 한다 — 기출 쪽도 발문·보기가 다 들어 있는
            # 통짜 텍스트라, 우리만 지문으로 재면 잣대가 어긋난다.
            seen["전체"].append(" ".join([q.get("stem", ""), q.get("passage", "")]
                                         + [str(o) for o in q["options"]]
                                         + (q.get("script") or [])))

    print("═" * 74)
    print(" 기출 기준선 ↔ 우리 모의고사 — 같은 잣대")
    print("═" * 74)

    ev = json.load(open(EVID, encoding="utf-8")) if os.path.exists(EVID) else None
    base = (ev or {}).get("읽기지문") or FALLBACK["읽기지문"]

    for fam in ("TOPIK I", "TOPIK II"):
        if fam not in ours:
            continue
        p = profile(ours[fam]["읽기"], kiwi, lex)
        b = base[fam]
        print(f"\n■ {fam} 읽기 지문  (우리 글 {p['글수']}편)")
        d = p["길이중앙"] - b["중앙값"]
        mark = "맞음" if abs(d) <= b["중앙값"] * 0.25 else ("짧음" if d < 0 else "긺")
        print(f"   길이 중앙값   기출 {b['중앙값']:>4}자  │ 우리 {p['길이중앙']:>4.0f}자   → {mark} ({d:+.0f}자)")
        d2 = p["길이상위10"] - b["상위10"]
        mark2 = "맞음" if abs(d2) <= b["상위10"] * 0.3 else ("짧음" if d2 < 0 else "긺")
        print(f"   상위 10% 길이 기출 {b['상위10']:>4}자  │ 우리 {p['길이상위10']:>4.0f}자   → {mark2} ({d2:+.0f}자)")
        print(f"   문장 중앙값                   │ 우리 {p['문장중앙']:>4.0f}자")

        # 어휘는 시험지 전체끼리 견준다
        w = profile([" ".join(ours[fam]["전체"])], kiwi, lex)
        gb = ((ev or {}).get("시험지전체") or {}).get(fam)
        print(f"   ── 어휘 (시험지 전체 기준 · 우리 낱말 {w['낱말수']:,})")
        for k in ("A", "B", "C", "밖"):
            mine, theirs = w["등급"][k], (gb or {}).get("등급", {}).get(k)
            line = f"     {k:<2} 기출 {theirs:>5.1f}%  │ 우리 {mine:>5.1f}%" if theirs is not None \
                   else f"     {k:<2}                 │ 우리 {mine:>5.1f}%"
            if theirs is not None:
                line += f"   {mine - theirs:+5.1f}%p"
            print(line + "  " + bar(mine))
        ht = (gb or {}).get("한자어")
        print(f"     한자어 기출 {ht:>5.1f}%  │ 우리 {w['한자어']:>5.1f}%   {w['한자어'] - ht:+5.1f}%p"
              if ht is not None else f"     한자어            │ 우리 {w['한자어']:>5.1f}%")

    if "TOPIK II 듣기" in ours:
        p = profile(ours["TOPIK II 듣기"]["듣기"], kiwi, lex)
        print(f"\n■ TOPIK II 듣기 대본  (우리 대본 {p['글수']}편)")
        print(f"   길이 중앙값 {p['길이중앙']:.0f}자 · 문장 중앙값 {p['문장중앙']:.0f}자 · 한자어 {p['한자어']}%")
        print(f"   어휘 등급   " + "  ".join(f"{k} {p['등급'][k]:>4.1f}%" for k in ("A", "B", "C", "밖")))

    # ⑤ 기출 고빈도 낱말 적중률
    if ev and ev.get("고빈도"):
        # 적중률도 **시험지 전체**로 센다 — 지문만 보면 보기에 쓴 말이 빠져
        # 실제보다 낮게 나온다(처음에 68%로 나왔는데 실은 89%였다).
        allw = Counter()
        for fam in ours:
            for t in ours[fam]["전체"]:
                allw.update(words(t, kiwi))
        # 기출 파일 앞머리(저작권 표시·응시 안내)에서 딸려 온 말은 문항의 어휘가 아니다.
        # 사람 이름(민수·수미)은 우리가 베트남 이름을 쓰기로 한 것이라 뺀다.
        SKIP = {"저작", "법령", "지문", "민수", "수미"}
        top = [w for w in ev["고빈도"] if w not in SKIP]
        hit = [w for w in top if allw.get(w)]
        print(f"\n■ 기출 고빈도 낱말 적중률  {len(hit)}/{len(top)} ({len(hit)/len(top):.0%})")
        miss = [w for w in top if not allw.get(w)][:25]
        if miss:
            print("   우리 글에 아직 안 나온 말:", " ".join(miss))
    else:
        print(f"\n   (기출 고빈도 목록이 없습니다 — {os.path.basename(EVID)} 를 만들어 두면 적중률까지 잽니다)")

    print("\n" + "═" * 74)
    print(" 기준: 국립국제교육원 공개 기출 12회차(2014~2025) 실측 · 국립국어원 학습용 어휘 5,965")
    print("═" * 74)


if __name__ == "__main__":
    main()
