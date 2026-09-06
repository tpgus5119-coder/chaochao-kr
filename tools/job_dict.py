#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""직무 낱말을 **사전에 대조**해서 낱말인지 가려낸다 → data/_jobdict.json

대표님 지시 (2026-08-31): "사전에 대조해서 있는건지 없는건지 체크하면안됨?
                         일단 우리 어플 내의 사전을 활용하고 거기에 해당안되는 단어들은
                         인터넷 사전과 대조해서... 최대한 토큰 소모 덜 하는 방법으로."

## 세 단계로 거른다 — 뒤로 갈수록 비싸다
  ① 우리 사전            data/_vi_ipa.json(5,381) · exgloss.json · 일상 낱말
                         → 있으면 '낱말 맞다'. 돈도 시간도 안 든다
  ② 위키낱말(무료 API)    vi.wiktionary.org 에 **베트남어 표제어**로 있나
                         → 있으면 낱말, 영어 표제어뿐이면 '영어'
  ③ 남은 것만 AI 에게      ①②로 못 가른 것만 Qwen 에게 묻는다
                         → 사전에 없는 것은 **전문 복합어**(품질관리)이거나 **구**(일정을 짜다)라
                           둘을 가르려면 판단이 필요하다

이렇게 하면 AI 에게 묻는 양이 크게 준다.
(실측: 위키낱말은 công ty·khay 를 표제어로, vendor 를 '영어', xếp lịch công tác·gắn ngược 를
 '없음' 으로 정확히 가려냈다. 다만 kiểm soát chất lượng 같은 **멀쩡한 전문 복합어도 '없음'** 이라
 그 갈래는 ③이 필요하다.)

쓰기: python3 tools/job_dict.py            # ①②만 (공짜)
      python3 tools/job_dict.py --ai       # ③까지
"""
import argparse, json, pathlib, subprocess, sys, time, unicodedata as U, urllib.parse

R = pathlib.Path(__file__).resolve().parent.parent
OUT = R / "data" / "_jobdict.json"
API = "https://vi.wiktionary.org/w/api.php?action=parse&prop=wikitext&format=json&page="

n = lambda s: U.normalize("NFC", str(s)).strip().lower()


def ours():
    """우리가 이미 가진 낱말 — 여기 있으면 더 볼 것 없다."""
    s = set()
    for f in ("_vi_ipa.json", "exgloss.json"):
        p = R / "data" / f
        if p.exists():
            s |= {n(k) for k in json.loads(p.read_text(encoding="utf-8"))}
    O = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))

    def walk(v):
        for t in (v.get("tracks") or [v]):
            for c in t["chapters"]:
                for l in c["lessons"]:
                    yield from l["words"]
    s |= {n(w["vi"]) for v in O["vols"] if v.get("kind") != "job" for w in walk(v)}
    return s


def wik(w, cache):
    """위키낱말에 베트남어 표제어로 있나. 한 번 본 것은 다시 안 묻는다."""
    k = n(w)
    if k in cache: return cache[k]
    try:
        r = subprocess.run(["curl", "-sS", "-m", "15", API + urllib.parse.quote(w)],
                           capture_output=True, text=True, timeout=25).stdout
        j = json.loads(r)
        if "error" in j: v = "없음"
        else:
            t = j["parse"]["wikitext"]["*"]
            v = "낱말" if ("Tiếng Việt" in t or "{{-vie-}}" in t) else "영어"
    except Exception:
        v = "실패"
    cache[k] = v
    time.sleep(0.25)                       # 무료 API 라 너무 빨리 두드리지 않는다
    return v


def jobwords():
    O = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    out = []
    for v in O["vols"]:
        if v.get("kind") != "job": continue
        for t in v["tracks"]:
            for c in t["chapters"]:
                for l in c["lessons"]:
                    out += l["words"]
    return out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--ai", action="store_true", help="사전으로 못 가른 것을 Qwen 에게 묻는다")
    a.add_argument("--limit", type=int, default=0)
    a = a.parse_args()

    job = jobwords()
    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    mine = ours()
    todo = [w for w in job if w["vi"] not in have]
    if a.limit: todo = todo[:a.limit]
    print(f"직무 낱말 {len(job)} · 볼 것 {len(todo)}", flush=True)

    cache = {}
    for i, w in enumerate(todo, 1):
        vi = w["vi"]
        if n(vi) in mine:
            have[vi] = {"how": "우리사전", "v": "낱말", "ko": w["ko"]}
        else:
            have[vi] = {"how": "위키낱말", "v": wik(vi, cache), "ko": w["ko"]}
        if i % 50 == 0:
            OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {i}/{len(todo)}", flush=True)
    OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")

    from collections import Counter
    c = Counter(v["v"] for v in have.values())
    print(f"\n사전으로 가른 결과 (모두 {len(have)})")
    print(f"  낱말이 맞다      {c.get('낱말',0)}")
    print(f"  영어             {c.get('영어',0)}")
    print(f"  사전에 없음      {c.get('없음',0)}   ← 전문 복합어이거나 구. AI 가 갈라야 한다")
    print(f"  못 물어봄        {c.get('실패',0)}")

    if not a.ai:
        print("\n(--ai 를 주면 '사전에 없음' 만 Qwen 에게 묻는다)")
        return

    sys.path.insert(0, str(R / "tools"))
    from qwen import ask_json, up
    if not up():
        print("Qwen 이 안 켜져 있다"); return
    rest = [(k, v) for k, v in have.items() if v["v"] == "없음" and "판정" not in v]
    print(f"\nAI 에게 물을 것 {len(rest)}개")
    ASK = ("아래는 사전에 표제어가 없는 베트남어 공장 용어다. 둘 중 하나로 갈라라.\n"
           "  term   : 현장에서 **하나의 용어**로 굳어 쓰는 말 (kiểm soát chất lượng=품질관리)\n"
           "  phrase : 그때그때 만들어 쓰는 구·문장 (xếp lịch công tác=출장 일정을 짜다)\n"
           '출력은 JSON 배열만: [{"vi":"낱말","v":"term|phrase"}]\n\n')
    got = ask_json(ASK, [{"vi": k, "ko": v["ko"]} for k, v in rest], chunk=20)
    by = {g.get("vi"): g.get("v") for g in got if isinstance(g, dict)}
    for k, v in rest:
        have[k]["판정"] = by.get(k) or "term"
    OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
    c2 = Counter(v.get("판정") for v in have.values() if v.get("판정"))
    print(f"  하나의 용어 {c2.get('term',0)} · 구·문장 {c2.get('phrase',0)}")


main()
