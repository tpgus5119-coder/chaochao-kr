#!/usr/bin/env python3
"""원어민 음성에서 성조별 음높이 곡선을 뽑아 본다.
pitch.js 와 **같은 알고리즘**(YIN + 중앙값 반음 정규화 + 20점 리샘플)을 파이썬으로 옮겼다 —
브라우저에서 재는 것과 다른 잣대로 재면 결론이 쓸모없다.
쓰임: 성조마다 곡선 모양이 정말 다른지, 그래서 '어느 성조로 들리는지' 맞힐 수 있는지 확인."""
import json, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np

R = pathlib.Path(__file__).resolve().parent.parent
FMIN, FMAX = 60, 500

def decode(path, rate=16000):
    p = subprocess.run(['ffmpeg','-v','quiet','-i',str(path),'-f','f32le','-ac','1','-ar',str(rate),'-'],
                       capture_output=True)
    return np.frombuffer(p.stdout, dtype=np.float32), rate

def yin(buf, rate, thr=0.12):
    tmin, tmax = int(rate/FMAX), int(rate/FMIN)
    n = len(buf); half = min(tmax, n//2)
    if half <= tmin: return 0.0
    d = np.empty(half+1, dtype=np.float64); d[0] = 0
    for tau in range(1, half+1):
        x = buf[:n-tau] - buf[tau:n]
        d[tau] = float(np.dot(x, x))
    cm = np.ones(half+1); run = 0.0
    for tau in range(1, half+1):
        run += d[tau]
        cm[tau] = d[tau]*tau/run if run else 1.0
    tau = -1
    for t in range(tmin, half+1):
        if cm[t] < thr:
            while t+1 <= half and cm[t+1] < cm[t]: t += 1
            tau = t; break
    if tau < 0:
        seg = cm[tmin:half+1]
        if seg.size == 0 or seg.min() > 0.55: return 0.0
        tau = tmin + int(seg.argmin())
    a = cm[tau-1] if tau-1 >= 0 else cm[tau]; b = cm[tau]; c = cm[tau+1] if tau+1 <= half else cm[tau]
    den = a + c - 2*b
    shift = (a-c)/(2*den) if den else 0
    return rate/(tau+shift)

def contour(x, rate):
    win, hop = round(rate*0.045), round(rate*0.010)
    peak = float(np.abs(x).max()) if x.size else 0
    floor = max(0.012, peak*0.10)
    out = []
    for s in range(0, max(0, len(x)-win), hop):
        seg = x[s:s+win]
        rms = float(np.sqrt(np.mean(seg*seg)))
        out.append(None if rms < floor else (yin(seg, rate) or None))
    return out

def normalize(hz):
    v = sorted(h for h in hz if h and FMIN < h < FMAX)
    if len(v) < 4: return None
    med = v[len(v)//2]
    return [12*np.log2(h/med) if (h and FMIN < h < FMAX) else None for h in hz]

def clean(st):
    if not st: return None
    idx = [i for i,v in enumerate(st) if v is not None]
    if len(idx) < 4: return None
    cut = st[idx[0]:idx[-1]+1]
    for i in range(1, len(cut)-1):
        p, q, c = cut[i-1], cut[i+1], cut[i]
        if c is None or p is None or q is None: continue
        if abs(c-p) > 10 and abs(c-q) > 10: cut[i] = (p+q)/2
    sm = list(cut)
    for i in range(1, len(cut)-1):
        w = [v for v in (cut[i-1], cut[i], cut[i+1]) if v is not None]
        if w: sm[i] = sum(w)/len(w)
    return sm

def resample(st, n=20):
    if not st: return None
    pts = [(i/(len(st)-1), v) for i,v in enumerate(st) if v is not None]
    if len(pts) < 4: return None
    ts = np.array([p[0] for p in pts]); vs = np.array([p[1] for p in pts])
    return list(np.interp(np.linspace(0,1,n), ts, vs))

def curve_of(path):
    x, rate = decode(path)
    if x.size < rate*0.05: return None, 0
    hz = contour(x, rate)
    c = resample(clean(normalize(hz)))
    sec = sum(1 for h in hz if h) * 0.010
    return c, sec

if __name__ == '__main__':
    from tone import word_tones
    idx = json.loads((R/'data/audio_index.json').read_text())
    d = json.loads((R/'data/days.json').read_text())
    words = {}
    for day in [*d.get('prep',[]), *d['days']]:
        for w in day.get('words',[]):
            vi = w['vi']
            if len(vi.split()) != 1: continue          # 한 음절짜리 낱말만
            t = word_tones(vi)
            if len(t) == 1: words[vi] = t[0]
    print(f'한 음절 낱말 {len(words)}개', file=sys.stderr)
    voices = sys.argv[1:] or ['f','m','sf','sm']
    rows = []
    for vi, tone in sorted(words.items()):
        h = idx.get(vi)
        if not h: continue
        for v in voices:
            p = R/'audio'/v/'n'/f'{h}.mp3'
            if not p.exists(): continue
            c, sec = curve_of(p)
            if c: rows.append({'vi':vi,'tone':tone,'voice':v,'sec':round(sec,3),
                               'curve':[round(x,3) for x in c]})
        if len(rows) % 100 < 4: print(f'  {len(rows)}개…', file=sys.stderr)
    (R/'data/_tone_curves.json').write_text(json.dumps(rows))
    print(f'곡선 {len(rows)}개 뽑음 → data/_tone_curves.json', file=sys.stderr)
