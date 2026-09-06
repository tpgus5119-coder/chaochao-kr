#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""기수 폴더의 **모든 파일**이 어떻게 되었는지 한 줄씩 적는다 — 빠짐 점검용.
쓰기: python3 tools/senior_audit.py 17 18 19 20
"""
import json, os, pathlib, re, sys, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import senior18 as S

BASE = S.BASE
def audit(gi):
    D = [x for x in BASE.iterdir() if x.is_dir() and x.name.startswith(gi)][0]
    rows, seen = [], {}
    for f in sorted(os.listdir(D)):
        if f.startswith("."): continue
        lab = S.label(f)
        if not lab:
            rows.append((f, "버림", "빈 시험지" if S.BLANK.search(f) else "이름에 시험 낱말 없음", 0)); continue
        p = D / f
        try:
            rows_ = S.rows_xlsx(p) if f.lower().endswith((".xlsx",".xls")) else S.rows_pdf(p)
        except Exception as e:
            rows.append((f, "버림", f"못 읽음 {type(e).__name__}", 0)); continue
        if not rows_: rows.append((f, "버림", "스캔 그림", 0)); continue
        ws = S.pairs(rows_)
        if len(ws) < 5: rows.append((f, "버림", f"낱말 {len(ws)}개뿐", len(ws))); continue
        tone = sum(1 for v,_ in ws if S.VI.search(v))/len(ws)
        if len(ws) >= 15 and tone < .25:
            rows.append((f, "버림", f"베트남어 아님(성조 {tone:.0%})", len(ws))); continue
        if lab in seen:
            rows.append((f, "겹침", f"{lab} 이미 있음(먼저 것 {seen[lab]}개)", len(ws)))
        else:
            seen[lab] = len(ws)
            rows.append((f, "씀", f"{lab[0]} {lab[1]}회", len(ws)))
    return D.name, rows

for gi in sys.argv[1:]:
    name, rows = audit(gi)
    used = [r for r in rows if r[1]=="씀"]
    print(f"\n=== {name} — 파일 {len(rows)} · 쓴 파일 {len(used)} · 낱말자리 {sum(r[3] for r in used)}")
    c = collections.Counter(r[2].split("(")[0].strip() if r[1]!="씀" else "씀" for r in rows)
    for k,v in c.most_common(): print(f"   {v:>4}  {k}")
    lost = [r for r in rows if r[1]=="겹침"]
    if lost:
        print(f"  --- 겹쳐서 버린 {len(lost)}개 (낱말 {sum(r[3] for r in lost)}자리)")
        for f,_,why,n in lost[:100]: print(f"     {n:>3}개  {f[:60]}  ← {why}")
    bad = [r for r in rows if r[1]=="버림" and "이름에" not in r[2] and "빈 시험지" not in r[2]]
    if bad:
        print(f"  --- 못 읽어 버린 {len(bad)}개")
        for f,_,why,n in bad[:60]: print(f"     {why[:34]:<34} {f[:58]}")
    nn = [r for r in rows if r[1]=="버림" and "이름에" in r[2]]
    if nn:
        print(f"  --- 이름 때문에 아예 안 연 {len(nn)}개")
        for f,_,_,_ in nn[:60]: print(f"     {f[:78]}")
