#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 가 낸 철자 교정 중 **믿을 수 있는 것만** 골라 senior_pool 에 넣는다.

왜 거르나 (2026-08-30): AI 가 뜻에 맞추려고 **아예 다른 낱말**로 바꾼 것이 섞여 있다.
  rộng rãi(넓은) → hào phóng(너그러운) · trụ sở(본부) → địa chỉ(주소)
그래서 뼈대(성조를 벗긴 글자)가 얼마나 달라졌는지로 가른다.
  ① 뼈대가 같다(성조·모자만 다름)      → 받는다   cá phê → cà phê
  ② 늘려 적은 것(줄임말 풀기·꼬리 붙이기) → 받는다   bV → bệnh viện · oi → oi bức
  ③ 글자 두 자 안쪽으로 다르다           → 받는다   ngưởi → người
  ④ 그 밖                              → **미룬다**. docs/spell-hold.tsv 에 남긴다
쓰기: python3 tools/spell_apply.py
"""
import json, pathlib, re, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent

def bare(v):
    s = U.normalize("NFD", v.lower())
    s = "".join(c for c in s if not U.combining(c)).replace("đ", "d")
    return re.sub(r"[^a-z ]", "", s).strip()

def dist(a, b):
    if a == b: return 0
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]

def verdict(old, new):
    bo, bn = bare(old), bare(new)
    if bo == bn: return "받음 · 성조만"
    if bn.startswith(bo) or bn.endswith(bo) or bo in bn.split(): return "받음 · 늘려 적음"
    if dist(bo, bn) <= 2: return "받음 · 두 자 안"
    ow, nw = bo.split(), bn.split()
    if len(ow) == len(nw) and sum(1 for a, b in zip(ow, nw) if dist(a, b) > 2) <= 1:
        return "받음 · 한 마디만"
    return "미룸"

def main():
    D = json.loads((R / "data" / "_spell.json").read_text(encoding="utf-8"))
    p = R / "data" / "senior_pool.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    fix, hold = {}, []
    for k, v in D.items():
        f = (v.get("fix") or "").strip()
        if not f or f == "?" or U.normalize("NFC", f) == U.normalize("NFC", v["vi"]): continue
        w = verdict(v["vi"], f)
        if w.startswith("받음"): fix[U.normalize("NFC", v["vi"]).lower()] = (f, w)
        else: hold.append((v["vi"], f, v["ko"], w))
    n = 0
    for w in d["words"]:
        k = U.normalize("NFC", w["vi"]).lower()
        if k in fix:
            w["spellwas"] = w["vi"]; w["vi"] = fix[k][0]; n += 1
    # 철자를 고치면 서로 같아지는 낱말이 생긴다 (aó sơ mi → áo sơ mi). 다시 합친다.
    import sys; sys.path.insert(0, str(R / "tools")); import senior_hand as H
    # 마지막 그물 — 손질 뒤에도 낱말이 아닌 것이 남아 있었다 (괄호 깨진 줄 하나)
    before = len(d["words"])
    d["words"] = [w for w in d["words"] if not H.junk(w["vi"], w.get("ko", ""))]
    if before != len(d["words"]): print(f"  마지막 그물에 걸린 것 {before - len(d['words'])}개")
    d["words"], gone = H.dedupe(d["words"])
    d["words"], g2 = H.same_word(d["words"]); gone += g2
    print(f"  철자를 고쳐 같아진 낱말 {gone}쌍을 합쳤다")
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    (R / "docs" / "spell-hold.tsv").write_text(
        "원래\t고치자고 한 것\t뜻\t왜 미뤘나\n" +
        "\n".join("\t".join(x) for x in hold), encoding="utf-8")
    print(f"고친 낱말 {n}개 · 미룬 것 {len(hold)}개 → docs/spell-hold.tsv")
    for a, b, k, _ in hold[:20]: print(f"   미룸  {a:<22}→ {b:<24}{k[:20]}")

main()
