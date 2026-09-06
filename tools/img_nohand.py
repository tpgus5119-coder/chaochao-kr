#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""그림 글감에서 **손·얼굴·글자**가 나올 장면을 다른 장면으로 바꾼다 → _imgprompts.json

왜 (대표님 지시, 2026-08-30): "손 같은 거 잘 못 만드니까 이미지에 손은 넣지 않도록 미리 세팅."
확산 모델은 손가락 수를 자주 틀린다. 그런데 **부정어로는 막을 수 없다** —
FLUX.1 schnell 은 negative prompt 를 쓰지 않고, 문장 속 "no hands"는 오히려 손을 부른다.
그래서 **손이 안 나오는 장면으로 바꿔 적는다**(긍정문으로).
쓰기: python3 tools/img_nohand.py
"""
import json, pathlib, re, subprocess, time

R = pathlib.Path(__file__).resolve().parent.parent
URL = "https://viet-ai.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"
P = R / "data" / "_imgprompts.json"
CHUNK = 15
# palm tree(야자수)는 손이 아니다 — 'palm' 만 보고 태풍 장면을 손으로 잡았었다.
# 자막·간판처럼 **글자가 있어야 뜻이 통하는** 낱말은 건드리지 않는다.
BAD = re.compile(r"\b(hands?|fingers?|palms?(?! tree)|holding|hold|faces?|smiling|"
                 r"writing)\b(?! tree)", re.I)
SKIP = re.compile(r"자막|간판|글자|문자|편지|서명|표지판|신문|책|메뉴판")
STYLE = ("Flat vector illustration, bold black outlines, flat pastel fill, "
         "one centered subject, plain white background")
ASK = ("아래는 낱말 카드에 넣을 **그림 장면**이다. 손·손가락·사람 얼굴·글자가 들어 있어 다시 써야 한다.\n"
       "그 뜻이 그대로 전해지면서 **손·얼굴·글자가 나오지 않는** 장면으로 바꿔라.\n"
       "바꾸는 법\n"
       " · 사람이 무엇을 든 장면 → **그 물건만** (손으로 컵을 든다 → 김이 나는 컵)\n"
       " · 손가락으로 가리킴 → 화살표 팻말·발자국·길\n"
       " · 사람이 하는 동작 → 그 동작의 **자취나 도구** (달리는 사람 → 운동화와 트랙)\n"
       " · 사람이 꼭 있어야 하면 **뒷모습이나 실루엣**으로\n"
       " · **부정어(no·without)를 쓰지 마라** — 그림이 오히려 그것을 그린다\n"
       " · 영어 한 문장, 열 단어 안팎. 대상은 하나\n"
       '출력은 JSON 배열만. [{"k":"뜻","p":"english scene"}]\n\n')


def ask(items, tries=3):
    body = json.dumps({"contents": [{"parts": [{"text": ASK + json.dumps(items, ensure_ascii=False)}]}]})
    for i in range(tries):
        p = subprocess.run(["curl", "-sS", "-X", "POST", URL, "-H", "Content-Type: application/json",
                            "-H", f"Origin: {ORIGIN}", "--data-binary", "@-"],
                           input=body, capture_output=True, text=True, timeout=200)
        t = p.stdout
        try: t = json.loads(t)["candidates"][0]["content"]["parts"][0]["text"]
        except Exception: pass
        if "[object Object]" not in t:
            m = re.search(r"\[.*\]", t, re.S)
            if m:
                try: return json.loads(m.group(0))
                except Exception: pass
        time.sleep(8 * (i + 1))
    return []


def main():
    D = json.loads(P.read_text(encoding="utf-8"))
    need = [(k, re.split(r",\s*Flat vector", str(v))[0]) for k, v in D.items()
            if BAD.search(re.split(r",\s*Flat vector", str(v))[0]) and not SKIP.search(k)]
    print(f"손·얼굴·글자가 든 글감 {len(need)}개", flush=True)
    fixed = 0
    for i in range(0, len(need), CHUNK):
        part = need[i:i + CHUNK]
        got = ask([{"k": k, "지금 장면": v} for k, v in part])
        ks = {k for k, _ in part}
        for g in got:
            k = str(g.get("k", "")); pr = str(g.get("p", "")).strip()
            if k in ks and pr and not BAD.search(pr) and not re.search(r"\bno\b|without", pr, re.I):
                D[k] = pr.rstrip(". ") + ". " + STYLE; fixed += 1
        P.write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {min(i+CHUNK,len(need))}/{len(need)} · 바꾼 것 {fixed}", flush=True)
        time.sleep(4)          # 무료 대리인은 분당 20회다 — 천천히 묻는다
    left = sum(1 for v in D.values() if BAD.search(re.split(r",\s*Flat vector", str(v))[0]))
    print(f"끝. 바꾼 글감 {fixed}개 · 아직 남은 것 {left}개")


if __name__ == "__main__":
    main()
