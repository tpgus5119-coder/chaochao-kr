#!/usr/bin/env python3
"""「베트남어 100일의 기적」 선배 정리본(스크린샷 15장)을 글로 뽑는다.

  python3 tools/hundred_days.py            → docs/hundred-days.md
  python3 tools/hundred_days.py --json     → data/_hundred_days.json 도

무엇인가: 시중에 파는 책이다. 20기 선배가 Day1~13에 걸쳐 **문장 100개**를 카페에
정리해 올린 것을 화면으로 담아 둔 자료다. 낱말이 아니라 **통문장**이다.

OCR 이 표를 **열 단위로 세로로** 읽는다. 그래서 한 쪽이 이렇게 나온다:
    [머리말] → [번호 1..20] → '베트남어' → [문장 20개] → '한글뜻' → [뜻 20개]
세 덩이를 잘라 짝지어 되살린다.

**성조가 날아간다.** 화면 글꼴 탓에 `Chúc ngủ ngon` 이 `Chuc ngu ngon` 으로 읽힌다.
그래서 **한국어 뜻을 열쇠로** 삼고, 베트남어는 '성조 확인 필요'로 표시해 둔다.
쓰려면 성조를 사람이 채워야 한다 — 성조가 틀린 베트남어는 다른 낱말이 된다.
"""
import argparse
import json
import os
import pathlib
import re
import subprocess

R = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path(os.path.expanduser(
    "~/Downloads/베트남어 학습자료/선배 자료/100일의 기적"))
OCR = R / "tools" / "ocr"
KO = re.compile(r"[가-힣]")


def ocr_pages():
    out = []
    for f in sorted(SRC.glob("*.png")):
        r = subprocess.run([str(OCR), str(f)], capture_output=True, text=True)
        out.append((f.name, r.stdout))
    return out


def parse(text):
    """한 쪽에서 (번호, 베트남어, 한국어) 를 뽑는다."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    lines = [l for l in lines if not l.startswith("=== ")]
    day = None
    for l in lines[:4]:
        m = re.search(r"DAY\s*(\d+)", l, re.I)
        if m:
            day = int(m.group(1))
            break
    # 덩이 나누기 — '베트남어' 와 '한글뜻' 이 칸막이 노릇을 한다
    try:
        a = next(i for i, l in enumerate(lines) if l.replace(" ", "") == "베트남어")
        b = next(i for i, l in enumerate(lines) if l.replace(" ", "") in ("한글뜻", "한국어뜻"))
    except StopIteration:
        return day, []
    nums = [int(l) for l in lines[:a] if re.fullmatch(r"\d{1,3}", l)]
    vis = [l for l in lines[a + 1:b] if l and not KO.search(l) and "URL" not in l]
    kos = [l for l in lines[b + 1:] if KO.search(l) and "댓글" not in l and "URL" not in l]
    n = min(len(vis), len(kos))
    if not n:
        return day, []
    # 번호는 OCR 이 빠뜨리기도 한다(1장에서 11을 놓쳤다) — 뜻 개수를 기준으로 맞춘다
    nums = nums[:n] if len(nums) >= n else list(range(1, n + 1))
    return day, list(zip(nums, vis[:n], kos[:n]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not SRC.exists():
        raise SystemExit(f"자료가 없다: {SRC}")

    rows, pages = {}, ocr_pages()
    per = []
    for name, txt in pages:
        day, got = parse(txt)
        per.append((name, day, len(got)))
        for no, vi, ko in got:
            if no not in rows or not rows[no][0]:
                rows[no] = (vi, ko, day)

    L = ["# 「베트남어 100일의 기적」 — 선배 정리본", ""]
    L.append(f"자료: 화면 {len(pages)}장 (`{SRC.name}`). 시중에 파는 책을 20기 선배가")
    L.append("카페에 Day1~13으로 나눠 정리한 것을 담아 둔 것이다.")
    L.append("")
    L.append(f"**낱말이 아니라 통문장 {len(rows)}개**다. 단어시험과 성격이 다르다.")
    L.append("")
    L.append("> 성조가 OCR 에서 날아갔다(`Chúc ngủ ngon` → `Chuc ngu ngon`).")
    L.append("> 아래 베트남어는 **성조를 사람이 채워야 쓸 수 있다.** 한국어 뜻은 정확하다.")
    L.append("")
    L.append("| 화면 | Day | 뽑은 문장 |")
    L.append("|---|---:|---:|")
    for name, day, n in per:
        L.append(f"| {name[-12:]} | {day if day else '?'} | {n} |")
    L.append("")
    L.append("## 문장")
    L.append("")
    L.append("| # | 베트남어 (성조 확인 필요) | 한국어 |")
    L.append("|---:|---|---|")
    for no in sorted(rows):
        vi, ko, _ = rows[no]
        L.append(f"| {no} | {vi} | {ko} |")
    L.append("")
    miss = sorted(set(range(1, (max(rows) if rows else 0) + 1)) - set(rows))
    if miss:
        L.append(f"**빠진 번호**: {', '.join(map(str, miss))}")
        L.append("")

    out = "\n".join(L)
    (R / "docs" / "hundred-days.md").write_text(out + "\n", encoding="utf-8")
    print(f"문장 {len(rows)}개 · 화면 {len(pages)}장 → docs/hundred-days.md")
    if miss:
        print("빠진 번호:", miss)
    if a.json:
        p = R / "data" / "_hundred_days.json"
        p.write_text(json.dumps(
            {"note": "100일의 기적(시판 책) 선배 정리본. 성조 확인 필요. 앱에 아직 안 넣음.",
             "rows": [{"no": n, "vi": rows[n][0], "ko": rows[n][1], "day": rows[n][2]}
                      for n in sorted(rows)]}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"→ {p}")


if __name__ == "__main__":
    main()
