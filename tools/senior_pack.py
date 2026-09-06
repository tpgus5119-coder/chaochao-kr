#!/usr/bin/env python3
"""선배 시험 자료를 앱이 실을 꼴로 굳힌다 → data/senior.json

무엇을 넣나 (대표님 지시)
  · **20기만** 넣는다. 대표님은 22기다 — 19기보다 20기가 가깝고, 4,000개는 못 외운다.
  · 19기에도 나온 낱말에는 **「중요」** 표를 붙인다(w=1).
    두 기수는 서로 모르는 채 각자 시험을 봤는데도 겹친다 — 내가 매긴 등급이 아니라
    자료가 스스로 말하는 증거다.
  · 19기에만 있는 낱말은 넣지 않는다.

차례는 어떻게 정했나 — **5일 + 주간 1** (대표님 지시, 자료가 그렇다고 말한다)
  일일시험은 하루 30낱말이고 다섯 번마다 토요일에 주간시험을 본다.
  겹친 것을 걷어내니 일일 94회 · 주간 19회 = 4.9 : 1 로, 5:1 이 맞았다.

왜 처음에는 60·90 낱말짜리 회차가 나왔나 — **내가 두 번 담았다.**
  시험 파일은 시트가 둘이다: 문제지(Kiểm tra)와 정답지(Đáp án).
  둘 다 읽어서 한 회차에 겹쳐 담았다. 낱말(vi)로 겹침을 걷어내면 75회가 정확히 30개다.
  그래도 30을 넘는 회차는 한 파일에 두 회가 든 것이라 **30개씩 쪼갠다.**
  쪼갠 뒤 번호를 1부터 다시 매긴다 — 원래 번호에는 빠진 것(63·65·76 …)이 있어 들쭉날쭉했다.

낱말은 한 벌만 두고 번호로 가리킨다 — 같은 낱말이 일일과 주간에 거듭 나온다.
"""
import json, pathlib, re, unicodedata

R = pathlib.Path(__file__).resolve().parent.parent
D = R / "data"
nf = lambda t: unicodedata.normalize("NFC", t.strip())

HAN = re.compile(r"[가-힣]")
ASCII = re.compile(r"[A-Za-z][A-Za-z0-9 .,\'’\-]*")
def kor(t):
    """뜻에서 영어를 걷어낸다 — 한국어만 남긴다.

    왜: 선배 자료의 뜻은 'cell phone/ 휴대폰', '주소 address', '아내 – wife' 처럼
    영어가 섞여 있는데 **일부만** 그렇다. 그러면 보기 넷 중 하나만 영어가 붙어
    뜻을 몰라도 답이 보인다. 시험 화면을 실제로 열어 보고 알았다(2026-08-29):
    'điện thoại di động' 문제의 보기가 [회의하다 / cell phone/ 휴대폰 / 가게·식당 / 권리·복리]
    였고 영어가 붙은 것이 곧 정답이었다.

    한국어가 하나도 없는 뜻(고유명사 등)은 손대지 않는다 — 지우면 뜻이 사라진다.
    괄호는 안에 한국어가 있으면 그대로 둔다('반꼼 (베트남 떡)').
    잃는 것: 'manteau' 같은 외래어 어원 표기. 답이 새는 것보다는 낫다."""
    parts = [x.strip() for x in t.split("/")]
    keep = [x for x in parts if HAN.search(x)]
    s = " / ".join(keep) if keep else t
    if not HAN.search(s):
        return t.strip()
    s = re.sub(r"\(([^)]*)\)", lambda m: m.group(0) if HAN.search(m.group(1)) else "", s)
    s = ASCII.sub("", s)
    if s.count("(") != s.count(")"):          # 짝 잃은 괄호만 턴다
        s = re.sub(r"[()]", "", s)
    s = re.sub(r"\s*[–\-]\s*$", "", s)
    s = re.sub(r"\s*\(\s*\)", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip(" ,/–-")
    return s if HAN.search(s) else t.strip()
low = lambda t: nf(t).lower()

def load(f):
    return json.loads((D / f).read_text(encoding="utf-8"))["sets"]

# 19기에 나온 낱말 — 「중요」 표를 붙일 근거
vi19 = {low(w["vi"]) for s in load("_senior_words-19.json") for w in s["words"]
        if (w.get("vi") or "").strip() and (w.get("ko") or "").strip()}
# 앱이 이미 가르치는 낱말 — 새로 외울 것이 몇인지 학습자가 알게
taught = {low(w["vi"]) for d in json.loads((D / "days.json").read_text(encoding="utf-8"))["days"]
          for w in (d.get("words") or []) if w.get("vi")}

PER = 30                                  # 하루 30낱말 — 자료의 75회가 정확히 이 값이다
EVERY = 5                                 # 다섯 번마다 주간시험

def clean(words):
    """한 회차의 낱말 — 답이 빈 줄과 겹친 줄을 걷어낸다."""
    seen, out = set(), []
    for w in words:
        vi, ko = nf(w.get("vi") or ""), kor(nf(w.get("ko") or ""))
        if not vi or not ko:
            continue                      # 문제지 쪽은 답이 비어 있다
        if low(vi) in seen:
            continue                      # 정답지와 겹치는 줄
        seen.add(low(vi))
        out.append((vi, ko))
    return out

daily, weekly = [], []
for st in load("_senior_words.json"):
    ws = clean(st["words"])
    if len(ws) < 5:
        continue
    if st["kind"] == "일일":
        ch = [ws[k:k + PER] for k in range(0, len(ws), PER)]   # 한 파일에 두 회가 들었으면 쪼갠다
        if len(ch) > 1 and len(ch[-1]) < 5:
            tail = ch.pop(); ch[-1] += tail   # 짧은 꼬리는 앞에 붙인다 — 낱말을 안 버린다
        for c in ch:
            if c: daily.append((st["no"], c))
    elif st["kind"] == "주간":
        weekly.append((st["no"], ws))
    # `4권 베트남어 교재_단어.xlsx` 는 담지 않는다 (2026-08-29, 대표님 지시).
    # 시험지가 아니라 **시판 교재의 단어장**을 가나다순 그대로 옮긴 파일이다.
    #   ① 유료 앱에 시판 교재의 목록을 순서까지 그대로 싣는 것은 위험하다
    #   ② "1년 과정이 실제로 시험 본 낱말" 이라는 명분이 깨진다 — 시험에 안 나온 말이다
    #   ③ 가나다순 30개 묶음은 학습 단위가 못 된다(모음 1 = A로 시작하는 말 30개)
    # 원본 파일은 그대로 두므로 필요하면 되살릴 수 있다.
daily.sort(key=lambda x: x[0])
weekly.sort(key=lambda x: x[0])

# 5일 + 주간 1 로 규칙적으로 섞는다. 번호는 1부터 새로 매긴다.
raw, wi = [], 0
for n, (_, ws) in enumerate(daily, 1):
    raw.append({"k": "d", "no": n, "ws": ws})
    if n % EVERY == 0 and wi < len(weekly):
        wi += 1
        raw.append({"k": "w", "no": wi, "ws": weekly[wi - 1][1]})
while wi < len(weekly):                   # 남은 주간시험은 뒤에 이어 붙인다
    wi += 1
    raw.append({"k": "w", "no": wi, "ws": weekly[wi - 1][1]})

# ── 낱말 한 벌 + 번호로 가리키기
words, idx, sets = [], {}, []
for r in raw:
    ns = []
    for vi, ko in r["ws"]:
        k = (vi, ko)
        if k not in idx:
            idx[k] = len(words)
            words.append([vi, ko, (1 if low(vi) in vi19 else 0) + (2 if low(vi) in taught else 0)])
        ns.append(idx[k])
    sets.append({"k": r["k"], "no": r["no"], "w": ns})

out = {"note": "20기가 1년 동안 실제로 시험 본 낱말만. 하루 30낱말 · 다섯 번마다 주간시험. "
               "표 t: 1=19기에도 나옴(중요) · 2=앱에서 이미 배움 · 3=둘 다.",
       "words": words, "sets": sets}
p = D / "senior.json"
p.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
# ── 검산 — 숫자를 눈으로 믿지 않는다 (2026-08-29 대표님 지적 뒤에 박아 둠)
#    두 번 틀렸다: ① 모음 묶음을 통째로 빠뜨려 722개가 사라졌고
#                 ② 꼬리 조각을 버려 2개가 더 사라졌다. 둘 다 화면에는 안 보였다.
src20 = {low(w["vi"]) for st in load("_senior_words.json") if st["kind"] in ("일일", "주간")
         for w in st["words"] if (w.get("vi") or "").strip() and (w.get("ko") or "").strip()}
got = {low(w[0]) for w in words}
gotimp = {low(w[0]) for w in words if w[2] & 1}
lost = src20 - got
assert not lost, f"시험에 나온 낱말 {len(lost)}개를 빠뜨렸다: {sorted(lost)[:8]}"
want = src20 & vi19
assert gotimp == want, f"「중요」가 안 맞는다 — 있어야 {len(want)}, 붙은 것 {len(gotimp)}"
print(f"검산 통과 — 20기가 **시험 본** 낱말 {len(got)}개 모두 담김 · 「중요」 {len(gotimp)}개 = 19기와 겹치는 말 그대로")

imp = sum(1 for w in words if w[2] & 1)
kno = sum(1 for w in words if w[2] & 2)
print(f"낱말 {len(words)}개 · 「중요」 {imp}개 · 앱에서 이미 배운 것 {kno}개")
print(f"묶음 {len(sets)}개 (일일 {sum(1 for s in sets if s['k']=='d')} · "
      f"주간 {sum(1 for s in sets if s['k']=='w')} · 모음 {sum(1 for s in sets if s['k']=='x')})")
print(f"파일 {p.stat().st_size/1024:.0f}KB")
print("\n차례 앞 14개:", [f"{'일일' if s['k']=='d' else '주간'}{s['no']}({len(s['w'])})" for s in sets[:14]])
