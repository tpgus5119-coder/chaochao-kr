#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**이름 없는 목차** — 권 / 챕터 / 레슨 번호만. → data/order.json

차례를 정하는 규칙 (대표님, 2026-08-30)
  ① **기수 번호를 더한 값이 큰 낱말이 앞**이다.
     20+19+18+17=74 > 20+19+18=57 > 19+18+17=54 > 20+19=39 > 20=20
     겹친 기수가 많을수록 합이 커지므로 이 하나로 '겹침 수'까지 함께 반영된다.
     그리고 같은 겹침 수라면 **더 최근 기수**에 나온 쪽이 앞이다.
  ② 합이 같으면 **가장 최근 기수에서 몇 회차에 나왔는지**(이른 회차가 앞).
  ③ 그것도 같으면 그 회차 안에서 적힌 차례.  ④ 그래도 같으면 글자 차례.
  → 예외 없이 모든 낱말의 자리가 정해진다.

무엇을 넣나
  · 일상: **선배 낱말만.** 우리가 만든 일상 낱말은 뺀다.
  · 직무: 선배 직무 낱말을 위 규칙대로 먼저, **우리가 만든 직무 낱말은 그 뒤에.**
쓰기: python3 tools/order_build.py
"""
import json, pathlib, re, sys, unicodedata as U, collections

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr
sys.path.insert(0, str(R / "tools"))
from senior_split import JOB as JOBPAT

PER = 15
JOBRE = [(k, re.compile(v)) for k, v in JOBPAT.items()]
# 갈래는 **다섯**이면 된다. 공통이 대부분이고 업종 낱말은 원래 적다 —
# 공장에서 쓰는 말의 대부분은 어느 공장에서나 같기 때문이다(실측: 620개 중 483개가 공통).
# 한국인이 실제로 취업하는 순서 (KOTRA 2023) — 제조업 1위, 그중 생산관리가 40%
# 갈래 차례 — 공통을 먼저(생산관리가 취업의 40%), 그 다음 업종을 채용 많은 순으로
# 갈래 차례 — 공통 먼저, 그 다음 업종을 **실제 취업 비중 + 향후 전망** 순으로
#   전자가 1순위다: 삼성이 GDP 13%(실제) · 반도체·첨단소재로 옮겨 가는 중(전망).
#   섬유·봉제와 신발·가방은 한 묶음이다 — 노동집약 경공업이고 공정이 같다.
JOBORDER = ["공통 · 생산과 공정", "공통 · 품질과 검사", "공통 · 자재와 창고",
            "공통 · 기계와 설비", "공통 · 안전과 환경", "공통 · 사람과 조직", "공통 · 서류와 회계",
            "전자·반도체", "섬유·봉제·신발", "기계·금속·자동차", "물류·무역",
            "건설", "화학·플라스틱", "식품", "유통·판매", "요식"]
# 직무는 **한 권**이다 (대표님 결정, 2026-08-30).
#   "꼭 필요한 기본 낱말만 남기고, 진짜 심화는 현장에서 배우라고 해라."
#   그래서 낱말마다 **기본인가 심화인가**를 가른다. 잣대는 자료다:
#     ① 선배 시험·일터 단톡방·앱 어디에든 나오면 = 실제로 입으로 쓰는 말 = 기본
#     ② 내가 쓴 낱말이면 두 마디 이하 + 뜻이 짧은 것 = 기본
#   나머지는 「현장에서 배우는 말」 사전으로 뺀다 — 지우지 않는다.
JOB_CAP = 999
# 갈래마다 몫 — **실제 취업 비중이 1순위, 향후 전망이 2순위** (대표님 기준, 2026-08-30).
#   전자가 가장 크다: 삼성 하나가 GDP 13%(실제) · 반도체·첨단소재로 옮겨 가는 중(전망).
#   섬유·봉제·신발이 그다음(노동집약 경공업 한 묶음).
#   자를 때 뒤쪽 갈래가 통째로 사라지지 않게, 갈래별로 자른다.
TRACK_CAP = {
 "전자·반도체": 260, "섬유·봉제·신발": 190,
 "공통 · 생산과 공정": 120, "공통 · 기계와 설비": 40,
 "공통 · 사람과 조직": 85, "공통 · 서류와 회계": 65,
 "공통 · 안전과 환경": 50, "공통 · 품질과 검사": 45, "공통 · 자재와 창고": 40,
 "기계·금속·자동차": 45, "물류·무역": 45, "건설": 35,
 "화학·플라스틱": 30, "식품": 30, "유통·판매": 25, "요식": 25,
}


def field_of(ko):
    """직무 낱말을 갈래로 — 봉제 갈 사람은 전자를 안 배워도 된다(대표님 지시).
       업종에 안 걸리면 '공통'이다. 관리자·잔업·수량·버튼 같은 말이 그것이다."""
    for k, rx in JOBRE:
        if k.startswith("공통"): continue
        if rx.search(ko or ""): return k
    return "공통 · 생산과 공정"


def src_rank(x):
    """출처 차례 — 선배 시험 → 카톡방 → 대표님이 주신 자료 → 앱이 만든 것.
       999개로 자를 때 **출처 없는 것부터** 잘리게 하려는 것이다."""
    if x.get("sr"): return 0
    if x.get("kakao"): return 1
    if x.get("sew") or x.get("trade"): return 2
    return 3                      # 한 레슨 열다섯 낱말

def key(v):
    """겹침을 견줄 때 쓰는 꼴 — 괄호 안은 곁들이 설명이라 뗀다."""
    s = U.normalize("NFC", str(v)).strip().lower()
    s = re.sub(r"\([^)]*\)", "", s)
    return re.sub(r"\s+", " ", s).strip(" .,;:!?~–—/\"'")


def cut_sent(s, vi):
    """대화 자료에는 **두 문장이 한 줄**에 든 것이 있다 —
       'Làm ơn giúp tôi được không? Tôi cần hỏi một chút.'
       예문으로는 길어서 그 낱말이 든 문장만 남긴다 (2026-08-30 검수)."""
    parts = [x.strip() for x in re.split(r"(?<=[.!?])\s+", s["vi"]) if x.strip()]
    if len(parts) < 2 or len(s["vi"].split()) <= 10: return s
    kos = [x.strip() for x in re.split(r"(?<=[.!?])\s+", s.get("ko", "")) if x.strip()]
    t = U.normalize("NFC", vi).lower()
    for i, x in enumerate(parts):
        if t in U.normalize("NFC", x).lower():
            return {"vi": x, "ko": kos[i] if i < len(kos) else s.get("ko", ""), "kr": ""}
    return s


def exkey(v):
    """예문 표(_examples.json)의 열쇠 꼴 — gen_examples.py 와 **똑같아야** 한다.
       여기서 괄호를 떼면 'bến xe (buýt)' 를 못 찾아 낱말이 통째로 떨어진다."""
    s = U.normalize("NFC", str(v)).strip().lower()
    s = re.sub(r"^[\d]+[.\)]\s*", "", s)
    return re.sub(r"\s+", " ", s).strip(" .,;:!?~–—/\"'()")

def rank(w):
    """작을수록 앞. 위 ①②③④ 를 그대로 옮긴 것."""
    gis = re.findall(r"\d\d", w.get("gi", ""))
    tot = sum(int(g) for g in gis)
    rd = w.get("rd") or {}
    late = max(rd, key=lambda g: int(g)) if rd else None
    no, at = rd[late] if late else (9999, 9999)
    return (-tot, no, at, w["vi"].lower())

def main():
    sp = json.loads((R / "data" / "_senior_split.json").read_text(encoding="utf-8"))["words"]
    ex = json.loads((R / "data" / "_examples.json").read_text(encoding="utf-8"))
    # 앱이 이미 가진 것 — 그림·한자·성조, 그리고 앱 대화의 예문
    d = json.loads((R / "data" / "days.json").read_text(encoding="utf-8"))
    days = d if isinstance(d, list) else d["days"]
    extra, appjob, sents = {}, [], []
    for day in days:
        work = day.get("track") == "work"
        for w in (day.get("words") or []):
            k = key(w.get("vi", ""))
            if not k: continue
            extra[k] = {t: w[t] for t in ("img", "hanja", "tones", "kr_read", "south") if w.get(t)}
            if work: appjob.append({"vi": w["vi"], "ko": w.get("ko", ""), "app": 1})
        dl = day.get("dialog") or {}
        for l in (dl.get("lines") or []):
            if l.get("vi"): sents.append({"vi": l["vi"], "ko": l.get("ko", ""), "kr": l.get("kr_read", "")})
    holds = [" " + key(s["vi"]) + " " for s in sents]
    used = set()

    def dress(w, job_app=False):
        k = key(w["vi"])
        o = {"vi": w["vi"], "ko": w["ko"], "kr": vi_kr.word(w["vi"]), "krs": vi_kr.word(w["vi"], True)}
        gis = re.findall(r"\d\d", w.get("gi", ""))
        if gis: o["gi"] = "".join(gis); o["sr"] = 1
        if len(gis) >= 2: o["core"] = len(gis)
        if job_app: o["app"] = 1
        for f in ("kakao", "sew", "trade", "track"):     # 출처 표시를 잃지 않는다
            if w.get(f): o[f] = w[f]
        # 갈래는 senior_split 이 이미 정했다 — 여기서 다시 계산하면 세부 갈래가 뭉개진다
        if w.get("field") and w["field"] != "일상": o.setdefault("track", w["field"])
        o.update(extra.get(k, {}))
        if w.get("ex"): o["ex"] = w["ex"]          # 자료에 예문이 딸려 있으면 그것을 쓴다
        t = " " + k + " "
        hit = next((i for i, h in enumerate(holds) if t in h and i not in used), None)
        if hit is not None:
            used.add(hit); s = cut_sent(sents[hit], w["vi"])
            o["ex"] = {"vi": s["vi"], "ko": s["ko"], "kr": s["kr"] or vi_kr.word(s["vi"]),
                       "krs": vi_kr.word(s["vi"], True)}
        else:
            e = ex.get(exkey(w["vi"])) or ex.get(k)
            if e: o["ex"] = e
        return o if o.get("ex") else None          # 예문이 없는 것은 낱말이 아니다

    life = sorted([w for w in sp if w["field"] == "일상"], key=rank)
    job  = sorted([w for w in sp if w["field"] not in ("일상", "문법용어")], key=rank)
    # 말에 대한 말(모음·자음·성조·명사…)은 **1권**으로 보낸다 — 일상 낱말이 아니다
    gramw = sorted([w for w in sp if w["field"] == "문법용어"], key=rank)
    L = [x for x in (dress(w) for w in life) if x]
    # 교재 낱말표(4권 베트남어 교재_단어.xlsx)는 **안 넣는다** (대표님 지시, 2026-08-30).
    # 1,148개 중 새로 나오는 것이 56개뿐이라 넣을 값어치가 없다 — 거의 다 시험지에 이미 있다.
    J = [x for x in (dress(w) for w in job) if x]
    seen = {key(x["vi"]) for x in J}
    # 직무 차례: 선배 시험 → 카톡방 정리 → 우리가 만든 것
    kk = R / "data" / "_kakao_job.json"
    if kk.exists():
        for w in json.loads(kk.read_text(encoding="utf-8"))["words"]:
            if key(w["vi"]) in seen: continue
            x = dress(w); 
            if x: x["kakao"] = 1; J.append(x); seen.add(key(w["vi"]))
    # **우리가 만든 직무 낱말은 맨 뒤**다 (대표님 지시). 근거가 선배 자료가 아니라
    # 예전에 우리가 "공장에서 쓸 만하다"고 넣은 것이라, 출처 있는 낱말 뒤에 둔다.
    # 대표님이 주신 봉제용어.xls — 갈래를 '봉제'로 박아 둔다(뜻이 '뒤품'이라 알아보는 말로는 못 잡는다)
    sw = R / "data" / "_sewing.json"
    if sw.exists():
        seen2 = {key(x["vi"]) for x in J}
        for w in json.loads(sw.read_text(encoding="utf-8"))["words"]:
            if key(w["vi"]) in seen2: continue
            x = dress(w)
            # 갈래는 sewing_words.py 가 이미 정했다(기본 / 찾아보기) — 덮어쓰지 않는다
            if x: x["track"] = w.get("track") or "섬유·봉제·신발"; J.append(x); seen2.add(key(w["vi"]))
    # 내가 쓴 업종 낱말 — 대표님 자료에 없던 갈래를 채운 것 (tools/job_words.py)
    jw = R / "data" / "_jobwords.json"
    if jw.exists():
        seenj = {key(x["vi"]) for x in J}
        for w in json.loads(jw.read_text(encoding="utf-8"))["words"]:
            if key(w["vi"]) in seenj: continue
            x = dress(w)
            if x: x["track"] = w["track"]; x["made"] = 1; J.append(x); seenj.add(key(w["vi"]))
    tw = R / "data" / "_trade.json"
    if tw.exists():
        seen4 = {key(x["vi"]) for x in J}
        for w in json.loads(tw.read_text(encoding="utf-8"))["words"]:
            if key(w["vi"]) in seen4: continue
            x = dress(w)
            if x: x["track"] = "공통"; J.append(x); seen4.add(key(w["vi"]))
    seen3 = {key(x["vi"]) for x in J}
    J += [x for x in (dress(w, True) for w in appjob if key(w["vi"]) not in seen3) if x]

    ALTS = {}
    _ap = R / "data" / "_altsplit.json"
    if _ap.exists(): ALTS = json.loads(_ap.read_text(encoding="utf-8"))

    def pair_same(ws):
        """뜻이 같아 보이는 **다른 낱말**을 어떻게 할지 정한다.

           처음에는 무조건 한 자리에 같이 보여 줬다. 그런데 살펴보니
           bí quyết(비결)↔bí mật(비밀) · cơ hội(기회)↔cơ(계기) · lông mày(눈썹)↔mắt(눈)
           처럼 **아예 다른 낱말**까지 묶여 있었다 (대표님 지적, 2026-08-30).
             · 쓰임이 다르면 → **갈라 세우고 뜻을 서로 다르게 적는다** (_altsplit.json)
             · 정말 같은 말이면 → 지금처럼 한 자리에 같이 (quần đùi / quần soóc)
           어느 쪽이든 **낱말을 지우지는 않는다** — 하나를 지우면 그 말을 못 배운다."""
        seen, out = {}, []
        for w in ws:
            k = re.sub(r"[\s,/()·]", "", w["ko"])
            if k and k in seen:
                first = seen[k]
                d = ALTS.get(f'{first["vi"]}|{w["vi"]}') or {}
                if d and not d.get("same"):
                    # 쓰임이 다르다 — 따로 세우고 뜻을 갈라 적는다
                    if d.get("ka"): first["ko"] = d["ka"]
                    if d.get("kb"): w["ko"] = d["kb"]
                    out.append(w)
                    continue
                first.setdefault("alt", []).append({"vi": w["vi"], "kr": w.get("kr", ""),
                                                    "krs": w.get("krs", "")})
                continue
            seen[k] = w
            out.append(w)
        return out


    def even(ws, base=PER, lo=10, hi=19):
        """낱말 뭉치를 **고르게** 레슨으로 나눈다 (대표님 규칙, 2026-08-30):
             · 기본 15개, **10~19개까지 허용**
             · 끝 레슨에 3개만 남는 꼴을 안 만든다 — 앞 레슨을 한 칸씩 늘려 흡수한다
             · 전체가 10개 미만이면 **그냥 한 레슨**이다 (더 쪼갤 수 없다)
           보기: 155개 → 16×5 + 15×5 (10레슨) · 20개 → 10+10 · 13개 → 13 하나 · 9개 → 9 하나"""
        n = len(ws)
        if n <= hi: return [ws]
        k = max(-(-n // hi), round(n / base) or 1)     # 한 레슨이 hi 를 넘지 않게
        k = max(1, min(k, n // lo))                    # 한 레슨이 lo 밑으로 안 내려가게
        q, r = divmod(n, k)
        out, i = [], 0
        for j in range(k):
            m = q + (1 if j < r else 0)
            out.append(ws[i:i + m]); i += m
        return out

    def cut(ws, per_ch):
        """낱말 뭉치 → 챕터들. 챕터마다 per_ch 레슨, 끝 챕터도 고르게 채운다."""
        les = even(ws)
        if len(les) <= per_ch: return [les]
        nc = max(1, round(len(les) / per_ch) or 1)     # 챕터 수
        q, r = divmod(len(les), nc)
        if q < 2: nc = max(1, len(les) // 2); q, r = divmod(len(les), nc)
        out, i = [], 0
        for j in range(nc):
            m = q + (1 if j < r else 0)
            out.append(les[i:i + m]); i += m
        return out

    # 레슨 15낱말 · 챕터 10레슨(150낱말) · 권 6챕터(900낱말)
    # 레슨 15낱말. **네 권이 똑같은 레슨 수**가 되게 나눈다 (대표님 지시, 2026-08-30).
    #   챕터 수를 먼저 정하면 마지막 권만 얇아진다 — 레슨 수를 먼저 맞춘다.
    LES_PER_CH, VOLS = 10, 4
    L = pair_same(L)
    per_vol_w = -(-len(L) // VOLS)                  # 권마다 낱말 수를 고르게
    vols = []
    for i in range(0, len(L), per_vol_w):
        part = L[i:i + per_vol_w]
        chs = cut(part, LES_PER_CH)
        vols.append({"kind": "life",
                     "chapters": [{"lessons": [{"words": w} for w in ch]} for ch in chs]})
    # 직무는 **갈래별로** 나눈다 — 갈래는 이름을 둔다(어디로 갈지가 사람마다 다르다)
    byf = collections.OrderedDict((k, []) for k in JOBORDER)
    J = pair_same(J)
    # 일상에서 이미 배우는 낱말은 **직무에서 뺀다** (대표님 지적, 2026-08-30).
    #   같은 낱말을 두 권에서 두 번 외우게 할 까닭이 없다. 일상을 먼저 배우니 거기 둔다.
    #   다만 **일터에서 뜻이 달라지면**(Kế hoạch 계획→계획 수량) 일상 카드에 그 뜻을 덧붙인다.
    lifeko = {}
    for x in L: lifeko[key(x["vi"])] = x
    same, moved = 0, 0
    keepJ = []
    for x in J:
        y = lifeko.get(key(x["vi"]))
        if not y: keepJ.append(x); continue
        a = x["ko"].split("/")[0].strip(); b = y["ko"].split("/")[0].strip()
        if a != b:
            y.setdefault("work", []).append(x["ko"])      # 일터에서는 이런 뜻
            moved += 1
        else: same += 1
    J = keepJ
    if same or moved:
        print(f"   일상과 겹쳐 직무에서 뺀 낱말 {same + moved}개 "
              f"(뜻이 같은 것 {same} · 일터 뜻을 일상 카드에 붙인 것 {moved})")

    # ── 직무에 들어갈 것이 아닌 것 (2026-08-30, 대표님 지시로 하나씩 읽고 골라냄)
    #    ① 낱말이 아니라 **그날 그 대화의 문장**  ② **그 공장에서만 쓰는 약어**
    #    ③ 일상 권에 있어야 할 말. 뺀 자리는 전자 낱말로 채운다(취업 비중 1순위).
    JUNK_CO = re.compile(r"PP팀|WRB|CRO|SEV|UPL|R420|리리프|PQC|OQC|EQM|ME\b|Hướng dẫn")
    JUNK_SENT = re.compile(r"(다|요|까|야|지|네|어)[.?!]?$")
    DAILY_IN_JOB = {
     "호치키스", "선풍기를 켜다", "점심밥", "점심 휴식", "층", "구역", "통로", "문", "계단",
     "되돌아가다", "전화를 받다", "펜", "공항", "방을 예약하다", "환율", "수수료", "비밀번호",
     "게으르다", "태도", "버리다", "도와주다", "존중하다", "따르다", "강요하다", "이유",
     "이것", "저것", "이렇게", "2차", "학사일정", "제조국", "자국 / 흔적", "노선, 라인",
     "실질적인, 현실적인", "고정된, / 일정한", "대신하다, 교대하다", "메모", "설치하다",
     "프레젠테이션 파일", "방법 / 방식", "발생하다", "철저히 / 완전히", "계속하다", "미달",
    }

    def job_junk(x):
        ko = x["ko"].strip()
        if ko in DAILY_IN_JOB: return True
        if JUNK_CO.search(ko) or JUNK_CO.search(x["vi"]): return True
        # 뜻이 네 어절 넘고 문장처럼 끝나면 낱말이 아니다
        if len(ko.split()) >= 4 and JUNK_SENT.search(ko): return True
        if len(ko) > 20: return True
        # 일터 단톡방에서 온 **세 마디 이상**은 그날 그 대화의 문장이다 —
        #   'còn lại 4 bạn(4명 남았다)' · 'line bóc không kịp(작업이 못 따라간다)'.
        #   두 마디 이하는 낱말이다('báo tổ trưởng 조장에게 알리다' · 'dừng chuyền 라인 정지').
        if x.get("kakao") and len(x["vi"].split()) >= 3: return True
        return False

    n_junk = sum(1 for x in J if job_junk(x))
    J = [x for x in J if not job_junk(x)]
    print(f"   직무에서 뺀 것 {n_junk}개 (문장 조각·그 공장 약어·일상 낱말)")

    # ── 기본인가 심화인가 (대표님 지시: 심화는 현장에서 배운다)
    def is_basic(x):
        if x.get("track") == "봉제 찾아보기": return False
        if x.get("sr") or x.get("kakao"): return True          # 실제로 시험 보고 말한 낱말
        # 내가 업종별로 **골라 쓴 낱말**은 애초에 기본만 고른 것이다(tools/job_words.py).
        #   길이로 다시 재면 bo mạch(기판)·chất bán dẫn(반도체) 같은 알맹이가 떨어진다.
        if x.get("made"): return True
        ko = x["ko"]
        if len(x["vi"].split()) <= 2 and len(ko) <= 9 and not re.search(r"[(/,·]", ko):
            return True                                        # 짧고 단순하면 기본
        return False
    # 심화 낱말은 **앱에 넣지 않는다** (대표님 지시, 2026-08-30).
    #   따로 사전으로 두지도 않는다 — 현장에서 배우면 되는 말이다.
    n_out = sum(1 for x in J if not is_basic(x))
    J = [x for x in J if is_basic(x)]
    print(f"   직무 기본 {len(J)} · 현장에서 배울 말이라 넣지 않은 것 {n_out}")
    # **두 권으로 나눈다** — 공통 900 · 업종 900. 각각 900을 넘으면 출처 없는 것부터 자른다.
    J.sort(key=lambda x: (src_rank(x), -sum(int(g) for g in re.findall(r"\d\d", x.get("gi", "")))))
    def trim(ws, cap, what):
        over = len(ws) - cap
        if over <= 0: return ws
        keep, dropped = [], 0
        for x in reversed(ws):
            if dropped < over and src_rank(x) == 3: dropped += 1; continue
            keep.append(x)
        print(f"   {what} {cap}개로 맞추려고 앱이 만든 낱말 {dropped}개를 뺐다")
        return list(reversed(keep))
    # 갈래별로 몫만큼 남긴다 — 출처가 있는 낱말이 앞이라 앱이 만든 것부터 잘린다
    byt = collections.OrderedDict()
    for x in J: byt.setdefault(x.get("track") or field_of(x["ko"]), []).append(x)
    J, cutn = [], 0
    for k, ws in byt.items():
        cap = TRACK_CAP.get(k, 40)
        if len(ws) > cap: cutn += len(ws) - cap
        J += ws[:cap]
    if cutn: print(f"   갈래 몫에 맞추려고 {cutn}개를 뺐다")
    for x in J:
        k = x.get("track") or field_of(x["ko"])
        if k == "공통": k = "공통 · 생산과 공정"
        byf.setdefault(k, []).append(x)
    tracks = []
    for k, ws in byf.items():
        if not ws: continue
        # 갈래 **안에서** 대표님이 정하신 차례를 지킨다 —
        # 선배 시험(기수 합 큰 것부터) → 카톡방 → 봉제·무역 자료 → 앱이 만든 것
        def src(x):
            return 0 if x.get("sr") else 1 if x.get("kakao") else 2 if x.get("sew") or x.get("trade") else 3
        ws.sort(key=lambda x: (src(x), -sum(int(g) for g in re.findall(r"\d\d", x.get("gi", "")))))
        tracks.append({"track": k, "words": len(ws),
                       "chapters": [{"lessons": [{"words": w} for w in ch]}
                                    for ch in cut(ws, LES_PER_CH)]})
    vols.append({"kind": "job", "vol": "직무", "tracks": tracks})
    G = [x for x in (dress(w) for w in gramw) if x]
    (R / "data" / "order.json").write_text(json.dumps(
        {"note": "이름 없는 목차. 권/챕터/레슨 번호만. 차례는 기수 합 → 최근 기수 회차 → 회차 안 자리.",
         "vols": vols, "gramwords": G}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"1권으로 보낸 '말에 대한 말' {len(G)}개:", " · ".join(x["ko"][:8] for x in G[:12]))
    print(f"일상(선배만) {len(L)} · 직무 {len(J)}(그중 우리가 만든 것 {sum(1 for x in J if x.get('app'))})")
    for i, v in enumerate(vols, 1):
        if v["kind"] == "job":
            print(f"   {i}권 직무 {v.get('vol','')} — 갈래 {len(v['tracks'])}개 · "
                  f"{sum(t['words'] for t in v['tracks'])}낱말")
            for t in v["tracks"]:
                ls = sum(len(c["lessons"]) for c in t["chapters"])
                print(f"        {t['track']:<16} {len(t['chapters'])}챕터 · {ls}레슨 · {t['words']}낱말")
            continue
        n = sum(len(l["words"]) for c in v["chapters"] for l in c["lessons"])
        ls = sum(len(c["lessons"]) for c in v["chapters"])
        print(f"   {i}권 일상  {len(v['chapters'])}챕터 · {ls}레슨 · {n}낱말")

if __name__ == "__main__":
    main()
