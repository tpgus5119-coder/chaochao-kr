#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""한글 발음 표기를 **사전 발음기호와 대조**한다 → docs/kr-verify.md

왜 (대표님 지시): "발음도 니가 대충하지말고 사전에 있는 그대로 해라."
자료: data/_vi_ipa.json — 영어 위키낱말사전의 하노이·후에·사이공 발음기호.
잣대: 첫소리와 끝소리를 사전 기호에서 뽑아, vi_kr.py 가 적은 한글 자모와 맞춰 본다.
      맞고 틀림을 세어 **규칙이 틀린 자리**를 찾는다. 낱말 하나하나가 아니라 규칙을 고친다.
쓰기: python3 tools/kr_verify.py
"""
import collections, json, pathlib, re, sys, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools")); import vi_kr

IPA = json.loads((R / "data" / "_vi_ipa.json").read_text(encoding="utf-8"))

# 사전 기호 → 한글 첫소리
ONSET = [("kʰ", "ㅋ"), ("tʰ", "ㅌ"), ("t͡ɕ", "ㅉ"), ("t͡s", "ㅉ"), ("ʈ", "ㅉ"), ("ɗ", "ㄷ"), ("ɓ", "ㅂ"),
         ("ŋ", "응"), ("ɲ", "니"), ("ʔ", ""), ("j", "ㅇ"), ("z", "ㅈ"), ("ʐ", "ㅈ"),
         ("ʂ", "ㅅ"), ("s", "ㅆ"), ("x", "ㅋ"), ("k", "ㄲ"), ("m", "ㅁ"), ("n", "ㄴ"),
         ("l", "ㄹ"), ("h", "ㅎ"), ("f", "ㅍ"), ("v", "ㅂ"), ("t", "ㄸ"), ("p", "ㅃ"),
         ("ɣ", "ㄱ"), ("r", "ㄹ")]
CODA = [("ŋ͡m", "ㅇ"), ("k͡p", "ㄱ"), ("ŋ", "ㅇ"), ("ɲ", "ㅇ"), ("n", "ㄴ"), ("m", "ㅁ"),
        ("k", "ㄱ"), ("t", "ㅅ"), ("p", "ㅂ"), ("j", ""), ("w", "")]
CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JONG = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"

def jamo(ch):
    """한글 한 글자에서 (첫소리, 끝소리)."""
    o = ord(ch) - 0xAC00
    if not 0 <= o < 11172: return ("", "")
    return (CHO[o // 588], JONG[o % 28 // 1].strip() if o % 28 else "")

def first_onset(ipa):
    s = ipa.split()[0] if ipa.split() else ipa
    s = s.lstrip("ʔ")
    for k, v in ONSET:
        if s.startswith(k): return v
    return None

def last_coda(ipa):
    s = ipa.split()[-1] if ipa.split() else ipa
    s = re.sub(r"[˧˨˩˦˥ˀ̌̆̚ ]", "", s)
    for k, v in CODA:
        if s.endswith(k): return v
    return None

def main():
    tot = collections.Counter(); bad = collections.defaultdict(list)
    for vi, d in IPA.items():
        for place, key, want in (("Hà Nội", "n", False), ("Saigon", "s", True)):
            ip = d.get(place)
            if not ip: continue
            kr = vi_kr.word(vi, want)
            if not kr: continue
            k1, kl = kr[0], kr[-1]
            o_want, o_got = first_onset(ip), jamo(k1)[0]
            if o_want is not None and o_got:
                tot[f"{key}·첫소리"] += 1
                if o_want and o_want != o_got and not (o_want == "응" and o_got == "ㅇ") \
                   and not (o_want == "니" and o_got == "ㄴ"):
                    tot[f"{key}·첫소리 틀림"] += 1
                    bad[f"{key} 첫소리 {o_want}≠{o_got}"].append((vi, kr, ip))
            c_want, c_got = last_coda(ip), jamo(kl)[1]
            # 어말 nh 는 소리로는 [ŋ] 이지만 **국립국어원 표기법이 'ㄴ'** 이다
            #   (Bình → 빈 · Thanh → 타인). 표기 관례를 따르므로 어긋남으로 세지 않는다.
            if vi.split()[-1].lower().endswith("nh") and c_want == "ㅇ" and c_got == "ㄴ":
                c_want = c_got
            if c_want is not None:
                tot[f"{key}·끝소리"] += 1
                if c_want != c_got:
                    tot[f"{key}·끝소리 틀림"] += 1
                    bad[f"{key} 끝소리 {c_want or '없음'}≠{c_got or '없음'}"].append((vi, kr, ip))
    out = ["# 발음 표기 대조 — 사전(위키낱말) 발음기호 기준\n",
           f"낱말 {len(IPA)}개\n"]
    for k in sorted(tot): out.append(f"  {k}: {tot[k]}")
    out.append("\n## 어긋난 자리 (많은 차례)")
    for k, v in sorted(bad.items(), key=lambda x: -len(x[1]))[:24]:
        out.append(f"\n### {k} — {len(v)}개")
        for vi, kr, ip in v[:4]: out.append(f"     {vi:<18}{kr:<14}{ip}")
    (R / "docs" / "kr-verify.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out[:60]))

main()
