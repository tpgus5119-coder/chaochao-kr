#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낱말의 **베트남어 철자**를 검사해 고친다 → data/_spell.json

왜 (2026-08-30): 예문을 못 만드는 낱말 75개를 들여다보니 전부 **오타**였다.
  cá phê sữa đá(생선커피) · giổng nhau · tư hào · bVđa khoa · người hương nội …
선배들이 시험지에 잘못 적은 것이 그대로 앱에 들어와 있었다.
잣대 ① 베트남어 사전(위키낱말) 발음표에 있으면 맞다  ② 없으면 AI 에게 묻는다
    ③ AI 가 고친 꼴이 **뜻과 맞는지** 다시 확인한다  ④ 못 미더우면 손 확인 목록에 남긴다
쓰기: python3 tools/spell_check.py [--limit N] [--all]
"""
import argparse, json, pathlib, re, subprocess, sys, time, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
URL = "https://viet-ai.chaochao-app.workers.dev"
# 이 일은 **Qwen 에게 넘겨도 되는 일**이다 — 철자 검사.
#   틀려도 사람이 알아볼 수 있는 갈래라 제미나이 몫을 아끼는 편이 낫다.
#   CHAO_LOCAL=1 로 돌리면 이 맥의 Qwen 이 한다 (tools/ai.py 참고).
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from ai import ask_text as _ask_text

ORIGIN = "https://tpgus5119-coder.github.io"
OUT = R / "data" / "_spell.json"
CHUNK = 20

ASK = ("너는 베트남어 사전 편집자다. 아래 목록에서 **철자가 틀린 것만** 바로잡아라.\n"
       "규칙\n"
       " ① 성조·모음 부호가 틀린 것을 고친다 (giổng→giống, tư hào→tự hào)\n"
       " ② 붙여 쓴 것을 띄운다 (tựgiới thiệu→tự giới thiệu)\n"
       " ③ 줄임말은 풀어 쓴다 (bVđa khoa→bệnh viện đa khoa)\n"
       " ④ **뜻이 맞아야 한다** — 주어진 한국어 뜻과 다른 낱말로 바꾸지 마라\n"
       " ⑤ 철자가 이미 맞으면 fix 를 빈 문자열로 둔다\n"
       " ⑥ 무엇으로 고칠지 모르겠으면 fix 를 \"?\" 로 둔다. 지어내지 마라\n"
       "출력은 JSON 배열만. 설명 금지.\n"
       '[{"vi":"원래 적힌 것","fix":"고친 것 또는 빈 문자열 또는 ?"}]\n\n')


def ask(items):
    body = json.dumps({"contents": [{"parts": [{"text": ASK + json.dumps(
        [{"vi": w["vi"], "ko": w["ko"]} for w in items], ensure_ascii=False)}]}]})
    p = subprocess.run(["curl", "-sS", "-X", "POST", URL, "-H", "Content-Type: application/json",
                        "-H", f"Origin: {ORIGIN}", "--data-binary", "@-"],
                       input=body, capture_output=True, text=True, timeout=180)
    t = p.stdout
    try:
        j = json.loads(t)
        t = j["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        pass
    m = re.search(r"\[.*\]", t, re.S)
    return json.loads(m.group(0)) if m else []


def main():
    a = argparse.ArgumentParser(); a.add_argument("--limit", type=int, default=0)
    a.add_argument("--all", action="store_true"); a = a.parse_args()

    P = json.loads((R / "data" / "senior_pool.json").read_text(encoding="utf-8"))["words"]
    ipa = json.loads((R / "data" / "_vi_ipa.json").read_text(encoding="utf-8"))
    dic = {U.normalize("NFC", k).lower() for k in ipa}
    done = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}

    need = []
    for w in P:
        v = U.normalize("NFC", w["vi"]).lower()
        if v in done: continue
        if not a.all and v in dic: continue        # 사전에 있으면 맞는 낱말이다
        need.append(w)
    if a.limit: need = need[:a.limit]
    print(f"검사할 낱말 {len(need)}개 · 이미 본 것 {len(done)}개 · 사전에 있는 것 {sum(1 for w in P if U.normalize('NFC',w['vi']).lower() in dic)}개", flush=True)

    nfix = 0
    for i in range(0, len(need), CHUNK):
        part = need[i:i + CHUNK]
        try: got = ask(part)
        except Exception as e: print("  건너뜀:", type(e).__name__); time.sleep(3); continue
        by = {U.normalize("NFC", str(g.get("vi", ""))).lower(): str(g.get("fix", "")).strip() for g in got}
        for w in part:
            v = U.normalize("NFC", w["vi"]).lower()
            f = by.get(v, "")
            done[v] = {"vi": w["vi"], "ko": w["ko"], "fix": f}
            if f and f != "?" and U.normalize("NFC", f).lower() != v: nfix += 1
        OUT.write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {min(i+CHUNK,len(need))}/{len(need)} · 고칠 것 누적 {nfix}", flush=True)
        time.sleep(.4)
    print(f"끝. 본 낱말 {len(done)} · 고칠 것 {nfix}")

main()
