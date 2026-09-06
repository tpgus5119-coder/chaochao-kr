#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 를 부르는 **한 곳** — 제미나이(워커)냐 이 맥의 Qwen 이냐를 여기서 고른다.

대표님 지시 (2026-09-01): "제미나이 키로 무슨 일을 하고 있니? 그것들을 qwen 에게
                          분담할 수 있으면 해야지."

## 왜 나누나
제미나이는 **하루 몫이 정해져 있다.** 다 쓰면 카드뉴스도 검수도 멈춘다.
그런데 예비 경로를 실제로 재 보니 **groq·openrouter 는 등록돼 있지 않았다**
(워커 ?health=1 : {"groq": false, "openrouter": false, "cloudflare": true}).
곧 구글이 막히면 남는 것은 Cloudflare AI 하나뿐이다.
그래서 **몫을 아껴야 하는 일과 아껴도 되는 일을 갈라** 쓴다.

## 어느 쪽에 맡기나
| Qwen(공짜·이 맥) | 제미나이(몫이 든다) |
|---|---|
| 분류·태그 붙이기 | 예문 **짓기** (문법이 틀리면 그대로 배운다) |
| 있는 것을 가려내기(철자·그림 판정) | 문법 **설명** 쓰기 |
| 짧은 뜻 달기 | 기사 → 학습 세트 만들기 |
| 그림 글감 만들기 | 뜻이 비어 있는 낱말 채우기 |
| 요약 | |

가르는 잣대: **틀렸을 때 사람이 알아볼 수 있나.**
분류·판정은 틀려도 눈에 띈다. 예문·문법은 틀린 채로 외워 버린다.

## 쓰는 법
    from ai import ask_text
    t = ask_text(prompt, local=True)     # Qwen
    t = ask_text(prompt)                 # 제미나이(워커)
환경변수 `CHAO_LOCAL=1` 을 주면 local 기본값이 참이 된다 — 도구를 안 고치고 통째로 돌릴 때.
"""
import json, os, pathlib, re, subprocess, time

WORKER = "https://viet-ai.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"
QWEN = "http://localhost:1234/v1/chat/completions"
BIG, SMALL = "qwen/qwen3.8-27b", "qwen/qwen3.5-9b"
QMODEL = SMALL                       # 기본은 작은 것. pick_model() 이 상황 보고 바꾼다
# 생각을 건너뛰게 하는 자리채움 — LM Studio API 에는 생각을 끄는 값이 없다.
# 어시스턴트 차례를 미리 닫아 두면 모델이 그 뒤부터 이어 쓴다.
NOTHINK = {"role": "assistant", "content": "<think>\n\n</think>\n\n"}

DEFAULT_LOCAL = os.environ.get("CHAO_LOCAL") == "1"


def free_gb():
    """지금 쓸 수 있는 메모리(GB). 애플 실리콘은 램을 CPU·GPU 가 나눠 쓴다."""
    import subprocess as _sp
    try:
        t = _sp.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
        page = 16384
        get = lambda k: int([l for l in t.split("\n") if l.startswith(k)][0].split(":")[1].strip(" ."))
        # 자유 + 비활성 + 압축 해제 가능한 것을 여유로 본다
        return (get("Pages free") + get("Pages inactive")) * page / 1024**3
    except Exception:
        return 0.0


def pick_model(prefer_big=False):
    """메모리를 보고 큰 모델(27B)과 작은 모델(9B) 중 고른다.

    27B 는 16GB, 9B 는 10.5GB 를 먹는다. 24GB 짜리 맥이라 27B 를 올리면
    다른 일(Draw Things · 브라우저)과 부딪혀 스왑이 걸린다 —
    실측으로 기사 하나에 10분이 넘었다. 그래서 **아무도 안 쓰는 밤에만** 큰 것을 쓴다.
    prefer_big=True 로 부르고 여유가 18GB 넘을 때만 27B 로 간다."""
    global QMODEL
    want = BIG if (prefer_big and free_gb() >= 18) else SMALL
    if want == QMODEL and loaded(want):
        return QMODEL
    import subprocess as _sp
    lms = str(pathlib.Path.home() / ".lmstudio/bin/lms")
    _sp.run([lms, "unload", "--all"], capture_output=True, timeout=120)
    ctx = "8192" if want == BIG else "16384"
    _sp.run([lms, "load", want, "-c", ctx, "--gpu", "max",
             "--ttl", "7200", "--parallel", "1", "-y"], capture_output=True, timeout=900)
    QMODEL = want
    return QMODEL


def loaded(name):
    import subprocess as _sp
    try:
        r = _sp.run([str(pathlib.Path.home() / ".lmstudio/bin/lms"), "ps"],
                    capture_output=True, text=True, timeout=20).stdout
        return name in r
    except Exception:
        return False


def qwen_up():
    try:
        r = subprocess.run(["curl", "-sS", "-m", "5", QWEN.replace("/chat/completions", "/models")],
                           capture_output=True, text=True, timeout=10).stdout
        return QMODEL in r
    except Exception:
        return False


def ask_text(prompt, local=None, tries=3, max_tokens=3000, timeout=300):
    """글자를 받아 온다. local 이 참이면 Qwen, 아니면 워커(제미나이)."""
    use_local = DEFAULT_LOCAL if local is None else local
    if use_local and not qwen_up():
        use_local = False                      # Qwen 이 꺼져 있으면 조용히 워커로
    for k in range(tries):
        try:
            if use_local:
                body = json.dumps({"model": QMODEL, "temperature": 0.2,
                                   "max_tokens": max_tokens,
                                   "messages": [{"role": "user", "content": prompt}, NOTHINK]})
                cmd = ["curl", "-sS", "-X", "POST", QWEN,
                       "-H", "Content-Type: application/json", "--data-binary", "@-"]
            else:
                body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]})
                cmd = ["curl", "-sS", "-X", "POST", WORKER,
                       "-H", "Content-Type: application/json",
                       "-H", f"Origin: {ORIGIN}", "--data-binary", "@-"]
            r = subprocess.run(cmd, input=body, capture_output=True, text=True,
                               timeout=timeout).stdout
            j = json.loads(r)
            t = (j["choices"][0]["message"]["content"] if use_local
                 else j["candidates"][0]["content"]["parts"][0]["text"])
            return re.sub(r"(?s)^.*?</think>\s*", "", t).strip()
        except Exception:
            time.sleep(1.5 * (k + 1))
    return ""


def ask_json(prompt, local=None, **kw):
    """JSON 배열이나 객체를 받아 온다. 못 받으면 None."""
    t = ask_text(prompt, local=local, **kw)
    m = re.search(r"[\[{].*[\]}]", t, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None
