#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""지금 앱에 실린 과정을 **글로 옮겨 적는다** → docs/지금-과정.md

대표님 지시 (2026-09-02): "우리 목차 세부목차까지 세세하게 말해봐.
                          거기에 해당하는 단어들 뭐 있는지도 다 보여줘."

**AI 를 쓰지 않는다.** 자료를 그대로 옮기는 일이라 세면 된다.
AI 에게 시키면 오히려 낱말을 빠뜨리거나 지어낸다.

쓰기: python3 tools/course_md.py
"""
import json, pathlib

R = pathlib.Path(__file__).resolve().parent.parent
o = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
out = ["# 지금 앱에 실린 과정", ""]

for v in o["vols"]:
    if "chapters" not in v:
        continue
    n = sum(len(l["words"]) for c in v["chapters"] for l in c["lessons"])
    out += [f"## {v.get('title') or v['kind']}",
            f"챕터 {len(v['chapters'])} · 레슨 {sum(len(c['lessons']) for c in v['chapters'])} · 낱말 {n}", ""]
    for ci, c in enumerate(v["chapters"], 1):
        cn = sum(len(l["words"]) for l in c["lessons"])
        out += [f"### {ci}. {c.get('t')}  ({cn}낱말)", ""]
        for l in c["lessons"]:
            out += [f"**{l.get('t')}** — {len(l['words'])}개", ""]
            # 다섯 개씩 줄바꿈해서 읽기 쉽게
            ws = [f"{w['vi']} {w['ko']}" for w in l["words"]]
            for i in range(0, len(ws), 5):
                out.append("　" + " ／ ".join(ws[i:i + 5]))
            out.append("")

p = R / "docs" / "지금-과정.md"
p.write_text("\n".join(out), encoding="utf-8")
print(f"{p} · {len(out)}줄")
