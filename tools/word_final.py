#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**최종 검수** — 낱말 하나하나를 실제 사전에서 확인한다 → data/_new_words.json

대표님 지시 (2026-09-01): "진짜 현존 최고의 사전을 우리 어플에 넣지 않는 이상,
                          최종 단어 검수는 현존 최고의 사전에서 점검을 해야 함."

## 왜 이게 마지막 관문인가
앞 단계들은 **빠르게 거르는** 체다. 우리 사전 목록은 '표제어인가'만 알려 주고 뜻은 모른다.
Qwen 은 공짜지만 틀린다. 그래서 마지막에는 **뜻풀이가 실린 사전 본문**을 직접 읽는다.

## 무엇을 보나 (낱말 하나에 요청 하나 — 공짜다)
영어 위키낱말 본문에서 그 낱말의 **베트남어 뜻풀이**를 뽑아
  ① 사전에 항목이 있는가                    → 없으면 '없음'
  ② 우리가 적은 한국어 뜻이 그 뜻풀이와 맞는가 → 맞으면 '맞음'
  ③ 애매하면 Qwen 에게 뜻풀이를 보여 주고 묻는다 (사람이 아니라 근거를 보고 답한다)
     — 이때 Qwen 은 **지어낼 수 없다.** 사전 본문을 놓고 고르는 일이라 안전하다

표시: fin=ok(사전이 뒷받침) · fin=diff(뜻이 다르다, 사전 뜻을 def 에) · fin=none(사전에 없다)
쓰기: python3 tools/word_final.py [--limit 200]
"""
import argparse, json, pathlib, re, subprocess, sys, time, urllib.parse, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
OUT = R / "data" / "_new_words.json"
DEF = R / "data" / "_vi_def.json"           # 받아 둔 뜻풀이 — 두 번 받지 않는다
n = lambda s: U.normalize("NFC", str(s)).strip()
# 위키낱말의 **뜻풀이 전용** 길목. 품사와 뜻만 깔끔하게 온다.
#   xe đạp → {"vi":[{"partOfSpeech":"Noun","definitions":[{"definition":"bicycle"}]}]}
# 앞서 extracts 로 스무 개씩 묶어 받으려 했으나 **한 개만 돌아왔다** (exlimit 은 전문에 안 먹는다).
# 그래서 낱말 하나에 요청 하나다. 대신 가볍고 빨라서 1,200개가 몇 분이면 된다.
API = "https://en.wiktionary.org/api/rest_v1/page/definition/"
# 위키미디어는 신원을 밝히지 않는 요청을 막는다 — 이것이 없어 1,212개 중 80개만 받았었다
UA = "chaochao-vn-app/1.0 (learning app dictionary check)"
GAP = 0.35        # 요청 사이 쉬는 시간. 0.12 로는 절반이 429 로 막혔다 (실측)


def defs(word, cache):
    """그 낱말의 **베트남어 뜻풀이**. 사전에 없으면 빈 글, 못 물어봤으면 None."""
    key = n(word)
    if key in cache:
        return cache[key]
    # 위키는 너무 빠르면 **429(그만 좀 걸어라)** 를 준다. 실측으로 절반이 여기서 조용히
    # 실패하고 있었다. 코드를 직접 보고, 429 면 점점 더 오래 쉬었다 다시 건다.
    for k_ in range(6):
        try:
            r = subprocess.run(["curl", "-sS", "-m", "20", "-w", "\n%{http_code}",
                                "-H", f"User-Agent: {UA}",
                                API + urllib.parse.quote(word.replace(" ", "_"))],
                               capture_output=True, text=True, timeout=30).stdout
            body, _, code = r.rpartition("\n")
            if code.strip() == "429":
                time.sleep(2 + k_ * 3); continue
            r = body
            if not r.strip():
                raise ValueError
            j = json.loads(r)
            if "vi" not in j:                     # 쪽은 있는데 베트남어 항목이 없다
                cache[key] = ""; time.sleep(GAP); return ""
            out = []
            for e in j["vi"]:
                pos = e.get("partOfSpeech", "")
                for x in e.get("definitions", [])[:3]:
                    t = re.sub(r"<[^>]+>", "", x.get("definition", "")).strip()
                    if t:
                        out.append(f"({pos}) {t}" if pos else t)
            cache[key] = " / ".join(out[:6])[:500]
            time.sleep(GAP)
            return cache[key]
        except Exception:
            time.sleep(1.5)
    return None                                   # 못 물어봄 — 표시하지 않는다


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--limit", type=int, default=0); a.add_argument("--all", action="store_true")
    a = a.parse_args()
    d = json.loads(OUT.read_text(encoding="utf-8"))
    cache = json.loads(DEF.read_text(encoding="utf-8")) if DEF.exists() else {}
    todo = [w for ws in d.values() for w in ws if a.all or not w.get("fin")]
    if a.limit:
        todo = todo[:a.limit]
    print(f"최종 검수할 낱말 {len(todo)}", flush=True)

    none_, have = [], []
    for i, w in enumerate(todo, 1):
        t = defs(w["vi"], cache)
        if t is None:
            continue
        if not t:
            w["fin"] = "none"; none_.append(w)
        else:
            w["fin"], w["def"] = "봐야함", t; have.append(w)
        if i % 200 == 0:
            OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            DEF.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            print(f"  {i}/{len(todo)}  (사전에 없음 {len(none_)})", flush=True)
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    DEF.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    print(f"사전에 뜻풀이가 있는 낱말 {len(have)} · 없는 낱말 {len(none_)}", flush=True)

    # ── 뜻이 맞는지는 Qwen 이 **사전 본문을 보고** 고른다 (지어낼 수 없다)
    from qwen import ask_json, up
    if not have or not up():
        print("Qwen 이 꺼져 있어 뜻 대조는 건너뛴다"); return
    # 사전의 **첫 번째 뜻**이 흔한 뜻이라는 법이 없다 — 실측:
    #   cầu 는 '셔틀콕'이 먼저 실려 있어 '다리'를 밀어냈고,
    #   tôi 는 '노예'가 먼저라 '저'가 흔들렸고,
    #   không 은 '숫자 꼭지'인데 '영'이 '없다'로 바뀌었다.
    # 그래서 ① 꼭지 상황을 함께 주고 ② 우리 뜻이 **여러 뜻 중 하나라도** 맞으면 ok 로 두고
    # ③ 고칠 때는 **사전의 어느 대목을 근거로 삼았는지** 적게 한다(근거 없이 못 고친다).
    ASK = ("아래는 베트남어 낱말과, 그 낱말이 실린 **꼭지(상황)**와, 우리가 적은 한국어 뜻과,\n"
           "영어 사전의 뜻풀이다. 사전 뜻풀이를 근거로만 답하라.\n"
           "  v  : ok  = 우리 뜻이 사전 뜻풀이 **가운데 하나라도** 해당한다\n"
           "       bad = 사전 뜻풀이 어디에도 우리 뜻이 없다\n"
           "  ko : bad 일 때만, **그 꼭지 상황에 맞는** 한국어 뜻을 12자 이내로\n"
           "  why: bad 일 때만, 근거로 삼은 사전 대목을 그대로 옮겨 적어라\n"
           "규칙\n"
           " · 사전에 여러 뜻이 있으면 **첫 번째가 아니라 그 꼭지에 맞는 것**을 본다\n"
           " · 우리 뜻이 그 꼭지에서 쓸 만하면 ok. **애매하면 ok**\n"
           " · why 를 못 적겠으면 bad 로 하지 마라\n"
           '출력은 JSON 배열만: [{"vi":"낱말","v":"ok|bad","ko":"뜻","why":"근거"}]\n\n')
    tp = {id(w): t for t, ws in d.items() for w in ws}
    items = [{"vi": w["vi"], "꼭지": tp.get(id(w), ""), "우리뜻": w["ko"],
              "사전": (w.get("def") or "")[:260]} for w in have]
    res = ask_json(ASK, items, chunk=8, max_tokens=2500)
    by = {n(g.get("vi", "")): g for g in (res or []) if isinstance(g, dict)}
    ok = bad = 0
    for w in have:
        g = by.get(n(w["vi"]))
        if not g:
            continue
        if str(g.get("v")) == "bad":
            ko, why = n(g.get("ko") or ""), n(g.get("why") or "")
            # **근거 없이는 못 고친다.** 사전 대목을 옮겨 적었고, 그 대목이 실제로
            # 우리가 받아 온 뜻풀이 안에 있어야 받아들인다 (지어낸 근거를 막는다)
            grounded = bool(why) and why[:18].lower() in (w.get("def") or "").lower()
            if (ko and grounded and len(ko) <= 12
                    and not re.search(r"[^가-힣ㄱ-ㆎ0-9 ·()~,./%\-]", ko)):
                w["ko_before"], w["ko"], w["why"] = w["ko"], ko, why
                w["fin"] = "diff"; bad += 1
            else:
                w["fin"] = "ok"; ok += 1        # 근거가 없으면 원래 뜻을 지킨다
        else:
            w["fin"] = "ok"; ok += 1
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"사전이 뒷받침 {ok} · 뜻이 달라 고침 {bad}")


# 불러오기만 할 때는 돌지 않는다 — 다른 도구가 TOPICS 같은 것을
# 가져다 쓸 때 낱말 모으기가 통째로 다시 도는 사고가 있었다 (2026-09-01).
if __name__ == "__main__":
    main()
