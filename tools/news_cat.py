#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""기사 갈래를 **세 겹으로** 정한다 → 후보 목록의 'cat' 을 고쳐 놓는다

대표님 지시 (2026-09-02): "기사마다 이미 자체적으로 분류되어 있지 않니?
                          있으면 그 분류를 1차로 믿고, 우리의 검수로 주제 분류해도 된다."

## 왜
낱말 맞추기만 하면 '삼성전자 수출 호조' 기사가 '총리 회담' 때문에 정치로 간다 (실측).
기사 사이트는 이미 편집자가 갈래를 달아 두었다. 그것부터 믿는 것이 옳다.

## 세 겹
① **사이트 자체 분류** — <meta article:section> 을 읽어 우리 갈래로 옮긴다 (공짜·즉시)
② **Qwen 검수** — 제목과 본문 첫머리를 보여 주고 갈래를 고르게 한다 (공짜, 12건에 약 1분)
③ **둘이 다르면** 우리 낱말 점수(cat_of)로 결정한다

Qwen 은 **고르는 일**만 한다 — 갈래 여섯 중 하나를 짚는 것이라 지어낼 자리가 없다.

쓰기: 다른 도구에서 `from news_cat import recat; recat(cand)`
"""
import json, re, subprocess, sys, pathlib

CATS = ['일자리', '공장·산업', '경제', '사회', '정치', '문화·생활']

# 기사 사이트의 갈래 → 우리 갈래
SITE_MAP = {
    # 인사이드비나
    '정치': '정치', '경제': '경제', '금융·부동산': '경제',
    '사회·문화': '사회', '여행·로컬': '문화·생활',
    '베트남 인사이트 랩': '경제', '칼럼·오피니언': '경제',
    # 베트남코리아타임즈
    '현지속살': '문화·생활', '베트남 한걸음 더': '문화·생활', '세계 공급망': '공장·산업',
    # VnExpress International
    'news': '사회', 'business': '경제', 'travel': '문화·생활', 'life': '문화·생활',
    'sports': '문화·생활', 'world': '정치', 'tech': '공장·산업',
}
SEC = re.compile(r'article:section" content="([^"]*)"')


def site_cat(url, html=None):
    """기사에 달린 자체 갈래를 읽는다. 못 읽으면 None."""
    try:
        if html is None:
            html = subprocess.run(['curl', '-sSL', '-m', '15', '-A', 'Mozilla/5.0', url],
                                  capture_output=True, text=True, timeout=25).stdout
        m = SEC.search(html or '')
        return SITE_MAP.get(m.group(1).strip()) if m else None
    except Exception:
        return None


ASK = ('아래 기사들을 갈래로 나누어라. 갈래는 이 여섯 중 하나만 고른다:\n'
       '  일자리 — 채용·비자·노동허가·임금·근로조건\n'
       '  공장·산업 — 제조·생산·공단·기술·물류\n'
       '  경제 — 수출입·투자·물가·환율·부동산·기업 실적\n'
       '  사회 — 사고·범죄·교통·보건·교육·날씨·행정 단속\n'
       '  정치 — 국회·외교·법·선거·당\n'
       '  문화·생활 — 관광·음식·축제·명절·스포츠·연예\n'
       '규칙: 반드시 여섯 중 하나. 새 갈래를 만들지 마라. 애매하면 본문에서 가장 많이 다루는 쪽으로.\n'
       '출력은 JSON 배열만: [{"i":번호,"cat":"갈래"}]\n\n')


def recat(cands):
    """후보 목록의 cat 을 세 겹으로 고쳐 놓는다. 목록을 그 자리에서 고친다."""
    # ① 사이트 자체 분류
    n_site = 0
    for c in cands:
        sc = site_cat(c['u'])
        if sc:
            c['site_cat'] = sc; n_site += 1
    # ② Qwen 검수
    ai = {}
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        from qwen import ask_json, up
        if up():
            items = [{'i': i, '제목': c['t'], '본문': (c.get('body') or '')[:220]}
                     for i, c in enumerate(cands)]
            got = ask_json(ASK, items, chunk=6, max_tokens=1200) or []
            for g in got:
                if isinstance(g, dict) and str(g.get('cat')) in CATS:
                    try:
                        ai[int(g['i'])] = g['cat']
                    except Exception:
                        pass
    except Exception as e:
        print(f'  Qwen 갈래 검수 건너뜀: {e}')
    # ③ 결정
    agree = 0
    for i, c in enumerate(cands):
        site, a = c.get('site_cat'), ai.get(i)
        if site and a and site == a:
            c['cat'] = site; agree += 1
        elif site and a:
            pass                       # 둘이 다르면 우리 낱말 점수(이미 들어 있는 cat)를 쓴다
        elif site:
            c['cat'] = site
        elif a:
            c['cat'] = a
    print(f'  갈래: 사이트가 알려준 것 {n_site} · Qwen 이 본 것 {len(ai)} · 둘이 같은 것 {agree}')
