#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낱말이 **제 목차에 있는지** 본다 → data/_new_words.json 의 fit

대표님 확인 (2026-09-01): "목차에 여러 낱말이 섞이는 건 상관없지 않니?
                          목차 이름 자체가 상황별로 지어져 있지 않니?"
맞다. 목차는 **상황**으로 묶는다. '식당에서 시키기'에 메뉴(명사)·주문하다(동사)·
맛있다(형용사)가 섞이는 것은 당연하고, 오히려 그래야 한다 —
같은 갈래만 모아 놓으면 서로 비슷해 헷갈린다는 실험 결과가 있다.

## 그래서 무엇을 보나
품사가 섞였는지가 아니라 **그 상황에서 쓰는 말인가**만 본다.
bàn chải(솔)가 '색깔'에 들어가 있으면 잘못이다.

Qwen 에게 묻되 **맨손으로 묻지 않는다** — 목차 이름과 '이 꼭지를 마치면 할 수 있는 것'을
함께 준다. 판단할 근거가 있어야 지어내지 않는다.

표시: fit=ok(맞다) · fit=<딴 꼭지 이름>(옮기는 게 낫다) · fit=drop(어디에도 안 맞다)
쓰기: python3 tools/topic_check.py [--only 색깔]
"""
import argparse, json, pathlib, re, sys, unicodedata as U
from collections import Counter

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
from qwen import ask_json, up
from new_words import TOPICS

OUT = R / "data" / "_new_words.json"
n = lambda s: U.normalize("NFC", str(s)).strip()
CANDO = {t: c for _, t, c in TOPICS}

ASK = ("아래 낱말들은 '{t}' 꼭지에 들어 있다.\n"
       "이 꼭지를 마치면 할 수 있는 일: {c}\n\n"
       "낱말마다 이 꼭지에 어울리는지 답하라.\n"
       " ok   : 이 상황에서 쓰는 말이다\n"
       " drop : 이 상황과 상관없는 말이다\n"
       "규칙\n"
       " · **품사가 섞이는 것은 문제가 아니다.** 명사·동사·형용사가 함께 있는 게 정상이다\n"
       " · 그 상황에서 한 번이라도 쓸 만하면 ok 다. 애매하면 ok\n"
       " · 뜻이 그 상황과 아무 상관없을 때만 drop\n"
       '출력은 JSON 배열만: [{{"vi":"낱말","fit":"ok|drop"}}]\n\n')


def main():
    a = argparse.ArgumentParser(); a.add_argument("--only", default=""); a = a.parse_args()
    if not up():
        print("Qwen 이 안 켜져 있다"); return
    d = json.loads(OUT.read_text(encoding="utf-8"))
    bad = []
    for topic, ws in d.items():
        if a.only and a.only != topic:
            continue
        todo = [w for w in ws if not w.get("fit")]
        if not todo:
            continue
        got = ask_json(ASK.format(t=topic, c=CANDO.get(topic, topic)),
                       [{"vi": w["vi"], "ko": w["ko"]} for w in todo], chunk=25)
        by = {n(g.get("vi", "")): g for g in (got or []) if isinstance(g, dict)}
        for w in todo:
            f = str((by.get(n(w["vi"])) or {}).get("fit") or "ok")
            w["fit"] = "drop" if f == "drop" else "ok"
            if w["fit"] == "drop":
                bad.append((topic, w["vi"], w["ko"]))
        OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {topic:16} {len(todo):3}개 봄 · 어울리지 않는 것 "
              f"{sum(1 for w in todo if w['fit']=='drop')}", flush=True)

    print(f"\n어울리지 않는다고 한 것 {len(bad)} — 사람이 본 뒤에 뺀다")
    for t, vi, ko in bad[:40]:
        print(f"  [{t}] {vi} = {ko}")


# 불러오기만 할 때는 돌지 않는다 — 다른 도구가 TOPICS 같은 것을
# 가져다 쓸 때 낱말 모으기가 통째로 다시 도는 사고가 있었다 (2026-09-01).
if __name__ == "__main__":
    main()
