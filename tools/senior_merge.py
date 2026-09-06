#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""네 기수 시험을 **하나로** 합친다 → data/senior_pool.json

앞선 판(_senior_pool3)과 다른 점 (2026-08-30)
  ① **버리던 판을 되살린다.** 뜻이 영어인 판(38개)·낱말만 있는 판(50개)을
     그냥 버렸었다. 낱말은 멀쩡하다 — 뜻은 **다른 기수에서 빌려** 채운다.
  ② **겹침을 제대로 지운다.** 홑화(NFC)·소문자·겹빈칸·끝부호·번호 찌꺼기까지
     맞춘 뒤 견준다. 성조만 다른 것은 다른 낱말이니 남긴다.
  ③ **문장은 뺀다.** 선배 시험지에는 예문도 섞여 있다(낱말이 아니다).
  ④ 배운 차례(pos)를 같이 적는다 — 목차를 이 값으로 세운다.
쓰기: python3 tools/senior_merge.py
"""
import json, pathlib, re, statistics, unicodedata as U, collections

R = pathlib.Path(__file__).resolve().parent.parent
GI = ["17", "18", "19", "20"]
KO = re.compile(r"[가-힣]")
SENT = re.compile(r"[.?!]|다\.$|요\.$|까\?$")

def norm(v):
    """낱말 꼴 다듬기. **앞뒤 괄호는 벗기되 안의 말은 살린다** —
       '(một) vài' 는 '몇몇의', '(màu) xanh da trời' 는 '파란색'인 진짜 낱말인데
       괄호로 시작한다는 이유로 통째로 버려지고 있었다 (2026-08-30)."""
    s = U.normalize("NFC", str(v)).strip().lower()
    s = re.sub(r"^[\d]+[.\)]\s*", "", s)
    s = re.sub(r"^\(([^)]{1,12})\)\s+", r"\1 ", s)     # (một) vài → một vài
    s = re.sub(r"\s+\(([^)]{1,12})\)$", r" \1", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" .,;:!?~–—/\"'()")

def clean_ko(k):
    """뜻에서 **영어를 다 뗀다**. 선배 시험은 'cell phone/ 휴대폰' 처럼 붙어 있는데,
       퀴즈에서 답이 새어 나온 적이 있다(영어가 붙은 보기만 정답이었다).
       한글이 한 글자도 안 남으면 뜻이 없는 것으로 친다."""
    k = U.normalize("NFC", str(k)).strip()
    k = re.sub(r"[（(][^)）]*[)）]", lambda m: "" if not KO.search(m.group(0)) else m.group(0), k)
    k = re.sub(r"[A-Za-z][A-Za-z0-9 ,'’\-]*", " ", k)          # 영어 토막 통째로
    k = re.sub(r"\s*[/=~·]\s*", " / ", k)
    k = re.sub(r"\s+", " ", k).strip(" ,/·-–—:=")
    k = k.strip(" .?!")                     # '왜?' · '교환하다.' 는 낱말이다. 부호만 뗀다
    k = re.sub(r"^/\s*|\s*/$", "", k).strip()
    k = re.sub(r"(\s*/\s*)+", " / ", k)
    # 영어를 떼고 나면 토막만 남는 것이 있다 — '스웨터를', '이 경우에는', '4 사이즈'
    if re.search(r"[을를이가에서로와과의]$", k) and len(k) <= 8: return ""
    if len(k) < 2: return ""
    return k if KO.search(k) else ""

DICT = set()
_d = pathlib.Path("/usr/share/dict/words")
if _d.exists():
    DICT = {w.strip().lower() for w in _d.read_text(errors="ignore").splitlines() if w.strip()}


def real_en(en):
    """정말 영어 낱말인가. 칸이 어긋나 '뜻' 자리에 베트남어(Anh·Em·Bao…)가 들어온다.
       성조 부호가 없으면 눈으로는 못 가른다 — 그래서 **영어 낱말집**에 물어본다."""
    t = [x for x in re.split(r"[\s/()]+", en.lower()) if x]
    t = [x for x in t if x not in ("to", "the", "a", "an")]
    return bool(t) and all(x in DICT for x in t)


def is_word(vi, ko, en="", raw=""):
    """낱말인가 문장인가. 선배 시험지엔 예문이 섞여 있고, 칸이 어긋나
       문장이 토막 나 들어오기도 한다(‘Nhà vệ / sinh đâu ạ?’). 둘 다 뺀다."""
    if not vi or len(vi) > 34: return False
    if len(vi.split()) > 4: return False
    if not re.search(r"[A-Za-zÀ-ỹ]", vi): return False
    # 물음표가 있어도 **낱말 넷 이하면 낱말**이다 ('Chúc mừng năm mới!' 는 인사말이다)
    if re.search(r"[?!]", raw or vi) and len((raw or vi).split()) >= 5: return False
    if ko and len(ko) > 34: return False
    if ko and re.search(r"(다|요|까)[.?!]\s*$", ko) and len(ko.split()) >= 4: return False
    if not ko:
        # 뜻이 없으면 **영어 낱말 하나**일 때만 살린다. 나머지는 문장 토막이다.
        # 칸이 어긋나면 '뜻' 자리에 베트남어가 들어온다(‘Bao / nhiêu vậy?’) — 그건 토막이다.
        if not en or len(en.split()) > 2 or "/" in en: return False
        if not re.fullmatch(r"[A-Za-z][A-Za-z \-/() ]*", en): return False
        if not real_en(en): return False                            # 뜻 자리에 베트남어
        if vi[:1].isupper() and " " in vi: return False             # 대문자로 시작하는 여러 낱말 = 문장 토막
    return True

ROUND = re.compile(r"(\d+)\s*(?:회차|회|차)")

def positions(files):
    """회차 번호를 0~1 자리로 바꾼다.
       **번호를 그대로 나누면 안 된다** — 18기엔 날짜를 번호로 쓴 파일이 섞여 있어
       (0118 → 118) 가장 큰 값이 튀고, 진짜 회차들이 전부 0 쪽에 몰린다.
       그래서 **이름에 '회차'가 박힌 파일만** 골라 **줄 세운 등수**로 자리를 매긴다."""
    real = sorted({f["no"] for f in files if ROUND.search(f["src"]) and f["no"] > 0})
    if len(real) < 3: return {}
    return {n: i / (len(real) - 1) for i, n in enumerate(real)}


def filled():
    """시험지에 뜻이 안 적혀 있던 낱말의 뜻 — tools/fill_meaning.py 가 채운 것.
       이게 없으면 `chúc mừng năm mới`·`mùa thu` 같은 흔한 말이 통째로 버려진다."""
    f = R / "data" / "_meanings.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def main():
    MK = filled()
    mk_of = set()
    hits = collections.defaultdict(lambda: collections.defaultdict(list))  # key -> gi -> [pos]
    # 차례를 정하려면 **회차 번호와 그 회차 안의 자리**가 있어야 한다 (대표님 규칙, 2026-08-30)
    rounds = collections.defaultdict(dict)     # key -> gi -> (회차, 회차 안 자리)
    ko_of = collections.defaultdict(collections.Counter)
    en_of = collections.defaultdict(collections.Counter)
    form  = {}
    stat  = collections.Counter()
    for gi in GI:
        d = json.loads((R / "data" / f"_senior_scan-{gi}.json").read_text(encoding="utf-8"))
        P = positions([f for f in d["files"] if f["kind"] == "일일"])
        for f in d["files"]:
            pos = P.get(f["no"]) if f["kind"] == "일일" and ROUND.search(f["src"]) else None
            note = f["kind"] == "모음집"                  # 시험지가 아닌 모음집에서 온 낱말
            for row in f["rows"]:
                vi, ko, en = norm(row["vi"]), clean_ko(row.get("ko", "")), (row.get("en") or "").strip()
                if not ko and vi in MK: ko = MK[vi]          # 채워 둔 뜻을 쓴다
                if not is_word(vi, ko, en, row["vi"]): stat["문장·토막 뺌"] += 1; continue
                form.setdefault(vi, U.normalize("NFC", row["vi"]).strip())
                if pos is not None: hits[vi][gi].append(pos)
                else: hits[vi].setdefault(gi, [])
                if note: hits[vi].setdefault("_note", [])
                if f["kind"] == "일일" and ROUND.search(f["src"]):
                    cur = rounds[vi].get(gi)
                    cand = (f["no"], f["rows"].index(row) if row in f["rows"] else 0)
                    if cur is None or cand < cur: rounds[vi][gi] = cand
                if ko and KO.search(ko): ko_of[vi][ko] += 1
                if vi in MK: mk_of.add(vi)
                if en: en_of[vi][en] += 1
    out, nomean = [], []
    for k, gis in hits.items():
        firsts = {g: min(v) for g, v in gis.items() if v}
        pos = statistics.median(firsts.values()) if firsts else None
        ko = ko_of[k].most_common(1)[0][0] if ko_of[k] else ""
        en = en_of[k].most_common(1)[0][0] if en_of[k] else ""
        note = "_note" in gis
        gis = {g: v for g, v in gis.items() if g != "_note"}
        rec = {"vi": form[k], "key": k, "ko": ko, "gi": "".join(sorted(gis)),
               "n": len(gis), "pos": round(pos, 4) if pos is not None else None,
               **({"note": 1} if note and not gis else {}),
               **({"mk": 1} if k in mk_of else {}),
               # 기수별 (회차, 회차 안 자리) — 차례를 정하는 데 쓴다
               "rd": {g: list(v) for g, v in sorted(rounds[k].items())}}
        if en and not ko: rec["en"] = en
        if not ko: nomean.append(rec)
        out.append(rec)
    out.sort(key=lambda w: (w["pos"] is None, w["pos"] or 0, -w["n"]))
    (R / "data" / "senior_pool.json").write_text(json.dumps(
        {"note": "네 기수(17·18·19·20) 단어시험을 합친 것. pos = 배운 차례 0~1. gi = 나온 기수.",
         "words": out}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"낱말 {len(out)}개 (겹침 지운 뒤) · 뜻 없는 것 {len(nomean)}개 (영어뜻만 {sum(1 for r in nomean if r.get('en'))})")
    print("  뺀 것:", dict(stat))
    print("  기수 겹침:", dict(sorted(collections.Counter(w['n'] for w in out).items())))


if __name__ == "__main__":
    main()
