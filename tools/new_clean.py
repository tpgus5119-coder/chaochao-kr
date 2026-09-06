#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""한 칸에 **낱말 하나만** 남긴다 → data/_new_words.json

대표님 지적 (2026-09-01): "màu đỏ 이건 애초에 2단어잖아. 너무 길다고 빼냐?
                          단어가 2개 이상 합쳐지면 나눠야 한다는 말이야."

## 잣대는 길이가 아니다
bảo hiểm y tế(건강보험)는 네 음절이지만 사전에 **한 낱말**로 실린다.
màu đỏ 는 두 음절이지만 màu + đỏ **두 낱말**이다.
그래서 음절 수로 자르지 않는다. **사전에 한 표제어로 실리는가**만 본다.

## 세 겹으로 가린다 (모두 공짜 — 클로드 토큰이 안 든다)
① 우리 사전(_vi_ipa 5,381 표제어)에 있으면 → 한 낱말이다. 길어도 남긴다
② 없으면 **쪼개 본다**(가장 긴 것부터 맞춰 본다). 조각이 모두 아는 낱말이면
   → 여러 낱말이 붙은 것이다. 통째로 빼고 **조각을 각각 넣는다**
③ 쪼개지지도 않으면 위키낱말에 물어본다. 거기 있으면 남긴다
   (사전에 구멍이 있다 — cam·mình·cô giáo 는 진짜 낱말인데 우리 사전에 없었다)
④ 그래도 모르면 '모름'으로 표시만 하고 남긴다. Qwen 이 나중에 가린다

여기에 더해 같은 뜻이 셋 이상이면 줄인다 — '안녕하세요' 여덟 개는 과하다.

쓰기: python3 tools/new_clean.py [--dry]
"""
import argparse, json, pathlib, re, subprocess, sys, time, unicodedata as U, urllib.parse

R = pathlib.Path(__file__).resolve().parent.parent
OUT = R / "data" / "_new_words.json"
IPA = R / "data" / "_vi_ipa.json"
WORDS = R / "data" / "_vi_words.json"        # tools/dict_build.py 가 받아 둔 큰 사전
CACHE = R / "data" / "_wik_word.json"
WIKI = "https://vi.wiktionary.org/w/api.php?action=parse&prop=wikitext&format=json&page="
n = lambda s: U.normalize("NFC", str(s)).strip()
k = lambda s: n(s).lower()


def wik(word, cache):
    """위키낱말에 베트남어 표제어로 있나. 한 번 물은 것은 파일에 적어 둔다."""
    if k(word) in cache:
        return cache[k(word)]
    try:
        r = subprocess.run(["curl", "-sS", "-m", "12", WIKI + urllib.parse.quote(word)],
                           capture_output=True, text=True, timeout=20).stdout
        j = json.loads(r)
        t = "" if "error" in j else j["parse"]["wikitext"]["*"]
        v = bool(t) and ("Tiếng Việt" in t or "{{-vie-}}" in t)
    except Exception:
        v = None                                   # 못 물어봄 — 버리지 않는다
    cache[k(word)] = v
    time.sleep(0.15)
    return v


def main():
    a = argparse.ArgumentParser(); a.add_argument("--dry", action="store_true")
    a.add_argument("--dedupe", action="store_true")
    a = a.parse_args()
    d = json.loads(OUT.read_text(encoding="utf-8"))
    # ── 1차 검증은 **우리 사전**으로 한다 (대표님 지시). 인터넷을 안 타서 빠르고 공짜다.
    #    위키낱말 실시간 조회는 우리 사전에도 없는 것만 간다.
    known = {k(x) for x in json.loads(IPA.read_text(encoding="utf-8"))}
    if WORDS.exists():
        known |= {k(x) for x in json.loads(WORDS.read_text(encoding="utf-8"))}
    print(f"우리 사전 {len(known)} 낱말로 1차 검증한다", flush=True)
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    # 손으로 쓴 것은 내가 보증한다 — 사전에 없어도 낱말이다
    known |= {k(w["vi"]) for ws in d.values() for w in ws if w.get("src") == "손으로 씀"}

    def seg(s):
        """가장 긴 것부터 맞춰 쪼갠다. 조각이 다 아는 낱말이면 그 목록, 아니면 None"""
        ws, out, i = n(s).split(), [], 0
        while i < len(ws):
            for j in range(min(len(ws), i + 4), i, -1):
                c = " ".join(ws[i:j])
                if k(c) in known:
                    out.append(c); i = j; break
            else:
                return None
        return out if len(out) > 1 else None

    split, drop, add = [], [], {}
    for topic, ws in d.items():
        keep, ko_cnt = [], {}
        for w in ws:
            vi, ko = n(w["vi"]), n(w["ko"])
            if w.get("v") == "bad" and w.get("fix"):          # 고칠 안이 있으면 뜻을 바꾼다
                ko = w["ko"] = n(w["fix"]); w.pop("fix", None); w["v"] = "재검"
            if k(vi) in known:
                pass                                          # ① 한 낱말이다
            else:
                parts = seg(vi)
                if parts:                                     # ② 여러 낱말이 붙었다
                    split.append((topic, vi, ko, parts))
                    add.setdefault(topic, []).extend(parts)
                    continue
                v = wik(vi, cache)                            # ③ 위키낱말에 물어본다
                if v:
                    known.add(k(vi)); w["src"] = "위키낱말"
                elif v is False:
                    drop.append((topic, vi, ko, "사전에 없고 쪼개지지도 않는다")); continue
                else:
                    w["src"] = "모름"
            # 베트남어가 아닌 것 — 성조 부호도 đ 도 없는 순 알파벳은 영어가 샌 것이다
            # (실제로 hobby 가 '취미'로 들어와 sở thích 을 밀어냈다)
            if re.fullmatch(r"[a-zA-Z ]+", vi) and k(vi) not in known:
                drop.append((topic, vi, ko, "베트남어가 아니다")); continue
            keep.append(w)
        d[topic] = keep

    # 쪼갠 조각을 제 꼭지에 넣는다 (이미 있으면 안 넣는다). 뜻은 Qwen 이 채운다
    added = 0
    for topic, parts in add.items():
        have = {k(w["vi"]) for w in d[topic]}
        for p in parts:
            if k(p) in have:
                continue
            have.add(k(p)); added += 1
            d[topic].append({"vi": n(p), "ko": "", "src": "쪼갠 조각", "v": "뜻없음"})

    # ── 겹치는 말 정리 (--dedupe 일 때만)
    # **뜻이 확정된 뒤에 해야 한다.** 짧은 쪽 뜻이 잘못 적혀 있으면 엉뚱한 것이 지워진다 —
    # bàn chải 를 '칫솔'로 잘못 적어 놓는 바람에 진짜 칫솔(bàn chải đánh răng)이 밀렸었다.
    # 그래서 word_final.py(사전 뜻풀이 대조)를 거친 **다음에** 부른다.
    # **뜻이 같다고 지우지 않는다.** về(돌아가다)와 đi(가다)처럼 뜻을 대충 같게 적었을 뿐
    # 서로 다른 낱말인 경우가 있다 (실제로 về 가 사라졌었다).
    # 한쪽이 다른 쪽을 **통째로 품고 뜻도 같을 때만** 뺀다 — đỏ 가 있는데 màu đỏ 가 또 있는 꼴.
    dup = []
    for topic, ws in (d.items() if a.dedupe else []):
        by_ko = {}
        for w in ws:
            by_ko.setdefault(n(w["ko"]), []).append(w)
        gone = set()
        for ko, group in by_ko.items():
            if len(group) < 2 or not ko:
                continue
            # 손으로 쓴 꼭지는 건드리지 않는다 — 내가 보증한 목록이다.
            # (tại sao 가 sao 에, cái gì 가 gì 에 밀려 사라졌었다. 둘 다 제자리에 있어야 한다)
            if any(w.get("src") == "손으로 씀" for w in group):
                continue
            for a_ in group:
                for b_ in group:
                    if a_ is b_ or id(a_) in gone:
                        continue
                    aw, bw = k(a_["vi"]).split(), k(b_["vi"]).split()
                    if len(aw) > len(bw) and set(bw) <= set(aw):     # 긴 쪽이 짧은 쪽을 품는다
                        gone.add(id(a_)); dup.append((topic, a_["vi"], ko, b_["vi"])); break
        d[topic] = [w for w in ws if id(w) not in gone]
    print(f"품는 관계라 뺀 것 {len(dup)}: " +
          ", ".join(f"{a}←{b}" for _, a, _, b in dup[:10]))

    tot = sum(len(v) for v in d.values())
    print(f"쪼갠 것 {len(split)} · 버린 것 {len(drop)} · 조각으로 새로 넣은 것 {added} · 남은 낱말 {tot}")
    print("\n쪼갠 보기 12")
    for t, vi, ko, ps in split[:12]:
        print(f"  {vi:22}{ko:16}→ {' + '.join(ps)}")
    print("\n버린 보기 12")
    for t, vi, ko, why in drop[:12]:
        print(f"  {vi:22}{ko:16}{why}")
    if not a.dry:
        OUT.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
        print("\n저장했다")


# 불러오기만 할 때는 돌지 않는다 — 다른 도구가 TOPICS 같은 것을
# 가져다 쓸 때 낱말 모으기가 통째로 다시 도는 사고가 있었다 (2026-09-01).
if __name__ == "__main__":
    main()
