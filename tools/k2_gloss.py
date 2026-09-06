#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""한국어 과정 2단계 — 어휘 5,965개에 베트남어 뜻을 붙인다.

재료: 한국어기초사전 Open API (krdict.korean.go.kr, 문체부·국립국어원)
      텍스트 저작권 CC BY-SA 2.0 KR — 출처 표시 조건으로 상업 이용 가능.
키:   .krdict_key (저장소 밖 — .gitignore 등록, 하루 5만 건 한도)
산출: data/_ko_vi_gloss.json  { "가격03": {vi, vi_dfn, ko_dfn, tc}, ... }
      원어(꼬리표 붙은) 표기를 열쇠로 남긴다 — 동형어가 안 섞이게.

동형어 가르기: 이름+품사가 같은 후보가 여럿이면 상세(view)로 원어(한자)를 받아
우리 표(nikl_5965.tsv 풀이 칸)의 한자와 맞춘다. 한자가 없으면 첫 후보.
중간 저장: 100개마다 파일로 적는다 — 끊겨도 이어서 돈다.
실행: python3 tools/k2_gloss.py   (진행은 stdout 한 줄씩)
"""
import json, pathlib, re, time, unicodedata, urllib.parse, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
KEY = (ROOT / ".krdict_key").read_text().strip()
OUT = ROOT / "data" / "_ko_vi_gloss.json"
UA = "Mozilla/5.0 chaochao-app (study tool)"
POS = {"명": "명사", "동": "동사", "형": "형용사", "부": "부사", "대": "대명사",
       "수": "수사", "관": "관형사", "감": "감탄사", "의": "의존 명사"}
CJK = re.compile(r'[一-鿿豈-﫿]+')
TAIL = re.compile(r'\d+$')

def get(url):
    # curl 사용 — 파이썬 3.14의 SSL 인증서 문제를 피한다
    r = subprocess.run(["curl", "-s", "-A", UA, url], capture_output=True, text=True, timeout=30)
    return r.stdout

def tag(xml, name):
    return re.findall(rf"<{name}>(.*?)</{name}>", xml, re.S)

def cdata(s):
    m = re.search(r"<!\[CDATA\[(.*?)\]\]>", s, re.S)
    return (m.group(1) if m else s).strip()

def items(xml):
    return re.findall(r"<item>(.*?)</item>", xml, re.S)

def hanja_of(pul):
    s = unicodedata.normalize("NFKC", pul)
    return "".join(CJK.findall(s)) or None

def search(word):
    q = urllib.parse.quote(word)
    return get(f"https://krdict.korean.go.kr/api/search?key={KEY}&q={q}"
               f"&translated=y&trans_lang=7&num=30")

def view_origin(tc):
    xml = get(f"https://krdict.korean.go.kr/api/view?key={KEY}&method=target_code&q={tc}")
    ol = tag(xml, "original_language")
    return "".join(CJK.findall(unicodedata.normalize("NFKC", " ".join(ol)))) or None

def pick(word, pos_short, hanja, xml):
    """이름·품사 맞는 후보들 중 하나 고르기. (item조각, 확실성) 반환."""
    cand = []
    for it in items(xml):
        w = (tag(it, "word") or [""])[0].strip()
        p = (tag(it, "pos") or [""])[0].strip()
        if w != word:
            continue
        want = POS.get(pos_short)
        if want and p != want and not (pos_short == "보" and p.startswith("보조")):
            continue
        cand.append(it)
    if not cand:
        return None, "none"
    if len(cand) == 1:
        return cand[0], "single"
    if hanja:                                   # 동형어 — 한자로 가른다
        for it in cand:
            tc = (tag(it, "target_code") or [""])[0]
            if tc and view_origin(tc) == hanja:
                return it, "hanja"
            time.sleep(0.4)
    return cand[0], "first"                     # 못 가르면 첫 후보(가장 흔한 뜻)

def sense_of(it):
    s = re.search(r"<sense>(.*?)</sense>", it, re.S)
    if not s:
        return None
    s = s.group(1)
    tw = tag(s, "trans_word")
    td = tag(s, "trans_dfn")
    df = tag(s, "definition")
    if not tw:
        return None
    return {"vi": cdata(tw[0]), "vi_dfn": cdata(td[0]) if td else "",
            "ko_dfn": (df[0].strip() if df else ""),
            "tc": (tag(it, "target_code") or [""])[0]}

def main():
    rows = [(ln.split("\t")) for ln in
            (ROOT / "tools" / "nikl_5965.tsv").read_text().splitlines()[1:]]
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    n_ok = n_miss = 0
    for i, (rank, raw, pos, pul, grade) in enumerate(rows):
        if raw in done:
            continue
        word = TAIL.sub("", raw)
        xml = search(word)
        it, how = pick(word, pos, hanja_of(pul), xml)
        g = sense_of(it) if it else None
        done[raw] = g or {"miss": how}
        if g: n_ok += 1
        else: n_miss += 1
        if (len(done)) % 100 == 0:
            OUT.write_text(json.dumps(done, ensure_ascii=False, separators=(",", ":")))
            print(f"{len(done)}/{len(rows)}  붙음 {n_ok}  못찾음 {n_miss}", flush=True)
            time.sleep(30)
        # 함정: 초당 여러 건 연타(0.12초 간격, 434건)에 방화벽이 IP를 하루쯤 차단했다(2026-08 실측)
        time.sleep(1.0)
    OUT.write_text(json.dumps(done, ensure_ascii=False, separators=(",", ":")))
    total_ok = sum(1 for v in done.values() if "vi" in v)
    print(f"끝. 전체 {len(done)}  베트남어 뜻 {total_ok} ({total_ok*100//len(done)}%)", flush=True)

if __name__ == "__main__":
    main()
