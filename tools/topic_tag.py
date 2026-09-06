#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낱말마다 **주제**를 붙인다 → data/_topics.json

왜 (2026-08-30, 대표님 지적 "목차구분 개이상함")
  내가 만든 알아보는 말(키워드)로는 낱말의 43%밖에 못 잡았다. 나머지 57%가
  「두루 쓰는 말 7 — 요금 · 부주의한 · 소중한」 같은 이름 없는 덩어리가 되었다.
  주제를 못 붙이는 게 문제지 목차 층이 문제가 아니다.
  그래서 **주제 목록을 정해 주고** 무료 AI 대리인에게 고르게 한다.
  스스로 주제를 짓게 하면 낱말 25개에 주제 21개가 나온다 — 목록을 반드시 준다.
쓰기: python3 tools/topic_tag.py [--part N --of M]
"""
import argparse, json, pathlib, re, subprocess, sys, time, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
URL = "https://viet-ai.chaochao-app.workers.dev"
# 이 일은 **Qwen 에게 넘겨도 되는 일**이다 — 주제 붙이기.
#   틀려도 사람이 알아볼 수 있는 갈래라 제미나이 몫을 아끼는 편이 낫다.
#   CHAO_LOCAL=1 로 돌리면 이 맥의 Qwen 이 한다 (tools/ai.py 참고).
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from ai import ask_text as _ask_text

ORIGIN = "https://tpgus5119-coder.github.io"
OUT = R / "data" / "_topics.json"
CHUNK = 30

# 주제 목록 — 교재 단원 이름을 바탕으로, 선배 낱말이 실제로 무엇이었나를 보고 넓혔다.
# **이 목록 밖의 주제는 만들지 못하게 한다.**
TOPICS = [
 "인사와 호칭", "가족", "나와 이력", "숫자와 셈", "때와 날짜", "날씨와 계절",
 "몸과 건강", "병원과 약", "감정과 마음", "성격과 사람됨", "모습과 색깔", "크기와 정도",
 "집과 살림", "옷과 몸단장", "먹고 마시기", "식당에서", "사고팔기", "돈과 거래",
 "길과 방향", "탈것과 이동", "여행과 관광", "호텔과 숙소",
 "학교와 공부", "말과 글", "전화와 연락", "여가와 취미", "운동과 경기",
 "일터와 직장", "회의와 보고", "서류와 절차", "공장과 기계", "품질과 안전",
 "자연과 환경", "동식물", "사회와 나라", "문화와 풍습", "역사와 전쟁",
 "동작 — 몸으로 하는 일", "동작 — 주고받기", "동작 — 생각하고 말하기", "동작 — 되어감과 변화",
 "이어 주는 말", "묻고 답하기", "때·정도를 나타내는 말",
]

ASK = ("아래 베트남어 낱말을 **주어진 주제 목록 중 하나**로 분류해라.\n"
       "규칙: ① 목록에 없는 주제는 절대 만들지 마라 ② 낱말 하나에 주제 하나\n"
       "③ 헷갈리면 그 낱말을 **배울 때 어느 단원에 넣겠는지**로 정해라\n"
       "출력은 JSON 배열만. 설명 금지.\n"
       '형식: [{"w":"낱말","t":"주제"}]\n\n주제 목록:\n')

def norm(v):
    return re.sub(r"\s+", " ", U.normalize("NFC", str(v)).strip().lower())

def ask(words):
    t = _ask_text(ASK + " / ".join(TOPICS) + "\n\n낱말:\n" +
                  "\n".join(f"- {w['vi']} ({w['ko'][:18]})" for w in words), max_tokens=2500)
    try:
        return json.loads(re.search(r"\[.*\]", t, re.S).group(0))
    except Exception:
        return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, default=0); ap.add_argument("--of", type=int, default=1)
    a = ap.parse_args()
    global OUT
    if a.of > 1: OUT = R / "data" / f"_topics-{a.part}.json"
    course = json.loads((R / "data" / "course.json").read_text(encoding="utf-8"))
    need = [{"vi": w["vi"], "ko": w["ko"]}
            for v in course["vols"] for u in v["units"] for c in u["chapters"] for w in c["words"]]
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    done = dict(have)
    for f in (R / "data").glob("_topics*.json"):
        if f != OUT:
            try: done.update(json.loads(f.read_text(encoding="utf-8")))
            except Exception: pass
    if a.of > 1: need = need[a.part::a.of]
    need = [w for w in need if norm(w["vi"]) not in done]
    print(f"주제를 붙일 낱말 {len(need)}개", flush=True)
    ok = set(TOPICS); bad = 0
    for i in range(0, len(need), CHUNK):
        part = need[i:i + CHUNK]
        for g in ask(part):
            w, t = norm(g.get("w", "")), str(g.get("t", "")).strip()
            if not w or t not in ok: bad += 1; continue
            have[w] = t
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"  {i + len(part)}/{len(need)} · 목록 밖 누적 {bad}", flush=True)
        time.sleep(1.0)
    print(f"끝. 주제 붙인 낱말 {len(have)}개", flush=True)
main()
