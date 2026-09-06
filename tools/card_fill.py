#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**고른 기사의 재료를 만든다** — 낱말 열·대화 두 줄·여섯 줄 풀이

대표님 지적 (2026-09-02): "기사를 먼저 선정하고, 그 기사에서 학습 세트를 뽑아야지."

## 왜 따로 만드나
`news_lesson.py` 는 **새로 받은 기사**만 처리한다 (이미 저장된 것은 건너뛴다).
`news_sum5.py` 는 **마지막에 받은 기사**의 본문만 본다.
그래서 '저장은 됐는데 재료가 없는' 기사는 어느 쪽도 손대지 못했다.
이 도구는 **pub 이 찍힌 기사**를 보고, 본문을 다시 받아서라도 재료를 채운다.

쓰기: python3 tools/card_fill.py
"""
import json, pathlib, re, subprocess, sys

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr
from qwen import ask, up

F = R / "data" / "news_days.json"
BODY = R / "data" / "_bodies.json"        # 주소 → 본문. 한 번 받으면 남는다

LESSON = ("아래 기사를 읽고 베트남어 학습 재료를 만들어라.\n"
          " ① words: 기사와 관련된 베트남어 낱말 **정확히 6개**. 초급이 쓸 만한 것\n"
          "    각각 vi(베트남어)·ko(한국어 뜻 12자 이내)\n"
          " ② lines: 그 기사 내용을 주고받는 **대화 두 줄**. who 는 A·B\n"
          "    각각 vi·ko. 위 낱말을 되도록 쓴다\n"
          " ③ theme: 이 기사를 두 낱말로 (예: 교통 안전)\n"
          "규칙: 성조 부호를 빠뜨리지 마라. 한국어 뜻은 한글만.\n"
          '출력은 JSON 하나만: {"theme":"","words":[{"vi":"","ko":""}],'
          '"lines":[{"who":"A","vi":"","ko":""}]}\n\n')

# **기사를 다시 쓰는 것**이지, 대표님께 보고하는 것이 아니다.
# 전에는 "마지막 줄은 우리에게 무슨 뜻인지" 라고 시켰더니
# "우리 기업도 노려볼 만해요", "우리는 함께 노력해야 해요" 같은 훈수가 나왔다
# (대표님 지적 2026-09-02 "기사 내용이 아니라 나한테 뭐 보고하듯이 작성하면 안 되지").
SUM5 = ("아래 기사를 **여섯 줄짜리 기사로 다시 써라.** 기사에 있는 사실만 쓴다.\n"
        " \u2460 존댓말이되 **'~요'** 로 끝낸다. '~습니다'\u00b7'~한다' 금지\n"
        " \u2461 **한 줄은 28자를 넘기지 마라.** 카드에서 두 줄로 접히면 답답해진다\n"
        " \u2462 한 줄에 **사실 하나만.** '~하고 ~하며' 로 길게 잇지 마라\n"
        " \u2463 **다음은 절대 쓰지 마라 — 하나라도 있으면 틀린 답이다:**\n"
        "    \u00b7 '우리'\u00b7'우리 기업'\u00b7'~해야 해요' 같은 훈수\u00b7제언\n"
        "    \u00b7 '안타깝네요'\u00b7'기대돼요'\u00b7'놀랍네요' 같은 느낌\n"
        "    \u00b7 '~을 보여줘요'\u00b7'~라는 뜻이에요' 같은 풀이\u00b7해석\n"
        "    \u00b7 읽는 사람에게 말을 거는 투\n"
        " \u2464 숫자\u00b7이름\u00b7날짜는 기사 그대로. **없는 숫자를 지어내지 마라**\n"
        "    베트남어 단위를 **꼭 바꿔 써라** — t\u1ef7 = 10억, tri\u1ec7u = 100만,\n"
        "    ngh\u00ecn t\u1ef7 = 1조, tr\u0103m tri\u1ec7u = 1억.\n"
        "    보기: 35,2 t\u1ef7 USD \u2192 352억 달러 / 500 t\u1ef7 USD \u2192 5,000억 달러\n"
        "    (베트남어는 소수점을 쉼표로 쓴다. 35,2 는 삼십오 점 이다)\n"
        "    베트남 말 \u2192 우리 말: n\u1ed9i tr\u00fa=전공의, R\u0103ng-H\u00e0m-M\u1eb7t=치의학,\n"
        "    ph\u01b0\u1eddng=동, h\u00f3a h\u1ecdc=화학, \u00f4ng ngo\u1ea1i=외할아버지\n"
        " \u2465 **모든 줄이 '요' 로 끝나야 한다.** 한 줄이라도 '~다' 로 끝나면 틀린 답이다\n"
        " \u2466 회사\u00b7기관 이름은 **한국에서 부르는 대로** 적어라.\n"
        "    영문 약칭이 더 알려졌으면 그것을 쓴다 (SCB\u00b7VIFA\u00b7GDP)\n"
        "    땅\u00b7사람 이름은 **한글로** (B\u1eafc Ninh\u2192박닌, Ph\u00fa Th\u1ecd\u2192푸토).\n"
        "    베트남어\u00b7영어 낱말을 그대로 남기지 마라\n"
        " \u2467 여섯 줄이 모여 기사 한 편이 되게 —\n"
        "    누가 / 무엇을 / 얼마나 / 언제\u00b7어디서 / 왜 / 앞으로 어떻게\n"
        "\n"
        # **말로 스무 번 시키는 것보다 보기 하나가 낫다.**
        # 단위 환산표를 글로만 줬더니 세 판 다 틀렸다 (2026-09-02 실측).
        # 틀린 보기와 맞는 보기를 나란히 놓고 **왜 맞는지**까지 적는다.
        "== 보기 ==\n"
        "원문: doanh thu 35,2 t\u1ef7 USD, l\u1ee3i nhu\u1eadn 2,31 t\u1ef7 USD\n"
        "  \u2715 틀림: 매출은 35억 2천만 달러예요\n"
        "  \u2713 맞음: 매출은 352억 달러예요 / 이익은 23억 1,000만 달러예요\n"
        "  왜: t\u1ef7 는 10억이다. 35,2 t\u1ef7 = 35.2 \u00d7 10억 = 352억.\n"
        "      베트남어는 쉼표가 소수점이라 35,2 는 삼십오 점 이다\n"
        "원문: xu\u1ea5t kh\u1ea9u l\u0169y k\u1ebf 500 t\u1ef7 USD\n"
        "  \u2715 틀림: 수출 500억 달러\n"
        "  \u2713 맞음: 수출 5,000억 달러\n"
        "원문: d\u1ecbp Qu\u1ed1c kh\u00e1nh 2/9\n"
        "  \u2715 틀림: 2월 9일 국경절\n"
        "  \u2713 맞음: 9월 2일 국경절\n"
        "  왜: 베트남은 날짜를 일/월 차례로 쓴다\n"
        "원문: th\u1ee7 khoa ng\u00e0nh R\u0103ng-H\u00e0m-M\u1eb7t b\u00e1c s\u0129 n\u1ed9i tr\u00fa\n"
        "  \u2715 틀림: 치과내과 수석\n"
        "  \u2713 맞음: 치의학 전공의 수석\n"
        "  왜: n\u1ed9i tr\u00fa 는 전공의(레지던트)지 내과가 아니다\n"
        "\n"
        "== 여섯 줄이 이런 꼴이면 맞다 ==\n"
        "  도요타가 베트남 푸토성 공장에 더 투자해요\n"
        "  금액은 2억 8,300만 달러예요\n"
        "  이번에 전동화 차량 조립\u00b7생산이 새로 들어갔어요\n"
        "  한 해 만들 수 있는 차는 5만 2,000대예요\n"
        "  내년 7월 도장 공장과 프레스 공장을 짓기 시작해요\n"
        "  두 공장은 2029년에 돌아가는 것이 목표예요\n"
        "  왜 맞나: 한 줄에 사실 하나, 숫자는 원문 그대로, 모두 '요' 로 끝나고,\n"
        "          훈수\u00b7느낌\u00b7기사 얘기가 한 줄도 없다\n\n"
        '출력은 JSON 하나만: {"sum5":["","","","","",""]}\n\n')


def body_of(url, cache):
    if url in cache and len(cache[url]) > 200:
        return cache[url]
    try:
        h = subprocess.run(["curl", "-sSL", "-m", "25", "-A", "Mozilla/5.0", url],
                           capture_output=True, text=True, timeout=40).stdout
    except Exception:
        return ""
    # 사이트마다 본문을 담는 곳이 다르다. 차례로 맞춰 본다.
    #   인사이드비나·코리아타임즈 = article-view-content-div
    #   VnExpress(영어·베트남어)  = <p class="Normal">
    #   Tuổi Trẻ                 = detail-content / detail__content
    #   Dân Trí                  = singular-content / dt-news__content
    m = re.search(r'id="article-view-content-div"[^>]*>(.*?)</div>\s*</div>', h, re.S)
    t = m.group(1) if m else ""
    if not t:
        t = " ".join(re.findall(r'<p class="Normal"[^>]*>(.*?)</p>', h, re.S))
    if not t:
        # **Dân Trí 는 <article id="articleContent"> 로 바뀌었다** (2026-09-02 실측).
        # 옛 이름(singular-content)만 찾다 못 찾고 **차림표를 본문으로 긁어**
        # "2026 AFF 컵과 네팔-중국 국경 홍수" 가 임금 정책 기사 요약으로 나갔다.
        i = h.find('id="articleContent"')
        if i > 0:
            j = h.find('data-content-name="article-related"', i)
            t = " ".join(re.findall(r"<p[^>]*>(.*?)</p>",
                                    h[i:j if j > 0 else i + 120000], re.S))
    if not t:
        for pat in (r'class="[^"]*detail-content[^"]*"[^>]*>(.*?)</div>\s*</div>',
                    r'class="[^"]*detail__content[^"]*"[^>]*>(.*?)</div>\s*</div>',
                    r'class="[^"]*singular-content[^"]*"[^>]*>(.*?)</div>\s*</div>',
                    r'class="[^"]*dt-news__content[^"]*"[^>]*>(.*?)</div>\s*</div>'):
            mm = re.search(pat, h, re.S)
            if mm:
                t = mm.group(1); break
    if not t:
        # 그래도 못 찾으면 <p> 를 다 모아 본다 (짧은 것은 버린다)
        ps = [x for x in re.findall(r"<p[^>]*>(.*?)</p>", h, re.S) if len(x) > 80]
        t = " ".join(ps[:30])
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S)
    import html as _h
    t = _h.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))).strip()
    # **차림표인가 본문인가.** 신문 첫 화면의 갈래 목록은 낱말만 촘촘히 늘어서고
    # 마침표가 거의 없다. 진짜 본문은 문장이라 마침표가 많다.
    dots = t.count(".") + t.count("!") + t.count("?")
    if len(t) > 400 and dots < len(t) / 400:
        print(f"    \u26a0 본문이 아니라 차림표를 긁었다 — 버린다: {url[:60]}")
        return ""
    if len(t) > 200:
        cache[url] = t[:6000]
    return t


def jget(txt):
    m = re.search(r"\{.*\}", txt or "", re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None


def lines_of(txt):
    """여섯 줄 풀이를 뽑는다. **JSON 이 아니어도 받는다** —
    Qwen 이 제대로 여섯 줄을 써 놓고 줄글로 줘서 통째로 버려졌다 (2026-09-02 실측)."""
    g = jget(txt)
    got = (g or {}).get("sum5") if isinstance(g, dict) else None
    if isinstance(got, list) and len(got) >= 4:
        return [str(x).strip() for x in got if str(x).strip()][:6]
    # JSON 이 **중간에 잘려도** 따옴표 안의 줄은 건진다 —
    # max_tokens 에 걸려 끝을 못 닫으면 좋은 요약이 통째로 버려졌다 (2026-09-02 실측)
    if '"sum5"' in (txt or ""):
        q = re.findall(r'"([^"\n]{12,90})"', txt[txt.index('"sum5"') + 7:])
        q = [x.strip() for x in q if re.search(r"[가-힣]", x)]
        if len(q) >= 4:
            return q[:6]
    # 줄글이면 줄로 나눈다. 번호·따옴표·머리표를 떼어 낸다
    out = []
    for ln in (txt or "").split("\n"):
        # 머리표만 뗀다 — '1.' '2)' '- ' 처럼 **점이나 괄호가 붙은** 숫자만.
        # 그냥 숫자로 시작하는 문장의 숫자를 떼면 안 된다
        # (실측 2026-09-02: '2020년 개정된 법은…' 이 '년 개정된 법은…' 이 됐다)
        t = re.sub(r'^[\s\-·•*]+', "", ln)
        t = re.sub(r'^\d{1,2}[.)]\s+', "", t).strip().strip('"').strip("'")
        t = re.sub(r'^[\[\]{}",]+|[\[\]{}",]+$', "", t).strip()
        if len(t) >= 10 and re.search(r"[가-힣]", t) and not t.startswith(("제목", "본문", "sum5")):
            out.append(t)
    return out[:6] if len(out) >= 4 else []


# **보고체·훈수체를 기계로 막는다.** 시키는 말만으로는 안 새어 나오게 못 한다 —
# "우리 기업도 노려볼 만해요" 가 그대로 카드에 찍혔다 (2026-09-02 실측).
# **기사 자체를 말하는 줄**은 기사가 아니다. 본문을 못 받으면 Qwen 이
# "본문이 태그 목록만 나열되어 있어요", "정확한 요약이 불가능해요" 라고 **변명을 써 냈다**
# (대표님 지적 2026-09-02 "기사 내용이 아니라 뭔 나랑 대화하니? 보고하니?").
# 이런 줄이 하나라도 있으면 **그 기사는 카드를 안 만든다** — 지어내느니 빼는 게 낫다.
META = [
    "기사 제목은", "기사 제목이", "이 기사는", "본문은", "본문이", "원문은", "제목만",
    "카테고리", "태그", "링크", "목록만", "나열", "누락", "요약이", "요약을", "요약은",
    "파악하기", "확인하지", "확인할 수 없", "알 수 없", "불가능", "어렵어요", "어려워요",
    "내용이 없", "정보가 없", "자료로", "불완전", "베트남어로 작성", "번역",
    "다양한 선택지", "최신 정보와",
]
PREACHY = [
    "우리", "저희", "여러분", "독자",
    "해야 해요", "해야겠어요", "해야 합니다", "필요해 보여요", "필요할 것 같",
    "노려볼", "주목할 만", "눈여겨", "참고하", "기억해",
    "안타깝", "놀랍", "기대돼", "다행이", "아쉽", "인상적",
    "보여줘요", "보여줍", "뜻이에요", "의미해요", "시사", "라는 점에서",
    "알아두", "살펴보", "생각해", "느껴",
]


def preachy(line):
    """기사가 아니라 **말을 거는 줄**인가."""
    return any(k in line for k in PREACHY)


# 베트남어 성조 부호 — 옮기다 만 낱말이 그대로 남은 것을 잡는다
# ('삼성 베트남은 누적 투자 vốn 이 240억 달러', 2026-09-02 실측)
VI_MARK = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệ"
                     r"ìíỉĩịòóỏõọôồốổỗộơờớởỡợ"
                     r"ùúủũụưừứửữựỳýỷỹỵđ]", re.I)


# **이름은 한국 신문이 쓰는 대로.** 억지로 음차하면 못 알아본다
# (대표님 지적 2026-09-02 "시암은행. 시암은 영어로 해야 하는 거 아니냐?").
#   \u00b7 베트남 땅\u00b7사람 이름 \u2192 한글 (B\u1eafc Ninh \u2192 박닌)  … 학습자가 읽어야 하니까
#   \u00b7 회사\u00b7기관\u00b7상표   \u2192 한국에서 부르는 이름. 영문 약칭이 더 알려졌으면 그것을
NAME_FIX = {
    "시암은행": "시암상업은행(SCB)", "시암 은행": "시암상업은행(SCB)",
    "북 Ninh": "박닌", "B\u1eafc Ninh": "박닌", "박 Ninh": "박닌",
    "Ph\u00fa Th\u1ecd": "푸토", "Th\u00e1i Nguy\u00ean": "타이응우옌", "태원": "타이응우옌",
    "H\u00e0 N\u1ed9i": "하노이", "TPHCM": "호찌민", "TP.HCM": "호찌민",
    "Ph\u00fa Qu\u1ed1c": "푸꾸옥", "D\u01b0\u01a1ng \u0110\u00f4ng": "즈엉동",
    "Roh Tae Moon": "노태문", "v\u1ed1n": "자본",
}


def fix_names(t):
    for a_, b_ in NAME_FIX.items():
        t = t.replace(a_, b_)
    return t


# **자주 나오는 틀린 꼴.** 새로 보이는 대로 여기에 더한다
# (대표님 지적 2026-09-02 "오타들도 간혹 있다. 예) 안타깝워요")
TYPO = ["았아요", "었아요", "였아요", "않어요", "좋어요", "많어요", "같어요", "깝워요", "깝어요", "립어요", "깁어요",
        "웁어요", "릅어요", "씁어요", "덥어요", "춥어요", "쉽어요", "겹어요", "이어요"]


def bad_line(t):
    """카드에 실으면 안 되는 줄인가 — 왜 안 되는지 돌려준다."""
    if any(k in t for k in META):
        return "기사가 아니라 기사 얘기"
    if any(k in t for k in TYPO):
        return "틀린 말꼴"
    if preachy(t):
        return "훈수·느낌"
    # **말투는 '~요' 하나로 굳힌다.** 한 카드 안에서 '~다' 와 '~요' 가 섞여 나왔다
    # (2026-09-02 실측: 푸꾸옥 카드가 '선정됐다'·'유명하다'·'포함돼요' 뒤범벅).
    if not t.rstrip(" .").endswith("요"):
        return "'~요' 로 안 끝남"
    if VI_MARK.search(t):
        return "베트남어 원문이 남음"
    if re.search(r"[\u4e00-\u9fff]", t):
        return "한자가 남음"
    # 28자로 시켰는데 45자짜리가 나와 카드에서 두 줄로 접혔다 (2026-09-02 실측)
    # 카드가 글꼴을 줄여 한 줄에 넣어 주므로 조금 긴 것은 괜찮다.
    # 38자로 조였더니 멀쩡한 줄이 다 죽었다 (2026-09-02 실측) — 달아나는 줄만 막는다
    if len(t) > 48:
        return "너무 김"
    return ""


def _nums(t):
    """숫자를 견줄 수 있는 꼴로 바꾼다.
    베트남어는 소수를 쉼표로 쓰고(35,2) 단위가 tỷ(10억)이라 우리 말로 옮기면
    자릿수가 달라진다. 그래서 **쉼표·점을 떼고 뒤쪽 0 도 떼어** 견준다 —
    352 ↔ 35,2 도, 5,000억 ↔ 500 tỷ 도 같은 수로 본다."""
    out = set()
    for m in re.findall(r"\d[\d.,]*", t or ""):
        z = re.sub(r"[.,]", "", m).lstrip("0")
        if len(z) >= 2:
            out.add(z.rstrip("0") or z)
    return out


def invented(line, body):
    """기사에 없는 숫자를 지어냈는가."""
    return _nums(line) - _nums(body)


def clean5(got, body=""):
    """카드에 못 쓸 줄을 뺀다. 넷을 못 채우면 빈 것을 돌려 다시 묻게 한다.

    **'기사 얘기' 가 하나라도 섞이면 통째로 버린다** — 본문을 못 받았다는 뜻이라
    남은 줄도 믿을 수 없다. 다시 물어도 같으면 그 기사는 카드를 안 만든다."""
    why = [f"{bad_line(x)}: {x[:26]}" for x in got if bad_line(x)]
    hit = [(k, x) for x in got for k in META if k in x]
    if hit:
        print(f"      ⚠ 본문을 못 받은 듯 — 통째로 버린다 ('{hit[0][0]}'): {hit[0][1][:34]}")
        return []
    keep = [x for x in got if not bad_line(x)]
    # **기사에 없는 숫자를 지어낸 줄은 뺀다** — 하동동이 '2025년 7월 1일 5개 동으로
    # 통합' 된다는 말이 본문에 없는데 나왔다 (2026-09-02 실측)
    if body:
        bad = [x for x in keep if invented(x, body)]
        if bad:
            print(f"      지어낸 수 {len(bad)}줄 뺌: {bad[0][:30]}")
        keep = [x for x in keep if x not in bad]
    # 같은 말을 두 번 하는 줄도 뺀다 (홈크레딧 '순익 1조 3천 430억' 이 두 줄)
    seen, uniq = set(), []
    for x in keep:
        k = tuple(sorted(_nums(x))) + (x[:8],)
        if k in seen:
            continue
        seen.add(k); uniq.append(x)
    keep = uniq
    if len(keep) < 4 and why:
        print("      " + " / ".join(why[:3]))
    return keep if len(keep) >= 4 else []


def main():
    if not up():
        print("Qwen 이 안 켜져 있다"); return
    j = json.loads(F.read_text(encoding="utf-8"))
    cache = json.loads(BODY.read_text(encoding="utf-8")) if BODY.exists() else {}
    pub = [d for d in j["days"] if d.get("pub")]
    print(f"펴낼 기사 {len(pub)}")

    for d in pub:
        need_l = (len(d.get("words") or []) < 6
                  or len(((d.get("dialog") or {}).get("lines") or [])) < 2)
        need_s = len(d.get("sum5") or []) < 4
        if not (need_l or need_s):
            continue
        b = body_of(d.get("u") or "", cache)
        if len(b) < 200:
            print(f"  본문 못 받음: {(d.get('title') or '')[:30]}"); continue
        head = f"제목: {d.get('title')}\n본문:\n{b[:2500]}"

        if need_l:
            g = jget(ask(LESSON + head, max_tokens=2500))
            if g and len(g.get("words") or []) >= 5 and len(g.get("lines") or []) >= 2:
                ws = []
                for w in g["words"][:6]:
                    vi = str(w.get("vi") or "").strip()
                    ko = str(w.get("ko") or "").strip()
                    if not vi or not ko or re.search(r"[^가-힣ㄱ-ㆎ0-9 ·()~,./%\-]", ko):
                        continue
                    ws.append({"vi": vi, "ko": ko, "kr_read": vi_kr.word(vi) or ""})
                ls = [{"who": (l.get("who") or "AB"[i % 2]),
                       "vi": str(l.get("vi") or "").strip(),
                       "ko": str(l.get("ko") or "").strip(),
                       "kr_read": vi_kr.word(str(l.get("vi") or "").strip()) or ""}
                      for i, l in enumerate(g["lines"][:2])]
                if len(ws) >= 5 and all(x["vi"] for x in ls):
                    d["words"] = ws
                    d["dialog"] = {"title": g.get("theme") or "기사", "emoji": "📰",
                                   "lines": ls, "extra": []}
                    d["theme"] = (g.get("theme") or d.get("theme") or "기사")[:12]
                    print(f"  낱말·대화 채움: {(d.get('title') or '')[:30]}")

        if need_s:
            got = []
            import news_sum5 as N
            for _try in range(3):
                # **다듬고 나서 검사한다.** 거꾸로 하면 '~했다' 가 '~했어요' 로
                # 바뀌기도 전에 걸려 멀쩡한 줄이 다 죽는다 (2026-09-02 실측)
                raw = [fix_names(N.tidy(x)) for x in lines_of(ask(SUM5 + head, max_tokens=2000))]
                got = clean5(raw, b)
                if len(got) >= 4:
                    break
                print(f"    (훈수\u00b7느낌이 섞여 다시 묻는다 {_try + 1}/3)")
            if len(got) >= 4:
                d["sum5"] = got[:6]
                print(f"  여섯 줄 풀이 채움: {(d.get('title') or '')[:30]}")
        F.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")

    BODY.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    bad = [d for d in pub if len(d.get("sum5") or []) < 4 or len(d.get("words") or []) < 6]
    print(f"\n아직 재료가 모자란 기사 {len(bad)}")
    for d in bad:
        print(f"  {(d.get('title') or '')[:40]}")


if __name__ == "__main__":
    main()
