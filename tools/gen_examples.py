#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낱말마다 **예문 한 줄**을 만든다 → data/_examples.json

왜 필요한가: 새 짜임에서는 문장이 따로 있지 않고 **낱말 밑에 예문**으로 붙는다.
앱이 가진 대화에서 1,313개는 꺼내 쓸 수 있지만 나머지 4,100개는 문장이 없다.
그래서 무료 AI 대리인(viet-ai)에게 스물다섯 개씩 묶어 부탁한다.

지키는 것
  · 문장은 **여덟 낱말 이하**, 지금 일어나는 일, 일상 말투
  · 그 낱말이 **문장 안에 반드시 들어 있어야** 받는다(안 들어 있으면 버린다)
  · 만든 것은 `src:"ai"` 로 표시해 나중에 사람이 볼 수 있게 남긴다
  · 중간에 끊겨도 **이어서** 돌 수 있게 한 묶음마다 파일에 쓴다
쓰기: python3 tools/gen_examples.py [--limit N]
"""
import argparse, json, pathlib, re, subprocess, sys, time, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr

URL = "https://viet-ai.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"
OUT = R / "data" / "_examples.json"
CHUNK = 25

ASK = ("너는 베트남어 교사다. 아래 낱말마다 **초급자용 예문 한 개**를 만든다.\n"
       "규칙: ① 문장은 여덟 낱말 이하 ② 그 낱말이 문장 안에 반드시 들어간다\n"
       "③ 아주 흔한 말만 쓴다 ④ 자연스러운 일상 문장 ⑤ 한국어 뜻을 함께 적는다\n"
       "출력은 JSON 배열만. 설명 금지.\n"
       '형식: [{"w":"낱말","vi":"베트남어 문장","ko":"한국어 뜻"}]\n\n낱말:\n')

def norm(v):
    return re.sub(r"\s+", " ", U.normalize("NFC", str(v)).strip().lower())

def ask(words):
    body = json.dumps({"contents": [{"parts": [{"text": ASK + "\n".join(
        f"- {w['vi']} ({w['ko'][:18]})" for w in words)}]}]}, ensure_ascii=False)
    p = subprocess.run(["curl", "-s", "-X", "POST", URL, "-m", "120",
                        "-H", "Content-Type: application/json", "-H", "Origin: " + ORIGIN,
                        "--data-binary", "@-"], input=body.encode(), capture_output=True)
    try:
        j = json.loads(p.stdout.decode())
        t = j["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return []
    m = re.search(r"\[.*\]", t, re.S)
    if not m: return []
    try: return json.loads(m.group(0))
    except Exception: return []

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int, default=0)
    # 여러 개를 한꺼번에 돌리려고 나눈다 — 한 판이 4천 개를 혼자 하면 일곱 시간이 걸린다.
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    a = ap.parse_args()
    global OUT
    if a.of > 1: OUT = R / "data" / f"_examples-{a.part}.json"
    # 낱말 목록은 **원천**에서 바로 가져온다 (2026-08-30).
    #   전에는 course.json 을 봤는데 그건 이미 걸러진 뒤라, 예문이 없어 떨어진 낱말은
    #   영영 예문을 못 받는 닭-달걀이 되었다.
    need = []
    for w in json.loads((R / "data" / "_senior_split.json").read_text(encoding="utf-8"))["words"]:
        if w.get("ko"): need.append({"vi": w["vi"], "ko": w["ko"]})
    d = json.loads((R / "data" / "days.json").read_text(encoding="utf-8"))
    for day in (d if isinstance(d, list) else d["days"]):
        for w in (day.get("words") or []):
            if w.get("vi") and w.get("ko"): need.append({"vi": w["vi"], "ko": w["ko"]})
    # 대표님이 주신 자료 — 봉제용어.xls · 생산관리 카톡방
    for f in ("_sewing.json", "_kakao_job.json", "_trade.json", "_jobwords.json"):
        p2 = R / "data" / f
        if p2.exists():
            for w in json.loads(p2.read_text(encoding="utf-8"))["words"]:
                need.append({"vi": w["vi"], "ko": w["ko"]})
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    # 다른 판이 이미 만든 것도 건너뛴다
    done = dict(have)
    for f in sorted((R / "data").glob("_examples*.json")):
        if f != OUT:
            try: done.update(json.loads(f.read_text(encoding="utf-8")))
            except Exception: pass
    need = [w for w in need if norm(w["vi"]) not in done]
    if a.of > 1: need = need[a.part::a.of]
    if a.limit: need = need[:a.limit]
    print(f"예문이 필요한 낱말 {len(need)}개 · 이미 만든 것 {len(have)}개", flush=True)
    bad = 0
    for i in range(0, len(need), CHUNK):
        part = need[i:i + CHUNK]
        got = ask(part)
        n = 0
        for g in got:
            w, vi, ko = norm(g.get("w", "")), str(g.get("vi", "")).strip(), str(g.get("ko", "")).strip()
            if not (w and vi and ko): continue
            if w not in norm(vi): bad += 1; continue          # 낱말이 안 들어간 문장은 버린다
            have[w] = {"vi": vi, "ko": ko, "kr": vi_kr.word(vi), "krs": vi_kr.word(vi, True), "src": "ai"}
            n += 1
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"  {i + len(part)}/{len(need)} · 이번에 {n}개 · 버린 것 누적 {bad}", flush=True)
        time.sleep(1.2)
    print(f"끝. 만든 예문 {len(have)}개", flush=True)
main()
