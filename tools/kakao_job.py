#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「생산관리 카톡방 단어 정리」를 **따로** 읽는다 → data/_kakao_job.json

이 파일은 시험지가 아니다 (대표님 지적, 2026-08-30).
  선배들이 일터 단톡방에서 주고받은 말을 모은 표다. 기수도 회차도 없으니
  **기수 합으로 차례를 매기는 규칙에 섞으면 안 된다.** 그래서 따로 읽어
  직무 낱말 맨 뒤(선배 시험 직무 → 카톡방 → 우리가 만든 것)에 붙인다.

읽으면서 손보는 것
  · `Cdoan (công đoạn)` 처럼 **괄호 안이 진짜 낱말**이면 그것을 쓴다.
  · `ko tồn tại` 의 ko 는 không 의 카톡 줄임말이라 되돌린다.
  · `PGM` `NG` `Unit matching` 같은 영어·약자는 낱말이 아니라 뺀다.
쓰기: python3 tools/kakao_job.py
"""
import json, os, pathlib, re, sys, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr

SRC = pathlib.Path(os.path.expanduser(
    "~/Downloads/베트남어 학습자료/선배 자료/생산관리 카톡방 단어 정리.xlsx"))
VI = re.compile(r"[ăâđêôơưÀ-ỹ]", re.I)
KO = re.compile(r"[가-힣]")

def fix(v):
    v = U.normalize("NFC", str(v)).strip()
    m = re.match(r"^\S+\s*\(([^)]+)\)\s*$", v)          # Cdoan (công đoạn) → công đoạn
    if m and VI.search(m.group(1)): v = m.group(1).strip()
    v = re.sub(r"\bko\b", "không", v)                    # 카톡 줄임말
    v = re.sub(r"\bhtrong\b", "hệ thống", v)
    v = re.sub(r"\bcn\b", "công nhân", v)
    return re.sub(r"\s+", " ", v).strip()

def main():
    if not SRC.exists(): raise SystemExit(f"파일 없음: {SRC}")
    import openpyxl
    wb = openpyxl.load_workbook(SRC, data_only=True)
    out, drop = [], 0
    seen = set()
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            c = [str(x).strip() for x in row if x is not None and str(x).strip()]
            if len(c) < 2: continue
            vi, ko = fix(c[0]), " / ".join(x for x in c[1:] if KO.search(x))
            if not ko or not vi: drop += 1; continue
            if not VI.search(vi) and not re.search(r"^[a-zà-ỹ ]+$", vi, re.I):
                drop += 1; continue                       # PGM · NG · Unit matching
            if len(vi.split()) > 5: drop += 1; continue
            k = vi.lower()
            if k in seen: continue
            seen.add(k)
            out.append({"vi": vi, "ko": ko, "kr": vi_kr.word(vi), "krs": vi_kr.word(vi, True),
                        "kakao": 1})
    (R / "data" / "_kakao_job.json").write_text(
        json.dumps({"note": "생산관리 카톡방 단어 정리 — 시험지가 아니다. 직무 낱말 뒤에 붙인다.",
                    "words": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"카톡방 낱말 {len(out)}개 · 낱말이 아니라 뺀 것 {drop}개")
    for w in out[:10]: print(f"   {w['vi']:<22} {w['ko'][:26]}")
main()
