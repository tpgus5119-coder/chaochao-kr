#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""베트남어 → 한글 발음 표기. **북부·남부 두 벌**을 짓는다.

왜 만드나 (대표님 지시, 2026-08-29)
  지금 앱의 발음 표기(kr_read) 1,080개는 **내가 손으로 타이핑한 것**이다.
  사전에서 온 것도 아니고 검증도 안 됐고, **남부판은 아예 없다.**
  소리 파일은 북부·남부가 다 있는데 글자는 북부 것만 보여 주고 있었다.

무엇을 기준으로 하나
  뼈대는 **국립국어원 외래어 표기법**(문화관광부 고시 2004-11호)을 따른다 —
  음절 쪼개기·받침·꽈/응우옌 같은 규칙이 거기 정해져 있고, 예시가 있어 검산이 된다.
  다만 **소리가 어긋나는 자리는 소리를 따른다** (대표님: 최대한 소리나는 대로):
    · r  표기법은 ㄹ. 그런데 북부는 /z/ 다 → 북 ㅈ · 남 ㄹ
    · d, gi  둘 다 표기법은 ㅈ. 북부 /z/ → ㅈ, **남부 /j/ → 야·여** 로 갈린다
    · v  표기법은 ㅂ. 북부 /v/ → ㅂ, **남부 /j/ → 야·여**
    · s  표기법은 ㅅ. 북부는 x와 같은 /s/ → ㅆ, 남부는 혀 마는 /ʂ/ → ㅅ
    · tr 표기법은 ㅉ. 북부는 ch와 같은 /tɕ/, 남부는 혀 마는 /ʈ/ — 한글로는 둘 다 ㅉ
  이 여섯 자리가 북부·남부가 갈리는 거의 전부다(앱 낱말에서 285음절).

검산: 표기법 문서에 실린 예시 낱말로 시험한다(맨 아래 TEST). 하나라도 어긋나면 멈춘다.
쓰기:  python3 tools/vi_kr.py            → 검산만
      python3 tools/vi_kr.py --diff     → 지금 표기와 어긋나는 것 목록
      python3 tools/vi_kr.py --write    → days.json 에 kr_read(북)·kr_south(남) 기록
"""
import argparse, json, pathlib, re, sys, unicodedata

R = pathlib.Path(__file__).resolve().parent.parent

# ── 첫소리 (긴 것부터 봐야 ng 가 n 으로 잘리지 않는다)
ONSET_N = [("ngh","응"),("ng","응"),("nh","니"),("gh","ㄱ"),("gi","ㅈ"),("kh","ㅋ"),("ph","ㅍ"),
           ("th","ㅌ"),("tr","ㅉ"),("ch","ㅉ"),("qu","꾸"),("b","ㅂ"),("c","ㄲ"),("d","ㅈ"),
           ("đ","ㄷ"),("g","ㄱ"),("h","ㅎ"),("k","ㄲ"),("l","ㄹ"),("m","ㅁ"),("n","ㄴ"),
           ("p","ㅃ"),("q","ㄲ"),("r","ㅈ"),("s","ㅆ"),("t","ㄸ"),("v","ㅂ"),("x","ㅆ")]
# 남부에서 달라지는 것만 덮어쓴다
ONSET_S = {"r": "ㄹ", "s": "ㅅ", "d": "y", "gi": "y"}   # y = 반모음 /j/ (야·여로 붙는다)
# v 는 뺐다 — 사전(위키낱말)에서 남부 94개가 **모두 [v]** 였다. 야·여로 적던 것은 내 짐작이었다.
#   d(97개 모두 [j]) · gi(65개 [j]) · r(48개 [ɹ]) · s(106개 [ʂ]) 는 사전과 맞아 그대로 둔다. (2026-08-30)

# ── 가운뎃소리
NUC = {"iê":"이에","yê":"이에","ia":"이어","ya":"이어","ưa":"으어","ươ":"으어","ua":"우어","uô":"우오",
       "oo":"오","ôô":"오","a":"아","ă":"아","â":"어","e":"애","ê":"에","i":"이","y":"이",
       "o":"오","ô":"오","ơ":"어","u":"우","ư":"으"}
# ── 끝소리
COD_N = {"ch":"ㄱ","nh":"ㄴ","ng":"ㅇ","c":"ㄱ","m":"ㅁ","n":"ㄴ","p":"ㅂ","t":"ㅅ","i":"이","y":"이","o":"오","u":"우"}
# 남부 받침. 사전 발음기호 3,040개를 앞모음별로 세어 규칙을 뽑았다 (2026-08-30).
#   -n  : i 뒤 17/17 · ê 뒤 24/24 가 [n] 그대로 · 그 밖 375곳은 모두 [ŋ]
#   -t  : i 뒤 3/3 · ê 뒤 12/12 가 [t] 그대로 · 그 밖 144곳은 모두 [k]
#   -ch : 앞모음과 상관없이 53/53 이 [t]
#   **어긋나는 보기가 하나도 없다** — 짐작이 아니라 사전이 그렇다.
COD_S = dict(COD_N, n="ㅇ", t="ㄱ", ch="ㅅ")
KEEP_S = {"i", "ê", "y"}     # 이 모음 뒤에서는 남부도 북부와 같다 (y 는 i 와 같은 소리)
# 남은 어긋남은 사전 쪽 quét 하나뿐이다(같은 꼴 표본이 1건). 규칙을 따른다.

TONE = "\u0300\u0301\u0303\u0309\u0323"        # 성조 부호 다섯만 (모자 ˆ ˘ ̛ 는 글자의 일부다)
nfc = lambda s: unicodedata.normalize("NFC", s)
def strip_tone(s):
    """성조만 뗀다. **모자는 남긴다** — ă â ê ô ơ ư 는 다른 글자다.
       전에 여기서 모자까지 날려서 lâu 가 '라우', cưa 가 '꽈'로 나왔다."""
    return nfc("".join(c for c in unicodedata.normalize("NFD", s) if c not in TONE))

# 끝소리가 **모음**이면 받침이 아니라 뒤에 붙는 글자다 (bao 바오 · gai 가이 · lâu 러우)
VCOD = {"i": "이", "y": "이", "o": "오", "u": "우"}
VOW = {"아":"ㅏ","애":"ㅐ","에":"ㅔ","어":"ㅓ","오":"ㅗ","우":"ㅜ","으":"ㅡ","이":"ㅣ",
       "야":"ㅑ","여":"ㅕ","요":"ㅛ","유":"ㅠ","얘":"ㅒ","예":"ㅖ",
       "와":"ㅘ","왜":"ㅙ","위":"ㅟ","웨":"ㅞ","워":"ㅝ"}

def jamo(cho, jung, jong=""):
    CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
    JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
    JONG = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
    i, j = CHO.find(cho or "ㅇ"), JUNG.find(jung)
    k = JONG.find(jong) if jong else 0
    if i < 0 or j < 0 or k < 0: return None
    return chr(0xAC00 + (i * 21 + j) * 28 + k)

# 첫소리가 붙으면 가운뎃소리가 바뀌는 것들
YOD = {"아":"야","어":"여","오":"요","우":"유","애":"얘","에":"예","이":"이","으":"으"}
# qu + 모음. 표기법 제2항: **"qu 는 이어지는 모음이 a 일 경우에만 합쳐서 '꽈'로 적는다."**
#   (문화관광부 고시 2004-11 『동남아시아 3개 언어 외래어 표기법』)
#   그래서 a 만 합친다 — Quang→꽝. 그 밖에는 '꾸'+모음이다: Quốc→꾸옥 · Quy→꾸이.
#   전에는 오·이·어까지 합쳐 Quốc 이 '꼭', Quy Nhơn 이 '뀌년'으로 나왔다 (2026-08-30 검수)
WOD = {"아": "와"}

# 미끄럼소리(glide)로 볼 짝만 딱 정한다.
#   ua·uô·ưa·ươ·ui·oi 는 **겹모음**이지 미끄럼소리가 아니다.
#   전에 이걸 안 갈라 của 가 '꽈', vui 가 '뷔', nói 가 '뉘' 로 나왔다.
GLIDE = ("oa", "oă", "oe", "uâ", "uê", "uy", "uơ")

def one(syl, south=False):
    """음절 하나 → 한글."""
    s = strip_tone(nfc(syl).lower())
    s = "".join(c for c in s if c in "abcdeghiklmnopqrstuvxyăâđêôơư")
    if not s: return ""
    cho, rest, cho_src = "", s, ""
    for a, b in ONSET_N:
        if s.startswith(a):
            if south and a in ONSET_S: b = ONSET_S[a]
            cho, rest, cho_src = b, s[len(a):], a
            break
    # gì·gia 처럼 gi 가 첫소리를 다 먹어 남는 게 없으면 i 를 가운뎃소리로 돌려준다.
    # **받침만 남는 gìn·gin 도 같다** — 남은 것이 모음으로 시작하지 않으면 i 가 가운뎃소리다.
    #   2026-08-31: 이것이 빠져 있어 'giữ gìn' 이 '즈' 한 덩이로 깨져 있었다
    #   (사전 발음 zin˨˩ → 진). kr_verify 가 'ㄴ≠없음' 으로 잡아냈다.
    #   **gi 일 때만이다** — r·d 도 북부에서 ㅈ 소리라 함께 걸리면
    #   carton('까 지')·Purchase('뿌 지') 처럼 없는 소리가 생긴다 (2026-08-31 실측).
    if cho_src == "gi" and (not rest or rest[0] not in "aeiouăâêôơưy"):
        rest = "i" + rest
    glide = ""
    if cho != "꾸" and rest[:2] in GLIDE:
        glide, rest = rest[0], rest[1:]      # 'o' 인지 'u' 인지 그대로 남긴다 — 소리가 다르다
    nuc, nuc_raw = "", ""
    for k in sorted(NUC, key=len, reverse=True):
        if rest.startswith(k): nuc, nuc_raw, rest = NUC[k], k, rest[len(k):]; break
    if not nuc: return ""
    tail, cod = "", ""
    if rest in VCOD: tail = VCOD[rest]
    elif rest:
        for k in sorted(COD_N, key=len, reverse=True):
            if rest == k:
                use_s = south and not (k in ("n", "t") and nuc_raw in KEEP_S)
                cod = (COD_S if use_s else COD_N)[k]; break
    # 표기법 1항 — 어말 nh 앞 모음이 a 면 a 와 합쳐 '아인'
    if rest == "nh" and nuc == "아": nuc, cod = "아이", "ㄴ"
    return build(cho, glide, nuc, cod) + tail

def build(cho, glide, nuc, cod):
    pre = ""
    if cho == "응": pre, cho = "응", ""
    elif cho == "니": cho, nuc = "ㄴ", YOD.get(nuc, nuc)
    elif cho == "꾸": cho, nuc = "ㄲ", WOD.get(nuc, "우" + nuc)   # qu 만 합친다 (꽈·꽝)
    elif cho == "y":  cho, nuc = "ㅇ", YOD.get(nuc, nuc)
    if glide:
        # 미끄럼소리는 **따로 한 글자**로 — 표기법의 Nguyên 응우옌 · Hòa Bình 호아빈 이 그 꼴이다.
        # **글자가 o 면 '오', u 면 '우'** 다. 늘 '우'로 적으면 hoa 가 '후아'가 된다(2026-08-30).
        gv = "ㅗ" if glide == "o" else "ㅜ"
        pre = pre + (jamo(cho or "ㅇ", gv) or ("오" if glide == "o" else "우")); cho = ""
        # 표기법 3항 — 미끄럼소리 뒤의 이에는 **한 음절로 합친다**: 우 + 이에 + n → 우 + 옌
        if nuc == "이에": nuc = "예"
        elif nuc == "이어": nuc = "여"
    if len(nuc) > 1:
        v0 = VOW.get(nuc[0]); v1 = VOW.get(nuc[-1])
        first = jamo(cho or "ㅇ", v0) if v0 else nuc[0]
        last = jamo("ㅇ", v1, cod) if v1 else nuc[-1]
        return pre + (first or nuc[0]) + nuc[1:-1] + (last or nuc[-1])
    v = VOW.get(nuc)
    return pre + (jamo(cho or "ㅇ", v, cod) if v else nuc)

# 베트남어 규칙으로 읽히지 않는 **빌려 온 말**. 손으로 적는다 (2026-08-30 검수).
FOREIGN = {
 "complê": "꼼 쁠레", "tennis": "때 니", "nobel": "노 벤", "inox": "이 녹",
 "violon": "비 오 롱", "web": "웹", "bar": "바", "sofa": "쏘 파", "taxi": "딱 씨",
 "wifi": "와 이 파이", "logo": "로 고", "menu": "메 뉴", "video": "비 데 오",
 "email": "이 메일", "internet": "인 떠 넷", "container": "꼰 떼 너", "pallet": "빠 렛",
 "sample": "쌈 쁠", "size": "싸이", "vitamin": "비 따 민", "gam": "감",
 # 공장에서 쓰는 **약어** — 베트남 사람도 글자 그대로 읽는다 (2026-08-30 검수)
 "pgm": "피 지 엠", "shortage": "쇼 티 지", "ng": "엔 지",
 "qlsx": "꾸이 에러 엣 익",          # Quản Lý Sản Xuất 의 머리글자
 "smt": "에스 엠 티", "aoi": "에이 오 아이", "pcb": "피 씨 비", "qc": "큐 씨",
 "iso": "아이 에스 오", "led": "엘 이 디", "usb": "유 에스 비",
}

def syllables(t, _d=0):
    """붙어 있는 음절을 쪼갠다 — kilôgam · Campuchia · violon.
       베트남어는 음절마다 띄어 쓰지만 외래어는 붙여 적는다.
       옛 one() 은 못 읽은 글자를 **말없이 버렸다**: kilôgam 이 '끼' 하나로 줄었다 (2026-08-30).
       왼쪽부터 「초성+모음+받침」 을 최대한 떼되, 받침은 **다음 음절이 모음으로 시작하지 않을 때만** 붙인다."""
    s = strip_tone(nfc(t).lower())
    s = "".join(c for c in s if c in "abcdeghiklmnopqrstuvxyăâđêôơư")
    if not s or _d > 8: return [t]
    i = 0
    for a, _ in ONSET_N:
        if s.startswith(a): i = len(a); break
    if i >= len(s): return [t]
    if s[i:i + 2] in GLIDE: i += 1
    for k in sorted(NUC, key=len, reverse=True):
        if s[i:].startswith(k): i += len(k); break
    else: return [t]
    rest = s[i:]
    if not rest or rest in VCOD or rest in COD_N: return [t]
    # 받침 후보를 떼어 본다 — 뒤에 모음이 이어지면 그 자음은 다음 음절의 첫소리다
    for k in sorted(COD_N, key=len, reverse=True):
        # 뒤가 h 면 그 자음은 받침이 아니라 다음 음절의 ch·kh·nh·ph·th 다 (Campuchia)
        if rest.startswith(k) and len(rest) > len(k) and rest[len(k)] not in "aeiouyăâêôơưh":
            i += len(k); break
    head, tail = nfc(t)[:i], nfc(t)[i:]
    return [head] + syllables(tail, _d + 1) if tail else [head]

def word(vi, south=False):
    # 붙임표(ki-lô · mi-li-mét)도 음절 사이 구분이다
    out = []
    for t in re.split(r"[\s\-]+", nfc(vi)):
        if not t: continue
        f = FOREIGN.get(t.lower().strip(".,()"))
        if f: out.append(f); continue
        out += [one(x, south) for x in syllables(t)]
    return " ".join(x for x in out if x)

TEST = [("Bao","바오"),("cao","까오"),("cha","짜"),("bach","박"),("đan","단"),("Đinh","딘"),
        ("gai","가이"),("ghe","개"),("hai","하이"),("Khai","카이"),("lâu","러우"),("long","롱"),
        ("minh","민"),("tôm","똠"),("Nam","남"),("bun","분"),("ngo","응오"),("đông","동"),
        ("nhât","녓"),("put","뿟"),("chap","짭"),("Pham","팜"),("tam","땀"),("hat","핫"),
        ("thao","타오"),("Trân","쩐"),("vai","바이"),("Quang","꽝"),("kia","끼어"),("chiêng","찌엥"),
        ("buôn","부온"),("cưa","끄어"),("anh","아인"),("xanh","싸인"),("Nguyên","응우옌"),
        ("của","꾸어"),("vui","부이"),("nói","노이"),("tuân","뚜언"),("ki-lô","끼 로"),
        # 미끄럼소리 o/u 를 가려 적는지 (2026-08-30에 여기서 hoa 가 '후아'로 나왔다)
        ("hoa","호아"),("hoang","호앙"),("toan","또안"),("khoe","코애"),("xoay","쏘아이")]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--diff", action="store_true")
    ap.add_argument("--write", action="store_true"); a = ap.parse_args()
    bad = [(v, k, word(v)) for v, k in TEST if word(v) != k]
    print(f"검산 {len(TEST)}개 중 어긋남 {len(bad)}개")
    for v, want, got in bad: print(f"   {v:<10} 있어야 {want:<8} 나온 것 {got}")
    if bad and not a.diff: return
    P = R / "data" / "days.json"
    d = json.loads(P.read_text(encoding="utf-8"))
    ws = [w for x in d["days"] for w in x.get("words", [])]
    if a.diff:
        n = 0
        for w in ws:
            got = word(w["vi"])
            if got and got.replace(" ", "") != (w.get("kr_read") or "").replace(" ", ""):
                n += 1
                if n <= 40: print(f"   {w['vi']:<16} 지금 {w.get('kr_read',''):<14} → {got:<14} 남부 {word(w['vi'], True)}")
        print(f"\n어긋나는 낱말 {n} / {len(ws)}")
    if a.write:
        for w in ws:
            n_, s_ = word(w["vi"]), word(w["vi"], True)
            if n_: w["kr_read"] = n_
            if s_ and s_ != n_: w["kr_south"] = s_
            elif "kr_south" in w: del w["kr_south"]
        P.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print("days.json 에 적음")

if __name__ == "__main__":
    main()

# 아직 못 고친 것 (2026-08-30) — **지어내지 않고 남겨 둔다**
#  · s 를 ㅆ 로 적고 있다. 국립국어원 표기법은 s→ㅅ, x→ㅆ 다.
#    다만 북부에서는 s 와 x 가 같은 소리(/s/)라 지금 것이 소리에는 더 가깝다.
#    표기법을 따를지 소리를 따를지는 **사전 대조(위키낱말사전 IPA)** 를 끝낸 뒤 정한다.
#  · qu + 오/우 를 한 음절로 붙인다(Quốc → 꼭). 'Quang → 꽝'은 맞는데 이쪽은 '꾸옥'이 맞아 보인다.
#    공식 예시에 이 꼴이 없어 확인 전까지 손대지 않는다.
