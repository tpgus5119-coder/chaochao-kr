#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**선배 시험에 나온 낱말에 별표**를 찍는다 → days.json / ko_days.json 에 "sr":1

규칙 (대표님, 2026-08-30)
  · 한 기수에만 나왔어도 별표를 준다. 기수 수는 따지지 않는다.
  · 기수 시험에 안 나온 낱말(우리가 만들어 넣은 것)은 별표가 없다.
견주는 방법: 성조는 살리고(bạn·bán 은 다른 낱말) 대소문자·겹빈칸·괄호·끝부호만 맞춘다.
쓰기: python3 tools/star_mark.py     (build_all.sh 안에서 돈다)
"""
import json, pathlib, re, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent

def key(v):
    s = U.normalize("NFC", str(v)).strip().lower()
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,;:!?~–—/\"'")

def main():
    pool = R / "data" / "senior_pool.json"
    if not pool.exists(): raise SystemExit("senior_pool.json 먼저 (tools/senior_merge.py)")
    sen = {key(w["vi"]) for w in json.loads(pool.read_text(encoding="utf-8"))["words"]}
    print(f"선배 낱말 {len(sen)}개")
    # **베트남어 과정에만** 찍는다. ko_days.json 은 베트남 사람이 한국어를 배우는 쪽이라
    # 거기서 vi 는 '뜻' 자리다 — 선배 시험(베트남어 시험)과는 상관이 없다.
    for f in ("days.json",):
        p = R / "data" / f
        if not p.exists(): continue
        d = json.loads(p.read_text(encoding="utf-8"))
        days = d if isinstance(d, list) else d.get("days", [])
        on = off = 0
        for day in days:
            for w in (day.get("words") or []):
                vi = w.get("vi") or w.get("word") or ""
                if key(vi) in sen: w["sr"] = 1; on += 1
                else: w.pop("sr", None); off += 1
        p.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"  {f}: 별표 {on}개 · 별표 없음 {off}개")

main()
