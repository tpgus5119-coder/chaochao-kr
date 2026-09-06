#!/usr/bin/env python3
"""EPS-TOPIK **출제 규격**을 공개문제집 960문항에서 뽑는다.

  python3 tools/eps_spec.py            → 화면에
  python3 tools/eps_spec.py --md       → docs/eps-blueprint.md 로

우리는 모의고사를 **계속** 만들어야 한다. 그러려면 "무엇을 몇 개, 몇 자로"가
숫자로 있어야 한다. 감으로 만들면 회차마다 난이도가 출렁인다.

문항을 베끼지 않는다 — **세기만 한다.** 유형별 개수·보기 길이·어휘 등급은
사실이고, 사실에는 저작권이 없다.

공개문제집은 유형 구간이 글로 박혀 있다:
  [1~200] 그림 보고 고르기 · [201~480] 빈칸 · [481~800] 질문에 답하기 ·
  [921~960] 글 읽고 물음에 답하기
이 구간이 곧 **출제 비율**이다. 공단 출제기준(읽기 20문항)에 이 비율을 곱하면
한 회분에 유형마다 몇 개를 넣어야 하는지가 나온다.
"""
import argparse
import pathlib
import re
import statistics as st
import sys

R = pathlib.Path(__file__).resolve().parent.parent
A = pathlib.Path.home() / "Documents" / "시험기출자료고" / "글자화-텍스트"
sys.path.insert(0, str(R / "tools"))

# 보기 표시로 쓰인 글자 — PDF 에서 ①②③④ 가 이렇게 깨져 나온다
OPT = re.compile(r"[Ø][¾¿À`]")
# 지시문은 '…고르십시오 [1~200]' 꼴로 붙어 있다. 앞에 쪽 머리글(322 EPS-KLT)과
# 앞 문항 꼬리가 섞여 들어오므로, **마지막 문장 하나만** 남긴다.
# '답하시오'(801~920)처럼 어미가 다른 구간이 하나 있어 둘 다 받는다.
HEAD = re.compile(r"([^.?!]{4,60}?(?:십시오|하시오))\s*\[\s*(\d+)\s*[~∼\-\s]\s*(\d+)\s*\]")


def load(name):
    return (A / name).read_text(encoding="utf-8")


def sections(t):
    """유형 구간을 글에서 찾아 낸다 — 우리가 정한 게 아니라 문제집이 적어 둔 것."""
    out = []
    for m in HEAD.finditer(t.replace("\n", " ")):
        ins, a, b = m.group(1).strip(), int(m.group(2)), int(m.group(3))
        ins = re.sub(r"^.*?(?:EPS-KLT|읽기\d+|\d{3})\s*", "", ins).strip()
        if b > a and b - a < 500:
            out.append((a, b, re.sub(r"\s+", " ", ins)))
    return sorted(set(out))


def items(t):
    """번호 + 보기 넷을 캔다. 보기 길이가 이 시험의 난이도를 가장 잘 말한다."""
    lines = [l.strip() for l in t.split("\n")]
    cur, out = None, {}
    for l in lines:
        m = re.match(r"^(\d{1,3})\s+(.*)$", l)
        if m and 1 <= int(m.group(1)) <= 960:
            cur = int(m.group(1))
            out.setdefault(cur, [])
            l = m.group(2)
        if cur is None:
            continue
        for piece in OPT.split(l):
            piece = piece.strip()
            if 1 < len(piece) < 90 and re.search(r"[가-힣]", piece):
                out[cur].append(piece)
    return {k: v[:4] for k, v in out.items() if v}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", action="store_true")
    a = ap.parse_args()

    t = load("EPS960_본문읽기.txt")
    secs = sections(t)
    its = items(t)
    L = []
    L.append("# EPS-TOPIK 출제 규격 — 960문항을 세어서")
    L.append("")
    L.append("공단 출제기준: **읽기 20문항 50점 25분 · 듣기 20문항 50점 25분 · 합 40문항 100점 50분**")
    L.append("4지 선택형. 상대평가(제조업 60점 · 그 외 45점 · 어업특례 30점 P/F).")
    L.append("")
    L.append("## 읽기 — 유형별 몫")
    L.append("")
    L.append("| 구간 | 문항 | 몫 | 20문항에 넣을 수 | 지시문 |")
    L.append("|---|---:|---:|---:|---|")
    tot = sum(b - a + 1 for a, b, _ in secs)
    for a_, b_, ins in secs:
        n = b_ - a_ + 1
        share = n / tot
        L.append(f"| {a_}~{b_} | {n} | {share*100:.0f}% | **{round(share*20)}** | {ins} |")
    L.append(f"| 합 | {tot} | 100% | 20 | |")
    L.append("")

    L.append("## 보기 길이 — 유형마다 다르다")
    L.append("")
    L.append("| 구간 | 잰 문항 | 보기 길이 중앙 | 가장 긴 보기 | 넷 중 최장−최단 |")
    L.append("|---|---:|---:|---:|---:|")
    for a_, b_, _ in secs:
        opts = [o for k, v in its.items() if a_ <= k <= b_ for o in v]
        per = [v for k, v in its.items() if a_ <= k <= b_ and len(v) >= 2]
        if not opts:
            continue
        spread = [max(len(x) for x in v) - min(len(x) for x in v) for v in per]
        L.append(f"| {a_}~{b_} | {len(per)} | {st.median(len(o) for o in opts):.0f}자 | "
                 f"{max(len(o) for o in opts)}자 | {st.median(spread):.0f}자 |")
    L.append("")
    L.append("> **넷 중 최장−최단**이 중요하다. 이 값이 크면 긴 보기가 정답이라는 버릇이 생겨")
    L.append("> 읽지 않고도 맞힌다. 우리 문항도 이 값 안에 들어야 한다.")
    L.append("")

    out = "\n".join(L)
    print(out)
    if a.md:
        p = R / "docs" / "eps-blueprint.md"
        p.write_text(out + "\n", encoding="utf-8")
        print(f"\n→ {p}")


if __name__ == "__main__":
    main()
