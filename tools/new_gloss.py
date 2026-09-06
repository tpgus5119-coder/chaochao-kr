#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""뜻이 빈 낱말을 채운다 → data/_new_words.json

new_clean.py 가 'màu đỏ' 를 màu + đỏ 로 쪼개면 조각에는 뜻이 없다. 그것을 채운다.

## 순서 (토큰을 아끼려고 있는 것부터)
① 우리가 이미 아는 뜻 — exgloss·다른 꼭지에 같은 낱말이 있으면 그대로 가져온다 (공짜)
② 남은 것만 Qwen 에게 묶어서 묻는다 (공짜)
③ 답은 규칙으로 다시 본다 — 한글 12자 이내가 아니면 안 받는다

쓰기: python3 tools/new_gloss.py
"""
import json, pathlib, re, sys, unicodedata as U
from collections import Counter

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
from qwen import ask_json, up

OUT = R / "data" / "_new_words.json"
n = lambda s: U.normalize("NFC", str(s)).strip()
k = lambda s: n(s).lower()
ASK = ("아래 베트남어 낱말의 한국어 뜻을 달아라.\n"
       "규칙\n"
       " ① 한글로 12자 이내. 가장 흔한 뜻 하나만\n"
       " ② 모르면 지어내지 말고 ko 를 빈칸으로 두라\n"
       " ③ 설명하지 말고 뜻만. '~하다'·'~것' 형태로\n"
       '출력은 JSON 배열만: [{"vi":"낱말","ko":"뜻"}]\n\n')


def main():
    d = json.loads(OUT.read_text(encoding="utf-8"))
    # ① 아는 뜻 모으기 — 우리 자료가 먼저다
    know = {}
    ex = R / "data" / "exgloss.json"
    if ex.exists():
        for w, v in json.loads(ex.read_text(encoding="utf-8")).items():
            if v.get("ko"):
                know.setdefault(k(w), n(v["ko"]))
    for ws in d.values():
        for w in ws:
            if w.get("ko"):
                know.setdefault(k(w["vi"]), n(w["ko"]))

    todo, got_free = [], 0
    for ws in d.values():
        for w in ws:
            if w.get("ko"):
                continue
            if k(w["vi"]) in know:
                w["ko"], w["v"], w["by"] = know[k(w["vi"])], "재검", "우리자료"; got_free += 1
            else:
                todo.append(w)
    print(f"우리 자료로 채운 것 {got_free} · Qwen 에게 물을 것 {len(todo)}", flush=True)

    if todo and up():
        res = ask_json(ASK, [{"vi": w["vi"]} for w in todo], chunk=25)
        by = {n(g.get("vi", "")): g for g in (res or []) if isinstance(g, dict)}
        ok = 0
        for w in todo:
            ko = n((by.get(n(w["vi"])) or {}).get("ko") or "")
            if ko and len(ko) <= 12 and not re.search(r"[^가-힣ㄱ-ㆎ0-9 ·()~,./%\-]", ko):
                w["ko"], w["v"], w["by"] = ko, "재검", "AI"; ok += 1
        print(f"Qwen 이 채운 것 {ok} · 못 채운 것 {len(todo)-ok}")

    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    empty = [w["vi"] for ws in d.values() for w in ws if not w.get("ko")]
    print(f"아직 뜻이 빈 낱말 {len(empty)}: {empty[:20]}")


# 불러오기만 할 때는 돌지 않는다 — 다른 도구가 TOPICS 같은 것을
# 가져다 쓸 때 낱말 모으기가 통째로 다시 도는 사고가 있었다 (2026-09-01).
if __name__ == "__main__":
    main()
