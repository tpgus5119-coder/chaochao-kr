#!/usr/bin/env python3
"""19기와 20기 선배 단어시험이 **같은 시험인가**를 재고, 생산관리 카톡방 낱말을 살핀다.

  python3 tools/senior_compare.py            → docs/senior-compare.md
  python3 tools/senior_compare.py --json     → data/_senior_pool.json 도

대표님 물음 셋에 답하려고 만들었다:
  ① 19기 낱말은 20기와 같은가 다른가
  ② 생산관리 카톡방 파일은 쓸모가 있는가
  ③ 앞의 것들이 우리 앱 낱말과 겹치는가

두 잣대로 잰다 — 어느 하나만 쓰면 틀리게 읽힌다:
  · **뜻으로**   `keyof` 로 한국어만 남겨 견준다. 19기는 `blank – 빈칸`,
    20기는 `빈칸 (blank)` 라 글자 그대로면 남남이 된다.
  · **말로**     베트남어를 견준다. 성조는 **절대 벗기지 않는다**
    (phóng ≠ phòng — 벗기면 딴 낱말이 같은 낱말로 보인다).
뜻이 같아도 말이 다를 수 있고(같은 뜻 다른 낱말), 말이 같아도 뜻풀이가 다를 수 있다.
"""
import argparse
import json
import pathlib
import re
import sys
import unicodedata
import warnings

warnings.filterwarnings("ignore")
R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import senior_words as SW                                          # noqa: E402

KAKAO = SW.GI["19"] / "생산관리 카톡방 단어 정리.xlsx"


def viof(s):
    """베트남어를 견줄 수 있게 다듬는다. **성조는 남긴다.**"""
    s = unicodedata.normalize("NFC", (s or "").lower())
    s = re.sub(r"[(（][^)）]*[)）]", " ", s)          # 괄호 풀이 걷어내기
    s = re.sub(r"[^0-9a-zà-ỹ\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def venn3(A, B, C, names=("A", "B", "C")):
    """세 뭉치를 일곱 칸으로 가르고 **스스로 검산한다.**

    왜 검산을 도구에 박아 넣나: 이 표를 처음 냈을 때 '19기+앱 165' 처럼
    **껍데기 조각**을 교집합인 양 늘어놓아 '둘 겹침이 셋 겹침보다 작다'는
    말이 안 되는 그림이 나왔다. 숫자는 맞았고 이름이 틀렸다.
    이제 조각과 교집합을 따로 돌려주고, 어긋나면 그 자리에서 멈춘다.
    """
    a, b, c = names
    only = {f"{a}만": A - B - C, f"{b}만": B - A - C, f"{c}만": C - A - B,
            f"{a}∩{b}만": (A & B) - C, f"{a}∩{c}만": (A & C) - B,
            f"{b}∩{c}만": (B & C) - A, f"{a}∩{b}∩{c}": A & B & C}
    pair = {f"{a}∩{b}": A & B, f"{a}∩{c}": A & C, f"{b}∩{c}": B & C}
    tri = A & B & C

    ks = list(only)
    for i, x in enumerate(ks):                       # ① 칸끼리 겹치면 안 된다
        for y in ks[i + 1:]:
            assert not (only[x] & only[y]), f"칸이 겹친다: {x} × {y}"
    assert sum(len(v) for v in only.values()) == len(A | B | C), "칸 합이 합집합과 다르다"
    for nm, S_ in ((a, A), (b, B), (c, C)):          # ② 칸을 도로 모으면 원래 크기
        got = sum(len(v) for k, v in only.items() if nm in k)
        assert got == len(S_), f"{nm} 복원 실패 {got} ≠ {len(S_)}"
    ie = (len(A) + len(B) + len(C) - len(A & B) - len(A & C) - len(B & C) + len(tri))
    assert ie == len(A | B | C), "포함배제가 안 맞는다"
    for nm, v in pair.items():                       # ③ 쌍 ≥ 삼중 (이게 깨지면 계산이 틀린 것)
        assert len(v) >= len(tri), f"{nm}({len(v)}) < 삼중({len(tri)}) — 있을 수 없다"
    return only, pair, tri


def load(gi):
    """기수 하나를 {(갈래, 번호): [(뜻열쇠, 말열쇠, 원래한국어, 원래베트남어)]} 로."""
    suffix = "" if gi == "20" else f"-{gi}"
    p = R / "data" / f"_senior_words{suffix}.json"
    if not p.exists():
        raise SystemExit(f"먼저 돌려라: python3 tools/senior_words.py --gi {gi} --json")
    out = {}
    for s in json.loads(p.read_text(encoding="utf-8"))["sets"]:
        out[(s["kind"], s["no"])] = [
            (SW.keyof(w["ko"]), viof(w["vi"]), w["ko"], w["vi"]) for w in s["words"]]
    return out


def kakao():
    """카톡방 낱말장을 읽는다 — **머리글이 없고 열이 뒤집혀 있다**(베트남어 | 한국어).

    시험지가 아니라 실제 공장 카톡방에서 오간 말을 선배가 그때그때 적어 둔 것이다.
    그래서 낱말만이 아니라 **구절과 문장**이 섞여 있고, 줄임말이 그대로 나온다
    (`ko` = `không`, `Cdoan` = `công đoạn`).
    """
    import openpyxl
    wb = openpyxl.load_workbook(KAKAO, data_only=True, read_only=True)
    out = []
    for r in wb.worksheets[0].iter_rows(values_only=True):
        if len(r) < 2 or not r[0] or not r[1]:
            continue
        vi, ko = str(r[0]).strip(), str(r[1]).strip()
        if not SW.KO.search(ko):
            continue
        out.append((vi, ko))
    wb.close()
    return out


def app_words():
    d = json.loads((R / "data" / "days.json").read_text(encoding="utf-8"))
    return [(w["vi"], w["ko"]) for day in d["days"] for w in day.get("words", [])]


def backfill(pool):
    """19기 11~37회차는 **뜻풀이를 영어로만 썼다**(`to eat`, `to drink`).

    한국어→베트남어 앱에 그대로는 못 쓴다. 같은 베트남어 낱말의 한국어 뜻을
    20기 시험·우리 앱에서 찾아 메운다. 메운 것은 `filled` 로 표시해 둔다 —
    선배가 적은 것이 아니라 우리가 붙인 것이라 구분이 필요하다.
    """
    src = {}
    for w in pool:
        if w["src"] != "19기" and SW.KO.search(w["ko"]):
            src.setdefault(viof(w["vi"]), w["ko"])
    for vi, ko in app_words():
        src.setdefault(viof(vi), ko)
    n = 0
    for w in pool:
        if SW.KO.search(w["ko"]) or not w["vi"].strip():
            continue
        got = src.get(viof(w["vi"]))
        if got:
            w["ko_en"], w["ko"], w["filled"] = w["ko"], got, True
            n += 1
    return n


def pct(a, b):
    return f"{len(a) / max(1, b) * 100:.0f}%"


SENT = re.compile(r"[.?!]\s*$|[.?!]\s")


def issent(ko, vi):
    """낱말인가 문장인가.

    갈라야 하는 까닭: 19기 시험은 낱말 20개 + **문장 10개**로 짜여 있고
    20기는 거의 낱말뿐이다. 섞어 세면 19기 쪽만 문장으로 부풀어
    '안 겹친다'는 잘못된 결론이 나온다 — 문장이 낱말과 겹칠 리 없다.
    """
    return bool(SENT.search(ko) or SENT.search(vi) or len(viof(vi).split()) >= 5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    G = {g: load(g) for g in ("19", "20")}
    # 시험 종류별로 낱말 자루를 만든다
    bag = {}
    for g, sets in G.items():
        for kind in ("일일", "주간"):
            ws = [w for (k, _), v in sets.items() if k == kind for w in v]
            bag[(g, kind)] = ws
        bag[(g, "전체")] = [w for (k, _), v in sets.items() if k != "기타" for w in v]

    L = ["# 19기 vs 20기 선배 단어시험 — 같은 시험인가", ""]
    L.append("두 기수 자료를 같은 잣대로 재서 견줬다. `docs/senior-words.md`(20기)와")
    L.append("`docs/senior-words-19.md`(19기)가 각 기수의 전수 정리다.")
    L.append("")

    L.append("## 규모")
    L.append("")
    L.append("| 기수 | 일일 회차 | 번호 범위 | 주간 | 서로 다른 낱말(뜻) | 서로 다른 낱말(베트남어) |")
    L.append("|---|---:|---|---:|---:|---:|")
    for g in ("19", "20"):
        rd = sorted(n for (k, n) in G[g] if k == "일일")
        wk = sorted(n for (k, n) in G[g] if k == "주간")
        ko = {w[0] for w in bag[(g, "전체")] if w[0]}
        vi = {w[1] for w in bag[(g, "전체")] if w[1]}
        L.append(f"| {g}기 | {len(rd)} | {min(rd)}~{max(rd)} | {len(wk)} | {len(ko):,} | {len(vi):,} |")
    L.append("")

    # ── 겹침 ────────────────────────────────────────────────────────────
    K = {g: {w[0] for w in bag[(g, "전체")] if w[0]} for g in ("19", "20")}
    V = {g: {w[1] for w in bag[(g, "전체")] if w[1] and not issent(w[2], w[3])}
         for g in ("19", "20")}
    SEN = {g: {w[1] for w in bag[(g, "전체")] if w[1] and issent(w[2], w[3])}
           for g in ("19", "20")}
    both_k, both_v = K["19"] & K["20"], V["19"] & V["20"]
    BOOK = {w[1] for (k, _), v in G["20"].items() if k == "기타" for w in v
            if w[1] and not issent(w[2], w[3])}

    L.append("### 먼저 — 낱말과 문장을 갈랐다")
    L.append("")
    L.append("19기 시험은 **낱말 20개 + 문장 10개**로 짜여 있다. 20기는 거의 낱말뿐이다.")
    L.append("섞어 세면 19기만 문장으로 부풀어 겹침이 낮게 나온다.")
    L.append("")
    L.append("| 기수 | 낱말 | 문장 |")
    L.append("|---|---:|---:|")
    for g in ("19", "20"):
        L.append(f"| {g}기 | {len(V[g]):,} | {len(SEN[g]):,} |")
    L.append("")
    L.append(f"문장끼리는 **{len(SEN['19'] & SEN['20'])}개** 겹친다. 아래 겹침은 모두 **낱말만** 센 것이다.")
    L.append("")

    L.append("## 답: **낱말 못은 절반쯤 같고, 시험 자체는 다르다**")
    L.append("")
    L.append("| 잣대 | 19기만 | 둘 다 | 20기만 | 19기 중 겹친 비율 | 20기 중 겹친 비율 |")
    L.append("|---|---:|---:|---:|---:|---:|")
    L.append(f"| **말(베트남어)** ← 믿을 것 | {len(V['19'] - V['20']):,} | {len(both_v):,} "
             f"| {len(V['20'] - V['19']):,} | **{pct(both_v, len(V['19']))}** | **{pct(both_v, len(V['20']))}** |")
    L.append(f"| 뜻(한국어) ← 못 믿을 것 | {len(K['19'] - K['20']):,} | {len(both_k):,} "
             f"| {len(K['20'] - K['19']):,} | {pct(both_k, len(K['19']))} | {pct(both_k, len(K['20']))} |")
    L.append("")
    L.append("**두 줄이 세 배 차이 난다. 베트남어 쪽이 맞다.** 한국어로 재면 낮게 나오는 까닭은")
    L.append("겹침이 적어서가 아니라 **19기가 뜻을 딴 식으로 적었기 때문**이다 — 실제로 겹친")
    L.append("낱말의 뜻풀이를 뽑아 보면 이렇다:")
    L.append("")
    L.append("| 베트남어 | 19기가 쓴 뜻 | 20기가 쓴 뜻 |")
    L.append("|---|---|---|")
    KA = {w[1]: w[2] for w in bag[("19", "전체")] if w[1]}
    KB = {w[1]: w[2] for w in bag[("20", "전체")] if w[1]}
    for v in ("cuối tuần", "mặc cả", "dễ", "nhóm", "thị xã"):
        if v in KA and v in KB:
            L.append(f"| {v} | {KA[v][:34]} | {KB[v][:34]} |")
    L.append("")
    L.append("같은 낱말인데 19기는 영어로만 적거나 베트남어를 그대로 옮겨 놨다. 그래서")
    L.append("**한국어 잣대는 19기 기록 습관을 잰 것이지 낱말 겹침을 잰 것이 아니다.**")
    L.append("")

    # 회차 번호가 같으면 낱말도 같은가 — 같다면 '해마다 같은 시험'이다
    L.append("### 회차 번호가 같으면 낱말도 같은가")
    L.append("")
    L.append("같다면 **해마다 똑같은 시험**이라는 뜻이고, 그러면 22기 시험을 미리 아는 셈이다.")
    L.append("")
    rows = []                                   # 여기서도 잣대는 **베트남어**다
    for n in sorted({n for (k, n) in G["19"] if k == "일일"} & {n for (k, n) in G["20"] if k == "일일"}):
        x = {w[1] for w in G["19"][("일일", n)] if w[1]}
        y = {w[1] for w in G["20"][("일일", n)] if w[1]}
        if x and y:
            rows.append((n, len(x), len(y), len(x & y) / max(1, min(len(x), len(y)))))
    avg = sum(r[3] for r in rows) / max(1, len(rows))
    top = sorted(rows, key=lambda r: -r[3])[:5]
    L.append(f"같은 번호끼리 짝지을 수 있는 회차 {len(rows)}개를 견줬다. "
             f"**평균 겹침 {avg * 100:.0f}%**, 절반 넘게 같은 회차는 "
             f"{sum(1 for r in rows if r[3] >= .5)}개다.")
    L.append("")
    L.append("가장 많이 겹친 다섯 회차조차 이 정도다:")
    L.append("")
    L.append("| 회차 | 19기 낱말 | 20기 낱말 | 겹침 |")
    L.append("|---:|---:|---:|---:|")
    for n, a1, b1, ov in top:
        L.append(f"| {n} | {a1} | {b1} | {ov * 100:.0f}% |")
    L.append("")
    L.append("**회차 번호는 해마다 새로 짜인다.** 19기 30회차와 20기 30회차는 딴 시험이다.")
    L.append("")

    # ── 번호 말고 **내용**으로 짝을 찾으면 줄기가 보인다 ──────────────────
    RD = {}
    for g in ("19", "20"):
        RD[g] = {n: {w[1] for w in G[g][("일일", n)] if w[1] and not issent(w[2], w[3])}
                 for (k, n) in G[g] if k == "일일"}
        RD[g] = {n: s for n, s in RD[g].items() if len(s) >= 10}
    best = []
    for n, x in sorted(RD["19"].items()):
        s, m = max(((len(x & y) / min(len(x), len(y)), m) for m, y in RD["20"].items()),
                   default=(0, 0))
        best.append((n, m, s))

    L.append("### 그런데 **번호 말고 내용으로** 짝을 찾으면 줄기가 보인다")
    L.append("")
    L.append("19기 회차마다 '20기 어느 회차와 가장 닮았나'를 찾아봤다.")
    L.append("")
    L.append("| 19기 회차 | 가장 닮은 20기 회차 | 겹침 | 번호 차이 |")
    L.append("|---:|---:|---:|---:|")
    for n, m, s in sorted(sorted(best, key=lambda b: -b[2])[:9]):
        L.append(f"| {n} | {m} | {s * 100:.0f}% | {m - n:+d} |")
    L.append("")
    L.append("**번호 차이가 들쭉날쭉이 아니라 뒤로 갈수록 고르게 벌어진다.**")
    L.append("두 기수가 **같은 교재를 같은 차례로** 따라갔다는 뜻이다. 20기는 같은 데를")
    L.append("가는 데 회차를 더 썼다 — 낱말을 더 촘촘히 냈다.")
    L.append("")

    # ── 45% 가 왜 낮지 않은가 ────────────────────────────────────────────
    a, b, ov = len(V["19"]), len(V["20"]), len(both_v)
    n_est = round(a * b / max(1, ov))
    inA, inB, inAB = len(V["19"] & BOOK), len(V["20"] & BOOK), len(V["19"] & V["20"] & BOOK)
    exp = inA * inB / max(1, len(BOOK))
    oa, ob = V["19"] - BOOK, V["20"] - BOOK

    L.append("## 45%가 낮은 게 아니다 — **딱 이만큼 나와야 맞다**")
    L.append("")
    L.append("같은 교재를 쓴 두 기수인데 절반도 안 겹치는 게 이상해 보인다. 재 봤다.")
    L.append("")
    L.append("선생님 두 분이 **같은 낱말 못에서 저마다 골라** 시험을 냈다면, 겹침은")
    L.append("`19기 수 × 20기 수 ÷ 못의 크기` 다. 거꾸로 풀면 못의 크기가 나온다:")
    L.append("")
    L.append(f"    {ov} = {a:,} × {b:,} ÷ N   →   N ≈ **{n_est:,}낱말**")
    L.append("")
    L.append(f"우리가 가진 `4권 베트남어 교재_단어.xlsx` 는 **한 권치 {len(BOOK):,}낱말**이다.")
    L.append(f"기초 베트남어는 1~4권이니 네 권이면 대략 {len(BOOK) * 4:,}낱말 —")
    L.append(f"**추정한 못 {n_est:,}과 거의 같다.**")
    L.append("")
    L.append("> 이건 '네 권이 비슷한 분량'이라는 어림이다. 1~3권 낱말 목록은 우리에게 없다.")
    L.append("")
    L.append("교재 안팎으로 갈라 보면 더 뚜렷하다:")
    L.append("")
    L.append("| 어디 | 19기 | 20기 | 둘 다 | 우연이라면 |")
    L.append("|---|---:|---:|---:|---:|")
    L.append(f"| 교재 낱말 목록 **안** | {inA} | {inB} | **{inAB}** | {exp:.0f} |")
    L.append(f"| 교재 목록 **밖** | {len(oa):,} | {len(ob):,} | {len(oa & ob):,} | — |")
    L.append("")
    L.append(f"**교재 안에서는 우연보다 {inAB / max(1, exp):.1f}배 더 겹친다.** 함께 교재를 따라간 증거다.")
    L.append("교재 밖 낱말은 선생님이 그때그때 더한 것이라 겹칠 까닭이 없다.")
    L.append("")
    L.append("정리 — **낱말 못은 같고, 거기서 고른 것이 다르다.** 22기도 이 못에서 나온다.")
    L.append(f"두 기수를 합친 {len(V['19'] | V['20']):,}낱말이 교재 못({n_est:,})의 "
             f"**{len(V['19'] | V['20']) / n_est * 100:.0f}%** 를 덮는다.")
    L.append("")

    # 19기에만 있는 낱말 맛보기 — 뜻이 아니라 **말**로 골라야 한다
    only19 = sorted(V["19"] - V["20"])
    L.append(f"**19기에만 있는 낱말 {len(only19):,}개** 보기: "
             + " · ".join(f"{v}({KA[v][:16]})" for v in only19[:18] if v in KA))
    L.append("")

    # ── 카톡방 ───────────────────────────────────────────────────────────
    kk = kakao()
    kv = {viof(v) for v, _ in kk}
    one = [(v, k) for v, k in kk if len(viof(v).split()) <= 2]
    many = [(v, k) for v, k in kk if len(viof(v).split()) > 2]
    eng = [(v, k) for v, k in kk if re.search(r"[a-z]{2,}", v) and not SW.VI.search(v)]
    L.append("## 생산관리 카톡방 단어 정리 — **쓸모 있다. 성격이 다르다**")
    L.append("")
    L.append(f"`{KAKAO.name}` · 짝 **{len(kk)}개**. 시험지가 아니다. 한국 공장의")
    L.append("생산관리 카톡방에서 실제로 오간 말을 선배가 그때그때 적어 둔 것이다.")
    L.append("")
    L.append("| 갈래 | 몇 개 | 보기 |")
    L.append("|---|---:|---|")
    L.append(f"| 낱말(두 마디 이하) | {len(one)} | " + " · ".join(f"{v} {k}" for v, k in one[:3]) + " |")
    L.append(f"| 구절·문장 | {len(many)} | " + " · ".join(f"{v} {k}" for v, k in many[:3]) + " |")
    L.append(f"| 영어가 섞인 것 | {len(eng)} | " + " · ".join(f"{v} {k}" for v, k in eng[:3]) + " |")
    L.append("")
    L.append("겹침 — 시험 낱말과 얼마나 같은가:")
    L.append("")
    L.append("| 견준 대상 | 겹친 낱말 | 카톡 낱말 중 비율 |")
    L.append("|---|---:|---:|")
    for nm, s in (("19기 시험", V["19"]), ("20기 시험", V["20"]), ("두 기수 합", V["19"] | V["20"])):
        L.append(f"| {nm} | {len(kv & s)} | {pct(kv & s, len(kv))} |")
    aw = app_words()
    av = {viof(v) for v, _ in aw}
    L.append(f"| 우리 앱(베트남어 과정 {len(aw):,}낱말) | {len(kv & av)} | {pct(kv & av, len(kv))} |")
    L.append("")

    # ── 앱과의 겹침 ──────────────────────────────────────────────────────
    L.append("## 우리 앱 낱말과 겹치는가")
    L.append("")
    L.append("| 자료 | 서로 다른 베트남어 | 앱에 이미 있는 것 | 새로 얻는 것 |")
    L.append("|---|---:|---:|---:|")
    for nm, s in (("19기 시험", V["19"]), ("20기 시험", V["20"]),
                  ("두 기수 합", V["19"] | V["20"]), ("생산관리 카톡방", kv)):
        L.append(f"| {nm} | {len(s):,} | {len(s & av):,} | **{len(s - av):,}** |")
    allnew = (V["19"] | V["20"] | kv) - av
    L.append(f"| **셋 다 합쳐** | {len(V['19'] | V['20'] | kv):,} | "
             f"{len((V['19'] | V['20'] | kv) & av):,} | **{len(allnew):,}** |")
    L.append("")

    # ── 19기 × 20기 × 앱, 세 뭉치 ────────────────────────────────────────
    only, pair, tri = venn3(V["19"], V["20"], av, ("19기", "20기", "앱"))
    L.append("### 세 뭉치를 한꺼번에")
    L.append("")
    L.append("**먼저 진짜 교집합.** (아래 '조각' 표와 헷갈리면 안 된다 —")
    L.append("처음에 조각을 교집합인 양 늘어놨다가 '둘 겹침이 셋 겹침보다 작다'는")
    L.append("있을 수 없는 그림이 나왔다. 숫자는 맞았고 이름이 틀렸다.)")
    L.append("")
    L.append("| 교집합 | 크기 | 그중 셋 다 | 그 쌍에만 |")
    L.append("|---|---:|---:|---:|")
    for nm, v in pair.items():
        L.append(f"| {nm} | **{len(v):,}** | {len(tri):,} | {len(v - tri):,} |")
    L.append("")
    L.append(f"세 교집합 모두 삼중교집합 {len(tri):,} 보다 크다 — 도구가 이걸 어기면 그 자리에서 멈춘다.")
    L.append("")
    L.append("**칸으로 가르면** (일곱 칸은 서로 안 겹치고, 다 더하면 합집합이다)")
    L.append("")
    L.append("| 어디에만 있나 | 낱말 |")
    L.append("|---|---:|")
    for nm, v in only.items():
        L.append(f"| {nm} | {len(v):,} |")
    L.append(f"| **합** | **{sum(len(v) for v in only.values()):,}** |")
    L.append("")
    L.append("가운데(셋 다)가 두꺼운 것은 이상한 일이 아니다. 앱에도 있는 낱말은")
    L.append("**흔한 기본 낱말**이라 두 기수 모두가 낸다:")
    L.append("")
    L.append(f"- 19기 낱말 전체 중 20기에도 있는 비율 — {len(V['19'] & V['20']) / len(V['19']) * 100:.0f}%")
    L.append(f"- 그런데 `19기 ∩ 앱` 중 20기에도 있는 비율 — **{len(tri) / len(pair['19기∩앱']) * 100:.0f}%**")
    L.append("")
    L.append("가운데 낱말 보기: " + " · ".join(sorted(tri)[:16]))
    L.append("")

    # ── 낱말 못 ─────────────────────────────────────────────────────────
    seen, pool = set(), []
    for src, ws in (("20기", bag[("20", "전체")]), ("19기", bag[("19", "전체")])):
        for _, v, ko, vi in ws:
            if not v or v in seen:
                continue
            seen.add(v)
            pool.append({"vi": vi, "ko": ko, "src": src, "new": v not in av})
    for vi, ko in kk:
        v = viof(vi)
        if v and v not in seen:
            seen.add(v)
            pool.append({"vi": vi, "ko": ko, "src": "생산관리 카톡방", "new": v not in av})
    nofill = [w for w in pool if not SW.KO.search(w["ko"]) and w["vi"].strip()]
    filled = backfill(pool)
    still = [w for w in pool if not SW.KO.search(w["ko"]) and w["vi"].strip()]

    L.append("## 19기 뜻풀이가 영어로만 된 것 — 메웠다")
    L.append("")
    L.append("19기 11~37회차는 뜻을 **영어로만** 적었다(`to eat` · `to drink`). 한국어→베트남어")
    L.append("앱에 그대로는 못 쓴다. 세 단계로 걸렀다:")
    L.append("")
    L.append("1. 낱말 못을 만들 때 **20기를 먼저 넣었다** — 같은 낱말이면 뜻풀이가 온전한")
    L.append("   20기 것이 남는다. 영어로만 된 19기 낱말 대부분이 여기서 해결된다.")
    L.append(f"2. 그러고도 남은 **{len(nofill):,}개** 중 **{filled:,}개**를 우리 앱 낱말에서 찾아 메웠다.")
    L.append(f"3. 아직 **{len(still):,}개**가 영어로만 남아 있다.")
    L.append("")
    L.append("남은 것은 `_senior_pool.json` 에서 `ko` 가 영어인 줄이다. 메운 것은 `filled: true` 로")
    L.append("표시해 뒀다 — 선배가 적은 것이 아니라 우리가 붙인 것이라 구분해야 한다.")
    L.append("")
    L.append("남은 보기: " + " · ".join(f"{w['vi']}({w['ko']})" for w in still[:12]))
    L.append("")

    L.append("## 이 폴더의 나머지 — 앱에 넣으면 안 되는 것")
    L.append("")
    L.append("19기 폴더에는 낱말 말고도 음성·교재가 들어 있다. **모두 시판 교재 부속물이다.**")
    L.append("")
    L.append("| 자료 | 무엇 | 앱에 실을 수 있나 |")
    L.append("|---|---|---|")
    L.append("| `BAI 1~8.mp3` + `발음` | 수업 음원 14개 | ✗ 출처 불명 |")
    L.append("| `NVH＿TVNC＿Q1/Q2` zip | `Tiếng Việt nâng cao` 교재 음원 | ✗ 시판 교재 부속 CD |")
    L.append("| `Tieng Viet co so 2` zip | `기초 베트남어 2` 음원(2014) | ✗ 시판 교재 부속 CD |")
    L.append("| `Tiếng Việt CS － Q2/Q3/Q4.pdf` | 기초 베트남어 2·3·4권 **스캔본** | ✗ 시판 교재 스캔 |")
    L.append("")
    L.append("우리가 공부하는 데 쓰는 것과, **유료 앱에 실어 파는 것은 다르다.**")
    L.append("낱말 목록(사실)은 저작물이 아니지만 음원·지문·스캔은 저작물이다.")
    L.append("`100일의 기적`도 같다 — 시판 책이라 문장을 그대로 실으면 안 된다.")
    L.append("")

    out = "\n".join(L) + "\n"
    (R / "docs" / "senior-compare.md").write_text(out, encoding="utf-8")
    print(out)
    print("→ docs/senior-compare.md")

    if a.json:
        p = R / "data" / "_senior_pool.json"
        p.write_text(json.dumps(
            {"note": "19·20기 시험 + 생산관리 카톡방을 합친 낱말 못. 앱에 아직 안 넣음. "
                     "filled=true 는 영어 뜻풀이를 우리가 한국어로 메운 것.",
             "words": pool}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"→ {p}  ({len(pool):,}낱말 · 새것 {sum(1 for w in pool if w['new']):,})")


if __name__ == "__main__":
    main()
