#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""17·18기 단어시험을 읽는다 → data/_senior_words-{기수}.json

19·20기와 다른 점 (2026-08-30)
  · **PDF가 221개**다. 19·20기는 엑셀·워드뿐이었다.
  · 이름 규칙이 제각각이다: (단어)·(답안)·(문제)·(공란)·(공부)·(암기용) …
    - **(문제)·(공란) 은 빈 시험지**다 — 뜻만 있고 낱말이 비어 있다. 버린다.
    - **(단어)·(답안)** 이 쓸모 있다. 낱말과 뜻이 다 있다.
  · 칸 차례가 파일마다 다르다: `단어|뜻` 도 있고 `뜻|단어` 도 있다.
    한글이 든 칸을 '뜻'으로, 베트남 글자가 든 칸을 '낱말'로 **내용을 보고** 가른다.
  · 같은 회차가 pdf·xlsx 로 두 번 있다 — 회차별로 하나만 남긴다.

인도네시아어 섞임: 19기에서 겪은 일이라 여기서도 본다(성조 부호 비율로).
쓰기: python3 tools/senior18.py --gi 18 [--report]

19·20기는 tools/senior_words.py 가 읽는다(엑셀·워드만이라 짜임이 다르다).
"""
import argparse, json, os, pathlib, re, unicodedata, collections

R = pathlib.Path(__file__).resolve().parent.parent
BASE = pathlib.Path(os.path.expanduser("~/Downloads/베트남어 학습자료/선배 자료"))
D = None                    # --gi 로 정한다
KO = re.compile(r"[가-힣]")
VI = re.compile(r"[ăâđêôơưàáảãạằắẳẵặầấẩẫậèéẻẽẹềếểễệìíỉĩịòóỏõọồốổỗộờớởỡợùúủũụừứửữựỳýỷỹỵ]", re.I)
# 빈 시험지 — 괄호 없이 적힌 것도 있고 베트남어로 câu hỏi 라 적힌 것도 있다
BLANK = re.compile(r"문제|공란|câu\s*hỏi|kiểm\s*tra", re.I)
WEEK = re.compile(r"토요|주간|주차|복습")


def rows_pdf(p):
    """**표 칸 단위**로 읽는다. 글자 상자를 y 로 묶던 옛 방식은 낱말을 잘랐다:
       좁은 칸에서 'phân biệt' 가 두 줄로 그려지면 'biệt' 만 남는다.
       (2026-08-30 검수에서 an·ban·biệt·biểu 따위 토막이 무더기로 나왔다)
       411개 중 406개에서 표가 잡힌다. 안 잡히는 것만 옛 방식으로 넘긴다."""
    import pymupdf
    out = []
    doc = pymupdf.open(p)
    for pg in doc:
        got = False
        try:
            for t in pg.find_tables().tables:
                rows = t.extract()
                if len(rows) < 4: continue
                got = True
                for r in rows:
                    cells = [re.sub(r"\s+", " ", (c or "")).strip() for c in r]
                    if any(cells): out.append(cells)
        except Exception:
            pass
        if got: continue
        words = pg.get_text("words")          # 표가 없는 쪽 — 글자 상자를 y 로 묶는다
        by = collections.defaultdict(list)
        for w in words:
            by[round(w[1] / 6)].append((w[0], w[4]))
        for k in sorted(by):
            line = [t for _, t in sorted(by[k])]
            if line: out.append(line)
    doc.close()
    return out


def rows_xlsx(p):
    import openpyxl
    out = []
    wb = openpyxl.load_workbook(p, data_only=True)
    for ws in wb.worksheets:
        for r in ws.iter_rows(values_only=True):
            cells = [("" if c is None else str(c).strip()) for c in r]
            if any(cells): out.append(cells)
    return out


def pairs(rows):
    """줄마다 한글 칸과 베트남어 칸을 **내용으로** 가른다."""
    out = []
    for line in rows:
        cells = [c for c in line if c and c.strip()]
        if len(cells) < 2: continue
        joined = " ".join(cells)
        if re.match(r"^\s*(No\.?|단어|뜻|날짜|이름|단어\s*테스트)", joined): continue
        ko = [c for c in cells if KO.search(c)]
        vi = [c for c in cells if not KO.search(c) and re.search(r"[A-Za-zÀ-ỹ]", c)
              and not re.fullmatch(r"[\d.\s]+", c)]
        if ko and vi:
            out.append((" ".join(vi).strip(), " / ".join(ko).strip()))
    return out


def label(name):
    """쓸 파일인가, 어느 회차인가.
       이름 규칙이 열 가지가 넘는다 — `56회 답안.pdf` `65회차.xlsx` `240208(토)_아침 복습 단어`
       `베트남18기단어복습테스트_250315` … 그래서 **'시험지 같으면 일단 읽고**
       내용에 낱말이 없으면 그때 버린다'로 바꿨다. 이름으로 미리 자르니 26개를 놓쳤다."""
    n = name
    if BLANK.search(n): return None
    if not re.search(r"단어|시험|테스트|답안|답지|회차|\d+회|\d+차", n): return None
    kind = "주간" if WEEK.search(n) else "일일"
    m = re.search(r"(\d+)\s*(?:회차|회|차)", n)
    if m: return (kind, int(m.group(1)))
    # 번호가 없으면 날짜를 번호 대신 쓴다 (같은 날 것끼리 묶인다)
    dt = re.search(r"(2\d{5})|(\d{4})[_\-(]", n)
    return (kind, int((dt.group(1) or dt.group(2))[-4:]) if dt else 0)


def main():
    global D
    ap = argparse.ArgumentParser(); ap.add_argument("--report", action="store_true")
    ap.add_argument("--gi", default="18")
    a = ap.parse_args()
    cands = [x for x in BASE.iterdir() if x.is_dir() and x.name.startswith(a.gi)]
    if not cands: raise SystemExit(f"{a.gi}기 폴더를 못 찾음")
    D = cands[0]
    seen, sets, skip, noviet = {}, [], collections.Counter(), []
    for f in sorted(os.listdir(D)):
        if f.startswith("."): continue
        lab = label(f)
        if not lab: skip[("빈 시험지" if BLANK.search(f) else "갈래 모름")] += 1; continue
        p = D / f
        try:
            rows = rows_xlsx(p) if f.lower().endswith((".xlsx", ".xls")) else rows_pdf(p)
        except Exception as e:
            skip["못 읽음"] += 1; continue
        if not rows: skip["스캔 그림(글자층 없음)"] += 1; continue
        ws = pairs(rows)
        if len(ws) < 5: skip["낱말이 너무 적음"] += 1; continue
        # 인도네시아어 검사 — 성조 부호가 거의 없으면 베트남어가 아니다
        tone = sum(1 for v, _ in ws if VI.search(v)) / len(ws)
        if len(ws) >= 15 and tone < 0.25:
            skip["베트남어 아님(인도네시아어·영어)"] += 1
            noviet.append(f)
            continue
        key = lab
        if key in seen and len(seen[key][1]) >= len(ws): continue   # 더 많은 쪽을 남긴다
        seen[key] = (f, ws)
    for (kind, no), (f, ws) in sorted(seen.items(), key=lambda x: (x[0][0] != "일일", x[0][1])):
        sets.append({"kind": kind, "no": no, "src": f,
                     "words": [{"vi": v, "ko": k} for v, k in ws]})
    out = {"note": f"{a.gi}기 단어시험. 빈 시험지((문제)·(공란))는 뺐고, 회차마다 낱말이 가장 많은 판 하나만 남겼다.",
           "sets": sets}
    (R / "data" / f"_senior_words-{a.gi}.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    tot = sum(len(s["words"]) for s in sets)
    print(f"{a.gi}기 — 묶음 {len(sets)}개 · 낱말 자리 {tot}")
    print("  갈래:", dict(collections.Counter(s['kind'] for s in sets)))
    print("  건너뛴 파일:", dict(skip))
    if noviet: print("  베트남어가 아니라 뺀 파일:", [x[:40] for x in noviet])
    if a.report:
        for s in sets[:10]: print(f"   {s['kind']} {s['no']:>3} · {len(s['words']):>3}개 · {s['src'][:44]}")


if __name__ == "__main__":
    main()
