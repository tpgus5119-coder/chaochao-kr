#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""한국어 과정 1단계 — 국립국어원 학습용 어휘 5,965개를 우리 그릇에 붓는다.

재료: tools/nikl_5965.tsv (국립국어원 「한국어 학습용 어휘 목록」 2003,
      공공누리 제1유형 — 출처 표시 조건으로 상업 이용·변형 허용.
      출처: 국립국어원 https://www.korean.go.kr)
산출: data/_ko_words.json  (앱이 직접 읽지 않는다 — 나중에 ko_days 조립의 재료)

하는 일:
  ① 동형어 꼬리표 떼기 — '가격03' → '가격' (03은 사전 구분 번호, 학습자에겐 소음)
  ② 풀이 칸에서 한자만 추리기 — '價格' 같은 것. 55%가 갖고 있다.
  ③ 한자→한월(Hán-Việt) 다리 — 기존 HANVIET 표(베→한자)를 뒤집어
     같은 한자를 쓰는 베트남어 낱말을 자동으로 이어 붙인다.
  ④ 등급(A/B/C) 나눠 빈도 순위로 정렬 — A(982)가 초급 과정의 첫 창고.

실행: python3 tools/k1.py
"""
import json, pathlib, re, sys, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from hanviet import HANVIET

# 함정: 한국 코드표는 두음법칙 구분(旅 려/여)에 '호환 한자'(U+F900대)를 쓴다.
# NFKC 정규화로 본래 글자로 되돌린 뒤 뽑는다 — 안 하면 旅行에서 旅가 증발한다.
CJK = re.compile(r'[一-鿿豈-﫿]+')
TAIL = re.compile(r'\d+$')          # 동형어 번호 (가격03)

def hanja_of(pul):
    s = unicodedata.normalize('NFKC', pul)
    return "".join(CJK.findall(s)) or None

def load():
    rows = []
    for ln in (ROOT / "tools" / "nikl_5965.tsv").read_text().splitlines()[1:]:
        rank, word, pos, pul, grade = ln.split("\t")
        rows.append({"rank": int(rank), "raw": word, "pos": pos, "pul": pul, "grade": grade})
    return rows

def build():
    # k2가 만든 베트남어 뜻(원어 표기 열쇠) — 있으면 붙인다
    gpath = ROOT / "data" / "_ko_vi_gloss.json"
    gloss = json.loads(gpath.read_text()) if gpath.exists() else {}
    # 한월 다리(검증본) — Unihan 읽기가 krdict 뜻의 토큰과 연속 일치할 때만 인정한 735쌍
    bpath = ROOT / "tools" / "hanviet_bridge_ko.json"
    bridge = json.loads(bpath.read_text()) if bpath.exists() else {}
    # HANVIET 뒤집기: 한자 → 베트남어 낱말 (괄호 속 음독은 떼어낸다)
    h2v = {}
    for vi, tag in HANVIET.items():
        for h in CJK.findall(tag):
            h2v.setdefault(h, vi)

    rows = load()
    out, seen = [], set()
    for r in rows:
        word = TAIL.sub("", r["raw"])
        # 같은 표기가 등급 다르게 두 번 오면 낮은 등급(먼저 배울 것)만 남긴다
        key = (word, r["pos"])
        if key in seen:
            continue
        seen.add(key)
        hanja = hanja_of(r["pul"])
        item = {"ko": word, "pos": r["pos"], "grade": r["grade"],
                "rank": r["rank"] or 99999}
        g = gloss.get(r["raw"])
        if g and "vi" in g:
            item["vi"] = g["vi"]
        if word in bridge:
            item["vih"] = bridge[word]          # 같은 한자를 쓰는 베트남어 (한월 짝)
        if hanja:
            item["hanja"] = hanja
            vi = h2v.get(hanja)
            if vi:
                item["vi_bridge"] = vi          # 같은 한자를 쓰는 베트남어
        out.append(item)

    out.sort(key=lambda x: (x["grade"], x["rank"]))
    dst = ROOT / "data" / "_ko_words.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))

    # 보고
    from collections import Counter
    g = Counter(x["grade"] for x in out)
    hj = sum(1 for x in out if "hanja" in x)
    br = sum(1 for x in out if "vi_bridge" in x)
    a_hj = sum(1 for x in out if x["grade"] == "A" and "hanja" in x)
    print(f"낱말 {len(out)} (중복 제거 {len(rows)-len(out)})  등급 {dict(g)}")
    print(f"한자 보유 {hj} ({hj*100//len(out)}%)  ·  A등급 한자 {a_hj}/{g['A']}")
    print(f"한월 다리 자동 연결 {br}개 (HANVIET 표 {len(HANVIET)}개 기준 — 표가 클수록 늘어난다)")
    print(f"→ {dst.relative_to(ROOT)}")

if __name__ == "__main__":
    build()
