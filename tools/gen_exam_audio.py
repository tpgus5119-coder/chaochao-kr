#!/usr/bin/env python3
"""시험 듣기 소리를 **실제 시험 속도로** 따로 굽는다 (audio/ko-{f,m}/x/).

왜 따로 굽나 — 실측했다(tools/listen_rate.py):
    공식 102회 TOPIK I 듣기   2.97 ~ 3.33 글자/초 (무음 걷어낸 값)
    우리 듣기 소리(+0%)       5.62 글자/초
    → **우리가 1.78배 빨랐다.** 시험보다 훨씬 빠른 소리로 연습하면
      연습이 시험보다 어려워지고, 학습자가 자기 실력을 가늠할 수 없다.

    edge-tts 속도를 바꿔 가며 재 보니 -45% 에서 3.2 글자/초가 나온다.
    공식 범위 한가운데다. 그래서 -45%.

낱말 소리는 그대로 둔다. 낱말은 또박또박 빨리 들려주는 편이 외우기 좋고,
느린 것은 **시험 흉내**일 때만 필요하다. 그래서 'x'(시험) 갈래를 따로 둔다.

실행: python3 tools/gen_exam_audio.py [--limit N]
"""
import asyncio
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# 실측으로 고른 값. 공식 35회 TOPIK I 음원을 **같은 자로** 재면 3.28 글자/초다
# (파일 39.3분 중 말한 시간 15.1분 · 대본 1,488자 × 두 번 읽기).
# 같은 문장을 속도별로 실제로 구워 재 본 값:
#     -45% → 3.52   -50% → 3.21   -55% → 3.21   -60% → 3.21
# edge-tts 는 -50% 아래로는 더 느려지지 않는다(세 값이 같다). 그래서 -50% 가 하한이고,
# 공식 3.28 과 2% 차이라 여기가 맞는 자리다. 25~30번 대사를 공식 길이로 늘린 뒤
# 다시 재니 -45% 로는 3.5~3.7 이 나와 실제보다 빨랐다 — 그래서 옮겼다.
RATE = "-50%"
VOICES = {"f": "ko-KR-SunHiNeural", "m": "ko-KR-InJoonNeural"}


def wanted():
    """시험지에서 실제로 들려주는 말과, 그 말을 누가 하는지."""
    ex = json.loads((ROOT / "data" / "ko_exams.json").read_text(encoding="utf-8"))
    need = {}
    for e in ex["exams"]:
        for q in e["questions"]:
            for a in (q.get("audio") or []):
                if isinstance(a, str):
                    need.setdefault(a, set()).update("fm")   # 누구 목소리든 쓸 수 있다
                else:
                    need.setdefault(a.get("t", ""), set()).add(a.get("v") or "f")
    need.pop("", None)
    return need


async def one(text, v, key, sem, made):
    path = ROOT / "audio" / f"ko-{v}" / "x" / f"{key}.mp3"
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    import edge_tts
    async with sem:
        for attempt in range(3):
            try:
                await edge_tts.Communicate(text, VOICES[v], rate=RATE).save(str(path))
                made.append(1)
                if len(made) % 50 == 0:
                    print(f"  {len(made)}개", flush=True)
                return
            except Exception as e:
                if attempt == 2:
                    print(f"실패 {text[:18]} ({v}): {e}", file=sys.stderr)
                    path.unlink(missing_ok=True)
                else:
                    await asyncio.sleep(1 + attempt)


async def main():
    idx = json.loads((ROOT / "data" / "ko_audio_index.json").read_text(encoding="utf-8"))
    need = wanted()
    jobs = []
    miss = 0
    for text, vs in need.items():
        key = idx.get(text)
        if not key:
            miss += 1          # 색인에 없는 말 — 낱말 소리부터 만들어야 한다
            continue
        for v in vs:
            jobs.append((text, v, key))
    lim = None
    if "--limit" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--limit") + 1])
        jobs = jobs[:lim]
    print(f"시험 듣기 말 {len(need)}개 · 구울 것 {len(jobs)}개 "
          f"(속도 {RATE} · 색인에 없는 말 {miss}개)")
    sem = asyncio.Semaphore(8)
    made = []
    await asyncio.gather(*[one(t, v, k, sem, made) for t, v, k in jobs])
    print(f"끝 — 새로 {len(made)}개")


if __name__ == "__main__":
    asyncio.run(main())
