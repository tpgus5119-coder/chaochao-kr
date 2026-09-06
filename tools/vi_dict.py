#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""낱말마다 **사전에서** 지방별 발음기호를 받아 둔다 → data/_vi_ipa.json

왜 (대표님 지적, 2026-08-29): 앱의 발음 표기는 내가 손으로 타이핑한 것이고
사전에서 확인한 적이 없다. 실제로 틀린 것이 나왔다 — răng 을 '랑'이라 적었는데
사전은 하노이 [zaŋ], 즉 'ㅈ' 이다. 남부 표기는 아예 없었다.

어디서: 영어 위키낱말사전. 베트남어를 **하노이(북) · 후에(중) · 사이공(남)** 세 발음으로 싣는다.
       한 번에 여러 개를 물으면 글이 잘려서 **하나씩** 묻는다.
없는 낱말: 지어내지 않는다. 없다고 적어 두고 규칙 변환기(vi_kr.py) 값을 쓴다.

받아 둔 것은 파일에 쌓이므로 중간에 끊겨도 이어서 돌리면 된다.
쓰기: python3 tools/vi_dict.py [--limit N]
"""
import argparse, html, json, pathlib, re, subprocess, sys, time, unicodedata

R = pathlib.Path(__file__).resolve().parent.parent
OUT = R / "data" / "_vi_ipa.json"
API = "https://en.wiktionary.org/w/api.php"
# 태그를 걷어내면 괄호 안에 공백이 남는다 — '( Hà Nội ) IPA ( key ) : [ … ]'
PAT = re.compile(r"\(\s*(Hà Nội|Huế|Saigon)\s*\)\s*IPA\s*\(\s*key\s*\)\s*:\s*\[([^\]]+)\]")
nfc = lambda s: unicodedata.normalize("NFC", s.strip())


def ask(title):
    q = f"{API}?action=parse&format=json&prop=text&page=" + subprocess.run(
        [sys.executable, "-c", "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))", title],
        capture_output=True, text=True).stdout.strip()
    # 위키미디어는 **이름표(User-Agent)를 요구한다.** 없이 두들기면 막는다.
    # 실제로 막혔다(2026-08-29): 0.12초 간격으로 쏘다가 600개가 '사전에 없음'으로
    # 잘못 기록됐다. 막힌 것과 없는 것은 **다른 일**이라 반드시 갈라야 한다.
    for attempt in range(4):
        r = subprocess.run(["curl", "-s", "--max-time", "30",
                            "-H", "User-Agent: chaochao-vocab/1.0 (study app; contact via github tpgus5119-coder/chaochao)",
                            q], capture_output=True, text=True)
        if "too many requests" in r.stdout.lower() or not r.stdout.strip():
            time.sleep(5 * (attempt + 1))          # 막혔으면 쉬었다 다시
            continue
        break
    else:
        return None                                 # 끝내 못 받음 — **없다고 적지 않는다**
    try:
        t = json.loads(r.stdout)["parse"]["text"]["*"]
    except Exception:
        if '"missing"' in r.stdout or '"invalid"' in r.stdout:
            return {}                               # 쪽이 진짜 없다
        return None
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    # 언어 칸을 자르지 않는다 — 맨 위 목차에 'Vietnamese' 가 있어서 잘못 잘렸다.
    # 하노이·후에·사이공은 베트남어 자리에만 나오는 말이라 자를 까닭이 없다.
    return {a: b for a, b in PAT.findall(t)} or {}


def variants(w):
    """같은 낱말의 다른 적기 — 사전에 하나만 실려 있을 때가 있다.
       베트남어는 성조 부호를 첫 모음에 얹기도 하고 뒤 모음에 얹기도 한다
       (khỏe ↔ khoẻ · hòa ↔ hoà). 실제로 khỏe 가 안 잡혀서 넣었다."""
    out = [w]
    d = unicodedata.normalize("NFD", w)
    marks = "\u0300\u0301\u0303\u0309\u0323"
    for i, c in enumerate(d):
        if c in marks:                      # 부호를 앞·뒤 모음으로 옮겨 본다
            for j in (i - 2, i + 1):
                if 0 <= j < len(d) and unicodedata.normalize("NFD", d[j])[0].lower() in "aăâeêioôơuưy":
                    q = list(d); q.pop(i); q.insert(j + 1 if j > i else j + 1, c)
                    v = unicodedata.normalize("NFC", "".join(q))
                    if v != w: out.append(v)
    return out


def ask_deep(w):
    """낱말째로 물어보고, 없으면 **음절 하나씩** 물어서 이어 붙인다.
       두 낱말짜리(số lượng)는 통째 쪽이 없을 때가 많은데 음절은 거의 다 있다."""
    blocked = False
    for v in variants(w):
        r = ask(v)
        if r is None: blocked = True
        elif r: return r, "낱말"
    parts = re.split(r"[\s\-]+", w)
    if len(parts) > 1:
        got = {}
        for pt in parts:
            r = None
            for v in variants(pt):
                r = ask(v)
                if r: break
            if r is None: return None, ""
            if not r: return {}, ""
            for k, val in r.items(): got[k] = (got.get(k, "") + " " + val).strip()
        if got: return got, "음절"
    return (None if blocked else {}), ""


def words():
    """**지금 과정(order.json)의 낱말 전부** + 옛 앱 낱말 + 선배 낱말.
       전에는 days.json 만 봐서 새 과정 낱말 2,556개가 통째로 빠졌다 (2026-08-30)."""
    seen = {}
    op = R / "data" / "order.json"
    if op.exists():
        o = json.loads(op.read_text(encoding="utf-8"))
        def ws(v):
            for t in (v.get("tracks") or [v]):
                for c in t["chapters"]:
                    for l in c["lessons"]: yield from l["words"]
        for v in o["vols"]:
            for w in ws(v):
                seen.setdefault(nfc(w["vi"]).lower(), nfc(w["vi"]))
                for a in (w.get("alt") or []): seen.setdefault(nfc(a["vi"]).lower(), nfc(a["vi"]))
    for x in json.loads((R / "data" / "days.json").read_text(encoding="utf-8"))["days"]:
        for w in x.get("words") or []:
            seen.setdefault(nfc(w["vi"]).lower(), nfc(w["vi"]))
    for f in ("_senior_words.json", "_senior_words-19.json"):
        p = R / "data" / f
        if not p.exists(): continue
        for s in json.loads(p.read_text(encoding="utf-8"))["sets"]:
            if s["kind"] not in ("일일", "주간"): continue
            for w in s["words"]:
                v = nfc(w.get("vi") or "")
                # 선배 자료에는 **문장**이 섞여 있다 — 낱말만 쓴다 (대표님 지시).
                # 마침표·물음표가 있거나 다섯 음절이 넘으면 문장으로 본다.
                if re.search(r"[.?!]", v) or len(v.split()) > 4: continue
                if v and (w.get("ko") or "").strip(): seen.setdefault(v.lower(), v)
    return sorted(seen.values(), key=str.lower)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    got = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    todo = [w for w in words() if w not in got]
    if a.limit: todo = todo[:a.limit]
    print(f"받을 낱말 {len(todo)} (이미 받은 것 {len(got)})", flush=True)
    for i, w in enumerate(todo, 1):
        r, how = ask_deep(w)
        if r is None: continue                      # 막힌 것은 기록하지 않는다
        got[w] = r or {}
        if i % 50 == 0:
            OUT.write_text(json.dumps(got, ensure_ascii=False, indent=0), encoding="utf-8")
            hit = sum(1 for v in got.values() if v)
            print(f"  {i}/{len(todo)} · 사전에 있는 것 {hit}/{len(got)}", flush=True)
        time.sleep(0.6)   # 위키미디어를 두들기지 않는다
    OUT.write_text(json.dumps(got, ensure_ascii=False, indent=0), encoding="utf-8")
    hit = sum(1 for v in got.values() if v)
    print(f"끝 — 모은 낱말 {len(got)} · 사전에 있는 것 {hit} ({hit/max(1,len(got))*100:.0f}%)")


if __name__ == "__main__":
    main()
