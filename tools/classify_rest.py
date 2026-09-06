#!/usr/bin/env python3
"""그림이 없는 단어 433개를 둘로 가른다.

  draw   — 사람·동작·상태·장소처럼 **장면으로 그릴 수 있는 말** → 그림 프롬프트를 만든다
  form   — ~이다 · ~의 · 그리고 · 매우 같은 **기능어** → 그림 대신 짧은 공식을 만든다

기능어에 억지로 그림을 붙이면 배우는 사람이 그 그림을 뜻으로 오해한다
(검수에서 'cảm ơn = 고맙습니다'에 우는 아이가 그려진 게 정확히 그 경우였다).
기능어는 그림보다 'A của B = B의 A' 같은 한 줄 공식이 훨씬 잘 통한다.

결과: tools/imgrest.json
사용: python3 tools/classify_rest.py        (중계 서버로 물어본다)
"""
import json, pathlib, subprocess, sys, time

R = pathlib.Path(__file__).resolve().parent.parent
RELAY = 'https://viet-ai.chaochao-app.workers.dev'
OUT = R / 'tools' / 'imgrest.json'
BATCH = 30

PROMPT = """너는 베트남어 학습앱의 단어 카드를 설계한다. 배우는 사람은 한국인 초보다.

**추상어를 그림으로 그리는 방법은 이미 정해져 있다. 새로 짜내지 마라.**
그림 사전(Oxford Picture Dictionary 계열), 언어 학습 앱, 그리고 말 대신 그림으로 뜻을
전하는 픽토그램 체계(ARASAAC 등)가 백 년 가까이 다듬어 온 규약이 있다. 그걸 그대로 쓴다.
뜻만 같으면 어느 언어의 교재든 같은 방법이 통한다 — '알다'는 어느 나라 교재에서나
머리 위 전구다.

【규약 — 이 안에서 골라라】
 (1) 은유적 닻 — 뜻을 담은 구체물 하나로 바꾼다
     알다=머리 위 전구 · 시간=모래시계 · 어렵다=무거운 바위를 미는 사람
     자유=새 · 기억=머릿속 실타래 · 준비=가방을 싸는 모습
 (2) 화살표 — 방향·변화·가리킴. 추상어 그림의 절반은 화살표가 만든다
     가다=사람에서 앞으로 뻗은 화살표 · 오다=안으로 들어오는 화살표
     다시=휘어 돌아오는 화살표 · 위·아래·앞·뒤=상자 하나와 공 하나, 화살표로 관계만
 (3) 생각풍선·말풍선
     원하다=생각풍선 안에 갖고 싶은 것 · 그리워하다=생각풍선 안에 사람
     말하다=말풍선 · 묻다=말풍선 안 물음표 · 모른다=머리 위 물음표
 (4) X 표시·사선 — 부정. 없다=X 친 빈 상자 · 하지 마라=X 친 동작
 (5) 흐린 회색은 배경, 진한 색은 주인공. 여럿 중 하나를 가리킬 때 나머지를 회색으로
 (6) 표정과 자세 — 감정·몸 상태
     아프다=아픈 곳을 짚고 찡그린 얼굴 · 피곤하다=축 처진 어깨와 하품
 (7) 두 장면을 나란히 — 비교·정도
     더=작은 것 옆에 큰 것 · 가장=셋 중 제일 큰 것만 진한 색
     빠르다=속도선이 붙은 사람 / 느리다=거북이 걸음
 (8) 저울·화살표·크기 — 정도와 비교. 매우=막대가 끝까지 찬 눈금

【손을 피해라】
그림을 만드는 AI는 손을 제대로 못 그린다(우리 검수에서 44장이 손 때문에 못 쓰게 됐다).
손짓으로 뜻을 만드는 규약은 되도록 피하고, 물건·화살표·표정으로 바꿔라.
꼭 손이 필요하면 "one simple mitten-like hand, fingers not detailed" 라고 적어라.

이제 아래 낱말들을 둘로 가른다.

  "draw" — 위 규약 중 하나로 **한 장면에 담을 수 있는 말**.
           규약이 있으니 대부분은 여기에 들어간다. 애매해도 규약이 잡히면 draw 다.
  "form" — 규약으로도 그림이 안 되는 순수 문법 기능어
           (~이다 · ~의 · 문장 끝 공손 · 의문 조사 같은 것). 이건 그림 대신 한 줄 공식.

JSON 배열로만 답하라.
 draw 이면 {{"vi":"...", "k":"draw", "c":"쓴 규약 번호", "p":"영어 그림 프롬프트"}}
 form 이면 {{"vi":"...", "k":"form", "f":"한 줄 공식", "e":"베트남어 보기 = 한국어 뜻"}}

그림 프롬프트(p) 규칙
 · 영어. 한 장면. 요소 세 개 이하. 사진이 아니라 **아이콘처럼 단순하게**.
 · 규약을 프롬프트 안에 그대로 적어라
   (예: "a thought bubble above a person's head containing a bicycle")
 · 반드시 이 꼬리말로 끝낼 것:
   ", simple flat icon illustration, soft pastel colors, thick outlines, plain white background,
   minimal detail, hands not visible, absolutely no text, no letters, no numbers, no logo"

공식(f) 규칙
 · 한국어로 열 글자 안팎. 자리를 A·B로 표시한다.
   của → "A của B = B의 A"   ·   là → "A là B = A는 B이다"
 · e 는 그 공식이 쓰인 짧은 보기. "tên của tôi = 내 이름" 처럼.

낱말:
{words}
"""

def ask(words):
    body = json.dumps({
        'contents': [{'role': 'user', 'parts': [{'text': PROMPT.format(
            words='\n'.join(f"{w['vi']} = {w['ko']}" for w in words))}]}],
        'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 8000,
                             'responseMimeType': 'application/json',
                             'thinkingConfig': {'thinkingBudget': 0}},
    }, ensure_ascii=False)
    pathlib.Path('/tmp/cls.json').write_text(body)
    for _ in range(3):
        r = subprocess.run(['curl', '-s', '-X', 'POST', RELAY,
                            '-H', 'Origin: http://localhost:8899',
                            '-H', 'Content-Type: application/json',
                            '--data-binary', '@/tmp/cls.json'],
                           capture_output=True, text=True).stdout
        try:
            return json.loads(json.loads(r)['candidates'][0]['content']['parts'][0]['text'])
        except Exception:
            time.sleep(6)
    return []

def main():
    words = json.loads(pathlib.Path('/tmp/noimg.json').read_text())
    got = json.loads(OUT.read_text()) if OUT.exists() else {}
    todo = [w for w in words if w['vi'] not in got]
    print(f'남은 낱말 {len(todo)} / {len(words)}')
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        res = ask(chunk)
        for x in res:
            if x.get('vi'):
                got[x['vi']] = x
        OUT.write_text(json.dumps(got, ensure_ascii=False, indent=1))
        d = sum(1 for v in got.values() if v.get('k') == 'draw')
        print(f'  {len(got)}/{len(words)} (그림 {d} · 공식 {len(got)-d})', flush=True)
        time.sleep(4)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
