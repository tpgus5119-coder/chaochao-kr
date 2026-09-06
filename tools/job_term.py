#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""직무 낱말이 **낱말 하나인지** 가려낸다 → data/_jobterm.json (판정만)

대표님 지시 (2026-08-31): "직무 단어는 아까 말한대로 1개의 단어만으로 구성되어야지."

## 무엇이 '낱말 하나'인가 — 베트남어는 음절마다 띄어 쓴다
`công ty`(회사)는 두 덩이지만 사전에 **한 낱말**로 실린다.
`dây chuyền sản xuất`(생산라인)도 네 덩이지만 한 낱말이다 — 한국어 '품질관리'와 같다.
그러니 **띄어쓰기 수로는 못 가른다.** 가르는 잣대는 이것이다:

  ① 사전에 실릴 만한 **하나의 말**인가        → 둔다 (kiểm soát chất lượng = 품질관리)
  ② **문장·구**인가                          → 뺀다 (xếp lịch công tác = 출장 일정을 짜다)
  ③ 베트남어가 아니라 **영어**인가            → 베트남어로 바꾼다 (vendor → nhà cung cấp)
  ④ 억지로 붙여 만든 말인가                   → 뺀다 (việc làm việc)

고치지는 않는다 — 판정만 모아 사람이 정한다.
쓰기: python3 tools/job_term.py [--limit N]
"""
import argparse, json, pathlib, sys
from collections import Counter

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
from qwen import ask_json, up

OUT = R / "data" / "_jobterm.json"

ASK = (
    "너는 베트남어 공장·직무 용어 사전을 만드는 편집자다.\n"
    "아래 [베트남어, 한국어 뜻] 이 **낱말 하나로 사전에 실릴 만한가** 가려라.\n"
    "베트남어는 음절마다 띄어 쓴다는 것을 잊지 마라 — 띄어쓰기 수로 가르면 안 된다.\n"
    "  둔다(ok)   : 사전에 실릴 하나의 말. công ty(회사) · kiểm soát chất lượng(품질관리)\n"
    "  구(phrase) : 문장이나 구. xếp lịch công tác(출장 일정을 짜다) · gắn ngược(거꾸로 붙이다)\n"
    "  영어(eng)  : 베트남어가 아니라 영어. vendor · tray · Purchase → 베트남어 낱말을 fix 에\n"
    "  억지(made) : 실제로 안 쓰는 말을 붙여 만든 것. việc làm việc\n"
    "규칙: 확신이 없으면 ok 로 둬라. 멀쩡한 용어를 빼면 더 나쁘다.\n"
    '출력은 JSON 배열만: [{"vi":"낱말","v":"ok|phrase|eng|made","fix":"바꿀 말 또는 빈칸"}]\n\n'
)


def main():
    a = argparse.ArgumentParser(); a.add_argument("--limit", type=int, default=0); a = a.parse_args()
    if not up():
        print("Qwen 이 안 켜져 있다 — ~/.lmstudio/bin/lms server start"); return

    O = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    job = []
    for v in O["vols"]:
        if v.get("kind") != "job":
            continue
        for t in v["tracks"]:
            for c in t["chapters"]:
                for l in c["lessons"]:
                    job += l["words"]

    have = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    need = [w for w in job if w["vi"] not in have]
    if a.limit: need = need[:a.limit]
    print(f"직무 낱말 {len(job)} · 아직 안 본 것 {len(need)}", flush=True)

    for i in range(0, len(need), 20):
        part = need[i:i + 20]
        got = ask_json(ASK, [{"vi": w["vi"], "ko": w["ko"]} for w in part], chunk=20)
        by = {g.get("vi"): g for g in got if isinstance(g, dict)}
        for w in part:
            g = by.get(w["vi"]) or {}
            have[w["vi"]] = {"v": g.get("v") or "ok", "fix": g.get("fix") or "", "ko": w["ko"]}
        OUT.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
        if (i // 20) % 8 == 0:
            print(f"  {min(i+20,len(need))}/{len(need)}", flush=True)

    c = Counter(v["v"] for v in have.values())
    print(f"\n끝. 본 것 {len(have)}")
    for k, label in (("ok", "낱말 하나 — 둔다"), ("phrase", "구·문장"), ("eng", "영어"), ("made", "억지로 만든 말")):
        print(f"  {label:18} {c.get(k,0)}")


main()
