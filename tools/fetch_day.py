#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**하루치 기사를 통째로** 받아 온다 → data/news_body.json · news_days.json 후보

대표님 지적 (2026-09-02): "9월 1일 기사들로 이루어진 거 맞니? 그제 기사가 섞였잖아."
섞인 까닭은 그날 기사가 넷뿐이었기 때문이다. 실제로는 훨씬 많이 나왔는데
`fetch_news.py` 가 자리(quota)에 맞춰 몇 건만 받고 말았다.
이 도구는 **그날 것을 다 받아** 후보를 넉넉히 만든다.

쓰기: python3 tools/fetch_day.py 2026-09-01
"""
import json, pathlib, re, subprocess, sys, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
KST = timezone(timedelta(hours=9))
FEEDS = [
    "https://www.insidevina.com/rss/allArticle.xml",
    "http://www.vietnamkoreatimes.com/rss/allArticle.xml",
    "https://e.vnexpress.net/rss/news.rss",
    "https://e.vnexpress.net/rss/business.rss",
    "https://e.vnexpress.net/rss/travel.rss",
    "https://e.vnexpress.net/rss/life.rss",
]


def get(u):
    return subprocess.run(["curl", "-sSL", "-m", "30", "-A", "Mozilla/5.0", u],
                          capture_output=True, timeout=50).stdout


def main():
    want = sys.argv[1] if len(sys.argv) > 1 else (
        datetime.now(KST) - timedelta(days=1)).strftime("%Y-%m-%d")
    import card_fill as CF
    from fetch_news import care_score, daily_score, cat_of, force_cat, about_vn

    got = []
    for f in FEEDS:
        try:
            root = ET.fromstring(get(f))
        except Exception:
            continue
        for it in root.iter("item"):
            t = (it.findtext("title") or "").strip()
            u = (it.findtext("link") or "").strip()
            p = (it.findtext("pubDate") or "").strip()
            if not t or not u:
                continue
            m = re.search(r"(\d{4})-(\d\d)-(\d\d)", p)
            if m:
                day = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            else:
                m2 = re.search(r"(\d\d) (\w\w\w) (\d{4})", p)
                if not m2:
                    continue
                MM = "JanFebMarAprMayJunJulAugSepOctNovDec".index(m2.group(2)) // 3 + 1
                day = f"{m2.group(3)}-{MM:02d}-{m2.group(1)}"
            if day == want:
                got.append({"t": t, "u": u, "ts": day})
    seen, uniq = set(), []
    for g in got:
        if g["u"] not in seen:
            seen.add(g["u"]); uniq.append(g)
    print(f"{want} 기사 {len(uniq)}건 찾음", flush=True)

    cache = json.loads((R / "data" / "_bodies.json").read_text(encoding="utf-8")) \
        if (R / "data" / "_bodies.json").exists() else {}
    out = []
    for g in uniq:
        b = CF.body_of(g["u"], cache)
        if len(b) < 300:
            continue
        g["body"] = b
        g["care"] = care_score(g["t"]) + min(care_score(b[:1500]), 12)
        g["daily"] = daily_score(g["t"])
        g["cat"] = force_cat(g["t"]) or cat_of(g["t"] + " " + b[:1200])
        if not about_vn(g):
            continue
        out.append(g)
    (R / "data" / "_bodies.json").write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    out.sort(key=lambda c: -c["care"])
    print(f"본문까지 받은 베트남 기사 {len(out)}건")
    from collections import Counter
    print("갈래별:", dict(Counter(c["cat"] for c in out)))

    # news_days 에 뼈대만 넣는다 (재료는 card_fill 이 채운다)
    F = R / "data" / "news_days.json"
    j = json.loads(F.read_text(encoding="utf-8"))
    have = {d.get("u") for d in j["days"]}
    add = 0
    for c in out:
        if c["u"] in have:
            continue
        j["days"].append({"ts": c["ts"], "day": "N" + c["u"][-8:], "track": "news",
                          "theme": (c["t"][:10] or "기사"), "title": c["t"], "u": c["u"],
                          "cat": c["cat"], "intro": c["body"][:140],
                          "words": [], "dialog": {"lines": []}})
        add += 1
    j["days"].sort(key=lambda d: (d.get("ts") or ""), reverse=True)
    for i, d in enumerate(j["days"]):
        d["n"] = len(j["days"]) - i
    F.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"새로 넣은 기사 {add} · 보관 {len(j['days'])}")


if __name__ == "__main__":
    main()
