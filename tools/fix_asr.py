#!/usr/bin/env python3
"""받아쓰기 검사에서 심각 판정(asr_bad.json)된 남부 음원을 다시 굽는다.
채택 조건(전부 통과해야 교체): ① 덧말 절단 통과 ② 한 음절이면 성조 방향 통과
③ 위스퍼가 부호 빼고 같게 받아 적거나 닮음 0.65 이상.
못 만들면 원본을 남긴다(성조 검증된 파일을 더 나쁜 걸로 바꾸지 않기 위해).
실행: <vieneu 환경>/bin/python tools/fix_asr.py"""
import difflib, json, pathlib, re, sys, unicodedata
import soundfile as sf, librosa
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from vnsound import mono, cut, speech_span, f0_trend, tone_of, tone_ok

R = pathlib.Path(__file__).resolve().parent.parent
BAD = json.loads((R / 'tools' / 'asr_bad.json').read_text())

def norm(s):
    s = s.lower().strip()
    s = re.sub(r'[.,!?;:"\'“”‘’…–—-]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()
def bare(s):
    d = unicodedata.normalize('NFD', s)
    return unicodedata.normalize('NFC', ''.join(c for c in d if not unicodedata.combining(c))).replace('đ', 'd')

from faster_whisper import WhisperModel
asr = WhisperModel('small', device='cpu', compute_type='int8')
def hear(path):
    segs, _ = asr.transcribe(str(path), language='vi', beam_size=5,
                             vad_filter=True, condition_on_previous_text=False)
    return norm(''.join(s.text for s in segs))

from vieneu import Vieneu
tts = Vieneu(mode="v3turbo")

fixed = kept = 0
for i, b in enumerate(BAD):
    text, h = b['text'], b['h']
    tk = len(text.split())
    tone = tone_of(text) if tk == 1 else None
    ref = speech_span(R / f'audio/f/n/{h}.mp3') or 0.6
    want = norm(text)
    ok_done = False
    for attempt in range(4):
        voice = 'Mỹ Duyên' if attempt >= 2 else 'Thùy Dung'
        try:
            wav = tts.infer(text, voice=voice, temperature=0.3)
            tmp = R / 'audio/sf/_fx.wav'
            tts.save(wav, str(tmp))
            y, sr = sf.read(tmp)
            y24 = librosa.resample(mono(y).astype('float32'), orig_sr=sr, target_sr=24000)
            y24, _, fused = cut(y24, 24000, ref, tk)
            if fused: continue
            if tone and not tone_ok(tone, f0_trend(y24, 24000)): continue
            cand = R / 'audio/sf/_fx.mp3'
            sf.write(cand, y24, 24000, format='MP3')
            heard = hear(cand)
            ratio = difflib.SequenceMatcher(None, bare(want), bare(heard)).ratio()
            if bare(heard) == bare(want) or ratio >= 0.65:
                sf.write(R / f'audio/sf/n/{h}.mp3', y24, 24000, format='MP3')
                slow = librosa.effects.time_stretch(y24, rate=0.72)
                sf.write(R / f'audio/sf/slow/{h}.mp3', slow, 24000, format='MP3')
                print(f'수리: {text}  ({voice}, 들림 "{heard}", 닮음 {ratio:.2f})', flush=True)
                fixed += 1; ok_done = True
                break
        except Exception as e:
            print(f'오류 {text}: {e}', flush=True)
    if not ok_done:
        kept += 1
        print(f'보류: {text} — 4번 다시 구워도 기준 미달, 원본 유지', flush=True)
    if (i + 1) % 10 == 0: print(f'--- {i+1}/{len(BAD)} (수리 {fixed} 보류 {kept})', flush=True)

for f in ['_fx.wav', '_fx.mp3']: (R / 'audio/sf' / f).unlink(missing_ok=True)
print(f'끝 — 수리 {fixed} / 원본 유지 {kept}', flush=True)
