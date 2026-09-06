#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""한국어 과정 소리를 Qwen3-TTS 하나의 목소리로 통째로 굽는다.

왜: 대표님 지시(2026-09-06) — 강의·애니·자유대화·면접 전부 같은 목소리여야 한다.
    지금 강의 소리는 gen_ko_audio.py(edge-tts, SunHi/InJoon 두 목소리)로 구워져 있는데,
    실시간 기능(면접·대화)은 Qwen3-TTS(sohee)로 가기로 했으므로 강의 쪽도 sohee로 다시 굽는다.

무엇이 필요한지는 gen_ko_audio.py의 collect()를 그대로 가져다 쓴다(중복 금지) — 새
데이터 출처가 생겨도 거기 한 곳만 고치면 둘 다 반영된다.

**기본은 안전 모드다** — audio/ko-qwen/n/ 이라는 새 자리에 굽는다. 실제 앱이 쓰는
audio/ko-f/n/ 을 덮지 않는다. 다 굽고 들어본 다음, 정말 바꿀 거면 --replace 로
실제 자리에 다시 굽는다(그때도 파일명은 같은 해시라 앱 코드는 손 안 대도 된다).

이미 있는 파일은 건너뛴다. 밤새 돌리다 끊겨도 이어서 하면 된다.

사용:
    ~/qwen-tts-env/bin/python tools/gen_ko_audio_qwen.py            # 안전 모드, audio/ko-qwen/
    ~/qwen-tts-env/bin/python tools/gen_ko_audio_qwen.py --replace  # 실제 자리(audio/ko-f/)에 굽기
    ~/qwen-tts-env/bin/python tools/gen_ko_audio_qwen.py --limit 50 # 먼저 50개만 (시간 가늠용)

밤새 돌리기:
    nohup ~/qwen-tts-env/bin/python tools/gen_ko_audio_qwen.py > logs/ko_audio_qwen.log 2>&1 &
"""
import hashlib, pathlib, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from gen_ko_audio import collect  # 무엇을 구울지는 기존 도구 그대로 재사용
from tts_qwen import speak


def speak_mp3(text: str, mp3_path: str):
    """tts_qwen 은 wav 로 만든다 — 기존 앱이 기대하는 mp3 로 바꿔서 저장한다."""
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        speak(text, tmp.name)
        subprocess.run(
            ["ffmpeg", "-y", "-v", "quiet", "-i", tmp.name, mp3_path],
            check=True,
        )

REPLACE = "--replace" in sys.argv
LIMIT = None
for i, a in enumerate(sys.argv):
    if a == "--limit":
        LIMIT = int(sys.argv[i + 1])

SUBDIR = "ko-f" if REPLACE else "ko-qwen"


def key(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:12]


def main():
    need = collect()
    items = list(need.items())
    if LIMIT:
        items = items[:LIMIT]
    total = len(items)
    print(f"대상 {total}개 · 자리: audio/{SUBDIR}/n/ {'(실제 자리 — 덮어씀)' if REPLACE else '(안전 모드, 새 자리)'}", flush=True)

    made, skipped, failed = 0, 0, 0
    out_dir = ROOT / "audio" / SUBDIR / "n"
    out_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.time()

    for i, (text, kind) in enumerate(items, 1):
        path = out_dir / f"{key(text)}.mp3"
        if path.exists():
            skipped += 1
            continue
        try:
            speak_mp3(text, str(path))
            made += 1
        except Exception as e:
            failed += 1
            print(f"실패: {text!r} — {e}", file=sys.stderr, flush=True)
        if i % 20 == 0:
            elapsed = time.time() - t_start
            print(f"  {i}/{total} · 만듦 {made} · 건너뜀 {skipped} · 실패 {failed} · {elapsed:.0f}초 경과", flush=True)

    print(f"\n끝 — 대상 {total} · 새로 만듦 {made} · 이미 있어 건너뜀 {skipped} · 실패 {failed}", flush=True)
    if failed:
        print("실패한 것들이 있다 — 위 로그에서 확인하고 다시 돌리면 그것만 재시도된다", flush=True)


if __name__ == "__main__":
    main()
