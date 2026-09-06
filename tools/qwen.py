#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""이 맥의 Qwen(LM Studio)에게 일을 시키는 **하나뿐인 통로**.

왜 따로 두나: 도구마다 제각각 부르면 설정이 어긋난다. 여기 한 곳만 고치면 전부 바뀐다.

## 확인한 사실 (2026-08-31, lmstudio.ai 공식 문서 + 이 맥에서 실측)
· 이어붙이는 곳은 **REST API** 하나면 된다 — http://localhost:1234/v1/chat/completions
  (MCP 는 대화형 도구 연결용이라 배치 작업에는 무겁다. lms CLI 는 서버·모델 관리용)
· 이 API 가 받는 값은 이것뿐이다:
  model, messages, temperature, max_tokens, top_p, top_k, stream, stop,
  presence_penalty, frequency_penalty, logit_bias, repeat_penalty, seed
  → **생각(reasoning)을 끄는 값이 아예 없다.** `/no_think`·`enable_thinking`·
    `chat_template_kwargs` 를 보내도 무시된다(실측: 둘 다 시간만 끌다 끊겼다)
· **매 호출이 독립이다(stateless).** 우리가 보낸 messages 가 그 요청의 전부고
  서버는 앞 대화를 기억하지 않는다 → "대화창 리셋" 같은 것이 필요 없다.
  기억이 쌓이는 곳은 LM Studio **화면의 채팅창**뿐이다.

## 생각을 끄는 법 — 실측으로 찾은 방법
어시스턴트 차례를 **미리 채워** 생각 블록을 닫아 둔다:
    {"role":"assistant","content":"<think>\\n\\n</think>\\n\\n"}
모델은 그 뒤부터 이어 쓰므로 생각을 건너뛴다.
  낱말 24개 뜻 달기 — 생각 켠 채: 573초, 답 0개(토큰 3,999를 전부 생각에 씀)
                     생각 끈 뒤:  37초, 23개 전부
"조금만 생각"은 이 API 로는 못 한다(단계 값이 없다). 그래서 일의 성격으로 가른다:
  · think=False — 뽑아 적기·분류·형식 맞추기처럼 답이 정해진 일 (기본)
  · think=True  — 판단이 필요한 일. 대신 max_tokens 를 넉넉히 줘야 한다

## 모델 올릴 때 (한 번만)
    ~/.lmstudio/bin/lms server start
    ~/.lmstudio/bin/lms load qwen/qwen3.5-9b -c 16384 --gpu max --ttl 3600 --parallel 1 -y
  · 9B 를 쓴다. 27B 는 24GB 램에서 스왑이 걸려 기사 하나에 10분이 넘었다
  · --ttl 3600 : 한 시간 안 쓰면 저절로 내려 램을 돌려준다
  · --parallel 1 : 한 번에 하나씩. 여럿이면 각각이 느려진다

쓰기:
    from qwen import ask, ask_json
    ask_json("낱말 뜻을 적어라 …", items)      # JSON 배열을 받아 온다
"""
import json, re, subprocess, time

URL = "http://localhost:1234/v1/chat/completions"
MODEL = "qwen/qwen3.5-9b"
NOTHINK = {"role": "assistant", "content": "<think>\n\n</think>\n\n"}


def up():
    """서버가 살아 있고 모델이 올라와 있나."""
    try:
        r = subprocess.run(["curl", "-sS", "-m", "5", URL.replace("/chat/completions", "/models")],
                           capture_output=True, text=True, timeout=10).stdout
        return MODEL in r
    except Exception:
        return False


def ask(prompt, think=False, max_tokens=1500, temperature=0.2, tries=3, timeout=600):
    """한 번 묻고 글자를 받는다. think=False 면 생각을 건너뛴다."""
    msgs = [{"role": "user", "content": prompt}]
    if not think:
        msgs.append(NOTHINK)
    body = json.dumps({"model": MODEL, "messages": msgs, "temperature": temperature,
                       "max_tokens": max_tokens})
    for k in range(tries):
        try:
            r = subprocess.run(["curl", "-sS", "-X", "POST", URL,
                                "-H", "Content-Type: application/json", "--data-binary", "@-"],
                               input=body, capture_output=True, text=True, timeout=timeout).stdout
            t = json.loads(r)["choices"][0]["message"]["content"]
            # 생각을 켠 경우 앞머리에 남는 것을 떼어 낸다
            return re.sub(r"(?s)^.*?</think>\s*", "", t).strip()
        except Exception:
            time.sleep(1.5 * (k + 1))
    return ""


def ask_json(instruction, items, think=False, max_tokens=2500, chunk=25):
    """목록을 나눠 물어 JSON 배열을 이어 받는다.

    작게 나눠 묻는 편이 낫다 — 한 번에 많이 주면 뒤쪽을 대충 답하거나 잘린다."""
    out = []
    for i in range(0, len(items), chunk):
        part = items[i:i + chunk]
        t = ask(instruction + json.dumps(part, ensure_ascii=False),
                think=think, max_tokens=max_tokens)
        m = re.search(r"\[.*\]", t, re.S)
        if not m:
            continue
        try:
            got = json.loads(m.group(0))
            if isinstance(got, list):
                out += got
        except Exception:
            pass
    return out


if __name__ == "__main__":
    print("서버·모델:", "준비됨" if up() else "안 켜져 있음 — lms server start 먼저")
    t0 = time.time()
    print("시험:", ask("ví 는 한국어로? 낱말 하나만.", max_tokens=50))
    print("걸린 시간 %.1f초" % (time.time() - t0))
