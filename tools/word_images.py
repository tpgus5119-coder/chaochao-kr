#!/usr/bin/env python3
"""**낱말 하나에 그림 하나** — 빠진 자리를 찾아 채울 계획을 세운다.

왜 필요했나: 한 챕터는 낱말 열 개인데 그림 카드가 열 장이 아니었다.
  · 한국어 과정(ko_days.json) 78일 × 10낱말 = 780개에 그림이 **하나도** 없었다.
  · 베트남어 과정(days.json)도 26개가 비어 있었다(Day 43.5 색과 무늬는 열 개 전부).

채우는 방법 세 가지 — 싼 것부터 쓴다:
  1) 재사용: 뜻이 같으면 이미 있는 그림을 쓴다. 학생 = học sinh 는 같은 그림이 맞다.
  2) 코드 작화: 색·무늬·도형·개수처럼 **정확해야 하는 것**은 tools/draw_words.py 가 직접 그린다.
     (생성 모델은 '하늘색'과 '남색'을 구별해 내지 못하고 줄무늬 개수도 못 맞춘다)
  3) 생성: 나머지 구체어는 Draw Things 로 굽는다. 프롬프트는 docs/image-prompts.md 에 쌓인다.

이 파일은 **계획만** 만든다(data/_word_img_plan.json). 실제로 굽는 것은 gen_images.py,
직접 그리는 것은 draw_words.py, 자료에 박아 넣는 것은 apply_word_images.py 가 한다.

실행: python3 tools/word_images.py
"""
import json
import pathlib
import re
import unicodedata

R = pathlib.Path(__file__).resolve().parent.parent
IMG = R / "img"

# 한글 로마자 — 한국어 낱말은 한국어 이름으로 파일을 만든다(k-ireum).
# 베트남어 표기로 이름을 지으면 "bài hát đại chúng, ca khúc được yêu thích"(가요) 같은
# 긴 풀이가 그대로 파일 이름이 된다. 한국어 과정은 한국어가 주인이다.
CHO = ["g", "kk", "n", "d", "tt", "r", "m", "b", "pp", "s", "ss", "", "j", "jj",
       "ch", "k", "t", "p", "h"]
JUNG = ["a", "ae", "ya", "yae", "eo", "e", "yeo", "ye", "o", "wa", "wae", "oe",
        "yo", "u", "wo", "we", "wi", "yu", "eu", "ui", "i"]
JONG = ["", "k", "k", "k", "n", "n", "n", "t", "l", "l", "l", "l", "l", "l", "l",
        "l", "m", "p", "p", "t", "t", "ng", "t", "t", "k", "t", "p", "t"]


def romanize(s):
    out = []
    for ch in s:
        o = ord(ch)
        if 0xAC00 <= o <= 0xD7A3:
            i = o - 0xAC00
            out.append(CHO[i // 588] + JUNG[(i % 588) // 28] + JONG[i % 28])
        elif ch.isalnum():
            out.append(ch.lower())
        else:
            out.append("-")
    return re.sub(r"-+", "-", "".join(out)).strip("-")


def slug(s):
    """베트남어 표기 → ASCII 이름 (기존 파일 이름 규칙과 같게)."""
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")


def load():
    vi = json.loads((R / "data" / "days.json").read_text())["days"]
    ko = json.loads((R / "data" / "ko_days.json").read_text())["days"]
    return vi, ko


def head(s):
    """뜻풀이의 첫 갈래만 — '가요' 의 vi 는 쉼표로 이어진 긴 풀이다."""
    return re.split(r"[,;(·]", s)[0].strip()


def build():
    vi, ko = load()
    have = {p.stem for p in IMG.glob("*.webp")}

    # 이미 있는 그림을 어떤 말로 찾아갈 수 있는지 — 베트남어 표기·한국어 뜻 두 갈래
    by_vi, by_ko = {}, {}
    for d in vi:
        for w in d["words"]:
            if w.get("img") and pathlib.Path(w["img"]).stem in have:
                n = pathlib.Path(w["img"]).stem
                by_vi.setdefault(head(w["vi"]).lower(), n)
                by_ko.setdefault(head(w["ko"]), n)

    plan = {"reuse": [], "new": []}
    used = set()

    # ── 한국어 과정 ────────────────────────────────────────────────
    for d in ko:
        for w in d["words"]:
            k, v = w["ko"].strip(), head(w["vi"]).lower()
            src = by_vi.get(v) or by_ko.get(head(k))
            if src:
                plan["reuse"].append({"course": "ko", "day": d["day"], "ko": k,
                                      "vi": w["vi"], "img": src + ".webp"})
                continue
            name = "k-" + romanize(k)
            while name in used:
                name += "-2"
            used.add(name)
            plan["new"].append({"course": "ko", "day": d["day"], "theme": d["theme"]["ko"],
                                "ko": k, "vi": w["vi"], "name": name,
                                "exists": name in have})

    # ── 베트남어 과정에서 빠진 자리 ───────────────────────────────
    for d in vi:
        for w in d["words"]:
            if w.get("img"):
                continue
            pre = "x-" if isinstance(d["day"], str) or w.get("shared") else \
                  f"d{str(d['day']).replace('.', '')}-"
            name = pre + slug(w["vi"])
            if name in have or name in used:
                name = "x-" + slug(w["vi"])
            while name in used:
                name += "-2"
            used.add(name)
            plan["new"].append({"course": "vi", "day": d["day"], "theme": d["theme"],
                                "ko": w["ko"], "vi": w["vi"], "name": name,
                                "exists": name in have})
    return plan


if __name__ == "__main__":
    p = build()
    (R / "data" / "_word_img_plan.json").write_text(
        json.dumps(p, ensure_ascii=False, indent=1))
    n_new = sum(1 for x in p["new"] if not x["exists"])
    print(f"재사용 {len(p['reuse'])}장 · 새로 필요 {n_new}장 "
          f"(이미 구워진 것 {len(p['new']) - n_new}장)")
    for c in ("ko", "vi"):
        print(f"  {c}: 재사용 {sum(1 for x in p['reuse'] if x['course'] == c)} · "
              f"새로 {sum(1 for x in p['new'] if x['course'] == c and not x['exists'])}")
