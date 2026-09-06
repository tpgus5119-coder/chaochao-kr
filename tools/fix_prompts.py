#!/usr/bin/env python3
"""검수에서 걸린 그림의 프롬프트를 고친다 — 같은 실패가 반복되지 않게.

검수 결과(689장 전수)에서 나온 고장 유형별 처방:
  A 손·손가락 / B 팔·다리 → 손을 아예 화면에서 뺀다. 생성 모델은 손을 못 그린다.
  C 얼굴            → 얼굴을 단순하게, 이목구비를 또렷하게 지정한다
  D 글자 얼룩       → '글자 금지'를 문장 앞뒤로 두 번 박고, 글자가 생길 물건(간판·명찰·달력)을 뺀다
  E 개수            → tools/draw_exact.py 가 직접 그린다 (여기서 다루지 않는다)
  F 뜻 불일치 / G 기타 → 검수원이 적어 준 처방을 그대로 프롬프트에 반영한다

사용: python3 tools/fix_prompts.py            (프롬프트만 고친다)
      python3 tools/fix_prompts.py --wipe     (고친 그림 파일도 지운다 → 다시 뽑히게)
"""
import json, pathlib, re, sys

R = pathlib.Path(__file__).resolve().parent.parent
QA = json.load(open('/tmp/imgqa.json', encoding='utf-8')) if pathlib.Path('/tmp/imgqa.json').exists() \
     else json.load(open(R / 'docs' / 'image-qa.json', encoding='utf-8'))
MD = R / 'docs' / 'image-prompts.md'

NOTEXT = 'absolutely no text, no letters, no numbers, no words, no logo, no label, no signage, blank surfaces'
NOHAND = 'hands not visible, arms relaxed and out of frame or fully behind the object, no fingers shown'
CLEARFACE = 'simple clear face with two eyes, small nose and mouth, symmetrical'

RULE = {
    'A': NOHAND, 'B': NOHAND + ', full body in natural proportion, both legs attached at the hips',
    'C': CLEARFACE, 'D': NOTEXT, 'F': '', 'G': '',
}

def patch(name, kind, fix):
    add = RULE.get((kind or 'G')[0], '')
    bits = [add, NOTEXT]
    # 검수원 처방에 담긴 구체적 지시를 영어 키워드로 옮긴다
    f = (fix or '') + ' ' + (kind or '')
    if '달력' in f or '요일' in f: bits.append('no calendar, no grid of dates')
    if '시계' in f or '숫자판' in f: bits.append('clock face without any numbers, plain tick marks only')
    if '국기' in f or '태극' in f: bits.append('no national flag')
    if '손' in f: bits.append(NOHAND)
    seen, out = set(), []
    for b in bits:
        for part in [p.strip() for p in b.split(',') if p.strip()]:
            if part.lower() not in seen:
                seen.add(part.lower()); out.append(part)
    return ', '.join(out)

def main():
    txt = MD.read_text()
    lines = txt.splitlines()
    bad = {x['name']: x for x in QA['bad'] if (x.get('kind') or 'G')[0] != 'E'}
    fixed, missing = 0, []
    for i, ln in enumerate(lines):
        m = re.match(r'\*\*([\w-]+)\.webp\*\*', ln)
        if not m or m.group(1) not in bad:
            continue
        nm = m.group(1)
        # 바로 다음의 '> ' 줄이 프롬프트다
        for j in range(i + 1, min(i + 4, len(lines))):
            if lines[j].startswith('> '):
                base = lines[j][2:].strip()
                base = re.sub(r',?\s*no text[^,]*', '', base, flags=re.I)
                base = re.sub(r',?\s*no letters[^,]*', '', base, flags=re.I)
                lines[j] = '> ' + base.rstrip(', ') + ', ' + patch(nm, bad[nm].get('kind'), bad[nm].get('fix'))
                fixed += 1
                break
        else:
            missing.append(nm)
    MD.write_text('\n'.join(lines) + '\n')
    print(f'프롬프트 {fixed}개 고침' + (f' · 못 찾음 {len(missing)}: {missing[:5]}' if missing else ''))
    if '--wipe' in sys.argv:
        gone = 0
        for nm in bad:
            p = R / 'img' / f'{nm}.webp'
            if p.exists(): p.unlink(); gone += 1
        print(f'그림 {gone}장 지움 — 이제 tools/gen_images.py 가 다시 뽑는다')

if __name__ == '__main__':
    main()
