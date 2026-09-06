#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""한 카드에 묶인 **뜻이 겹치는 낱말**을 갈라 세우고, 각자의 뜻을 다시 매긴다
   → data/_altsplit.json (낱말별 구별된 뜻)

왜 (대표님 지시, 2026-08-30): "미세하게 약간 다른 의미이며 다르게 사용될 것 같은데 맞니?
  그렇다면 그 단어들은 하나로 합치면 안 되겠다."
맞는 말이었다. 살펴보니 아예 다른 낱말까지 묶여 있었다 —
  bí quyết(비결) ↔ bí mật(비밀) · cơ hội(기회) ↔ cơ(기계) · lông mày(눈썹) ↔ mắt(눈)
그냥 가르기만 하면 두 낱말에 같은 뜻이 붙어 더 헷갈린다. 그래서 **뜻을 갈라 적는다.**
쓰기: python3 tools/split_alt.py
"""
import json, pathlib, re, subprocess, time, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
URL = "https://viet-ai.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"
OUT = R / "data" / "_altsplit.json"
CHUNK = 12
ASK = ("너는 베트남어 사전 편집자다. 아래는 **한국어 뜻이 겹쳐 보이는 낱말 짝**이다.\n"
       "둘의 쓰임이 어떻게 다른지 가려, 각 낱말에 **서로 구별되는 짧은 한국어 뜻**을 달아라.\n"
       "규칙\n"
       " ① 각 뜻은 14자 이내. 헷갈리지 않게 서로 다르게 적는다\n"
       "    (khó→어렵다 / khó khăn→곤란·어려움  ·  bí quyết→비결·노하우 / bí mật→비밀)\n"
       " ② 정말로 완전히 같은 말이면 same 를 true 로 둔다 (quần đùi / quần soóc)\n"
       " ③ 품사가 다르면 그것을 드러낸다 (동사/명사/형용사)\n"
       " ④ 모르면 뜻을 빈 문자열로 둔다. 지어내지 마라\n"
       '출력은 JSON 배열만. [{"a":"낱말1","ka":"뜻1","b":"낱말2","kb":"뜻2","same":false}]\n\n')


def ask(items):
    body = json.dumps({"contents": [{"parts": [{"text": ASK + json.dumps(items, ensure_ascii=False)}]}]})
    p = subprocess.run(["curl", "-sS", "-X", "POST", URL, "-H", "Content-Type: application/json",
                        "-H", f"Origin: {ORIGIN}", "--data-binary", "@-"],
                       input=body, capture_output=True, text=True, timeout=180)
    t = p.stdout
    try: t = json.loads(t)["candidates"][0]["content"]["parts"][0]["text"]
    except Exception: pass
    m = re.search(r"\[.*\]", t, re.S)
    return json.loads(m.group(0)) if m else []


def main():
    O = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    def walk(v):
        for t in (v.get("tracks") or [v]):
            for c in t["chapters"]:
                for l in c["lessons"]: yield from l["words"]
    pairs = []
    for v in O["vols"]:
        for w in walk(v):
            for a in (w.get("alt") or []):
                pairs.append({"a": w["vi"], "b": a["vi"], "ko": w["ko"]})
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    need = [p for p in pairs if f'{p["a"]}|{p["b"]}' not in have]
    print(f"갈라야 할 짝 {len(pairs)}개 · 아직 안 본 것 {len(need)}", flush=True)
    for i in range(0, len(need), CHUNK):
        part = need[i:i + CHUNK]
        try: got = ask(part)
        except Exception as e: print("  건너뜀", type(e).__name__); time.sleep(3); continue
        for g in got:
            a, b = str(g.get("a", "")).strip(), str(g.get("b", "")).strip()
            k = f"{a}|{b}"
            if any(p["a"] == a and p["b"] == b for p in part):
                have[k] = {"ka": str(g.get("ka", "")).strip(), "kb": str(g.get("kb", "")).strip(),
                           "same": bool(g.get("same"))}
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {min(i+CHUNK,len(need))}/{len(need)} · 가른 짝 {len(have)}", flush=True)
        time.sleep(.3)
    same = sum(1 for v in have.values() if v.get("same"))
    print(f"끝. 가른 짝 {len(have)} · 정말 같은 말이라 그대로 둘 것 {same}")

main()
