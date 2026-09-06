#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""사이트가 **이미 골라 둔 기사**를 알아낸다 → 주소 집합

대표님 물음 (2026-09-02): "각 사이트에서 이미 메인 기사와 중요한 기사들은
구분하지 않니? 이미 좋은 기사를 구분해 준 상태인데."

맞다. 인사이드비나 첫 화면에 **「많이 본 뉴스」** 구역이 있다 —
편집자가 고른 것이 아니라 **독자가 실제로 많이 읽은 것**이라 더 낫다.
우리 낱말 점수는 '우리 독자에게 쓸모 있는가'를 재고,
이것은 '베트남 사는 사람들이 실제로 읽었는가'를 잰다. 둘은 다른 잣대다.

## 어떻게 쓰나
`fetch_news.py` 가 점수를 매길 때 **가산점**으로 쓴다. 자리를 못 채울 때
억지로 낮은 점수 기사를 넣는 것보다, 많이 읽힌 기사를 넣는 편이 낫다.

쓰기: from news_hot import hot_urls;  hot = hot_urls()
"""
import re, subprocess

SITES = [
    ("https://www.insidevina.com/", "많이 본 뉴스"),
    ("http://www.vietnamkoreatimes.com/", "많이 본"),
]

# 현지 신문은 첫 화면 **맨 위**가 그 날의 주요 기사다.
# (대표님 지시 2026-09-02: 주요 기사를 **가산점**으로 쓴다 — 대상으로 삼지 않는다.
#  첫 화면 상위 절반이 국제·연예·스포츠라 그것만 쓰면 우리 독자와 안 맞는다.)
TOP_SITES = [
    ("https://dantri.com.vn", r'https?://dantri\.com\.vn/[a-z0-9-]+/[a-z0-9-]{16,}\.htm'),
    ("https://vnexpress.net", r'https?://vnexpress\.net/[a-z0-9-]{16,}-\d{7}\.html'),
    ("https://tuoitre.vn",    r'https?://tuoitre\.vn/[a-z0-9-]{16,}\.htm'),
]
TOP_N = 20        # 첫 화면 맨 위 스무 건까지를 '주요 기사'로 본다


def hot_urls():
    """첫 화면의 '많이 본' 구역에 실린 기사 주소를 모은다."""
    out = set()
    for url, mark in SITES:
        try:
            h = subprocess.run(["curl", "-sSL", "-m", "25", "-A", "Mozilla/5.0", url],
                               capture_output=True, text=True, timeout=40).stdout
        except Exception:
            continue
        i = h.find(mark)
        if i < 0:
            continue
        seg = h[i:i + 9000]
        base = url.rstrip("/")
        for idx in set(re.findall(r"idxno=(\d+)", seg)):
            out.add(f"{base}/news/articleView.html?idxno={idx}")

    # 현지 신문 — 첫 화면 맨 위 기사
    for url, pat in TOP_SITES:
        try:
            h = subprocess.run(["curl", "-sSL", "-m", "25", "-A", "Mozilla/5.0", url],
                               capture_output=True, text=True, timeout=45).stdout
        except Exception:
            continue
        for u in list(dict.fromkeys(re.findall(pat, h)))[:TOP_N]:
            out.add(u)
    return out


if __name__ == "__main__":
    u = hot_urls()
    print(f"많이 본 기사 {len(u)}건")
    for x in sorted(u):
        print(" ", x)
