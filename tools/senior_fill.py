#!/usr/bin/env python3
"""자료가 없는 일일 회차를 **주간 시험에서 되살린다** → data/_senior_filled.json

  python3 tools/senior_fill.py

63·65·66·67·76·86·92 회차는 파일 143개 어디에도 없다(시트 이름·본문 전수 확인).
그러나 **주간 시험이 그 주 낱말을 담고 있어** 되살릴 수 있다.

되살리는 근거 — 주간 표의 배열 규칙을 실측했다:
    12주차 낱말을 차례로 훑으며 '이 낱말이 어느 일일 회차 것인가'를 표시하면
        51 52 53 54 51 52 53 54 51 52 53 54 …
    가 나온다. 즉 주간 표는 **4열짜리 표**이고, 열이 곧 일일 회차다.
    표를 왼쪽에서 오른쪽으로 읽었으니 낱말 차례가 `회차1, 회차2, 회차3, 회차4` 로
    번갈아 나온다. 6·11·12주차에서 미상이 0~2개로 이 규칙이 확인된다.

그래서 나누는 법은 둘이다:
  ① 순환이 확인되면 **그 자리(index % 열수)** 로 나눈다 — 원래 회차를 그대로 복원
  ② 확인이 안 되면 **차례대로 균등하게** 나눈다(30개씩)
어느 쪽으로 나눴는지 낱말마다 표시해 둔다(way).
"""
import collections
import json
import pathlib
import sys

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import senior_words as SW                                        # noqa: E402

PER_DAY = 30            # 일일 시험 한 회 낱말 수(실측 표준)


def main():
    src = json.loads((R / "data" / "_senior_words.json").read_text(encoding="utf-8"))
    S = {(s["kind"], s["no"]): s["words"] for s in src["sets"]}
    K = {k: [SW.keyof(w["ko"]) for w in v if SW.keyof(w["ko"])] for k, v in S.items()}
    have = sorted(n for (k, n) in S if k == "일일")
    weeks = sorted(n for (k, n) in S if k == "주간")
    missing = sorted(set(range(1, max(have) + 1)) - set(have))

    filled, report = {}, []
    for wno in weeks:
        wk_words = [w for w in S[("주간", wno)] if SW.keyof(w["ko"])]
        wk = [SW.keyof(w["ko"]) for w in wk_words]
        owned = [n for n in have
                 if len(set(wk) & set(K[("일일", n)])) / max(1, len(K[("일일", n)])) >= .5]
        if not owned:
            continue
        # 이 주가 덮는 회차 구간 안에서 자료가 없는 것들.
        # **구간을 좁게 잡아야 한다.** 처음에 min~max 로 잡았더니 14주차(61,64,95)가
        # 95까지 뻗어 63~92를 통째로 떠안았다 — 95회차는 그 주 것이 아니라 낱말이
        # 겹쳐 딸려 들어온 것이다. 그래서 **이웃한 회차 덩어리**만 구간으로 본다.
        run = [owned[0]]
        for n in owned[1:]:
            if n - run[-1] <= 6:               # 한 주는 4~5회차라 6칸 넘게 벌어지면 딴 주다
                run.append(n)
            else:
                break
        lo, hi = run[0], run[-1] + (5 - len(run) if len(run) < 5 else 0)
        gaps = [m for m in missing if lo <= m <= hi]
        if not gaps:
            continue

        # 이미 아는 낱말은 빼고, 남은 것이 빠진 회차의 몫이다
        known = set()
        for n in owned:
            known |= set(K[("일일", n)])
        left = [w for w in wk_words if SW.keyof(w["ko"]) not in known]
        if not left:
            continue

        # ① 열 순환이 잡히는가 — 아는 낱말의 자리로 열 수를 재 본다
        tags = []
        for w in wk:
            o = [n for n in owned if w in set(K[("일일", n)])]
            tags.append(o[0] if o else None)
        cyc = None
        for c in (4, 5, 3, 6):
            cols = collections.defaultdict(set)
            for i, t in enumerate(tags):
                if t:
                    cols[i % c].add(t)
            # 열마다 회차가 하나로 모이면 그 열 수가 맞다
            if cols and all(len(v) == 1 for v in cols.values()) and len(cols) >= 2:
                cyc = c
                break

        n_gap = len(gaps)
        if cyc:
            # 열이 곧 회차다. 아는 회차가 안 쓰는 열이 빠진 회차의 열이다.
            used_col = {i % cyc: (list(cols[i % cyc])[0] if cols[i % cyc] else None)
                        for i in range(cyc)}
            free = [c for c in range(cyc) if not used_col.get(c)]
            way = "열 순환"
            if len(free) == n_gap:
                assign = dict(zip(free, gaps))
                for i, w in enumerate(wk_words):
                    c = i % cyc
                    if c in assign and SW.keyof(w["ko"]) not in known:
                        filled.setdefault(assign[c], []).append({**w, "way": way, "week": wno})
                report.append((wno, gaps, way, cyc, len(left)))
                continue
        # ② 순환이 안 잡히면 차례대로 균등하게.
        # 한 회차는 30낱말이 표준이므로 **넘치면 자른다.** 안 그러면 19·20주차가
        # 92회차 하나에 116개를 몰아넣는다(주간 낱말 중 다른 회차 것까지 딸려 온다).
        way = "차례 균등"
        room = {g: PER_DAY - len(filled.get(g, [])) for g in gaps}
        left = [w for w in left if SW.keyof(w["ko"]) not in
                {SW.keyof(x["ko"]) for g in gaps for x in filled.get(g, [])}]
        take = min(len(left), sum(max(0, v) for v in room.values()))
        if take <= 0:
            continue
        left = left[:take]
        size = max(1, -(-take // n_gap))          # 올림 — 마지막 회차가 비지 않게
        put = 0
        for g in gaps:
            n = min(size, max(0, room[g]), len(left) - put)
            for w in left[put:put + n]:
                filled.setdefault(g, []).append({**w, "way": way, "week": wno})
            put += n
        report.append((wno, gaps, way, cyc, put))

    print(f"자료 없는 회차 {len(missing)}개: {missing}")
    print(f"주간에서 되살린 회차 {len(filled)}개: {sorted(filled)}\n")
    print("| 주차 | 되살린 회차 | 나눈 법 | 열 | 나눈 낱말 |")
    print("|---:|---|---|---:|---:|")
    for wno, gaps, way, cyc, n in report:
        print(f"| {wno} | {', '.join(map(str, gaps))} | {way} | {cyc or '-'} | {n} |")
    print()
    for no in sorted(filled):
        ws = filled[no]
        print(f"  {no}회차 ← {len(ws)}낱말 ({ws[0]['way']}, {ws[0]['week']}주차에서) "
              f"보기: " + " · ".join(w["ko"][:14] for w in ws[:4]))

    out = R / "data" / "_senior_filled.json"
    out.write_text(json.dumps(
        {"note": "자료가 없는 일일 회차를 주간 시험에서 되살린 것. 원본이 아니라 추정이다.",
         "sets": [{"kind": "일일(추정)", "no": n, "words": filled[n]} for n in sorted(filled)]},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n→ {out}")


if __name__ == "__main__":
    main()
