#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""이미 구워 둔 그림을 **과정 낱말에 이어 붙인다** → order.json 에 img 를 채운다.

새로 굽기 전에 이것부터 한다 — 그림이 2,128장 있는데 과정 낱말에는 713개만 붙어 있었다.
붙이는 잣대 ① 같은 낱말(베트남어)  ② 같은 뜻(한국어 첫 조각)
쓰기: python3 tools/img_link.py
"""
import json, os, pathlib, re, unicodedata as U, collections

R = pathlib.Path(__file__).resolve().parent.parent

def key(v):
    s = U.normalize("NFC", str(v)).strip().lower()
    s = re.sub(r"\([^)]*\)", "", s)
    return re.sub(r"\s+", " ", s).strip(" .,;:!?~–—/\"'")

def kko(k):
    """뜻에서 견줄 알맹이만 남긴다.
       **앞의 품사 표시를 먼저 뗀다** — '(동) 쑥스러운' 을 '(' 에서 자르면 빈 문자열이 되고,
       빈 키끼리 맞아떨어져 **엉뚱한 그림**이 붙었다 (인사 그림이 '기회'에 붙어 있었다).
       2026-08-30 검수"""
    t = U.normalize("NFC", str(k)).strip()
    # 앞의 품사 표시만 뗀다. **품사 이름을 못 박는다** — 아무 괄호나 떼면
    #   '(집중하다)' 까지 지워져 빈 키가 되고, 빈 키끼리 맞아 엉뚱한 그림이 붙는다.
    t = re.sub(r"^\(\s*(?:명|동|형|부|전|접|대|수|조|감)(?:\s*[·/]\s*(?:명|동|형|부|전|접|대|수|조|감))*\s*\)\s*",
               "", t)
    t = t.split("/")[0]
    if not t.startswith("("): t = t.split("(")[0]      # 통째로 괄호인 뜻은 안쪽을 쓴다
    else: t = t.strip("()")
    return re.sub(r"[\s,·]", "", t).strip()

def wname(ko):
    """뜻에서 구운 그림 파일 이름. 있으면 그 이름을, 없으면 None."""
    import hashlib
    k = U.normalize("NFC", str(ko)).split("/")[0].strip()
    n = "w-" + hashlib.sha1(k.encode()).hexdigest()[:10] + ".webp"
    return n if (R / "img" / n).exists() else None


# 낱말은 같은데 **뜻이 갈라진** 것 — 옛 그림이 지금 뜻과 안 맞는다 (2026-08-30 검수)
#   hay 는 '흥미롭다'와 '또는' 두 뜻인데 그림은 '흥미롭다' 것이었다
DROP = {("hay", "d18-hay.webp"), ("hiểu", "x-biet.webp"), ("leo", "x-tawng.webp"),
        ("kêu", "x-keu.webp"), ("xảy ra", "d11-day.webp")}


def main():
    have = {p.name for p in (R / "img").glob("*.webp")}
    byvi, byko = {}, {}
    for f in ("days.json", "ko_days.json"):
        p = R / "data" / f
        if not p.exists(): continue
        d = json.loads(p.read_text(encoding="utf-8"))
        for day in (d if isinstance(d, list) else d.get("days", [])):
            for w in (day.get("words") or []):
                im = w.get("img")
                if not im or im not in have: continue
                byvi.setdefault(key(w.get("vi", "")), im)
                _k = kko(w.get("ko", ""))
                if _k: byko.setdefault(_k, im)          # 빈 키는 담지 않는다
    o = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    stat = collections.Counter()

    def walk(v):
        for t in (v.get("tracks") or [v]):
            for c in t["chapters"]:
                for l in c["lessons"]:
                    yield from l["words"]

    for v in o["vols"]:
        for w in walk(v):
            if w.get("img") and w["img"] in have: stat["이미 있음"] += 1; continue
            # gen_word_img 가 구운 것은 **뜻의 해시**가 파일 이름이다 (w-<sha1>.webp).
            #   order.json 을 다시 만들면 img 가 날아가는데 여기서 되찾는다 (2026-08-30)
            _kk = kko(w["ko"])
            im = byvi.get(key(w["vi"])) or (byko.get(_kk) if _kk else None) or wname(w["ko"])
            if (w["vi"], im) in DROP: im = None          # 뜻이 갈라져 안 맞는 그림
            if im: w["img"] = im; stat["새로 이어 붙임"] += 1
            else:
                w.pop("img", None); stat["아직 그림 없음"] += 1
    for w in o.get("gramwords", []):
        im = byvi.get(key(w["vi"])) or byko.get(kko(w["ko"]))
        if im: w["img"] = im
    (R / "data" / "order.json").write_text(json.dumps(o, ensure_ascii=False, separators=(",", ":")),
                                           encoding="utf-8")
    print("그림 파일", len(have), "· 낱말별:", dict(stat))
main()
