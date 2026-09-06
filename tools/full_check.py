#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**전체 점검** — 목차·낱말·소리·그림·앱·카드뉴스를 한 번에 센다 → docs/점검.md

대표님 지시 (2026-09-02): "단어가 목차에 알맞게 들어가 있는지, 그 목차 안에서도
낱말의 순서, 목차 리스트, 목차의 순서, tts, 이미지, 어플 작동 등 모든 것을 점검해줘."

**AI 를 안 쓴다.** 세면 되는 일이다 — 공짜이고 늘 같은 답이 나온다.
"""
import hashlib, json, pathlib, re, sys, unicodedata as U
from collections import Counter

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr

key = lambda t: hashlib.sha1(t.encode()).hexdigest()[:12]
n = lambda s: U.normalize("NFC", str(s)).strip()
out = []
def say(x=""): out.append(x); print(x, flush=True)

D = json.loads((R / "data" / "days.json").read_text(encoding="utf-8"))
O = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
days = D.get("days", [])

say("# 전체 점검\n")

# ── 1. 목차
say("## 1. 목차 (하루 5분 = 학습 2권)\n")
say(f"- 날 수 **{len(days)}** · 낱말 **{sum(len(x.get('words') or []) for x in days)}**")
noth = [x for x in days if not (x.get("theme") or "").strip()]
say(f"- 이름 없는 날: **{len(noth)}**" + (f" {[x.get('day') for x in noth][:5]}" if noth else " ✓"))
th = Counter((x.get("theme") or "").strip() for x in days)
dup = [t for t, c in th.items() if c > 1]
say(f"- 이름이 겹치는 날: **{len(dup)}**" + (f" {dup[:6]}" if dup else " ✓"))
# 차례 — day 값이 커지는가
ds = [x.get("day") for x in days]
num = [d for d in ds if isinstance(d, (int, float))]
say(f"- 날 번호가 차례대로인가: {'✓' if num == sorted(num) else '**아니오** — 뒤섞여 있다'}")
bad_seq = [(a, b) for a, b in zip(num, num[1:]) if b < a]
if bad_seq:
    say(f"  - 거꾸로 가는 곳 {len(bad_seq)}군데: {bad_seq[:5]}")

# ── 2. 낱말이 제 날에 있나 (한 날 = 한 주제)
say("\n## 2. 낱말 수와 차례\n")
c10 = Counter(len(x.get("words") or []) for x in days)
say(f"- 한 날 낱말 수 분포: {dict(sorted(c10.items()))}")
odd = [(x.get("day"), len(x.get("words") or [])) for x in days if len(x.get("words") or []) != 10]
say(f"- 10개가 아닌 날: **{len(odd)}**" + (f" {odd[:8]}" if odd else " ✓"))
seen, dupw = {}, []
for x in days:
    for w in (x.get("words") or []):
        k = n(w.get("vi", "")).lower()
        if k in seen:
            dupw.append((w.get("vi"), seen[k], x.get("day")))
        else:
            seen[k] = x.get("day")
say(f"- 여러 날에 겹쳐 나오는 낱말: **{len(dupw)}**" + (f" 보기 {dupw[:5]}" if dupw else " ✓"))

# ── 3. 뜻·발음
say("\n## 3. 뜻과 발음\n")
allw = [w for x in days for w in (x.get("words") or [])]
noko = [w["vi"] for w in allw if not (w.get("ko") or "").strip()]
say(f"- 뜻이 빈 낱말: **{len(noko)}**" + (f" {noko[:6]}" if noko else " ✓"))
badko = [w["vi"] for w in allw if re.search(r"[^가-힣ㄱ-ㆎ0-9 ·()~,./%\-·]", w.get("ko") or "")]
say(f"- 뜻에 한글 아닌 글자: **{len(badko)}**" + (f" {badko[:6]}" if badko else " ✓"))
wrong = [(w["vi"], w.get("kr_read"), vi_kr.word(w["vi"]))
         for w in allw if w.get("kr_read") and vi_kr.word(w["vi"])
         and n(w["kr_read"]) != n(vi_kr.word(w["vi"]))]
say(f"- 발음이 우리 도구와 다른 낱말: **{len(wrong)}**" + (f" 보기 {wrong[:5]}" if wrong else " ✓"))

# ── 4. 소리
say("\n## 4. 소리 (북부 남녀 · 남부 남녀)\n")
V = {"f": "북부 여", "m": "북부 남", "sf": "남부 여", "sm": "남부 남"}
miss = {v: [] for v in V}
for w in allw:
    k = key(w["vi"])
    for v in V:
        if not (R / f"audio/{v}/n/{k}.mp3").exists():
            miss[v].append(w["vi"])
for v, nm in V.items():
    say(f"- {nm}: 없는 소리 **{len(miss[v])}**" + (f" {miss[v][:5]}" if miss[v] else " ✓"))
idx = R / "data" / "audio_index.json"
if idx.exists():
    A = json.loads(idx.read_text(encoding="utf-8"))
    nm2 = [w["vi"] for w in allw if w["vi"] not in A]
    say(f"- 소리 목록에 없는 낱말: **{len(nm2)}**" + (f" {nm2[:5]}" if nm2 else " ✓"))

# ── 5. 그림
say("\n## 5. 그림\n")
noimg = [w["vi"] for w in allw if not w.get("img")]
gone = [w["img"] for w in allw if w.get("img") and not (R / "img" / w["img"]).exists()]
say(f"- 그림이 없는 낱말: **{len(noimg)}** / {len(allw)}")
say(f"- 파일이 사라진 그림: **{len(gone)}**" + (f" {gone[:5]}" if gone else " ✓"))
used = Counter(w["img"] for w in allw if w.get("img"))
many = [(i, c) for i, c in used.items() if c > 3]
say(f"- 한 그림이 넷 이상 낱말에 붙음: **{len(many)}**" + (f" {many[:5]}" if many else " ✓"))
see = R / "data" / "_imgsee.json"
if see.exists():
    S = json.loads(see.read_text(encoding="utf-8"))
    say(f"- 눈으로 본 그림 {len(S)} · 뜻이 안 보인다 **{sum(1 for x in S.values() if not x['ok'])}**")

# ── 5-2. 두 낱말이 합쳐졌나 (사전에 한 표제어로 있나)
say("\n## 5-2. 한 칸에 낱말 하나인가\n")
W = R / "data" / "_vi_words.json"
if W.exists():
    known = {n(x).lower() for x in json.loads(W.read_text(encoding="utf-8"))}
    ipa = R / "data" / "_vi_ipa.json"
    if ipa.exists():
        known |= {n(x).lower() for x in json.loads(ipa.read_text(encoding="utf-8"))}
    def seg(t):
        ws2, o2, i2 = n(t).split(), [], 0
        while i2 < len(ws2):
            for j in range(min(len(ws2), i2 + 4), i2, -1):
                c2 = " ".join(ws2[i2:j])
                if c2.lower() in known:
                    o2.append(c2); i2 = j; break
            else:
                return None
        return o2 if len(o2) > 1 else None
    notword = [w["vi"] for w in allw if n(w["vi"]).lower() not in known]
    split = [(v, seg(v)) for v in notword]
    can = [x for x in split if x[1]]
    say(f"- 사전에 한 낱말로 없는 것: **{len(notword)}** / {len(allw)}")
    say(f"  - 그중 **여러 낱말이 합쳐진 것**: **{len(can)}**")
    for v, ps in can[:12]:
        say(f"    - {v} → {' + '.join(ps)}")
    say(f"  - 쪼개지지도 않는 것: **{len(notword)-len(can)}** (사전에 없는 말이거나 구어)")
else:
    say("- 우리 사전 파일이 없다 — tools/dict_build.py 를 돌려라")

# ── 5-3. 낱말이 그 날 주제에 어울리나 (그림 검수 결과로 갈음)
say("\n## 5-3. 그림이 뜻을 보여 주나 (눈 달린 모델)\n")
if see.exists():
    S2 = json.loads(see.read_text(encoding="utf-8"))
    byimg = {w["img"]: (x.get("theme"), w) for x in days for w in (x.get("words") or []) if w.get("img")}
    bad2 = [(byimg[k][0], byimg[k][1]["vi"], v["ko"]) for k, v in S2.items()
            if not v["ok"] and k in byimg]
    say(f"- 하루 5분 그림 중 '뜻이 안 보인다': **{len(bad2)}**")
    from collections import Counter as _C
    top = _C(t for t, _, _ in bad2).most_common(8)
    say(f"  - 많이 걸린 날: {top}")

# ── 6. 앱 자료
say("\n## 6. 앱\n")
for f in ("app.js", "index.html", "style.css", "sw.js"):
    say(f"- {f}: {'✓ 있음' if (R / f).exists() else '**없음**'}")
try:
    for f in ("data/order.json", "data/days.json", "data/news_days.json", "data/audio_index.json"):
        json.loads((R / f).read_text(encoding="utf-8"))
    say("- 앱이 읽는 자료 네 개: **모두 정상**")
except Exception as e:
    say(f"- 자료가 깨졌다: **{e}**")
vols = [v.get("title") or v.get("kind") for v in O["vols"]]
say(f"- 학습 권 구성: {vols}")

# ── 7. 카드뉴스
say("\n## 7. 카드뉴스\n")
N = json.loads((R / "data" / "news_days.json").read_text(encoding="utf-8"))["days"]
pub = [d for d in N if d.get("pub")]
say(f"- 펴낼 기사 **{len(pub)}**")
bad5 = [(d.get("title") or "")[:24] for d in pub if len(d.get("sum5") or []) < 4]
say(f"- 여섯 줄 풀이가 모자란 기사: **{len(bad5)}**" + (f" {bad5}" if bad5 else " ✓"))
notyo = []
for d in pub:
    for l in (d.get("sum5") or []):
        if re.search(r"(습니다|합니다|입니다|된다|한다|이다)\.?$", l.strip()):
            notyo.append(l[:26])
say(f"- 말투가 '~요' 가 아닌 줄: **{len(notyo)}**" + (f" {notyo[:4]}" if notyo else " ✓"))
site = Counter((d.get("u") or "").split("/")[2].replace("www.", "") for d in pub)
say(f"- 출처별: {dict(site)}")
say(f"  - 한 곳이 5건을 넘나: {'**넘음**' if any(c > 5 for c in site.values()) else '✓'}")
w6 = [(d.get("title") or "")[:22] for d in pub if len(d.get("words") or []) < 6]
say(f"- 낱말이 여섯 개가 안 되는 기사: **{len(w6)}**" + (f" {w6}" if w6 else " ✓"))
dl = [(d.get("title") or "")[:22] for d in pub if len(((d.get("dialog") or {}).get("lines") or [])) < 2]
say(f"- 대화가 두 줄이 안 되는 기사: **{len(dl)}**" + (f" {dl}" if dl else " ✓"))
cat = Counter(d.get("cat") for d in pub)
say(f"- 갈래별: {dict(cat)}")
krbad = []
for d in pub:
    for w in (d.get("words") or []):
        good = vi_kr.word(w.get("vi") or "")
        if good and n(w.get("kr_read") or "") != n(good):
            krbad.append(w.get("vi"))
say(f"- 카드 낱말 발음이 틀린 것: **{len(krbad)}**" + (f" {krbad[:5]}" if krbad else " ✓"))

(R / "docs" / "점검.md").write_text("\n".join(out), encoding="utf-8")
say("\n→ docs/점검.md 에 적었다")
