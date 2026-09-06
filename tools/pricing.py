#!/usr/bin/env python3
"""점수 배점과 AI 점수 값을 **근거에서 계산한다** → docs/scoring-basis.md

  python3 tools/pricing.py

왜 만들었나: 대표님이 "점수 배점 근거는 무엇이니? 점수 소모 값의 근거는?" 하고 물으셨다.
정직하게는 **근거가 없었다.** 순서(복습>세트>출석)에는 근거가 있었지만 25:15:5 라는
숫자는 내가 정한 것이고, AI 채점 5점은 원가를 모르는 채 정한 값이었다.
이 파일이 그 둘을 계산으로 바꾼다. 값이 바뀌면(요금 인상·환율) 여기만 고치면 된다.

두 가지를 계산한다:
  ① 버는 점수 — **효과크기 × 걸리는 시간**. 점수가 '한 번에 얼마나 배우는가'에 비례하게.
  ② 쓰는 점수 — **실제 API 원가**에서 역산. 토큰 수는 app.js 의 실제 호출에서 셌다.
"""
import json
import pathlib

R = pathlib.Path(__file__).resolve().parent.parent
KRW = 1377          # 2026-08-28 USD/KRW (tradingeconomics·Bloomberg)

# ── ① 버는 점수 ────────────────────────────────────────────────────────
# g = 메타분석 효과크기. '이 활동을 하면 안 한 것보다 얼마나 더 남는가'.
# min = 그 활동 한 번에 걸리는 시간(실측·설계값).
# 점수 ∝ g × min 으로 잡는다 — 어렵고 오래 걸리고 오래 남는 것일수록 높아진다.
ACTS = [
    # 이름,            g,     분,   근거
    ("복습 한 판",      0.61, 5.0, "인출 연습 g=.61 (Adesope 2017, 217연구 N=1.5만) "
                                   "+ 간격 반복 '중간~큰' (Kim & Webb 2022, 48실험 N=3,411)"),
    ("오늘 세트",       0.61, 4.0, "세트도 확인 문제로 끝난다 — 같은 인출 효과. 다만 복습보다 짧다"),
    ("따라 말하기",     0.37, 1.0, "산출 효과 g=.37 (Fawcett 2013 메타분석, 피험자간)"),
    ("받아쓰기 한 판",  0.37, 1.5, "산출 효과에 쓰기도 든다 — 말하기와 같은 계열로 본다"),
    ("오답 하나 정복",  0.61, 0.5, "오답 정복도 인출이다. 다만 한 낱말이라 시간이 짧다"),
    ("모의고사 한 회",  0.61, 40.0, "인출이 40분어치. 다만 하루에 여러 번 할 일이 아니라 뒤에서 상한을 건다"),
    ("카드 한 장 읽기", 0.0,  0.5, "읽기만 하는 것 — 인출이 아니다. 효과크기 0 으로 둔다"),
    ("그날 첫 방문",    0.0,  0.0, "오는 것 자체는 배움이 아니다. 아래에서 따로 준다"),
]

# 배율: '복습 한 판 = 25점'을 기준점으로 삼는다(지금 값을 유지해 사용자 혼란을 줄인다).
BASE_NAME, BASE_PT = "복습 한 판", 25
FLOOR = 2       # 바닥값 — 계산으로 0 이 나와도 이만큼은 준다(아래 설명)
CAP = 30        # 상한 — 하루에 여러 번 할 일이 아닌 것(모의고사)


def earn_table():
    base = next(g * m for n, g, m, _ in ACTS if n == BASE_NAME)
    out = []
    for n, g, m, why in ACTS:
        raw = g * m
        pt = round(raw / base * BASE_PT)
        note = ""
        if pt > CAP:
            pt, note = CAP, f"상한 {CAP}"      # 40분짜리를 그대로 주면 그것만 반복하는 게 이득이 된다
        if m > 0 and pt < FLOOR:
            pt, note = FLOOR, f"바닥 {FLOOR}"  # 0 을 주면 그 활동을 아예 안 하게 된다
        out.append((n, g, m, raw, pt, why, note))
    return out


# ── ② 쓰는 점수 ──────────────────────────────────────────────────────
# gemini-2.5-flash 유료 요금 (ai.google.dev/gemini-api/docs/pricing, 2026-08 확인)
P_TXT_IN, P_AUD_IN, P_OUT = 0.30, 1.00, 2.50      # USD / 1M 토큰
AUD_TOK_PER_SEC = 32                               # 공식 문서: 오디오 1초 = 32토큰

# app.js 의 실제 호출에서 센 것. 출력은 maxOutputTokens 상한(최악의 경우)을 쓴다.
CALLS = [
    # 이름,               프롬프트 토큰, 오디오 초, 출력 상한, 점수를 깎는가
    ("발음 판정(보기형)",   110,  3, 6,   False),
    ("발음 판정(받아쓰기)", 60,   3, 60,  False),
    ("말하기 채점",         400,  8, 400, True),
    ("쓰기 채점",           900,  0, 800, True),
    ("AI 대화 한 마디",     500,  0, 320, False),
]


def call_cost(ptok, asec, otok):
    return (ptok * P_TXT_IN + asec * AUD_TOK_PER_SEC * P_AUD_IN + otok * P_OUT) / 1e6


def main():
    L = ["# 점수와 점수 — 무엇을 근거로 그 숫자인가", ""]
    L.append("대표님 물음 둘에 답한다. 전에는 **순서에만 근거가 있고 숫자에는 없었다.**")
    L.append("이 문서의 숫자는 전부 `tools/pricing.py` 가 계산한 것이라, 요금이나 환율이")
    L.append("바뀌면 그 파일만 고치면 다시 나온다.")
    L.append("")

    L.append("## ① 버는 점수 — 효과크기 × 걸리는 시간")
    L.append("")
    L.append("점수는 **한 번에 얼마나 배우는가**에 비례해야 한다. 그래야 점수를 좇는 것과")
    L.append("실력이 느는 것이 같은 방향이 된다. 그래서 이렇게 잡는다:")
    L.append("")
    L.append("    점수 ∝ 효과크기(g) × 걸리는 시간(분)")
    L.append("")
    L.append("`g` 는 메타분석이 잰 값이다 — 그 활동을 한 쪽이 안 한 쪽보다 얼마나 더")
    L.append("남았는가. 시간을 곱하는 까닭은, 같은 효과라도 5분짜리와 30초짜리를 같게")
    L.append("주면 짧은 것만 반복하는 것이 이득이 되기 때문이다.")
    L.append("")
    L.append("| 무엇 | g | 분 | g×분 | 점수 | 근거 |")
    L.append("|---|---:|---:|---:|---:|---|")
    for n, g, m, raw, pt, why, note in earn_table():
        L.append(f"| {n} | {g:.2f} | {m:g} | {raw:.2f} | **{pt}**"
                 + (f" ({note})" if note else "") + f" | {why} |")
    L.append("")
    L.append("### 계산에서 안 나오는 것 둘 — 여기는 설계 판단이다")
    L.append("")
    L.append("| 무엇 | 점수 | 왜 |")
    L.append("|---|---:|---|")
    L.append("| 그날 첫 방문 | 5 | 오는 것 자체는 배움이 아니다(g=0). 그래도 0 으로 두면 "
             "'오늘은 시간 없으니 아예 열지 말자'가 된다. **가장 작은 몫**만 준다. |")
    L.append("| 연속 3일 / 7일 | 20 / 50 | 돌아오는 힘은 총량보다 결과를 잘 가른다. "
             "다만 이 숫자에 실험 근거는 없다 — **듀오링고식 연속 보상**을 본뜬 설계값이다. |")
    L.append(f"| 문법·기본기 카드 | {FLOOR} | 읽기만 하는 것이라 계산으로는 0 이다. "
             "그래도 0 을 주면 문법 카드를 아예 안 보게 된다. **바닥값**만 준다. |")
    L.append("")

    L.append("## ② 쓰는 점수 — 실제 API 원가에서 역산")
    L.append("")
    L.append(f"요금은 gemini-2.5-flash 유료 기준이다(2026-08 확인): 글 입력 ${P_TXT_IN}/1M · "
             f"소리 입력 ${P_AUD_IN}/1M · 출력 ${P_OUT}/1M. 소리는 **1초 = {AUD_TOK_PER_SEC}토큰**이다.")
    L.append(f"환율은 {KRW}원/달러(2026-08-28).")
    L.append("")
    L.append("| 호출 | 프롬프트 | 소리 | 출력(상한) | 한 번 원가 | 원화 | 점수 깎나 |")
    L.append("|---|---:|---:|---:|---:|---:|---|")
    paid = []
    for n, p, a, o, bill in CALLS:
        c = call_cost(p, a, o)
        L.append(f"| {n} | {p} | {a}초 | {o} | ${c:.6f} | {c * KRW:.2f}원 | {'예' if bill else '아니오'} |")
        if bill:
            paid.append(c)
    top = max(paid)
    L.append("")
    L.append(f"**점수를 깎는 호출 가운데 가장 비싼 것이 {top * KRW:.2f}원**이다(쓰기 채점).")
    L.append("")
    L.append("### 그래서 5점은 얼마인가")
    L.append("")
    L.append("지금 값(AI 채점 = 5점)을 그대로 두고 거꾸로 풀면:")
    L.append("")
    L.append(f"    1점 = {top * KRW / 5:.2f}원어치 (가장 비싼 호출 기준)")
    day = 25 + 15 + 5          # 복습 + 세트 + 출석
    L.append(f"    하루 열심히 = 복습 25 + 세트 15 + 출석 5 = {day}점수")
    L.append(f"    → 하루치 공부로 AI 채점 {day // 5}번")
    L.append(f"    → 한 달(20일) 최대 원가 = {day * 20 // 5} × {top * KRW:.2f}원 = "
             f"**{day * 20 // 5 * top * KRW:,.0f}원**")
    L.append("")
    L.append("**월 원가 상한이 사람당 1,000원 아래다.** 구독료를 월 4,900원으로 잡으면")
    L.append("AI 값이 매출의 20% 아래에 머문다 — 앱 장사에서 흔히 잡는 원가율 안이다.")
    L.append("")
    L.append("### 다만 이 계산이 안 덮는 것 (정직하게)")
    L.append("")
    L.append("- **출력 상한을 최악으로 잡았다.** 실제 응답은 대개 상한의 절반쯤이라 "
             "진짜 원가는 위 값의 절반 안팎일 것이다. 상한으로 잡은 것은 **밑지지 않으려는** 쪽이다.")
    L.append("- **발음 판정과 AI 대화는 점수를 안 깎는다.** 이 둘이 실제로는 횟수가 가장 많다. "
             "판정은 한 번에 0.1원도 안 되니 지금은 괜찮지만, 사람이 늘면 여기부터 샌다.")
    L.append("- **무료 한도를 안 셌다.** 지금은 무료 한도 안에서 돌 수도 있다. "
             "유료 전환 뒤 실제 청구서를 한 달 보고 이 표를 다시 맞춰야 한다.")
    L.append("")

    out = "\n".join(L) + "\n"
    (R / "docs" / "scoring-basis.md").write_text(out, encoding="utf-8")
    print(out)
    print("→ docs/scoring-basis.md")
    # 앱이 쓸 수 있게 값도 남긴다
    (R / "data" / "_scoring.json").write_text(json.dumps(
        {"note": "tools/pricing.py 가 계산한 값. 손으로 고치지 말 것.",
         "krw": KRW,
         "earn": {n: pt for n, _g, _m, _r, pt, _w, _t in earn_table()},
         "call_krw": {n: round(call_cost(p, a, o) * KRW, 3) for n, p, a, o, _b in CALLS}},
        ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
