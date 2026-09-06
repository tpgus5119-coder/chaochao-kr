#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""선배 시험지에 섞여 있던 **예문**을 건진다 → data/_senior_sents.json

낱말을 뽑을 때는 문장을 버렸다(5,600개). 그런데 그건 버릴 것이 아니라
**예문으로 쓸 진짜 자료**다 — 선배들이 실제로 배운 문장이고 뜻도 함께 적혀 있다.
칸이 어긋나 토막 난 것만 걸러 낸다.
쓰기: python3 tools/senior_sents.py
"""
import json, pathlib, re, sys, unicodedata as U, collections

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
KO = re.compile(r"[가-힣]")
VI = re.compile(r"[ăâđêôơưÀ-ỹ]", re.I)

def ok(vi, ko):
    """문장인가, 토막인가."""
    if not vi or not ko: return False
    w = vi.split()
    if not (3 <= len(w) <= 14): return False
    if not KO.search(ko) or len(ko) < 4: return False
    if re.search(r"[A-Za-z]{3,}", ko): return False        # 뜻에 영어가 섞인 것
    if not VI.search(vi): return False                     # 베트남어가 아님
    if vi[0].islower() and not re.search(r"[.?!]$", vi.strip()):
        # 대문자로 시작하지도, 문장부호로 끝나지도 않으면 토막일 확률이 높다
        if len(w) < 5: return False
    if re.search(r"^\s*[\d.]+\s*$", vi): return False
    # 한 줄에 낱말 둘이 나란히 적힌 것 — 뜻이 '막내 / 다큐멘터리' 처럼 갈라져 있다
    if "/" in ko and all(len(x.strip()) <= 12 for x in ko.split("/")): return False
    # 진짜 문장은 **대문자로 시작하거나 문장부호로 끝난다**. 둘 다 아니면 버린다.
    if not (vi[0].isupper() or re.search(r"[.?!]\s*$", vi)): return False
    return True

def main():
    out, seen = [], set()
    for gi in ("17", "18", "19", "20"):
        p = R / "data" / f"_senior_scan-{gi}.json"
        if not p.exists(): continue
        for f in json.loads(p.read_text(encoding="utf-8"))["files"]:
            for row in f["rows"]:
                vi = U.normalize("NFC", (row.get("vi") or "")).strip()
                ko = U.normalize("NFC", (row.get("ko") or "")).strip()
                if not ok(vi, ko): continue
                k = re.sub(r"\s+", " ", vi.lower())
                if k in seen: continue
                seen.add(k)
                out.append({"vi": vi, "ko": ko, "gi": gi})
    (R / "data" / "_senior_sents.json").write_text(
        json.dumps({"note": "선배 시험지에 섞여 있던 예문. 낱말 예문으로 쓴다.", "sents": out},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"건진 예문 {len(out)}개")
    print("  기수별:", dict(collections.Counter(x["gi"] for x in out)))
    for x in out[:8]: print("   ", x["vi"], "—", x["ko"][:26])
main()
