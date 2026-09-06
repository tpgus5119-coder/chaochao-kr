#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""한국어 과정 소리를 Qwen3-TTS(여성 sohee · 남성 aiden)로 굽고, Whisper로 실제 발음이
원문과 맞는지 검수까지 한다 — 생성만 하고 끝내지 않는다(2026-09-06 대표님 지시: "검수 당연히
했지?"에 대한 답으로 이 스크립트를 새로 만듦. gen_ko_audio_qwen.py는 검수가 없었다).

방법(오늘 Orpheus에 썼던 것과 같은 원칙, 단 Qwen은 실패율이 훨씬 낮아 재시도 횟수를 줄임):
  생성 → Whisper 로 받아쓰기 → (순서를 살린 문자열 비교 + 길이 이상 여부) 로 판정
  → 틀리면 최대 3번까지 재생성 → 그래도 안 되면 실패 목록에 남기고 넘어간다(수동 확인용).

무엇을 구울지는 gen_ko_audio.py 의 collect() 그대로 재사용(중복 금지).
남녀 둘 다 같은 문장을 굽는다 — 기존 edge-tts(ko-f/ko-m) 구조와 동일하게, 듣기 문항에서
두 사람이 주고받는 말을 만들 수 있어야 하기 때문이다.

**기본은 안전 모드다** — audio/ko-qwen2/{f,m}/ 라는 새 자리에 굽는다. 실제 앱이 쓰는
audio/ko-f, audio/ko-m 을 덮지 않는다. 다 굽고 검수 결과까지 확인한 다음, 정말 바꿀 거면
--replace 로 실제 자리에 다시 굽는다(그때도 파일명은 같은 해시라 앱 코드는 손 안 대도 된다).

사용:
    ~/qwen-tts-env/bin/python tools/gen_ko_audio_qwen_verified.py             # 안전 모드
    ~/qwen-tts-env/bin/python tools/gen_ko_audio_qwen_verified.py --replace   # 실제 자리
    ~/qwen-tts-env/bin/python tools/gen_ko_audio_qwen_verified.py --limit 50  # 시간 가늠용

밤새 돌리기:
    nohup ~/qwen-tts-env/bin/python tools/gen_ko_audio_qwen_verified.py \
        > logs/ko_audio_qwen_verified.log 2>&1 & disown
"""
import difflib
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from gen_ko_audio import collect  # 무엇을 구울지는 기존 도구 그대로 재사용
from tts_qwen import VOICES, speak

REPLACE = "--replace" in sys.argv
LIMIT = None
for i, a in enumerate(sys.argv):
    if a == "--limit":
        LIMIT = int(sys.argv[i + 1])

MAX_ROUNDS = 3
_DIGIT_MAP = {"한": "1", "두": "2", "세": "3", "네": "4", "다섯": "5",
              "여섯": "6", "일곱": "7", "여덟": "8", "아홉": "9", "열": "10"}


def norm(s):
    return re.sub(r"[^가-힣0-9a-zA-Z]", "", s)


def digit_norm(s):
    for k, v in _DIGIT_MAP.items():
        s = s.replace(k, v)
    return s


def key(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:12]


_whisper_model = None


def get_whisper():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print("Whisper 로딩 중...", flush=True)
        _whisper_model = whisper.load_model("small")
    return _whisper_model


def verify(wav_path: str, sent: str) -> dict:
    """받아쓰기와 원문을 순서 살려 비교 + 문장 길이 대비 오디오 길이 이상 여부.
    (오늘 Orpheus 검수에서 문자 집합 overlap만 보다가 "밥이나"->"가리나" 놓친 것,
    Whisper가 뒤쪽 환각을 못 받아써서 길이 이상을 놓친 것 — 이 두 버그를 이미 겪어서
    처음부터 이 두 가지를 다 본다.)"""
    target_n = digit_norm(norm(sent))
    model = get_whisper()
    r = model.transcribe(wav_path, language="ko", verbose=False)
    got_n = digit_norm(norm(r["text"].strip()))
    seq_ratio = difflib.SequenceMatcher(None, got_n, target_n, autojunk=False).ratio()
    dur = float(subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", wav_path]).decode().strip())
    expected_max = len(target_n) * 0.35 + 1.8
    ok = seq_ratio >= 0.92 and dur <= expected_max
    return {"ok": ok, "seq_ratio": seq_ratio, "dur": dur, "expected_max": expected_max, "text": r["text"].strip()}


def speak_mp3_verified(text: str, mp3_path: str, speaker: str) -> dict:
    """검수까지 통과한 mp3 를 mp3_path 에 쓴다. 결과 상태를 반환."""
    for round_i in range(MAX_ROUNDS):
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            speak(text, tmp.name, speaker=speaker)
            v = verify(tmp.name, text)
            if v["ok"]:
                subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-i", tmp.name, mp3_path], check=True)
                return {"status": "통과", "round": round_i, **v}
    # 마지막 시도 결과라도 남겨서 손으로 확인할 수 있게 한다(실패해도 최선 결과를 mp3로 남김)
    subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-i", tmp.name, mp3_path], check=True)
    return {"status": "미해결", "round": MAX_ROUNDS - 1, **v}


def main():
    need = collect()
    items = list(need.items())
    if LIMIT:
        items = items[:LIMIT]
    total = len(items)
    # 여성(f)은 오늘 새벽 이미 4,102개를 audio/ko-qwen/n/ 에 구워뒀다(미검수 상태) — 그 자리를
    # 그대로 재사용해서 검수만 하고, 틀린 것만 다시 굽는다(3시간 41분짜리 작업을 통째로
    # 버리지 않기 위해). 남성(aiden)은 이번에 새로 고른 목소리라 처음부터 굽는다.
    base = ("ko-f", "ko-m") if REPLACE else ("ko-qwen", "ko-qwen2/m")
    print(f"대상 {total}개 x 2목소리 · 자리: {base} {'(실제 자리 — 덮어씀)' if REPLACE else '(안전 모드)'}", flush=True)

    fail_log = []
    t_start = time.time()
    counters = {"made": 0, "skipped": 0, "failed": 0}

    for gender, subdir in zip(("f", "m"), base):
        speaker = VOICES[gender]
        out_dir = ROOT / "audio" / subdir / "n"
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, (text, kind) in enumerate(items, 1):
            path = out_dir / f"{key(text)}.mp3"
            if path.exists():
                # 이미 파일이 있어도(예: 오늘 새벽 미검수 상태로 만든 sohee 배치) "생성됨"과
                # "검수 통과"는 다른 것이므로 일단 검수부터 한다 — 통과면 재생성 없이 넘어간다.
                v = verify(str(path), text)
                if v["ok"]:
                    counters["skipped"] += 1
                    continue
                print(f"  기존 파일 검수 실패[{gender}], 재생성: {text!r} seq={v['seq_ratio']:.2f}", flush=True)
            try:
                r = speak_mp3_verified(text, str(path), speaker)
                if r["status"] == "통과":
                    counters["made"] += 1
                else:
                    counters["failed"] += 1
                    fail_log.append({"gender": gender, "text": text, **r})
                    print(f"  미해결[{gender}]: {text!r} seq={r['seq_ratio']:.2f} dur={r['dur']:.1f}/{r['expected_max']:.1f} 받아쓰기={r['text']!r}", flush=True)
            except Exception as e:
                counters["failed"] += 1
                fail_log.append({"gender": gender, "text": text, "status": "예외", "error": str(e)})
                print(f"  예외[{gender}]: {text!r} — {e}", file=sys.stderr, flush=True)
            if i % 20 == 0:
                elapsed = time.time() - t_start
                print(f"  [{gender}] {i}/{total} · 새로검수통과 {counters['made']} · 기존검수통과 {counters['skipped']} · 미해결 {counters['failed']} · {elapsed:.0f}초 경과", flush=True)

    print(f"\n끝 — 새로검수통과 {counters['made']} · 기존검수통과(재생성불필요) {counters['skipped']} · 미해결 {counters['failed']}", flush=True)
    if fail_log:
        fail_path = ROOT / "logs" / "ko_audio_qwen_verified_fails.json"
        fail_path.write_text(json.dumps(fail_log, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"미해결 목록: {fail_path}", flush=True)


if __name__ == "__main__":
    main()
