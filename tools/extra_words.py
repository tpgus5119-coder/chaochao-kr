#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""시험지가 **아닌** 모음집에서 낱말을 따로 건진다 → data/_extra_words.json

파일 779개를 하나씩 열어 보고 가려낸 것들이다 (2026-08-30, 대표님 지시).
이것들은 **회차가 없어 차례를 매길 수 없다.** 그래서 시험 낱말 뒤에 붙인다.
  · 4권 베트남어 교재_단어.xlsx  — 교재(Nâng cao Q2)의 낱말표 1,148개. 가나다 차례.
  · 토요시험단어 자체제작.xlsx   — 선배가 직접 만든 토요 시험 낱말
  · 토요단어시험 함수양식.xlsx   — 시험 만드는 양식(낱말은 들어 있다)
카톡방 파일은 tools/kakao_job.py 가 따로 다룬다(직무라서).
쓰기: python3 tools/extra_words.py
"""
import json, os, pathlib, re, sys, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr, senior_scan as SC, senior18 as S

FILES = ["4권 베트남어 교재_단어.xlsx", "토요시험단어 자체제작.xlsx", "토요단어시험 함수양식.xlsx"]
KO = re.compile(r"[가-힣]")

def key(v):
    s = U.normalize("NFC", str(v)).strip().lower()
    s = re.sub(r"\([^)]*\)", "", s)
    return re.sub(r"\s+", " ", s).strip(" .,;:!?~–—/\"'")

def main():
    pool = {key(w["vi"]) for w in
            json.loads((R / "data" / "senior_pool.json").read_text(encoding="utf-8"))["words"]}
    out, seen, src = [], set(), {}
    for d in sorted(S.BASE.iterdir()):
        if not d.is_dir(): continue
        for fn in os.listdir(d):
            if fn not in FILES: continue
            try: rows = SC.cells_of(d / fn)
            except Exception as e: print("  못 읽음", fn, e); continue
            n = 0
            for vi, ko, en in SC.split(rows):
                vi = U.normalize("NFC", vi).strip()
                ko = re.sub(r"\s+", " ", (ko or "")).strip()
                if not (vi and ko and KO.search(ko)): continue
                if len(vi.split()) > 5 or len(vi) > 34: continue
                k = key(vi)
                if not k or k in seen or k in pool: continue     # 시험에 이미 나온 말은 거기 두면 된다
                seen.add(k)
                out.append({"vi": vi, "ko": ko, "kr": vi_kr.word(vi), "krs": vi_kr.word(vi, True),
                            "book": 1})
                n += 1
            src[fn] = n
    (R / "data" / "_extra_words.json").write_text(json.dumps(
        {"note": "시험지가 아닌 모음집에서 건진 낱말. 회차가 없어 시험 낱말 뒤에 붙인다.",
         "words": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"모음집에서 새로 건진 낱말 {len(out)}개")
    for k, v in src.items(): print(f"   {v:>5}  {k}")
main()
