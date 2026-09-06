#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""기수 폴더의 **모든 파일**을 열어 무엇이 들었는지 적는다 → data/_senior_scan-{기수}.json

왜 만들었나 (2026-08-30): 이름만 보고 거른 탓에 회차를 놓쳤다.
  · 「답안」이라 적혀 있어도 **뜻 칸이 비어 있는** 판이 있다(17기). 낱말만 건진다.
  · 뜻이 **영어**로 된 판이 있다(18기 8·9회차 등). 버리지 말고 영어를 받아 둔다.
  · 스캔 그림은 글자층이 없다 — 이것만 진짜로 못 쓴다.
쓰기: python3 tools/senior_scan.py 17 18 19 20
"""
import json, os, pathlib, re, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import senior18 as S

R = pathlib.Path(__file__).resolve().parent.parent
EN = re.compile(r"^[A-Za-z][A-Za-z .,'\-/()]*$")
# **시험지가 아닌 것** — 이름에 '단어'가 들어 있어 시험지로 찍히지만 시험지가 아니다.
#   '생산관리 카톡방 단어 정리' 는 선배들이 일터 단톡방에서 쓴 말을 모은 표다(2026-08-30, 대표님 지적).
#   기수·회차가 없으므로 **차례를 매기는 데 섞이면 안 된다.** 따로 표시해 둔다.
# 파일 779개를 하나씩 열어 보고 추린 목록(2026-08-30). **시험지가 아닌 것**은
#   회차가 없어 차례를 매길 수 없다. 기수 순서에 섞이면 순서가 거짓이 된다.
NOTEST = re.compile(r"카톡|생산관리|용어|정리\.xlsx$|Q&A|교재_단어|함수양식|총합|자체제작")

def rows_xlsx_lean(p):
    """15MB 짜리 엑셀이 있다 — 통째로 열면 메모리가 터진다. 읽기전용 + 줄 제한."""
    import openpyxl
    out = []
    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    for ws in wb.worksheets:
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i > 4000: break
            cells = [("" if c is None else str(c).strip()) for c in r[:12]]
            if any(cells): out.append(cells)
    wb.close()
    return out


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def rows_docx(p):
    """docx 를 **덧붙인 꾸러미 없이** 읽는다 — docx 는 그냥 zip 안의 XML이다.
       (python-docx 를 안 깐 컴퓨터에서 38개가 통째로 조용히 빠졌었다. 2026-08-30)"""
    import zipfile, xml.etree.ElementTree as ET
    out = []
    with zipfile.ZipFile(p) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    def txt(node):
        return "".join(t.text or "" for t in node.iter(W + "t")).strip()
    for tbl in root.iter(W + "tbl"):
        for tr in tbl.iter(W + "tr"):
            cells = [txt(tc) for tc in tr.iter(W + "tc")]
            if any(cells): out.append(cells)
    if not out:                      # 표가 없으면 문단이라도
        for pr in root.iter(W + "p"):
            t = txt(pr)
            if t: out.append([t])
    return out


def cells_of(p):
    f = p.name.lower()
    if f.endswith((".xlsx", ".xls")): return rows_xlsx_lean(p)
    if f.endswith(".docx"): return rows_docx(p)
    return S.rows_pdf(p)

# ── 머리글로 열 짝을 찾는다 ────────────────────────────────────────────────
# 시험지 대부분이 「No.|단어|뜻」 묶음을 **가로로 두세 벌** 늘어놓는다.
# 한 행을 한 낱말로 읽으면 네 낱말이 한 덩어리가 되어 뜻이 어긋난다.
#   'còn cô tay đầu bếp | 반면에 / 여자 선생님 / 손 / 요리사'  ← 이렇게 망가졌었다 (2026-08-30 발견)
# 열 차례도 파일마다 다르다: 「No.|단어|뜻」 과 「No.|뜻|단어」 가 섞여 있다.
HV = re.compile(r"^(단어|베트남어|từ|tiếng việt|vietnam\w*)$", re.I)
HK = re.compile(r"^(뜻|의미|한국어|nghĩa|korea\w*)$", re.I)
HE = re.compile(r"^(영어|english|nghĩa tiếng anh)$", re.I)

def col_pairs(cells):
    """머리글 한 줄에서 (단어열, 뜻열, 영어열) 짝들을 낸다. 못 찾으면 빈 목록."""
    tags = [("v" if HV.fullmatch(c) else "k" if HK.fullmatch(c) else
             "e" if HE.fullmatch(c) else "") for c in cells]
    if sum(1 for t in tags if t in "vk") < 2: return []
    pairs, cur = [], {}
    for i, t in enumerate(tags):
        if not t: continue
        if t in cur:                       # 같은 갈래가 또 나오면 새 묶음이다
            if "v" in cur and "k" in cur: pairs.append(cur)
            cur = {}
        cur[t] = i
    if "v" in cur and "k" in cur: pairs.append(cur)
    return pairs

def split_wide(rows):
    """머리글이 있으면 열 짝대로, 없으면 빈 목록(= 옛 방식으로 넘긴다)."""
    out, pairs = [], []
    for line in rows:
        cs = [(c or "").strip() for c in line]
        p = col_pairs(cs)
        if p: pairs = p; continue          # 머리글 줄 — 짝을 새로 잡고 넘어간다
        if not pairs: continue
        for q in pairs:
            vi = cs[q["v"]] if q["v"] < len(cs) else ""
            ko = cs[q["k"]] if q["k"] < len(cs) else ""
            en = cs[q["e"]] if "e" in q and q["e"] < len(cs) else ""
            vi = re.sub(r"\s+", " ", vi).strip()
            if not vi or not re.search(r"[A-Za-zÀ-ỹ]", vi): continue
            if re.fullmatch(r"[\d.\s]+", vi): continue
            # 칸이 뒤바뀐 판이 있다 — 한글이 단어칸에 있으면 맞바꾼다
            if S.KO.search(vi) and not S.KO.search(ko): vi, ko = ko, vi
            if not vi: continue
            out.append((vi, re.sub(r"\s+", " ", ko).strip(), en.strip()))
    return out

def split(rows):
    """줄마다 (베트남어, 한글뜻, 영어뜻) 을 낸다. 없으면 빈 칸."""
    w = split_wide(rows)
    if w: return w                          # 머리글이 있으면 열 짝대로 읽는다
    out = []
    for line in rows:
        cells = [c.strip() for c in line if c and c.strip()]
        if len(cells) < 2: continue
        j = " ".join(cells)
        if re.match(r"^\s*(No\.?|단어|뜻|날짜|이름|번호|STT)", j): continue
        ko = [c for c in cells if S.KO.search(c)]
        rest = [c for c in cells if not S.KO.search(c) and re.search(r"[A-Za-zÀ-ỹ]", c)
                and not re.fullmatch(r"[\d.\s]+", c)]
        vi = [c for c in rest if S.VI.search(c)]
        en = [c for c in rest if not S.VI.search(c) and EN.match(c)]
        if not vi and rest: vi = rest[:1]; en = [c for c in rest[1:] if EN.match(c)]
        if not vi: continue
        out.append((" ".join(vi).strip(), " / ".join(ko).strip(), " / ".join(en).strip()))
    return out

def main():
    for gi in sys.argv[1:]:
        D = [x for x in S.BASE.iterdir() if x.is_dir() and x.name.startswith(gi)][0]
        recs, why = [], collections.Counter()
        for f in sorted(os.listdir(D)):
            if f.startswith(".") or not f.lower().endswith((".pdf",".xlsx",".xls",".docx")):
                why["시험지 아님(소리·그림 등)"] += 1; continue
            try: rows = cells_of(D / f)
            except Exception as e: why[f"못 읽음 {type(e).__name__}"] += 1; continue
            if not rows: why["스캔 그림(글자층 없음)"] += 1; continue
            ws = split(rows)
            if len(ws) < 5: why["낱말 5개 미만"] += 1; continue
            nk = sum(1 for _, k, _ in ws if k)
            ne = sum(1 for _, _, e in ws if e)
            tone = sum(1 for v, _, _ in ws if S.VI.search(v)) / len(ws)
            kind = ("한글" if nk >= len(ws) * .5 else "영어" if ne >= len(ws) * .5 else "낱말만")
            if tone < .25 and len(ws) >= 15: why["베트남어 아님"] += 1; continue
            lab = S.label(f) or ("일일", 0)
            if NOTEST.search(f): lab = ("모음집", 0)          # 시험지가 아님
            recs.append({"src": f, "kind": lab[0], "no": lab[1], "meaning": kind,
                         "rows": [{"vi": v, "ko": k, "en": e} for v, k, e in ws]})
        (R / "data" / f"_senior_scan-{gi}.json").write_text(
            json.dumps({"gi": gi, "files": recs}, ensure_ascii=False, indent=1), encoding="utf-8")
        c = collections.Counter(r["meaning"] for r in recs)
        print(f"{gi}기 · 읽은 파일 {len(recs)} · 낱말자리 {sum(len(r['rows']) for r in recs)} · 뜻갈래 {dict(c)}")
        print("   못 쓴 파일:", dict(why))

main()

# 남은 빠짐 (2026-08-30, 확인 끝)
#  · 17기 41·46·49·57·63·85회차 — **공란본밖에 없다**. 뜻만 있고 베트남어 칸이 비었다.
#    답안본이 폴더에 없다 → 되살릴 방법이 없다. (뜻만으로 낱말을 지어내지 않는다)
#  · 20기 2회차 — 베트남어 칸이 영어로 된 판만 있다.
#  · 18기 '단어 총합 정답지.xlsx' · '05.23 주간복습' — **인도네시아어**다(da-da·ubi·singkong).
#  · 19기 'Tiếng Việt CS Q3·Q4.pdf' — 교재 스캔이라 글자층이 없다.
#    다만 **목차는 눈으로 읽어 두었다** (Nguyễn Việt Hương, 각 권 12과 = 5과+복습 두 묶음).
#  · 그 밖의 안 쓴 공란본은 같은 회차 답안본이 있어서 안 쓴 것 — 빠진 게 아니다.
