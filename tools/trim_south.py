#!/usr/bin/env python3
"""남부 음원 덧말 전수 검사·수리 — 북부 길이를 잣대로.
로컬 TTS가 단어 뒤에 헛말을 덧붙이는 일이 있다. 같은 글을 읽은 북부(edge-tts)
소리의 말 길이보다 1.45배+0.3초 넘게 길면 덧말로 보고 자른다.
덧말이 본말에 붙어 한 덩어리면 다시 굽는다(최대 5회) — 한 음절 단어는
성조 방향 검사까지 통과해야 채택한다. 너무 짧은(앞서 과하게 잘린) 파일도 다시 굽는다.
느리게 버전은 확정된 소리에서 다시 만든다.
실행: <vieneu 환경>/bin/python tools/trim_south.py
"""
import json, pathlib, sys
import numpy as np, soundfile as sf, librosa
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vnsound import mono, segments, speech_span, cut, f0_trend, tone_of, tone_ok

R = pathlib.Path(__file__).resolve().parent.parent
IDX = json.loads((R/'data/audio_index.json').read_text())

tts = None
def gen24(text):
    global tts
    if tts is None:
        from vieneu import Vieneu
        tts = Vieneu(mode="v3turbo")
    wav = tts.infer(text, voice="Thùy Dung", temperature=0.3)
    tmp = R/'audio/sf/_tmp.wav'
    tts.save(wav, str(tmp))
    y, sr = sf.read(tmp)
    return librosa.resample(mono(y).astype('float32'), orig_sr=sr, target_sr=24000)

def write(h, y):
    sf.write(R/f'audio/sf/n/{h}.mp3', y, 24000, format='MP3')
    sf.write(R/f'audio/sf/slow/{h}.mp3', librosa.effects.time_stretch(y, rate=0.72), 24000, format='MP3')

kept = trimmed = regen_ok = regen_fail = 0
fails = []
items = list(IDX.items())
for i, (text, h) in enumerate(items):
    p = R/f'audio/sf/n/{h}.mp3'
    refp = R/f'audio/f/n/{h}.mp3'
    if not p.exists() or not refp.exists(): continue
    ref = speech_span(refp)
    if not ref: continue
    tk = len(text.split())
    y, sr = sf.read(p); y = mono(y)
    segs = segments(y, sr)
    span = (segs[-1][1]-segs[0][0])/sr if segs else 0
    y2, did_cut, fused = cut(y, sr, ref, tk)
    too_short = tk > 1 and span < ref*0.45 - 0.05   # 앞선 다듬기가 과하게 잘랐던 흔적
    if not fused and not too_short:
        if did_cut: write(h, y2); trimmed += 1
        else: kept += 1
    else:
        tone = tone_of(text) if tk == 1 else None
        best = None
        for _ in range(5):
            c = gen24(text)
            c2, _, fz = cut(c, 24000, ref, tk)
            if fz: continue
            sp = 0
            sg = segments(c2, 24000)
            if sg: sp = (sg[-1][1]-sg[0][0])/24000
            if sp < (0.12 if tk == 1 else ref*0.45): continue
            if tone and not tone_ok(tone, f0_trend(c2, 24000)): continue
            best = c2; break
        if best is not None: write(h, best); regen_ok += 1
        else: regen_fail += 1; fails.append(text)
    if (i+1) % 100 == 0:
        print(f'{i+1}/{len(items)} (그대로 {kept} 자름 {trimmed} 재생성 {regen_ok} 실패 {regen_fail})', flush=True)

(R/'audio/sf/_tmp.wav').unlink(missing_ok=True)
print(f'끝 — 그대로 {kept} / 덧말 자름 {trimmed} / 다시 구움 {regen_ok} / 실패 {regen_fail}', flush=True)
for t in fails: print('  실패:', t, flush=True)
