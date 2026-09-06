---
name: 일-나누기
description: 짜오짜오 앱 일을 기계·Qwen·제미나이·클로드에게 나눈다. 낱말 검수, 뜻 달기, 그림 글감, 카드뉴스, TTS 검수 같은 일을 시작할 때 누구에게 맡길지 정하고 실제로 붙여 준다. 토큰을 아끼면서 품질을 지켜야 할 때 쓴다.
---

# 일 나누기

## 1) 먼저 물어라 — 셀 수 있나

셀 수 있으면 **AI 를 부르지 마라.** 공짜이고 늘 같은 답이고 틀릴 일이 없다.

셀 수 있는 일들 (실제로 이렇게 했다):
- 낱말에 소리 파일이 있나 → 낱말을 해시로 바꿔 `audio/{f,m,sf,sm}/n/<해시>.mp3` 를 센다
- 네 목소리가 다른가 → 해시를 견준다
- 북부·남부가 갈리나 → 크기 무리가 갈린다 (북 ~10.7KB · 남 ~4.8KB)
- 낱말이 사전에 있나 → `data/_vi_words.json` (47,341개)
- 한 낱말인가 두 낱말이 붙었나 → 사전 표제어면 한 낱말. 아니면 쪼개 본다
- 발음이 한글인가 → 정규식. 아니면 `vi_kr.word()` 로 다시 만든다
- 그림이 겹치나 → 파일 해시

## 2) 아니면 관문 넷

    python3 tools/route.py "뜻 달기"        # → qwen
    python3 tools/route.py                  # 표 전체

코드에서:

    import sys; sys.path.insert(0, "tools")
    from route import who
    who(verifiable=True, visible=True, closed=True, n=800)

관문: 검산되나 · 틀리면 보이나 · 지어낼 자리 없나 · 시간 되나(1.2초/건)

## 3) Qwen 을 부르는 법

    import sys; sys.path.insert(0, "tools")
    from ai import ask_text, ask_json
    ask_json(prompt, local=True)          # 이 맥의 Qwen
    # 또는 환경변수로 통째로:  CHAO_LOCAL=1 python3 tools/....py

**반드시 근거를 함께 준다.** 사전 뜻풀이·기사 본문·꼭지 이름 같은 것.
근거 없이 물으면 지어낸다.

**받은 답은 규칙으로 다시 거른다.** 최소한 이 셋:
- 한글이어야 할 자리에 다른 글자가 섞였나
- 12자를 넘나 (뜻은 짧아야 한다)
- 고칠 때 근거를 댔고, 그 근거가 실제 자료 안에 있나

## 4) 만드는 도구

| 만들 것 | 도구 | 비고 |
|---|---|---|
| 그림 | Draw Things `http://127.0.0.1:7860` | FLUX schnell **4단계** |
| 소리 북부 | `tools/gen_audio.py` | edge-tts |
| 소리 남부 | `tools/gen_south_vtts.py --voice sf\|sm` | v-tts |
| 소리 검수 | faster-whisper | 받아쓰고 낱말과 맞대 본다 |
| 한글 발음 | `tools/vi_kr.py` | **AI 금지** |

## 5) 마치기 전에

숫자 확인 → 눈으로 확인 → `python3 tools/stamp.py` → **`git push origin main`**

커밋만으로는 앱이 안 바뀐다. 실제로 이걸 놓쳐 33개가 반영 안 된 적이 있다.
