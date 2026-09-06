#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**손으로 쓴** 체계 꼭지를 새 낱말에 덮어쓴다 → data/_new_words.json

왜 손으로 쓰나 (2026-09-01 실측):
  숫자·시간·요일처럼 **정해진 체계**는 AI 에게 물으면 조합을 무한정 지어낸다.
  실제로 나온 것들: hai trăm giờ(이백 시), năm nghìn giờ(오천 시간),
  triệu=천만(백만이 맞다). 정작 '한 시·두 시'와 '누구·무엇·어디'는 빠져 있었다.
  닫힌 목록이라 사람이 쓰는 편이 빠르고 정확하다.

바탕 자료: data/_core_words.json  (꼭지 → [[베트남어, 뜻], ...])
발음은 tools/new_kr.py 가 나중에 단다.

쓰기: python3 tools/new_core.py
"""
import json, pathlib, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
OUT, CORE = R / "data" / "_new_words.json", R / "data" / "_core_words.json"
n = lambda s: U.normalize("NFC", str(s)).strip()


def main():
    d = json.loads(OUT.read_text(encoding="utf-8"))
    core = json.loads(CORE.read_text(encoding="utf-8"))
    # 손으로 쓴 꼭지가 **이긴다** — 같은 말이 다른 꼭지에 흩어져 있으면 거기서 뺀다.
    # (묻는 말의 '누구·무엇'이 엉뚱한 꼭지에 가 있어서 정작 제자리가 비었었다)
    mine = {n(vi).lower() for pairs in core.values() for vi, _ in pairs}
    moved = 0
    for t, ws in d.items():
        if t in core:
            continue
        keep = [w for w in ws if n(w["vi"]).lower() not in mine]
        moved += len(ws) - len(keep); d[t] = keep
    print(f"제자리로 옮기려고 다른 꼭지에서 뺀 말 {moved}\n")

    for topic, pairs in core.items():
        was = len(d.get(topic, []))
        ws, seen = [], set()
        for vi, ko in pairs:
            k = n(vi).lower()
            if k in seen:
                continue
            seen.add(k)
            ws.append({"vi": n(vi), "ko": n(ko), "src": "손으로 씀", "v": "ok", "real": 1})
        d[topic] = ws
        print(f"  {topic:14} {was:3} → {len(ws):3}")
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n모두 {sum(len(v) for v in d.values())} 낱말")


main()
