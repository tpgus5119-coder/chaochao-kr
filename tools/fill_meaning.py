#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**뜻이 비어 있는 선배 낱말**의 뜻을 채운다 → data/_meanings.json

시험지에는 낱말이 적혀 있는데 뜻 칸이 빈 줄이 많다(공란 시험지·칸 어긋남).
그 낱말이 다른 줄에도 없으면 통째로 버려졌다 — 767개나 된다.
`chúc mừng năm mới`(새해 복) · `thư ký`(비서) · `mùa thu`(가을) 같은 흔한 말이다.
버릴 것이 아니라 **뜻을 찾아 넣어야** 한다 (대표님 지시, 2026-08-30).

지키는 것
  · 한국어 뜻 하나만. 설명 금지.
  · 인도네시아어가 섞여 있다(18기 자료) — 낱말집으로 걸러 낸다.
  · 만든 뜻은 `mk:1` 로 표시해 나중에 사람이 볼 수 있게 남긴다.
쓰기: python3 tools/fill_meaning.py [--part N --of M]
"""
import argparse, json, pathlib, re, subprocess, sys, time, unicodedata as U, collections

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import senior_merge as M, senior_hand as H

URL = "https://viet-ai.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"
OUT = R / "data" / "_meanings.json"
CHUNK = 30
VI = re.compile(r"[ăâđêôơưÀ-ỹ]", re.I)
# 인도네시아어 표시말 — 18기 자료에 섞여 있다
ID = re.compile(r"^(peng|pen|per|ber|ter|mem|meng|men|se)[a-z]{3,}|kan$|nya$|"
                r"^(memang|sekaligus|adalah|dengan|untuk|yang|dari|akan|sudah|tidak)$", re.I)

ASK = ("아래 베트남어 낱말의 **한국어 뜻**을 하나씩 적어라.\n"
       "규칙: ① 뜻만 짧게(설명 금지) ② 베트남어가 아니면 뜻 자리에 빈 문자열\n"
       "③ 여러 뜻이면 가장 흔한 것 하나, 필요하면 '·'로 둘까지\n"
       "출력은 JSON 배열만.\n"
       '형식: [{"w":"낱말","ko":"뜻"}]\n\n낱말:\n')

def ask(words):
    body = json.dumps({"contents": [{"parts": [{"text": ASK + "\n".join("- " + w for w in words)}]}]},
                      ensure_ascii=False)
    p = subprocess.run(["curl", "-s", "-X", "POST", URL, "-m", "120",
                        "-H", "Content-Type: application/json", "-H", "Origin: " + ORIGIN,
                        "--data-binary", "@-"], input=body.encode(), capture_output=True)
    try:
        t = json.loads(p.stdout.decode())["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(re.search(r"\[.*\]", t, re.S).group(0))
    except Exception:
        return []

def need_words():
    raw = []
    for gi in ("17", "18", "19", "20"):
        p = R / "data" / f"_senior_scan-{gi}.json"
        if not p.exists(): continue
        for f in json.loads(p.read_text(encoding="utf-8"))["files"]:
            for r in f["rows"]: raw.append((r.get("vi", ""), r.get("ko", ""), (r.get("en") or "")))
    pool = {M.norm(w["vi"]) for w in
            json.loads((R / "data" / "senior_pool.json").read_text(encoding="utf-8"))["words"]}
    c = collections.Counter()
    for vi0, ko0, en0 in raw:
        vi, ko = M.norm(vi0), M.clean_ko(ko0)
        if not vi or ko or en0.strip() or vi in pool: continue
        if len(vi.split()) > 4 or len(vi) > 34: continue
        if any(ID.match(t) for t in vi.split()): continue        # 인도네시아어
        if H.not_viet(vi) and not VI.search(vi): continue
        c[vi] += 1
    return [w for w, _ in c.most_common()]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, default=0); ap.add_argument("--of", type=int, default=1)
    a = ap.parse_args()
    global OUT
    if a.of > 1: OUT = R / "data" / f"_meanings-{a.part}.json"
    need = need_words()
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    done = dict(have)
    for f in (R / "data").glob("_meanings*.json"):
        if f != OUT:
            try: done.update(json.loads(f.read_text(encoding="utf-8")))
            except Exception: pass
    if a.of > 1: need = need[a.part::a.of]
    need = [w for w in need if w not in done]
    print(f"뜻을 채울 낱말 {len(need)}개", flush=True)
    for i in range(0, len(need), CHUNK):
        part = need[i:i + CHUNK]
        for g in ask(part):
            w, ko = str(g.get("w", "")).strip().lower(), str(g.get("ko", "")).strip()
            if w and ko and len(ko) <= 24: have[w] = ko
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"  {i + len(part)}/{len(need)}", flush=True)
        time.sleep(1.0)
    print(f"끝. 뜻 {len(have)}개", flush=True)

main()
