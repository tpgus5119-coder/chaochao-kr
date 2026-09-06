#!/usr/bin/env python3
"""한국어 모의고사 출제기 — 시험 '형식'을 따르되 문항은 우리가 만든다.

왜 이렇게 만드나:
  EPS 표준교재·공개문항, KIIP 교재·평가 견본은 모두 '변경금지' 또는 라이선스 미표시다.
  즉 기출 문항을 그대로 옮겨 쓰는 건 못 한다. 반면 시험의 **형식**(몇 문항, 어떤 유형,
  몇 분)은 저작물이 아니라 사실이라 그대로 따라도 된다. 그래서 형식만 베끼고
  문항은 우리 어휘 자료(국립국어원 학습용 어휘 5,744 + krdict 뜻풀이)로 새로 찍는다.

오답 보기 고르는 법:
  같은 등급(A/B/C) + 같은 품사에서만 뽑는다. 등급이 섞이면 난이도가 튀고,
  품사가 섞이면 뜻을 몰라도 형태만 보고 답이 찍힌다.
"""
import json, os, random, re, sys, unicodedata
import ko_content
import ko_content_t2
import ko_society
import ko_speak_topik
import ko_t1_listen as L1
import ko_t1_read as R1
import ko_t2_listen as L2
import ko_t2_read as R2
import topik_blueprint as BP
import gen_charts

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
TOOLS = os.path.dirname(os.path.abspath(__file__))

def load():
    words = json.load(open(os.path.join(DATA, "_ko_words.json"), encoding="utf-8"))
    gloss = json.load(open(os.path.join(DATA, "_ko_vi_gloss.json"), encoding="utf-8"))
    days = json.load(open(os.path.join(DATA, "days.json"), encoding="utf-8"))
    # 베트남어 과정에 붙여 둔 그림을 한국어 뜻으로 되짚어 재사용한다
    pics = {}
    for d in days["days"]:
        for w in d.get("words") or []:
            if w.get("img") and w.get("ko"):
                pics.setdefault(w["ko"].split("(")[0].strip(), w["img"])
    return words, gloss, pics

def clean_dfn(s):
    """뜻풀이에 표제어가 그대로 박혀 있으면 답이 새어 나간다 — 그런 건 안 쓴다."""
    return (s or "").strip()

def vi_tokens(s):
    """'y tá, bác sĩ' → {'y tá','bác sĩ'}. 뜻이 겹치는 보기를 걸러내는 데 쓴다."""
    return {t.strip().lower() for t in str(s or "").split(",") if t.strip()}


# ── 유의어·반의어·의미범주 (국립국어원 등급별 어휘 12,010) ───────────
# 왜 필요했나 — 두 가지다.
#  ① **정답이 둘이 되는 문항을 막는다.** 오답을 '같은 등급·같은 품사'에서만 뽑았더니
#     정답의 유의어가 오답 자리에 앉는 일이 생겼다. '가격'을 묻는데 보기에 '값'이 있으면
#     그건 틀린 보기가 아니라 또 하나의 정답이다. 뜻풀이형(dfn2word)과
#     뜻→낱말형(vi2word)에서 특히 그렇다.
#  ② **오답을 그럴듯하게 만든다.** 반의어와 같은 의미범주의 낱말은 뜻이 가깝되
#     분명히 답이 아니라서, 뜻을 정확히 아는 사람만 가려낸다.
#     지금은 '같은 등급·같은 품사'뿐이라 뜻이 아주 먼 낱말이 보기에 섞인다.
def _load_lex():
    syn, ant, cat = {}, {}, {}
    p = os.path.join(TOOLS, "nikl_12019.tsv")
    if not os.path.exists(p):
        return syn, ant, cat
    def heads(v):
        # '가급적01/가급적' · '증속00' · '가뜩|가뜩이00' → {'가급적','증속','가뜩','가뜩이'}
        out = set()
        for chunk in re.split(r"[|/]", v or ""):
            w = re.sub(r"\d+$", "", chunk.strip().lstrip("-")).strip()
            if w:
                out.add(w)
        return out
    with open(p, encoding="utf-8") as f:
        head = f.readline().rstrip("\n").split("\t")
        wi, si, ai = head.index("어휘"), head.index("유의어"), head.index("반의어")
        bi, mi = head.index("대범주"), head.index("소범주")
        for line in f:
            c = line.rstrip("\n").split("\t")
            if len(c) <= mi:
                continue
            for w in heads(c[wi]):
                if c[si]:
                    syn.setdefault(w, set()).update(heads(c[si]))
                if c[ai]:
                    ant.setdefault(w, set()).update(heads(c[ai]))
                if c[bi] or c[mi]:
                    cat.setdefault(w, set()).add((c[bi], c[mi]))
    # 유의어는 서로를 가리켜야 한다 — 한쪽에만 적혀 있는 짝이 많다
    for a, bs in list(syn.items()):
        for b in bs:
            syn.setdefault(b, set()).add(a)
    return syn, ant, cat


SYN, ANT, CAT = _load_lex()


def is_syn(a, b):
    """둘이 서로 유의어인가 — 오답으로 쓰면 정답이 둘이 된다."""
    return b in SYN.get(a, ()) or a in SYN.get(b, ())


def close_to(a, b):
    """뜻이 가까운가 — 반의어이거나 의미범주가 같으면 그럴듯한 오답이 된다."""
    if b in ANT.get(a, ()) or a in ANT.get(b, ()):
        return True
    ca, cb = CAT.get(a), CAT.get(b)
    return bool(ca and cb and (ca & cb))

def pick_distractors(rng, answer, pool_by_key, key, n=3, distinct_vi=False, show=None):
    """오답은 같은 등급·같은 품사에서만 뽑는다.

    distinct_vi=True 면 보기끼리 베트남어 뜻이 한 조각도 겹치지 않게 한다 —
    보기 넷의 뜻이 겹치면 정답이 둘이 되어 문제가 깨진다.

    show 를 주면 **화면에 보이는 글자 길이**까지 맞춘다. 왜 필요한가:
    뜻이 'sự nghèo khó, cái nghèo' 처럼 길게 적힌 낱말이 정답이고 오답은 한 낱말뿐이면,
    한국어를 몰라도 '제일 긴 것'을 찍어 맞힌다. 실제로 만들어 놓고 세어 보니
    1,274문항 가운데 118개가 그렇게 찍히는 문항이었다.
    """
    pool = pool_by_key.get(key, [])
    cands = [w for w in pool if w["ko"] != answer["ko"]]
    # ① 정답의 **유의어는 오답이 될 수 없다** — 그건 틀린 보기가 아니라 또 하나의 정답이다.
    #    '가격'을 묻는데 보기에 '값'이 있으면 문항이 깨진다.
    kept = [w for w in cands if not is_syn(answer["ko"], w["ko"])]
    if len(kept) >= n:
        cands = kept
    if len(cands) < n:
        return None
    # ② 뜻이 가까운 것(반의어·같은 의미범주)을 **먼저** 쓴다. 뜻이 아주 먼 낱말이
    #    보기에 섞이면 한국어를 몰라도 어울리지 않는 것을 지워 가며 맞힌다.
    near = [w for w in cands if close_to(answer["ko"], w["ko"])]

    alen = len(str(show(answer))) if show else 0

    def len_ok(pick):
        """정답이 **유일하게** 가장 길거나 짧으면 안 된다.

        예전 규칙은 길이 차가 12자 이상일 때만 봤다. 그랬더니 몇 자 차이가
        문항마다 쌓여, 시험 전체로는 '긴 보기 찍기'가 57.8% 맞는 시험이 됐다
        (우연 25%). 이제 차이가 작아도 정답이 홀로 끝값이면 다시 뽑는다."""
        if not show:
            return True
        L = [alen] + [len(str(show(w))) for w in pick]
        mx, mn = max(L), min(L)
        if alen == mx and L.count(mx) == 1:
            # 아예 금지하면 반대 단서가 생긴다("긴 것은 답이 아니다" — 실측 7.3%까지
            # 떨어졌다). 우연과 같은 4분의 1 확률로는 정답이 가장 길어도 둔다.
            # 단, **차이가 클 때는 안 된다.** 이 4분의 1 허용이 26자 대 8자짜리까지
            # 통과시켜, 뜻을 몰라도 눈으로 찍히는 문항 다섯 개를 흘려보냈다.
            return mx - mn < 12 and rng.random() < 0.25
        if alen == mn and L.count(mn) == 1:
            return mx - mn < 12 and rng.random() < 0.25
        # 정답이 최장(또는 최단)을 다른 보기와 **나눠 가져도** 차이가 크면 안 된다.
        # '홀로 끝값'만 막았더니, 5자와 17자가 섞인 판에서 정답이 17자 쪽에 동률로
        # 앉는 문항이 새어 나왔다. 둘 중 하나를 찍으면 절반이라 여전히 단서다.
        if alen in (mx, mn) and mx - mn >= 12:
            return False
        return True

    def extreme(pick):
        """정답이 홀로 끝값이고 차이도 큰가 — 대체 후보로도 못 쓸 만큼 나쁜 조합."""
        if not show:
            return False
        L = [alen] + [len(str(show(w))) for w in pick]
        return (max(L) - min(L) >= 12) and (alen in (max(L), min(L)))

    best = None
    for t in range(120):
        # 앞쪽 시도에서는 뜻이 가까운 것을 섞어 뽑는다. 다 가까운 것으로만 채우면
        # 매번 같은 보기가 나와 회차끼리 겹치므로, 가까운 것 한둘 + 나머지로 짠다.
        if t < 80 and len(near) >= 2:
            k = min(len(near), 2 if n >= 3 else 1)
            head = rng.sample(near, k)
            rest = [w for w in cands if w not in head]
            if len(rest) < n - k:
                continue
            pick = head + rng.sample(rest, n - k)
            rng.shuffle(pick)
        else:
            pick = rng.sample(cands, n)
        if distinct_vi:
            sets = [vi_tokens(answer.get("vi"))] + [vi_tokens(w.get("vi")) for w in pick]
            if any(not s for s in sets):
                continue
            if any(sets[i] & sets[j]
                   for i in range(len(sets)) for j in range(i + 1, len(sets))):
                continue
        # 대체 후보도 골라 둔다 — 극단 조합은 마지막의 마지막에만 쓴다
        if best is None or (extreme(best) and not extreme(pick)):
            best = pick
        if len_ok(pick):
            return pick
    # 120번을 뽑아도 전부 극단이면 **그 낱말은 포기한다.**
    # 뜻이 'trường trung học phổ thông'(26자)처럼 유난히 긴 낱말은 같은 등급·품사
    # 안에 길이가 맞는 짝이 아예 없다. 그런 낱말로 문항을 만들면 한국어를 몰라도
    # 제일 긴 것을 찍어 맞는다. 없는 낱말을 억지로 쓰느니 다른 낱말을 고르는 게 낫다
    # (바깥 고리가 4,000번까지 다른 낱말로 다시 시도한다).
    return None if best is not None and extreme(best) else best

def mk_choice_q(rng, answer, distractors, stem, show, qtype, extra=None, note=None):
    """note(보기, 정답인가) → 그 보기 한 줄 해설. 보기 순서가 바뀌어도 같이 따라간다."""
    opts = distractors + [answer]
    rng.shuffle(opts)
    q = {
        "type": qtype,
        "stem": stem,
        "options": [show(o) for o in opts],
        "answer": opts.index(answer),
        "word": answer["ko"],
    }
    if note:
        q["exp"] = [note(o, o is answer) for o in opts]
    if extra:
        q.update(extra)
    return q


def one_sense(v):
    """보기에는 뜻을 하나만 보여 준다.

    사전에 뜻이 여럿 달린 낱말('sự ghi chép, sự ghi hình, bản ghi')이 정답이고
    오답은 한 낱말짜리면, 뜻을 몰라도 '제일 긴 것'을 찍어 맞힌다.
    그렇다고 뜻을 지어낼 수는 없으니, **첫 번째 뜻만** 보여 준다 —
    틀린 말이 아니고, 보기 넷의 길이도 고만고만해진다.
    (겹침 검사는 여전히 뜻 전체로 한다 — 정답이 둘이 되는 것은 막아야 하니까)
    """
    return str(v or "").split(",")[0].strip() or str(v or "")


def gl(w):
    """'낱말(뜻)' 한 덩어리 — 해설에서 되풀이해 쓴다."""
    v = (w.get("vi") or "").split(",")[0].strip()
    return f"'{w['ko']}'" + (f"({v})" if v else "")

# ── 문항 유형 ────────────────────────────────────────────────
def q_dfn2word(rng, w, gloss, pool_by_key):
    """뜻풀이를 주고 단어를 고르게 한다 (TOPIK·KIIP 어휘 유형)."""
    g = gloss.get(w["ko"]) or {}
    dfn = clean_dfn(g.get("ko_dfn"))
    if not dfn or w["ko"] in dfn:
        return None
    d = pick_distractors(rng, w, pool_by_key, (w["grade"], w["pos"]),
                         distinct_vi=True, show=lambda o: o["ko"])
    if not d:
        return None
    return mk_choice_q(rng, w, d, f"다음 설명에 맞는 단어는?\n{dfn}",
                       lambda o: o["ko"], "dfn2word",
                       note=lambda o, a: (f"맞습니다. 설명이 가리키는 말이 {gl(w)}입니다."
                                          if a else f"{gl(o)}. 설명과 뜻이 다릅니다."))

def q_word2vi(rng, w, gloss, pool_by_key):
    """단어를 주고 베트남어 뜻을 고르게 한다 (학습자 자가 점검용)."""
    if not w.get("vi"):
        return None
    d = pick_distractors(rng, w, pool_by_key, (w["grade"], w["pos"]),
                         distinct_vi=True, show=lambda o: one_sense(o["vi"]))
    if not d:
        return None
    return mk_choice_q(rng, w, d, f"'{w['ko']}'의 뜻으로 알맞은 것은?",
                       lambda o: one_sense(o["vi"]), "word2vi",
                       note=lambda o, a: (f"맞습니다. {gl(w)}."
                                          if a else f"이 뜻은 '{o['ko']}'입니다."))

def q_vi2word(rng, w, gloss, pool_by_key):
    """베트남어 뜻을 주고 한국어 단어를 고르게 한다 (산출 방향 — 더 어렵다)."""
    if not w.get("vi"):
        return None
    d = pick_distractors(rng, w, pool_by_key, (w["grade"], w["pos"]),
                         distinct_vi=True, show=lambda o: o["ko"])
    if not d:
        return None
    return mk_choice_q(rng, w, d, f"'{w['vi']}'에 해당하는 한국어는?",
                       lambda o: o["ko"], "vi2word",
                       note=lambda o, a: (f"맞습니다. {gl(w)}."
                                          if a else f"{gl(o)}. 물어본 뜻이 아닙니다."))

# 그림 문항에 쓸 수 있는 낱말 — 그림 하나만 보고 그 말이 딱 떠오르는 것만 손으로 골랐다.
#
# 왜 손으로 골랐나: 그림은 베트남어 과정에 붙여 둔 것을 되쓰는데, 거기엔 동사·부사·
# 추상명사에도 그림이 있다("더", "가다", "세금"). 베트남어 수업에서는 앞뒤 문맥이 있어
# 통했지만, 시험 문항으로 그림만 떼면 무슨 뜻인지 알 길이 없다. 품사만으로는 못 거른다
# ("세금"도 명사다). 그래서 191개 명사를 눈으로 훑어 구체물만 남겼다.
#
# 오답도 반드시 이 목록에서 뽑는다 — 오답이 그림으로 못 그릴 말이면
# 그림을 안 보고도 "저건 그림이 안 되니 답이 아니다"로 찍어 맞힐 수 있다.
#
# 몸의 부위(손·코·입·머리)는 뺐다. 시험지를 실제로 그려 보고 알았다 —
# 테이프 그림이 "손에 들린 테이프"였는데 오답에 '손'이 있어 정답이 둘처럼 보였다.
# 물건 그림에는 그걸 쥔 손·사람이 딸려 나오는 일이 흔해서, 몸 부위는 오답으로 못 쓴다.
#
# 상위 개념어도 뺐다('야채'는 감자·당근·오이·토마토를 다 아우르고, '볶음밥'은 '밥'과 겹친다).
# 토마토 그림에 오답으로 '야채'가 붙으면 둘 다 맞는 말이라 다툴 거리가 된다.
PIC_OK = set("""
가위 감자 개 계단 고양이 고추 골목 공장 공항 구름 기계 기숙사 길 노래방 눈 단추 달걀
닭고기 당근 대사관 돈 돼지 두부 딸기 마늘 맥주 문 바나나 바늘 바지 밥 버스 병원
복숭아 비닐봉지 비행기 사과 사진 사탕 서류 선물 수박 숟가락 시장 신발 실
쓰레기 아이스크림 약 약국 엘리베이터 여권 오이 우산 은행 의자 자 장갑 전선
정류장 종이 주머니 지갑 집 창고 천 칼 커피 컴퓨터 택시 테이프 토마토 통로 호텔 화장실
""".split())

def q_pic2word(rng, w, gloss, pool_by_key, pics, pic_pool):
    """그림을 보고 단어를 고르게 한다 (EPS [1~4], KIIP [1~2] 유형)."""
    key = w["ko"].split("(")[0].strip()
    if key not in PIC_OK:
        return None
    img = pics.get(key)
    if not img:
        return None
    cands = [x for x in pic_pool if x["ko"] != w["ko"]]
    if len(cands) < 3:
        return None
    d = rng.sample(cands, 3)
    return mk_choice_q(rng, w, d, "그림에 맞는 것을 고르십시오.",
                       lambda o: o["ko"], "pic2word", extra={"img": img},
                       note=lambda o, a: (f"맞습니다. 그림은 {gl(w)}입니다."
                                          if a else f"{gl(o)}. 그림과 다릅니다."))

# 조사 문항 — 문틀은 직접 썼다(기출 전재 아님).
# 고르는 규칙: **주어진 보기 넷 중 하나만** 말이 되어야 한다.
#   보기에 없는 다른 조사가 또 맞는 건 상관없다("오늘도 비가"). 보기 안에 정답이 둘이면 안 된다.
#   그래서 오답은 기능이 확연히 다른 것(에게=사람에게, 처럼=비유, 마다=매번, 보다=비교)에서 골랐다.
PARTICLE_BANK = [
    ("아침마다 공원(   ) 걷습니다.", "에서", ["에게", "처럼", "보다"]),
    ("친구(   ) 같이 밥을 먹었습니다.", "와", ["를", "에게", "마다"]),
    ("회사(   ) 집까지 30분 걸립니다.", "에서", ["에게", "보다", "처럼"]),
    ("동생(   ) 선물을 주었습니다.", "에게", ["에서", "부터", "까지"]),
    ("오늘(   ) 비가 옵니다.", "은", ["를", "에게", "와"]),
    ("한국어(   ) 공부합니다.", "를", ["에게", "처럼", "마다"]),
    ("월요일(   ) 금요일까지 일합니다.", "부터", ["에게", "처럼", "보다"]),
    ("이 옷이 저 옷(   ) 쌉니다.", "보다", ["에게", "부터", "마다"]),
    ("커피(   ) 마실까요?", "를", ["에게", "처럼", "마다"]),
    ("주말에는 집(   ) 쉽니다.", "에서", ["에게", "보다", "처럼"]),
    ("가방 안(   ) 책이 있습니다.", "에", ["를", "처럼", "부터"]),
    ("저(   ) 베트남 사람입니다.", "는", ["를", "에게", "에서"]),
    ("학교(   ) 갑니다.", "에", ["를", "처럼", "보다"]),
    ("밥(   ) 먹었습니다.", "을", ["에", "에서", "처럼"]),
    ("병원(   ) 일합니다.", "에서", ["를", "처럼", "마다"]),
    ("형(   ) 함께 삽니다.", "과", ["를", "에", "부터"]),
    ("일요일(   ) 쉽니다.", "에", ["를", "처럼", "보다"]),
    ("시장(   ) 과일을 샀습니다.", "에서", ["에게", "처럼", "마다"]),
    ("어머니(   ) 전화를 드렸습니다.", "께", ["를", "에서", "부터"]),
    ("물(   ) 없습니다.", "이", ["을", "에게", "처럼"]),
    ("매일 두 시간(   ) 공부합니다.", "씩", ["에게", "부터", "처럼"]),
    ("이것은 제 것(   ) 아닙니다.", "이", ["을", "에게", "처럼"]),
    ("서울(   ) 기차로 갑니다.", "까지", ["에게", "처럼", "마다"]),
    ("그 사람(   ) 되고 싶습니다.", "처럼", ["를", "에서", "부터"]),
    ("사장님(   ) 오셨습니다.", "께서", ["를", "에게", "부터"]),
    ("아이(   ) 같이 갑니다.", "도", ["를", "에서", "처럼"]),
    ("방(   ) 창문이 있습니다.", "마다", ["를", "에게", "보다"]),
    ("친구(   ) 편지를 받았습니다.", "에게서", ["를", "처럼", "마다"]),
    ("저는 매운 것(   ) 못 먹습니다.", "을", ["에게", "처럼", "마다"]),
    ("여기(   ) 사진을 찍지 마세요.", "에서", ["를", "에게", "보다"]),
    ("다섯 시(   ) 만납시다.", "에", ["를", "처럼", "마다"]),
    ("지갑(   ) 잃어버렸습니다.", "을", ["에", "에게", "처럼"]),
    ("한국(   ) 온 지 3년 됐습니다.", "에", ["를", "처럼", "보다"]),
    ("날씨(   ) 좋습니다.", "가", ["를", "에게", "에서"]),
    ("은행(   ) 갔다 왔습니다.", "에", ["를", "처럼", "마다"]),
    ("연필(   ) 이름을 씁니다.", "로", ["에게", "마다", "보다"]),
] + ko_content.PARTICLE_EXTRA

def shuffled(rng, ans, wrong, why=None, bad=None):
    """정답 하나 + 오답 셋을 섞고, 해설도 같은 자리로 따라가게 한다."""
    pairs = [(ans, why or "")] + [(w, (bad or {}).get(w, "") if isinstance(bad, dict)
                                     else (bad[i] if bad and i < len(bad) else ""))
                                  for i, w in enumerate(wrong)]
    rng.shuffle(pairs)
    opts = [p[0] for p in pairs]
    out = {"options": opts, "answer": opts.index(ans)}
    if why or bad:
        out["exp"] = [p[1] for p in pairs]
    return out


# 조사·어미가 하는 일. 해설은 이 표에서 자동으로 나온다 —
# 기능이 고정된 말이라 문항마다 따로 쓸 필요가 없고, 새 문항을 넣어도 해설이 저절로 붙는다.
PARTICLE_FN = {
    "이": "주어 자리를 표시합니다(받침 있는 말 뒤)", "가": "주어 자리를 표시합니다(받침 없는 말 뒤)",
    "은": "무엇에 대해 말하는지 주제를 세웁니다(받침 있는 말 뒤)",
    "는": "무엇에 대해 말하는지 주제를 세웁니다(받침 없는 말 뒤)",
    "을": "동작을 받는 대상을 표시합니다(받침 있는 말 뒤)",
    "를": "동작을 받는 대상을 표시합니다(받침 없는 말 뒤)",
    "에": "장소로 가거나, 무엇이 있는 곳이나, 시각을 나타냅니다",
    "에서": "어떤 일이 벌어지는 장소, 또는 출발점을 나타냅니다",
    "에게": "사람이나 동물에게 무엇을 줄 때 그 상대를 나타냅니다",
    "께": "'에게'의 높임말입니다 — 웃어른에게 쓸 때", "께서": "'이/가'의 높임말입니다 — 웃어른이 주어일 때",
    "에게서": "사람에게서 받아 올 때 그 출처를 나타냅니다",
    "와": "'…와 함께/…과 …'로 둘을 잇습니다(받침 없는 말 뒤)",
    "과": "'…과 함께/…와 …'로 둘을 잇습니다(받침 있는 말 뒤)",
    "도": "'또한'의 뜻으로 덧붙입니다", "만": "'그것 하나뿐'이라는 뜻입니다",
    "부터": "시작하는 지점을 나타냅니다", "까지": "끝나는 지점을 나타냅니다",
    "보다": "두 가지를 견줍니다", "처럼": "무엇과 닮았다고 비유합니다",
    "마다": "'하나하나 빠짐없이'라는 뜻입니다", "씩": "같은 몫으로 나눠 되풀이함을 나타냅니다",
    "로": "도구·수단, 또는 방향을 나타냅니다(받침 없는 말 뒤)",
    "으로": "도구·수단, 또는 방향을 나타냅니다(받침 있는 말 뒤)",
    "의": "앞말이 뒷말의 것임을 나타냅니다", "이나": "여럿 가운데 아무거나 고를 때 씁니다",
    "밖에": "'그것 말고는 없다'는 뜻이라 뒤에 부정이 옵니다",
}


def fn_note(tok, right):
    f = PARTICLE_FN.get(tok)
    if right:
        return f"맞습니다. '{tok}'는 {f}." if f else "맞습니다."
    return f"'{tok}'는 {f}. 이 문장에는 맞지 않습니다." if f else f"'{tok}'는 이 문장에 맞지 않습니다."


def q_particle(rng, idx):
    stem, ans, wrong, *rest = PARTICLE_BANK[idx]
    why = rest[0] if rest else fn_note(ans, True)
    bad = rest[1] if len(rest) > 1 else [fn_note(w, False) for w in wrong]
    return {"type": "particle", "stem": f"( )에 알맞은 것을 고르십시오.\n{stem}",
            "word": ans, **shuffled(rng, ans, wrong, why, bad)}

# ── 듣기·읽기 (직접 쓴 재료를 문항으로 감싼다) ────────────────
def q_listen_reply(rng, idx):
    """질문을 듣고 알맞은 대답을 고른다. 문제는 소리로만 나가고 화면엔 안 적힌다."""
    heard, ans, wrong, *rest = ko_content.LISTEN_REPLY[idx]
    why = rest[0] if rest else f"들려준 말은 “{heard}”입니다. 이 물음에 맞는 대답입니다."
    bad = rest[1] if len(rest) > 1 else ["들려준 물음에 맞지 않는 대답입니다."] * 3
    return {"type": "listen_reply", "stem": "잘 듣고 알맞은 대답을 고르십시오.",
            "audio": [heard], "heard": heard,
            **shuffled(rng, ans, wrong, why, bad)}

def q_listen_dialog(rng, idx):
    """짧은 대화를 듣고 물음에 답한다. 질문은 글로 보여 준다(실제 시험도 그렇다)."""
    lines, q, ans, wrong, *rest = ko_content.LISTEN_DIALOG[idx]
    why = rest[0] if rest else "대화에서 그렇게 말했습니다."
    bad = rest[1] if len(rest) > 1 else ["대화에 나오지 않았거나 대화와 다른 내용입니다."] * 3
    return {"type": "listen_dialog", "stem": f"잘 듣고 물음에 답하십시오.\n{q}",
            # 남녀가 번갈아 말하도록 목소리를 같이 실어 보낸다
            "audio": [{"v": "m" if who == "남" else "f", "t": text} for who, text in lines],
            "script": [f"{who}: {text}" for who, text in lines],
            **shuffled(rng, ans, wrong, why, bad)}

def q_listen_pic(rng, w, pics, pic_pool):
    """낱말을 듣고 맞는 그림을 고른다 — 보기가 넷 다 그림이다."""
    key = w["ko"].split("(")[0].strip()
    img = pics.get(key)
    if not img:
        return None
    cands = [x for x in pic_pool if x["ko"] != w["ko"]]
    if len(cands) < 3:
        return None
    picked = [w] + rng.sample(cands, 3)
    rng.shuffle(picked)
    return {"type": "listen_pic", "stem": "잘 듣고 알맞은 그림을 고르십시오.",
            "audio": [w["ko"]],
            "options": [pics[x["ko"].split("(")[0].strip()] for x in picked],
            "answer": picked.index(w), "word": w["ko"], "optkind": "img",
            "exp": [(f"맞습니다. 들려준 말은 {gl(w)}입니다." if x is w
                     else f"이 그림은 {gl(x)}입니다.") for x in picked]}

# ── TOPIK II 듣기 ────────────────────────────────────────────
# 중급은 대사가 길고(중앙값 35자) 대화가 여러 턴이다. 유형도 초급과 다르다 —
# '이어질 말', '이어서 할 행동', '중심 생각'은 TOPIK II 에만 있는 꼴이다.
def _voiced(lines):
    return [{"v": "m" if who == "남" else "f", "t": t} for who, t in lines]


def q_t2_reply(rng, idx):
    lines, ans, wrong, why, bad = ko_content_t2.T2_REPLY[idx]
    return {"type": "t2_reply", "stem": "다음 대화를 잘 듣고 이어질 수 있는 말을 고르십시오.",
            "audio": _voiced(lines), "script": [f"{w}: {t}" for w, t in lines],
            **shuffled(rng, ans, wrong, why, bad)}


def q_t2_act(rng, idx):
    lines, q, ans, wrong, why, bad = ko_content_t2.T2_ACT[idx]
    return {"type": "t2_act", "stem": f"다음 대화를 잘 듣고 물음에 답하십시오.\n{q}",
            "audio": _voiced(lines), "script": [f"{w}: {t}" for w, t in lines],
            **shuffled(rng, ans, wrong, why, bad)}


def q_t2_same(rng, idx):
    lines, ans, wrong, why, bad = ko_content_t2.T2_SAME[idx]
    return {"type": "t2_same", "stem": "다음을 듣고 내용과 같은 것을 고르십시오.",
            "audio": _voiced(lines), "script": [t for _, t in lines],
            **shuffled(rng, ans, wrong, why, bad)}


def q_t2_idea(rng, idx):
    lines, ans, wrong, why, bad = ko_content_t2.T2_IDEA[idx]
    who = "남자" if lines[0][0] == "남" else "여자"
    return {"type": "t2_idea", "stem": f"다음을 듣고 {who}의 중심 생각을 고르십시오.",
            "audio": _voiced(lines), "script": [t for _, t in lines],
            **shuffled(rng, ans, wrong, why, bad)}


def q_t2_long(rng, pidx, qidx):
    title, lines, qs = ko_content_t2.T2_LONG[pidx]
    q, ans, wrong, why, bad = qs[qidx]
    return {"type": "t2_long", "stem": f"다음을 듣고 물음에 답하십시오.\n{q}",
            "ptitle": title, "audio": _voiced(lines),
            "script": [f"{w}: {t}" if len(lines) > 1 else t for w, t in lines],
            **shuffled(rng, ans, wrong, why, bad)}


def q_society(rng, idx):
    """KIIP 5단계 '한국사회이해' — 어휘가 아니라 사실을 묻는다."""
    q, ans, wrong, cat, why, bad = ko_society.SOCIETY[idx]
    return {"type": "society", "stem": q, "cat": cat,
            **shuffled(rng, ans, wrong, why, bad)}


def q_short(rng, w, gloss, pool_by_key):
    """단답형 주관식 — 보기를 주지 않고 **직접 써 넣게** 한다.

    KIIP 사전평가 필기 50문항 가운데 2문항이 이 꼴이다(나머지 48은 객관식).
    객관식만 내면 실제 시험과 다르고, 찍기가 통하는 쉬운 시험이 된다.

    채점은 띄어쓰기·문장부호를 지우고 견준다. 사람이 '근로 계약서'라고 써도
    '근로계약서'와 같게 본다 — 맞춤법 시험이 아니라 낱말을 아는지 보는 것이라서.
    """
    g = gloss.get(w["ko"]) or {}
    dfn = clean_dfn(g.get("ko_dfn"))
    if not dfn or w["ko"] in dfn:
        return None
    return {"type": "short", "short": True,
            "stem": f"다음 설명에 맞는 말을 쓰십시오.\n{dfn}",
            "answerText": w["ko"], "vi": (g.get("vi") or w.get("vi") or ""),
            "exp": f"{gl(w)} — 설명이 가리키는 말입니다."}


def q_t2_read(rng, pidx, qidx):
    """TOPIK II 읽기 — 중급 지문. 초급 지문(READ_BANK)을 쓰면 난이도가 안 맞는다."""
    title, passage, qs = ko_content_t2.T2_READ[pidx]
    q, ans, wrong, why, bad = qs[qidx]
    return {"type": "t2_read", "stem": q, "passage": passage, "ptitle": title,
            **shuffled(rng, ans, wrong, why, bad)}


def q_read(rng, pidx, qidx):
    """지문을 읽고 물음에 답한다."""
    title, passage, qs = ko_content.READ_BANK[pidx]
    q, ans, wrong, *rest = qs[qidx]
    why = rest[0] if rest else "지문에 그대로 나와 있습니다."
    bad = rest[1] if len(rest) > 1 else ["지문에 없거나 지문과 다른 내용입니다."] * 3
    return {"type": "read", "stem": q, "passage": passage, "ptitle": title,
            **shuffled(rng, ans, wrong, why, bad)}

# ── 설계도가 직접 모는 문항들 ────────────────────────────────
# 여기서부터는 **발문도 차례도 우리가 정하지 않는다.** tools/topik_blueprint.py 에
# 옮겨 둔 국립국제교육원 평가틀·발문 안내가 그대로 내려온다. 이 파일은 재료만 감싼다.
#
# 왜 이렇게 바꿨나: 예전에는 문항 수만 70개로 맞추고 유형은 우리 마음대로 늘어놓았다.
# 실제 시험지와 문항 번호별로 맞대 보니 자리가 맞는 것이 70개 중 3개뿐이었다(4%).
# '같은 문항 수'는 같은 시험이 아니다 — 몇 번에 무엇이 나오는지가 같아야 같은 시험이다.

def _dlg(lines):
    """대본줄 → 소리(남녀 목소리)와 글로 된 대본."""
    return {"audio": _voiced(lines), "script": [f"{w}: {t}" for w, t in lines]}


def _mk(rng, kind, stem, ans, wrong, why, bad, **extra):
    return {"type": kind, "stem": stem, **extra, **shuffled(rng, ans, wrong, why, bad)}


def q_bank_listen(rng, kind, stem, item):
    lines, ans, wrong, why, bad = item
    return _mk(rng, kind, stem, ans, wrong, why, bad, **_dlg(lines))


def q_bank_read(rng, kind, stem, item):
    text, ans, wrong, why, bad = item
    return _mk(rng, kind, stem, ans, wrong, why, bad, passage=text)


def q_titled(rng, kind, stem, item):
    """제목이 붙은 지문 하나에 물음 하나 — 실용문·기사·도표·글."""
    title, text, ans, wrong, why, bad = item
    return _mk(rng, kind, stem, ans, wrong, why, bad, passage=text, ptitle=title)


def q_pos(rng, kind, stem, item):
    """주어진 문장이 들어갈 곳 — 넣을 문장은 물음 아래 〈보기〉로 붙인다."""
    title, text, ins, ans, wrong, why, bad = item
    return _mk(rng, kind, f"{stem}\n〈보기〉 {ins}", ans, wrong, why, bad,
               passage=text, ptitle=title)


def q_pic_dlg(rng, stem, item, pics, pic_pool):
    """대화를 듣고 알맞은 그림 — 보기 넷이 다 그림이다."""
    lines, ko = item
    if ko not in pics:
        return None
    cands = [x for x in pic_pool if x["ko"].split("(")[0].strip() != ko]
    if len(cands) < 3:
        return None
    names = [ko] + [x["ko"].split("(")[0].strip() for x in rng.sample(cands, 3)]
    rng.shuffle(names)
    return {"type": "listen_pic", "stem": stem, "optkind": "img",
            "options": [pics[n] for n in names], "answer": names.index(ko),
            "word": ko, **_dlg(lines),
            "exp": [(f"맞습니다. 대화에서 말한 것은 '{n}'입니다." if n == ko
                     else f"이 그림은 '{n}'입니다.") for n in names]}


def q_chart(rng, stem, idx):
    """도표 고르기 — 들려준 수치대로 그린 그래프 하나와 차례만 바꾼 것 셋."""
    title, lines, items, right, wrongs, why = L2.T2_CHART[idx]
    files = gen_charts.names(idx)
    order = list(range(4))
    rng.shuffle(order)
    return {"type": "t2_pic", "stem": stem, "optkind": "img", "ptitle": title,
            "options": [files[p] for p in order], "answer": order.index(0),
            **_dlg(lines),
            "exp": [(why if p == 0 else "값의 차례가 들려준 것과 다릅니다.") for p in order]}


TAG4 = ["(가)", "(나)", "(다)", "(라)"]


def q_order(rng, kind, stem, item):
    """순서 배열 — 문장 넷에 (가)~(라)를 섞어 붙이고 바른 차례를 답으로 만든다.

    보기는 모두 (가) 아니면 (나)로 시작한다. 실제 시험이 그렇고, 그래야
    '앞에 오는 말'을 골라내는 힘을 재게 된다(아무 차례나 늘어놓으면 찍기가 쉬워진다).
    """
    sents, why = item
    while True:
        perm = list(range(4))
        rng.shuffle(perm)                    # perm[j] = j번째 줄에 놓을 문장 번호
        # 첫 문장은 (가)나 (나)를 받고, 인쇄된 차례가 곧 정답이 되면 안 된다
        # (그대로 인쇄되면 읽지 않고 ①번을 찍어 맞힌다)
        if perm.index(0) < 2 and perm != [0, 1, 2, 3]:
            break
    body = "\n".join(f"{TAG4[j]} {sents[perm[j]]}" for j in range(4))
    at = {perm[j]: j for j in range(4)}      # 문장 번호 → 붙은 이름표 자리
    right = "-".join(TAG4[at[k]] for k in range(4))
    seen, wrong = {right}, []
    for _ in range(200):
        if len(wrong) == 3:
            break
        cand = list(range(4))
        rng.shuffle(cand)
        if cand[0] > 1:
            continue
        s = "-".join(TAG4[i] for i in cand)
        if s not in seen:
            seen.add(s)
            wrong.append(s)
    return _mk(rng, kind, stem, right, wrong, why,
               ["앞뒤가 이어지지 않는 차례입니다."] * 3, passage=body)


def q_pair(rng, kind, subs, title, body, qs, listen=False, n=None):
    """묶음 문항 — 지문(대본) 하나에 소문항 여럿. **발문은 설계도의 sub 에서 온다.**"""
    out = []
    for i, (ans, wrong, why, bad) in enumerate(qs[:n or len(qs)]):
        q = _mk(rng, kind, (subs[i] if subs and i < len(subs) else ""),
                ans, wrong, why, bad, ptitle=title)
        q.update(_dlg(body) if listen else {"passage": body})
        out.append(q)
    return out


def restem(q, head):
    """물음 첫 줄을 공식 발문으로 갈아 끼운다(둘째 줄 — 문장·물음 — 은 그대로 둔다)."""
    rest = q["stem"].split("\n")[1:]
    q["stem"] = "\n".join([head] + rest)
    return q


# 유형 이름 → 재료 뭉치. 설계도의 ours 값이 이 열쇠다.
BANKS = {
    "listen_next": L1.LISTEN_NEXT, "listen_place": L1.LISTEN_PLACE,
    "listen_topic": L1.LISTEN_TOPIC, "listen_idea": L1.LISTEN_IDEA,
    "listen_same": L1.LISTEN_SAME,
    "read_topic": R1.READ_TOPIC, "read_idea": R1.READ_IDEA, "read_same": R1.READ_SAME,
}
LISTENY = {"listen_next", "listen_place", "listen_topic", "listen_idea",
           "listen_same", "t2_idea_dlg"}
# 묶음 유형 → (재료 뭉치, 듣기인가)
PAIRS = {
    "pair_why": (L1.PAIR_WHY, True), "pair_what": (L1.PAIR_WHAT, True),
    "pair_reason": (L1.PAIR_REASON, True),
    "read_pair": (R1.READ_PAIR, False), "read_pair_long": (R1.READ_PAIR_LONG, False), "pair_topic": (R1.PAIR_TOPIC, False),
    "pair_purpose": (R1.PAIR_PURPOSE, False),
}
# 낱개로 세어 쓰는 나머지 뭉치들
PAIRS.update({
    "t2p_dlg_idea": (L2.DLG_IDEA, True), "t2p_dlg_act": (L2.DLG_ACT, True),
    "t2p_itv_idea": (L2.ITV_IDEA, True), "t2p_dlg_intent": (L2.DLG_INTENT, True),
    "t2p_itv_who": (L2.ITV_WHO, True), "t2p_debate": (L2.DEBATE, True),
    "t2p_lec_topic": (L2.LEC_TOPIC, True), "t2p_speech": (L2.SPEECH, True),
    "t2p_show_idea": (L2.SHOW_IDEA, True), "t2p_talk_before": (L2.TALK_BEFORE, True),
    "t2p_lec_main": (L2.LEC_MAIN, True), "t2p_doc": (L2.DOC, True),
    "t2p_lec_att": (L2.LEC_ATT, True), "t2p_talk_att": (L2.TALK_ATT, True),
    "t2p_lec_att2": (L2.LEC_ATT2, True),
})
PAIRS.update({
    "t2rp_blank_theme": (R2.BLANK_THEME, False), "t2rp_blank_same": (R2.BLANK_SAME, False),
    "t2rp_feel_i": (R2.FEEL_I, False), "t2rp_feel_he": (R2.FEEL_HE, False),
    "t2rp_att": (R2.ATT, False), "t2rp_purpose3": (R2.PURPOSE3, False),
})
BANKS.update({"t2_idea_dlg": L2.T2_IDEA_DLG, "t2r_gram": R2.GRAM, "t2r_similar": R2.SIMILAR,
              "t2r_ad": R2.AD, "t2r_blank": R2.BLANK, "t2r_head": R2.HEAD})
# 제목이 붙은 지문(실용문·기사·도표·글) — 뭉치 모양이 (제목, 지문, …)로 하나 더 길다
TITLED = {"read_notice": R1.READ_NOTICE, "t2r_fact": R2.FACT,
          "t2r_same": R2.SAME, "t2r_theme": R2.THEME}
SOLO = {"read_notice": R1.READ_NOTICE, "read_order": R1.READ_ORDER,
        "t2r_fact": R2.FACT, "t2r_same": R2.SAME, "t2r_theme": R2.THEME,
        "t2r_order": R2.ORDER, "t2r_pos": R2.POS,
        "listen_pic_dlg": L1.LISTEN_PIC_DLG, "pair_pos": R1.PAIR_POS,
        "t2_picdlg": L2.T2_PICDLG, "t2_chart": L2.T2_CHART}

# 설계도의 [1~3]은 '그림 **또는** 그래프'다 — 실제 시험은 1·2번이 그림, 3번이 그래프다.
# 뭉치가 둘이라 한 자리로는 못 세고, 출제기에서 앞 둘·뒤 하나로 갈라 쓴다.
# 아래는 '한 회분에 몇 개가 드는가'를 세는 데만 쓴다.
T2PIC_SPLIT = 2

# 설계도의 [17~20]은 **남자의** 중심 생각만 묻고, [9~12]는 **여자가** 이어서 할 행동만 묻는다.
# 우리 뭉치에는 남녀가 섞여 있다 — 발문과 화자가 어긋나면 답이 없는 문항이 된다.
T2_IDEA_M = [i for i, it in enumerate(ko_content_t2.T2_IDEA) if it[0][0][0] == "남"]
T2_ACT_F = [i for i, it in enumerate(ko_content_t2.T2_ACT) if "여자" in it[1]]
# 발문이 물음까지 통째로 담고 있는 유형 — 뭉치에 딸린 물음을 지우고 공식 발문만 쓴다
STEM_ONLY = {"t2_act"}
# 설계도의 'listen_pic'은 TOPIK I 에서 **대화를 듣고** 그림을 고르는 꼴이다.
# EPS·KIIP 에 쓰던 '낱말 하나를 듣고 그림 고르기'와 재료가 다르므로 따로 잇는다.
ALIAS = {"listen_pic": "listen_pic_dlg"}


def bp_sections(areas):
    """공식 설계도 → 우리 구간표. 문항 번호·발문·묶음 여부가 그대로 내려온다."""
    out = []
    for name in areas:
        for b in BP.FORMS[name]["items"]:
            a, z = b["block"]          # 설계도의 번호가 이미 절대번호다(읽기는 31~70)
            n = z - a + 1
            # 배점 — TOPIK I 은 문항마다 다르고(4·3점 / 2·3점), TOPIK II 는 전 문항 2점이다.
            pts = b.get("pts") or ([2] * n if name.startswith("TOPIK II") else [1] * n)
            out.append({"label": f"[{a}~{z}] {b['stem']}",
                        "kind": b["ours"], "n": n, "pts": pts,
                        "stem": b["stem"], "sub": b.get("sub"), "bp": True})
    return out


def bp_sets(areas):
    """재료가 몇 회분인가 — 가장 모자란 유형이 회차 수를 정한다.

    없는 것을 있는 척하지 않기 위해서다. 한 유형이라도 동나면 그 회차는 구멍이 난다.
    """
    need = {}
    for sec in bp_sections(areas):
        k = ALIAS.get(sec["kind"], sec["kind"])
        if k == "t2_pic":                          # 그림 둘 + 그래프 하나로 갈린다
            need["t2_picdlg"] = need.get("t2_picdlg", 0) + T2PIC_SPLIT
            need["t2_chart"] = need.get("t2_chart", 0) + sec["n"] - T2PIC_SPLIT
        elif k in PAIRS or k == "pair_pos":
            need[k] = need.get(k, 0) + 1          # 묶음은 지문 하나로 여러 문항
        elif k in BANKS or k in SOLO:
            need[k] = need.get(k, 0) + sec["n"]
        elif k == "t2_idea":
            need["t2_idea_m"] = need.get("t2_idea_m", 0) + sec["n"]
        elif k == "t2_act":
            need["t2_act_f"] = need.get("t2_act_f", 0) + sec["n"]
    have = {**{k: len(v) for k, v in BANKS.items()},
            **{k: len(v) for k, v in SOLO.items()},
            **{k: len(v) for k, (v, _) in PAIRS.items()},
            "t2_idea_m": len(T2_IDEA_M), "t2_act_f": len(T2_ACT_F)}
    return min([have[k] // n for k, n in need.items() if n] or [1])


# ── 시험 설계도 ──────────────────────────────────────────────
# 문항 수·시간·유형 배열은 실제 시험을 그대로 따랐다(형식은 사실이라 따라도 된다).
# 업종 이름 — 베트남 사람이 고르는 자리라 베트남어가 있어야 한다
IND_VI = {"고무·플라스틱": "Cao su · Nhựa", "기계·금형": "Cơ khí · Khuôn mẫu",
          "섬유·의복": "Dệt may", "식품": "Thực phẩm", "전자·전기": "Điện tử · Điện",
          "펄프·제지·목재": "Bột giấy · Giấy · Gỗ", "화학": "Hóa chất",
          "금속": "Kim loại"}

BLUEPRINTS = {
    # EPS-TOPIK은 읽기 20 + 듣기 20 = 40문항이다. 그 비율을 그대로 지켰다.
    "eps-topik": {
        "name": "EPS-TOPIK 모의고사",
        "name_vi": 'Đề thi thử EPS-TOPIK',
        "desc_vi": 'Kỳ thi năng lực tiếng Hàn EPS · Đọc 20 + Nghe 20',
        "desc": "고용허가제 한국어능력시험 · 읽기 20 + 듣기 20",
        "minutes": 50,
        # 두 번 — **공식 프로그램에서 확정했다**(2026-08-29).
        # epstopik.hrdkorea.or.kr → 「체험하기 · 평가프로그램 체험」 은 설명 글이 아니라
        # 실제 CBT 프로그램이다. 그 안내문에 "Listening test will be played two times."
        # 가 있고, 연습 음원 q6~q10 을 받아 적으니 소리 자체가 이랬다:
        #     "6번 문제입니다." → [지문] → "다시 들으십시오." → [지문]
        # <audio time="13000"> 값이 음원 길이(12.75초)와 같다 → 프로그램은 한 번 튼다.
        # **반복은 음원 안에 있다.** TOPIK 은 맨 앞에서 "두 번씩 읽겠습니다"라고
        # 한 번 알리고 지나가는데, EPS 는 문항마다 그 자리에서 넣는다 — 소리를 구울 때
        # 이 차이를 지켜야 한다(다시 듣기 단추가 아니라 소리 안에).
        "plays": 2,
        # 답을 한 번 고르면 **못 바꾼다.** 같은 체험 프로그램에서 ①을 고른 뒤 ②를
        # 눌러 봤는데 바뀌지 않았고, 안내문에도 그대로 적혀 있다:
        #     "Once you choose an answer, you can`t change the answer."
        # TOPIK IBT 는 정반대다("문제 번호를 클릭하면 … 선택 번호를 수정할 수 있습니다").
        # 그래서 **EPS 에만** 건다.
        "lock": True,
        # **베트남은 CBT 다** — 공단 시험일정 표기(2026). UBT(태블릿)를 쓰는 나라와
        # 조작 규칙이 정반대에 가까우므로 우리는 CBT 규칙으로 흉내 낸다.
        # 공식 체험 프로그램의 타이머 코드(timer_script)를 직접 읽어 확인한 것:
        #   · 읽기·듣기 타이머가 **따로** 돈다(t_left_time / t_right_time)
        #   · 읽기 시간이 0이 되면 examTestNext() 로 **듣기 첫 문항에 강제 이동**
        #   · 듣기 구간에서는 앞뒤 이동 단추가 **사라진다**(되돌아갈 수 없다)
        #   · 번호판 칸에는 onclick 이 없다 — **상태 표시 전용**
        # 그래서 읽기에 남긴 시간은 듣기로 넘어가지 않고, 안 푼 읽기 문항은 사라진다.
        "cbt": {"read": 25, "listen": 25},
        "grades": ["A", "B"],
        "sections": [
            {"label": "[1~4] 그림을 보고 맞는 것을 고르십시오.", "kind": "pic2word", "n": 4},
            {"label": "[5~8] 다음 설명에 맞는 단어를 고르십시오.", "kind": "dfn2word", "n": 4},
            {"label": "[9~14] ( )에 알맞은 것을 고르십시오.", "kind": "particle", "n": 6},
            {"label": "[15~20] 다음 글을 읽고 물음에 답하십시오.", "kind": "read", "n": 6},
            {"label": "[21~26] 잘 듣고 알맞은 그림을 고르십시오.", "kind": "listen_pic", "n": 6},
            {"label": "[27~34] 잘 듣고 알맞은 대답을 고르십시오.", "kind": "listen_reply", "n": 8},
            {"label": "[35~40] 대화를 듣고 물음에 답하십시오.", "kind": "listen_dialog", "n": 6},
        ],
    },
    # KIIP 사전평가 — 공식 규격(kiiptest.org 사전평가 안내)을 그대로 맞췄다.
    #   필기 50문항 / 60분 = 객관식 48(한국어 38 + 문화 10) + 단답형 주관식 2
    #   배점 필기 75점(문항당 1.5점) + 구술 5문항 25점(문항당 5점) = 100점
    # 전에는 40문항 50분에 균등 배점이었다 — 문항 수도 시간도 배점도 다 틀렸고,
    # 단답형이 아예 없어서 "찍으면 되는 시험"이 되어 있었다.
    # 필기에 듣기가 없는 것은 맞다(듣기 대신 구술이 따로 있다).
    "kiip-pre": {
        "name": "KIIP 사전평가 모의고사",
        "name_vi": 'Đề thi thử KIIP — Sơ khảo',
        "desc_vi": 'Bài viết sơ khảo KIIP · 50 câu 60 phút (48 trắc nghiệm + 2 câu tự luận ngắn)',
        "desc": "사회통합프로그램 기본소양 사전평가 필기 · 50문항 60분 (객관식 48 + 단답형 2)",
        "minutes": 60,
        "grades": ["A", "B", "C"],
        "pt": 1.5,                      # 필기는 문항마다 1.5점 — 50문항이면 75점
        "oral": (5, 25),                # 구술 5문항 25점은 우리가 채점할 수 없다
        # 총점(필기 75 + 구술 25)으로 배정 단계가 정해진다. 소수점 버림.
        "place_at": [[3, "1단계"], [21, "2단계"], [41, "3단계"],
                     [61, "4단계"], [81, "5단계"]],
        "sections": [
            {"label": "[1~4] 그림을 보고 알맞은 것을 고르십시오.", "kind": "pic2word", "n": 4},
            {"label": "[5~14] ( )에 알맞은 것을 고르십시오.", "kind": "particle", "n": 10},
            {"label": "[15~26] 다음 설명에 맞는 단어는?", "kind": "dfn2word", "n": 12},
            {"label": "[27~32] 뜻이 맞는 것을 고르십시오.", "kind": "word2vi", "n": 6},
            {"label": "[33~38] 다음 글을 읽고 물음에 답하십시오.", "kind": "read", "n": 6},
            {"label": "[39~48] 한국 사회와 문화에 대한 물음입니다.", "kind": "society", "n": 10},
            {"label": "[49~50] 다음 설명에 맞는 말을 쓰십시오. (단답형)", "kind": "short", "n": 2},
        ],
    },
    # KIIP 중간평가 — 1~4단계를 마치고 다음 단계로 오를 때 본다.
    #   객관식 28문(2.5점 = 70점) + 작문형 2문(2.5점 = 5점) + 구술 5문(5점 = 25점)
    #   필기 50분(객관식 40분 + 작문 10분) + 구술 10분 · 합격 60점
    "kiip-mid": {
        "name": "KIIP 중간평가 모의고사",
        "name_vi": 'Đề thi thử KIIP — Giữa kỳ',
        "desc_vi": 'Trắc nghiệm giữa kỳ KIIP · 28 câu 40 phút (viết 2 · vấn đáp 5 tính riêng)',
        "desc": "사회통합프로그램 중간평가 객관식 · 28문항 40분 (작문 2·구술 5는 따로)",
        "minutes": 40,
        "grades": ["A", "B"],
        "pt": 2.5,
        "essay": (2, 5), "oral": (5, 25),
        "pass_at": 60,
        "sections": [
            {"label": "[1~8] 다음 설명에 맞는 단어는?", "kind": "dfn2word", "n": 8},
            {"label": "[9~16] ( )에 알맞은 것을 고르십시오.", "kind": "particle", "n": 8},
            {"label": "[17~20] 뜻이 맞는 것을 고르십시오.", "kind": "word2vi", "n": 4},
            {"label": "[21~24] 다음 글을 읽고 물음에 답하십시오.", "kind": "read", "n": 4},
            {"label": "[25~28] 한국 사회와 문화에 대한 물음입니다.", "kind": "society", "n": 4},
        ],
    },
}

# ── KIIP 종합평가 — 영주용(KIPRAT)·귀화용(KINAT) ───────────────────
# 둘 다 객관식 36문 65점 + 작문 4문 10점 + 구술 5문 25점 = 100점, 합격 60점.
# 다른 것은 **객관식 배점 배열뿐**이다(공식 안내 그대로):
#   영주용 14문×1.5 + 22문×2 = 65     귀화용 7문×1 + 29문×2 = 65
# 어떤 문항이 몇 점인지는 공개돼 있지 않다. 그래서 주제로 나누지 않고
# 공개된 배열 그대로 앞에서부터 붙인다 — 없는 규칙을 지어내지 않는다.
KIIP_COMP = [
    ("perm", "영주용", "KIPRAT", [1.5] * 14 + [2.0] * 22),
    ("nat", "귀화용", "KINAT", [1.0] * 7 + [2.0] * 29),
]
for _sfx, _nm, _abbr, _pts in KIIP_COMP:
    BLUEPRINTS[f"kiip-{_sfx}"] = {
        "name": f"KIIP {_nm} 종합평가 모의고사",
        "name_vi": f"Đề thi thử KIIP — Tổng hợp ({'thường trú' if _sfx == 'perm' else 'nhập tịch'})",
        "desc_vi": "Trắc nghiệm tổng hợp KIIP · 36 câu 60 phút (viết 4 · vấn đáp 5 tính riêng)",
        "desc": f"사회통합프로그램 {_nm} 종합평가({_abbr}) 객관식 · 36문항 60분 "
                f"(작문 4·구술 5는 따로)",
        "minutes": 60,
        "grades": ["B", "C"],
        "essay": (4, 10), "oral": (5, 25),
        "pass_at": 60,
        "sections": [
            {"label": "[1~24] 한국 사회와 문화에 대한 물음입니다.",
             "kind": "society", "n": 24, "pts": _pts[:24]},
            {"label": "[25~30] 다음 설명에 맞는 단어는?",
             "kind": "dfn2word", "n": 6, "pts": _pts[24:30]},
            {"label": "[31~36] 다음 글을 읽고 물음에 답하십시오.",
             "kind": "read", "n": 6, "pts": _pts[30:36]},
        ],
    }

BLUEPRINTS.update({
    # TOPIK I — 구간표를 손으로 쓰지 않는다. 공식 평가틀·발문 안내가 그대로 내려온다.
    # (듣기 30 + 읽기 40 = 70문항, 묶음 26개)
    "topik-1": {
        "name": "TOPIK I 모의고사",
        "name_vi": 'Đề thi thử TOPIK I',
        "desc_vi": 'TOPIK I · Nghe 30 + Đọc 40 — theo đúng thứ tự câu hỏi và câu lệnh của khung đề chính thức',
        "desc": "TOPIK I · 듣기 30 + 읽기 40 — 공식 평가틀의 문항 차례와 발문을 그대로 따랐다",
        "minutes": 100,
        "grades": ["A", "B"],
        # 두 번. **공식 안내 방송을 그대로 옮겨 확인했다**(102회 음원 1-01.mp3):
        #   "아래 1번부터 30번까지는 듣기 문제입니다. 문제를 잘 듣고 질문에 맞는
        #    답을 고르십시오. **두 번씩 읽겠습니다.**"
        # 실제로 이어지는 1번 '우산이 있어요?' 도 두 번 읽는다.
        "plays": 2,
        "sections": bp_sections(["TOPIK I 듣기", "TOPIK I 읽기"]),
    },
    # TOPIK II 읽기 — 구간표를 손으로 쓰지 않는다. [9~12]와 [32~34]는 발문이 비슷해 보여도
    # 글의 갈래가 다르다(앞은 실용문·기사·도표, 뒤는 글) — 설계도가 그것까지 정해 준다.
    # 쓰기는 정답이 하나가 아니라 extra.write 쪽에서 AI가 채점한다.
    "topik-2-read": {
        "name": "TOPIK II 읽기 모의고사",
        "name_vi": 'Đề thi thử TOPIK II — Đọc',
        "desc_vi": 'TOPIK II ca 2 Đọc · 50 câu — theo đúng khung đề chính thức',
        "desc": "TOPIK II 2교시 읽기 · 50문항 — 공식 평가틀의 문항 차례와 발문을 그대로 따랐다",
        "minutes": 70,
        "grades": ["B", "C"],
        "sections": bp_sections(["TOPIK II 읽기"]),
    },
    # TOPIK II 듣기 — 구간표를 손으로 쓰지 않는다. 21번부터 끝까지가 전부 묶음 문항이고
    # 담화의 갈래(대화·인터뷰·토론·강연·대담·다큐·인사말·교양)까지 번호마다 정해져 있다.
    "topik-2-listen": {
        "name": "TOPIK II 듣기 모의고사",
        "name_vi": 'Đề thi thử TOPIK II — Nghe',
        "desc_vi": 'TOPIK II ca 1 Nghe · 50 câu — theo đúng khung đề chính thức',
        "desc": "TOPIK II 1교시 듣기 · 50문항 — 공식 평가틀의 문항 차례와 발문을 그대로 따랐다",
        "minutes": 60,
        "grades": ["B", "C"],
        # 한 번. **공식 안내 방송 그대로**(102회 음원 2-01.mp3):
        #   "아래 1번부터 50번까지는 듣기 문제입니다. … **한 번 읽겠습니다.**"
        "plays": 1,
        "sections": bp_sections(["TOPIK II 듣기"]),
    },
})

# ── KIIP 단계평가 — 0단계부터 4단계까지 (사용자 지시: 전 단계 확장) ────────
# 사회통합프로그램은 0단계(기초)~4단계(한국어와 한국문화) + 5단계(한국사회이해)다.
# 단계가 오를수록 (a)어려운 등급 어휘를 쓰고 (b)읽기 비중이 커진다.
# 5단계는 어휘 시험이 아니라 '한국사회이해'라 우리 문화 자료(ko_culture)로 따로 낸다.
KIIP_STAGES = [
    (0, "기초", ["A"], [("pic2word", 8), ("dfn2word", 8), ("particle", 4)]),
    (1, "초급 1", ["A"], [("pic2word", 4), ("dfn2word", 10), ("particle", 6), ("read", 4)]),
    (2, "초급 2", ["A", "B"], [("pic2word", 2), ("dfn2word", 10), ("particle", 8), ("read", 6)]),
    (3, "중급 1", ["B"], [("dfn2word", 12), ("particle", 8), ("word2vi", 4), ("read", 8)]),
    (4, "중급 2", ["B", "C"], [("dfn2word", 12), ("particle", 8), ("vi2word", 4), ("read", 8)]),
]
LABEL = {"society": "다음 물음에 알맞은 답을 고르십시오.",
         "pic2word": "그림을 보고 알맞은 것을 고르십시오.",
         "dfn2word": "다음 설명에 맞는 단어를 고르십시오.",
         "particle": "( )에 알맞은 것을 고르십시오.",
         "word2vi": "뜻이 알맞은 것을 고르십시오.",
         "vi2word": "한국어로 알맞은 것을 고르십시오.",
         "read": "다음을 읽고 물음에 답하십시오.",
         "short": "다음 설명에 맞는 말을 쓰십시오.",
         "listen_pic": "잘 듣고 알맞은 그림을 고르십시오.",
         "listen_reply": "잘 듣고 알맞은 대답을 고르십시오.",
         "listen_dialog": "잘 듣고 물음에 답하십시오.",
         "job": "일터에서 쓰는 말입니다. 뜻이 알맞은 것을 고르십시오."}


def numbered(mix):
    """[(유형, 개수)] → 문항 번호가 매겨진 구간표. [1~4] 처럼 실제 시험처럼 보이게."""
    out, at = [], 1
    for kind, n in mix:
        out.append({"label": f"[{at}~{at + n - 1}] {LABEL[kind]}", "kind": kind, "n": n})
        at += n
    return out


# 5단계는 앞의 단계와 성격이 다르다 — 한국어 실력이 아니라 '한국 사회를 아는가'를 본다.
# 그래서 어휘 문항을 섞지 않고 사회·제도·역사·문화만 낸다.
BLUEPRINTS["kiip-5"] = {
    "name": "KIIP 5단계 한국사회이해 모의고사",
        "name_vi": 'Đề thi thử KIIP bậc 5 — Hiểu biết xã hội Hàn Quốc',
        "desc_vi": 'KIIP bậc 5 · xã hội · thể chế · lịch sử · văn hóa, 40 câu',
    "desc": "사회통합프로그램 5단계 · 사회·제도·역사·문화 40문항",
    "minutes": 40, "grades": ["A", "B", "C"],
    "sections": [{"label": "[1~40] 다음 물음에 알맞은 답을 고르십시오.",
                  "kind": "society", "n": 40}],
}

for st, nm, grades, mix in KIIP_STAGES:
    BLUEPRINTS[f"kiip-{st}"] = {
        "name": f"KIIP {st}단계 평가 모의고사",
        "name_vi": f"Đề thi thử KIIP — bậc {st}",
        "desc_vi": f"Dạng bài đánh giá bậc {st} của KIIP",
        "desc": f"사회통합프로그램 {st}단계({nm}) 단계평가 형식 · {sum(n for _, n in mix)}문항",
        "minutes": 30 + st * 5, "grades": grades, "sections": numbered(mix),
    }

# ── EPS 직무 어휘 — 8개 업종 (사용자 지시: EPS 확장) ──────────────────
# 공개 직무문항(산업인력공단)에 실제로 나오는 말 가운데, 그 업종에만 몰려 나오고
# 우리 사전에 뜻이 있는 것만 골라 뽑았다(tools 밖 분석 → data/_job_vocab.json).
# 뜻을 모르는 말은 지어내지 않고 그냥 뺐다 — 그래서 업종마다 문항 수가 다르다.
JOB_MIN = 12
try:
    JOB_VOCAB = json.load(open(os.path.join(DATA, "_job_vocab.json"), encoding="utf-8"))
except Exception:
    JOB_VOCAB = {}
for _ind, _ws in JOB_VOCAB.items():
    if len(_ws) < JOB_MIN:
        continue
    _n = min(20, len(_ws))
    BLUEPRINTS[f"eps-job-{_ind}"] = {
        "name": f"EPS 직무 어휘 · {_ind}",
        "name_vi": f"Từ vựng nghề EPS · {IND_VI.get(_ind, _ind)}",
        "desc_vi": f"{IND_VI.get(_ind, _ind)} — từ thực dùng tại nơi làm việc",
        "desc": f"{_ind} 업종에서 실제로 쓰이는 말 {_n}개",
        "minutes": 20, "grades": ["A", "B", "C"], "industry": _ind,
        # 뜻 길이가 안 맞는 낱말은 건너뛰므로 실제 문항 수가 한둘 적을 수 있다.
        # 그래서 구간 이름에 [1~20] 같은 번호를 안 붙인다 — 안 맞으면 더 이상하다.
        "sections": [{"label": LABEL["job"], "kind": "job", "n": _n}],
    }


def q_job(rng, industry, idx, used):
    """업종 낱말의 뜻 고르기. 오답도 같은 업종에서 뽑아 '분야로 찍기'를 막는다."""
    pool = JOB_VOCAB.get(industry) or []
    if len(pool) < 4 or idx >= len(pool):
        return None
    w = pool[idx]
    if w["ko"] in used:
        return None
    cands = [x for x in pool if x["ko"] != w["ko"] and x["vi"] != w["vi"]]
    if len(cands) < 3:
        return None
    # 뜻 길이가 고만고만한 것끼리 — 길이로 찍히지 않게
    al = len(one_sense(w["vi"]))
    d = None
    for _ in range(40):
        p = rng.sample(cands, 3)
        L = [al] + [len(one_sense(x["vi"])) for x in p]
        if max(L) - min(L) < 12 or (al != max(L) and al != min(L)):
            d = p; break
    if d is None:
        # 뜻 길이가 비슷한 짝을 못 찾으면 이 낱말은 안 낸다.
        # 억지로 내면 '제일 긴 것'을 찍어 맞히는 문항이 된다 — 문항 수보다 질이 먼저다.
        return None
    used.add(w["ko"])
    return mk_choice_q(rng, w, d, f"'{w['ko']}'의 뜻으로 알맞은 것은?",
                       lambda o: one_sense(o["vi"]), "job",
                       extra={"industry": industry},
                       note=lambda o, a: (f"맞습니다. {industry} 일터에서 {gl(w)}."
                                          if a else f"이 뜻은 '{o['ko']}'입니다."))

def build(exam_id, seed, words, gloss, pics, state):
    bp = BLUEPRINTS[exam_id]
    rng = random.Random(f"{exam_id}-{seed}")

    usable = [w for w in words if w["grade"] in bp["grades"]]
    # 그림 문항 전용 후보 — 정답도 오답도 여기서만 뽑는다
    pic_pool = [w for w in words
                if w["ko"].split("(")[0].strip() in PIC_OK
                and pics.get(w["ko"].split("(")[0].strip())]
    pool_by_key = {}
    for w in usable:
        pool_by_key.setdefault((w["grade"], w["pos"]), []).append(w)

    # 회차를 넘어 이어지는 기억. 1·2·3회차를 연달아 푸는 사람에게 같은 문제가 또 나오면 안 된다.
    used = state.setdefault("used_words", set())

    # 손으로 쓴 재료(조사 문틀·듣기 대본·읽기 지문)는 개수가 정해져 있다.
    # 회차마다 앞에서부터 꺼내 쓰고, 동나면 조용히 줄이지 말고 아래에서 부족분을 보고한다.
    def take(name, size):
        left = state.get(name)
        if left is None:
            left = list(range(size))
            random.Random(f"{exam_id}-{name}").shuffle(left)
            state[name] = left
        return left
    p_left = take("particles", len(PARTICLE_BANK))
    t2 = {k: take("t2_" + k, len(getattr(ko_content_t2, "T2_" + k.upper())))
          for k in ("reply", "act", "same", "idea")}
    soc_left = take("society", len(ko_society.SOCIETY))
    t2_read = state.get("t2_read")
    if t2_read is None:
        t2_read = [(pi, qi) for pi, p in enumerate(ko_content_t2.T2_READ)
                   for qi in range(len(p[2]))]
        random.Random(f"{exam_id}-t2read").shuffle(t2_read)
        state["t2_read"] = t2_read
    t2_long = state.get("t2_long")
    if t2_long is None:
        t2_long = [(pi, qi) for pi, p in enumerate(ko_content_t2.T2_LONG)
                   for qi in range(len(p[2]))]
        state["t2_long"] = t2_long
    lr_left = take("listen_reply", len(ko_content.LISTEN_REPLY))
    ld_left = take("listen_dialog", len(ko_content.LISTEN_DIALOG))
    # 설계도가 모는 유형들 — 재료 뭉치마다 회차를 넘어 이어지는 대기줄을 둔다
    bp_left = {k: take("bp_" + k, len(v))
               for k, v in list(BANKS.items()) + list(SOLO.items())}
    bp_left.update({k: take("bp_" + k, len(v)) for k, (v, _) in PAIRS.items()})
    bp_left["t2_idea_m"] = take("bp_t2_idea_m", len(T2_IDEA_M))
    bp_left["t2_act_f"] = take("bp_t2_act_f", len(T2_ACT_F))
    # 읽기는 (지문번호, 그 지문의 몇째 문항)이 한 짝이다
    rd_left = state.get("read")
    if rd_left is None:
        rd_left = [(pi, qi) for pi, p in enumerate(ko_content.READ_BANK) for qi in range(len(p[2]))]
        random.Random(f"{exam_id}-read").shuffle(rd_left)
        state["read"] = rd_left

    qs, skipped, job_at = [], 0, 0

    for sec in bp["sections"]:
        made = 0
        tries = 0
        while made < sec["n"] and tries < 4000:
            tries += 1
            # 설계도가 모는 구간이면 유형 이름과 공식 발문이 여기서 내려온다
            bpsec = sec.get("bp")
            kind = ALIAS.get(sec["kind"], sec["kind"]) if bpsec else sec["kind"]
            head = sec.get("stem")
            if bpsec and (kind in PAIRS or kind == "pair_pos"):
                pool = bp_left[kind]
                if not pool:
                    break
                idx = pool.pop(0)
                if kind == "pair_pos":
                    title, body, ins, subqs = R1.PAIR_POS[idx]
                    q = q_pair(rng, kind, sec["sub"], title, body, subqs, n=sec["n"])
                    q[0]["stem"] += "\n〈보기〉 " + ins    # 넣을 문장은 첫 물음에 붙인다
                else:
                    bank, listen = PAIRS[kind]
                    title, body, subqs = bank[idx]
                    q = q_pair(rng, kind, sec["sub"], title, body, subqs, listen, n=sec["n"])
            elif bpsec and kind in BANKS:
                pool = bp_left[kind]
                if not pool:
                    break
                item = BANKS[kind][pool.pop(0)]
                q = (q_bank_listen if kind in LISTENY else q_bank_read)(rng, kind, head, item)
            elif bpsec and kind in TITLED:
                if not bp_left[kind]:
                    break
                q = q_titled(rng, kind, head, TITLED[kind][bp_left[kind].pop(0)])
            elif bpsec and kind in ("read_order", "t2r_order"):
                if not bp_left[kind]:
                    break
                src = R1.READ_ORDER if kind == "read_order" else R2.ORDER
                q = q_order(rng, kind, head, src[bp_left[kind].pop(0)])
            elif bpsec and kind == "t2r_pos":
                if not bp_left[kind]:
                    break
                q = q_pos(rng, kind, head, R2.POS[bp_left[kind].pop(0)])
            elif bpsec and kind == "listen_pic_dlg":
                if not bp_left[kind]:
                    break
                q = q_pic_dlg(rng, head, L1.LISTEN_PIC_DLG[bp_left[kind].pop(0)],
                              pics, pic_pool)
                if not q:
                    continue
            elif bpsec and kind == "t2_pic":
                # 실제 시험처럼 앞 둘은 그림, 마지막 하나는 그래프
                if made < T2PIC_SPLIT:
                    if not bp_left["t2_picdlg"]:
                        break
                    q = q_pic_dlg(rng, head, L2.T2_PICDLG[bp_left["t2_picdlg"].pop(0)],
                                  pics, pic_pool)
                    if not q:
                        continue
                    q["type"] = "t2_pic"
                else:
                    if not bp_left["t2_chart"]:
                        break
                    q = q_chart(rng, head, bp_left["t2_chart"].pop(0))
            elif bpsec and kind in ("t2_idea", "t2_act"):
                key, src, fn = (("t2_idea_m", T2_IDEA_M, q_t2_idea) if kind == "t2_idea"
                                else ("t2_act_f", T2_ACT_F, q_t2_act))
                if not bp_left[key]:
                    break
                q = fn(rng, src[bp_left[key].pop(0)])
            elif sec["kind"] == "particle":
                if not p_left:
                    break
                q = q_particle(rng, p_left.pop(0))
            elif sec["kind"] == "listen_reply":
                if not lr_left:
                    break
                q = q_listen_reply(rng, lr_left.pop(0))
            elif sec["kind"] == "listen_dialog":
                if not ld_left:
                    break
                q = q_listen_dialog(rng, ld_left.pop(0))
            elif sec["kind"] == "read":
                if not rd_left:
                    break
                q = q_read(rng, *rd_left.pop(0))
            elif sec["kind"] in ("t2_reply", "t2_act", "t2_same", "t2_idea"):
                k = sec["kind"][3:]
                if not t2[k]:
                    break
                q = {"reply": q_t2_reply, "act": q_t2_act,
                     "same": q_t2_same, "idea": q_t2_idea}[k](rng, t2[k].pop(0))
            elif sec["kind"] == "t2_read":
                if not t2_read:
                    break
                q = q_t2_read(rng, *t2_read.pop(0))
            elif sec["kind"] == "society":
                if not soc_left:
                    break
                q = q_society(rng, soc_left.pop(0))
            elif sec["kind"] == "t2_long":
                if not t2_long:
                    break
                q = q_t2_long(rng, *t2_long.pop(0))
            elif sec["kind"] == "job":
                if job_at >= len(JOB_VOCAB.get(bp["industry"], [])):
                    break
                q = q_job(rng, bp["industry"], job_at, used)
                job_at += 1
                if not q:
                    continue          # 이 낱말은 건너뛰고 다음 낱말로
            elif sec["kind"] == "listen_pic":
                w = rng.choice(pic_pool) if pic_pool else None
                if not w or w["ko"] in used:
                    continue
                q = q_listen_pic(rng, w, pics, pic_pool)
                if not q:
                    continue
                used.add(w["ko"])
            else:
                w = rng.choice(pic_pool if sec["kind"] == "pic2word" and pic_pool else usable)
                if w["ko"] in used:
                    continue
                fn = {"dfn2word": q_dfn2word, "word2vi": q_word2vi,
                      "vi2word": q_vi2word, "short": q_short}.get(sec["kind"])
                if fn:
                    q = fn(rng, w, gloss, pool_by_key)
                else:
                    q = q_pic2word(rng, w, gloss, pool_by_key, pics, pic_pool)
                if not q:
                    continue
                used.add(w["ko"])
            # 묶음 문항은 지문 하나에서 여럿이 한꺼번에 나온다
            if isinstance(q, list):
                for k, one in enumerate(q):
                    one["section"] = sec["label"]
                    one["no"] = len(qs) + 1
                    if sec.get("pts"):
                        one["pt"] = sec["pts"][min(made + k, len(sec["pts"]) - 1)]
                    qs.append(one)
                made += len(q)
                continue
            # 설계도 구간인데 옛 유형(조사·대답 고르기)이 들어왔으면 발문만 공식 문구로 바꾼다
            if bpsec and head:
                if kind in STEM_ONLY:
                    q["stem"] = head          # 뭉치에 딸린 물음이 공식 발문과 겹친다
                elif q["stem"].split("\n")[0] != head:
                    restem(q, head)
            q["section"] = sec["label"]
            q["no"] = len(qs) + 1
            if sec.get("pts"):
                q["pt"] = sec["pts"][min(made, len(sec["pts"]) - 1)]
            qs.append(q)
            made += 1
        if made < sec["n"]:
            skipped += sec["n"] - made
            print(f"  ! '{sec['label']}' {sec['n']}문항 요청 → {made}문항만 생성", file=sys.stderr)

    rebalance(rng, qs)

    out = {
        "id": exam_id, "set": seed, "name": bp["name"], "desc": bp["desc"],
        "name_vi": bp.get("name_vi", ""), "desc_vi": bp.get("desc_vi", ""),
        "minutes": bp["minutes"], "total": len(qs), "shortfall": skipped,
        "questions": qs,
    }
    # 문항마다 같은 배점인 시험(KIIP)은 설계도에 한 값으로 적혀 있다
    if bp.get("pt"):
        for q in qs:
            q["pt"] = bp["pt"]
    # 배점이 있는 시험은 만점과 급/합격 기준을 같이 실어 보낸다 — 화면에서 다시 세지 않게
    if any(q.get("pt") for q in qs):
        out["full"] = round(sum(q.get("pt", 0) for q in qs), 1)
        if exam_id == "topik-1":
            # 듣기+읽기 200점 만점. 국립국제교육원 공고 기준: 1급 80점 · 2급 140점
            out["grades_at"] = [[80, "1급"], [140, "2급"]]
    # KIIP은 우리가 채점할 수 없는 몫(작문·구술)이 따로 있다. 그 사실을 숨기지 않고
    # 같이 실어 보내서, 화면이 "이 점수가 전부"인 것처럼 보이지 않게 한다.
    for k in ("oral", "essay", "pass_at", "place_at"):
        if bp.get(k):
            out[k] = list(bp[k]) if isinstance(bp[k], tuple) else bp[k]
    # 듣기 재생 횟수 · 답 잠금 — 실제 시험이 막는 것을 우리도 막는다
    if bp.get("plays"):
        out["plays"] = bp["plays"]
    if bp.get("lock"):
        out["lock"] = True
    # CBT 규칙 — 읽기·듣기를 나눠 세고, 듣기로 넘어가면 되돌아갈 수 없다.
    # 경계는 문항에 소리가 붙는 자리에서 스스로 찾는다(청사진 순서가 바뀌어도 안 어긋나게).
    if bp.get("cbt"):
        qs = out["questions"]
        first_listen = next((i for i, q in enumerate(qs)
                             if q.get("audio") or q.get("heard") or q.get("script")), len(qs))
        out["cbt"] = {"split": first_listen,
                      "read": bp["cbt"]["read"], "listen": bp["cbt"]["listen"]}
    return out

ANCHOR_N = 6          # 한 시험 종류당 공통문항 수


def add_anchors(exams, per_type=ANCHOR_N):
    """회차마다 **같은 문항 몇 개**를 심는다 — 공통문항(anchor).

    왜 필요한가. 지금까지 회차마다 문항이 전부 달랐다. 그러면 1회차 70점과
    2회차 70점을 **견줄 수가 없다** — 점수 차이가 실력이 는 것인지 문제가 쉬웠던
    것인지 가릴 방법이 없기 때문이다. 시험을 여러 벌 만드는 곳은 어디나
    회차에 걸쳐 같은 문항 몇 개를 두고 그것으로 눈금을 맞춘다.

    우리는 여섯 개를 둔다(TOPIK I 70문항 기준 8.6%). 자리는 시험 전체에
    고르게 흩어 놓는다 — 앞쪽에 몰면 쉬운 문항만 공통이 되어 눈금이 한쪽으로 쏠린다.

    같은 구간(section)일 때만 바꿔 넣는다. 구간이 다르면 배점과 발문이 어긋난다.
    ko_exam_check 의 '회차중복'은 anchor 를 건너뛴다 — 일부러 넣은 것이라서.
    """
    by = {}
    for e in exams:
        by.setdefault(e["id"], []).append(e)
    n_marked = 0
    for eid, sets in by.items():
        if len(sets) < 2:
            continue                      # 한 벌뿐이면 견줄 상대가 없다
        base, rest = sets[0], sets[1:]
        n = min(len(s["questions"]) for s in sets)
        if n < per_type * 2:
            continue
        step = n // per_type
        idxs = [i * step + step // 2 for i in range(per_type)]   # 고르게 흩는다
        for i in idxs:
            src = base["questions"][i]
            if src.get("short"):
                continue                  # 단답형은 채점이 글자 대조라 눈금으로 안 쓴다
            ok = [s for s in rest
                  if s["questions"][i].get("section") == src.get("section")
                  and not s["questions"][i].get("short")]
            if not ok:
                continue
            src["anchor"] = True
            n_marked += 1
            for s in ok:
                old = s["questions"][i]
                q = json.loads(json.dumps(src))
                q["no"] = old["no"]
                if "pt" in old:
                    q["pt"] = old["pt"]
                q["anchor"] = True
                s["questions"][i] = q
    print(f"공통문항: {n_marked}자리 × 회차 (시험 {len(by)}종)", file=sys.stderr)


def rebalance(rng, qs):
    """정답 번호를 네 자리에 고르게 흩는다.

    보기를 섞기만 하고 두면 정답이 한 번호에 몰리는 판이 가끔 나온다
    (실제로 20문항 중 13개가 ④번에 몰린 회차가 나왔다 — 그러면 ④만 찍어도 65점이다).
    운에 맡기지 말고, 각 번호가 전체의 1/4씩 되도록 정답과 그 자리의 보기를 맞바꾼다.
    보기 내용은 그대로고 자리만 바뀌므로 문제의 뜻은 달라지지 않는다.
    """
    # 단답형은 보기가 없다 — 섞을 자리도 없으니 빼고 센다
    pick = [q for q in qs if not q.get("short")]
    targets = [i % 4 for i in range(len(pick))]
    rng.shuffle(targets)
    for q, t in zip(pick, targets):
        a = q["answer"]
        if a == t:
            continue
        q["options"][a], q["options"][t] = q["options"][t], q["options"][a]
        if q.get("exp"):
            q["exp"][a], q["exp"][t] = q["exp"][t], q["exp"][a]
        q["answer"] = t

if __name__ == "__main__":
    words, gloss, pics = load()
    print(f"어휘 {len(words)} · 뜻풀이 {len(gloss)} · 그림 {len(pics)}", file=sys.stderr)
    out = {"note": "형식만 실제 시험을 따르고 문항은 자체 생성. 기출 전재 아님.", "exams": [],
           # 정답이 하나가 아닌 문항 — AI가 채점한다
           "extra": {
               "speak": [{"passage": p, "questions": qs} for p, qs in ko_content.SPEAK_BANK],
               "write": [{"title": t, "chars": n} for t, n in ko_content.WRITE_BANK],
               # TOPIK II 쓰기 — 51·52(빈칸 둘) / 53·54(긴 글). 채점 요령을 같이 실어
               # AI 가 무엇을 볼지 정해 준다(그냥 "잘 썼나요"라고 물으면 채점이 흔들린다).
               "t2_blank": [{"title": t, "text": x, "model": m, "how": h}
                            for t, x, m, h in ko_content_t2.T2_WRITE_BLANK],
               "t2_long": [{"title": t, "chars": n, "how": h}
                           for t, n, h in ko_content_t2.T2_WRITE_LONG],
               # TOPIK 말하기 — 유형마다 준비·응답 시간이 다르다. 그 시간표가 이 시험의 핵심이라
               # 문항과 함께 그대로 실어 보낸다(화면에서 다시 정하지 않게).
               "topik_speak": ko_speak_topik.build(),
           }}
    for exam_id in BLUEPRINTS:
        state = {}                     # 시험 종류마다 따로 — EPS와 KIIP는 서로 겹쳐도 된다
        # 직무 어휘는 낱말이 정해져 있어 회차를 나눌 수 없다 — 한 벌만 낸다
        # 재료가 몇 벌치인지에 따라 회차 수가 다르다 — 없는 것을 있는 척하지 않는다.
        n_sets = 3
        if exam_id.startswith("eps-job-") or exam_id == "kiip-5":
            n_sets = 1
        elif exam_id == "topik-2-listen":
            n_sets = bp_sets(["TOPIK II 듣기"])
        elif exam_id == "topik-2-read":
            n_sets = bp_sets(["TOPIK II 읽기"])
        elif exam_id == "topik-1":
            # 설계도가 모는 시험은 재료가 몇 회분인지 세어서 정한다
            n_sets = bp_sets(["TOPIK I 듣기", "TOPIK I 읽기"])
        for seed in range(1, n_sets + 1):
            e = build(exam_id, seed, words, gloss, pics, state)
            out["exams"].append(e)
            print(f"{exam_id} {seed}회차: {e['total']}문항 (부족 {e['shortfall']})", file=sys.stderr)
    add_anchors(out["exams"])
    path = os.path.join(DATA, "ko_exams.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", path, file=sys.stderr)
