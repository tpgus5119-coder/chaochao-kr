#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""면접·자유대화처럼 **그때그때 무슨 말이 나올지 모르는** 한국어 음성을 만드는 통로.

왜 edge-tts(`gen_audio.py`)가 아니라 이걸 따로 두나:
edge-tts 는 마이크로소프트 엣지 브라우저 기능을 빌려 쓰는 것이라, 미리 구워 두는
교재·모의고사 소리(하루 몇 번, 대표님이 직접 돌림)에는 맞지만, 실서비스에서 유저가
아무 때나 실시간으로 부르는 기능(면접·자유대화)에 그대로 쓰기엔 상업적 근거가 약하다.
Qwen3-TTS(알리바바, Apache 2.0 — 상업 이용 명시)를 이 맥에서 직접 돌려서 그 자리를 메운다.

## 확인한 사실 (2026-09-06, 대화 세션에서 40개 문장 생성 후 Whisper 대조 검수)
· 모델: Qwen3-TTS-12Hz-1.7B-CustomVoice (0.6B 판보다 3배 큰데 속도는 거의 같음 — 3~11초/문장)
· 목소리: 여성=sohee(한국어 전용), 남성=aiden(영어 화자지만 한국어 발음 정확도 검수 통과) —
  대표님이 9명 전부 들어보고 직접 고름(2026-09-06). 듣기 문항처럼 남녀가 번갈아 말하는
  자리엔 이 두 목소리를 그대로 쓴다(edge-tts 시절 ko-f/ko-m 구조와 동일).
· CPU 로만 돌려도 된다(느리지만 GPU 없이 실사용 가능한 속도)
· 문장 40개(성별 섞어서) 생성 후 전부 Whisper 로 받아써서 대조 — 이상한 문장·반복 0건
  (같은 세션에서 비교한 Orpheus 는 10개 중 10개가 환각 — 그래서 이 모델을 골랐다)

## 모델 자리 — **임시 폴더에 두지 않는다** (gen_south_vtts.py 와 같은 원칙)
venv: ~/qwen-tts-env  ·  모델 캐시: ~/.cache/huggingface (첫 실행 때 자동으로 받는다, ~2GB)
둘 다 이 프로젝트 폴더 밖, 홈 디렉터리 아래 있어 대화 상자가 닫혀도 안 지워진다.

쓰기:
    from tts_qwen import speak
    speak("면접 질문 텍스트", "out.wav")

실행 확인:  ~/qwen-tts-env/bin/python tools/tts_qwen.py "테스트할 문장"
"""
import sys

MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "Sohee"  # 기본값(여성). 남성은 speak() 호출 시 speaker="aiden" 넘긴다.
VOICES = {"f": "sohee", "m": "aiden"}  # gen_ko_audio.py 의 VOICES 와 짝 맞춤(같은 문장, 두 목소리)
# instruct 는 영어 지시문(생성할 문장 자체는 한글 그대로) — 신나거나 화난 톤이 아니라
# 내레이션처럼 차분하고 약간 느리게. 2026-09-06 대표님 지시.
INSTRUCT = "Calm narration tone. Speak slowly and clearly, with no excitement or emotion."

_model = None


def _load():
    global _model
    if _model is None:
        import torch
        from qwen_tts import Qwen3TTSModel
        print("모델 로딩 중... (첫 실행이면 ~2GB 내려받음)", flush=True)
        _model = Qwen3TTSModel.from_pretrained(MODEL_ID, device_map="cpu", dtype=torch.float32)
    return _model


def speak(text: str, out_path: str, speaker: str = SPEAKER, instruct: str = INSTRUCT) -> str:
    """text 를 out_path(.wav) 로 만든다. 반환값은 out_path 그대로(체이닝용).
    instruct 는 영어로 톤을 지시하는 문장 — text(한글) 자체와는 별개다."""
    import soundfile as sf
    model = _load()
    wavs, sr = model.generate_custom_voice(text=text, language="Korean", speaker=speaker, instruct=instruct)
    sf.write(out_path, wavs[0], sr)
    return out_path


if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "안녕하세요, 테스트 음성입니다."
    out = speak(text, "tts_qwen_test.wav")
    print(f"만듦: {out} — 재생해서 확인하세요")
