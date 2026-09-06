#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**앱 밖 낱말이 든 예문**을 앱 안 낱말로 다시 짓는다 → data/_examples.json 을 고쳐 쓴다

대표님이 정한 차례 (2026-08-30):
  0. 그 낱말이 예문에 들어 있어야 한다 (기본)
  1. 이미 배운 낱말 → 2. 같은 레슨 → 3. 같은 챕터 → 4. 같은 권 → 5. 앱 어딘가
  6. 앱에 없는 낱말은 되도록 안 쓴다
그래서 AI 에게 **쓸 수 있는 낱말 목록을 함께 준다** — 앞선 레슨에서 배운 말을 먼저.
새 예문이 옛것보다 나쁘면 **안 바꾼다** (등급을 매겨 견준다).
쓰기: python3 tools/ex_fix.py [--limit N] [--worst N]
"""
import argparse, json, pathlib, re, subprocess, sys, time, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import ex_check as EC, vi_kr

URL = "https://viet-ai.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"
CHUNK = 10
ASK = ("너는 베트남어 교사다. 아래 낱말마다 **예문 한 개**를 다시 만들어라.\n"
       "규칙\n"
       " ① 그 낱말이 예문에 **반드시** 들어간다\n"
       " ② 나머지 말은 되도록 **'쓸 수 있는 낱말'** 목록 안에서 고른다\n"
       " ③ 여덟 낱말 이하, 일터·일상에서 실제로 쓸 말\n"
       " ④ 한국어 뜻을 함께 적는다\n"
       "출력은 JSON 배열만. 설명 금지.\n"
       '[{"vi":"주어진 낱말","ex":"베트남어 예문","ko":"한국어 뜻"}]\n\n')


def ask(items):
    body = json.dumps({"contents": [{"parts": [{"text": ASK + json.dumps(items, ensure_ascii=False)}]}]})
    p = subprocess.run(["curl", "-sS", "-X", "POST", URL, "-H", "Content-Type: application/json",
                        "-H", f"Origin: {ORIGIN}", "--data-binary", "@-"],
                       input=body, capture_output=True, text=True, timeout=240)
    t = p.stdout
    try: t = json.loads(t)["candidates"][0]["content"]["parts"][0]["text"]
    except Exception: pass
    m = re.search(r"\[.*\]", t, re.S)
    return json.loads(m.group(0)) if m else []


def score(vi_text, self_vi, p, seq, place, order, other):
    """예문 하나를 재서 (앱 밖 낱말 수, 등급 합) 을 낸다. 작을수록 좋다."""
    bad = tot = n = 0
    for t in [EC.nfc(x) for x in vi_text.split() if EC.nfc(x)]:
        if re.fullmatch(r"[\d.,%]+", t): continue
        g = EC.grade(t, self_vi, p, seq, place, order, other)
        tot += g; n += 1
        if g == 6: bad += 1
    return (bad, tot / max(1, n))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--limit", type=int, default=0)
    a.add_argument("--worst", type=int, default=2)      # 앱 밖 낱말이 이만큼 넘는 것만
    a = a.parse_args()

    place, order, cards, other = EC.load()
    EXP = R / "data" / "_examples.json"
    EX = json.loads(EXP.read_text(encoding="utf-8"))
    sys.path.insert(0, str(R / "tools")); import order_build as OB

    todo = []
    for p, seq, w in cards:
        ex = w.get("ex")
        if not ex: continue
        self_vi = {EC.nfc(x) for x in [w["vi"]] + [z["vi"] for z in (w.get("alt") or [])]}
        bad, avg = score(ex["vi"], self_vi, p, seq, place, order, other)
        if bad >= a.worst:
            # 이 낱말이 있는 자리에서 **앞서 배우는 낱말**을 골라 준다
            near = [x for x in place if order.get(x, 10 ** 9) < seq]
            near.sort(key=lambda x: -order.get(x, 0))
            todo.append({"w": w, "p": p, "seq": seq, "self": self_vi, "bad": bad,
                         "vocab": near[:70]})
    todo.sort(key=lambda x: -x["bad"])
    if a.limit: todo = todo[:a.limit]
    print(f"다시 지을 예문 {len(todo)}개 (앱 밖 낱말 {a.worst}개 이상)", flush=True)

    better = worse = 0
    for i in range(0, len(todo), CHUNK):
        part = todo[i:i + CHUNK]
        items = [{"vi": t["w"]["vi"], "ko": t["w"]["ko"], "쓸 수 있는 낱말": t["vocab"]} for t in part]
        try: got = ask(items)
        except Exception as e: print("  건너뜀", type(e).__name__); time.sleep(3); continue
        by = {EC.nfc(g.get("vi", "")): g for g in got}
        for t in part:
            g = by.get(EC.nfc(t["w"]["vi"]))
            if not g: continue
            new = str(g.get("ex", "")).strip()
            ko = str(g.get("ko", "")).strip()
            if not new or not ko: continue
            if not any(v and v in EC.nfc(new) for v in t["self"]): continue   # 낱말이 안 들어감
            nb, navg = score(new, t["self"], t["p"], t["seq"], place, order, other)
            if (nb, navg) >= (t["bad"], 99): worse += 1; continue
            if nb >= t["bad"]: worse += 1; continue
            k = OB.exkey(t["w"]["vi"])
            EX[k] = {"vi": new, "ko": ko, "kr": vi_kr.word(new), "krs": vi_kr.word(new, True), "src": "ai2"}
            better += 1
        EXP.write_text(json.dumps(EX, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {min(i+CHUNK,len(todo))}/{len(todo)} · 나아진 것 {better} · 그대로 둔 것 {worse}", flush=True)
        time.sleep(.3)
    print(f"끝. 바꾼 예문 {better}개 · 옛것이 나아 그대로 둔 것 {worse}개")

main()
