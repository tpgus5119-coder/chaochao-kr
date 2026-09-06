#!/usr/bin/env python3
"""남부 음원 자동 검수 + 자가 치유.
모든 한 음절 단어의 음높이 방향을 물리적으로 재서, 성조 기대와 어긋나면
통과할 때까지 다시 굽는다(최대 5회). 다시 구운 소리도 반드시 덧말 절단(북부 길이
잣대)을 거쳐 저장한다 — 전에는 이 단계가 없어서 치유 파일에 헛말이 남았다.
기준(남부 실측 보정): sắc ≥ +1.0 반음 / huyền ≤ -0.3 / nặng ≤ 0 / ngang |±2.5|
hỏi·ngã는 굴곡형이라 방향 단정이 불가능해 기록만 한다.
실행: <vieneu 환경>/bin/python tools/qa_south.py
"""
import json, pathlib, sys
import numpy as np, soundfile as sf, librosa
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vnsound import mono, cut, speech_span, f0_trend, tone_of, tone_ok

R = pathlib.Path(__file__).resolve().parent.parent
IDX = json.loads((R/'data/audio_index.json').read_text())

def f0_file(path):
    y, sr = sf.read(path)
    return f0_trend(mono(y), sr)

words = [(t, h) for t, h in IDX.items() if len(t.split()) == 1]
print(f'한 음절 단어 {len(words)}개 검수 시작', flush=True)

tts = None
def gen(text):
    global tts
    if tts is None:
        from vieneu import Vieneu
        tts = Vieneu(mode="v3turbo")
    return tts.infer(text, voice="Thùy Dung", temperature=0.3)

passed = healed = failed = 0
loglines = []
for i, (t, h) in enumerate(words):
    tone = tone_of(t)
    p = R/f'audio/sf/n/{h}.mp3'
    if not p.exists(): continue
    st = f0_file(p)
    if tone_ok(tone, st):
        passed += 1
    else:
        ref = speech_span(R/f'audio/f/n/{h}.mp3') or 0.6
        good = False
        for attempt in range(5):
            wav = gen(t)
            tmp = R/'audio/sf/_qa.wav'
            tts.save(wav, str(tmp))
            y, sr = sf.read(tmp)
            y24 = librosa.resample(mono(y).astype('float32'), orig_sr=sr, target_sr=24000)
            y24, _, fused = cut(y24, 24000, ref, 1)   # 치유 파일도 덧말을 자르고 저장한다
            if fused: continue
            st2 = f0_trend(y24, 24000)
            if tone_ok(tone, st2):
                sf.write(p, y24, 24000, format='MP3')
                slow = librosa.effects.time_stretch(y24, rate=0.72)
                sf.write(R/f'audio/sf/slow/{h}.mp3', slow, 24000, format='MP3')
                healed += 1; good = True
                loglines.append(f'치유: {t} ({tone}) {st} → {st2:+.1f}')
                break
        if not good:
            failed += 1
            loglines.append(f'미달: {t} ({tone}) st={st}')
    if (i+1) % 40 == 0: print(f'{i+1}/{len(words)} (통과 {passed} 치유 {healed} 미달 {failed})', flush=True)

(R/'audio/sf/_qa.wav').unlink(missing_ok=True)
print(f'끝 — 통과 {passed} / 다시 구워 통과 {healed} / 미달 {failed}', flush=True)
for l in loglines: print(' ', l, flush=True)
