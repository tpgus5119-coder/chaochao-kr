#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""선배 자료 폴더의 **파일 하나하나**가 무엇이고 어떻게 되었는지 적는다 → docs/file-audit.tsv

대표님 지시(2026-08-30): "파일 하나하나 다 확인하라".
앞서 딱지(kind)만 보고 '시험지'라 말했다가 틀렸다 — 「생산관리 카톡방 단어 정리」가
시험지로 찍혀 있었다. 그래서 **파일마다 안을 열어** 시험지인지 아닌지 직접 본다.
쓰기: python3 tools/file_audit.py
"""
import json, os, pathlib, re, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import senior_scan as SC, senior18 as S

R = pathlib.Path(__file__).resolve().parent.parent
BASE = S.BASE
ROUND = re.compile(r"(\d+)\s*(?:회차|회|차)")
BLANK = re.compile(r"문제|공란|câu\s*hỏi|kiểm\s*tra", re.I)

def look(p):
    """안을 열어 무엇인지 말한다."""
    f = p.name.lower()
    if f.endswith((".mp3", ".wav", ".m4a")): return "소리", 0, ""
    if f.endswith((".png", ".jpg", ".jpeg", ".gif")): return "그림", 0, ""
    if not f.endswith((".pdf", ".xlsx", ".xls", ".docx")): return "그 밖", 0, ""
    try: rows = SC.cells_of(p)
    except Exception as e: return f"못 읽음({type(e).__name__})", 0, ""
    if not rows: return "스캔 그림(글자층 없음)", 0, ""
    ws = SC.split(rows)
    if len(ws) < 5:
        # 교재처럼 글이 많은 것인가
        chars = sum(len(" ".join(map(str, r))) for r in rows)
        return ("교재·설명글" if chars > 2000 else "낱말이 적음"), len(ws), ""
    nk = sum(1 for _, k, _ in ws if k)
    ne = sum(1 for _, _, e in ws if e)
    tone = sum(1 for v, _, _ in ws if S.VI.search(v)) / len(ws)
    if tone < .25: return "베트남어 아님", len(ws), ""
    mean = "한글뜻" if nk >= len(ws) * .5 else ("영어뜻" if ne >= len(ws) * .5 else "낱말만")
    kind = "시험지" if ROUND.search(p.name) else "모음집(회차 없음)"
    if BLANK.search(p.name) and mean == "낱말만": kind = "빈 시험지"
    return f"{kind}·{mean}", len(ws), ws[0][0][:18]

def main():
    used = {}
    for gi in ("17", "18", "19", "20"):
        f = R / "data" / f"_senior_scan-{gi}.json"
        if f.exists():
            for x in json.loads(f.read_text(encoding="utf-8"))["files"]:
                used[(gi, x["src"])] = f"{x['kind']} {x['no']}"
    lines = ["폴더\t파일\t무엇인가\t낱말수\t첫낱말\t썼나"]
    stat = collections.Counter()
    targets = [(d.name, d) for d in sorted(BASE.iterdir()) if d.is_dir()]
    targets.append(("(바로 아래)", BASE))
    for name, D in targets:
        gi = name[:2]
        for fn in sorted(os.listdir(D)):
            p = D / fn
            if p.is_dir() or fn.startswith("."): continue
            what, n, first = look(p)
            u = used.get((gi, fn), "안 씀")
            lines.append(f"{name}\t{fn}\t{what}\t{n}\t{first}\t{u}")
            stat[what.split("·")[0]] += 1
    (R / "docs" / "file-audit.tsv").write_text("\n".join(lines), encoding="utf-8")
    print(f"파일 {len(lines)-1}개 확인 → docs/file-audit.tsv")
    for k, v in stat.most_common(): print(f"   {v:>4}  {k}")
main()
