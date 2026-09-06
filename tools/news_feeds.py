#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**주제별 주소에서 기사를 받는다** — 갈래를 우리가 정하지 않는다

대표님 판단 (2026-09-02): "사이트마다 주제 구분이 되어 있으면 굳이 우리가 기준을 가지고
                          선정할 필요가 적어지지. 그냥 점수만 매겨주면 될 듯."

맞다. 신문사가 이미 갈래를 나눠 두었다. **주소가 곧 갈래**다.
우리가 하던 세 겹 판정(사이트→Qwen→낱말)은 자주 틀렸다. 이제 안 쓴다.

## 실측 (2026-09-01 하루치)
  Dân Trí 경제 25 · VnExpress 시사 12 · 인사이드비나 8 · VnExpress 경제 8
  VnExpress 사건 6 · Dân Trí 일자리 2   → **하루 61건**
전에는 인사이드비나 8건뿐이었다.

쓰기: python3 tools/news_feeds.py 2026-09-01
"""
import json, pathlib, re, subprocess, sys, xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

R = pathlib.Path(__file__).resolve().parent.parent
KST = timezone(timedelta(hours=9))
MON = "JanFebMarAprMayJunJulAugSepOctNovDec"

# (사이트, 우리 갈래, 주소) — **주소가 곧 갈래다**
FEEDS = [
    ("Dân Trí",    "일자리",    "https://dantri.com.vn/rss/lao-dong-viec-lam.rss"),
    ("Dân Trí",    "경제",      "https://dantri.com.vn/rss/kinh-doanh.rss"),
    ("VnExpress",  "경제",      "https://vnexpress.net/rss/kinh-doanh.rss"),
    ("VnExpress",  "사회",      "https://vnexpress.net/rss/thoi-su.rss"),
    ("VnExpress",  "사회",      "https://vnexpress.net/rss/phap-luat.rss"),
    ("VnExpress",  "문화·생활",  "https://vnexpress.net/rss/du-lich.rss"),
    ("VnExpress",  "공장·산업",  "https://vnexpress.net/rss/khoa-hoc-cong-nghe.rss"),
    ("Tuổi Trẻ",   "경제",      "https://tuoitre.vn/rss/kinh-doanh.rss"),
    ("Tuổi Trẻ",   "사회",      "https://tuoitre.vn/rss/thoi-su.rss"),
    # **갈래를 고루 채운다** (대표님 지시 2026-09-02 "주제가 밸런스 있게 다 있어야").
    # 전에는 경제 주소만 여럿이라 후보 49건 중 40건이 경제였다.
    ("Dân Trí",    "사회",      "https://dantri.com.vn/rss/xa-hoi.rss"),
    ("Dân Trí",    "사회",      "https://dantri.com.vn/rss/giao-duc.rss"),
    ("Dân Trí",    "문화·생활",  "https://dantri.com.vn/rss/du-lich.rss"),
    ("Dân Trí",    "정치",      "https://dantri.com.vn/rss/the-gioi.rss"),
    ("Tuổi Trẻ",   "문화·생활",  "https://tuoitre.vn/rss/du-lich.rss"),
    ("Tuổi Trẻ",   "정치",      "https://tuoitre.vn/rss/the-gioi.rss"),
    ("VnExpress",  "정치",      "https://vnexpress.net/rss/the-gioi.rss"),
    ("VnExpress",  "공장·산업",  "https://vnexpress.net/rss/oto-xe-may.rss"),
    ("인사이드비나",   "",         "https://www.insidevina.com/rss/allArticle.xml"),
    ("코리아타임즈",   "",         "http://www.vietnamkoreatimes.com/rss/allArticle.xml"),
]


def when(p):
    """날짜를 읽는다. 신문사마다 꼴이 다르다 —
    '2026-09-01 …' · '01 Sep 2026 …' · '9/1/2026 7:00:00 PM' (Tuổi Trẻ)."""
    p = (p or "").replace(" ", " ")
    m = re.search(r"(\d{4})-(\d\d)-(\d\d)", p)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r"(\d\d) (\w\w\w) (\d{4})", p)
    if m:
        return f"{m.group(3)}-{MON.index(m.group(2))//3+1:02d}-{m.group(1)}"
    m = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})", p)      # 달/일/해
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return None


def fetch(day=None):
    """그날 기사를 주제별 주소에서 다 받는다 → [{t,u,ts,site,cat}]"""
    want = day or (datetime.now(KST) - timedelta(days=1)).strftime("%Y-%m-%d")
    got, seen = [], set()
    for site, cat, url in FEEDS:
        try:
            root = ET.fromstring(subprocess.run(
                ["curl", "-sSL", "-m", "25", "-A", "Mozilla/5.0", url],
                capture_output=True, timeout=45).stdout)
        except Exception:
            print(f"  {site} {cat}: 못 받음"); continue
        n = 0
        for it in root.iter("item"):
            t = (it.findtext("title") or "").strip()
            u = (it.findtext("link") or "").strip()
            if not t or not u or u in seen:
                continue
            if when(it.findtext("pubDate")) != want:
                continue
            seen.add(u); n += 1
            got.append({"t": t, "u": u, "ts": want, "site": site, "cat": cat or None})
        print(f"  {site:12}{cat or '전체':8}{n:3}건", flush=True)
    print(f"{want} 기사 {len(got)}건")
    return got


if __name__ == "__main__":
    fetch(sys.argv[1] if len(sys.argv) > 1 else None)
