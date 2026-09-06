#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""예문에 쓰인 낱말이 **어디서 온 말인지** 등급을 매겨 보고한다 → docs/ex-check.md

대표님이 정한 차례 (2026-08-30):
  0. 그 낱말 자체가 예문에 들어 있어야 한다 ← **기본. 없으면 잘못된 예문**
  1. 이미 배운 낱말(앞선 레슨)      ← 가장 좋다
  2. 같은 레슨에 들어갈 낱말
  3. 같은 챕터
  4. 같은 권
  5. 그냥 앱 어딘가에 있는 낱말(문법·기본기·문화·다른 권 포함)
  6. 앱에 아예 없는 낱말            ← 나쁘다
목차가 바뀌거나 낱말이 들고 나도 **다시 돌리면 그때 자리로 다시 잰다** —
등급을 파일에 굳혀 두지 않는 이유다.
**예문을 여기서 고치지는 않는다** (대표님 지시: "따로 보고만 해줘").
쓰기: python3 tools/ex_check.py [--top N]
"""
import argparse, collections, json, pathlib, re, unicodedata as U

R = pathlib.Path(__file__).resolve().parent.parent
nfc = lambda s: U.normalize("NFC", str(s)).lower().strip(" .,!?;:\"'…")

def load():
    """앱 안 모든 낱말의 **자리**를 잰다: (권, 챕터, 레슨, 레슨 안 차례)."""
    O = json.loads((R / "data" / "order.json").read_text(encoding="utf-8"))
    place, order, cards = {}, {}, []
    seq = 0
    for vi, v in enumerate(O["vols"]):
        for ti, t in enumerate(v.get("tracks") or [v]):
            for ci, c in enumerate(t["chapters"]):
                for li, l in enumerate(c["lessons"]):
                    for wi, w in enumerate(l["words"]):
                        p = (vi, ti, ci, li)
                        for k in [w["vi"]] + [a["vi"] for a in (w.get("alt") or [])]:
                            place.setdefault(nfc(k), p); order.setdefault(nfc(k), seq)
                        cards.append((p, seq, w)); seq += 1
    other = set()
    for w in O.get("gramwords", []): other.add(nfc(w["vi"]))
    for f, pick in (("grammar.json", "gram"), ("exgloss.json", "gloss"), ("know.json", "know")):
        p = R / "data" / f
        if not p.exists(): continue
        d = json.loads(p.read_text(encoding="utf-8"))
        if pick == "gram":
            for b in d["books"]:
                for x in b["bai"]:
                    for g in x["g"]:
                        for kw in (g.get("kw") or []): other.add(nfc(kw[0]))
                        for e in g["ex"]:
                            for t in e["vi"].split(): other.add(nfc(t))
        elif pick == "gloss":
            other |= {nfc(k) for k in d}
    for f in ("days.json",):
        p = R / "data" / f
        if not p.exists(): continue
        d = json.loads(p.read_text(encoding="utf-8"))
        for day in d.get("days", []):
            for w in day.get("words", []): other.add(nfc(w["vi"]))
    return place, order, cards, other

def grade(tok, self_vi, p, seq, place, order, other):
    if tok in self_vi: return 0
    q = place.get(tok)
    if q is None: return 5 if tok in other else 6
    if order.get(tok, 10 ** 9) < seq: return 1          # 앞서 배운다
    if q == p: return 2                                  # 같은 레슨
    if q[:3] == p[:3]: return 3                          # 같은 챕터
    if q[:2] == p[:2]: return 4                          # 같은 권/갈래
    return 5

def main():
    a = argparse.ArgumentParser(); a.add_argument("--top", type=int, default=40); a = a.parse_args()
    place, order, cards, other = load()
    NAME = {0: "그 낱말", 1: "이미 배운 말", 2: "같은 레슨", 3: "같은 챕터",
            4: "같은 권", 5: "앱 어딘가", 6: "앱에 없음"}
    cnt = collections.Counter(); bad = []; noself = []
    for p, seq, w in cards:
        ex = w.get("ex")
        if not ex: continue
        self_vi = {nfc(x) for x in [w["vi"]] + [a2["vi"] for a2 in (w.get("alt") or [])]}
        toks = [nfc(t) for t in ex["vi"].split() if nfc(t)]
        # 낱말이 예문에 들어 있나 (두세 마디로 이어 붙여도 본다)
        joined = nfc(ex["vi"])
        if not any(v and v in joined for v in self_vi): noself.append((w["vi"], ex["vi"]))
        gs = []
        for t in toks:
            if re.fullmatch(r"[\d.,%]+", t): continue
            g = grade(t, self_vi, p, seq, place, order, other)
            cnt[g] += 1; gs.append((t, g))
        n6 = sum(1 for _, g in gs if g == 6)
        if n6: bad.append((n6, w["vi"], ex["vi"], [t for t, g in gs if g == 6]))
    tot = sum(cnt.values())
    out = ["# 예문 낱말 등급 — 대표님이 정한 차례로 잰 것\n",
           f"예문 {len(cards)}개 · 낱말 자리 {tot}개\n", "| 등급 | 뜻 | 개수 | 몫 |", "|---|---|---:|---:|"]
    for g in range(7):
        out.append(f"| {g} | {NAME[g]} | {cnt[g]} | {cnt[g]*100/max(1,tot):.1f}% |")
    good = cnt[0] + cnt[1] + cnt[2] + cnt[3] + cnt[4]
    out += ["", f"**배운 말 안에서 만든 몫: {good*100/max(1,tot):.1f}%** "
                f"(0~4등급) · 앱 밖 말: {cnt[6]*100/max(1,tot):.1f}%", ""]
    out += [f"## ① 낱말이 예문에 안 들어 있는 것 — {len(noself)}개 (기본이 어긋난 것)", ""]
    for v, e in noself[:a.top]: out.append(f"- `{v}` → {e}")
    bad.sort(reverse=True)
    out += ["", f"## ② 앱에 없는 낱말이 많은 예문 — {len(bad)}개 (많은 차례 {a.top}개)", ""]
    for n, v, e, ws in bad[:a.top]:
        out.append(f"- **{n}개** `{v}` → {e}  ← {', '.join(ws)}")
    (R / "docs" / "ex-check.md").write_text("\n".join(out), encoding="utf-8")
    print("\n".join(out[:16]))
    print(f"\n① 낱말 빠진 예문 {len(noself)} · ② 앱 밖 낱말이 든 예문 {len(bad)}")
    print("→ docs/ex-check.md")

if __name__ == "__main__":
    main()
