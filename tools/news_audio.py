#!/usr/bin/env python3
"""기사 세트에 새로 생긴 베트남어의 북부 음성을 만든다 — 깃허브 액션에서 돈다.

edge-tts 는 마이크로소프트 음성 서비스를 쓰는 무료 라이브러리다(가입·키 불필요).
그래서 개발자 노트북이 꺼져 있어도 깃허브 서버에서 그대로 돌아간다.
남부 음성(sf·sm)은 로컬 모델(v-tts)이 필요해 여기서 못 만든다.
edge-tts 의 베트남어 목소리는 북부 둘(여 HoaiMy · 남 NamMinh)뿐이고 남부 목소리는 없다.
그래서 기사 세트는 북부 남녀 두 목소리로 만들고, 남부로 듣는 사람에게는 앱이
북부 소리로 대신 낸다(play() 가 파일이 없으면 알아서 북부를 쓴다).
나중에 개발자 맥에서 tools/gen_south_vtts.py 를 돌리면 남부도 채워진다.

일주일 지난 기사 세트의 음성은 지운다 — 안 그러면 저장소가 매일 커진다.

사용: python3 tools/news_audio.py
"""
import asyncio, hashlib, json, pathlib, sys
import edge_tts

R = pathlib.Path(__file__).resolve().parent.parent
VOICES = {'f': 'vi-VN-HoaiMyNeural', 'm': 'vi-VN-NamMinhNeural'}
SLOW_RATE = '-35%'

key = lambda t: hashlib.sha1(t.encode()).hexdigest()[:12]

def wanted():
    """기사 세트의 단어와 문장 전부."""
    try:
        store = json.loads((R / 'data' / 'news_days.json').read_text())
    except Exception:
        return []
    out = []
    for d in store.get('days', []):
        out += [w['vi'] for w in d.get('words', [])]
        out += [l['vi'] for l in d.get('dialog', {}).get('lines', [])]
    return sorted(set(t for t in out if t))

async def one(text, voice, path, slow):
    kw = {'rate': SLOW_RATE} if slow else {}
    await edge_tts.Communicate(text, voice, **kw).save(str(path))

def sweep(mine):
    """일주일 지나 사라진 **기사 세트 음성만** 지운다.
       커리큘럼 음성은 절대 건드리지 않는다 — 그래서 '내가 만든 것' 목록을 따로 들고 다닌다
       (audio_index 만 보고 지우면 app.js 안에 있는 문법 예문 음성까지 날아간다)."""
    live = set(wanted())
    gone = 0
    for text in list(mine):
        if text in live:
            continue
        h = mine.pop(text)
        for v in VOICES:
            for kind in ('n', 'slow'):
                p = R / 'audio' / v / kind / f'{h}.mp3'
                if p.exists(): p.unlink(); gone += 1
    return gone

async def main():
    idx_p = R / 'data' / 'audio_index.json'
    idx = json.loads(idx_p.read_text()) if idx_p.exists() else {}
    mine_p = R / 'data' / 'news_audio.json'          # 이 스크립트가 만든 것만 적어 둔다
    mine = json.loads(mine_p.read_text()) if mine_p.exists() else {}
    made = skip = fail = 0
    for text in wanted():
        h = idx.get(text) or key(text)
        need = []
        for v, name in VOICES.items():
            # 느린 판은 만들지 않는다 (2026-08-31). 다른 도구는 진작에 없앴는데
            #   여기만 남아 매일 새 느린 파일을 쌓고 있었다(354개까지 늘었다).
            #   앱은 느린 파일이 없으면 보통 소리를 늘려 튼다 — 성조는 안 뭉개진다.
            for kind, slow in (('n', False),):
                p = R / 'audio' / v / kind / f'{h}.mp3'
                if p.exists():
                    continue
                p.parent.mkdir(parents=True, exist_ok=True)
                need.append((name, p, slow))
        if not need:
            idx[text] = h
            skip += 1
            continue
        try:
            for name, p, slow in need:
                await one(text, name, p, slow)
            idx[text] = h
            mine[text] = h                            # 우리가 만든 것
            made += 1
        except Exception as e:
            fail += 1
            print(f'실패 {text}: {e}', flush=True)
    gone = sweep(mine)                                # 사라진 기사 세트의 음성 치우기
    idx_p.write_text(json.dumps(idx, ensure_ascii=False))
    mine_p.write_text(json.dumps(mine, ensure_ascii=False))
    print(f'음성 — 새로 {made} · 이미 있음 {skip} · 실패 {fail} · 지난 기사 음성 {gone}개 치움')

if __name__ == '__main__':
    asyncio.run(main())
