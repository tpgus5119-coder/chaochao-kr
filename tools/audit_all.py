#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**전체 검수** — 낱말·소리·그림·발음·목차를 하나씩 대조한다 → docs/audit.md

대표님 지시 (2026-08-30): "하나하나 천천히 꼼꼼히 다 검수해."
숫자로만 말한다. 못 고친 것은 못 고쳤다고 적는다.
쓰기: python3 tools/audit_all.py
"""
import collections, hashlib, json, os, pathlib, re, sys, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr

O = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
AIDX = json.loads((R / "data" / "audio_index.json").read_text(encoding="utf-8"))
VI = re.compile(r"[ăâđêôơưÀ-ỹ]", re.I)
KO = re.compile(r"[가-힣]")
out = []
def say(t=""): print(t); out.append(t)

def walk(v):
    for t in (v.get("tracks") or [v]):
        for c in t["chapters"]:
            for l in c["lessons"]: yield from l["words"]

WORDS, ALT = [], []
for v in O["vols"]:
    for w in walk(v):
        WORDS.append(w)
        for a in (w.get("alt") or []): ALT.append((w, a))
WORDS += O.get("gramwords", [])
say(f"# 검수 — 과정 낱말 {len(WORDS)}장 · 같은 뜻으로 붙은 낱말 {len(ALT)}개\n")

# ── ① 낱말 자체 (오타·거짓)
say("## ① 낱말")
bad = collections.defaultdict(list)
for w in WORDS:
    vi, ko = w["vi"].strip(), w["ko"].strip()
    if not vi or not ko: bad["빈 칸"].append(w)
    if re.search(r"[A-Za-z]{3,}", ko): bad["뜻에 영어가 남음"].append(w)
    if re.search(r"[fjwzFJWZ]", vi): bad["베트남어에 없는 글자(f·j·w·z)"].append(w)
    if vi.count("(") != vi.count(")"): bad["괄호가 안 맞음"].append(w)
    if len(vi.split()) > 5: bad["낱말이 아니라 문장 같음"].append(w)
    if len(ko) > 24: bad["뜻이 너무 긺"].append(w)
    if re.search(r"[a-z][A-ZĐ]", vi): bad["붙어 버린 것"].append(w)
    if not VI.search(vi) and not re.fullmatch(r"[a-zA-Z0-9 \-]+", vi): bad["이상한 글자"].append(w)
for k, v in sorted(bad.items(), key=lambda x: -len(x[1])):
    say(f"  {len(v):>4}  {k}")
    for w in v[:5]: say(f"        {w['vi'][:26]:<28}{w['ko'][:24]}")
if not bad: say("  이상 없음")

# 겹침
key = lambda v: re.sub(r"\s+", " ", U.normalize("NFC", v).lower().strip(" .,;:!?"))
c = collections.Counter(key(w["vi"]) for w in WORDS)
dup = [(k, n) for k, n in c.items() if n > 1]
say(f"\n  같은 낱말이 두 번 들어간 것: {len(dup)}개")
for k, n in dup[:8]: say(f"        {n}× {k}")

# ── ② 소리
say("\n## ② 소리 (TTS)")
def h(t): return AIDX.get(t)
dirs = {"북부 여": "f", "북부 남": "m", "남부 여": "sf", "남부 남": "sm"}
files = {k: {p[:-4] for p in os.listdir(R / "audio" / d / "n")} for k, d in dirs.items()}
for what, items in [("낱말", [w["vi"] for w in WORDS] + [a["vi"] for _, a in ALT]),
                    ("예문", [w["ex"]["vi"] for w in WORDS if w.get("ex")])]:
    items = [x for x in items if x]
    say(f"  {what} {len(items)}개")
    for k in dirs:
        miss = sum(1 for t in items if not h(t) or h(t) not in files[k])
        say(f"      {k}: 있음 {len(items)-miss} · **없음 {miss}**")

# ── ③ 그림
say("\n## ③ 그림")
have = {p.name for p in (R / "img").glob("*.webp")}
withimg = [w for w in WORDS if w.get("img")]
broken = [w for w in withimg if w["img"] not in have]
say(f"  그림 붙은 낱말 {len(withimg)} · 없는 낱말 {len(WORDS)-len(withimg)}")
say(f"  **파일이 없는데 붙어 있는 것 {len(broken)}개**")
for w in broken[:5]: say(f"        {w['vi']} → {w['img']}")

# ── ④ 발음 표기
say("\n## ④ 발음 표기")
nokr = [w for w in WORDS if not w.get("kr")]
nokrs = [w for w in WORDS if not w.get("krs")]
same = [w for w in WORDS if w.get("kr") and w.get("kr") == w.get("krs")]
say(f"  북부 발음 없음 {len(nokr)} · 남부 발음 없음 {len(nokrs)}")
say(f"  북부와 남부가 같은 낱말 {len(same)} ({len(same)*100//max(1,len(WORDS))}%) — 자음이 안 겹치면 같은 게 맞다")
wrong = [w for w in WORDS if w.get("kr") and w["kr"] != vi_kr.word(w["vi"])]
say(f"  **도구와 다른 발음 {len(wrong)}개** (손으로 적힌 것)")
for w in wrong[:5]: say(f"        {w['vi']:<18}{w['kr']:<16}도구: {vi_kr.word(w['vi'])}")

# ── ⑤ 예문
say("\n## ⑤ 예문")
noex = [w for w in WORDS if not w.get("ex")]
say(f"  예문 있음 {len(WORDS)-len(noex)} · **없음 {len(noex)}**")
exbad = [w for w in WORDS if w.get("ex") and key(w["vi"]) not in key(w["ex"]["vi"])]
say(f"  **낱말이 예문에 안 들어 있는 것 {len(exbad)}개**")
for w in exbad[:5]: say(f"        {w['vi']:<18}{w['ex']['vi'][:34]}")

# ── ⑥ 목차
say("\n## ⑥ 목차")
for i, v in enumerate(O["vols"], 2):
    if v["kind"] == "life":
        n = sum(len(l["words"]) for c in v["chapters"] for l in c["lessons"])
        ls = sum(len(c["lessons"]) for c in v["chapters"])
        say(f"  {i}권 일상 · {len(v['chapters'])}챕터 · {ls}레슨 · {n}낱말")
    else:
        say(f"  {i}권 직무 · 갈래 {len(v['tracks'])} · {sum(t['words'] for t in v['tracks'])}낱말")
        for t in v["tracks"]:
            ls = sum(len(c["lessons"]) for c in t["chapters"])
            odd = " ← 레슨 하나뿐" if ls <= 1 else ""
            say(f"      {t['track']:<20}{t['words']:>4}낱말 {ls:>2}레슨{odd}")
(R / "docs" / "audit.md").write_text("\n".join(out), encoding="utf-8")
say("\n→ docs/audit.md 에 적었습니다")
