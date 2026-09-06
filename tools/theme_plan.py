#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""일상 낱말을 **상황별 챕터**로 다시 묶는다 → data/_theme.json (판정만)

대표님 지시 (2026-08-31): "일상 단어 다시 아예 처음부터 구성해보자"

## 왜 이렇게 묶나 (조사 근거)
· 듀오링고는 주제가 아니라 **CEFR 'can-do'(할 수 있는 것) 상황**이 뼈대다.
  한 단원 = 한 대화 상황. 어휘는 그 안에 배분한다.
· 베트남어 교재도 모두 상황 배열이다 —
  Colloquial Vietnamese 14과: 인사→공항→호텔→전화→길→식당→시장→은행→여행→작별
  Elementary Vietnamese(Harvard) 14과: 문형 중심 · Teach Yourself 18과: 주제형
· **같은 갈래를 한 번에 몰아넣으면 오히려 해롭다** (Tinkham 1993/1997, Waring 1997,
  Erten & Tekin 2008: 즉시 회상 55% vs 44%). 색깔 10개·요일 7개를 한 과에 넣는 것이 그 예다.
  반대로 **한 장면을 이루는 말들**(개구리·뛰다·초록·연못)은 서로 돕는다.
· 그래서: **고르기는 빈도순(지금 그대로), 묶기는 상황별.**
  같은 갈래가 한 레슨에 몰리지 않게 흩는 것은 tools/theme_apply.py 가 한다.

## 지금 상태
낱말이 '선배 시험 빈도순'으로만 늘어서 있어 한 레슨에
'백·꿰매다·머리카락·성격·쑥스러운' 이 뒤섞인다. 장면이 없으니 기억할 고리가 없다.

쓰기: python3 tools/theme_plan.py [--limit N]
"""
import argparse, json, pathlib, sys

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
from qwen import ask_json, up

OUT = R / "data" / "_theme.json"

# 28개 = 일상 4권 × 7챕터. 교재들의 공통 차례를 따르되 뒤로 갈수록 넓어진다.
CH = [
 ("A1", "인사와 첫 만남"),      ("A2", "나와 가족"),        ("A3", "숫자와 셈"),
 ("A4", "시간과 날짜"),        ("A5", "하루 일과"),        ("A6", "집과 방"),
 ("A7", "먹고 마시기"),
 ("B1", "길 묻기와 방향"),      ("B2", "교통과 이동"),      ("B3", "시장과 값"),
 ("B4", "가게에서 사기"),       ("B5", "식당에서 시키기"),   ("B6", "은행·우체국·관공서"),
 ("B7", "전화와 약속"),
 ("C1", "몸과 건강"),          ("C2", "병원과 약국"),      ("C3", "마음과 성격"),
 ("C4", "옷과 꾸미기"),        ("C5", "날씨와 철"),        ("C6", "쉬는 날과 취미"),
 ("C7", "사람 사귀기"),
 ("D1", "학교와 공부"),        ("D2", "일과 직장"),        ("D3", "집 구하기와 살림"),
 ("D4", "여행과 묵을 곳"),      ("D5", "잔치와 명절"),      ("D6", "탈이 났을 때"),
 ("D7", "생각을 말하기"),
]
CODES = [c for c, _ in CH]

ASK = (
    "너는 베트남어 교재를 짜는 편집자다. 낱말마다 **어느 상황 챕터**에 넣을지 하나만 고르라.\n"
    "챕터 목록\n" + "\n".join(f"  {c} {n}" for c, n in CH) + "\n"
    "규칙\n"
    " ① 그 낱말을 **실제로 쓰게 되는 장면**을 고른다 (값을 깎는다 → B3)\n"
    " ② 여러 곳에 되면 **처음 배우기 좋은 쪽**으로 (쉬운 장면 먼저)\n"
    " ③ 어디에도 안 맞는 기본어(그리고·매우·이것)는 **A5** 로 보낸다\n"
    " ④ 반드시 목록에 있는 코드만 쓴다\n"
    '출력은 JSON 배열만: [{"vi":"낱말","ch":"코드"}]\n\n'
)


def walk(v):
    for t in (v.get("tracks") or [v]):
        for c in t["chapters"]:
            for l in c["lessons"]:
                yield from l["words"]


def main():
    a = argparse.ArgumentParser(); a.add_argument("--limit", type=int, default=0); a = a.parse_args()
    if not up():
        print("Qwen 이 안 켜져 있다 — ~/.lmstudio/bin/lms server start"); return

    O = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    life = [w for v in O["vols"] if v.get("kind") != "job" for w in walk(v)]
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    need = [w for w in life if w["vi"] not in have]
    if a.limit: need = need[:a.limit]
    print(f"일상 낱말 {len(life)} · 아직 안 나눈 것 {len(need)}", flush=True)

    for i in range(0, len(need), 25):
        part = need[i:i + 25]
        got = ask_json(ASK, [{"vi": w["vi"], "ko": w["ko"]} for w in part], chunk=25)
        by = {g.get("vi"): g.get("ch") for g in got if isinstance(g, dict)}
        for w in part:
            ch = by.get(w["vi"])
            have[w["vi"]] = ch if ch in CODES else ""      # 빈칸 = 못 정함, 나중에 사람이
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
        if (i // 25) % 8 == 0:
            done = sum(1 for v in have.values() if v)
            print(f"  {min(i+25,len(need))}/{len(need)} · 정해진 것 {done}", flush=True)

    from collections import Counter
    c = Counter(v for v in have.values() if v)
    print(f"\n끝. 나눈 낱말 {sum(c.values())} · 못 정한 것 {sum(1 for v in have.values() if not v)}")
    for code, name in CH:
        print(f"  {code} {name:18} {c.get(code,0):4}장")


main()
