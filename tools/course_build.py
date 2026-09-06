#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**하나로 합친 과정**을 만든다 → data/course.json

일곱 권 (대표님 결정, 2026-08-30)
  1권 기본기·문법 | 2~5권 일상 | 6권 직무 | 7권 문화·베트남 바로알기
  한 강 = **15낱말**. 복습 강은 없다(앱에 복습 기능이 따로 있다).
  낱말마다 예문이 붙고, 예문은 낱말마다 눌러 소리·발음·뜻을 본다.

앞의 도구와 이어지는 자리
  senior_scan → senior_merge → senior_hand → senior_split → toc_build → **course_build**
쓰기: python3 tools/course_build.py
"""
import json, pathlib, re, sys, unicodedata as U, collections

R = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(R / "tools"))
import vi_kr

PER = 15

def key(v):
    s = U.normalize("NFC", str(v)).strip().lower()
    s = re.sub(r"\([^)]*\)", "", s)
    return re.sub(r"\s+", " ", s).strip(" .,;:!?~–—/\"'")

def app_extras():
    """앱이 이미 가진 것 — 그림·한자·성조·예문을 낱말에 도로 붙인다.
       새로 만들 필요가 없다. 있는 것을 버리면 그게 제일 아깝다."""
    d = json.loads((R / "data" / "days.json").read_text(encoding="utf-8"))
    days = d if isinstance(d, list) else d["days"]
    ex, sent = {}, []
    for day in days:
        for w in (day.get("words") or []):
            k = key(w.get("vi", ""))
            if k: ex[k] = {t: w[t] for t in ("img", "hanja", "tones", "kr_read", "south", "emoji") if w.get(t)}
        dl = day.get("dialog") or {}
        for l in (dl.get("lines") or []):
            if l.get("vi"): sent.append({"vi": l["vi"], "ko": l.get("ko", ""), "kr": l.get("kr_read", "")})
        for t in (dl.get("extra") or []):
            if isinstance(t, dict) and t.get("vi"): sent.append({"vi": t["vi"], "ko": t.get("ko", ""), "kr": t.get("kr_read", "")})
    return ex, sent

def norm_sent(t):
    return " " + re.sub(r"\s+", " ", str(t).lower().replace(",", " ").replace(".", " ")
                        .replace("?", " ").replace("!", " ")).strip() + " "

def main():
    toc = json.loads((R / "data" / "_toc.json").read_text(encoding="utf-8"))
    ex, sents = app_extras()
    # AI 가 만든 예문 — 앱 대화에 없는 낱말을 메운다 (tools/gen_examples.py)
    exf = R / "data" / "_examples.json"
    made = json.loads(exf.read_text(encoding="utf-8")) if exf.exists() else {}
    holds = [norm_sent(s["vi"]) for s in sents]
    used = set()

    def example(vi):
        """그 낱말이 든 문장을 앱의 대화에서 찾아 준다. 한 문장은 되도록 한 낱말에만."""
        t = " " + key(vi) + " "
        cand = [i for i, h in enumerate(holds) if t in h]
        for i in cand:
            if i not in used: used.add(i); return sents[i]
        return sents[cand[0]] if cand else None

    vols, stat = [], collections.Counter()
    for src, vname in [(None, None)]:
        pass
    order = toc["daily"] + [toc["job"]]
    for v in order:
        units = []
        for u in v["units"]:
            ws = []
            for vi, ko, n in u["list"]:
                k = key(vi)
                w = {"vi": vi, "ko": ko, "kr": vi_kr.word(vi), "krs": vi_kr.word(vi, True)}
                if n: w["sr"] = 1                    # 선배 시험에 나온 낱말 = 별표
                # **두 기수 이상**에 나온 낱말은 '핵심'이다. 한 기수에만 나온 말은 그 해
                # 교재 사정일 수 있지만, 두 해 넘게 나온 말은 그 과정의 뼈대다.
                if n >= 2: w["core"] = n
                w.update(ex.get(k, {}))
                e = example(vi)
                if e:
                    w["ex"] = {"vi": e["vi"], "ko": e["ko"],
                               "kr": e["kr"] or vi_kr.word(e["vi"]),
                               "krs": vi_kr.word(e["vi"], True)}
                    stat["예문 — 앱 대화에서"] += 1
                elif k in made:
                    w["ex"] = made[k]
                    stat["예문 — 새로 만든 것"] += 1
                else:
                    # 예문을 끝내 못 만든 낱말은 **낱말이 아니다**. 두 번 넘게 부탁했는데도
                    # 그 낱말이 든 문장이 안 나온다면 오타이거나 칸이 붙은 찌꺼기다.
                    # (Bà ầy · ngưởi · mởcửa · bạn tari …)
                    stat["예문을 못 만들어 뺌"] += 1
                    continue
                if w.get("img"): stat["그림 있음"] += 1
                ws.append(w)
            ch = [ws[i:i + PER] for i in range(0, len(ws), PER)]
            if not ws: continue
            units.append({"unit": u["unit"], "chapters": [{"n": i + 1, "words": c} for i, c in enumerate(ch)]})
        vols.append({"vol": v["vol"], "units": units,
                     "words": sum(len(c["words"]) for u in units for c in u["chapters"]),
                     "chapters": sum(len(u["chapters"]) for u in units)})

    out = {"note": "일곱 권으로 합친 과정. 한 강 15낱말. 복습 강 없음.", "vols": vols}
    (R / "data" / "course.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")),
                                            encoding="utf-8")
    tot = sum(v["words"] for v in vols); ch = sum(v["chapters"] for v in vols)
    print(f"낱말 {tot} · 강 {ch}")
    for v in vols: print(f"   {v['vol']:<14} {v['words']:>5}낱말 {v['chapters']:>4}강 {len(v['units']):>3}과")
    print("  ", dict(stat))
main()
