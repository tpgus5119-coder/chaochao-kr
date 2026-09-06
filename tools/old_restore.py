#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""선배 낱말 **이전** 과정을 되살린다 → data/order.json

대표님 지시 (2026-09-02): "선배 단어 이전에 있던 목차와 단어 다 복구시켜라."

data/course.json 이 그 과정이다 — 4,846낱말, 다섯 권, 단원 이름이 교재처럼 붙어 있다
('베트남어 할 줄 아세요' · '우체국이 어디예요?' · '지금 몇 시예요?').
선배 낱말로 갈아엎을 때 이 파일만 남고 화면에서 사라졌다.

## 옮기는 규칙
  course.json                     order.json
  vols[].units[].chapters[].words → vols[].chapters[].lessons[].words
  단원 이름(unit)                 → 챕터 제목(t)          ← 이것이 목차다
  챕터 번호(n)                    → 레슨 제목(t)
직무 권(6권)은 지금 order.json 의 직무를 그대로 쓴다 — 그쪽이 더 새것이다.

쓰기: python3 tools/old_restore.py
"""
import json, pathlib

R = pathlib.Path(__file__).resolve().parent.parent
c = json.loads((R / "data" / "course.json").read_text(encoding="utf-8"))
o = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))

vols, n_all = [], 0
for v in c["vols"]:
    name = str(v.get("vol", "")).strip()
    if "직무" in name:           # 직무는 지금 것을 쓴다 (999낱말로 새로 짠 것)
        continue
    chapters = []
    for u in v["units"]:
        lessons = []
        for ch in u["chapters"]:
            ws = ch.get("words") or []
            if not ws:
                continue
            lessons.append({"t": f"{u['unit']} ({ch.get('n')})" if len(u["chapters"]) > 1
                                 else u["unit"],
                            "words": ws})
            n_all += len(ws)
        if lessons:
            chapters.append({"t": u["unit"], "lessons": lessons})
    # 권 이름에서 번호를 떼고 제목만 남긴다 ('2권 첫걸음' → '첫걸음')
    title = name.split(" ", 1)[1] if " " in name else name
    vols.append({"kind": "life", "title": title, "chapters": chapters})

job = [v for v in o["vols"] if v.get("kind") != "life"]
o["vols"] = vols + job
(R / "data" / "order.json").write_text(json.dumps(o, ensure_ascii=False), encoding="utf-8")
print(f"되살린 낱말 {n_all} · 권 {len(vols)}")
for v in vols:
    n = sum(len(l["words"]) for ch in v["chapters"] for l in ch["lessons"])
    print(f"  {v['title']:10} 챕터 {len(v['chapters']):3} · 낱말 {n}")
