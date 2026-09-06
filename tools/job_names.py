#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**직무 레슨 75개에 이름을 붙인다** → data/order.json 의 lessons[].theme

대표님 지시 (2026-09-03): "챕터 123단어, 레슨1. 이렇게 하면 어떤 내용인지 모르잖아.
                          하루5분-(첫 인사와 자기소개)인사와 호칭  이런 식으로."
하루 5분은 날마다 theme 이 있는데(인사와 호칭·이름 묻고 답하기) 직무는 없었다.
낱말 열여섯을 보고 **그 묶음이 무엇인지** 한 줄로 짓는다.

쓰기: python3 tools/job_names.py [--dry]
"""
import argparse, json, pathlib, re, sys

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
F = R / "data" / "order.json"

ASK = ("아래는 베트남어 직무 낱말 묶음이다. 이 묶음의 **이름**을 지어라.\n"
       " ① 우리말 **4~9글자.** 명사로 끝낸다\n"
       " ② 낱말들을 아우르는 이름 — 하나만 콕 집지 마라\n"
       " ③ '단어'·'학습'·'1과' 같은 말은 넣지 마라\n"
       " ④ 큰 갈래 이름을 그대로 되풀이하지 마라\n"
       "\n"
       "보기\n"
       "  낱말: 생산하다, 고정된, 시간대, 공정, 작업하다, 기계\n"
       "  큰 갈래: 공통 · 생산과 공정\n"
       "  ✓ 이름: 라인에서 쓰는 말\n"
       "  ✕ 이름: 생산과 공정 (큰 갈래를 그대로 씀)\n"
       "  ✕ 이름: 생산하다 (하나만 집음)\n"
       "\n"
       "이름만 한 줄로 답하라. 따옴표·설명 없이.\n\n")

BAD = re.compile(r"[^가-힣0-9 ·()]")


# **금지어에 '과' 한 글자를 넣었더니 절반이 죽었다** (2026-09-03 실측) —
# '생산과 공정'·'공정과 작업' 처럼 이어 주는 '과' 까지 걸렸다.
# 한 글자짜리 금지어는 두더지잡기가 된다. '제3과' 꼴만 정규식으로 막는다.
NOGO = ("단어", "낱말", "학습", "묶음", "세트", "레슨", "챕터", "파트")
NUMPART = re.compile(r"(제?\s*\d+\s*과|\d+\s*번째)")


def clean(t, track, taken=()):
    t = (t or "").strip().splitlines()[0].strip()
    t = re.sub(r'^["\'\s·\-]+|["\'\s·\-.]+$', "", t)
    t = re.sub(r"^(이름|제목)\s*[:：]\s*", "", t).strip()
    if BAD.search(t) or not (3 <= len(t) <= 14):
        return ""
    if any(k in t for k in NOGO) or NUMPART.search(t):
        return ""
    # 큰 갈래를 **그대로** 되풀이한 것만 막는다 (겹치는 낱말이 있는 것은 괜찮다)
    if t == track or t == track.split("·")[-1].strip():
        return ""
    if t in taken:                       # 같은 갈래 안에서 이름이 겹치면 안 된다
        return ""
    return t


def main():
    a = argparse.ArgumentParser(); a.add_argument("--dry", action="store_true")
    a = a.parse_args()
    from qwen import ask, up
    if not up():
        print("Qwen 이 안 켜져 있다"); return
    j = json.loads(F.read_text(encoding="utf-8"))
    n = 0
    for v in j["vols"]:
        for t in v.get("tracks") or []:
            track = t.get("track") or ""
            taken = set()
            for c in t.get("chapters") or []:
                for i, l in enumerate(c.get("lessons") or [], 1):
                    if l.get("theme"):
                        continue
                    ws = [w.get("ko", "") for w in (l.get("words") or [])][:10]
                    q = f"낱말: {', '.join(ws)}\n큰 갈래: {track}\n"
                    name = ""
                    for _ in range(4):
                        name = clean(ask(ASK + q, max_tokens=120), track, taken)
                        if name:
                            break
                    if not name:
                        # 그래도 못 지으면 **첫 낱말 둘**로 짓는다 — 번호보다는 낫다
                        head = [w for w in ws[:2] if w]
                        name = " · ".join(head)[:14] or f"{i}번째"
                    taken.add(name)
                    l["theme"] = name
                    n += 1
                    print(f"  [{track}] {i} → {l['theme']}", flush=True)
    if not a.dry:
        F.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    print(f"\n이름 붙인 레슨 {n}")


if __name__ == "__main__":
    main()
