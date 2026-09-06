#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""듣기 대본 길이 — 공식 대본과 우리 것을 같은 자로 잰다.

**왜 도구로 굳히나.** 이 값을 세 번 틀렸다.
  ① "우리 1,022자 대 공식 1,666자" — 둘 다 틀린 값이었다. 공식 쪽은 음원을
     받아 적은 것이라 **안내 방송과 두 번 읽기가 섞여** 부풀었다.
  ② 다시 잴 때 정규식을 `(남자|여자)\\s*[:：]\\s*([^\\n]+)` 로 썼다. PDF 를 글자로
     바꾼 파일은 한 대사가 **여러 줄로 접혀** 있어서 첫 줄만 세고 말았다.
     그래서 공식 최대 대사를 32자로 읽었는데 실제로는 158자였다.
  ③ 그 틀린 값으로 "우리가 너무 길다"고 판단할 뻔했다.
손으로 재면 또 틀린다. 그래서 도구로 만든다.

세는 법: 문제지의 **듣기 대본**(듣기통합 판)에서 화자 표시로 턴을 끊고,
다음 화자 표시나 문항 번호가 나올 때까지를 한 턴으로 본다. 공백과 괄호는 뺀다.
(딩동댕) 같은 효과음도 뺀다 — 사람이 읽는 말이 아니다.

쓰기:  python3 tools/listen_len_check.py [기출텍스트폴더]
       폴더를 안 주면 ~/Documents/시험기출자료고/글자화-텍스트 를 본다.
"""
import glob
import json
import pathlib
import re
import statistics as st
import sys

R = pathlib.Path(__file__).resolve().parent.parent
DEF = pathlib.Path.home() / "Documents" / "시험기출자료고" / "글자화-텍스트"

SPK = re.compile(r"(남자|여자)\s*[:：]")
# 대사가 끝났다고 볼 줄 — 문항 번호·보기·머리글·쪽 번호
STOP = re.compile(r"^\s*(?:\d{1,2}\s*[.．]|※|\[\d|[①②③④lⅠ]\s|제\d+회|\)?TOPIK|\d+\s*$)")
DROP = re.compile(r"\(딩동댕\)|\(댕동딩\)|[\s()（）]")


def turns(t):
    """대사를 턴 단위로 끊는다. **여러 줄로 접힌 한 대사를 다시 잇는 것이 핵심.**"""
    out, cur = [], None
    for ln in t.splitlines():
        m = SPK.search(ln)
        if m:
            if cur is not None:
                out.append(cur)
            cur = ln[m.end():].strip()
        elif cur is not None:
            if STOP.match(ln) or not ln.strip():
                out.append(cur); cur = None
            else:
                cur += " " + ln.strip()
    if cur is not None:
        out.append(cur)
    return [x for x in (DROP.sub("", y) for y in out) if x]


def spread(v):
    v = sorted(v)
    q = lambda p: v[min(len(v) - 1, int(len(v) * p))]
    return dict(n=len(v), 합=sum(v), 중앙=st.median(v), 평균=round(st.mean(v), 1),
                하위25=q(.25), 상위25=q(.75), 상위10=q(.90), 최대=max(v))


def show(name, per_set):
    """per_set: [[턴 길이…], …] — 회차별"""
    flat = [x for s in per_set for x in s]
    if not flat:
        print(f"{name}: 잰 것 없음"); return None
    s = spread(flat)
    tot = [sum(x) for x in per_set]
    print(f"\n── {name} — {len(per_set)}회차")
    print(f"   회차당 턴 {round(st.mean([len(x) for x in per_set]))}개 · "
          f"글자 {min(tot)}~{max(tot)} (중앙 {st.median(tot):.0f})")
    print(f"   한 대사: 중앙 {s['중앙']:.0f}자 · 평균 {s['평균']} · "
          f"하위25% {s['하위25']} · 상위25% {s['상위25']} · 최대 {s['최대']}")
    for k in (40, 60, 100):
        print(f"   {k}자 초과 {100*sum(1 for x in flat if x > k)/len(flat):.1f}%", end="")
    print()
    return s


def main():
    src = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEF
    off = []
    for f in sorted(set(glob.glob(str(src / "*TOPIK1*듣기통합*.txt")))):
        off.append([len(x) for x in turns(pathlib.Path(f).read_text(
            encoding="utf-8", errors="ignore"))])
    o = show("공식 TOPIK I 듣기 대본", off)

    E = json.loads((R / "data" / "ko_exams.json").read_text(encoding="utf-8"))
    ex = E["exams"] if isinstance(E, dict) else E
    our = []
    for e in ex:
        if e["id"] != "topik-1":
            continue
        v = [len(re.sub(r"\s", "", str(a.get("t") if isinstance(a, dict) else a)))
             for q in e["questions"] for a in (q.get("audio") or [])]
        our.append([x for x in v if x])
    u = show("우리 topik-1", our)

    if o and u:
        print("\n── 견주면")
        for k in ("중앙", "평균", "하위25", "상위25", "최대"):
            d = (u[k] - o[k]) / o[k] * 100 if o[k] else 0
            mark = "  " if abs(d) <= 15 else " ←"
            print(f"   {k:>5}  공식 {o[k]:>5}  우리 {u[k]:>5}  {d:+6.0f}%{mark}")
        print("\n   ±15% 안이면 맞다고 본다(기출해부 검증표 기준).")
        print("   걸리는 곳은 **긴 쪽**이다. 짧은 대사(하위25%)는 공식과 거의 같은데,")
        print("   상위25%와 최대가 3분의 1 넘게 짧다 — 안내 방송·인터뷰·대담처럼")
        print("   한 사람이 길게 말하는 자리가 공식만큼 길지 않다는 뜻이다.")
        print("   짧은 대사를 늘릴 일이 아니라 **긴 자리만** 늘려야 한다.")


if __name__ == "__main__":
    main()
