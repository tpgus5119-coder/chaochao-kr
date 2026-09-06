#!/usr/bin/env python3
"""남부(호찌민) 음원을 이 컴퓨터에서 직접 만든다 — VieNeu-TTS (Apache 2.0, 무료·무제한).
FPT.AI가 개인 서비스를 접어서(2026-07-06) 로컬 생성으로 전환했다.

실행: 별도 파이썬 환경이 필요하다 (uv venv --python 3.12 → pip install vieneu librosa)
      <환경>/bin/python tools/gen_south_local.py
목소리: Thùy Dung (남부 여성). 온도 0.3 — 높이면 성조 높낮이가 판마다 흔들린다(실측).
느리게: 0.72배 시간 늘이기(음높이 유지). 출력은 24kHz mp3로 줄여 저장한다.
"""
import json, pathlib, sys

R = pathlib.Path(__file__).resolve().parent.parent
IDX = json.loads((R/'data/audio_index.json').read_text())
for sub in ['n', 'slow']: (R/f'audio/sf/{sub}').mkdir(parents=True, exist_ok=True)

todo = [(t, h) for t, h in IDX.items()
        if not ((R/f'audio/sf/n/{h}.mp3').exists() and (R/f'audio/sf/slow/{h}.mp3').exists())]
print(f'전체 {len(IDX)} / 남은 {len(todo)}', flush=True)
if not todo: sys.exit(0)

import numpy as np, soundfile as sf, librosa
from vieneu import Vieneu
tts = Vieneu(mode="v3turbo")

for i, (text, h) in enumerate(todo):
    try:
        wav = tts.infer(text, voice="Thùy Dung", temperature=0.3)
        # save가 배열을 주지 않으므로 임시 wav를 거친다
        tmp = R/'audio/sf/_tmp.wav'
        tts.save(wav, str(tmp))
        y, sr = sf.read(tmp)
        if y.ndim > 1: y = y.mean(axis=1)
        y24 = librosa.resample(y.astype('float32'), orig_sr=sr, target_sr=24000)
        sf.write(R/f'audio/sf/n/{h}.mp3', y24, 24000, format='MP3')
        slow = librosa.effects.time_stretch(y24, rate=0.72)
        sf.write(R/f'audio/sf/slow/{h}.mp3', slow, 24000, format='MP3')
    except Exception as e:
        print(f'실패 {text[:25]}: {e}', flush=True)
    if (i+1) % 25 == 0: print(f'{i+1}/{len(todo)}', flush=True)
(R/'audio/sf/_tmp.wav').unlink(missing_ok=True)
print('끝', flush=True)
