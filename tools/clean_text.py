#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낱말·뜻·예문에 섞인 **엉뚱한 글자**를 씻는다 → senior_pool.json · _examples.json

왜 (2026-08-30 검수): 글자 하나하나를 훑어보니 여섯 곳이 깨져 있었다.
  · 'ngoان' — 아랍 글자가 섞였다 (ngoan 착한)
  · '민㈜적인' — 괄호 주식회사 기호 (민주적인)
  · '／후에' '～후에' — 전각 기호
  · 떠 있는 성조 부호 (U+0300~0323 이 앞 글자에 안 붙은 것)
잣대: 라틴 기본·확장A/B·베트남어 확장·한글·숫자·기본 문장부호만 남긴다.
쓰기: python3 tools/clean_text.py
"""
import json, pathlib, re, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
# 손으로 바로잡는 표 — 기계가 못 고치는 것
HAND = {"ngoان": "ngoan", "민㈜적인": "민주적인", "대(大)": "대(크다)", "lúy": "lũy"}
FULL = {"／": "/", "～": "~", "－": "-", "（": "(", "）": ")", "，": ",", "．": ".",
        "：": ":", "；": ";", "！": "!", "？": "?", "％": "%", "　": " "}

def ok(c):
    o = ord(c)
    return (o < 0x250 or 0x1E00 <= o <= 0x1EFF          # 라틴 + 베트남어
            or 0xAC00 <= o <= 0xD7A3                     # 한글
            or o in (0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026, 0x00B7))

def wash(s):
    if not s: return s
    for a, b in HAND.items(): s = s.replace(a, b)
    s = "".join(FULL.get(c, c) for c in s)
    s = U.normalize("NFC", s)
    # 앞 글자에 안 붙은 성조 부호를 버린다
    s = "".join(c for c in s if not U.combining(c) or True)
    s = re.sub(r"(?<![A-Za-zÀ-ỹ])[̀-̣]+", "", U.normalize("NFD", s))
    s = U.normalize("NFC", s)
    s = "".join(c for c in s if ok(c))
    return re.sub(r"\s+", " ", s).strip()


def wash_vi(s):
    """낱말 칸 전용 — 꼬리의 '~' 를 뗀다.
       'hóa ra~' 는 '뒤에 말이 이어진다'는 표시였지만 낱말로는 지저분하고,
       예문에 그 낱말이 들었는지 재는 데도 걸림돌이 된다 (2026-08-30 검수)."""
    return re.sub(r"[\s~\-–—]+$", "", wash(s)).strip()

def main():
    n = 0
    p = R / "data" / "senior_pool.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    for w in d["words"]:
        for k in ("vi", "ko"):
            v = (wash_vi if k == "vi" else wash)(w.get(k, ""))
            if v != w.get(k, ""): w[k] = v; n += 1
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    q = R / "data" / "_examples.json"
    if q.exists():
        e = json.loads(q.read_text(encoding="utf-8"))
        for k, v in e.items():
            for f in ("vi", "ko", "kr", "krs"):
                if isinstance(v, dict) and v.get(f):
                    x = wash(v[f])
                    if x != v[f]: v[f] = x; n += 1
        q.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  씻은 자리 {n}곳")

main()
