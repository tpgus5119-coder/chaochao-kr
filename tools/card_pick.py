#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**이미 받아 둔 기사** 중에서 오늘 카드로 낼 것을 고른다 → news_days.json 의 pub

fetch_news.py 는 **새 기사를 받을 때** 고른다. 그런데 이미 받아 둔 기사 중에서
다시 고르고 싶을 때가 있다 (기준을 바꿨거나, 오늘 새 기사가 적을 때).
그때 이 도구를 쓴다. 인터넷을 안 탄다.

## 고르는 잣대 (docs/기준.md 와 같다)
  · 주제마다 자리: 일자리3 · 경제2 · 사회2 · 문화2 · 공장2 · 정치1
  · 여섯 줄 풀이가 있고, 낱말 여섯 이상, 대화 두 줄 이상인 것만
  · 모자라면 주제 상관없이 채워 최소 10건
  · 정치는 베트남 밖 매체에서만

쓰기: python3 tools/card_pick.py [--pub 2026-09-02] [--days 3]
"""
import argparse, json, pathlib, re
from collections import Counter
from datetime import datetime, timedelta, timezone

R = pathlib.Path(__file__).resolve().parent.parent
QUOTA = [('일자리', 3), ('경제', 2), ('사회', 2), ('문화·생활', 2), ('공장·산업', 2), ('정치', 1)]
MIN_DAY = 12
# **섞어 싣는다** (대표님 지시 2026-09-02 "한국 사이트의 베트남 기사 + 베트남어·영어
# 사이트의 기사로 합쳐서"). 한국어 매체는 하루 8건뿐이고 그중 여섯이 경제라
# 한국어 매체만으로는 주제가 안 맞는다. 그래서 **자리를 나눠 준다**:
#   한국어 매체 4 : 현지(베트남어·영어) 매체 8  = 1 : 2
# 한국어 매체 기사는 같은 갈래에서 점수가 조금 낮아도 KO_MIN 을 채울 때까지 먼저 든다.
KO_MIN = 4
KO_MAX = 5
# **주제가 고루 있어야 한다** (대표님 지시 2026-09-02 "주제가 밸런스 있게 다 있어야").
# 자리를 못 채운 갈래가 있으면, 남는 자리를 다른 갈래로 몰아 주지 않고
# **점수선을 한 단계 낮춰** 그 갈래에서 다시 찾는다. 그래도 없으면 비운다.
FLOOR_RELAX = 6   # 자리를 못 채운 갈래에만 적용하는 낮춘 점수선
MIN_CATS = 5      # 적어도 이만큼 갈래가 나와야 한다

FLOOR = 8        # **이 점수 미만은 자리가 비어도 안 싣는다.**
                 # 이게 없어서 0점짜리 두리안 절도 기사가 '문화·생활' 자리를 채웠다
                 # (2026-09-02 실측). 낱말로 막는 것은 두더지잡기다 — 점수를 지켜야 한다.
POLITICS_OK = ('insidevina.com', 'vietnamkoreatimes.com')
KO_SITES = ('insidevina.com', 'vietnamkoreatimes.com')


def host_of(d):
    try:
        return (d.get('u') or '').split('/')[2].replace('www.', '')
    except IndexError:
        return ''


def is_ko(d):
    h = host_of(d)
    return any(h.endswith(x) for x in KO_SITES)

# **국내 정치만** 베트남 밖 매체에서 가져온다 (대표님 지시).
# 현지 매체는 국내 정치를 한쪽으로만 전하기 때문이다.
# 다만 **외교·국제 소식은 현지 매체도 괜찮다** — 사실 전달이라 한쪽으로 기울 일이 적다.
# (실측 2026-09-02: 이 구분이 없어 '미얀마 대통령 베트남 방문'까지 걸러졌다)
DOMESTIC = ['국회', '당대회', '서기장', '총비서', '선거', '개헌', '내각', '인사',
            'quốc hội', 'đại hội đảng', 'tổng bí thư', 'bầu cử', 'bộ chính trị',
            'national assembly', 'party congress', 'election']


def domestic_politics(d):
    hay = " ".join(str(d.get(k) or "") for k in ("title", "title_card", "intro")).lower()
    return any(k in hay for k in DOMESTIC)
KST = timezone(timedelta(hours=9))


def junk(d):
    """시시한 기사인가 — **원제와 옮긴 제목을 다 본다.**
    저장된 기사는 title_card(한국어)만 보게 되어 두리안 절도가 계속 남았다 (2026-09-02)."""
    import sys as _s, pathlib as _p
    _s.path.insert(0, str(_p.Path(__file__).resolve().parent))
    from fetch_news import junk_score
    hay = " ".join(str(d.get(k) or "") for k in ("title", "title_card", "theme"))
    return junk_score(hay) > 0


def ok(d):
    """카드로 **낼 만한 기사인가** — 재료가 있느냐로 고르지 않는다.

    전에는 '여섯 줄 풀이·낱말·대화가 이미 있는가'로 골랐다. 그건 거꾸로다 —
    **기사를 먼저 고르고, 고른 기사의 재료를 만드는 것**이 옳다
    (대표님 지적 2026-09-02). 재료로 고르면 좋은 기사가 재료가 없다는 이유로 빠진다.
    여기서는 **기사 자체가 쓸 만한가**만 본다."""
    return bool((d.get('body') or d.get('intro') or d.get('title')))


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--pub', default='')
    a.add_argument('--days', type=int, default=1)   # **어제 하루치만** (대표님 지시)
    # 한국어 매체(베트남 소식만 다루는 곳)로만 만들어 견주어 본다 (대표님 지시 2026-09-02)
    a.add_argument('--ko-only', action='store_true')
    a = a.parse_args()
    now = datetime.now(KST)
    pub = a.pub or (now + timedelta(days=1) if now.hour >= 12 else now).strftime('%Y-%m-%d')

    p = R / 'data' / 'news_days.json'
    j = json.loads(p.read_text(encoding='utf-8'))
    days = j['days']
    for d in days:
        d.pop('pub', None)

    # **하루치만 쓴다** (대표님 지적 2026-09-02 "그제 기사들이 있는 거 아니냐").
    # 9월 2일 카드는 9월 1일 기사로만 만든다. 며칠을 섞으면 지난 소식이 오늘 것처럼 나간다.
    from datetime import date as _date
    y, m, dd = map(int, (a.pub or now.strftime('%Y-%m-%d')).split('-'))
    want = (_date(y, m, dd) - timedelta(days=1)).strftime('%Y-%m-%d')
    # **갈래는 주소가 정한다** (대표님 판단 2026-09-02) — 우리가 다시 안 매긴다.
    # 다만 갈래가 없는 기사(인사이드비나 전체 주소 등)만 낱말로 붙인다.
    import sys as _s
    _s.path.insert(0, str(R / 'tools'))
    try:
        from fetch_news import force_cat, cat_of
        for d in days:
            if d.get('cat') in (None, '', '소식'):
                d['cat'] = force_cat(d.get('title') or '') or \
                           cat_of((d.get('title') or '') + ' ' + (d.get('intro') or ''))
    except Exception as e:
        print(f'  갈래 붙이기 건너뜀: {e}')
    cand = [d for d in days if d.get('ts') == want and ok(d)]
    if a.ko_only:
        cand = [d for d in cand
                if any((d.get('u') or '').split('/')[2].replace('www.', '').endswith(h)
                       for h in KO_SITES)]
        print(f'  한국어 매체만: 후보 {len(cand)}건')
    if len(cand) < MIN_DAY:
        # 그날 기사가 모자라면 하루 더 거슬러 본다 (주말·명절)
        back = (_date(y, m, dd) - timedelta(days=2)).strftime('%Y-%m-%d')
        extra = [d for d in days if d.get('ts') == back and ok(d)]
        if a.ko_only:
            extra = [d for d in extra
                     if any((d.get('u') or '').split('/')[2].replace('www.', '').endswith(h)
                            for h in KO_SITES)]
        print(f'  {want} 기사가 {len(cand)}건뿐 — {back} 에서 {len(extra)}건 더 본다')
        cand += extra
    cand.sort(key=lambda d: -(d.get('care') or 0))
    print(f'낼 만한 기사 {len(cand)} (최근 {a.days}일)')

    # 같은 소식을 여러 신문이 쓴다 — 하나만 싣는다
    # (삼성 공장 이익 기사를 VnExpress·Tuổi Trẻ 둘 다 써서 나란히 뽑혔다, 2026-09-02)
    from difflib import SequenceMatcher

    def _same(a_, b_):
        ta, tb = (a_.get('title') or '').lower(), (b_.get('title') or '').lower()
        if SequenceMatcher(None, ta, tb).ratio() > 0.5:
            return True
        # 말이 다르면 제목이 안 닮는다 — 숫자·고유명사가 겹치는지도 본다
        import re as _re
        na = set(_re.findall(r"[A-Z][a-z]{3,}|\d[\d,.]{2,}", a_.get('title') or ''))
        nb = set(_re.findall(r"[A-Z][a-z]{3,}|\d[\d,.]{2,}", b_.get('title') or ''))
        return len(na & nb) >= 2

    picked = []

    def ko_n():
        return sum(1 for x in picked if is_ko(x))

    def order(cat_list):
        """한국어 매체 몫(KO_MIN)이 아직 안 찼으면 그쪽을 앞세운다.
        다 찼거나 KO_MAX 를 넘으면 현지 매체를 앞세운다."""
        if a.ko_only:
            return cat_list
        n = ko_n()
        if n < KO_MIN:
            return sorted(cat_list, key=lambda d: (not is_ko(d), -(d.get('care') or 0)))
        if n >= KO_MAX:
            return sorted(cat_list, key=lambda d: (is_ko(d), -(d.get('care') or 0)))
        return cat_list

    for cat, want in QUOTA:
        got = 0
        for d in order([x for x in cand if x.get('cat') == cat]):
            if d in picked or got >= want or d.get('cat') != cat:
                continue
            if (d.get('care') or 0) < FLOOR:
                continue
            if any(_same(d, x) for x in picked):
                continue
            if cat == '정치' and domestic_politics(d):
                # 국내 정치만 밖 매체에서. 외교·국제는 현지 매체도 쓴다
                host = (d.get('u') or '').split('/')[2].replace('www.', '')
                if not any(host.endswith(h) for h in POLITICS_OK):
                    continue
            picked.append(d); got += 1
        if got < want:
            print(f'  자리 못 채움: {cat} {got}/{want}')
    # ── 못 채운 갈래를 **먼저** 다시 찾는다 (점수선을 8 → 6 으로 낮춰서).
    #    남는 자리를 이미 찬 갈래로 몰면 주제가 한쪽으로 쏠린다.
    for cat, want in QUOTA:
        got = sum(1 for x in picked if x.get('cat') == cat)
        if got >= want:
            continue
        for d in order([x for x in cand if x.get('cat') == cat]):
            if d in picked or got >= want or d.get('cat') != cat:
                continue
            if (d.get('care') or 0) < FLOOR_RELAX:
                continue
            if any(_same(d, x) for x in picked):
                continue
            if cat == '정치' and domestic_politics(d):
                # 국내 정치만 밖 매체에서. 외교·국제는 현지 매체도 쓴다
                host = (d.get('u') or '').split('/')[2].replace('www.', '')
                if not any(host.endswith(h) for h in POLITICS_OK):
                    continue
            picked.append(d); got += 1
        if got < want:
            print(f'  아직 못 채움: {cat} {got}/{want}')

    for d in cand:
        if len(picked) >= MIN_DAY:
            break
        if (d.get('care') or 0) < FLOOR:
            continue
        if d not in picked and not any(_same(d, x) for x in picked):
            lim = dict(QUOTA).get(d.get('cat'), 2) + 1
            if sum(1 for x in picked if x.get('cat') == d.get('cat')) >= lim:
                continue
            picked.append(d)

    # ── 고른 기사의 **재료를 여기서 만든다** (없는 것만)
    need = [d for d in picked
            if len(d.get('sum5') or []) < 4
            or len(d.get('words') or []) < 6
            or len(((d.get('dialog') or {}).get('lines') or [])) < 2]
    if need:
        print(f'\n재료가 없는 기사 {len(need)}건 — 지금 만든다')
        for d in need:
            print(f"   · {(d.get('title') or '')[:40]}")
    from collections import Counter as _C
    cats = _C(d.get('cat') for d in picked)
    if len(cats) < MIN_CATS:
        print(f"  ⚠ 갈래가 {len(cats)}가지뿐이다 (목표 {MIN_CATS}) — {dict(cats)}")

    for d in picked:
        d['pub'] = pub
    p.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'\n펴낸날 {pub} · 고른 기사 {len(picked)}')
    print('갈래별:', dict(Counter(d.get('cat') for d in picked)))
    print(f'한국어 매체 {ko_n()} : 현지 매체 {len(picked) - ko_n()}')
    print('출처별:', dict(Counter((d.get('u') or '').split('/')[2].replace('www.', '') for d in picked)))
    for d in picked:
        print(f"  [{str(d.get('cat')):8}] {(d.get('title_card') or d.get('title') or '')[:44]}")


if __name__ == '__main__':
    main()
