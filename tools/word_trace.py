#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""선배 시험지의 **낱말 하나하나가 어떻게 되었는지** 표로 만든다 → docs/word-trace.tsv

대표님 지시 (2026-08-30): "다시 선배들 단어 처음부터 끝까지 모든 파일 다 체크해서 가져와.
그리고 완전히 중복되는 단어만 빼. 뜻은 같고 단어가 다른건 다 추가해야지."

그래서 **건너뛰지 않고** 시험지에 적힌 모든 (베트남어, 뜻) 짝을 세고,
빠진 것마다 **왜 빠졌는지**를 한 줄씩 적는다. 눈으로 확인할 수 있어야 한다.
쓰기: python3 tools/word_trace.py
"""
import collections, json, pathlib, re, sys, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import senior_merge as M, senior_hand as H

def main():
    raw = []                       # (기수, 파일, 베트남어, 뜻)
    for gi in ("17", "18", "19", "20"):
        p = R / "data" / f"_senior_scan-{gi}.json"
        if not p.exists(): continue
        for f in json.loads(p.read_text(encoding="utf-8"))["files"]:
            for row in f["rows"]:
                raw.append((gi, f["src"], f["kind"], row.get("vi", ""), row.get("ko", ""),
                            row.get("en", "")))
    print(f"시험지에 적힌 줄 {len(raw)}개")

    # ① 낱말 꼴로 다듬기 + 문장·토막 거르기 (senior_merge 와 같은 잣대)
    kept, why = {}, collections.Counter()
    lines = ["기수\t파일\t원래 베트남어\t원래 뜻\t다듬은 낱말\t다듬은 뜻\t결과"]
    for gi, src, kind, vi0, ko0, en0 in raw:
        vi, ko, en = M.norm(vi0), M.clean_ko(ko0), (en0 or "").strip()
        res = ""
        if not M.is_word(vi, ko, en, vi0):
            res = "문장·토막"
        elif not ko and not en:
            res = "뜻 없음"
        if res:
            why[res] += 1
            lines.append(f"{gi}\t{src}\t{vi0}\t{ko0}\t{vi}\t{ko}\t{res}")
            continue
        kept.setdefault(vi, {"vi": vi0.strip(), "ko": ko, "src": []})["src"].append((gi, src))
        lines.append(f"{gi}\t{src}\t{vi0}\t{ko0}\t{vi}\t{ko}\t남김")
    print(f"  걸러진 줄: {dict(why)}")
    print(f"  남은 **서로 다른 낱말** {len(kept)}개")

    # ② 완전히 같은 낱말만 합치는지 확인
    #    (성조·모자·대소문자·괄호만 다른 것 = 같은 낱말. 그 밖은 다른 낱말.)
    g = collections.defaultdict(list)
    for k, v in kept.items():
        key = (H.bare(v["vi"]), v["ko"]) if v["ko"] else ("\0" + v["vi"], "")
        g[key].append(v["vi"])
    same = {k: v for k, v in g.items() if len(v) > 1}
    print(f"  **완전히 같은 낱말**(뼈대·뜻 둘 다 같음) 무리 {len(same)}개 → 합치면 {sum(len(v)-1 for v in same.values())}개 줄어듦")
    for k, v in list(same.items())[:10]: print("     ", " = ".join(v), f"({k[1][:14]})")

    # ③ 뜻만 같고 낱말이 다른 것은 **몇 개인가** (이건 절대 안 지운다)
    byko = collections.defaultdict(set)
    for v in kept.values(): byko[v["ko"]].add(H.bare(v["vi"]))
    syn = {k: v for k, v in byko.items() if len(v) > 1}
    print(f"  뜻은 같지만 **낱말이 다른** 무리 {len(syn)}개 · 그 안의 낱말 {sum(len(v) for v in syn.values())}개 — 이건 전부 남긴다")
    (R / "docs" / "word-trace.tsv").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n낱말마다 한 줄씩 → docs/word-trace.tsv ({len(lines)-1}줄)")
main()
