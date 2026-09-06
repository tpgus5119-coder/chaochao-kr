#!/usr/bin/env python3
"""남부 음원을 '듣고 받아 적어' 글자와 대조한다 (로컬 위스퍼 — 무료·무제한).
방식: 글자를 아는 상태에서 소리를 듣고, 받아 적은 것이 글자와 일치해야 통과.
등급: 일치(성조까지) / 글자 일치(성조 표기만 다름 — 성조는 F0 검사가 따로 담당) / 불일치.
한 음절짜리는 기계 받아쓰기도 흔들리는 게 알려져 있어(제미나이 실험으로 확인)
불일치가 곧 불량은 아니다 — 의심 목록으로 뽑아 사람이/재생성이 정리한다.
실행: <vieneu 환경>/bin/python tools/asr_south.py [--stride N] [--out 파일]"""
import json, pathlib, re, sys, unicodedata

R = pathlib.Path(__file__).resolve().parent.parent
IDX = json.loads((R / 'data' / 'audio_index.json').read_text())

def norm(s):
    s = s.lower().strip()
    s = re.sub(r'[.,!?;:"\'“”‘’…–—-]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

def bare(s):
    d = unicodedata.normalize('NFD', s)
    out = ''.join(c for c in d if not unicodedata.combining(c))
    return unicodedata.normalize('NFC', out).replace('đ', 'd')

stride = 1
out_path = None
args = sys.argv[1:]
for i, a in enumerate(args):
    if a == '--stride': stride = int(args[i + 1])
    if a == '--out': out_path = args[i + 1]

from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')

def hear(path):
    segs, _ = model.transcribe(str(path), language='vi', beam_size=5,
                               vad_filter=True, condition_on_previous_text=False)
    return norm(''.join(s.text for s in segs))

def ok(heard, want):
    return heard == want or bare(heard) == bare(want)

# 대조군 기법: 기계 귀 자체가 틀릴 수 있으므로, 남부가 틀리게 들리면
# 같은 글을 읽은 북부(맞다고 검증된 소리)도 들려본다.
# 북부는 맞는데 남부만 틀리면 → 진짜 의심. 둘 다 틀리면 → 기계 귀 한계(무시).
items = list(IDX.items())[::stride]
exact = weak = 0
sus = []
for i, (text, h) in enumerate(items):
    ps = R / f'audio/sf/n/{h}.mp3'
    pn = R / f'audio/f/n/{h}.mp3'
    if not ps.exists() or not pn.exists(): continue
    want = norm(text)
    hs = hear(ps)
    if ok(hs, want): exact += 1
    elif ok(hear(pn), want):
        sus.append({'text': text, 'heard': hs, 'h': h, 'tokens': len(text.split())})
    else:
        weak += 1
    if (i + 1) % 50 == 0:
        print(f'{i+1}/{len(items)} (통과 {exact} 의심 {len(sus)} 기계한계 {weak})', flush=True)

n = exact + weak + len(sus)
print(f'끝 — 검사 {n} / 통과 {exact} / 진짜 의심 {len(sus)} / 기계 귀 한계 {weak}', flush=True)
for b in sus:
    print(f"  의심: {b['text']}  →  들림 \"{b['heard']}\"", flush=True)
if out_path:
    pathlib.Path(out_path).write_text(json.dumps(sus, ensure_ascii=False, indent=1))
    print('의심 목록 저장:', out_path, flush=True)
