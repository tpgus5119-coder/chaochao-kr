#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""대표님이 주신 **봉제용어.xls** 를 읽는다 → data/_sewing.json

이 파일을 그동안 못 읽고 있었다 (2026-08-30, 대표님 지적).
`.xls` 는 구형 판이라 openpyxl 이 못 연다 — xlrd 로 읽어야 한다.
그래서 봉제 낱말이 34개밖에 없었다. 실제로는 570줄이 들어 있다.

시트 셋
  · 봉제용어        영어 | 한국어 | **Vietnam** | 일본어 | 설명   → 봉제 낱말
  · 무역용어        약자 | Full | 한국어 | 설명                  → 거래 낱말(약어)
  · 봉제 및 검사 교육  한·베 문장 짝                              → 문장이라 낱말로는 안 쓴다
쓰기: python3 tools/sewing_words.py
"""
import json, os, pathlib, re, sys, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr

SRC = pathlib.Path(os.path.expanduser("~/Downloads/베트남어 학습자료/선배 자료/봉제용어.xls"))
KO = re.compile(r"[가-힣]")
VI = re.compile(r"[ăâđêôơưÀ-ỹ]", re.I)

# 낱말 432개를 **하나씩 눈으로 읽고** 고친 것 (2026-08-30, 대표님 지시).
# 인터넷으로 확인한 것만 고쳤다 — 확인 못 한 것은 손대지 않고 그대로 둔다.
TYPO = {"sửa chửa": "sửa chữa", "áo khoát": "áo khoác", "dđịnh mức": "định mức",
        "lot": "lót", "manocanh": "ma-nơ-canh", "manocanh to": "ma-nơ-canh to",
        "bà là": "bàn là",                 # 다리미 (북부 bàn là · 남부 bàn ủi)
        "giử điểm cố định": "giữ điểm cố định",
        "daây viền": "dây viền",
        "tay raglăng": "tay raglan",
        "diểu thành phẩm": "diễu thành phẩm",
        "vòng chử D": "vòng chữ D",
        "lệch, vếch lên, lé ra": "lệch, vênh lên, lé ra",
        "da": "da lộn",                    # 세무가죽은 da lộn 이다 (da 는 그냥 가죽)
        }

# 일본어에서 온 현장 은어를 **한국어로** 바꾼다 (대표님 지시, 2026-08-30).
#   시다·가이루빠·고땃찌는 공장에서 실제로 쓰지만 배우는 사람에겐 또 하나의 외국어다.
#   원래 말은 괄호로 남긴다 — 현장에서 그 말을 들을 때 알아들어야 하기 때문이다.
JPKO = {
 "오바록": "휘감아 박기(오버록)",
 "니혼오바(니트오바)": "네 실 휘감아 박기",
 "가이루빠": "덮어 박는 기계(커버스티치)",
 "인타록": "다섯 실 휘감아 박기",
 "보조공원/시다": "보조 작업자",
 "보조대/시다다이": "보조 작업대",
 "빗장 박기, 바택": "빗장 박기",
 "속감침 /세발뜨기/스쿠이": "속감침(밑단 감침질)",
 "봉탈": "실 끊김",
 "환봉(루빠 박음질)": "사슬 박음질",
 "쵸크, 자고": "재단용 분필",
 "몸새,다트": "다트(입체 주름)",
 "칫수안정성": "치수 안정성",
 "줄임, 울림,여유분/이세": "여유분 넣기",
 "칼본봉": "칼 달린 본봉(실밥 자동 절단)",
 "칼 본봉": "칼 달린 본봉(실밥 자동 절단)",
 "표면 맞대기 연단 방법": "겉면끼리 마주 대고 펴기",
 "표면위 위로 오게 연단 방법": "겉면이 위로 오게 펴기",
 "몸새 맞춤": "옷 맵시 맞춤",
 "잔주름, 게더링,샤링": "잔주름 잡기",
 "옷을 넉넉하게 하거나 후레아 지게 대는 삼각천": "넉넉하게 대는 삼각 천",
 "옷 낫장에 포리백 포장을 하는것": "한 장씩 비닐에 넣어 포장",
 "속옷감이 무릎까지 오는 우라": "무릎까지 오는 안감",
 "옷본 배치도/마카": "옷본 배치도",
 "형입,옷본 끼워 그리기": "옷본 대고 그리기",
 "칫수재기": "치수 재기",
 "다본침, 닥고미싱": "여러 바늘 박기",
 "덧댐": "덧대어 박기",
 "봉제울음(파카링)": "박음선 우는 현상",
 "이세나 퍼커링을 지칭 하는 말": "여유분·우는 현상",
 "리쁘/고무뜨기단": "고무뜨기 단(시보리)",
 "밑윗길이/시리": "밑위 길이",
 "번들거림/히까리": "다림질 번들거림",
 "작은주름/샤링": "잔주름",
 "일반적인 본봉": "보통 본봉(외줄 박음)",
 "소매트임(타개)": "소매 트임",
 "직단": "실 뽑힘 불량",
 "나름질/연단": "원단 펴기(연단)",
 "스댕칼라": "선 칼라",
 "짝짝이,찐빠": "짝이 안 맞음",
 "시다마이 플라켓": "지퍼 밑 덧단",
 "뒷트기(타개,트임)": "뒤 트임",
}

# 뜻이 안 맞던 것 — 베트남어는 맞는데 한국어 뜻이 엉뚱했다.
FIXKO = {"móc áo": "옷걸이", "nhuộm": "염색하다", "khóa": "지퍼·잠금장치",
         "đội kế hoạch": "생산계획팀", "tay bị vặn": "소매가 뒤틀림",
         "may": "박다·재봉하다", "dài áo": "옷 길이",
         "lỗi loang nước": "물얼룩 불량", "sự nhuộm": "염색"}

# 쓸 수 없는 것 — 원본이 잘못됐거나 봉제 낱말이 아니다
DROP = {"baghết chiếc",          # 베트남어가 아니다 (baguette 를 잘못 적은 듯)
        "theo suốt", "theo đuổi",  # '따라하기' 가 아니다 (추구하다)
        "kiểm tra rập", "kiểm tra sọc",   # 영어 check 를 '검사'로 잘못 옮겼다(체크무늬가 맞다)
        "ngực",                  # '여밈선'이 아니다. 가슴은 이미 따로 있다
        "vô lý, tồi tệ", "vững vàng , chắc chắn", "rõ ràng, chính xác",
        "kéo, giật", "nghiêng , xéo", "cắt đứt ra", "kiểm tra, kiểm định",
        "tạo đường song song", "bất biến (không thay đổi)",   # 봉제 낱말이 아니라 사전 뜻풀이다
        }

# 봉제어가 아니라 **어느 공장에서나 쓰는 말** — 지우지 않고 '공통'으로 보낸다
# (대표님 지시, 2026-08-30: "봉제어가 아닌것은 공통으로 빼라")
TO_COMMON = {
 "Thừa nhận, tán thành", "hợp thành, dung hợp, giảm bớt", "kết hợp, phối hợp",
 "chi tiết, tỉ mỉ", "ngăn nấp, rõ ràng", "hạng mục, chủng loại", "mua / bán lẻ",
 "mang tính tạm thời", "chiều cao (của vật)", "chất lượng, tay nghề, tài năng",
 "Tẩy, nhặt, làm sạch", "sửa đổi, điều chỉnh", "lệch, vênh lên, lé ra",
 "ánh ra, nhìn thấy", "đối xứng mang tính trực quan", "duyệt, xác nhận",
 "tuân thủ", "thiệt hại", "cảnh cáo", "tiền phạt", "sự tạo hình", "chèn",
 "giặt", "nhiệt độ", "màu sắc", "chiều dài", "vị trí", "mẫu", "lỗi", "đặt",
}


def sents():
    """「봉제 및 검사 교육」 시트의 한·베 문장 짝 — 낱말의 예문으로 쓴다."""
    import xlrd
    wb = xlrd.open_workbook(SRC)
    sh = wb.sheet_by_name("봉제 및 검사 교육")
    rows = [str(sh.cell_value(i, 0)).strip() for i in range(sh.nrows)]
    rows = [r for r in rows if r]
    out = []
    for a, b in zip(rows, rows[1:]):
        if KO.search(a) and not KO.search(b) and VI.search(b) and 3 <= len(b.split()) <= 24:
            out.append({"vi": b.strip(), "ko": a.strip()})
    return out


def basic(vi, ko, seen):
    """**첫날 쓰는 말**인가, 도면에 적힌 말인가 (대표님 물음, 2026-08-30).
       잣대 두 가지 — 지어내지 않고 자료로 판단한다.
         ① 선배 시험·일터 단톡방·앱 어디에도 나오면 = 입으로 말하는 말이다.
         ② 낱말이 두 마디 이하이고 뜻이 짧으면 = 기본이다.
       나머지(도면·검사표에만 있는 말)는 '찾아보기'로 뺀다."""
    from re import search
    if vi.lower() in seen: return True
    if len(vi.split()) <= 2 and len(ko) <= 8 and not search(r"[(/,]", ko): return True
    return False


def main():
    import xlrd
    wb = xlrd.open_workbook(SRC)
    out, seen, stat = [], set(), {}
    sh = wb.sheet_by_name("봉제용어")
    n = 0
    for i in range(sh.nrows):
        c = [str(sh.cell_value(i, j)).strip() for j in range(sh.ncols)]
        ko, vi = c[1] if len(c) > 1 else "", c[2] if len(c) > 2 else ""
        if not (ko and vi) or not KO.search(ko): continue
        if ko in ("한국어",) or vi in ("Vietnam",): continue
        vi = re.sub(r"\s+", " ", U.normalize("NFC", vi)).strip()
        if vi in DROP: continue
        vi = TYPO.get(vi, TYPO.get(vi.lower(), vi))
        if vi in FIXKO: ko = FIXKO[vi]
        ko = JPKO.get(ko.strip(), ko)
        if ko not in JPKO.values():                 # 띄어쓰기가 조금 달라도 잡는다
            for a, b in JPKO.items():
                if a.replace(" ", "") == ko.replace(" ", ""): ko = b; break
        if len(vi.split()) > 6 or len(vi) > 40: continue
        if not re.search(r"[A-Za-zÀ-ỹ]", vi): continue
        k = vi.lower()
        if k in seen: continue
        seen.add(k)
        out.append({"vi": vi, "ko": re.sub(r"\s+", " ", ko)[:26],
                    "kr": vi_kr.word(vi), "krs": vi_kr.word(vi, True),
                    "track": None if vi in TO_COMMON else "섬유·봉제·신발", "sew": 1})
        n += 1
    stat["봉제용어"] = n
    # 무역용어 — 약자는 낱말이 아니라 '한국어 뜻'만 쓸모가 있는데 베트남어가 없다. 안 쓴다.
    # 다른 자료에도 나오는 낱말 모으기
    import unicodedata as UU
    def kk(v):
        t = UU.normalize("NFC", str(v)).strip().lower()
        t = re.sub(r"\([^)]*\)", "", t)
        return re.sub(r"\s+", " ", t).strip(" .,;:!?~–—/\"'")
    seen = set()
    for f in ("senior_pool.json", "_kakao_job.json"):
        q = R / "data" / f
        if q.exists():
            j = json.loads(q.read_text(encoding="utf-8"))
            for w in j["words"]: seen.add(kk(w["vi"]))
    dj = R / "data" / "days.json"
    if dj.exists():
        d = json.loads(dj.read_text(encoding="utf-8"))
        for day in (d if isinstance(d, list) else d["days"]):
            for w in (day.get("words") or []): seen.add(kk(w.get("vi", "")))
    nb = 0
    for w in out:
        if w["track"] is None: continue
        if basic(w["vi"], w["ko"], seen): w["track"] = "섬유·봉제·신발"; nb += 1
        else: w["track"] = "봉제 찾아보기"          # 999 밖 — 공장 가면 그때 여는 사전

    ss = sents()
    # 문장에 그 낱말이 들어 있으면 **그 문장을 예문으로** 준다 (대표님 지시)
    n_ex = 0
    for w in out:
        t = w["vi"].lower()
        hit = next((x for x in ss if t in x["vi"].lower()), None)
        if hit:
            w["ex"] = {"vi": hit["vi"], "ko": hit["ko"],
                       "kr": vi_kr.word(hit["vi"]), "krs": vi_kr.word(hit["vi"], True)}
            n_ex += 1
    (R / "data" / "_sewing.json").write_text(json.dumps(
        {"note": "대표님이 주신 봉제용어.xls 의 봉제 낱말. xls 는 xlrd 로 읽는다.",
         "words": out, "sents": ss}, ensure_ascii=False, indent=1), encoding="utf-8")
    import collections as C
    print(f"봉제 낱말 {len(out)}개 · 교육 시트 문장 {len(ss)}개 · 그중 예문으로 붙은 것 {n_ex}개")
    print("  갈래:", dict(C.Counter(w["track"] or "공통" for w in out)))
    print("  ", dict(stat))
    for w in out[:12]: print(f"   {w['vi']:<26} {w['ko']}")
main()
