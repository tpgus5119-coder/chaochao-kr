#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""새 낱말이 **실제로 쓰는 말인지** 가린다 → data/_new_words.json 의 real·v·ko

왜 (2026-09-01 실측): 뜻 검수(new_check.py)는 뜻만 본다. 그래서
Chào buổi sáng cực muộn 같이 **말 자체가 가짜**인 것을 못 잡았다.
규칙으로 거를 수 있는 것은 new_clean.py 가 이미 잘라냈고, 여기서는
"베트남 사람이 이 말을 쓰나"를 묻는다.

## 순서
① 사전(우리 것·위키낱말)에서 이미 확인된 말은 건너뛴다 — 물어볼 필요가 없다
② 나머지만 Qwen 에게 스무 개씩 묶어 묻는다 (공짜)
③ 답은 규칙으로 다시 검수한다 — 뜻에 한글이 아닌 글자가 섞이거나
   12자를 넘으면 안 받는다 (아랍 문자가 샌 적이 있다)

쓰기: python3 tools/new_real.py [--all]
"""
import argparse, json, pathlib, re, sys
from collections import Counter

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
from qwen import ask_json, up

OUT = R / "data" / "_new_words.json"
ASK = ("너는 베트남어 사전을 만드는 사람이다. 아래 [베트남어, 한국어 뜻] 을 보고 답하라.\n"
       "  real : 베트남 사람이 실제로 쓰는 말인가. 1 이면 쓴다, 0 이면 안 쓴다\n"
       "         (사전에 없거나, 단어를 기계적으로 붙여 만든 말이면 0)\n"
       "  ko   : 뜻이 맞으면 그대로, 틀리면 **맞는 뜻**을 한글 12자 이내로\n"
       "규칙: 여러 뜻 중 하나만 적은 것은 맞는 것이다. 확신이 없으면 real 1, ko 는 그대로 두라.\n"
       '출력은 JSON 배열만: [{"vi":"낱말","real":1,"ko":"뜻"}]\n\n')


def main():
    a = argparse.ArgumentParser(); a.add_argument("--all", action="store_true"); a = a.parse_args()
    if not up():
        print("Qwen 이 안 켜져 있다"); return
    d = json.loads(OUT.read_text(encoding="utf-8"))

    todo = [w for ws in d.values() for w in ws
            if a.all or (w.get("real") is None and w.get("src") == "확인못함")]
    print(f"물어볼 낱말 {len(todo)}", flush=True)
    if not todo:
        return

    got = ask_json(ASK, [{"vi": w["vi"], "ko": w["ko"]} for w in todo], chunk=20)
    by = {str(g.get("vi", "")).strip(): g for g in (got or []) if isinstance(g, dict)}
    fixed = gone = miss = 0
    for w in todo:
        g = by.get(w["vi"])
        if not g:
            miss += 1; continue
        w["real"] = 0 if str(g.get("real")) in ("0", "False", "false") else 1
        ko = str(g.get("ko") or "").strip()
        # 답을 그대로 믿지 않는다 — 한글 12자 이내일 때만 받는다
        if ko and ko != w["ko"] and len(ko) <= 12 and not re.search(
                r"[^가-힣ㄱ-ㆎ0-9 ·()~,./%\-]", ko):
            w["ko_before"], w["ko"] = w["ko"], ko; fixed += 1
        if not w["real"]:
            gone += 1
    OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"안 쓰는 말이라 한 것 {gone} · 뜻 고친 것 {fixed} · 답을 안 준 것 {miss}")
    c = Counter(w.get("real") for ws in d.values() for w in ws)
    print("real 분포", dict(c))


# 불러오기만 할 때는 돌지 않는다 — 다른 도구가 TOPICS 같은 것을
# 가져다 쓸 때 낱말 모으기가 통째로 다시 도는 사고가 있었다 (2026-09-01).
if __name__ == "__main__":
    main()
