#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""그림이 **뜻을 실제로 알려 주는지** 가려낸다 → data/_imgok.json

왜 (2026-08-30 검수): 구운 그림을 눈으로 보니
  '독특한' → 무지개색 자전거 · '적합하다' → 희미한 퍼즐 조각
그림을 보고 뜻을 떠올릴 수 없다. 대표님도 "추상적인 것들은 이미지 없어도 된다"고 하셨다.
그림이 뜻을 못 알려 주면 **없느니만 못하다** — 엉뚱한 것을 외우게 된다.
잣대: 그 그림만 보고 한국인이 뜻을 맞힐 수 있는가.
쓰기: python3 tools/img_audit.py [--limit N]
"""
import argparse, json, pathlib, re, subprocess, time

R = pathlib.Path(__file__).resolve().parent.parent
URL = "https://viet-ai.chaochao-app.workers.dev"
# 이 일은 **Qwen 에게 넘겨도 되는 일**이다 — 그림이 뜻을 알려 주는지 판정.
#   틀려도 사람이 알아볼 수 있는 갈래라 제미나이 몫을 아끼는 편이 낫다.
#   CHAO_LOCAL=1 로 돌리면 이 맥의 Qwen 이 한다 (tools/ai.py 참고).
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from ai import ask_text as _ask_text

ORIGIN = "https://tpgus5119-coder.github.io"
OUT = R / "data" / "_imgok.json"
CHUNK = 25
ASK = ("너는 낱말 카드를 만드는 편집자다. 아래는 [한국어 뜻, 그림 설명] 짝이다.\n"
       "**그 그림만 보고 한국인이 그 뜻을 떠올릴 수 있는가**를 판정하라.\n"
       "규칙\n"
       " ① 눈에 보이는 것(사과·의자·병원)은 대개 yes\n"
       " ② 성질·상태·마음·정도(독특한·적합하다·아마도·매우)는 대개 no\n"
       "    — 그림이 그 뜻이 아니라 **다른 것**을 떠올리게 하기 때문이다\n"
       " ③ 동작(달리다·먹다)은 그림이 그 동작을 뚜렷이 보여 주면 yes\n"
       " ④ 그림 설명이 뜻과 어긋나면 no\n"
       '출력은 JSON 배열만. [{"ko":"뜻","ok":true}]\n\n')


def ask(items, tries=4):
    """대리인이 이따금 '[object Object]' 를 돌려준다 — 그러면 다시 묻는다 (2026-08-30)."""
    for k in range(tries):
        t = _ask_text(ASK + json.dumps(items, ensure_ascii=False), max_tokens=2500)
        if "[object Object]" in t: time.sleep(1.2 * (k + 1)); continue
        m = re.search(r"\[.*\]", t, re.S)
        if m:
            try: return json.loads(m.group(0))
            except Exception: pass
        time.sleep(1.2 * (k + 1))
    return []


def main():
    a = argparse.ArgumentParser(); a.add_argument("--limit", type=int, default=0); a = a.parse_args()
    P = json.loads((R / "data" / "_imgprompts.json").read_text(encoding="utf-8"))
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    need = [(k, v) for k, v in P.items() if k not in have]
    if a.limit: need = need[:a.limit]
    print(f"판정할 그림 글감 {len(need)}개 · 이미 본 것 {len(have)}", flush=True)
    for i in range(0, len(need), CHUNK):
        part = need[i:i + CHUNK]
        items = [{"ko": k, "그림": re.split(r",\s*simple flat", str(v))[0]} for k, v in part]
        try: got = ask(items)
        except Exception as e: print("  건너뜀", type(e).__name__); time.sleep(3); continue
        ks = {k for k, _ in part}
        for g in got:
            k = str(g.get("ko", ""))
            if k in ks: have[k] = bool(g.get("ok"))
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
        no = sum(1 for v in have.values() if not v)
        print(f"  {min(i+CHUNK,len(need))}/{len(need)} · 뗄 것 {no}", flush=True)
        time.sleep(.3)
    no = sum(1 for v in have.values() if not v)
    print(f"끝. 본 것 {len(have)} · 그림을 뗄 것 {no}")


if __name__ == "__main__":
    main()
