#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""새 낱말에 **한글 발음**을 단다 → data/_new_words.json 의 kr·krs

AI 를 쓰지 않는다. tools/vi_kr.py 가 국립국어원 표기법으로 만든다 —
같은 글자면 늘 같은 결과라 검산이 된다.

쓰기: python3 tools/new_kr.py
"""
import json, pathlib, sys

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr

OUT = R / "data" / "_new_words.json"


def main():
    data = json.loads(OUT.read_text(encoding="utf-8"))
    n = 0
    for ws in data.values():
        for w in ws:
            kr, krs = vi_kr.word(w["vi"]), vi_kr.word(w["vi"], south=True)
            if not kr:                      # 도구가 못 읽는 것은 표시만 하고 넘어간다
                w["kr_warn"] = 1
                continue
            if w.get("kr") != kr or w.get("krs") != krs:
                w["kr"], w["krs"] = kr, krs
                n += 1
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    warn = [w["vi"] for ws in data.values() for w in ws if w.get("kr_warn")]
    print(f"발음 단 낱말 {n}")
    if warn:
        print(f"도구가 못 읽은 것 {len(warn)}개: {warn[:15]}")


main()
