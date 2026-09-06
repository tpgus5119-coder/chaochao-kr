#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""기사 본문을 **설명하듯 여섯 줄**로 풀어 준다 → data/news_days.json 의 sum5 칸

왜 (대표님 지시 2026-08-31): "기사내용이 너무 빈약하다"(8/31) → 다섯 줄 → **여덟 줄**로 늘렸다(같은 날 재지시)
  지금 카드에 얹히던 intro 는 두 줄뿐이라 기사를 읽은 느낌이 안 났다.
  본문(1,500~3,500자)이 data/news_body.json 에 이미 있으므로 그것을 줄여 쓴다.

AI 는 중계 워커(tools/worker.js)를 부른다 — 열쇠는 스크립트가 아니라 워커 금고에 있다.
쓰기: python3 tools/news_sum5.py [--day 2026-08-28] [--local]
      --local 은 인터넷·열쇠 없이 이 맥의 Qwen 에게 시킨다
"""
import argparse, json, pathlib, re, subprocess, sys, time

R = pathlib.Path(__file__).resolve().parent.parent
URL = "https://viet-ai.chaochao-app.workers.dev"
ORIGIN = "https://tpgus5119-coder.github.io"

# --local 을 주면 이 맥의 LM Studio(Qwen)에게 시킨다. 인터넷도 열쇠도 필요 없다.
#   먼저 서버를 켠다:  ~/.lmstudio/bin/lms server start
#   확인:             curl http://localhost:1234/v1/models
LOCAL_URL = "http://localhost:1234/v1/chat/completions"
# 27B 는 이 맥(24GB)에서 스왑이 걸려 기사 하나에 10분이 넘는다(2026-08-31 실측).
# 9B 가 이 일에는 충분하고 훨씬 빠르다. 바꾸려면 이 한 줄만 고친다.
LOCAL_MODEL = "qwen/qwen3.5-9b"

ASK = (
    "너는 베트남 소식을 **옆에서 설명해 주는 사람**이다. 신문 기사를 그대로 옮기지 마라.\n"
    "아래 기사를 읽고, 읽는 사람에게 **말로 풀어 주듯** 여섯 줄로 알려 줘라.\n"
    "말투 (2026-08-31 대표님 지시)\n"
    " ① 존댓말이되 **'~요'** 로 끝낸다. '~습니다'·'~한다' 는 쓰지 마라\n"
    "    (○ 기록을 세웠어요 / 늘어날 것 같아요   × 달성했습니다 / 전망이다)\n"
    " ② 설명하듯 부드럽게. 딱딱한 신문 문장을 그대로 베끼지 마라\n"
    "    (× 누적 수출액 5천억 달러를 돌파했습니다\n"
    "     ○ 삼성이 베트남에서 만든 물건 수출이 5천억 달러를 넘었어요)\n"
    " ③ 어려운 말은 풀어 준다 (사후 신고 → 나중에 내야 하는 서류)\n"
    "규칙\n"
    " ④ 정확히 6줄. 한 줄은 **28자 안팎**으로 짧게. 길면 카드에서 두 줄로 접혀 답답해진다\n"
    " ⑤ 숫자·회사 이름·지역은 살린다. 다만 한 줄에 숫자를 두 개 넘게 넣지 마라\n"
    " ⑥ 첫 줄은 무슨 일이 있었는지, 마지막 줄은 **우리에게 무슨 뜻인지**\n"
    " ⑦ 같은 말을 되풀이하지 마라\n"
    ' 출력은 JSON 만: {"sum5": ["줄1","줄2","줄3","줄4","줄5","줄6"]}\n\n'
)


LOCAL = "--local" in sys.argv


# ("니다","어요") 를 넣어 두었더니 **아무 'ㅂ니다' 에나 붙어** '여깁니다' 가 '여깁어요',
# '열립니다' 가 '열립어요' 가 됐다 (2026-09-02 실측). 'ㅂ니다' 는 어간이 ㄹ 을 흘린 것인지
# (만듭니다=만들다) 아닌지 (여깁니다=여기다) 기계가 가릴 수 없다 —
# **바꾸지 말고 그냥 두고**, 뒤에서 '요' 로 안 끝난 줄을 버리고 다시 묻는다.
ENDFIX = [("합니다", "해요"), ("됩니다", "돼요"), ("있습니다", "있어요"),
          ("한다", "해요"), ("된다", "돼요"),
          ("이다", "이에요"), ("전망이다", "것 같아요"), ("예정이다", "예정이에요")]


def to_yo(t):
    """말투를 **'~요'로 굳힌다.** 지시문에 적어 뒀는데도 '~습니다' 가 섞여 나온다
    (대표님 지적 2026-09-02 '말투 통일해'). 부탁이 아니라 규칙으로 막는다.

    끝말만 보면 '~하려 합니다' 같은 것을 놓친다 — 정규식으로 **어떤 꼴이든** 잡는다."""
    t = t.rstrip().rstrip(".")

    # '~습니다' 를 '~어요' 로만 바꾸면 **모음이 안 맞는다** — '않습니다' 가 '않어요' 가 됐다
    # (2026-09-02 실측). 어간의 마지막 홀소리가 ㅏ·ㅗ 면 '아요', 아니면 '어요' 다.
    def _yo(stem):
        if stem.endswith("하"):
            return stem[:-1] + "해요"
        for ch in reversed(stem):
            if "가" <= ch <= "힣":
                v = ((ord(ch) - 0xAC00) // 28) % 21
                return stem + ("아요" if v in (0, 8) else "어요")   # ㅏ·ㅗ
        return stem + "어요"
    m = re.match(r"^(.*[가-힣])습니다$", t)
    if m:
        t = _yo(m.group(1))
    # 'ㅂ니다' 를 낱글자로 붙여 쓰지 않는다 — '보여줍니다' 가 '보여줍어요' 가 됐다
    t = re.sub(r"줍니다$", "줘요", t)
    t = re.sub(r"([가-힣])습니다$", r"\1어요", t)
    def _ida0(m):
        ch = m.group(1)
        has = (ord(ch) - 0xAC00) % 28 != 0 if "가" <= ch <= "힣" else True
        return ch + ("이에요" if has else "예요")
    t = re.sub(r"([가-힣])입니다$", _ida0, t)
    # 신문 문체 '~했다\u00b7됐다\u00b7밝혔다' 도 '요' 로 굳힌다
    # 'ㅂ니다' — 어간이 ㅣ·ㅐ·ㅔ·ㅚ 로 끝날 때만 바꾼다. 이때는 ㄹ 이 빠진 꼴일 수가 없어
    # 헷갈리지 않는다 (열립니다→열려요, 여깁니다→여겨요). 만듭니다(만들다) 같은 것은
    # 그냥 두고 뒤에서 버린 뒤 다시 묻는다.
    def _bnida(m):
        ch = m.group(1)
        if not ("가" <= ch <= "힣") or (ord(ch) - 0xAC00) % 28 != 17:   # 받침 ㅂ
            return m.group(0)
        base = chr(0xAC00 + ((ord(ch) - 0xAC00) // 28) * 28)           # 받침 뗀 글자
        v = ((ord(base) - 0xAC00) // 28) % 21
        JOIN = {20: 6, 1: 1, 5: 5, 11: 10}      # ㅣ→ㅕ, ㅐ→ㅐ, ㅔ→ㅔ, ㅚ→ㅙ
        if v not in JOIN:
            return m.group(0)
        cho = (ord(base) - 0xAC00) // 588
        return chr(0xAC00 + cho * 588 + JOIN[v] * 28) + "요"
    t = re.sub(r"([가-힣])니다$", _bnida, t)

    def _past(m):
        ch = m.group(1)
        # 받침이 ㅆ 이면 지난 일이다 — 했다\u00b7됐다\u00b7밝혔다\u00b7늘었다
        return ch + "어요" if (ord(ch) - 0xAC00) % 28 == 20 else m.group(0)
    t = re.sub(r"([가-힣])다$", _past, t)
    t = re.sub(r"있다$", "있어요", t)
    t = re.sub(r"없다$", "없어요", t)
    for a_, b_ in ENDFIX:
        if t.endswith(a_):
            t = t[: -len(a_)] + b_
            break
    # 그래도 남은 딱딱한 끝말
    t = re.sub(r"합니다$", "해요", t)
    # 받침이 있으면 '이에요', 없으면 '예요' — '기회이에요' 는 어색하다
    def _ida(m):
        ch = m.group(1)
        has = (ord(ch) - 0xAC00) % 28 != 0 if "가" <= ch <= "힣" else True
        return ch + ("이에요" if has else "예요")
    t = re.sub(r"([가-힣])입니다$", _ida, t)
    t = re.sub(r"됩니다$", "돼요", t)
    t = re.sub(r"(한|된|일|할|될)\s*것입니다$", r"\1 거예요", t)
    return t


def tidy(x):
    """숫자와 단위가 벌어지는 버릇을 고친다 — '5 억 5 천만' · '2035 년' · '40% 를' (실측).
    붙이는 것은 **수를 이루는 말까지만**이다. '달러·원' 같은 화폐는 띄어 쓴다."""
    t = str(x).strip()
    t = re.sub(r"(\d)\s+(월|일|년|시|분|초|%|천|백|십|만|억|조)", r"\1\2", t)
    t = re.sub(r"(천|백|십|만|억)\s+(만|억|조)", r"\1\2", t)
    t = re.sub(r"(\d)\s+(명|개|원|동|대|건|배|위|차)", r"\1\2", t)
    t = re.sub(r"(%)\s+(을|를|로|와|과|의|에|이|가)", r"\1\2", t)
    # 옮기다 생긴 겹침 — '집집에'·'집집방'. 다만 **겹쳐 쓰는 우리말은 지킨다**
    # (꼼꼼히·각각·번번이·나날이…). 규칙을 넓게 잡았더니 '각의 사람'이 됐다.
    KEEP = ('꼼꼼', '각각', '번번', '나날', '겹겹', '층층', '곳곳', '집집마다',
            '사사', '점점', '조금조금', '차차', '가끔가끔', '두둑', '반반')
    def _dedup(m):
        w = m.group(0)
        return w if any(k in w for k in KEEP) else m.group(1)
    t = re.sub(r"([가-힣])\1(?=[가-힣])", _dedup, t)
    return to_yo(re.sub(r"\s{2,}", " ", t).strip())


def ask(title, body, tries=4):
    # 로컬 모델은 문맥이 좁다 — 본문을 더 짧게 준다
    p = ASK + f"제목: {title}\n본문:\n{body[:1600 if LOCAL else 3500]}"
    if LOCAL:
        # **max_tokens 를 넉넉히 줘야 한다.** 이 모델은 답하기 전에 길게 '생각'하는데,
        #   그 생각도 토큰을 먹는다. 좁게 주면 생각만 하다 끝나 **답이 빈 채로** 돌아온다
        #   (2026-08-31 실측: 200토큰을 줬더니 199가 생각, 답은 ''. 3000을 주니 제대로 답했다)
        req = json.dumps({"model": LOCAL_MODEL, "temperature": 0.4, "max_tokens": 3000,
                          # 생각을 미리 닫아 둔다 — 안 그러면 3,000토큰을 생각에 다 쓰고
                          # 답이 빈 채로 돌아온다 (tools/ai.py 의 NOTHINK 와 같은 수법)
                          "messages": [{"role": "user", "content": p},
                                       {"role": "assistant",
                                        "content": "<think>\n\n</think>\n\n"}]})
        cmd = ["curl", "-sS", "-X", "POST", LOCAL_URL,
               "-H", "Content-Type: application/json", "--data-binary", "@-"]
    else:
        req = json.dumps({"contents": [{"parts": [{"text": p}]}]})
        cmd = ["curl", "-sS", "-X", "POST", URL, "-H", "Content-Type: application/json",
               "-H", f"Origin: {ORIGIN}", "--data-binary", "@-"]
    for k in range(tries):
        try:
            r = subprocess.run(cmd, input=req, capture_output=True, text=True,
                               timeout=600 if LOCAL else 200).stdout
        except Exception:
            time.sleep(2 * (k + 1)); continue
        t = r
        try:
            j = json.loads(r)
            t = (j["choices"][0]["message"]["content"] if LOCAL
                 else j["candidates"][0]["content"]["parts"][0]["text"])
        except Exception: pass
        # 로컬 모델로 바꿔 쓸 때를 대비해 생각 부분을 떼어 낸다
        t = re.sub(r"(?s)<think>.*?</think>", "", t)
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try:
                got = json.loads(m.group(0)).get("sum5")
                if isinstance(got, list) and len(got) >= 4:
                    return [tidy(x) for x in got[:6] if str(x).strip()]
            except Exception:
                pass
        time.sleep(1.5 * (k + 1))
    return None


def main():
    a = argparse.ArgumentParser(); a.add_argument("--day"); a.add_argument("--force", action="store_true")
    a.add_argument("--local", action="store_true", help="이 맥의 LM Studio(Qwen)에게 시킨다")
    a = a.parse_args()

    bp = R / "data" / "news_body.json"
    if not bp.exists():
        print("data/news_body.json 이 없다 — fetch_news.py 를 먼저 돌려라"); return
    bodies = {x["t"]: x.get("body", "") for x in json.loads(bp.read_text(encoding="utf-8"))["picked"]}

    dp = R / "data" / "news_days.json"
    D = json.loads(dp.read_text(encoding="utf-8"))
    days = D["days"]
    target = [d for d in days if (not a.day or d.get("ts") == a.day)]

    done = 0
    for d in target:
        if d.get("sum5") and not a.force:
            continue
        body = bodies.get(d.get("title", ""))
        if not body or len(body) < 200:
            print("  본문 없음:", d.get("title", "")[:30]); continue
        got = ask(d["title"], body)
        if not got:
            print("  실패:", d.get("title", "")[:30]); continue
        d["sum5"] = got
        done += 1
        print(f"  {d.get('theme','')} — {len(got)}줄", flush=True)

    if done:
        dp.write_text(json.dumps(D, ensure_ascii=False), encoding="utf-8")
    print(f"여섯 줄 풀이 {done}편 만듦")


# 불러오기만 할 때는 돌지 않는다 — tidy 를 가져다 쓰는 곳이 있다
if __name__ == "__main__":
    main()
