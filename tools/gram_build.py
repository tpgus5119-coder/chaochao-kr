#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""문법 175개를 하나로 묶는다 → data/grammar.json  (1권 = 기본기 + 문법)

바탕: NGUYỄN VIỆT HƯƠNG 『Tiếng Việt Cơ sở Q2』 · 『Nâng cao Q1』 · 『Nâng cao Q2』
      — 선배 네 기수가 실제로 쓴 교재의 **과별 문법 항목 그대로**다. 내가 고른 것이 아니다.
한글 소리는 tools/vi_kr.py 가 붙인다(북부·남부 두 벌).
쓰기: python3 tools/gram_build.py
"""
import json, pathlib, sys

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
sys.path.insert(0, str(R / "tools" / "gram"))
import vi_kr
import g1_coso, g2_nc1, g3_nc2

def main():
    # AI 가 채운 자세한 설명 — 낱말 뜻(kw)·긴 설명(b)·예문 더(ex)·자주 하는 실수(tip)
    #   대표님 지적(2026-08-30): "모르는 단어를 나열만 하고, 예문은 2개냐"
    rich = {}
    _rp = R / "data" / "_gramrich.json"
    if _rp.exists(): rich = json.loads(_rp.read_text(encoding="utf-8"))

    books, n, ne, nr = [], 0, 0, 0
    for bi, m in enumerate((g1_coso, g2_nc1, g3_nc2)):
        bais = []
        for ni, b in enumerate(m.BAI):
            gs = []
            for gi, g in enumerate(b["g"]):
                r = rich.get(f"{bi}-{ni}-{gi}") or {}
                pairs = [tuple(x) for x in r.get("ex", [])] or g["ex"]
                if r: nr += 1
                ex = [{"vi": v, "ko": k,
                       "kr": vi_kr.word(v), "krs": vi_kr.word(v, True)} for v, k in pairs]
                gs.append({"t": g["t"], "k": g["k"], "b": r.get("b") or g["b"], "ex": ex,
                           **({"kw": r["kw"]} if r.get("kw") else {}),
                           **({"tip": r["tip"]} if r.get("tip") else {})})
                n += 1; ne += len(ex)
            bais.append({"no": b["no"], "t": b["t"], "g": gs})
        books.append({"book": m.BOOK, "bai": bais})
    (R / "data" / "grammar.json").write_text(json.dumps(
        {"note": "교재(NGUYỄN VIỆT HƯƠNG) 세 권의 과별 문법 그대로. 1권 = 기본기 + 문법.",
         "books": books}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"책 {len(books)} · 과 {sum(len(x['bai']) for x in books)} · 문법 {n} · 예문 {ne}"
          f" · 자세히 채운 것 {nr}/{n}")
    print("강 수(문법 5개를 한 강으로):", -(-n // 5))
main()
