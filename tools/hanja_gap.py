#!/usr/bin/env python3
"""한자어가 얼마나 모자란지 잰다.  실행: python3 tools/hanja_gap.py [--list 60]

잣대는 **공단이 공개한 EPS-TOPIK 공개문항**이다(~/eps-공개문제/*.txt,
tools/hwp_text.py 로 hwp 에서 뽑아 둔 것). 베껴 쓰지 않는다 — 세기만 한다.
낱말의 빈도는 사실이고, 사실에는 저작권이 없다.

베트남 학습자에게 한자어는 공짜 점수다(교육→giáo dục). 그 자리가 비면
가장 값진 자리를 버리는 것이라 따로 잰다.

주의 — 같은 잣대로 재라. 공개문항 파일에는 문제뿐 아니라 안내문·정답표·듣기
대본이 섞여 있고, 대본에는 '남:' '여:' 가 붙어 있다. 이걸 안 걷어내면 '남'이
22번 나온 한자어로 잡혀 비율이 부푼다(처음에 그렇게 나왔다).
"""
import argparse
import glob
import json
import os
import pathlib
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baseline_check as B                                       # noqa: E402

# 잣대는 **공식 두 가지를 함께** 쓴다. 공개문항만 쓰면 낱말 1,033개짜리 자라 흔들린다.
#  · 공개문항 30문항(2025)              — 시험이 어떻게 생겼는가
#  · EPS 표준교재 1권 388쪽             — 시험이 **어디서 나오는가**
#    공단이 직접 밝힌다: "100% 비공개 출제되며 「한국어표준교재」를 바탕으로 한다."
#    두 자료가 따로 재도 38.9% / 39.5% 로 맞아떨어진다.
ARCHIVE = pathlib.Path.home() / "Documents" / "시험기출자료고" / "글자화-텍스트"
OFF = pathlib.Path.home() / "eps-공개문제"
BOILER = re.compile(r"^(=====.*|고용허가제.*|\d{4} - \d+ -.*|읽기 \(\d+문항\)|"
                    r"듣기 \(\d+문항\)|\[?\d+~\d+\]?.*고르십시오\.?|정답|번호|문항|"
                    r".*정답과 지문.*)$", re.M)
SPK = re.compile(r"^\s*(남자?|여자?)\s*[:：]\s*", re.M)


def clean(t):
    return SPK.sub("", BOILER.sub("", t))


def our_texts(qs):
    out = []
    for q in qs:
        for k in ("stem", "passage", "script"):
            if isinstance(q.get(k), str):
                out.append(clean(q[k]))
        out += [c for c in (q.get("options") or []) if isinstance(c, str)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", type=int, default=30, help="빠진 한자어 몇 개까지 보일까")
    a = ap.parse_args()

    files = sorted(glob.glob(str(OFF / "*.txt"))) + \
        [p for p in glob.glob(str(ARCHIVE / "EPS표준교재*.txt"))
         if len(re.findall(r"[가-힣]", open(p, encoding="utf-8").read(200000))) > 1000]
    if not files:
        sys.exit(f"잣대가 없다: {OFF} 에 *.txt 가 없다.\n"
                 "  공개문제 자료실에서 hwp 를 받아 tools/hwp_text.py 로 뽑아 둘 것.")

    from kiwipiepy import Kiwi
    kiwi, lex = Kiwi(), B.nikl()
    base = B.profile([clean(open(p, encoding="utf-8").read()) for p in files], kiwi, lex)

    d = json.load(open(os.path.join(os.path.dirname(OFF.parts and __file__), "..",
                                    "data", "ko_exams.json"), encoding="utf-8"))
    groups = {}
    for e in d["exams"]:
        k = ("EPS" if e["id"].startswith("eps")
             else "KIIP" if e["id"].startswith("kiip") else "TOPIK")
        groups.setdefault(k, []).extend(our_texts(e["questions"]))

    print(f"잣대 · 공단 EPS 공개문항   낱말 {base['낱말수']:,}   한자어 {base['한자어']:>5.1f}%")
    ours = {}
    for k in ("EPS", "TOPIK", "KIIP"):
        if k not in groups:
            continue
        ours[k] = w = B.profile(groups[k], kiwi, lex)
        d_ = w["한자어"] - base["한자어"]
        print(f"우리 {k:<6}              낱말 {w['낱말수']:,}   한자어 {w['한자어']:>5.1f}%"
              f"   {d_:+5.1f}%p {'✗' if d_ < -3 else '✓'}")

    oh = {w: c for w, c in base["어휘"].items() if lex.get(w, ("", 0))[1]}
    for k, w in ours.items():
        miss = sorted(((x, c) for x, c in oh.items() if w["어휘"].get(x, 0) == 0),
                      key=lambda t: -t[1])
        print(f"\n■ 공단엔 있고 우리 {k} 엔 **한 번도 없는** 한자어 {len(miss)}개")
        print("  " + " · ".join(f"{x}({c})" for x, c in miss[:a.list]))


if __name__ == "__main__":
    main()
