#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""카드에 얹을 **제목**을 다듬는다 → data/news_days.json 의 title_card

대표님 지시 (2026-09-01): "제목 안 바꿔도 되면 그대로 사용하고, 바꿔야 한다면 새로 지어라."

## 왜 다듬나 — 법이 아니라 화면 때문이다
신문 제목은 저작물로 잘 인정되지 않아 그대로 써도 된다. 다만 신문 제목과 카드 제목은
쓰임이 다르다. 신문 제목은 **기사 목록에서 훑는** 것이고, 카드 제목은 **사진 한 장 안에서
손가락을 멈추게** 하는 것이다. 33자 두 줄짜리는 카드에서 안 읽힌다.

## 언제 손대나
**{LIM}자를 넘을 때만.** 넘지 않으면 원문 그대로 둔다 — 고칠 이유가 없다.

## 짓는 규칙 (아래 ASK 그대로)
① 사실만 남긴다. 없는 말을 보태지 않는다  ② 누가·무엇을 앞에 둔다
③ 낚시 금지 — '충격', '경악' 따위  ④ {LIM}자 이내 한 줄

쓰기: python3 tools/card_title.py [--day 2026-08-31] [--force]
"""
import argparse, json, pathlib, re, sys

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
from ai import ask_text

F = R / "data" / "news_days.json"
LIM = 28

ASK = ("아래 기사 제목을 카드뉴스용으로 짧게 다듬어라.\n"
       "규칙\n"
       " ① 원문에 있는 사실만 쓴다. 없는 말을 보태지 마라\n"
       " ② 어디서·무엇이 일어났는지를 앞에 둔다\n"
       " ③ '충격'·'경악' 같은 낚시말을 쓰지 마라\n"
       f" ④ 한국어로 {LIM}자 이내, 한 줄. 마침표 없이\n"
       "출력은 다듬은 제목 한 줄만. 다른 말은 적지 마라.\n\n"
       "원문 제목: {t}\n"
       "기사 요약: {s}\n")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--day", default=""); a.add_argument("--force", action="store_true")
    a = a.parse_args()
    j = json.loads(F.read_text(encoding="utf-8"))
    todo = [d for d in j["days"]
            if (not a.day or d.get("ts") == a.day)
            and (a.force or not d.get("title_card"))
            and len(d.get("title", "")) > LIM]
    print(f"다듬을 제목 {todo and len(todo) or 0} (그 밖은 원문 그대로 쓴다)", flush=True)

    for d in todo:
        s = " ".join((d.get("sum5") or [])[:2])
        t = ask_text(ASK.format(t=d["title"], s=s), local=True, max_tokens=800)
        t = re.sub(r'^["\'\s]+|["\'\s.]+$', "", (t or "").split("\n")[0]).strip()
        # ── 검수 ① 띄어쓰기 — 모델이 "9 월 1 일" 처럼 숫자와 단위를 떼어 놓는다 (실측)
        # 숫자와 단위 사이가 벌어지는 버릇 — '9 월 1 일' · '2억 8 천만' (실측 두 번).
        # 붙이는 것은 **수를 이루는 말까지만**이다. '달러·원' 같은 화폐는 띄어 쓴다.
        t = re.sub(r"(\d)\s+(월|일|년|시|분|초|%|천|백|십|만|억|조)", r"\1\2", t)
        t = re.sub(r"(천|백|십|만|억)\s+(만|억|조)", r"\1\2", t)
        t = re.sub(r"(\d)\s+(명|개|원|동|대|건|배|위|차)", r"\1\2", t)
        t = re.sub(r"\s{2,}", " ", t).strip()
        # ── 검수 ② 지어낸 숫자 — 제목에 새로 나온 수는 원문·요약에 있어야 한다
        src = d["title"] + " " + " ".join(d.get("sum5") or []) + " " + (d.get("intro") or "")
        made_up = [x for x in re.findall(r"\d[\d,.]*", t) if x not in src]
        # ── 검수 ③ 길이·글자
        if not t or len(t) > LIM + 6 or not re.search(r"[가-힣]", t) or made_up:
            why = f"지어낸 수 {made_up}" if made_up else "길거나 비었다"
            print(f"  버림({why}): {t!r}  ← 원문 그대로 둔다"); continue
        d["title_card"] = t
        print(f"  {d['title'][:30]}\n   → {t}", flush=True)
    F.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")


# 불러오기만 할 때는 돌지 않는다 — 다른 도구가 TOPICS 같은 것을
# 가져다 쓸 때 낱말 모으기가 통째로 다시 도는 사고가 있었다 (2026-09-01).
if __name__ == "__main__":
    main()
