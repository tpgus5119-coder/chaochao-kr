#!/usr/bin/env python3
"""남부 음원을 v-tts(VITS)로 만든다 — 남부 여성(SF)·남성(SM) 두 목소리.
VieNeu(자기회귀 LLM)와 달리 말 길이를 먼저 정하고 찍어내는 구조라 꼬리 덧말이 없다.
느린 버전도 시간 늘이기가 아니라 '천천히 말하게' 만들어(length_scale) 소리가 안 뭉갠다.
검사: ① 말 덩어리 절단 ② 한 음절 성조 방향 — 실패하면 noise_scale 을 바꿔 최대 4번 다시 만든다.
이미 있는 파일은 건너뛴다(검수 통과분을 덮지 않기 위해). 다시 만들려면 --force.
실행: <환경>/bin/python tools/gen_south_vtts.py [--voice sf|sm] [--limit N] [--force]"""
import json, pathlib, sys
import numpy as np, soundfile as sf

R = pathlib.Path(__file__).resolve().parent.parent
# 모델 자리 — **임시 폴더에 두지 않는다.** (2026-08-29)
# 전에는 대화 상자의 scratchpad 에 받아 뒀는데, 그 폴더는 상자가 닫히면 지워진다.
# 그래서 남부 소리를 더 못 굽는 상태로 몇 주를 보냈다. 이제 집 아래에 둔다.
#   코드: github.com/tronghieuit/v-tts  →  deployments/edge/inference.py
#   모델: huggingface.co/v-tts/v-tts-onnx  (첫 실행 때 스스로 받는다)
#   목소리: 0=NF(북부여) 1=SF(남부여) 2=NM1(북부남) 3=SM(남부남) 4=NM2
S = str(pathlib.Path.home() / 'vtts-edge')
sys.path.insert(0, str(R / 'tools'))
from vnsound import segments, f0_trend, tone_of, tone_ok, speech_span, cut

# 파이썬 3.12 호환 심 + 리눅스 전용 정규화기 우회 (우리 글은 이미 정규형이라 불필요)
import types, importlib.util
shim = types.ModuleType('imp')
def _find_module(name, path=None):
    spec = importlib.util.find_spec(name)
    loc = spec.submodule_search_locations[0] if spec.submodule_search_locations else spec.origin
    return (None, loc, None)
shim.find_module = _find_module
sys.modules['imp'] = shim
import viphoneme
viphoneme.TTSnorm = lambda t, **k: t

sys.path.insert(0, S)
from inference import VietnameTTSEdge

VOICE = {'sf': 1, 'sm': 3}          # SF=남부 여성, SM=남부 남성
voice = 'sf'
limit = None
for i, a in enumerate(sys.argv):
    if a == '--voice': voice = sys.argv[i + 1]
    if a == '--limit': limit = int(sys.argv[i + 1])
sid = VOICE[voice]

IDX = json.loads((R / 'data' / 'audio_index.json').read_text())
for sub in ('n', 'slow'):
    (R / f'audio/{voice}/{sub}').mkdir(parents=True, exist_ok=True)

tts = VietnameTTSEdge(model_dir=S + '/model')   # ~/vtts-edge/model — 안 지워지는 곳
SR = 24000
made = fail = healed = 0
bad = []
items = list(IDX.items())[:limit] if limit else list(IDX.items())
for i, (text, h) in enumerate(items):
    # 이미 있는 것은 건드리지 않는다. 다시 만들면 **검수를 통과한 음성이 검사 안 된 것으로 바뀐다.**
    # 일부러 다시 만들려면 --force 를 준다.
    # 2026-08-31: 여기서 slow 까지 함께 있어야 건너뛰게 해 두었는데, 느린 판을 폐지해서
    #   slow 는 하나도 없다 → 이 조건이 **한 번도 참이 되지 않아** 그냥 다시 돌리면
    #   이미 있는 1만 1천 개를 처음부터 다시 굽고 검수 통과분을 덮어썼다. n 만 본다.
    if '--force' not in sys.argv and (R / f'audio/{voice}/n/{h}.mp3').exists():
        continue
    tk = len(text.split())
    tone = tone_of(text) if tk == 1 else None
    # 북부 파일이 없을 수도 있다(안 쓰는 소리를 정리했다) — 없으면 기본값으로 간다
    _np = R / f'audio/f/n/{h}.mp3'
    try: ref = (speech_span(_np) if _np.exists() else 0) or 0.6
    except Exception: ref = 0.6
    best = None
    for attempt, ns in enumerate([0.667, 0.5, 0.8, 0.35]):
        audio, sr = tts.synthesize(text, speaker_id=sid, noise_scale=ns)
        y = np.asarray(audio, dtype='float32')
        y, _, fused = cut(y, sr, ref, tk)
        if fused: continue
        if best is None: best = y
        if tone and tone not in ('hỏi', 'ngã') and not tone_ok(tone, f0_trend(y, sr)):
            continue                       # 성조 방향이 어긋나면 다른 판으로
        best = y
        if attempt: healed += 1
        break
    else:
        fail += 1; bad.append(text)
    if best is None:
        # 네 번 다 걸렸다. 2026-08-31: 그냥 건너뛰면 **소리 파일에 구멍이 남고**,
        #   앱은 파일이 없으면 기기 내장 목소리로 읽어 버린다 — 골라 둔 남부 남자 대신
        #   딴 목소리가 튀어나온다. 그래서 마지막 판을 그대로라도 남긴다.
        #   ('tv' 같은 영어 약어에서 생긴다 — 성조 잣대를 댈 수 없는 말이다)
        audio, sr = tts.synthesize(text, speaker_id=sid, noise_scale=0.667)
        best = np.asarray(audio, dtype='float32')
        print('  잣대 미달이라 그대로 남김:', text, flush=True)
    sf.write(R / f'audio/{voice}/n/{h}.mp3', best, SR, format='MP3')
    # 느린 판은 더 만들지 않는다 — '느리게 듣기'를 없앴고 저장소가 1GB 에 닿았다
    #   (느린 판만 14,983개 161MB 였다. 2026-08-30)
    made += 1
    if made % 200 == 0: print(f'{made}/{len(items)} (성조 재시도 {healed} 미달 {fail})', flush=True)
print(f'끝 [{voice}] — 만듦 {made} / 재시도로 통과 {healed} / 성조 미달 {fail}', flush=True)
for t in bad[:30]: print('  미달:', t, flush=True)
