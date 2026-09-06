#!/usr/bin/env python3
"""프롬프트를 고친 그림을 **제자리에서** 다시 굽는다 (지우지 않는다).
지우고 새로 구우면 다 구워질 때까지 앱에 그림이 안 보인다 — 그래서 덮어쓴다.
사용: python3 tools/redo_images.py <이름목록파일> [--limit N]"""
import base64, io, json, pathlib, re, sys, urllib.request, zlib
from PIL import Image
R = pathlib.Path(__file__).resolve().parent.parent
API = 'http://127.0.0.1:7860/sdapi/v1/txt2img'
want = [l.strip() for l in pathlib.Path(sys.argv[1]).read_text().splitlines() if l.strip()]
limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 10**9
doc, cur = {}, None
for line in (R / 'docs' / 'image-prompts.md').read_text().splitlines():
    m = re.match(r'\*\*([\w-]+)\.webp\*\*', line)
    if m: cur = m.group(1)
    elif cur and line.startswith('> '): doc[cur] = line[2:].strip(); cur = None
done = fail = 0
for n in want:
    if done >= limit: break
    p = doc.get(n)
    if not p: continue
    try:
        body = json.dumps({'prompt': p, 'steps': 4, 'cfg_scale': 1, 'width': 640, 'height': 640,
                           'seed': zlib.crc32(n.encode()) % 2_000_000_000}).encode()
        r = json.loads(urllib.request.urlopen(
            urllib.request.Request(API, data=body, headers={'Content-Type': 'application/json'}),
            timeout=600).read())
        im = Image.open(io.BytesIO(base64.b64decode(r['images'][0]))).convert('RGB')
        im.save(R / 'img' / f'{n}.webp', 'WEBP', quality=82)     # 제자리 덮어쓰기
        done += 1
        if done % 20 == 0: print(f'{done}장', flush=True)
    except Exception as e:
        fail += 1; print(f'실패 {n}: {e}', flush=True)
print(f'다시 구움 {done}장 · 실패 {fail}')
