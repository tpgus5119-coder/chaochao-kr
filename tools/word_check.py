#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낱말이 **낱말답게 되어 있는지** 전수 검사한다 → data/_wordchk.json

대표님 지적 (2026-08-31): "납땜 박리가 뭐임?? 사전에 나오는 단어가 아닌것들이 있는지
                         점검해봐. 기판 휨, 기판 균열 등.. 두개의 단어 아니냐?
                         낙하시험 등등. 처음부터 끝까지 다 검사해라."

무엇을 보나 (한 낱말에 대해)
  ① 베트남어가 **진짜 쓰는 말**인가 (영어를 그대로 적었거나 철자가 틀리지 않았나)
  ② 한국어 뜻이 **말이 되는가** — 중간에 잘렸거나('부품 반'), 뜻이 어긋나지 않았나
     ('Tỷ lệ' 는 '비율'인데 '불량 비율'로 좁혀 적은 것 따위)
  ③ 두 낱말을 붙여 만든 말이면, 현장에서 실제로 그렇게 쓰는가
     ('기판 휨'처럼 현장에서 쓰면 괜찮다. 억지로 만든 말이면 걸러야 한다)

고치지는 않는다 — **판정만 모아** 사람이 보고 정한다.
AI 는 중계 워커(tools/worker.js)를 부른다.

쓰기: python3 tools/word_check.py [--limit N] [--track 직무]
"""
import argparse, json, pathlib, re, subprocess, sys, time, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
URL = "https://viet-ai.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"
OUT = R / "data" / "_wordchk.json"
CHUNK = 12

ASK = (
    "너는 베트남어-한국어 낱말 카드를 검수하는 편집자다.\n"
    "아래 [베트남어, 한국어 뜻] 짝을 하나씩 보고 **문제가 있는 것만** 골라라.\n"
    "문제 갈래\n"
    " · eng   : 베트남어 자리에 영어가 그대로 있다 (code left, marking G)\n"
    " · spell : 베트남어 철자가 틀렸다 (nhìu → nhiều)\n"
    " · cut   : 한국어 뜻이 중간에서 잘렸다 ('부품 반')\n"
    " · wrong : 뜻이 어긋난다. 너무 좁히거나 넓혔다 (Tỷ lệ=비율인데 '불량 비율')\n"
    " · made  : 실제로 안 쓰는 말을 억지로 붙여 만들었다\n"
    "괜찮은 것 (문제 아님)\n"
    " · 현장에서 실제로 쓰는 두 낱말 짜임 — 기판 휨, 낙하 시험, 생산 라인\n"
    " · 베트남어 동사를 한국어로 옮기며 목적어가 붙는 것 — '길을 잃다', '머리를 감다'\n"
    " · 뜻이 여럿이라 빗금(/)이나 쉼표로 나란히 적은 것\n"
    "규칙: 확신이 없으면 **넣지 마라.** 멀쩡한 것을 문제 삼으면 더 나쁘다.\n"
    '출력은 JSON 배열만: [{"vi":"...","why":"eng|spell|cut|wrong|made","fix":"고칠 안 또는 빈칸"}]\n\n'
)


def ask(items, tries=4):
    body = json.dumps({"contents": [{"parts": [{"text": ASK + json.dumps(items, ensure_ascii=False)}]}]})
    for k in range(tries):
        try:
            t = subprocess.run(
                ["curl", "-sS", "-X", "POST", URL, "-H", "Content-Type: application/json",
                 "-H", f"Origin: {ORIGIN}", "--data-binary", "@-"],
                input=body, capture_output=True, text=True, timeout=200).stdout
        except Exception:
            time.sleep(2 * (k + 1)); continue
        try: t = json.loads(t)["candidates"][0]["content"]["parts"][0]["text"]
        except Exception: pass
        t = re.sub(r"(?s)<think>.*?</think>", "", t)
        m = re.search(r"\[.*\]", t, re.S)
        if m:
            try: return json.loads(m.group(0))
            except Exception: pass
        time.sleep(1.5 * (k + 1))
    return []


def walk(v):
    for t in (v.get("tracks") or [v]):
        for c in t["chapters"]:
            for l in c["lessons"]:
                yield from l["words"]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--limit", type=int, default=0)
    a.add_argument("--track", default="")
    a = a.parse_args()

    O = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    words = []
    for i, v in enumerate(O["vols"]):
        if a.track == "직무" and v.get("kind") != "job":
            continue
        if a.track == "일상" and v.get("kind") == "job":
            continue
        words += list(walk(v))
    if not a.track:
        words += O.get("gramwords", [])

    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    need = [w for w in words if w["vi"] not in have]
    if a.limit: need = need[:a.limit]
    print(f"검사할 낱말 {len(need)}개 · 이미 본 것 {len(have)}", flush=True)

    hit = 0
    for i in range(0, len(need), CHUNK):
        part = need[i:i + CHUNK]
        items = [{"vi": w["vi"], "ko": w["ko"]} for w in part]
        try: got = ask(items)
        except Exception as e:
            print("  건너뜀", type(e).__name__); time.sleep(3); continue
        bad = {g.get("vi"): g for g in got if isinstance(g, dict) and g.get("vi")}
        for w in part:
            have[w["vi"]] = bad.get(w["vi"], {"why": "", "fix": "", "ko": w["ko"]})
            if w["vi"] in bad: hit += 1
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
        if (i // CHUNK) % 5 == 0:
            print(f"  {min(i+CHUNK,len(need))}/{len(need)} · 걸린 것 {hit}", flush=True)
    print(f"끝. 본 낱말 {len(need)} · 문제로 걸린 것 {hit} → {OUT}")


main()
