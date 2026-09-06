#!/usr/bin/env python3
"""우리가 가르치는 낱말에 **한자와 한월(漢越) 읽기**를 붙인다.

  python3 tools/hanja_attach.py            → data/*.json 에 han 칸을 넣는다
  python3 tools/hanja_attach.py --dry      → 세기만 하고 쓰지 않음

왜: 베트남 학습자에게 한자어는 공짜 점수다. 教育 → 교육 / giáo dục.
한 번 다리를 놓으면 그 뒤로 한자어가 통째로 쉬워진다. 우리 시험 지문의 한자어가
공식 자료보다 10%p 모자란 것도 결국 여기서 갈린다 — **가르치지 않은 낱말은 쓸 수 없다.**

동음이의어를 어떻게 가리나: 한글이 같고 한자가 다른 낱말이 210개 있다
(인상 = 人相 / 引上 / 印象). **찍지 않는다.** 우리 자료에 이미 적힌 베트남어 뜻과
사전의 베트남어 뜻을 맞대어, 겹치는 것만 고른다. 못 고르면 비워 둔다 —
틀린 한자를 다는 것이 안 다는 것보다 나쁘다(다리로 쓰는 글자라서).
"""
import argparse
import glob
import json
import pathlib
import re
import unicodedata

R = pathlib.Path(__file__).resolve().parent.parent
SRC = pathlib.Path.home() / "krdict" / "json"
FILES = ["data/ko_days.json", "data/days.json", "data/news_days.json"]


def feats(o):
    if isinstance(o, list):
        o = o[0] if o else {}
    f = o.get("feat") if isinstance(o, dict) else None
    if f is None:
        return {}
    return {x["att"]: x["val"] for x in (f if isinstance(f, list) else [f])
            if isinstance(x, dict) and "att" in x}


FILLER = {"sự", "việc", "cái", "người", "con", "một", "các", "những", "là", "của"}


def norm(s):
    """뜻을 견주기 좋게 다듬는다 — 대소문자와 군말만 벗긴다.

    **성조는 절대 벗기지 않는다.** 처음에 벗겼더니 phóng(쏘다)과 phòng(방)이,
    trương과 trưởng이 같은 낱말이 되어 誇張(과장하다)이 課長(과장님)과 비겼다.
    베트남어에서 성조는 곧 뜻이다.
    """
    s = unicodedata.normalize("NFC", (s or "").lower())
    ws = re.split(r"[^0-9a-zà-ỹ]+", s)
    return {w for w in ws if len(w) > 1 and w not in FILLER}


def dictionary():
    """{한글: [(한자, 베트남어뜻), …]} — 등급을 가리지 않고 전부 담는다."""
    out = {}
    for fn in sorted(glob.glob(str(SRC / "*.json"))):
        d = json.load(open(fn, encoding="utf-8"))
        for e in d["LexicalResource"]["Lexicon"]["LexicalEntry"]:
            ko = feats(e["Lemma"]).get("writtenForm", "").strip()
            han = feats(e).get("origin", "")
            if not ko or not re.search(r"[一-鿿]", han):
                continue
            han = re.sub(r"[^一-鿿]", "", han)      # '尖銳하다' → '尖銳'
            vi = ""
            ss = e["Sense"] if isinstance(e["Sense"], list) else [e["Sense"]]
            for s in ss:
                eq = s.get("Equivalent") or []
                for q in (eq if isinstance(eq, list) else [eq]):
                    m = feats(q)
                    if m.get("language") == "베트남어" and m.get("lemma"):
                        vi = m["lemma"]
                        break
                if vi:
                    break
            out.setdefault(ko, []).append((han, vi))
    return out


def pick(cands, our_vi):
    """여러 한자 중 하나를 고른다. 못 고르면 None — 찍지 않는다.

    낱말이 하나라도 겹치면 고르게 했더니 헐거웠다 — 'bác sĩ' 의 sĩ 가
    義士(nghĩa sĩ)에도 걸려 의사를 못 가렸다. 그래서 **얼마나 겹치는지**를 재고,
    으뜸이 버금을 확실히 앞설 때만 고른다. 비기면 비워 둔다.
    """
    cands = [(h, v) for h, v in cands if h]
    if not cands:
        return None
    if len({h for h, _ in cands}) == 1:
        return cands[0][0]
    mine = norm(our_vi)
    if not mine:
        return None
    scored = sorted(((len(mine & norm(v)) / len(mine), h) for h, v in cands),
                    key=lambda t: -t[0])
    best, second = scored[0], (scored[1] if len(scored) > 1 else (0.0, None))
    return best[1] if best[0] > 0 and best[0] > second[0] else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if not SRC.exists():
        raise SystemExit(f"사전이 없다: {SRC}")

    D = dictionary()
    print(f"사전에서 한자 붙은 표제어 {len(D):,}개")

    tot = hit = amb = plain = 0
    for fn in FILES:
        p = R / fn
        d = json.load(open(p, encoding="utf-8"))
        n_before = 0

        def walk(o):
            nonlocal tot, hit, amb, plain, n_before
            if isinstance(o, dict):
                if isinstance(o.get("ko"), str) and isinstance(o.get("vi"), str) \
                        and "who" not in o:                 # 대화 줄은 낱말이 아니다
                    tot += 1
                    if o.get("han"):
                        n_before += 1
                    if o.get("hanja"):
                        # 손으로 적어 둔 한자가 있으면 건드리지 않는다.
                        # 그 칸은 **베트남어 낱말의 어원**이고(thứ hai = 次二),
                        # 여기서 붙이는 han 은 **한국어 뜻의 한자**다(월요일 = 月曜日).
                        # 둘을 한 카드에 같이 두면 배우는 사람이 어느 쪽이 그 낱말의
                        # 한자인지 알 수 없다 — 실제로 118개가 어긋나 있었다.
                        plain += 1
                        for v in o.values():
                            walk(v)
                        return
                    c = D.get(o["ko"].strip())
                    if not c:
                        plain += 1
                    else:
                        h = pick(c, o["vi"])
                        if h:
                            o["han"] = h
                            hit += 1
                        else:
                            amb += 1
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for x in o:
                    walk(x)
        walk(d)
        if not a.dry:
            p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"  {fn}")

    print(f"\n낱말 {tot:,}개 · 한자 붙임 {hit:,} ({hit/max(1,tot)*100:.1f}%) · "
          f"한자어 아님 {plain:,} · **못 가림 {amb:,}(비워 둠)**")
    print("못 가린 것은 한자를 안 단다 — 틀린 다리가 없는 다리보다 나쁘다.")


if __name__ == "__main__":
    main()
