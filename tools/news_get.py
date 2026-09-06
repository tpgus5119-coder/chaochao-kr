#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**하루치 기사를 주제별 주소에서 받아 점수만 매긴다** → news_days.json 후보

대표님 판단 (2026-09-02): "사이트마다 주제 구분이 되어 있으면 굳이 우리가 기준을 가지고
                          선정할 필요가 적어지지. 그냥 점수만 매겨주면 될 듯."

## 차례
① tools/news_feeds.py 가 **주제별 주소**에서 그날 기사를 다 받는다 (갈래는 주소가 정함)
② 본문을 받는다 (사이트마다 담는 곳이 다르다)
③ **점수만** 매긴다 — 한국어·영어·베트남어 낱말표를 똑같이
④ '많이 본 기사' 가산점
⑤ 베트남 소식인지 본다
⑥ news_days.json 에 뼈대를 넣는다 (재료는 card_fill 이 채운다)

쓰기: python3 tools/news_get.py [2026-09-01] [--top 40]
"""
import argparse, json, pathlib, sys
from collections import Counter

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("day", nargs="?", default=None)
    a.add_argument("--top", type=int, default=40)
    a = a.parse_args()

    from news_feeds import fetch
    from fetch_news import care_score, daily_score, about_vn, junk_score
    import card_fill as CF

    got = fetch(a.day)
    if not got:
        print("받은 기사가 없다"); return

    # 제목 점수로 먼저 줄을 세우고, 위에서부터 본문을 받는다 (본문 받기가 느리다)
    for c in got:
        c["care"] = care_score(c["t"]) - junk_score(c["t"])
        c["daily"] = daily_score(c["t"])
    try:
        from news_hot import hot_urls
        hot = hot_urls()
        for c in got:
            if c["u"] in hot:
                c["care"] += 6
        print(f"  많이 본 기사 가산점: {sum(1 for c in got if c['u'] in hot)}건")
    except Exception:
        pass
    got.sort(key=lambda c: -c["care"])

    cache = json.loads((R / "data" / "_bodies.json").read_text(encoding="utf-8")) \
        if (R / "data" / "_bodies.json").exists() else {}
    ok = []
    for c in got[:a.top]:
        b = CF.body_of(c["u"], cache)
        if len(b) < 300:
            continue
        c["body"] = b
        c["care"] += min(care_score(b[:1500]), 12)
        if not about_vn(c):
            continue
        ok.append(c)
    (R / "data" / "_bodies.json").write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    ok.sort(key=lambda c: -c["care"])
    print(f"\n본문까지 받고 베트남 소식인 기사 **{len(ok)}건**")
    print("갈래별:", dict(Counter(c.get("cat") or "(없음)" for c in ok)))
    print("사이트별:", dict(Counter(c["site"] for c in ok)))

    F = R / "data" / "news_days.json"
    j = json.loads(F.read_text(encoding="utf-8"))
    have = {d.get("u") for d in j["days"]}
    add = 0
    for c in ok:
        if c["u"] in have:
            continue
        j["days"].append({"ts": c["ts"], "day": "N" + c["u"][-10:], "track": "news",
                          "theme": c["t"][:10], "title": c["t"], "u": c["u"],
                          "cat": c.get("cat"), "care": c["care"],
                          "intro": c["body"][:140], "words": [], "dialog": {"lines": []}})
        add += 1
    j["days"].sort(key=lambda d: (d.get("ts") or ""), reverse=True)
    for i, d in enumerate(j["days"]):
        d["n"] = len(j["days"]) - i
    F.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"새로 넣은 기사 {add} · 보관 {len(j['days'])}")
    print("\n점수 높은 열둘:")
    for c in ok[:12]:
        print(f"  {c['care']:3}점 [{str(c.get('cat')):8}] {c['site']:10} {c['t'][:44]}")


if __name__ == "__main__":
    main()
