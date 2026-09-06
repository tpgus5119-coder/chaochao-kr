#!/usr/bin/env python3
"""생산현장어 8강을 직무 차례의 **제자리**에 넣는다 → data/days.json

왜 (대표님 지적, 2026-08-29): 처음에는 '새로 만들었다'는 이유로 맨 뒤에 붙였다.
그건 차례가 아니라 만든 순서다. 배우는 사람에게는 아무 뜻이 없다.

직무 차례는 원래 이렇게 짜여 있다:
  ① 공통 기초 → ② 업종별(봉제·전자·사무) → ③ 공통 생활·행정
  → ④ 공통 관리 → ⑤ 업종별 심화
새 여덟 강은 모두 **업종을 안 가리는 공통**이므로 ①과 ④에 나눠 넣는다.
  · 공정·설비 = 기초다. '지시 알아듣기' 와 '기계와 전기' 옆에 둔다.
  · 검사·원인·절차 = 업종별 품질 강의를 배우기 전에 알아야 하는 공통 바탕이다.
  · 사람·부담·앞날 = 관리다. '회의 진행' 뒤에 잇는다.

`cat`(업종)도 채운다. 여덟 강만 비어 있어서 업종 거르개가 제대로 못 걸렀다.
Day 113 은 이름을 바꾼다 — 봉제 Day 90 도 '작업 표준서 읽기' 라 둘이 겹쳐 보였다.
  90  = 도면·기호·페이지 (문서 자체를 읽는 법)
  113 = 과정·순서·방법  (일하는 절차)
"""
import json, pathlib

R = pathlib.Path(__file__).resolve().parent.parent
P = R / "data" / "days.json"
d = json.loads(P.read_text(encoding="utf-8"))
by = {x.get("day"): x for x in d["days"]}

NEW = [107, 108, 109, 110, 111, 112, 113, 114]
for n in NEW:
    by[n]["cat"] = "공통"
by[113]["theme"] = "절차와 방법"

# (이 강 **뒤에** 넣는다, 넣을 강들)
AFTER = [
    (28,  [107]),        # 지시 알아듣기 → 공정과 작업 흐름
    (29,  [110]),        # 기계와 전기   → 설비와 재료
    (40,  [108, 109, 113]),  # 전화와 연락 → 외관 검사 · 원인과 대책 · 절차와 방법
    (85,  [111, 112, 114]),  # 회의 진행   → 사람 뽑기 · 일이 벅찰 때 · 앞을 내다보기
]

work = sorted([x for x in d["days"] if x.get("track") == "work"], key=lambda x: x.get("n", 0))
seq = [x for x in work if x.get("day") not in NEW]
for anchor, adds in AFTER:
    i = next(k for k, x in enumerate(seq) if x.get("day") == anchor)
    for j, day in enumerate(adds):
        seq.insert(i + 1 + j, by[day])

for i, x in enumerate(seq, 1):
    x["n"] = i
P.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"직무 {len(seq)}강 차례를 다시 매겼다\n")
for x in seq:
    star = " ←" if x.get("day") in NEW else ""
    print(f"  n={x['n']:>3}  Day {str(x['day']):>4}  {x.get('cat',''):<3} {x.get('theme','')}{star}")
