#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""그림 프롬프트를 낱말 뜻에서 만든다 → data/_imgprompts.json

왜: 과정 낱말 5,027개 중 그림이 붙은 것은 1,297개뿐이다. 나머지를 구우려면 프롬프트가 있어야
한다. 3,730개를 손으로 쓸 수는 없으니 무료 AI 대리인에게 **영어 장면 설명**만 받는다.
화풍 지시는 docs/image-prompts.md 와 **똑같이** 뒤에 붙인다 — 그림체가 갈리면 안 된다.

**그릴 수 있는 것만 고른다** (대표님: "추상적인것들은 이미지 없어도된다").
  · 그릴 수 있음 — 사물·사람·동물·음식·장소·몸으로 하는 동작
  · 그릴 수 없음 — 개념·정도·접속사·마음·문법
쓰기: python3 tools/img_prompt_gen.py [--part N --of M]
"""
import argparse, json, pathlib, re, subprocess, sys, time, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
URL = "https://viet-ai.chaochao-app.workers.dev"
# 이 일은 **Qwen 에게 넘겨도 되는 일**이다 — 그림 글감 만들기.
#   틀려도 사람이 알아볼 수 있는 갈래라 제미나이 몫을 아끼는 편이 낫다.
#   CHAO_LOCAL=1 로 돌리면 이 맥의 Qwen 이 한다 (tools/ai.py 참고).
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from ai import ask_text as _ask_text

ORIGIN = "https://tpgus5119-coder.github.io"
OUT = R / "data" / "_imgprompts.json"
CHUNK = 25
# 화풍은 **모든 그림이 같아야** 한다 — 낱말마다 그림체가 달라지면 눈이 그림체에 끌린다
# (Mayer 의 멀티미디어 학습 원리 중 coherence: 뜻과 상관없는 요소를 뺄수록 배운다).
# 부정어는 넣지 않는다 — FLUX 는 negative prompt 를 쓰지 않고, 문장 속 no/without 은
# 오히려 그 대상을 불러온다. 그래서 **긍정문으로만** 적는다.
STYLE = ("Flat vector illustration, bold black outlines, flat pastel fill, "
         "one centered subject, plain white background")

ASK = ("아래는 베트남어를 배우는 사람이 외울 낱말의 **한국어 뜻**이다.\n"
       "낱말마다 **그림으로 그릴 장면**을 영어 한 줄로 적어라.\n"
       "규칙 (근거는 아래에 적어 둔다)\n"
       " ① **한 장면에 대상 하나**. 배경·소품을 넣지 마라\n"
       " ② 그 뜻이 **그림만 보고 떠오를** 장면이어야 한다. 상징·비유는 안 된다\n"
       " ③ **손·손가락·사람 얼굴·글자·숫자를 장면에 넣지 마라.** 대신 사물이나 뒷모습으로 바꿔라\n"
       "    (손가락으로 가리키기 → 화살표 팻말, 사람이 먹는 모습 → 김이 나는 밥그릇)\n"
       " ④ **부정어를 쓰지 마라** — no·without·not 을 쓰면 그림이 오히려 그것을 그린다\n"
       " ⑤ 열 단어 안팎, 영어 한 문장\n"
       " ⑥ **그림으로 그릴 수 없는 말**(성질·정도·접속사·문법·마음)이면 빈 문자열\n"
       "출력은 JSON 배열만.\n"
       '형식: [{"k":"뜻","p":"english scene"}]\n\n뜻 목록:\n')

# 그릴 수 없는 말 — 미리 걸러 AI 를 아낀다
ABSTRACT = re.compile(
 r"^(그리고|그러나|하지만|그래서|또는|혹은|만약|비록|때문|위해|대해|따라|통해|동안|부터|까지|"
 r"에게|에서|으로|매우|아주|너무|조금|약간|더|덜|가장|제일|훨씬|거의|겨우|꽤|상당|정도|만큼|"
 r"보다|처럼|같이|이|그|저|무엇|어디|언제|누구|왜|어떻게|얼마|몇)")
ABS_TAIL = re.compile(r"(하다|되다|이다|스럽다|롭다|답다)$")
ABS_WORD = re.compile(r"생각|마음|느낌|뜻|의미|목적|이유|원인|결과|영향|방법|과정|상태|성격|"
                      r"개념|경우|조건|기회|가능|필요|중요|문제|의견|사실|정신|영혼|운명|가치")

def norm(v): return re.sub(r"\s+", " ", U.normalize("NFC", str(v)).strip())

def drawable(ko):
    k = norm(ko).split("/")[0].split("(")[0].strip()
    if not k or len(k) > 14: return False
    if ABSTRACT.match(k) or ABS_WORD.search(k): return False
    return True

def ask(items):
    body = json.dumps({"contents": [{"parts": [{"text": ASK + "\n".join("- " + x for x in items)}]}]},
                      ensure_ascii=False)
    p = subprocess.run(["curl", "-s", "-X", "POST", URL, "-m", "120",
                        "-H", "Content-Type: application/json", "-H", "Origin: " + ORIGIN,
                        "--data-binary", "@-"], input=body.encode(), capture_output=True)
    try:
        t = json.loads(p.stdout.decode())["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(re.search(r"\[.*\]", t, re.S).group(0))
    except Exception:
        return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, default=0); ap.add_argument("--of", type=int, default=1)
    a = ap.parse_args()
    global OUT
    if a.of > 1: OUT = R / "data" / f"_imgprompts-{a.part}.json"
    o = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    need = []

    def walk(v):
        for t in (v.get("tracks") or [v]):
            for c in t["chapters"]:
                for l in c["lessons"]: yield from l["words"]

    seen = set()
    for v in o["vols"]:
        for w in walk(v):
            if w.get("img"): continue
            k = norm(w["ko"]).split("/")[0].split("(")[0].strip()
            if k in seen or not drawable(w["ko"]): continue
            seen.add(k); need.append(k)
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    done = dict(have)
    for f in (R / "data").glob("_imgprompts*.json"):
        if f != OUT:
            try: done.update(json.loads(f.read_text(encoding="utf-8")))
            except Exception: pass
    if a.of > 1: need = need[a.part::a.of]
    need = [x for x in need if x not in done]
    print(f"그림 프롬프트가 필요한 뜻 {len(need)}개", flush=True)
    for i in range(0, len(need), CHUNK):
        part = need[i:i + CHUNK]
        for g in ask(part):
            k, pr = norm(g.get("k", "")), norm(g.get("p", ""))
            if not k or not pr or len(pr) < 8: continue
            have[k] = pr + ", " + STYLE
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=0), encoding="utf-8")
        print(f"  {i + len(part)}/{len(need)}", flush=True)
        time.sleep(1.0)
    print(f"끝. 프롬프트 {len(have)}개", flush=True)
main()
