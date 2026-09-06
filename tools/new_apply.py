#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""검수 끝난 새 낱말을 **앱에 넣는다** → data/order.json

대표님 지시 (2026-09-01): "모든 검수 진행하고 최종 어플에 등록해. 이미지와 tts도 당연히."

## 넣는 방식
새 일상 과정을 **1권부터 다시** 짠다 (docs/일상-목차.md 46꼭지 차례대로).
한 강 15낱말, 한 챕터 7강 — 지금 앱과 같은 결이다.
**옛 낱말은 지우지 않는다.** '예전 낱말' 권으로 뒤에 남긴다 —
이미 외운 사람이 잃는 것이 없어야 한다.

## 무엇만 넣나
최종 검수를 통과한 것만 (fin=ok). 사전에 없거나(none) 아직 못 본 것은 뺀다.
빼는 것이 아깝지만, **틀린 뜻을 외우게 하는 것보다 낫다.**

소리와 그림은 이 파일을 읽는 도구가 알아서 만든다 —
  tools/gen_audio.py (북부 남녀) · tools/gen_south_vtts.py (남부 남녀)
  tools/gen_word_img.py (그림)

쓰기: python3 tools/new_apply.py [--dry]
"""
import argparse, json, pathlib, sys, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
from new_words import TOPICS

# ── 제목은 **손으로 짓는다** (대표님 지시 2026-09-02: "1권이 목차의 제목이지 마라.
#    제목을 글로 해줘, 그 아래의 것들도 모두").
#    기계가 꼭지 이름을 이어 붙이면 목록이지 제목이 아니다.
#    장 제목은 그 장에서 **할 수 있게 되는 일**을 한 줄로 적는다.
CHAPTER_TITLES = [
 "나를 소개합니다",           # 인사·호칭·나이·이름·나라
 "나와 내 사람들",            # 나라·숫자·가족·직업
 "말을 잇는 법",             # 직업·기본 동사·가리킴·접속·정도
 "때를 말합니다",             # 정도·묻는 말·시간·요일
 "우리 집 하루",             # 요일·하루 일과·집·살림
 "무엇을 먹을까",            # 위치·먹을거리·마실거리·맛
 "사고 팔기",               # 맛·식당·색깔·값·가게
 "길을 나섭니다",            # 가게·옷·길·탈것·장소
 "볼일을 봅니다",            # 장소·관공서·여행·아픈 곳
 "몸과 마음",               # 병원·기분·성격·날씨
 "함께 지내기",              # 날씨·자연·취미·친구·잡담
 "사람들 사이에서",           # 잡담·명절·전화·직장
 "생각을 말합니다",           # 직장·의견·도움 청하기
]
VOL_TITLES = ["첫마디부터 장보기까지", "길에서 사람들 사이로"]

ORDER = R / "data" / "order.json"
NEW = R / "data" / "_new_words.json"
PER_LESSON, PER_CHAPTER = 15, 7
n = lambda s: U.normalize("NFC", str(s)).strip()


def main():
    a = argparse.ArgumentParser(); a.add_argument("--dry", action="store_true"); a = a.parse_args()
    d = json.loads(NEW.read_text(encoding="utf-8"))
    o = json.loads(ORDER.read_text(encoding="utf-8"))

    # 목차 차례대로 낱말을 늘어놓는다 (꼭지 안의 차례는 모은 차례 그대로)
    from collections import Counter
    elsewhere = Counter(n(w["vi"]).lower() for ws in d.values() for w in ws)
    seq, skipped = [], {"검수못함": 0, "사전에없음": 0, "다른 꼭지에 있음": 0}
    for _grp, topic, _c in TOPICS:
        for w in d.get(topic, []):
            # 목차 적합성 판정(Qwen)은 **그대로 믿지 않는다.** 실측으로
            # Chào buổi sáng(좋은 아침)·Chúc ngủ ngon(잘 자요)을 '인사가 아니다'라고 했다.
            # 그래서 '안 어울린다'고 한 것 중 **다른 꼭지에 같은 낱말이 있을 때만** 뺀다 —
            # Chào bố 를 쪼개다 생긴 bố(아버지)는 '가족'에 이미 있으니 인사 꼭지에서 뺀다.
            if w.get("fit") == "drop" and elsewhere.get(n(w["vi"]).lower(), 0) > 1:
                skipped["다른 꼭지에 있음"] += 1; continue
            if w.get("fin") == "none":
                skipped["사전에없음"] += 1; continue
            if w.get("fin") != "ok":
                skipped["검수못함"] += 1; continue
            item = {"vi": n(w["vi"]), "ko": n(w["ko"]),
                    "kr": n(w.get("kr") or ""), "krs": n(w.get("krs") or ""),
                    "topic": topic, "sr": 1, "core": 4}
            if w.get("kr"):
                item["kr_read"] = n(w["kr"])
            seq.append(item)

    # ── 제목을 붙인다 (대표님 지시 2026-09-01: "목차에 제목이 있잖아. 교재처럼")
    #    한 강은 한 꼭지에서만 나오므로 그 꼭지 이름이 곧 강 제목이다.
    #    같은 꼭지가 여러 강에 걸치면 뒤에 (2)·(3) 을 붙인다.
    # **꼭지 경계에서 자른다.** 15개씩 기계적으로 자르면 '3과 나이와 생일'인데
    # 첫 낱말이 호칭인 꼴이 된다 (실측). 한 강에는 한 꼭지의 낱말만 담는다.
    lessons = []
    for _grp, topic, _c in TOPICS:
        ws = [w for w in seq if w.get("topic") == topic]
        if not ws:
            continue
        parts = [ws[i:i + PER_LESSON] for i in range(0, len(ws), PER_LESSON)]
        # 마지막 조각이 다섯 개도 안 되면 앞 강에 붙인다 — 토막 강을 만들지 않는다
        if len(parts) > 1 and len(parts[-1]) < 5:
            last = parts.pop(); parts[-1] = parts[-1] + last
        for j, part in enumerate(parts, 1):
            no = f" ({j})" if len(parts) > 1 else ""
            lessons.append({"t": f"{topic}{no}", "topic": topic, "words": part})

    # 챕터 제목은 그 챕터에 든 꼭지들을 이어 붙인다 — 무엇을 배우는지 보이게
    chapters = []
    for i in range(0, len(lessons), PER_CHAPTER):
        part = lessons[i:i + PER_CHAPTER]
        tops = []
        for l in part:
            if l["topic"] not in tops:
                tops.append(l["topic"])
        i2 = len(chapters)
        name = CHAPTER_TITLES[i2] if i2 < len(CHAPTER_TITLES) else " · ".join(tops[:2])
        chapters.append({"t": name, "sub": " · ".join(tops), "lessons": part})

    # **전에 넣은 새 과정은 걷어낸다.** 표를 안 달아 두면 다시 돌릴 때마다 겹쳐 쌓인다
    # (실측: 두 번 돌리니 '예전 낱말 1권' 안에 새 꼭지가 들어가 있었다).
    # **옛 낱말은 넣지 않는다.** 대표님이 여러 번 말씀하셨다 (2026-08-31, 09-02):
    #   "선배 단어나 과거에 있던 일상단어나 완전히 제외하고 처음부터 다시."
    # 내가 '잃는 것이 없게' 하려고 뒤에 남겨 뒀는데, 그건 지시를 어긴 것이다.
    old = []
    job = [v for v in o["vols"] if v.get("kind") != "life"]
    # 새 과정을 앞에, 예전 낱말을 뒤에
    # 권 하나에 챕터 일곱씩 묶는다
    # 일상은 **한 권**이다 (대표님 지시 2026-09-02 "1권 2권 나누지 마. 하나로 해").
    # 권을 나누면 '어디까지 왔나'가 두 군데로 흩어져 오히려 안 보인다.
    vols = [{"kind": "life", "gen": "new", "title": "일상", "chapters": chapters}]
    o["vols"] = vols + old + job

    print(f"넣을 낱말 {len(seq)} · 강 {len(lessons)} · 챕터 {len(chapters)} · 권 {len(vols)}")
    print("뺀 것", skipped)
    if not a.dry:
        ORDER.write_text(json.dumps(o, ensure_ascii=False), encoding="utf-8")
        print("order.json 에 넣었다")


main()
