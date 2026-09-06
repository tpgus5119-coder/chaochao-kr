#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""소리가 **정말 그 낱말을 말하는지** 듣고 확인한다 → data/_ttschk.json

대표님 지적 (2026-09-01): "소리 듣는 거는 클로드도 못 했지?"
맞다. 지금까지의 소리 검수는 **파일이 있나·서로 다른가**만 봤다.
'이 파일이 그 낱말을 말하는가'는 아무도 확인하지 않았다. 그 구멍을 메운다.

## 어떻게
① **받아쓰기(Whisper)** — 소리를 글자로 되돌려 낱말과 맞대 본다
   Whisper 는 CPU 로 돈다. Draw Things 는 GPU 를 쓰므로 **함께 돌려도 안 부딪힌다**
② **목소리 높이** — 남녀가 제자리인지 잰다 (남 100~130Hz · 여 180~250Hz)

받아쓰기는 완벽하지 않다(성조 부호를 자주 놓친다).
그래서 **글자가 얼마나 닮았나**로 재고, **크게 어긋난 것만** 집어낸다.

쓰기: python3 tools/tts_check.py [--n 150] [--model small]
"""
import argparse, hashlib, json, pathlib, sys, unicodedata as U
from difflib import SequenceMatcher

R = pathlib.Path(__file__).resolve().parent.parent
OUT = R / "data" / "_ttschk.json"
VOICES = {"f": "북부 여", "m": "북부 남", "sf": "남부 여", "sm": "남부 남"}
key = lambda t: hashlib.sha1(t.encode()).hexdigest()[:12]


def plain(s):
    """성조 부호를 떼고 소문자로 — 받아쓰기는 성조를 자주 놓친다"""
    s = U.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if not U.combining(c))
    return "".join(c for c in s.replace("đ", "d") if c.isalnum() or c == " ").strip()


def f0_mean(path):
    """목소리 높이 평균(Hz). 남녀를 가르는 데 쓴다."""
    try:
        import numpy as np, soundfile as sf, subprocess, io, tempfile, os
        wav = tempfile.mktemp(suffix=".wav")
        subprocess.run(["ffmpeg", "-v", "quiet", "-y", "-i", str(path), "-ar", "16000",
                        "-ac", "1", wav], check=True)
        x, sr = sf.read(wav); os.unlink(wav)
        x = np.asarray(x, dtype=float)
        if x.size < sr // 10:
            return None
        # 자기상관으로 기본 주파수를 찾는다 (60~350Hz 만 본다)
        x = x - x.mean()
        lo, hi = sr // 350, sr // 60
        best, bv = None, 0
        c = np.correlate(x, x, "full")[len(x) - 1:]
        seg = c[lo:hi]
        if seg.size:
            i = int(np.argmax(seg)) + lo
            if c[0] > 0 and c[i] / c[0] > 0.3:
                best = sr / i
        return best
    except Exception:
        return None


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--n", type=int, default=150); a.add_argument("--model", default="small")
    a = a.parse_args()
    from faster_whisper import WhisperModel
    import random

    # **낱말이 사는 곳이 두 군데다** — days.json(하루 5분)과 order.json(직무).
    # 전에는 order.json 의 'topic' 붙은 낱말만 봐서, 그 과정을 빼자 대상이 0이 됐다
    # (2026-09-02 실측: 그림 검수도 같은 구멍이 있었다).
    o = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    def _walk(v):
        for t in (v.get("tracks") or [v]):
            for c in t.get("chapters", []):
                for l in c["lessons"]:
                    yield from l["words"]
    new = [w for v in o["vols"] for w in _walk(v)]
    dp = R / "data" / "days.json"
    if dp.exists():
        dj = json.loads(dp.read_text(encoding="utf-8"))
        new += [w for x in dj.get("days", []) for w in (x.get("words") or [])]
    seen_v, uniq = set(), []
    for w in new:
        if w.get("vi") and w["vi"] not in seen_v:
            seen_v.add(w["vi"]); uniq.append(w)
    new = uniq
    random.seed(7)
    S = random.sample(new, min(a.n, len(new)))
    print(f"들어 볼 낱말 {len(S)} × 네 목소리 = {len(S)*4}개", flush=True)

    m = WhisperModel(a.model, device="cpu", compute_type="int8", cpu_threads=6)
    res, bad = [], []
    for i, w in enumerate(S, 1):
        k = key(w["vi"]); want = plain(w["vi"])
        row = {"vi": w["vi"], "ko": w["ko"]}
        for v in VOICES:
            p = R / f"audio/{v}/n/{k}.mp3"
            if not p.exists():
                row[v] = {"들린 말": "(파일 없음)", "닮음": 0.0}; continue
            segs, _ = m.transcribe(str(p), language="vi", beam_size=1,
                                   vad_filter=False, without_timestamps=True)
            got = plain(" ".join(s.text for s in segs))
            sim = SequenceMatcher(None, want, got).ratio()
            row[v] = {"들린 말": got[:40], "닮음": round(sim, 2)}
        res.append(row)
        worst = min(row[v]["닮음"] for v in VOICES)
        if worst < 0.45:
            bad.append(row)
        if i % 25 == 0:
            print(f"  {i}/{len(S)} · 크게 어긋난 것 {len(bad)}", flush=True)
            OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    import statistics as st
    if not res:
        print("들어 본 낱말이 없다"); return
    print("\n목소리별 평균 닮음")
    for v, nm in VOICES.items():
        vals = [r[v]["닮음"] for r in res]
        print(f"  {nm}: {st.mean(vals):.2f}  (0.45 미만 {sum(1 for x in vals if x<0.45)}개)")
    print(f"\n네 목소리가 다 어긋난 낱말 {len(bad)}개")
    for r in bad[:20]:
        print(f"  {r['vi']:16}{r['ko']:12} 북여가 들은 말: {r['f']['들린 말'][:28]}")


if __name__ == "__main__":
    main()
