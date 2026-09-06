"""남부 음원 공용 도구 — 말 덩어리 찾기, 북부 길이 잣대 절단, 성조 방향 측정.
trim_south.py 와 qa_south.py 가 같이 쓴다."""
import unicodedata
import numpy as np, soundfile as sf

MARKS = {'̀': 'huyền', '́': 'sắc', '̉': 'hỏi', '̃': 'ngã', '̣': 'nặng'}

def tone_of(syl):
    for ch in unicodedata.normalize('NFD', syl):
        if ch in MARKS: return MARKS[ch]
    return 'ngang'

def mono(y):
    return y.mean(axis=1) if getattr(y, 'ndim', 1) > 1 else y

def segments(y, sr, thresh=0.012, merge_gap=0.15):
    """소리에서 말 덩어리 [시작,끝] 목록. 0.15초 미만으로 쉰 것은 한 덩어리."""
    win = int(sr * 0.02)
    if len(y) < win * 3: return []
    env = np.array([np.sqrt((y[i:i+win]**2).mean()) for i in range(0, len(y)-win, win)])
    segs, start = [], None
    for i, v in enumerate(env > thresh):
        if v and start is None: start = i
        if not v and start is not None: segs.append([start*win, i*win]); start = None
    if start is not None: segs.append([start*win, len(y)])
    merged = []
    for s, e in segs:
        if merged and s - merged[-1][1] < merge_gap*sr: merged[-1][1] = e
        else: merged.append([s, e])
    return merged

def speech_span(path):
    """파일 속 말의 길이(초) — 첫 덩어리 시작부터 마지막 덩어리 끝까지."""
    y, sr = sf.read(path)
    segs = segments(mono(y), sr)
    return (segs[-1][1] - segs[0][0]) / sr if segs else None

def cut(y, sr, ref, tokens=2):
    """뒤 덧말을 자른다. 단어(3음절 이하)는 '첫 소리 덩어리 하나'만 남긴다 —
    1음절은 0.06초, 2~3음절은 0.18초 넘게 쉬면 그 뒤는 전부 덧말이다
    (베트남어 낱말 안에는 그만한 침묵이 없다. 끝 파열음도 불파음이라 안전).
    문장은 북부 말 길이 ref(초)의 1.45배+0.3초 잣대로 그 안까지만 남긴다.
    돌려주기: (자른 소리, 잘랐는가, 덧말이 본말에 붙어 못 자르는가=다시 구울 것)"""
    gap = 0.06 if tokens == 1 else 0.18 if tokens <= 3 else 0.15
    segs = segments(y, sr, merge_gap=gap)
    if not segs: return y, False, False
    limit = 0.85 if tokens == 1 else (ref * 1.6 + 0.35 if tokens <= 3 else ref * 1.45 + 0.30)
    if (segs[0][1] - segs[0][0]) / sr > limit:
        return y, False, True                        # 첫 덩어리부터 초과 — 다시 구워야
    keep = segs[0][1]
    if tokens > 3:
        for s, e in segs[1:]:
            if (e - segs[0][0]) / sr > limit: break
            keep = e
    start = max(0, segs[0][0] - int(.06 * sr))
    end = min(len(y), keep + int(.10 * sr))
    if end >= len(y) - int(.05 * sr) and start <= int(.05 * sr):
        return y, False, False                       # 자를 게 없다
    return y[start:end].astype('float32'), True, False

def f0_trend(y, sr):
    """음높이 흐름: 끝이 처음보다 몇 반음 높은가. 성조 방향 검사용."""
    y = mono(y)
    win, hop = int(sr*.04), int(sr*.01)
    lo, hi = int(sr/400), int(sr/80)
    v = []
    for i in range(0, len(y)-win, hop):
        fr = y[i:i+win] * np.hanning(win)
        if np.sqrt((fr**2).mean()) < 0.015: continue
        ac = np.correlate(fr, fr, 'full')[win-1:]
        seg = ac[lo:hi]
        if len(seg) == 0 or ac[0] <= 0: continue
        lag = lo + int(np.argmax(seg))
        if seg.max()/ac[0] > 0.35: v.append(sr/lag)
    if len(v) < 6: return None
    a = np.median(v[:max(2, len(v)//3)]); b = np.median(v[-max(2, len(v)//3):])
    return 12*np.log2(b/a)

def tone_ok(tone, st):
    if st is None: return False
    return {'sắc': st >= 1.0, 'huyền': st <= -0.3, 'nặng': st <= 0.0,
            'ngang': -2.5 <= st <= 2.5}.get(tone, True)   # hỏi·ngã 는 방향 단정 불가
