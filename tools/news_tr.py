#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""영어 기사를 **한국어로 옮긴다** — 같은 잣대로 점수를 매기기 위해

대표님 지시 (2026-09-02): "영어 기사를 번역해서 비교해 주면 되잖아.
                          다른 점은 영어라는 점밖에 없는데."

## 왜
점수 낱말(비자·최저임금·병원…)이 전부 한국어라 **영어 제목은 늘 0점**이었다.
VnExpress 에서 하루 36건을 받아 놓고 한 건도 안 뽑혔다 (2026-09-02 실측).
영어 낱말표를 따로 두는 것보다 **옮겨서 같은 표로 재는 것**이 옳다 —
낱말표가 둘이면 둘이 어긋난다.

## 어떻게
Qwen 이 제목과 본문 첫머리를 한국어로 옮긴다. **고르는 일이 아니라 옮기는 일**이라
지어낼 자리가 적고, 틀려도 점수가 조금 어긋날 뿐이다.
옮긴 것은 `t_ko`·`body_ko` 에 담는다 — 원문은 그대로 둔다.

쓰기: from news_tr import translate_titles; translate_titles(cand)
"""
import json, pathlib, re, sys

ASK = ("아래 영어 기사 제목과 첫머리를 한국어로 옮겨라.\n"
       "규칙\n"
       " ① 뜻만 옮긴다. 요약하거나 보태지 마라\n"
       " ② 사람·회사·지역 이름은 그대로 (Samsung → 삼성, Hanoi → 하노이)\n"
       " ③ 제목은 한 줄, 첫머리는 두 문장 이내\n"
       '출력은 JSON 배열만: [{"i":번호,"t":"제목","b":"첫머리"}]\n\n')


def is_en(t):
    """영어 기사인가 — 한글이 거의 없으면 영어로 본다"""
    ko = len(re.findall(r"[가-힣]", t))
    return ko < 3 and len(re.findall(r"[A-Za-z]", t)) > 10


def translate_titles(cands):
    """영어 기사에 t_ko·body_ko 를 채운다. 목록을 그 자리에서 고친다."""
    todo = [(i, c) for i, c in enumerate(cands) if is_en(c.get("t", ""))]
    if not todo:
        return 0
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    try:
        from qwen import ask_json, up
        if not up():
            print("  Qwen 이 꺼져 있어 번역을 건너뛴다"); return 0
    except Exception as e:
        print(f"  번역 건너뜀: {e}"); return 0

    items = [{"i": i, "title": c["t"], "body": (c.get("body") or "")[:220]}
             for i, c in todo]
    got = ask_json(ASK, items, chunk=6, max_tokens=1600) or []
    n = 0
    for g in got:
        if not isinstance(g, dict):
            continue
        try:
            i = int(g.get("i"))
        except Exception:
            continue
        if not (0 <= i < len(cands)):
            continue
        t = str(g.get("t") or "").strip()
        b = str(g.get("b") or "").strip()
        # 한글이 없으면 옮긴 것이 아니다 — 안 받는다
        if len(re.findall(r"[가-힣]", t)) < 3:
            continue
        cands[i]["t_ko"] = t
        cands[i]["body_ko"] = b
        n += 1
    print(f"  영어 기사 {len(todo)}건 중 {n}건을 한국어로 옮겼다")
    return n
