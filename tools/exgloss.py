#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**예문에만 나오는 낱말**의 뜻을 채운다 → data/exgloss.json

왜 (대표님 지시, 2026-08-30): "예문의 단어는 누르면 소리도 나야하고 발음과 뜻도 보여야한다."
눌러 보니 này(이)·đang(~하는 중)·ở(~에) 같은 기본 낱말이
「아직 뜻이 없는 낱말입니다」로 나왔다 — 466종이 3,201번.
과정 낱말표에 없는 말들이라 앱이 뜻을 못 찾은 것이다.
쓰기: python3 tools/exgloss.py
"""
import collections, json, pathlib, re, subprocess, time, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
URL = "https://viet-ai.chaochao-app.workers.dev"
# 이 일은 **Qwen 에게 넘겨도 되는 일**이다 — 예문 낱말 뜻 달기.
#   틀려도 사람이 알아볼 수 있는 갈래라 제미나이 몫을 아끼는 편이 낫다.
#   CHAO_LOCAL=1 로 돌리면 이 맥의 Qwen 이 한다 (tools/ai.py 참고).
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from ai import ask_text as _ask_text

ORIGIN = "https://tpgus5119-coder.github.io"
OUT = R / "data" / "exgloss.json"
CHUNK = 30
ASK = ("너는 베트남어-한국어 사전이다. 아래 낱말의 뜻을 **아주 짧게** 적어라.\n"
       "규칙 ① 한국어로 12자 이내 ② 여러 뜻이면 '·' 로 나눈다 ③ 기능어는 쓰임을 적는다\n"
       " (này→이·이것 · đang→~하는 중 · ở→~에·있다)\n"
       " ④ 모르면 뜻을 빈 문자열로 둔다. 지어내지 마라\n"
       '출력은 JSON 배열만. [{"vi":"낱말","ko":"뜻"}]\n\n')

def ask(items):
    t = _ask_text(ASK + json.dumps(items, ensure_ascii=False), max_tokens=2500)
    m = re.search(r"\[.*\]", t, re.S)
    return json.loads(m.group(0)) if m else []

def main():
    O = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    def walk(v):
        for t in (v.get("tracks") or [v]):
            for c in t["chapters"]:
                for l in c["lessons"]: yield from l["words"]
    W = [w for v in O["vols"] for w in walk(v)] + O.get("gramwords", [])
    voc = {U.normalize("NFC", w["vi"]).lower() for w in W}
    for w in W:
        for a in (w.get("alt") or []): voc.add(U.normalize("NFC", a["vi"]).lower())
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    voc |= {k for k, v in have.items() if v}

    miss = collections.Counter()
    for w in W:
        ex = w.get("ex")
        if not ex: continue
        toks = ex["vi"].split(); i = 0
        while i < len(toks):
            hit = 0
            for n in (3, 2, 1):
                ph = " ".join(toks[i:i + n]).strip(",.!?;:").lower()
                if len(toks[i:i + n]) == n and ph in voc: hit = n; break
            if hit: i += hit
            else: miss[toks[i].strip(",.!?;:").lower()] += 1; i += 1
    need = [k for k, _ in miss.most_common() if k and k not in have and re.search(r"[a-zà-ỹđ]", k)]
    print(f"뜻이 없는 낱말 {len(need)}종 (나온 횟수 {sum(miss.values())}회) · 이미 채운 것 {len(have)}", flush=True)
    for i in range(0, len(need), CHUNK):
        part = need[i:i + CHUNK]
        try: got = ask(part)
        except Exception as e: print("  건너뜀", type(e).__name__); time.sleep(3); continue
        for g in got:
            v = U.normalize("NFC", str(g.get("vi", ""))).lower().strip()
            k = str(g.get("ko", "")).strip()
            if v in {x.lower() for x in part} and k: have[v] = k
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {min(i+CHUNK,len(need))}/{len(need)} · 채운 것 {len(have)}", flush=True)
        time.sleep(.3)
    print(f"끝. 예문 낱말 사전 {len(have)}개")

main()
