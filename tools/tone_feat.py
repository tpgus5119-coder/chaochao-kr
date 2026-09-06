#!/usr/bin/env python3
"""성조 특징을 F0 말고도 뽑는다.
근거: 하노이 베트남어는 성조와 **발성(phonation)** 이 붙어 있다 —
ngã 는 모음 뒷부분이 삐걱거리고(creaky), nặng 은 낮게 떨어지며 삐걱거리고,
hỏi 는 성문이 더 조여진다. 연구들이 "높이보다 삐걱거림·숨소리가 주된 단서"라고 한다.
삐걱거리는 구간에서는 **음높이 측정이 아예 안 된다** — 그 '구멍'이야말로 신호다.
그래서 F0 곡선만 쓰던 것을 버리고 아래를 함께 잰다.
  · gapmid  가운데 60% 구간에서 음높이를 못 잰 비율 (삐걱거림의 자국)
  · jit     이웃 프레임 사이 F0 흔들림 (불규칙한 성대 진동)
  · en      에너지 곡선 20점 (로그 + 정규화)
  · edrop   끝 에너지 / 최대 에너지 (nặng 은 뚝 끊긴다)
  · sec     소리 난 길이
"""
import json, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
from tone_corpus import decode, contour, normalize, clean, resample, FMIN, FMAX

R = pathlib.Path(__file__).resolve().parent.parent

def feats(path):
    x, rate = decode(path)
    if x.size < rate*0.05: return None
    hop, win = round(rate*0.010), round(rate*0.045)
    hz = contour(x, rate)
    c = resample(clean(normalize(hz)))
    if not c: return None
    # 소리가 난 구간(앞뒤 무음 잘라내기) 안에서만 본다
    idx = [i for i,v in enumerate(hz) if v]
    if len(idx) < 6: return None
    a, b = idx[0], idx[-1]
    span = hz[a:b+1]
    n = len(span)
    lo, hi = int(n*0.2), int(n*0.8)
    mid = span[lo:hi] or span
    gapmid = sum(1 for v in mid if not v)/max(1,len(mid))
    v = [h for h in span if h]
    jit = float(np.mean(np.abs(np.diff(v))/np.array(v[:-1]))) if len(v) > 2 else 0.0
    # 에너지
    en = []
    for s in range(0, max(0, len(x)-win), hop):
        seg = x[s:s+win]; en.append(float(np.sqrt(np.mean(seg*seg))+1e-9))
    en = en[a:b+1] if len(en) > b else en
    if len(en) < 4: return None
    le = np.log(np.array(en))
    le = (le - le.mean())/(le.std()+1e-9)                       # 로그 + 정규화 (연구 권고)
    enc = list(np.interp(np.linspace(0,1,20), np.linspace(0,1,len(le)), le))
    edrop = float(np.mean(le[-max(1,len(le)//6):]) - le.max())
    return {'curve':[round(t,3) for t in c], 'en':[round(float(t),3) for t in enc],
            'gapmid':round(gapmid,3), 'jit':round(jit,4), 'edrop':round(edrop,3),
            'sec':round(len(v)*0.010,3)}

if __name__ == '__main__':
    from tone import word_tones
    idx = json.loads((R/'data/audio_index.json').read_text())
    d = json.loads((R/'data/days.json').read_text())
    words = {}
    for day in [*d.get('prep',[]), *d['days']]:
        for w in day.get('words',[]):
            if len(w['vi'].split()) != 1: continue
            t = word_tones(w['vi'])
            if len(t) == 1: words[w['vi']] = t[0]['name'] if isinstance(t[0],dict) else t[0]
    rows = []
    for vi, tone in sorted(words.items()):
        h = idx.get(vi)
        if not h: continue
        for v in ('f','m'):
            p = R/'audio'/v/'n'/f'{h}.mp3'
            if not p.exists(): continue
            f = feats(p)
            if f: f.update(vi=vi, tone=tone, voice=v); rows.append(f)
        if len(rows) % 200 < 2: print(f'  {len(rows)}…', file=sys.stderr, flush=True)
    (R/'data/_tone_feats.json').write_text(json.dumps(rows))
    print(f'{len(rows)}개 → data/_tone_feats.json', file=sys.stderr)
