#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""기계로 못 가른 116개를 **손으로** 마무리한다 → senior_pool.json 을 고쳐 쓴다.

왜 손인가 (2026-08-30): 시험지 칸이 어긋나 '뜻' 자리에 베트남어가 들어온 것이
남았다(who=ai 처럼 앞뒤가 뒤집힌 것도 있다). 규칙을 더 얹으면 멀쩡한 낱말까지
같이 떨어진다. 116개면 눈으로 다 읽을 수 있는 양이다 — 그래서 읽고 적었다.
쓰기: python3 tools/senior_hand.py
"""
import collections, json, pathlib, re, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent

# 낱말 → 한글 뜻 (살릴 것)
# 손으로 바로잡는 표 — 대소문자·붙여쓰기가 자료마다 어긋난 것 (2026-08-30 검수)
SPELL = {
 "Balan": "Ba Lan", "Căm Pu Chia": "Campuchia", "quần Jin": "quần jin",
 "mùa Hạ": "mùa hạ", "chủ Nhật": "chủ nhật", "tháng Chạp": "tháng chạp",
 "tháng Giêng": "tháng giêng", "hướng Nam": "hướng nam", "viễn Đông": "viễn đông",
 "hồng Kông": "Hồng Kông", "tây Nguyên": "Tây Nguyên", "Việ T": "Việt",
 "ngày Nhà giáo": "ngày Nhà giáo Việt Nam", "bệnh viện Đông y": "bệnh viện đông y",
 "hội Lim": "hội Lim", "giải Nobel": "giải Nobel",
}

# 뜻이 깨져 들어온 것을 손으로 바로잡는다 — 다른 줄의 글자가 섞여 들어왔다 (2026-08-30 검수)
# AI 가 미룬 교정을 손으로 판정했다 (2026-08-30). 빈 값이면 원래대로 둔다.
SPELL2 = {
 "cây gia hệ": "cây phả hệ", "máy di động": "điện thoại di động",
 "thấy thấy": "thấy", "bVđa khoa": "bệnh viện đa khoa",
 "bVchuyên khoa": "bệnh viện chuyên khoa", "bVĐông y": "bệnh viện Đông y",
 "đến nhau": "đến gần nhau",
 "rộng rãi": "rộng rãi",          # 원래가 맞다 — 씀씀이가 큰 이라는 뜻으로도 쓴다
 "trụ sở": "trụ sở",              # 낱말은 맞다. 틀린 것은 뜻이다 (아래 FIXKO)
}

FIXKO = {
 "trụ sở": "본사, 사무소",         # '주소'로 적혀 있었다 — địa chỉ 와 헷갈린 것
 "tự giới thiệu": "자기소개",      # '아이디어'로 적혀 있었다
 "họa sĩ": "화가",                # '도장공'으로 적혀 있었다 — 도장공은 thợ sơn
 "tiếng Nhật": "일본어",          # '예습 / 일본어'

 "mũi": "코", "tiếng": "시간, 언어", "rồi": "이미, 벌써 (~했다)",
 "chưa": "아직 ~않다 / ~했습니까?", "giàu": "넉넉한, 부자인",
 "càng": "~할수록 더", "tuy": "비록 ~일지라도",
 "mở trang": "(책의 ~쪽을) 펴다", "làm ăn": "사업을 하다, 생계를 꾸리다",
}

KEEP = {
 "khoẻ":"건강하다", "mọi người":"모두, 사람들", "củ hành tây":"양파", "hiền":"착하다",
 "sẽ":"~할 것이다", "Tường":"벽", "tennis":"테니스장", "núi":"산", "tối qua":"어젯밤",
 "hải":"바다", "chơi":"놀다", "làm việc":"일하다", "viết":"쓰다", "chiều nay":"오늘 오후",
 "rút":"뽑다, 인출하다", "cắt":"자르다", "nước ép":"주스", "thuốc lá":"담배",
 "ký túc xá":"기숙사", "cuối":"마지막", "bến xe (buýt)":"버스 정류장",
 "(Viện) bảo tàng":"박물관", "Có tiếng":"유명하다", "(màu) xanh lá cây":"초록색",
 "(màu) xanh da trời":"파란색", "(màu) da trời":"하늘색", "thành viên":"구성원",
 "cầu tre":"대나무 다리", "đối diện(với)":"맞은편", "tàu thuỷ":"배, 선박",
 "ở kia":"저기", "thay đổi":"바꾸다", "liên hoan":"모임, 회식",
 "Thứ hai":"월요일", "Thứ ba":"화요일", "Thứ tư":"수요일", "Thứ năm":"목요일",
 "Thứ bảy":"토요일", "Thư viện Quốc gia":"국립도서관", "hẹn hò":"데이트하다",
 "kết thúc / xong":"끝나다", "đói bụng":"배고프다", "Tây":"서쪽", "Bắc":"북쪽",
 "Trải":"펴다, 깔다", "dùng được":"쓸 수 있다", "size nhỏ":"작은 치수",
 "size vừa":"보통 치수", "size lớn":"큰 치수", "phía":"쪽, 방향",
 "nói rõ":"분명히 말하다", "chương trình học":"교육 과정", "quán nhậu":"술집",
 "sống":"살다", "dong dỏng/cao gầy":"호리호리하다", "gà mái":"암탉",
 "Tư lạng":"냉장고", "aó sơ":"와이셔츠", "mời / xin":"청하다, 권하다",
 "Hè này":"올여름", "Năm sau":"내년", "good / well/ or":"좋다 / 잘 / 또는",
 "A Lô ạ":"여보세요", "nâng cốc":"건배하다", "đạo":"따르다, 종교",
 "ấn":"누르다", "dê":"염소", "bàn":"책상, 탁자",
}
# 베트남어가 아닌 글자와 끝소리 — **모양으로** 가른다.
#   f·j·w·z 는 베트남어에 없다. 끝소리는 c·ch·m·n·ng·nh·p·t 와 모음뿐이다.
#   이 잣대여야 nghe·mua·cao·xem 같은 **성조 부호 없는 진짜 베트남어**를 안 버린다.
#   (한때 '알파벳만 있으면 영어'로 쳐서 295개를 통째로 버릴 뻔했다.)
NOTVI = re.compile(r"[fjwzFJWZ]")
CODA_OK = re.compile(r"(?:[aeiouyàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]"
                     r"|ch|ng|nh|[cmnpt])$", re.I)

# 베트남어가 빌려 쓰는 말 — 모양은 베트남어가 아니지만 진짜 쓰는 낱말이다
LOAN = {"web", "inox", "email", "video", "internet", "wifi", "taxi", "logo", "menu",
        "shop", "sales", "marketing", "container", "pallet", "sample", "size"}

# 베트남어 음절은 「초성 + 모음 + 종성 하나」다. 모음 뒤에 자음이 둘 넘게 오지 않는다
#   (오는 것은 ch·ng·nh 뿐). 같은 모음이 두 번 잇달지도 않는다.
#   인도네시아반 시험지가 섞여 들어와 konsumsi·ungkapkan 이 남아 있었다 (2026-08-30).
BAD_SYL = re.compile(r"[aeiouy](?!ch$|ng|nh)[^aeiouy]{2,}|([aeiou])\1")

def bad_syllable(t):
    """베트남어 **한 덩어리는 한 음절**이다 — 음절마다 띄어 쓰기 때문이다.
       그래서 모음 무리가 둘이면 베트남어가 아니다: atap(a·ta·p) · damai · seragam.
       인도네시아반 시험지가 섞여 들어온 것을 이 잣대로 가려낸다 (2026-08-30)."""
    b = "".join(c for c in U.normalize("NFD", t.lower()) if not U.combining(c)).replace("đ", "d")
    if len(b) > 7 or BAD_SYL.search(b): return True
    return len(re.findall(r"[aeiouy]+", b)) > 1


def not_viet(v):
    for tok in v.split():
        if tok.lower().strip(".,;:!?()") in LOAN: continue
        t = tok.strip(".,;:!?()'\"")
        if not t: continue
        if NOTVI.search(t): return True
        if not CODA_OK.search(t): return True
        if bad_syllable(t): return True
    return False

def junk(vi, ko):
    """칸이 어긋나 붙어 버린 것·오타·영어 찌꺼기를 가려낸다 (2026-08-30).
       기계로 예문을 만들어 보니 **문장이 안 만들어지는 것들**이 있었다.
       들여다보니 낱말이 아니었다 — 'viện nhóm ô'(기관/무리/우산)처럼 세 낱말이 붙은 것,
       '(I'm' 처럼 괄호가 깨진 것, 'Menerapkan'(인도네시아어) 같은 것들이다."""
    v = vi.strip()
    if v.count("(") != v.count(")"): return "괄호 깨짐"
    # 'tính toán (계산의 의미만 맞음, 예습은' 처럼 한글 설명이 낱말 칸에 딸려 왔다
    if re.search(r"[가-힣]", v): return "낱말 칸에 한글"
    if re.match(r"^[A-Za-z][A-Za-z .,'\-]*$", v) and not_viet(v): return "베트남어 아님"
    # 뜻이 '기관 / 무리 / 우산' 처럼 두 번 넘게 갈라져 있으면 칸이 붙은 것이다
    if ko.count("/") >= 2 and len(v.split()) >= 2: return "칸이 붙음"
    if len(v.split()) >= 3 and ko.count("/") >= 1: return "칸이 붙음"
    if re.search(r"[a-z][A-ZĐ]", v): return "붙어 버림"          # mởcửa
    # **문장은 낱말이 아니다** — 시험지의 '문장 번역' 문제가 낱말 칸으로 새어 들어왔다.
    #   'Anh bị làm sao?'(어디 아프세요) · 'Ý hay đấy!'(좋은 생각이야) (2026-08-30 검수)
    if re.search(r"[?!]", v) or ":" in v: return "문장"
    if re.search(r"\.\.+|…", v): return "문법 틀"
    if re.search(r"(^|\s)[ABC](\s|$)", v): return "문법 틀"      # 'tuy A nhưng B'
    if len(v.split()) >= 6: return "문장"
    return None


def head(vi):
    """낱말 하나로 다듬는다 — 시험지에는 '보기'가 여럿 적힌 칸이 많다.
       'bố / ba' → bố · 'bến xe (buýt)' → bến xe · 'anh/chị/em họ' → anh họ.
       예문을 만들 때도, 소리를 만들 때도 **낱말 하나**여야 한다."""
    v = U.normalize("NFC", str(vi)).strip()
    v = re.sub(r"\s*\([^)]*\)\s*", " ", v)          # 괄호 안은 곁들이 설명이다
    if "/" in v:
        parts = [x.strip() for x in v.split("/") if x.strip()]
        if parts:
            # 'anh/chị/em họ' 처럼 뒤에 공통 꼬리가 붙는 꼴을 살린다
            tail = parts[-1].split()
            v = parts[0] + (" " + " ".join(tail[1:]) if len(tail) > 1 and len(parts[0].split()) == 1 else "")
    return re.sub(r"\s+", " ", v).strip(" ,.;:")


# 나라·땅·회사 이름은 베트남어에서도 **대문자가 규칙**이다. 이것만 대문자를 지킨다.
#   Anh(영국) 과 anh(형) 은 서로 다른 낱말이다 — 소문자로 눌러 버리면 안 된다.
PROPER = {"Anh","Mỹ","Nga","Nhật","Pháp","Đức","Ý","Úc","Canada","Lào","Huế","Việt","Tết","Noel",
          "Trung Quốc","Hàn Quốc","Việt Nam","Thái Lan","Nhật Bản","Hà Nội","Sài Gòn","Đà Nẵng",
          "Hải Phòng","Cần Thơ","Nha Trang","Hạ Long","Sa Pa","Hồ Chí Minh","Singapore",
          "Tết Nguyên Đán","Tết Trung Thu","Facebook","Google","Zalo","Grab","Samsung","Hyundai"}
# 뜻이 **나라·도시·명절 이름**이면 베트남어도 대문자가 규칙이다.
#   시험지가 문장 첫 낱말을 대문자로 적은 것과 구별하려면 뜻을 봐야 한다 (2026-08-30).
NAMES = (r"이집트|폴란드|캄보디아|핀란드|스웨덴|노르웨이|스위스|네덜란드|벨기에|오스트리아|"
         r"스페인|이탈리아|포르투갈|그리스|터키|이스라엘|이란|이라크|인도|대만|말레이시아|"
         r"인도네시아|필리핀|미얀마|싱가포르|브라질|멕시코|아르헨티나|칠레|남아프리카|뉴질랜드|"
         r"영국|미국|중국|일본|한국|러시아|프랑스|독일|호주|캐나다|태국|라오스|베트남|"
         r"하노이|호찌민|호치민|다낭|사이공|후에|나트랑|하롱|사파|설날|추석|중추절")
# 뜻이 **딱 나라·도시·명절 이름 하나**일 때만 대문자로 되돌린다.
#   '러시아워'·'베트남전통모자' 까지 나라로 읽어 Cao Điểm·Nón 이 되었다 (2026-08-30).
KO_NAME1 = re.compile(rf"^\(?\s*(?:나라\s*)?({NAMES})\s*(?:어|인|족|사람|말)?\s*\)?$")
# 'nước Hàn'(나라 한국)·'tiếng Nhật'(일본어) 처럼 앞머리가 보통명사면 그 머리는 소문자다.
LEAD = re.compile(r"^(nước|tiếng|người|ngày|món|đồ|chữ|xe|bánh|phía|thành phố|dân)\b", re.I)


# 베트남어에서 대문자로 적는 **조각**들. 이것 말고는 다 소문자다.
#   'Bọn Anh'(우리 형들) 의 Anh 은 형이지 영국이 아니다 — 그래서 조각 판단만으로는 모자라
#   앞머리가 bọn·người·tiếng 처럼 보통명사면 뒤 조각도 함께 본다.
CAPS = {"Anh","Mỹ","Nga","Nhật","Bản","Pháp","Đức","Ý","Úc","Hàn","Quốc","Trung","Việt","Nam",
        "Thái","Lan","Lào","Hán","Âu","Phi","Á","Cập","Ai","Điển","Thụy","Phần","Ba","Kông",
        "Hồng","Khme","Canada","Singapore","Nobel","Tết","Nguyên","Đán","Thu","Campuchia",
        "Huế","Hà","Nội","Sài","Gòn","Đà","Nẵng","Hải","Phòng","Cần","Thơ","Nha","Trang",
        "Hạ","Long","Sa","Pa","Hồ","Chí","Minh","Bắc","Bộ","Tây","Lim","Đông","Giêng","Chạp",
        "Facebook","Google","Zalo","Grab","Samsung","Hyundai","Noel","Jin","Nhà"}
# 앞머리가 이것이면 **뒤가 나라 이름일 때만** 대문자다 (bọn anh · tiếng Anh)
KIN = re.compile(r"^(bọn|chúng|các)\b", re.I)

def uncap(v, ko=""):
    """시험지가 문장 첫 낱말을 대문자로 적어 놓은 것을 되돌린다 (2026-08-30 검수, 516개).
       조각마다 본다 — 'Bọn Anh'(우리 형들) 은 둘 다 소문자, 'tiếng Anh'(영어) 은 Anh 만 대문자."""
    if v in PROPER: return v
    kin = bool(KIN.match(v))
    one = len(v.split()) == 1
    out = []
    for k, t in enumerate(v.split()):
        keep = (t in CAPS) and not kin
        # 여러 마디 낱말의 **첫 마디**는 문장 첫 글자일 뿐이다 —
        #   'Anh họ'(사촌형)의 Anh 은 영국이 아니다 (2026-08-30 검수)
        if k == 0 and not one and t != "Tết": keep = False
        if one and t in PROPER: keep = True
        out.append(t if keep else t[:1].lower() + t[1:])
    r = SPELL.get(" ".join(out), " ".join(out))
    if KO_NAME1.match(ko.strip()):                 # 뜻이 딱 나라 이름이면 통째로 고유명사
        ts = r.split()
        head = 1 if LEAD.match(r) and len(ts) > 1 else 0
        r = " ".join([t for t in ts[:head]] + [t[:1].upper() + t[1:] for t in ts[head:]])
    return SPELL.get(r, r)



V_ = re.compile(r"[aeiouyăâêôơư]", re.I)   # 베트남어 음절엔 반드시 모음이 있다

def glue(v, known=None):
    """PDF 에서 음절 가운데 공백이 끼어 들어온 것을 도로 붙인다 (2026-08-30 검수).
       ① 모음이 아예 없는 토막('b ệnh')은 무조건 붙인다.
       ② 그 밖에는 **붙인 꼴이 다른 자료에도 있을 때만** 붙인다.
          'Hàn Qu ốc' 의 'Qu' 에는 모음 u 가 있어 ①에 안 걸린다.
          그렇다고 아무 데나 붙이면 'bà ấy'(그 사람)까지 'bày' 로 뭉갠다."""
    ss = v.split()
    if len(ss) < 2: return v
    out = []
    for t in ss:
        if out and t not in ("A","B","C","X","Y") and re.fullmatch(r"[A-Za-zĐđ]+", t) and not V_.search(U.normalize("NFD", t)):
            out.append(out.pop() + t)
        elif out and not V_.search(U.normalize("NFD", out[-1])) and re.search(r"[A-Za-zĐđ]", out[-1]):
            out[-1] = out[-1] + t
        else:
            out.append(t)
    if known:                                   # ② 자료에 있는 꼴이면 붙인다
        i = 1
        while i < len(out):
            cand = out[:i - 1] + [out[i - 1] + out[i]] + out[i + 1:]
            if " ".join(cand).lower() in known: out = cand
            else: i += 1
    return " ".join(out)


def bare(v):
    """성조·모자·괄호·대소문자를 다 벗긴 뼈대. 겹침을 찾을 때만 쓴다."""
    s = U.normalize("NFD", v.lower())
    s = "".join(c for c in s if not U.combining(c)).replace("đ", "d")
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z ]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def merge_ko(a, b):
    """같은 낱말의 두 뜻을 하나로 잇는다. 한쪽이 다른 쪽을 품으면 넓은 쪽만 남긴다."""
    out = [x.strip() for x in re.split(r"[/·]", a) if x.strip()]
    for x in [y.strip() for y in re.split(r"[/·]", b) if y.strip()]:
        if not any(x in y or y in x for y in out): out.append(x)
    return " / ".join(out)


def same_word(ws):
    """**표기가 완전히 같은** 낱말은 한 장으로 합치고 뜻을 잇는다 (2026-08-30 검수).
       성조가 다르면 다른 낱말이다 — bạn(친구)·bán(팔다)·bận(바쁘다) 은 여기 안 걸린다.
       'xử lý 처리하다' 와 'xử lý 다루다, 처리하다' 가 두 장으로 나뉘어 있었다(51쌍)."""
    g = collections.OrderedDict()
    for w in ws:
        k = U.normalize("NFC", w["vi"])
        if k in g:
            g[k]["ko"] = merge_ko(g[k]["ko"], w["ko"])
            g[k]["n"] = max(g[k].get("n", 0), w.get("n", 0))
            g[k]["gi"] = "".join(sorted(set(re.findall(r"\d\d", g[k].get("gi", "") + w.get("gi", "")))))
        else: g[k] = w
    return list(g.values()), len(ws) - len(g)


def dedupe(ws):
    known = {w["vi"].lower() for w in ws if " " not in w["vi"] or "  " not in w["vi"]}
    known |= {" ".join(w["vi"].lower().split()) for w in ws}
    for w in ws: w["vi"] = uncap(glue(w["vi"], known), w.get("ko", ""))
    """뼈대도 같고 **뜻도 같은** 것만 하나로 합친다.
       성조가 다르면 다른 낱말이다(bạn 친구 · bán 팔다 · bận 바쁘다) — 절대 안 합친다."""
    g = collections.defaultdict(list)
    for w in ws:
        # **뜻이 비어 있으면 절대 합치지 않는다** — ấn(누르다)과 ăn(먹다)이 합쳐졌었다.
        # 뼈대가 같아도 뜻이 없으면 같은 낱말이라는 근거가 없다 (2026-08-30).
        key = (bare(w["vi"]), w["ko"]) if w.get("ko") else ("\0" + w["vi"], "")
        g[key].append(w)
    out, gone = [], 0
    for _, arr in g.items():
        if len(arr) == 1: out.append(arr[0]); continue
        # 남길 것: 기수에 더 많이 나온 것 → 괄호 없는 것 → 소문자로 시작하는 것
        arr.sort(key=lambda w: (-w["n"], "(" in w["vi"], w["vi"][:1].isupper(), len(w["vi"])))
        keep = dict(arr[0])
        keep["gi"] = "".join(sorted({c for w in arr for c in re.findall(r"\d\d", w["gi"])}))
        keep["n"] = len(re.findall(r"\d\d", keep["gi"]))
        out.append(keep); gone += len(arr) - 1
    return out, gone


def main():
    p = R / "data" / "senior_pool.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    kept = dropped = 0
    out = []
    for w in d["words"]:
        if w.get("ko"): out.append(w); continue
        ko = KEEP.get(w["vi"])
        if not ko: dropped += 1; continue          # 남은 것은 문장 토막이다 — 버린다
        w = dict(w); w["ko"] = ko; w.pop("en", None)
        out.append(w); kept += 1
    for w in out:                       # 낱말 하나로 다듬기
        h = head(w["vi"])
        if h and h != w["vi"]: w["vi"] = h
    # ── 칸이 붙은 줄은 **버리지 말고 쪼갠다** (2026-08-30).
    #    'xe tải mặt trăng | 트럭 / 달' 은 xe tải(트럭) 과 mặt trăng(달) 두 낱말이
    #    한 줄에 붙어 버린 것이다. 쪼개면 둘 다 살아난다.
    #    쪼갤 수 있는지는 **쪼갠 조각이 다른 줄에도 낱말로 있는가**로 판단한다.
    # 쪼갠 조각이 **그 뜻 그대로** 다른 줄에도 있어야 한다.
    #   낱말만 아는 것으로는 모자란다 — 'năm sản xuất | 제조 연도' 를 왼쪽부터 붙이면
    #   năm=제조, sản xuất=연도 가 되어 **뒤바뀐다**(베트남어와 한국어의 어순이 반대다).
    #   조각과 뜻이 짝으로 확인될 때만 쪼갠다. (2026-08-30)
    known = {bare(w["vi"]) for w in out}
    pairs = {(bare(w["vi"]), w["ko"].split("/")[0].strip()) for w in out if w.get("ko")}
    split_add, split_n = [], 0
    import itertools
    for w in list(out):
        if junk(w["vi"], w["ko"]) != "칸이 붙음": continue
        parts = [x.strip() for x in w["ko"].split("/") if x.strip()]
        toks = w["vi"].split()
        n = len(parts)
        if not (2 <= n <= 4) or len(toks) < n: continue
        # 베트남어를 n 조각으로 나누는 모든 방법 × 뜻을 붙이는 모든 차례를 다 해 본다.
        # **모든 짝이 다른 줄에서 확인되는 경우에만** 쪼갠다 — 하나라도 확인 안 되면 안 쪼갠다.
        best = None
        for cuts in itertools.combinations(range(1, len(toks)), n - 1):
            b = [0, *cuts, len(toks)]
            chunks = [" ".join(toks[b[i]:b[i + 1]]) for i in range(n)]
            for perm in itertools.permutations(parts):
                if all((bare(c), p.split("/")[0].strip()) in pairs for c, p in zip(chunks, perm)):
                    best = list(zip(chunks, perm)); break
            if best: break
        if best:
            for vi2, ko2 in best:
                split_add.append({**w, "vi": vi2, "ko": ko2, "split": 1})
            out.remove(w); split_n += 1
    out += split_add

    junked = collections.Counter()
    keep = []
    for w in out:
        why = junk(w["vi"], w["ko"])
        if why: junked[why] += 1
        else: keep.append(w)
    out = keep
    out, gone = dedupe(out)
    out, gone2 = same_word(out); gone += gone2
    for w in out:                                   # 손으로 바로잡은 철자와 뜻
        if w["vi"] in SPELL2: w["vi"] = SPELL2[w["vi"]]
        if w["vi"] in FIXKO: w["ko"] = FIXKO[w["vi"]]
    out.sort(key=lambda w: (w.get("pos") is None, w.get("pos") or 0, -w["n"]))
    d["words"] = out
    d["note"] = ("네 기수(17·18·19·20) 단어시험. 겹침을 지웠다(뼈대와 뜻이 둘 다 같을 때만). "
                 "pos = 배운 차례 0~1. gi = 나온 기수.")
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"손으로 뜻 채운 것 {kept} · 토막이라 버린 것 {dropped} · 겹쳐서 합친 것 {gone} · 남은 낱말 {len(out)}")
    if junked: print("  낱말이 아니라 버린 것:", dict(junked))
    print(f"  칸이 붙은 줄을 쪼개 살린 것: {split_n}줄 → {len(split_add)}낱말")


if __name__ == "__main__":
    main()
