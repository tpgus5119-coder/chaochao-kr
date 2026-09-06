#!/usr/bin/env python3
"""준비 3일 + 일상 20일(하루 단어 10 + 대화 2문장)을 days.json 으로.
검증: 단어 중복 / 문장에 아직 안 배운 낱말 / 모든 단어가 어딘가 문장에 나오는가"""
import json, pathlib, re, sys, collections, unicodedata

def slug(vi):
    """베트남어 → 부호 없는 파일이름 (cảm ơn → cam-on). 그림 파일 이름에 쓴다."""
    s = unicodedata.normalize('NFD', vi)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return s.replace('đ','d').replace('Đ','d').lower().replace(' ','-')

# 부호를 그냥 떼면 tăng 과 tầng 이 똑같이 'tang' 이 된다 — 그림 하나를 두 낱말이 나눠 쓰게 되고
# 둘 중 하나는 반드시 엉뚱한 그림을 보게 된다(실제로 19쌍이 그랬다).
# 겹치는 낱말만 텔렉스로 적는다. 베트남 사람이 자판으로 성조를 치는 그 방식이라 규칙이 명확하다.
TELEX_TONE = {'\u0301':'s', '\u0300':'f', '\u0309':'r', '\u0303':'x', '\u0323':'j'}
TELEX_HAT  = {'\u0302':'a', '\u0306':'w', '\u031b':'w'}   # â→aa ă→aw ơ/ư→ow/uw

def telex(vi):
    """cảm ơn → carm own, tăng → tawng, tầng → taafng. 겹칠 때만 쓴다."""
    out = []
    for syl in vi.split():
        body, tone = [], ''
        for c in unicodedata.normalize('NFD', syl):
            if c in TELEX_TONE: tone = TELEX_TONE[c]
            elif c in TELEX_HAT: body.append(TELEX_HAT[c])
            elif c in 'đĐ': body.append('dd')
            elif not unicodedata.combining(c): body.append(c)
        out.append((''.join(body) + tone).lower())
    return '-'.join(out)
sys.path.insert(0,'tools')
from visuals import attach
from polite import polite      # 앱 글은 모두 존댓말 (사용자 지시)
from hanviet import HANVIET    # 한자어 힌트 — 한 곳에 모아 두고 여기서 채운다
R = pathlib.Path('.')
p1 = json.loads((R/'data/_part1.json').read_text())
days, patches = [], []
for f in ['_b1','_b2','_b3','_b4','_w1','_w2','_b5','_w3','_w4','_b6','_w5','_w6','_b7','_b8','_b9']:
    j = json.loads((R/f'data/{f}.json').read_text())
    days += j['days']
    patches += j.get('patch', [])

# ── 덜어낸 세트 ────────────────────────────────────────────────
# 억지로 늘린 것들을 도로 뺐다. 기준은 '중간관리자가 실제로 쓰는가' 와 '이미 다른 세트에 있는가'.
#   72 가족 자랑과 반려동물 — 반려동물 어휘는 공장에서 안 쓰인다 (가족 이야기는 앞 두 세트에 있다)
#   79 세탁소와 수선집     — 기숙사·아파트면 쓸 일이 없다
#   58 통역 첫걸음        — 우리는 통역을 **쓰는** 쪽이지 하는 쪽이 아니다
#   54 확대해서 검사      — 전자 검사가 셋이나 됐다 (불량 증상·출하 전 검수만 남긴다)
#   86 공정 흐름         — '라인 돌리기' 와 겹친다
#   87 규격 지시         — '작업 표준서 읽기' 와 겹친다
#   98 재고 조사 / 99 상차와 하차 — 창고 넷은 물류 담당 전용이다 ('입고와 출고' 하나면 된다)
# 빼도 다른 세트 문장이 못 배운 낱말을 쓰지 않는 것은 미리 재서 확인했다.
DROP = {54, 58, 72, 79, 86, 87, 98, 99}
days = [x for x in days if x['day'] not in DROP]

# 직무 재배열 — 취업 여정 순서: ①공장 기초(공통, 첫 주에 모두 필요) ②자기 업종 기초
# (봉제→전자→사무) ③직장 문화·계약·행정(공통) ④관리자 화법(공통) ⑤업종 심화
# ⑥창고·물류(공통, 출하는 모든 공장의 마지막 공정). 각 묶음 안은 원래 설계 순서 유지.
# 문장의 '배운 단어만' 규칙이 지켜지는지는 아래 검증이 확인한다.
W_BASE   = [21, 26,27,28,29,30, 35, 37,38,39,40]   # 공장 기초 (공통)
W_SEW    = [22,23,24,25, 31,32,33,34, 36]          # 봉제 기초
WORK_ORDER = (W_BASE + W_SEW + [k for k in range(51,61) if k not in DROP]  # 전자·사무
              + list(range(61,71))                 # 문화·행정 (공통)
              + list(range(81,86)) + [k for k in range(96,101) if k not in DROP]   # 관리자·창고
              + [k for k in range(86,96) if k not in DROP]    # 봉제·전자 심화
              + list(range(107,115)))                # 생산관리 현장어 (관리자 말)
by = {d["day"]: d for d in days}
# 보강 패치 — 딴 소스가 만든 day 에 단어·문장을 덧붙인다 (b8: 수업 5~10강을 흩어 넣기)
for p in patches:
    t = by[p["day"]]
    t["words"] += p.get("words", [])
    t["dialog"]["extra"] += p.get("extra", [])
# ── 일상 차례 — **같은 주제끼리 붙여 놓는다** ──────────────────────
# 교재·어플이 주제별로 묶는 데에는 이유가 있다. 상황이 같으면 문장 틀이 같아서
# 열 낱말을 따로 외우는 대신 한 장면을 통째로 익히게 된다.
# 다만 우리 문장은 '그날까지 배운 낱말로만' 쓰도록 만들어져 있어서, 주제를 모으면
# 몇몇 낱말이 제 차례보다 먼저 나온다. 그 낱말들은 표지에 '미리 만나는 말'로 적어 준다
# (17개뿐이고, 문장 밑 뜻풀이에도 그대로 나온다).
# 묶음 차례는 위반이 가장 적게 나오도록 골랐다 (25건 → 미리 만나는 말로 처리).
# 차례는 **한 주제가 한 덩어리**가 되게 짰다. 교재들(Colloquial Vietnamese, Tiếng Việt 123, VSL)이
# 모두 '장소·상황' 단위로 묶고 그 이름을 단원 제목으로 쓴다 — 그 방식을 따랐다.
# 날씨와 색깔은 같은 주제가 아니고 축구는 명절이 아니다 — 갈라서 어울리는 데로 보냈다.
#   색깔 → 시장에서(무슨 색을 살 것인가) · 날씨·주말·축구 → 스몰토크(말문 트기)
# 묶음 차례는 '그날까지 배운 낱말로만' 규칙을 가장 적게 어기는 순서로 골랐다.
# (식당을 앞으로 당겨 보니 어기는 낱말이 34→75로 두 배가 됐다. 그래서 이 차례다.)
DAILY_HEAD = [1,2,3,4,5,6,         # 첫 인사와 자기소개
              7,8,                 # 숫자 세기
              9,10,19,             # 시간과 요일
              101,11,              # 일과 하루
              17,18,20,            # 부탁하고 약속하기
              45,49,               # 쉬는 날과 명절
              16,47,               # 아플 때 — 약국과 병원
              13,102]              # 시장에서 — 사고 팔기
DAILY_MID  = [43,                  # 시장에서 — 사고 팔기
              44,75,               # 마음과 맞장구
              12,106,104,48,76,77, # 식당에서 — 장보기·과일은 먹고 마시기 바로 뒤
              14,42,80]            # 길과 교통
DAILY_TAIL = [46,50,78,            # 집과 살림 (79 세탁소와 수선집은 뺐다)
              15,71,               # 가족과 고향 (72 반려동물은 뺐다)
              41,74,73]            # 스몰토크 — 날씨 · 주말 · 축구
days = ([by[k] for k in DAILY_HEAD]
        + [by[k] for k in W_BASE] + [by[k] for k in W_SEW]
        + [by[k] for k in DAILY_MID] + [by[k] for k in range(51, 71) if k not in DROP]
        + [by[k] for k in DAILY_TAIL]
        + [by[k] for k in range(81, 86)] + [by[k] for k in range(96, 101) if k not in DROP]
        + [by[k] for k in range(86, 96) if k not in DROP]
        # 생산관리 현장어 — 라인 작업자 말이 아니라 **관리자 말**이라 맨 끝에 둔다
        + [by[k] for k in range(107, 115)])

out = {"meta": {"version":"v4",
                "voices":{"f":"vi-VN-HoaiMyNeural","m":"vi-VN-NamMinhNeural"},
                "track":"일상 기초 (완전 초보)",
                "note":"북부 표준. 하루 = 단어 10개 + 주고받는 대화 2문장 = 1세트."},
       "prep": p1["prep"], "tonedrill": p1["tonedrill"],
       "voweldrill": p1.get("voweldrill", []),
       "ruledrill": p1.get("ruledrill", []), "days": days}

SCENE = {1:"👋",2:"🪪",3:"🌏",4:"😊",5:"❓",6:"🚪",7:"🔢",8:"📦",9:"🕐",10:"📅",
         11:"⏰",12:"🍜",13:"🛒",14:"🗺️",15:"👨‍👩‍👧",16:"🏥",17:"🙏",18:"👍",19:"⏳",20:"🤞"}
# 이모지가 안 붙는 단어(추상어·기능어)는 tools/imgrest.json 이 둘로 갈라 놓았다.
#   draw — 장면으로 그릴 수 있는 말 → 그림 자리를 준다
#   form — 문법 기능어 → 그림 대신 한 줄 공식을 준다
# 기능어에 억지 그림을 붙이면 배우는 사람이 그 그림을 뜻으로 오해한다.
try:
    REST = json.loads((R/'tools/imgrest.json').read_text())
except Exception:
    REST = {}

# 표지 설명·목표를 존댓말로. 원본(tools/b*.py)은 평서체로 두고 여기서 한 번에 바꾼다 —
# 백 몇 줄을 손으로 고치면 다음에 문장을 더할 때 또 섞인다.
for d in out["days"] + out["prep"]:
    for k in ("intro", "goal", "how"):
        if d.get(k): d[k] = polite(d[k])
    for x in d.get("rules", []) or []:
        for k in ("say", "note", "tip"):
            if isinstance(x, dict) and x.get(k): x[k] = polite(x[k])

# 그림 이름을 붙이기 전에, 부호를 떼면 겹치는 낱말들을 먼저 찾아 둔다
_plain = collections.Counter()
for d in out["days"]:
    for w in d["words"]:
        if not w.get("emoji") and (REST.get(w["vi"]) or {}).get("k") == "draw":
            _plain[slug(w["vi"])] += 1
CLASH = {s for s, n in _plain.items() if n > 1}

for d in out["days"]:
    used = set()
    for w in d["words"]:
        attach(w)
        # 한자어 힌트 — 낱말 파일에 없으면 표에서 채운다 (표에 있는 것이 우선하지 않는다)
        if not w.get("hanja") and w["vi"] in HANVIET:
            w["hanja"] = HANVIET[w["vi"]]
        # 구체어(이모지가 붙는 단어)만 그림 파일 자리를 준다. img/ 에 파일을 넣으면 그걸 보여준다.
        if w.get("emoji"):
            s = slug(w["vi"])                      # 부호를 떼면 겹칠 수 있다 (đau/đầu → dau)
            if s in used: s += "2"
            used.add(s)
            w["img"] = f"d{d['day']:02d}-{s}.webp"
        else:
            r = REST.get(w["vi"])
            if r and r.get("k") == "draw":
                base = slug(w["vi"])
                w["img"] = "x-" + (telex(w["vi"]) if base in CLASH else base) + ".webp"
            elif r and r.get("k") == "form":
                w["form"] = r.get("f", "")
                if r.get("e"): w["fex"] = r["e"]
    d["dialog"]["emoji"] = SCENE.get(d["day"], "")
    d["dialog"]["img"] = f"d{d['day']:02d}-scene.webp"

CAT = {**{k:'공통' for k in [21,26,27,28,29,30,35,37,38,39,40]},
       **{k:'봉제' for k in [22,23,24,25,31,32,33,34,36]},
       **{k:'전자' for k in range(51,56)}, **{k:'사무' for k in range(56,61)},
       **{k:'공통' for k in range(61,71)},
       **{k:'공통' for k in list(range(81,86))+list(range(96,101))},
       **{k:'봉제' for k in range(86,91)}, **{k:'전자' for k in range(91,96)}}
for d in out["days"]:
    dd = d["day"]
    if dd in CAT: d["cat"] = CAT[dd]
dn = wn = 0
for d in out["days"]:
    if d.get("track") == "work": wn += 1; d["n"] = wn
    else: dn += 1; d["n"] = dn                   # Day N = 나온 차례 (삽입해도 이어진다)

seen = collections.defaultdict(list)
for d in out["days"]:
    for w in d["words"]: seen[w["vi"]].append(d["day"])
dups = {k:v for k,v in seen.items() if len(v)>1}

PROPER = {"hàn","quốc","việt","nam","minsu","nguyễn","văn","hùng","trần","thị","lan",
          "hà","nội","busan","nghệ"}
toks = lambda s: [t for t in re.split(r"[\s,.!?]+", s) if t]
vocab, bad, PRE = set(), [], {}
for d in out["days"]:
    for w in d["words"]: vocab.update(t.lower() for t in w["vi"].split())
    texts = [l["vi"] for l in d["dialog"]["lines"]] + [x["vi"] for x in d["dialog"]["extra"]]
    for txt in texts:
        for t in toks(txt):
            lt=t.lower()
            if lt in PROPER or lt in vocab: continue
            bad.append((d["day"], txt, t))
            PRE.setdefault(d["day"], {})[lt] = None

# 제 차례보다 먼저 나오는 낱말 → 표지의 '미리 만나는 말'. 뜻은 그 낱말을 가르치는 날에서 가져온다.
MEAN = {}
for d in out["days"]:
    for w in d["words"]:
        MEAN.setdefault(w["vi"].lower(), (w["vi"], w["ko"]))
        if len(w["vi"].split()) > 1:
            for t in w["vi"].split(): MEAN.setdefault(t.lower(), (w["vi"], w["ko"]))
lost = []
for d in out["days"]:
    ts = PRE.get(d["day"])
    if not ts: continue
    pre = []
    for t in sorted(ts):
        m = MEAN.get(t)
        if m: pre.append({"vi": m[0], "ko": m[1]})
        else: lost.append((d["day"], t))
    seen_vi = set(); d["pre"] = [x for x in pre if not (x["vi"] in seen_vi or seen_vi.add(x["vi"]))]
print(f"미리 만나는 말 {sum(len(d.get('pre',[])) for d in out['days'])}개 / 어디에도 없는 낱말 {len(lost)}건 {lost}")

# 모든 단어가 어딘가 문장에 나오는가
unused=[]
for d in out["days"]:
    txt=' '.join([l["vi"] for l in d["dialog"]["lines"]]+[x["vi"] for x in d["dialog"]["extra"]]).lower()
    for w in d["words"]:
        if w["vi"].lower() not in txt: unused.append((d["day"], w["vi"]))

nw=sum(len(d["words"]) for d in out["days"])
print(f"준비 {len(out['prep'])}일 + Day {len(out['days'])}일 / 단어 {nw} (고유 {len(seen)})")
print(f"대화 {len(out['days'])}개 · {sum(len(d['dialog']['lines']) for d in out['days'])}문장"
      f" / 바꿔말하기 {sum(len(d['dialog']['extra']) for d in out['days'])}")
print("\n중복 단어:", dups or "없음")
print(f"미학습 낱말 {len(bad)}건:")
for a in bad: print('   Day%-3s "%s"  ←  %s' % a)
print(f"\n문장에 안 나오는 단어 {len(unused)}건:")
for a in unused: print('   Day%-3s %s' % a)

if "--write" in sys.argv and not lost and not dups:
    (R/'data/days.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("\n→ days.json 기록")
elif "--write" in sys.argv:
    print("\n→ 문제가 있어 기록하지 않음")
