#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""우리 사전을 키운다 → data/_vi_words.json

대표님 지시 (2026-09-01): "우리 사전이 빈약하니까 우리 사전을 더 보강하고,
                          일단 우리 사전으로 1차 검증하고 나서 위키 사전에서 보라."

## 왜
_vi_ipa.json 은 5,381 표제어뿐이라 구멍이 컸다 — cam(주황)·mình(나)·cô giáo 같은
기본 낱말이 없어서, 있는 낱말을 '사전에 없다'고 잘라 버릴 뻔했다.

## 무엇을 받나
영어 위키낱말의 **Vietnamese lemmas** 분류 (45,381 표제어).
표제어란 사전에 **제 항목으로 실린 말**이다. 그래서 이 목록에 있으면 한 낱말이고,
없으면 여러 낱말이 붙은 것이거나 사전에 없는 말이다 — 우리가 필요한 잣대가 바로 이것이다.
(뜻은 안 받는다. 우리는 '한 낱말인가'만 물으면 된다. 자료가 가볍고 빨라진다)

한 번 받아 두면 다시 받을 일이 없다. 인터넷을 안 타므로 검증이 **빨라지고 공짜**가 된다.

쓰기: python3 tools/dict_build.py [--refresh]
"""
import argparse, json, pathlib, subprocess, sys, time, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
OUT = R / "data" / "_vi_words.json"
API = ("https://en.wiktionary.org/w/api.php?action=query&list=categorymembers"
       "&cmtitle=Category:Vietnamese_lemmas&cmlimit=500&cmnamespace=0&format=json&continue=")
n = lambda s: U.normalize("NFC", str(s)).strip()


def get(url):
    for _ in range(4):
        try:
            r = subprocess.run(["curl", "-sS", "-m", "30", url],
                               capture_output=True, text=True, timeout=45).stdout
            return json.loads(r)
        except Exception:
            time.sleep(2)
    return {}


def main():
    a = argparse.ArgumentParser(); a.add_argument("--refresh", action="store_true"); a = a.parse_args()
    if OUT.exists() and not a.refresh:
        print(f"이미 있다: {len(json.loads(OUT.read_text(encoding='utf-8')))} 낱말 (--refresh 로 다시 받는다)")
        return
    words, cont, page, miss = [], "", 0, 0
    while True:
        j = get(API + cont)
        got = j.get("query", {}).get("categorymembers", [])
        if not got:
            # 받기에 실패했을 뿐일 수 있다 — 조용히 멈추면 반도 못 받는다 (실측: 9,499/45,381)
            miss += 1
            if miss >= 5:
                print(f"  다섯 번 잇달아 못 받았다 — 여기까지 ({len(words)}개)"); break
            time.sleep(5); continue
        miss = 0
        words += [n(x["title"]) for x in got]
        page += 1
        if page % 20 == 0:
            print(f"  {len(words)}개", flush=True)
        # MediaWiki 는 continue 를 **두 값**으로 준다. 하나만 보내면 첫 장만 돌아온다
        # (그래서 처음엔 5,000개에서 멈췄다 — 45,381개 중 열에 하나였다)
        co = j.get("continue", {})
        if not co or not got:
            break
        cont = "".join(f"&{key}={val}" for key, val in co.items())
        time.sleep(0.1)

    # 우리가 이미 갖고 있던 것과 합친다 — 버릴 이유가 없다
    ipa = R / "data" / "_vi_ipa.json"
    if ipa.exists():
        words += [n(x) for x in json.loads(ipa.read_text(encoding="utf-8"))]
    uniq = sorted({w for w in words if w and not w.startswith(("Category:", "Appendix:"))})
    OUT.write_text(json.dumps(uniq, ensure_ascii=False), encoding="utf-8")
    multi = sum(1 for w in uniq if " " in w)
    print(f"\n우리 사전 {len(uniq)} 낱말 (여러 음절짜리 {multi}) → {OUT}")


# 불러오기만 할 때는 돌지 않는다 — 다른 도구가 TOPICS 같은 것을
# 가져다 쓸 때 낱말 모으기가 통째로 다시 도는 사고가 있었다 (2026-09-01).
if __name__ == "__main__":
    main()
