#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""목차 — **네 기수가 실제로 배운 차례**대로 짠다 → data/_toc_real.json

앞선 초안(toc_draft.py)과 다른 점 (2026-08-30)
  앞엣것은 내가 주제 이름을 먼저 정해 놓고 낱말을 밀어 넣었다. 그래서 2,719개가
  갈 곳을 못 찾았다. **순서를 지어낸 것**이 문제였다.
  선배 시험지에는 순서가 이미 적혀 있다 — 회차 번호가 곧 배운 날짜다.
  네 기수의 '처음 나온 회차'를 0~1 로 맞춰 가운뎃값을 내면 그게 공통 차례다.
  그 차례를 **급**으로 자르고, 급 안에서만 주제로 묶는다. 그러면 남는 낱말이 없다.

읽어 낸 차례 (pos 10% 구간, 실측)
   0~10  탈것·먹을것·사람  |  10~20 기본 동사   |  20~30 길·방향
  30~40  일상 문장·전화     |  40~50 식당·호텔·공항
  50~60  몸·병원·맛        |  60~70 사회·일 시작 |  70~80 회사·태도
  80~90  여가·사무기기      |  90~100 공장·사무 실무
  → **앞은 살아남기, 뒤는 일하기.** 1년 과정이 그렇게 짜여 있었다.
쓰기: python3 tools/toc_real.py
"""
import json, pathlib, re, collections

R = pathlib.Path(__file__).resolve().parent.parent
PER = 10

# 급 = 배운 차례를 자른 것. (이름, pos 시작, pos 끝)
LEVEL = [("1급 첫걸음",      .00, .08), ("2급 눈앞의 것",   .08, .18),
         ("3급 하루 살기",   .18, .30), ("4급 오가기",      .30, .42),
         ("5급 먹고 자기",   .42, .54), ("6급 몸과 마음",   .54, .66),
         ("7급 사람 사이",   .66, .78), ("8급 배우고 일하기",.78, .90),
         ("9급 일터에서",    .90, 1.01)]

# 급 안에서 묶는 뜻갈래. 걸리지 않으면 품사 갈래로 간다.
THEME = [
 ("인사와 부름", r"인사|안녕|고맙|감사|미안|죄송|잘 가|반갑|형$|누나|오빠|언니|동생|아저씨|아줌마|할아버지|할머니|여보세요"),
 ("나와 남",   r"이름|나이|살$|생일|소개|직업|국적|나라|한국|베트남|중국|일본|미국|사람$|친구|가족|아빠|엄마|아들|딸|남편|아내|결혼"),
 ("수와 셈",   r"숫자|하나|둘$|셋$|넷$|다섯|여섯|일곱|여덟|아홉|열$|백$|천$|만$|백만|몇$|번째|얼마|개$|명$|장$|킬로|그램|미터|리터|도$|무게|길이|넓이"),
 ("때",       r"시간|시$|분$|초$|아침|점심|저녁|밤$|새벽|오전|오후|어제|오늘|내일|모레|요일|월요|화요|수요|목요|금요|토요|일요|주말|달$|월$|년$|해$|작년|올해|내년|계절|봄$|여름|가을|겨울|지금|먼저|나중|이미|아직|벌써"),
 ("곳과 방향", r"길$|방향|왼쪽|오른쪽|앞$|뒤$|옆|위$|아래|안$|밖$|사이|맞은편|가까|멀$|직진|건너|사거리|골목|여기|거기|저기|어디"),
 ("탈것과 오가기", r"버스|택시|기차|오토바이|자전거|비행기|배$|역$|공항|정류장|타다|내리다|운전|주차|가다|오다|돌아|출발|도착|여행|출장|짐$|표$|요금"),
 ("먹고 마시기", r"먹|마시|밥$|국$|국수|쌀국수|고기|생선|채소|과일|반찬|빵$|계란|쌀$|물$|음료|차$|커피|주스|우유|맥주|술$|맛|짜다|달다|맵|시다|배고|배부|식당|주문|메뉴|계산서"),
 ("사고팔기",  r"사다|팔다|시장|가게|상점|마트|물건|손님|주인|값|가격|비싸|싸다|돈$|계산|영수증|할인|깎|현금|카드|봉지"),
 ("집과 살림", r"집$|방$|화장실|부엌|거실|침실|문$|창문|층$|계단|마당|가구|침대|의자|책상|소파|책꽂이|꽃병|카펫|거울|서랍|청소|빨래|이사"),
 ("몸과 아픔", r"몸|머리|눈$|코$|입$|귀$|손$|발$|배$|다리|팔$|어깨|얼굴|이빨|아프|병원|약$|의사|간호|기침|감기|열$|다치|건강|피곤|졸리"),
 ("모습과 성질", r"크$|작$|길$|짧$|넓$|좁$|굵$|가늘|두껍|얇|무겁|가볍|높$|낮$|빠르|느리|새$|낡|예쁘|못생|뚱뚱|마르|늙|젊|어리|색|빨강|파랑|노랑|검|하양"),
 ("마음과 성격", r"기쁘|슬프|화나|무섭|걱정|사랑|좋아|싫|착하|나쁘|똑똑|멍청|게으|부지런|조용|시끄|친절|얌전|자신|수줍|재미|지루|편하|불편|만족|후회|긴장|외롭"),
 ("배우기",    r"배우|가르|공부|학교|학생|선생|수업|교실|숙제|시험|점수|졸업|입학|대학|책$|글자|문법|발음|읽|쓰다|외우|질문|대답|연습|복습"),
 ("일하기",    r"일하|회사|사무|직장|팀$|부서|출근|퇴근|월급|휴가|회의|보고|계획|서류|전화|이메일|약속|맡|담당|책임|협력|처리|해결"),
 ("공장에서",  r"생산|공장|현장|작업|기계|설비|공정|조립|가공|부품|자재|원단|불량|검사|규격|포장|출고|입고|재고|창고|납기|안전|봉제|재봉|미싱|재단|원료|품질"),
 ("사회와 세상", r"나라|정부|법$|규정|사회|경제|정치|문화|역사|환경|자연|문제|이유|원인|결과|영향|변화|발전|사건|소식|신문|뉴스"),
]
POS = [("움직이는 말", r"(하)?다$|되다$|시키다$|가다$|오다$|보다$|주다$|받다$"),
       ("꾸미는 말",  r"[은는]$|[다]$"), ("이름 붙은 말", r".")]

def bucket(ko, pats):
    for name, rx in pats:
        if re.search(rx, ko): return name
    return None

def main():
    p = R / "data" / "senior_pool.json"
    if not p.exists(): raise SystemExit("senior_pool.json 먼저 (tools/senior_merge.py)")
    ws = [w for w in json.loads(p.read_text(encoding="utf-8"))["words"] if w.get("ko")]
    th = [(n, re.compile(r)) for n, r in THEME]
    ps = [(n, re.compile(r)) for n, r in POS]
    lv = collections.OrderedDict((n, collections.OrderedDict()) for n, _, _ in LEVEL)
    # 1차: 차례를 아는 낱말을 급에 넣는다
    theme_of = {}
    for w in ws:
        theme_of[id(w)] = bucket(w["ko"], th) or ("그 밖 · " + (bucket(w["ko"], ps) or "이름 붙은 말"))
    known = [w for w in ws if w.get("pos") is not None]
    for w in known:
        name = next((n for n, a, b in LEVEL if a <= w["pos"] < b), LEVEL[-1][0])
        lv[name].setdefault(theme_of[id(w)], []).append(w)
    # 2차: 차례를 모르는 낱말(주간·날짜 시험지에만 나온 것)은
    #      **같은 뜻갈래가 주로 놓인 급**으로 보낸다 — 버리지 않는다.
    home = {}
    for name, units in lv.items():
        for t, arr in units.items(): home.setdefault(t, []).append((len(arr), name))
    home = {t: max(v)[1] for t, v in home.items()}
    tail = []
    for w in ws:
        if w.get("pos") is not None: continue
        t = theme_of[id(w)]
        name = home.get(t)
        if not name: tail.append(w); continue
        lv[name].setdefault(t, []).append(w)
    out, tot, ch = [], 0, 0
    for name, units in lv.items():
        us = sorted(units.items(), key=lambda x: -len(x[1]))
        u2 = []
        for t, arr in us:
            arr.sort(key=lambda w: (-w["n"], w["pos"] if w["pos"] is not None else 1.0))
            n = max(1, round(len(arr) / PER))
            u2.append({"unit": t, "words": len(arr), "chapters": n,
                       "sample": [w["ko"][:9] for w in arr[:8]]})
            tot += len(arr); ch += n
        out.append({"level": name, "words": sum(u["words"] for u in u2), "units": u2})
    (R / "data" / "_toc_real.json").write_text(json.dumps(
        {"note": "네 기수가 배운 차례(pos)로 급을 자르고, 급 안에서 뜻으로 묶었다.",
         "levels": out, "unplaced": len(tail)}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"담긴 낱말 {tot} · 강 {ch} · 차례를 모르는 낱말 {len(tail)}")
    for L in out:
        print(f"\n■ {L['level']} — {L['words']}개")
        for u in L["units"]:
            print(f"    {u['words']:>4}개 {u['chapters']:>2}강  {u['unit']:<16} {' · '.join(u['sample'][:6])}")
main()
