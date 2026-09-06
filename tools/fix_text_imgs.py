# -*- coding: utf-8 -*-
"""그림에 박힌 **깨진 글자**를 지운다 — 다시 굽고 OCR로 확인해 깨끗한 판만 채택.

이 도구가 한 번 틀렸던 것 (2026-08-29 고침):
  전 판은 긍정 프롬프트 뒤에 "no signage, no labels, no writing of any kind"를
  **덧붙였다.** 확산 모델은 긍정 쪽 부정어를 못 알아듣는다 — 오히려 그 낱말이
  불려 나온다. 예전에 "손을 감춰라"가 손을 불러낸 것과 같은 사고다.
  이제 부정어는 **negative_prompt 칸**으로 보내고, 긍정 쪽에서는 **지운다.**

지우지 않는 것 (사용자 원칙: "좋은 이미지는 절대 수정하지 마라"):
  경찰서의 POLICE, 은행의 BANK 처럼 **뜻이 있는 간판**은 맞는 그림이다.
  이 도구는 부르는 대로만 다시 굽는다 — 무엇이 깨졌는지는 img_audit 이 가린다.

씨앗을 바꿔 가며 최대 5번. 다 실패하면 **글자가 가장 적은 판**을 채택하되,
원본보다 나쁘면 원본을 그대로 둔다.

사용: python3 tools/fix_text_imgs.py 이름1,이름2,...
      python3 tools/fix_text_imgs.py --file data/_img_broken.json
"""
import json, io, base64, zlib, urllib.request, re, pathlib, subprocess, sys
from PIL import Image

R = pathlib.Path(__file__).resolve().parent.parent
IMG = R / 'img'
API = 'http://127.0.0.1:7860/sdapi/v1/txt2img'
OCR = str(R / 'tools' / 'bin' / 'ocr')
TMP = pathlib.Path('/tmp/txtfix'); TMP.mkdir(exist_ok=True)

# 부정어는 여기로만 간다. 긍정 프롬프트에 넣으면 반대로 불러온다.
NEG = ('text, letters, words, writing, signage, labels, captions, watermark, '
       'logo, numbers, alphabet, typography, subtitles')
# 전 판이 긍정 프롬프트에 심어 둔 부정어 — 있으면 뽑아낸다.
STRIP = re.compile(r',\s*(no signage|no labels|no writing of any kind|blank surfaces|'
                   r'no text|no letters)', re.I)

pairs, name = {}, None
for line in (R / 'docs' / 'image-prompts.md').read_text().splitlines():
    m = re.match(r'\*\*([\w-]+)\.webp\*\*', line)
    if m:
        name = m.group(1)
    elif name and line.startswith('> '):
        pairs[name] = line[2:].strip(); name = None


def ocr_text(p):
    r = subprocess.run([OCR, str(p)], capture_output=True, text=True, timeout=90)
    if r.returncode != 0:
        raise RuntimeError('OCR 실행 실패 — 조용히 통과시키면 가짜 합격이 된다: '
                           + r.stderr[:100])
    # tools/ocr.swift 는 "=== 경로" 머리줄 뒤에 맨글을 낸다.
    return ' '.join(ln.strip() for ln in r.stdout.splitlines()
                    if ln.strip() and not ln.startswith('==='))


def bake(prompt, seed):
    body = json.dumps({'prompt': prompt, 'negative_prompt': NEG, 'steps': 4,
                       'cfg_scale': 1, 'width': 640, 'height': 640,
                       'seed': seed}).encode()
    r = json.loads(urllib.request.urlopen(
        urllib.request.Request(API, data=body,
                               headers={'Content-Type': 'application/json'}),
        timeout=600).read())
    return Image.open(io.BytesIO(base64.b64decode(r['images'][0]))).convert('RGB')


def main():
    a = sys.argv[1:]
    if a[:1] == ['--file']:
        names = [n.removesuffix('.webp') for n in json.load(open(R / a[1]))]
    else:
        names = a[0].split(',')

    fixed = kept = 0
    for i, n in enumerate(names, 1):
        pr = pairs.get(n)
        if not pr:
            print(f'  ? 그림말 없음 {n}', flush=True); continue
        pr = STRIP.sub('', pr)                      # 긍정 쪽 부정어를 뽑아낸다
        was = len(ocr_text(IMG / f'{n}.webp')) if (IMG / f'{n}.webp').exists() else 999
        best = None
        for t in range(5):
            seed = (zlib.crc32(n.encode()) + t * 7919 + 4241) % 2_000_000_000
            try:
                im = bake(pr, seed)
            except Exception as e:
                print(f'  ! {n} 굽기 실패 {e}', flush=True); break
            p = TMP / f'{n}.webp'
            im.save(p, 'WEBP', quality=82, method=6)
            got = len(ocr_text(p))
            if best is None or got < best[0]:
                best = (got, im.copy())
            if got == 0:
                break
        if best is None:
            continue
        if best[0] < was:
            best[1].save(IMG / f'{n}.webp', 'WEBP', quality=82, method=6)
            fixed += 1
            print(f'  [{i}/{len(names)}] {n} 글자 {was}→{best[0]}', flush=True)
        else:
            kept += 1
            print(f'  [{i}/{len(names)}] {n} 그대로 둔다 (원본 {was} ≤ 새판 {best[0]})',
                  flush=True)
    print(f'\n고침 {fixed}장 · 원본 유지 {kept}장')


if __name__ == '__main__':
    main()
